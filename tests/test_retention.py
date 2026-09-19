from __future__ import annotations

from datetime import timedelta
from io import StringIO
from unittest.mock import AsyncMock, patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from monitoring.jobs import evaluate_job_monitor
from monitoring.models import CheckResult, JobEvent, Monitor
from monitoring.retention import RetentionResult, prune_monitor_history


class MonitorHistoryRetentionTests(TestCase):
    def test_prunes_expired_check_results_and_preserves_recent_results(self):
        monitor = Monitor.objects.create(
            name="retention-push",
            kind=Monitor.Kind.PUSH,
            interval_seconds=60,
        )
        now = timezone.now()
        old = CheckResult.objects.create(
            monitor=monitor,
            checked_at=now - timedelta(days=31),
            success=True,
            observed_state=Monitor.State.UP,
            message="old",
        )
        recent = CheckResult.objects.create(
            monitor=monitor,
            checked_at=now - timedelta(days=1),
            success=True,
            observed_state=Monitor.State.UP,
            message="recent",
        )

        result = prune_monitor_history(
            now=now,
            check_retention_days=30,
            job_event_retention_days=90,
        )

        self.assertEqual(result.check_results_deleted, 1)
        self.assertFalse(CheckResult.objects.filter(pk=old.pk).exists())
        self.assertTrue(CheckResult.objects.filter(pk=recent.pk).exists())

    def test_prunes_old_job_history_but_preserves_latest_terminal_state(self):
        monitor = Monitor.objects.create(
            name="retention-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
        )
        now = timezone.now()
        old_failure = JobEvent.objects.create(
            monitor=monitor,
            received_at=now - timedelta(days=120),
            event_type=JobEvent.EventType.FAILURE,
            run_id="old-failure",
            exit_code=1,
        )
        matched_start = JobEvent.objects.create(
            monitor=monitor,
            received_at=now - timedelta(days=100),
            event_type=JobEvent.EventType.START,
            run_id="latest-run",
        )
        latest_terminal = JobEvent.objects.create(
            monitor=monitor,
            received_at=now - timedelta(days=99),
            event_type=JobEvent.EventType.SUCCESS,
            run_id="latest-run",
            duration_ms=1000,
        )
        old_log = JobEvent.objects.create(
            monitor=monitor,
            received_at=now - timedelta(days=98),
            event_type=JobEvent.EventType.LOG,
            run_id="latest-run",
            message="expired log",
        )

        result = prune_monitor_history(
            now=now,
            check_retention_days=30,
            job_event_retention_days=90,
        )

        self.assertEqual(result.job_events_deleted, 3)
        self.assertFalse(JobEvent.objects.filter(pk=old_failure.pk).exists())
        self.assertFalse(JobEvent.objects.filter(pk=matched_start.pk).exists())
        self.assertFalse(JobEvent.objects.filter(pk=old_log.pk).exists())
        self.assertTrue(JobEvent.objects.filter(pk=latest_terminal.pk).exists())

    def test_preserves_unmatched_start_required_for_overrun_evaluation(self):
        monitor = Monitor.objects.create(
            name="retention-running-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
            job_max_runtime_seconds=60,
        )
        now = timezone.now()
        stale_log = JobEvent.objects.create(
            monitor=monitor,
            received_at=now - timedelta(days=120),
            event_type=JobEvent.EventType.LOG,
            message="expired",
        )
        active_start = JobEvent.objects.create(
            monitor=monitor,
            received_at=now - timedelta(days=100),
            event_type=JobEvent.EventType.START,
            run_id="still-running",
        )

        result = prune_monitor_history(
            now=now,
            check_retention_days=30,
            job_event_retention_days=90,
        )

        self.assertEqual(result.job_events_deleted, 1)
        self.assertFalse(JobEvent.objects.filter(pk=stale_log.pk).exists())
        self.assertTrue(JobEvent.objects.filter(pk=active_start.pk).exists())
        evaluation = evaluate_job_monitor(monitor, now)
        self.assertFalse(evaluation.success)
        self.assertIn("maximum runtime", evaluation.message)

    def test_recent_job_events_are_not_pruned(self):
        monitor = Monitor.objects.create(
            name="retention-recent-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
        )
        now = timezone.now()
        recent = JobEvent.objects.create(
            monitor=monitor,
            received_at=now - timedelta(days=1),
            event_type=JobEvent.EventType.LOG,
            message="recent",
        )
        result = prune_monitor_history(
            now=now,
            check_retention_days=30,
            job_event_retention_days=90,
        )
        self.assertEqual(result.job_events_deleted, 0)
        self.assertTrue(JobEvent.objects.filter(pk=recent.pk).exists())

    def test_retention_period_must_be_positive(self):
        with self.assertRaises(ValueError):
            prune_monitor_history(check_retention_days=0, job_event_retention_days=90)
        with self.assertRaises(ValueError):
            prune_monitor_history(check_retention_days=30, job_event_retention_days=0)


class WorkerRetentionIntegrationTests(TestCase):
    def test_runmonitor_once_invokes_history_pruning(self):
        fake_result = RetentionResult(check_results_deleted=0, job_events_deleted=0)
        with (
            patch(
                "monitoring.management.commands.runmonitor.prune_monitor_history",
                return_value=fake_result,
            ) as prune,
            patch(
                "monitoring.management.commands.runmonitor.run_batch",
                new=AsyncMock(),
            ) as run_batch,
        ):
            call_command("runmonitor", once=True, stdout=StringIO())

        prune.assert_called_once()
        run_batch.assert_awaited_once()

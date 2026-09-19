from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from asgiref.sync import sync_to_async
from django.test import TestCase
from django.utils import timezone

from monitoring.engine import CheckOutcome, _apply_outcome, check_dns, check_push, run_monitor
from monitoring.jobs import evaluate_job_monitor, record_job_event
from monitoring.models import CheckResult, Incident, JobEvent, Monitor, NotificationOutbox


class EngineStateTests(TestCase):
    def setUp(self):
        self.monitor = Monitor.objects.create(
            name="service",
            kind=Monitor.Kind.PUSH,
            interval_seconds=60,
            heartbeat_grace_seconds=30,
            failure_threshold=2,
            recovery_threshold=1,
        )

    def test_failure_threshold_opens_one_incident(self):
        now = timezone.now()
        _apply_outcome(self.monitor.id, CheckOutcome(False, Monitor.State.DOWN, None, "failure 1"), now)
        self.monitor.refresh_from_db()
        self.assertNotEqual(self.monitor.state, Monitor.State.DOWN)
        _apply_outcome(self.monitor.id, CheckOutcome(False, Monitor.State.DOWN, None, "failure 2"), now + timedelta(seconds=1))
        self.monitor.refresh_from_db()
        self.assertEqual(self.monitor.state, Monitor.State.DOWN)
        self.assertEqual(Incident.objects.filter(monitor=self.monitor, ended_at__isnull=True).count(), 1)

    def test_recovery_closes_incident(self):
        now = timezone.now()
        self.monitor.failure_threshold = 1
        self.monitor.save()
        _apply_outcome(self.monitor.id, CheckOutcome(False, Monitor.State.DOWN, None, "down"), now)
        _apply_outcome(self.monitor.id, CheckOutcome(True, Monitor.State.UP, None, "up"), now + timedelta(seconds=1))
        self.monitor.refresh_from_db()
        self.assertEqual(self.monitor.state, Monitor.State.UP)
        self.assertFalse(Incident.objects.filter(monitor=self.monitor, ended_at__isnull=True).exists())

    async def test_transition_persists_exact_notify_outbox_record(self):
        self.monitor.failure_threshold = 1
        await sync_to_async(self.monitor.save)()
        outcome = CheckOutcome(False, Monitor.State.DOWN, 12.5, "failure")
        with patch("monitoring.engine.perform_check", new=AsyncMock(return_value=outcome)):
            await run_monitor(self.monitor.id)

        check_result = await sync_to_async(CheckResult.objects.get)(monitor_id=self.monitor.id)
        outbox = await sync_to_async(NotificationOutbox.objects.get)()
        self.assertEqual(outbox.transition, "DOWN")
        self.assertEqual(outbox.payload["source"], "goreecloud-monitor")
        self.assertEqual(outbox.payload["channel"], "monitoring")
        self.assertIn("service", outbox.payload["body"])
        self.assertTrue(outbox.idempotency_key.startswith("gcm-v1-"))
        expected_transition_id = (
            f"check-result:{self.monitor.id}:{check_result.id}:{check_result.checked_at.isoformat()}"
        )
        from monitoring.notifications import create_notify_idempotency_key

        self.assertEqual(
            outbox.idempotency_key,
            create_notify_idempotency_key("DOWN", expected_transition_id),
        )


    async def test_push_monitor_detects_stale_heartbeat(self):
        self.monitor.last_heartbeat_at = timezone.now() - timedelta(seconds=100)
        outcome = await check_push(self.monitor)
        self.assertFalse(outcome.success)

    async def test_push_monitor_accepts_current_heartbeat(self):
        self.monitor.last_heartbeat_at = timezone.now()
        outcome = await check_push(self.monitor)
        self.assertTrue(outcome.success)


    def test_simple_scheduled_job_detects_missed_completion_after_grace(self):
        monitor = Monitor.objects.create(
            name="simple-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=60,
            job_grace_seconds=10,
        )
        completed_at = monitor.created_at + timedelta(seconds=5)
        record_job_event(monitor.id, JobEvent.EventType.SUCCESS, received_at=completed_at)
        outcome = evaluate_job_monitor(monitor, completed_at + timedelta(seconds=71))
        self.assertFalse(outcome.success)
        self.assertEqual(outcome.observed_state, Monitor.State.DOWN)

    def test_cron_scheduled_job_accepts_completion_in_current_window(self):
        monitor = Monitor.objects.create(
            name="cron-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=60,
            job_schedule_mode=Monitor.JobScheduleMode.CRON,
            job_cron_expression="*/5 * * * *",
            job_timezone="UTC",
            job_grace_seconds=60,
        )
        Monitor.objects.filter(pk=monitor.pk).update(
            created_at=datetime(2026, 9, 19, 12, 0, 0, tzinfo=UTC)
        )
        monitor.refresh_from_db()
        completed_at = datetime(2026, 9, 19, 12, 5, 20, tzinfo=UTC)
        record_job_event(monitor.id, JobEvent.EventType.SUCCESS, received_at=completed_at)
        outcome = evaluate_job_monitor(
            monitor,
            datetime(2026, 9, 19, 12, 5, 30, tzinfo=UTC),
        )
        self.assertTrue(outcome.success)
        self.assertEqual(outcome.observed_state, Monitor.State.UP)

    def test_new_cron_monitor_does_not_inherit_pre_creation_missed_window(self):
        monitor = Monitor.objects.create(
            name="cron-new",
            kind=Monitor.Kind.JOB,
            interval_seconds=60,
            job_schedule_mode=Monitor.JobScheduleMode.CRON,
            job_cron_expression="*/5 * * * *",
            job_timezone="UTC",
            job_grace_seconds=60,
        )
        Monitor.objects.filter(pk=monitor.pk).update(
            created_at=datetime(2026, 9, 19, 12, 3, 0, tzinfo=UTC)
        )
        monitor.refresh_from_db()
        outcome = evaluate_job_monitor(
            monitor,
            datetime(2026, 9, 19, 12, 3, 30, tzinfo=UTC),
        )
        self.assertTrue(outcome.success)
        self.assertEqual(outcome.observed_state, Monitor.State.UNKNOWN)
        self.assertIn("first scheduled job window", outcome.message)

    def test_cron_scheduled_job_detects_missed_window(self):
        monitor = Monitor.objects.create(
            name="cron-missed",
            kind=Monitor.Kind.JOB,
            interval_seconds=60,
            job_schedule_mode=Monitor.JobScheduleMode.CRON,
            job_cron_expression="*/5 * * * *",
            job_timezone="UTC",
            job_grace_seconds=60,
        )
        Monitor.objects.filter(pk=monitor.pk).update(
            created_at=datetime(2026, 9, 19, 12, 0, 0, tzinfo=UTC)
        )
        monitor.refresh_from_db()
        outcome = evaluate_job_monitor(
            monitor,
            datetime(2026, 9, 19, 12, 6, 5, tzinfo=UTC),
        )
        self.assertFalse(outcome.success)
        self.assertEqual(outcome.observed_state, Monitor.State.DOWN)

    def test_job_evaluation_is_not_confused_by_high_log_volume(self):
        monitor = Monitor.objects.create(
            name="log-heavy-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
            job_grace_seconds=60,
        )
        completed_at = timezone.now()
        record_job_event(
            monitor.id,
            JobEvent.EventType.SUCCESS,
            run_id="log-heavy-run",
            received_at=completed_at,
        )
        JobEvent.objects.bulk_create(
            [
                JobEvent(
                    monitor=monitor,
                    event_type=JobEvent.EventType.LOG,
                    run_id="log-heavy-run",
                    received_at=completed_at + timedelta(milliseconds=index + 1),
                    message=f"log line {index}",
                )
                for index in range(250)
            ]
        )
        outcome = evaluate_job_monitor(monitor, completed_at + timedelta(seconds=30))
        self.assertTrue(outcome.success)
        self.assertEqual(outcome.observed_state, Monitor.State.UP)

    def test_scheduled_job_detects_runtime_overrun(self):
        monitor = Monitor.objects.create(
            name="long-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
            job_max_runtime_seconds=60,
        )
        started_at = timezone.now() - timedelta(seconds=61)
        record_job_event(
            monitor.id,
            JobEvent.EventType.START,
            run_id="run-overrun",
            received_at=started_at,
        )
        outcome = evaluate_job_monitor(monitor, started_at + timedelta(seconds=61))
        self.assertFalse(outcome.success)
        self.assertIn("maximum runtime", outcome.message)

    def test_started_job_without_explicit_max_runtime_uses_grace_limit(self):
        monitor = Monitor.objects.create(
            name="grace-limited-running-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
            job_grace_seconds=30,
            job_max_runtime_seconds=0,
        )
        started_at = timezone.now() - timedelta(seconds=31)
        record_job_event(
            monitor.id,
            JobEvent.EventType.START,
            run_id="grace-run",
            received_at=started_at,
        )
        outcome = evaluate_job_monitor(monitor, started_at + timedelta(seconds=31))
        self.assertFalse(outcome.success)
        self.assertEqual(outcome.observed_state, Monitor.State.DOWN)
        self.assertIn("grace runtime", outcome.message)

    async def test_job_monitor_failure_enters_existing_incident_pipeline(self):
        monitor = await sync_to_async(Monitor.objects.create)(
            name="failed-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=60,
            failure_threshold=1,
        )
        await sync_to_async(record_job_event)(
            monitor.id,
            JobEvent.EventType.FAILURE,
            run_id="run-failed",
            exit_code=2,
        )
        await run_monitor(monitor.id)
        await sync_to_async(monitor.refresh_from_db)()
        self.assertEqual(monitor.state, Monitor.State.DOWN)
        self.assertTrue(
            await sync_to_async(
                Incident.objects.filter(monitor=monitor, ended_at__isnull=True).exists
            )()
        )

    async def test_dns_monitor_uses_validated_explicit_resolver(self):
        monitor = Monitor(
            name="resolver-specific",
            kind=Monitor.Kind.DNS,
            target="dns://1.1.1.1/example.test",
            dns_record_type="A",
            expected_dns_answer="203.0.113.10",
            interval_seconds=60,
            timeout_seconds=10,
        )
        resolver = MagicMock()
        resolver.resolve = AsyncMock(return_value=["203.0.113.10"])
        with (
            patch("monitoring.engine.resolve_and_validate_network_target", new=AsyncMock(return_value=["1.1.1.1"])) as validate,
            patch("monitoring.engine.dns.asyncresolver.Resolver", return_value=resolver) as resolver_factory,
        ):
            outcome = await check_dns(monitor)

        self.assertTrue(outcome.success)
        validate.assert_awaited_once_with("1.1.1.1", 53)
        resolver_factory.assert_called_once_with(configure=False)
        self.assertEqual(resolver.nameservers, ["1.1.1.1"])
        self.assertEqual(resolver.port, 53)
        self.assertEqual(resolver.lifetime, 10.0)
        resolver.resolve.assert_awaited_once_with("example.test", "A")

    async def test_dns_monitor_keeps_system_resolver_for_plain_target(self):
        monitor = Monitor(
            name="system-resolver",
            kind=Monitor.Kind.DNS,
            target="example.test",
            dns_record_type="AAAA",
            interval_seconds=60,
            timeout_seconds=10,
        )
        resolver = MagicMock()
        resolver.resolve = AsyncMock(return_value=["2001:db8::10"])
        with (
            patch("monitoring.engine.resolve_and_validate_network_target", new=AsyncMock()) as validate,
            patch("monitoring.engine.dns.asyncresolver.Resolver", return_value=resolver) as resolver_factory,
        ):
            outcome = await check_dns(monitor)

        self.assertTrue(outcome.success)
        validate.assert_not_awaited()
        resolver_factory.assert_called_once_with()
        resolver.resolve.assert_awaited_once_with("example.test", "AAAA")

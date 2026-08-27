from __future__ import annotations

import json
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase

from monitoring.models import Monitor
from monitoring.parallel import evaluate_parallel_series, normalize_kuma_snapshot


def _comparison_report(*results):
    statuses = (
        "match",
        "state-different",
        "latency-different",
        "missing",
        "monitor-only",
        "source-unknown",
        "source-duplicate",
        "source-invalid",
    )
    monitors = [{"name": name, "status": status} for name, status in results]
    summary = {status: sum(1 for item in monitors if item["status"] == status) for status in statuses}
    summary["compared"] = len(monitors)
    return {
        "schema": "goreecloud-monitor-uptime-kuma-runtime-comparison",
        "version": 1,
        "latency_tolerance_ms": 250.0,
        "summary": summary,
        "monitors": monitors,
    }


class KumaRuntimeNormalizationTests(SimpleTestCase):
    def test_status_mapping_matches_kuma_cli_semantics(self):
        self.assertEqual(normalize_kuma_snapshot({"name": "down", "active": True, "heartbeat": {"status": 0}}).state, Monitor.State.DOWN)
        self.assertEqual(normalize_kuma_snapshot({"name": "up", "active": True, "heartbeat": {"status": 1}}).state, Monitor.State.UP)
        self.assertEqual(normalize_kuma_snapshot({"name": "pending", "active": True}).state, Monitor.State.UNKNOWN)
        self.assertEqual(normalize_kuma_snapshot({"name": "maintenance", "active": True, "heartbeat": {"status": 3}}).state, Monitor.State.MAINTENANCE)
        self.assertEqual(normalize_kuma_snapshot({"name": "paused", "active": False, "heartbeat": {"status": 1}}).state, Monitor.State.PAUSED)

    def test_unknown_heartbeat_status_is_not_claimed_equivalent(self):
        snapshot = normalize_kuma_snapshot({"name": "future", "active": True, "heartbeat": {"status": 99, "ping": 10}})
        self.assertEqual(snapshot.state, Monitor.State.UNKNOWN)
        self.assertFalse(snapshot.status_known)


class ParallelSeriesEvaluationTests(SimpleTestCase):
    def test_three_complete_parity_observations_are_ready(self):
        reports = [
            _comparison_report(("A", "match"), ("B", "match")),
            _comparison_report(("A", "match"), ("B", "match")),
            _comparison_report(("A", "match"), ("B", "match")),
        ]
        result = evaluate_parallel_series(reports)
        self.assertTrue(result["ready"])
        self.assertEqual(result["summary"]["parity_observations"], 3)
        self.assertEqual(result["summary"]["monitor_count"], 2)
        self.assertEqual(result["blockers"], [])

    def test_insufficient_observations_fail_closed(self):
        result = evaluate_parallel_series([_comparison_report(("A", "match"))], minimum_observations=3)
        self.assertFalse(result["ready"])
        self.assertIn("insufficient observations", result["blockers"][0])

    def test_non_parity_status_blocks_acceptance(self):
        reports = [
            _comparison_report(("A", "match")),
            _comparison_report(("A", "state-different")),
            _comparison_report(("A", "match")),
        ]
        result = evaluate_parallel_series(reports)
        self.assertFalse(result["ready"])
        self.assertEqual(result["summary"]["status_totals"]["state-different"], 1)
        self.assertTrue(any("non-parity" in blocker for blocker in result["blockers"]))

    def test_coverage_drift_blocks_acceptance(self):
        reports = [
            _comparison_report(("A", "match"), ("B", "match")),
            _comparison_report(("A", "match")),
            _comparison_report(("A", "match"), ("B", "match")),
        ]
        result = evaluate_parallel_series(reports)
        self.assertFalse(result["ready"])
        self.assertEqual(result["summary"]["coverage_drift_observations"], 1)
        self.assertTrue(any("coverage drift" in blocker for blocker in result["blockers"]))

    def test_unsupported_schema_is_rejected(self):
        report = _comparison_report(("A", "match"))
        report["version"] = 99
        with self.assertRaisesRegex(ValueError, "unsupported comparison schema"):
            evaluate_parallel_series([report], minimum_observations=1)


class ParallelSeriesCommandTests(SimpleTestCase):
    def test_command_reads_multiple_reports_and_can_require_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index in range(3):
                path = Path(directory) / f"comparison-{index}.json"
                path.write_text(json.dumps(_comparison_report(("A", "match"))), encoding="utf-8")
                paths.append(str(path))

            out = StringIO()
            call_command("assessparallel", *paths, json=True, require_ready=True, stdout=out)
            report = json.loads(out.getvalue())
            self.assertTrue(report["ready"])
            self.assertEqual(report["observation_count"], 3)

    def test_command_exits_nonzero_when_readiness_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "comparison.json"
            path.write_text(json.dumps(_comparison_report(("A", "state-different"))), encoding="utf-8")
            with self.assertRaisesRegex(CommandError, "acceptance criteria"):
                call_command("assessparallel", str(path), require_ready=True, minimum_observations=1)


class KumaRuntimeComparisonCommandTests(TestCase):
    def _snapshot(self, items) -> tuple[tempfile.TemporaryDirectory, Path]:
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / "kuma-live.json"
        path.write_text(json.dumps({"ok": True, "data": items}), encoding="utf-8")
        return tmp, path

    def _run_json(self, items, *, tolerance=250.0):
        tmp, path = self._snapshot(items)
        out = StringIO()
        try:
            call_command(
                "compareuptimestate",
                str(path),
                json=True,
                latency_tolerance_ms=tolerance,
                stdout=out,
            )
        finally:
            tmp.cleanup()
        return json.loads(out.getvalue())

    def test_matching_state_and_latency_are_reported(self):
        Monitor.objects.create(
            name="homepage",
            kind=Monitor.Kind.HTTPS,
            target="https://example.test/",
            state=Monitor.State.UP,
            response_time_ms=120.0,
        )
        report = self._run_json(
            [{"name": "homepage", "type": "http", "active": True, "heartbeat": {"status": 1, "ping": 100}}],
            tolerance=50,
        )
        self.assertEqual(report["summary"]["match"], 1)
        self.assertEqual(report["monitors"][0]["latency_delta_ms"], 20.0)
        self.assertTrue(report["monitors"][0]["latency_within_tolerance"])

    def test_state_difference_is_reported(self):
        Monitor.objects.create(name="homepage", kind=Monitor.Kind.PUSH, state=Monitor.State.DOWN)
        report = self._run_json(
            [{"name": "homepage", "type": "push", "active": True, "heartbeat": {"status": 1, "ping": None}}]
        )
        self.assertEqual(report["summary"]["state-different"], 1)
        self.assertEqual(report["monitors"][0]["source_state"], Monitor.State.UP)
        self.assertEqual(report["monitors"][0]["monitor_state"], Monitor.State.DOWN)

    def test_latency_difference_is_reported_separately(self):
        Monitor.objects.create(
            name="homepage",
            kind=Monitor.Kind.HTTPS,
            target="https://example.test/",
            state=Monitor.State.UP,
            response_time_ms=700.0,
        )
        report = self._run_json(
            [{"name": "homepage", "type": "http", "active": True, "heartbeat": {"status": 1, "ping": 100}}],
            tolerance=100,
        )
        self.assertEqual(report["summary"]["latency-different"], 1)
        self.assertFalse(report["monitors"][0]["latency_within_tolerance"])

    def test_missing_monitor_only_and_duplicate_source_are_explicit(self):
        Monitor.objects.create(name="monitor-only", kind=Monitor.Kind.PUSH, state=Monitor.State.UNKNOWN)
        report = self._run_json(
            [
                {"name": "missing", "type": "http", "active": True, "heartbeat": {"status": 1, "ping": 10}},
                {"name": "duplicate", "type": "http", "active": True, "heartbeat": {"status": 1, "ping": 10}},
                {"name": "duplicate", "type": "http", "active": True, "heartbeat": {"status": 0, "ping": 20}},
            ]
        )
        self.assertEqual(report["summary"]["missing"], 1)
        self.assertEqual(report["summary"]["monitor-only"], 1)
        self.assertEqual(report["summary"]["source-duplicate"], 2)

    def test_report_contains_no_source_target_or_notification_configuration(self):
        Monitor.objects.create(name="private", kind=Monitor.Kind.PUSH, state=Monitor.State.UP)
        report = self._run_json(
            [
                {
                    "name": "private",
                    "type": "http",
                    "url": "https://secret-target.example.test/path",
                    "headers": '{"Authorization":"Bearer secret-value"}',
                    "notificationIDList": {"1": True},
                    "active": True,
                    "heartbeat": {"status": 1, "ping": 5},
                }
            ]
        )
        serialized = json.dumps(report)
        self.assertNotIn("secret-target", serialized)
        self.assertNotIn("secret-value", serialized)
        self.assertNotIn("notificationIDList", serialized)

from __future__ import annotations

import json
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from monitoring.models import Monitor
from monitoring.parallel import normalize_kuma_snapshot


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

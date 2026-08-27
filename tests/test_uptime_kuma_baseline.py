from __future__ import annotations

import json
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from monitoring.management.commands.reconcileuptimebaseline import DEFAULT_BASELINE, load_baseline, reconcile


def baseline(*items):
    return {
        "schema": "goreecloud-monitor-documented-uptime-kuma-baseline",
        "version": 1,
        "basis": {"authority": "test"},
        "monitors": list(items),
    }


class BaselineReconciliationTests(SimpleTestCase):
    def test_exact_supported_baseline_is_ready(self):
        report = reconcile(
            [{"name": "Web", "type": "http", "url": "https://example.test/", "interval": 60, "timeout": 10, "maxredirects": 5, "accepted_statuscodes": ["200"]}],
            baseline({"name": "Web", "expected": "active", "cutover_gate": "none"}),
        )
        self.assertTrue(report["ready"])
        self.assertEqual(report["summary"]["matched"], 1)

    def test_missing_unexpected_and_retired_live_are_blockers(self):
        report = reconcile(
            [
                {"name": "Retired", "type": "http", "url": "https://retired.test/", "interval": 60, "timeout": 10},
                {"name": "New", "type": "http", "url": "https://new.test/", "interval": 60, "timeout": 10},
            ],
            baseline(
                {"name": "Expected", "expected": "active", "cutover_gate": "none"},
                {"name": "Retired", "expected": "retired", "cutover_gate": "none"},
            ),
        )
        self.assertFalse(report["ready"])
        statuses = {item["status"] for item in report["monitors"]}
        self.assertTrue({"retired-present", "unexpected-live", "expected-missing"}.issubset(statuses))

    def test_documented_ping_review_remains_blocking_until_live_validation(self):
        report = reconcile(
            [{"name": "Ping", "type": "ping", "hostname": "100.64.0.1", "interval": 60, "timeout": 10}],
            baseline({"name": "Ping", "expected": "active", "cutover_gate": "review", "reason": "live ICMP validation required"}),
        )
        self.assertFalse(report["ready"])
        self.assertEqual(report["monitors"][0]["status"], "review")
        self.assertNotIn("100.64.0.1", json.dumps(report))

    def test_documented_review_must_be_resolved(self):
        report = reconcile(
            [{"name": "DNS", "type": "dns", "hostname": "example.test", "dns_resolve_type": "A", "interval": 60, "timeout": 10}],
            baseline({"name": "DNS", "expected": "active", "cutover_gate": "review", "reason": "resolver semantics"}),
        )
        self.assertFalse(report["ready"])
        self.assertEqual(report["monitors"][0]["status"], "review")

    def test_documented_baseline_tracks_current_approved_scope(self):
        documented = load_baseline(DEFAULT_BASELINE)
        active = {item["name"] for item in documented["monitors"] if item.get("expected") == "active"}
        retired = {item["name"] for item in documented["monitors"] if item.get("expected") == "retired"}

        self.assertEqual(documented["basis"]["live_source_monitor_count"], 23)
        self.assertEqual(len(active), 22)
        self.assertEqual(retired, {"Flatnotes", "Linkding", "Termix"})
        self.assertNotIn("GoreeCloud Research Library", active)
        self.assertIn("GoreeCloud Memos", active)
        self.assertIn("GoreeCloud VPS", active)
        self.assertNotIn("GoreeCloud VPS Ping", active)

    def test_command_json_is_sanitized_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            baseline_path = root / "baseline.json"
            export_path = root / "export.json"
            baseline_path.write_text(
                json.dumps(baseline({"name": "Private", "expected": "active", "cutover_gate": "none"})),
                encoding="utf-8",
            )
            export_path.write_text(
                json.dumps({
                    "version": "1",
                    "monitors": [{
                        "name": "Private",
                        "type": "http",
                        "url": "https://secret-target.example.test/private",
                        "interval": 60,
                        "timeout": 10,
                        "bearer_token": "reusable-secret",
                    }],
                }),
                encoding="utf-8",
            )
            output = StringIO()
            with self.assertRaises(CommandError):
                call_command(
                    "reconcileuptimebaseline",
                    str(export_path),
                    baseline=str(baseline_path),
                    json=True,
                    stdout=output,
                )
            serialized = output.getvalue()
            self.assertNotIn("secret-target", serialized)
            self.assertNotIn("reusable-secret", serialized)
            self.assertIn("manual-authentication-required", serialized)

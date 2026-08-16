from __future__ import annotations

import json
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase

from monitoring.migration import load_kuma_monitors, map_kuma_monitor
from monitoring.models import Monitor


class UptimeKumaMappingTests(SimpleTestCase):
    def test_https_monitor_maps_without_activation_state(self):
        mapping = map_kuma_monitor(
            {
                "name": "homepage",
                "type": "http",
                "url": "https://homepage.example.test/healthz",
                "method": "GET",
                "interval": 60,
                "timeout": 10,
                "maxretries": 1,
                "retryInterval": 20,
                "maxredirects": 5,
                "accepted_statuscodes": ["200"],
            }
        )
        self.assertTrue(mapping.supported)
        self.assertEqual(mapping.values["kind"], Monitor.Kind.HTTPS)
        self.assertEqual(mapping.values["target"], "https://homepage.example.test/healthz")
        self.assertEqual(mapping.values["failure_threshold"], 2)
        self.assertNotIn("enabled", mapping.values)

    def test_keyword_maps_to_body_assertion(self):
        mapping = map_kuma_monitor(
            {
                "name": "keyword",
                "type": "keyword",
                "url": "https://example.test/",
                "keyword": "healthy",
                "interval": 60,
                "timeout": 10,
                "maxredirects": 5,
            }
        )
        self.assertTrue(mapping.supported)
        self.assertEqual(mapping.values["expected_body_text"], "healthy")

    def test_simple_json_query_maps_to_native_assertion(self):
        mapping = map_kuma_monitor(
            {
                "name": "json",
                "type": "json-query",
                "url": "https://example.test/health",
                "jsonPath": "$.status.value",
                "jsonPathOperator": "==",
                "expectedValue": "ok",
                "interval": 60,
                "timeout": 10,
            }
        )
        self.assertTrue(mapping.supported)
        self.assertEqual(mapping.values["expected_json_path"], "status.value")
        self.assertEqual(mapping.values["expected_json_value"], "ok")

    def test_complex_json_query_is_blocked(self):
        mapping = map_kuma_monitor(
            {
                "name": "json",
                "type": "json-query",
                "url": "https://example.test/health",
                "jsonPath": "$.items[0].status",
                "jsonPathOperator": "==",
                "expectedValue": "ok",
                "interval": 60,
                "timeout": 10,
            }
        )
        self.assertFalse(mapping.supported)
        self.assertIn("json-path", {issue.code for issue in mapping.issues})

    def test_sensitive_monitor_configuration_is_never_migrated(self):
        mapping = map_kuma_monitor(
            {
                "name": "authenticated",
                "type": "http",
                "url": "https://example.test/private",
                "interval": 60,
                "timeout": 10,
                "basic_auth_pass": "do-not-copy",
            }
        )
        self.assertFalse(mapping.supported)
        self.assertIn("manual-authentication-required", {issue.code for issue in mapping.issues})
        report = mapping.to_report()
        self.assertNotIn("do-not-copy", json.dumps(report))

    def test_tls_verification_bypass_is_blocked(self):
        mapping = map_kuma_monitor(
            {
                "name": "weak-tls",
                "type": "http",
                "url": "https://example.test/",
                "interval": 60,
                "timeout": 10,
                "ignoreTls": True,
            }
        )
        self.assertFalse(mapping.supported)
        self.assertIn("tls-verification-disabled", {issue.code for issue in mapping.issues})

    def test_tcp_dns_and_push_types_map(self):
        tcp = map_kuma_monitor(
            {"name": "tcp", "type": "port", "hostname": "service.example.test", "port": 443, "interval": 60, "timeout": 10}
        )
        dns = map_kuma_monitor(
            {"name": "dns", "type": "dns", "hostname": "service.example.test", "dns_resolve_type": "AAAA", "interval": 60, "timeout": 10}
        )
        push = map_kuma_monitor({"name": "push", "type": "push", "interval": 60, "timeout": 10})
        self.assertTrue(tcp.supported)
        self.assertEqual(tcp.values["kind"], Monitor.Kind.TCP)
        self.assertTrue(dns.supported)
        self.assertEqual(dns.values["dns_record_type"], "AAAA")
        self.assertTrue(push.supported)
        self.assertEqual(push.values["kind"], Monitor.Kind.PUSH)
        self.assertIn("push-token-rotated", {issue.code for issue in push.issues})

    def test_unknown_monitor_type_is_reported_not_guessed(self):
        mapping = map_kuma_monitor({"name": "browser", "type": "real-browser", "interval": 60, "timeout": 10})
        self.assertFalse(mapping.supported)
        self.assertIn("unsupported-type", {issue.code for issue in mapping.issues})


class UptimeKumaImportCommandTests(TestCase):
    def _write(self, document) -> tuple[tempfile.TemporaryDirectory, Path]:
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / "kuma.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return tmp, path

    def test_loader_accepts_kuma_cli_config_export_and_json_wrapper(self):
        document = {
            "ok": True,
            "data": {
                "version": "1",
                "monitors": [{"name": "push", "type": "push", "interval": 60, "timeout": 10}],
                "notifications": [],
            },
        }
        tmp, path = self._write(document)
        try:
            monitors, metadata = load_kuma_monitors(path)
        finally:
            tmp.cleanup()
        self.assertEqual(len(monitors), 1)
        self.assertEqual(metadata["source_format"], "kuma-cli-config-export")
        self.assertTrue(metadata["wrapped_json_output"])

    def test_import_defaults_to_paused_and_generates_new_push_token(self):
        document = {
            "version": "1",
            "monitors": [
                {
                    "name": "homepage",
                    "type": "http",
                    "url": "https://example.test/health",
                    "interval": 60,
                    "timeout": 10,
                    "maxredirects": 5,
                    "accepted_statuscodes": ["200"],
                }
            ],
            "notifications": [],
        }
        tmp, path = self._write(document)
        try:
            call_command("importuptimekuma", str(path), stdout=StringIO())
        finally:
            tmp.cleanup()
        monitor = Monitor.objects.get(name="homepage")
        self.assertFalse(monitor.enabled)
        self.assertEqual(monitor.state, Monitor.State.PAUSED)
        self.assertTrue(monitor.heartbeat_token)

    def test_import_is_atomic_when_unsupported_monitor_exists(self):
        document = {
            "version": "1",
            "monitors": [
                {"name": "supported", "type": "push", "interval": 60, "timeout": 10},
                {"name": "unsupported", "type": "ping", "hostname": "example.test", "interval": 60, "timeout": 10},
            ],
        }
        tmp, path = self._write(document)
        try:
            with self.assertRaises(CommandError):
                call_command("importuptimekuma", str(path), stdout=StringIO())
        finally:
            tmp.cleanup()
        self.assertEqual(Monitor.objects.count(), 0)

    def test_allow_partial_imports_only_supported_definitions(self):
        document = {
            "version": "1",
            "monitors": [
                {
                    "name": "supported",
                    "type": "http",
                    "url": "https://example.test/",
                    "interval": 60,
                    "timeout": 10,
                    "maxredirects": 5,
                    "accepted_statuscodes": ["200"],
                },
                {"name": "unsupported", "type": "ping", "hostname": "example.test", "interval": 60, "timeout": 10},
            ],
        }
        tmp, path = self._write(document)
        try:
            call_command("importuptimekuma", str(path), allow_partial=True, stdout=StringIO())
        finally:
            tmp.cleanup()
        self.assertEqual(list(Monitor.objects.values_list("name", flat=True)), ["supported"])

    def test_dry_run_leaves_database_empty(self):
        document = {
            "version": "1",
            "monitors": [
                {
                    "name": "homepage",
                    "type": "http",
                    "url": "https://example.test/",
                    "interval": 60,
                    "timeout": 10,
                    "maxredirects": 5,
                    "accepted_statuscodes": ["200"],
                }
            ],
        }
        tmp, path = self._write(document)
        try:
            call_command("importuptimekuma", str(path), dry_run=True, stdout=StringIO())
        finally:
            tmp.cleanup()
        self.assertEqual(Monitor.objects.count(), 0)

    def test_activate_refuses_definitions_with_migration_warnings(self):
        document = {
            "version": "1",
            "monitors": [
                {
                    "name": "homepage",
                    "type": "http",
                    "url": "https://example.test/",
                    "interval": 60,
                    "timeout": 10,
                    "maxredirects": 10,
                    "accepted_statuscodes": ["200-299"],
                }
            ],
        }
        tmp, path = self._write(document)
        try:
            with self.assertRaises(CommandError):
                call_command("importuptimekuma", str(path), activate=True, stdout=StringIO())
        finally:
            tmp.cleanup()
        self.assertEqual(Monitor.objects.count(), 0)

    def test_import_refuses_non_empty_monitor_target(self):
        Monitor.objects.create(name="existing", kind=Monitor.Kind.PUSH, interval_seconds=60)
        document = {"version": "1", "monitors": []}
        tmp, path = self._write(document)
        try:
            with self.assertRaises(CommandError):
                call_command("importuptimekuma", str(path), stdout=StringIO())
        finally:
            tmp.cleanup()

    def test_compare_reports_match_and_difference_without_secrets(self):
        Monitor.objects.create(
            name="homepage",
            kind=Monitor.Kind.HTTPS,
            target="https://example.test/",
            interval_seconds=60,
            timeout_seconds=10,
            failure_threshold=1,
            expected_status_code=200,
        )
        document = {
            "version": "1",
            "monitors": [
                {
                    "name": "homepage",
                    "type": "http",
                    "url": "https://example.test/",
                    "interval": 60,
                    "timeout": 10,
                    "maxredirects": 5,
                    "accepted_statuscodes": ["200"],
                }
            ],
        }
        tmp, path = self._write(document)
        out = StringIO()
        try:
            call_command("compareuptimekuma", str(path), json=True, stdout=out)
        finally:
            tmp.cleanup()
        report = json.loads(out.getvalue())
        self.assertEqual(report["summary"]["match"], 1)
        self.assertEqual(report["summary"]["different"], 0)

    def test_audit_json_report_excludes_source_secret_values(self):
        document = {
            "version": "1",
            "monitors": [
                {
                    "name": "private",
                    "type": "http",
                    "url": "https://example.test/private",
                    "interval": 60,
                    "timeout": 10,
                    "bearer_token": "very-secret-token",
                }
            ],
        }
        tmp, path = self._write(document)
        out = StringIO()
        try:
            call_command("audituptimekuma", str(path), json=True, stdout=out)
        finally:
            tmp.cleanup()
        self.assertNotIn("very-secret-token", out.getvalue())
        report = json.loads(out.getvalue())
        self.assertEqual(report["summary"]["unsupported"], 1)

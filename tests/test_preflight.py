from __future__ import annotations

import json
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from monitoring.preflight import configuration_findings, runtime_findings
from monitoring.models import Monitor

SAFE_SETTINGS = {
    "DEBUG": False, "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}}, "ALLOWED_HOSTS": ["monitor.example.test"],
    "SECRET_KEY": "Monitor-ci-preflight-key-2026-abcdefghijklmnopqrstuvwxyz-0123456789", "SECURE_SSL_REDIRECT": True, "SECURE_HSTS_SECONDS": 31536000,
    "SESSION_COOKIE_SECURE": True, "SESSION_COOKIE_HTTPONLY": True, "SESSION_COOKIE_SAMESITE": "Lax",
    "CSRF_COOKIE_SECURE": True, "CSRF_COOKIE_SAMESITE": "Lax", "X_FRAME_OPTIONS": "DENY", "SECURE_CROSS_ORIGIN_OPENER_POLICY": "same-origin",
    "MONITOR_CONTENT_SECURITY_POLICY": "default-src 'self'; object-src 'none'", "MONITOR_PERMISSIONS_POLICY": "camera=(), microphone=()",
    "MONITOR_ALLOWED_NETWORKS": ["10.20.30.0/24", "fd00:1234::/64"], "MONITOR_ALLOW_LEGACY_PATH_HEARTBEATS": False,
    "NTFY_BASE_URL": "http://ntfy:80", "NTFY_TOPIC": "goreecloud-uptime", "NTFY_TOKEN": "protected-test-token", "MANAGER_API_TOKEN": "manager-test-token",
}

class PreflightConfigurationTests(SimpleTestCase):
    @override_settings(**SAFE_SETTINGS)
    def test_safe_configuration_has_no_errors(self): self.assertEqual([f for f in configuration_findings() if f.severity == "error"], [])
    @override_settings(**{**SAFE_SETTINGS, "DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3"}}})
    def test_non_postgresql_database_is_blocking(self): self.assertIn("database-engine", {f.code for f in configuration_findings() if f.severity == "error"})
    @override_settings(**{**SAFE_SETTINGS, "DEBUG": True})
    def test_debug_is_blocking(self): self.assertIn("debug-enabled", {f.code for f in configuration_findings() if f.severity == "error"})
    @override_settings(**{**SAFE_SETTINGS, "ALLOWED_HOSTS": ["*"]})
    def test_wildcard_host_is_blocking(self): self.assertIn("allowed-hosts-wildcard", {f.code for f in configuration_findings() if f.severity == "error"})
    @override_settings(**{**SAFE_SETTINGS, "SECRET_KEY": "short-but-diverse"})
    def test_short_secret_key_is_blocking(self): self.assertIn("secret-key", {f.code for f in configuration_findings() if f.severity == "error"})
    @override_settings(**{**SAFE_SETTINGS, "SECRET_KEY": "x" * 64})
    def test_low_diversity_secret_key_is_blocking(self): self.assertIn("secret-key", {f.code for f in configuration_findings() if f.severity == "error"})
    @override_settings(**{**SAFE_SETTINGS, "SECRET_KEY": "django-insecure-abcdefghijklmnopqrstuvwxyz-0123456789-ABCDEFGHIJ"})
    def test_django_insecure_secret_key_is_blocking(self): self.assertIn("secret-key", {f.code for f in configuration_findings() if f.severity == "error"})
    @override_settings(**{**SAFE_SETTINGS, "MONITOR_ALLOWED_NETWORKS": ["0.0.0.0/0"]})
    def test_all_addresses_target_allowlist_is_blocking(self): self.assertIn("allowed-network-broad", {f.code for f in configuration_findings() if f.severity == "error"})
    @override_settings(**{**SAFE_SETTINGS, "NTFY_TOKEN": ""})
    def test_partial_ntfy_configuration_is_blocking(self): self.assertIn("ntfy-partial", {f.code for f in configuration_findings() if f.severity == "error"})
    @override_settings(**{**SAFE_SETTINGS, "SECURE_HSTS_SECONDS": 0})
    def test_hsts_is_blocking_for_target_acceptance(self): self.assertIn("hsts", {f.code for f in configuration_findings() if f.severity == "error"})
    @override_settings(**{**SAFE_SETTINGS, "SESSION_COOKIE_SAMESITE": None})
    def test_missing_session_samesite_is_blocking(self): self.assertIn("session-cookie-samesite", {f.code for f in configuration_findings() if f.severity == "error"})
    @override_settings(**{**SAFE_SETTINGS, "MONITOR_CONTENT_SECURITY_POLICY": ""})
    def test_missing_content_security_policy_is_blocking(self): self.assertIn("content-security-policy", {f.code for f in configuration_findings() if f.severity == "error"})
    @override_settings(**{**SAFE_SETTINGS, "MONITOR_ALLOW_LEGACY_PATH_HEARTBEATS": True})
    def test_legacy_path_heartbeat_is_blocking(self): self.assertIn("legacy-path-heartbeat", {f.code for f in configuration_findings() if f.severity == "error"})

class RuntimePreflightTests(TestCase):
    def test_legacy_plaintext_push_credential_is_blocking(self):
        monitor = Monitor.objects.create(name="legacy", kind=Monitor.Kind.PUSH, interval_seconds=60)
        Monitor.objects.filter(pk=monitor.pk).update(heartbeat_token="legacy-reusable-secret")
        codes = {finding.code for finding in runtime_findings() if finding.severity == "error"}
        self.assertIn("legacy-heartbeat-verifier", codes)

class PreflightCommandTests(TestCase):
    def test_insecure_ci_configuration_fails_closed_without_secrets_in_report(self):
        out = StringIO()
        with self.assertRaises(CommandError): call_command("targetpreflight", json=True, stdout=out)
        report = json.loads(out.getvalue())
        self.assertFalse(report["ready"])
        self.assertTrue({"debug-enabled", "secret-key", "https-redirect"} & {f["code"] for f in report["findings"]})
        serialized = json.dumps(report)
        self.assertNotIn("ci-only", serialized); self.assertNotIn("ci-postgres-password", serialized); self.assertNotIn("POSTGRES_PASSWORD", serialized)

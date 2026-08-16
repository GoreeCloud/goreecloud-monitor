from __future__ import annotations

import json
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from monitoring.preflight import configuration_findings


SAFE_SETTINGS = {
    "DEBUG": False,
    "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
    "ALLOWED_HOSTS": ["monitor.example.test"],
    "SECRET_KEY": "x" * 64,
    "SECURE_SSL_REDIRECT": True,
    "SESSION_COOKIE_SECURE": True,
    "CSRF_COOKIE_SECURE": True,
    "MONITOR_ALLOWED_NETWORKS": ["10.20.30.0/24", "fd00:1234::/64"],
    "NTFY_BASE_URL": "http://ntfy:80",
    "NTFY_TOPIC": "goreecloud-uptime",
    "NTFY_TOKEN": "protected-test-token",
    "MANAGER_API_TOKEN": "manager-test-token",
    "SECURE_HSTS_SECONDS": 31536000,
}


class PreflightConfigurationTests(SimpleTestCase):
    @override_settings(**SAFE_SETTINGS)
    def test_safe_configuration_has_no_errors(self):
        errors = [finding for finding in configuration_findings() if finding.severity == "error"]
        self.assertEqual(errors, [])

    @override_settings(**{**SAFE_SETTINGS, "DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3"}}})
    def test_non_postgresql_database_is_blocking(self):
        codes = {finding.code for finding in configuration_findings() if finding.severity == "error"}
        self.assertIn("database-engine", codes)

    @override_settings(**{**SAFE_SETTINGS, "DEBUG": True})
    def test_debug_is_blocking(self):
        codes = {finding.code for finding in configuration_findings() if finding.severity == "error"}
        self.assertIn("debug-enabled", codes)

    @override_settings(**{**SAFE_SETTINGS, "ALLOWED_HOSTS": ["*"]})
    def test_wildcard_host_is_blocking(self):
        codes = {finding.code for finding in configuration_findings() if finding.severity == "error"}
        self.assertIn("allowed-hosts-wildcard", codes)

    @override_settings(**{**SAFE_SETTINGS, "MONITOR_ALLOWED_NETWORKS": ["0.0.0.0/0"]})
    def test_all_addresses_target_allowlist_is_blocking(self):
        codes = {finding.code for finding in configuration_findings() if finding.severity == "error"}
        self.assertIn("allowed-network-broad", codes)

    @override_settings(**{**SAFE_SETTINGS, "NTFY_TOKEN": ""})
    def test_partial_ntfy_configuration_is_blocking(self):
        codes = {finding.code for finding in configuration_findings() if finding.severity == "error"}
        self.assertIn("ntfy-partial", codes)


class PreflightCommandTests(TestCase):
    def test_insecure_ci_configuration_fails_closed_without_secrets_in_report(self):
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command("targetpreflight", json=True, stdout=out)
        report = json.loads(out.getvalue())
        self.assertFalse(report["ready"])
        codes = {finding["code"] for finding in report["findings"]}
        self.assertTrue({"debug-enabled", "secret-key", "https-redirect"} & codes)
        serialized = json.dumps(report)
        self.assertNotIn("ci-only", serialized)
        self.assertNotIn("ci-postgres-password", serialized)
        self.assertNotIn("POSTGRES_PASSWORD", serialized)

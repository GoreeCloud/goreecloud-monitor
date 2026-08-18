from django.core.exceptions import ValidationError
from django.test import TestCase

from monitoring.models import Monitor, hash_heartbeat_token, heartbeat_token_is_digest


class MonitorModelTests(TestCase):
    def test_https_monitor_requires_https_url(self):
        monitor = Monitor(name="bad", kind=Monitor.Kind.HTTPS, target="http://example.com")
        with self.assertRaises(ValidationError): monitor.full_clean()

    def test_tcp_monitor_requires_port(self):
        monitor = Monitor(name="tcp", kind=Monitor.Kind.TCP, target="example.com", port=None)
        with self.assertRaises(ValidationError): monitor.full_clean()

    def test_head_monitor_rejects_body_assertion(self):
        monitor = Monitor(name="head", kind=Monitor.Kind.HTTPS, target="https://example.com", http_method="HEAD", expected_body_text="ok")
        with self.assertRaises(ValidationError): monitor.full_clean()

    def test_push_monitor_persists_only_a_verifier(self):
        monitor = Monitor.objects.create(name="push", kind=Monitor.Kind.PUSH, interval_seconds=60)
        self.assertTrue(heartbeat_token_is_digest(monitor.heartbeat_token))

    def test_issued_push_credential_is_not_persisted(self):
        monitor = Monitor.objects.create(name="issued", kind=Monitor.Kind.PUSH, interval_seconds=60)
        raw = monitor.issue_heartbeat_token()
        monitor.refresh_from_db()
        self.assertNotEqual(monitor.heartbeat_token, raw)
        self.assertEqual(monitor.heartbeat_token, hash_heartbeat_token(raw))

    def test_disabled_monitor_is_paused(self):
        monitor = Monitor.objects.create(name="paused", kind=Monitor.Kind.PUSH, enabled=False)
        self.assertEqual(monitor.state, Monitor.State.PAUSED)

from django.core.exceptions import ValidationError
from django.test import TestCase

from monitoring.models import Monitor, hash_heartbeat_token, heartbeat_token_is_digest
from monitoring.validators import format_dns_target, parse_dns_target


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

    def test_dns_monitor_accepts_plain_system_resolver_target(self):
        monitor = Monitor(name="dns", kind=Monitor.Kind.DNS, target="example.com", dns_record_type="A")
        monitor.full_clean(exclude=["heartbeat_token"])
        parsed = parse_dns_target(monitor.target)
        self.assertEqual(parsed.query_name, "example.com")
        self.assertFalse(parsed.uses_explicit_resolver)

    def test_dns_monitor_accepts_explicit_ipv4_and_ipv6_resolvers(self):
        ipv4 = format_dns_target("example.com", "1.1.1.1")
        ipv6 = format_dns_target("example.com", "2606:4700:4700::1111", 5353)
        self.assertEqual(ipv4, "dns://1.1.1.1/example.com")
        self.assertEqual(ipv6, "dns://[2606:4700:4700::1111]:5353/example.com")
        for index, target in enumerate((ipv4, ipv6), start=1):
            monitor = Monitor(name=f"dns-{index}", kind=Monitor.Kind.DNS, target=target, dns_record_type="AAAA")
            monitor.full_clean(exclude=["heartbeat_token"])

    def test_dns_monitor_rejects_credentialed_or_ambiguous_resolver_target(self):
        for target in (
            "dns://user:pass@1.1.1.1/example.com",
            "dns://1.1.1.1/example.com/extra",
            "dns://1.1.1.1:70000/example.com",
            "dns://1.1.1.1/example.com?mode=test",
        ):
            monitor = Monitor(name="bad-dns", kind=Monitor.Kind.DNS, target=target, dns_record_type="A")
            with self.assertRaises(ValidationError):
                monitor.full_clean(exclude=["heartbeat_token"])

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

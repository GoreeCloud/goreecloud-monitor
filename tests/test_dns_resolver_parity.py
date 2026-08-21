from django.test import SimpleTestCase

from monitoring.migration import map_kuma_monitor
from monitoring.models import Monitor
from monitoring.validators import parse_dns_target


class DnsResolverMigrationTests(SimpleTestCase):
    def test_uptime_kuma_custom_resolver_is_preserved_without_warning(self):
        mapping = map_kuma_monitor(
            {
                "name": "cloudflare-dns",
                "type": "dns",
                "hostname": "example.com",
                "dns_resolve_type": "A",
                "dns_resolve_server": "1.1.1.1",
                "interval": 60,
                "timeout": 10,
            }
        )
        self.assertTrue(mapping.supported)
        self.assertEqual(mapping.values["kind"], Monitor.Kind.DNS)
        self.assertEqual(mapping.values["target"], "dns://1.1.1.1/example.com")
        self.assertNotIn("custom-resolver-not-preserved", {issue.code for issue in mapping.issues})
        parsed = parse_dns_target(mapping.values["target"])
        self.assertEqual(parsed.query_name, "example.com")
        self.assertEqual(parsed.resolver_host, "1.1.1.1")
        self.assertEqual(parsed.resolver_port, 53)

    def test_uptime_kuma_custom_resolver_port_is_preserved_when_present(self):
        mapping = map_kuma_monitor(
            {
                "name": "custom-dns",
                "type": "dns",
                "hostname": "example.com",
                "dns_resolve_type": "AAAA",
                "dns_resolve_server": "2001:4860:4860::8888",
                "dns_resolve_port": 5353,
                "interval": 60,
                "timeout": 10,
            }
        )
        self.assertTrue(mapping.supported)
        self.assertEqual(mapping.values["target"], "dns://[2001:4860:4860::8888]:5353/example.com")

    def test_invalid_uptime_kuma_resolver_fails_closed(self):
        mapping = map_kuma_monitor(
            {
                "name": "invalid-dns",
                "type": "dns",
                "hostname": "example.com",
                "dns_resolve_type": "A",
                "dns_resolve_server": "resolver.example/path",
                "interval": 60,
                "timeout": 10,
            }
        )
        self.assertFalse(mapping.supported)
        self.assertIn("invalid-dns-resolver", {issue.code for issue in mapping.issues})

import json
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings

from monitoring.audit import record_security_event
from monitoring.validators import resolve_and_validate_network_target


class TargetPolicyTests(SimpleTestCase):
    @override_settings(MONITOR_ALLOWED_NETWORKS=["127.0.0.0/8"], MONITOR_ALLOW_PUBLIC_TARGETS=True)
    async def test_private_target_is_blocked_when_not_allowlisted(self):
        fake_info = [(2, 1, 6, "", ("10.10.0.5", 443))]
        with patch("socket.getaddrinfo", return_value=fake_info):
            with self.assertRaises(ValidationError):
                await resolve_and_validate_network_target("internal.example", 443)

    @override_settings(MONITOR_ALLOWED_NETWORKS=["10.10.0.0/24"], MONITOR_ALLOW_PUBLIC_TARGETS=False)
    async def test_explicit_private_network_is_allowed(self):
        fake_info = [(2, 1, 6, "", ("10.10.0.5", 443))]
        with patch("socket.getaddrinfo", return_value=fake_info):
            addresses = await resolve_and_validate_network_target("internal.example", 443)
        self.assertEqual(addresses, ["10.10.0.5"])


class WardveilAuditTests(SimpleTestCase):
    def test_security_event_is_structured_and_minimized(self):
        with self.assertLogs("monitoring.wardveil", level="INFO") as captured:
            record_security_event(
                "heartbeat.credential.rotated",
                outcome="success",
                object_type="monitor",
                object_id=42,
            )
        line = captured.output[0]
        prefix = "wardveil_security_event "
        payload = json.loads(line.split(prefix, 1)[1])
        self.assertEqual(payload["event"], "heartbeat.credential.rotated")
        self.assertEqual(payload["object_id"], "42")
        self.assertEqual(set(payload), {"event", "outcome", "object_type", "object_id"})
        self.assertNotIn("token", line.lower())
        self.assertNotIn("target", line.lower())
        self.assertNotIn("ip", line.lower())

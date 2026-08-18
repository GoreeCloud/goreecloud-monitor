import json
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import Client, SimpleTestCase, override_settings

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
        payload = json.loads(line.split(":", 2)[2])
        self.assertEqual(payload["event"], "heartbeat.credential.rotated")
        self.assertEqual(payload["object_id"], "42")
        self.assertEqual(set(payload), {"timestamp", "event", "outcome", "object_type", "object_id"})
        self.assertTrue(payload["timestamp"].endswith("+00:00"))
        self.assertNotIn("token", line.lower())
        self.assertNotIn("target", line.lower())
        self.assertNotIn("client_ip", line.lower())


class OperationalAccessLogTests(SimpleTestCase):
    def test_request_event_excludes_raw_path_query_and_user_agent(self):
        client = Client()
        with self.assertLogs("monitoring.access", level="INFO") as captured:
            response = client.get(
                "/health/live/?credential=do-not-log-this",
                HTTP_USER_AGENT="private-device-agent-do-not-log",
            )
        self.assertEqual(response.status_code, 200)
        payload = json.loads(captured.output[-1].split(":", 2)[2])
        self.assertEqual(payload["route"], "monitoring:health-live")
        self.assertEqual(payload["method"], "GET")
        self.assertEqual(payload["status"], 200)
        serialized = json.dumps(payload)
        self.assertNotIn("health/live", serialized)
        self.assertNotIn("credential", serialized)
        self.assertNotIn("do-not-log-this", serialized)
        self.assertNotIn("private-device-agent", serialized)
        self.assertNotIn("query", serialized)

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from django.test import SimpleTestCase, override_settings

from monitoring.notifications import publish_transition


class NtfyPublisherTests(SimpleTestCase):
    @override_settings(NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="write-only-token")
    async def test_publisher_uses_bearer_token_and_disables_environment_credentials(self):
        with patch("monitoring.notifications.httpx.AsyncClient") as client_class, self.assertLogs("monitoring.access", level="INFO") as captured:
            client=MagicMock(); client.post=AsyncMock(); response=MagicMock(); client.post.return_value=response
            context=client_class.return_value; context.__aenter__=AsyncMock(return_value=client); context.__aexit__=AsyncMock(return_value=False)
            await publish_transition("Tasks","DOWN","Health check failed")
            client_class.assert_called_once_with(timeout=10.0,trust_env=False); client.post.assert_awaited_once()
            args,kwargs=client.post.await_args; self.assertEqual(args[0],"http://ntfy:80/goreecloud-uptime"); self.assertEqual(kwargs["headers"],{"Authorization":"Bearer write-only-token"})
            body=kwargs["content"].decode("utf-8"); self.assertNotIn("write-only-token",body); self.assertIn("Availability check failed",body); response.raise_for_status.assert_called_once_with()
            payload=json.loads(captured.output[-1].split(":",2)[2]); self.assertEqual(payload["event"],"integration.notification.published"); self.assertNotIn("Tasks",json.dumps(payload))

    @override_settings(NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="write-only-token")
    async def test_raw_diagnostics_are_not_forwarded_to_notification(self):
        sensitive_detail="ConnectError: https://backend.internal.example/path?token=reusable-value refused"
        with patch("monitoring.notifications.httpx.AsyncClient") as client_class:
            client=MagicMock(); client.post=AsyncMock(); response=MagicMock(); client.post.return_value=response
            context=client_class.return_value; context.__aenter__=AsyncMock(return_value=client); context.__aexit__=AsyncMock(return_value=False)
            await publish_transition("Private Service","DOWN",sensitive_detail)
            _,kwargs=client.post.await_args; body=kwargs["content"].decode("utf-8"); self.assertNotIn("backend.internal.example",body); self.assertNotIn("reusable-value",body); self.assertNotIn("ConnectError",body); self.assertIn("Open GoreeCloud Monitor for diagnostic details",body)

    @override_settings(NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="write-only-token")
    async def test_controlled_tls_warning_preserves_useful_non_secret_context(self):
        with patch("monitoring.notifications.httpx.AsyncClient") as client_class:
            client=MagicMock(); client.post=AsyncMock(); response=MagicMock(); client.post.return_value=response
            context=client_class.return_value; context.__aenter__=AsyncMock(return_value=client); context.__aexit__=AsyncMock(return_value=False)
            await publish_transition("Website","DEGRADED","TLS certificate expires in 7 day(s)")
            _,kwargs=client.post.await_args; self.assertIn("TLS certificate expires in 7 day(s).",kwargs["content"].decode("utf-8"))

    @override_settings(NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="")
    async def test_partial_configuration_never_attempts_anonymous_publish(self):
        with patch("monitoring.notifications.httpx.AsyncClient") as client_class, self.assertLogs("monitoring.access",level="ERROR") as captured:
            await publish_transition("Tasks","DOWN","Health check failed"); client_class.assert_not_called()
            payload=json.loads(captured.output[-1].split(":",2)[2]); self.assertEqual(payload["event"],"integration.notification.refused"); self.assertEqual(payload["reason"],"partial_configuration")

    @override_settings(NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="write-only-token")
    async def test_publish_failure_logs_only_exception_type_and_safe_frames(self):
        sensitive="https://private.internal/path?token=should-not-log"
        with patch("monitoring.notifications.httpx.AsyncClient") as client_class, self.assertLogs("monitoring.access",level="ERROR") as captured:
            client=MagicMock(); client.post=AsyncMock(side_effect=httpx.ConnectError(sensitive)); context=client_class.return_value; context.__aenter__=AsyncMock(return_value=client); context.__aexit__=AsyncMock(return_value=False)
            await publish_transition("Private Service","DOWN",sensitive)
        serialized=captured.output[-1]
        payload=json.loads(serialized.split(":",2)[2]); self.assertEqual(payload["event"],"integration.notification.failed"); self.assertEqual(payload["exception_type"],"ConnectError")
        self.assertNotIn("private.internal",serialized); self.assertNotIn("should-not-log",serialized); self.assertNotIn("Private Service",serialized)

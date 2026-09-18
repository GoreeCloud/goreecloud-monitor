from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from django.test import SimpleTestCase, override_settings

from monitoring.notifications import (
    create_notify_idempotency_key,
    create_notify_payload,
    publish_notify_transition,
)



class GoreeCloudNotifyPublisherTests(SimpleTestCase):
    def test_runtime_key_matches_versioned_producer_contract(self):
        key = create_notify_idempotency_key("DOWN", "check-result:7:41:2026-08-31T15:30:00+00:00")
        self.assertEqual(key, "gcm-v1-1db64abe2ac5513e67edbda1f0791de413c90cb45af17e0f27c328114feb6c4c")

    def test_tls_warning_maps_to_minimized_tls_event(self):
        event_type, payload = create_notify_payload("Website", "DEGRADED", "TLS certificate expires in 7 day(s)")
        self.assertEqual(event_type, "TLS_EXPIRING")
        self.assertEqual(payload["severity"], "warning")
        self.assertIn("TLS certificate expires in 7 day(s).", payload["body"])

    @override_settings(MONITOR_NOTIFY_ENABLED=False, GOREECLOUD_NOTIFY_BASE_URL="", GOREECLOUD_NOTIFY_TOKEN="")
    async def test_disabled_feature_gate_never_attempts_network(self):
        with patch("monitoring.notifications.httpx.AsyncClient") as client_class:
            result = await publish_notify_transition("Tasks", "DOWN", "Health check failed", transition_id="check-result:1:2:time")
        self.assertFalse(result)
        client_class.assert_not_called()

    @override_settings(
        MONITOR_NOTIFY_ENABLED=True,
        GOREECLOUD_NOTIFY_BASE_URL="https://notify.example.test/base",
        GOREECLOUD_NOTIFY_TOKEN="dedicated-producer-token",
        MONITOR_NOTIFY_MAX_ATTEMPTS=3,
        MONITOR_NOTIFY_RETRY_BACKOFF_SECONDS=0,
        MONITOR_NOTIFY_TIMEOUT_SECONDS=10,
    )
    async def test_first_write_uses_bearer_json_and_opaque_idempotency_key(self):
        response = MagicMock(status_code=201, headers={})
        with patch("monitoring.notifications.httpx.AsyncClient") as client_class, self.assertLogs("monitoring.access", level="INFO") as captured:
            client=MagicMock(); client.post=AsyncMock(return_value=response)
            context=client_class.return_value; context.__aenter__=AsyncMock(return_value=client); context.__aexit__=AsyncMock(return_value=False)
            result = await publish_notify_transition("Tasks", "DOWN", "ConnectError: https://private.example/?token=secret", transition_id="check-result:7:41:2026-08-31T15:30:00+00:00")
        self.assertTrue(result)
        client_class.assert_called_once_with(timeout=10.0, trust_env=False, follow_redirects=False)
        args, kwargs = client.post.await_args
        self.assertEqual(args[0], "https://notify.example.test/api/v1/notifications")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer dedicated-producer-token")
        self.assertTrue(kwargs["headers"]["Idempotency-Key"].startswith("gcm-v1-"))
        serialized = json.dumps(kwargs["json"])
        self.assertNotIn("private.example", serialized); self.assertNotIn("secret", serialized); self.assertNotIn("ConnectError", serialized)
        self.assertNotIn("check-result", json.dumps(kwargs["headers"]))
        self.assertNotIn("dedicated-producer-token", serialized)
        log_payload=json.loads(captured.output[-1].split(":",2)[2]); self.assertEqual(log_payload["integration"],"goreecloud-notify"); self.assertFalse(log_payload["replayed"])

    @override_settings(
        MONITOR_NOTIFY_ENABLED=True,
        GOREECLOUD_NOTIFY_BASE_URL="https://notify.example.test",
        GOREECLOUD_NOTIFY_TOKEN="producer-token",
        MONITOR_NOTIFY_MAX_ATTEMPTS=3,
        MONITOR_NOTIFY_RETRY_BACKOFF_SECONDS=0,
        MONITOR_NOTIFY_TIMEOUT_SECONDS=10,
    )
    async def test_transient_retry_reuses_same_key_and_accepts_explicit_replay(self):
        responses = [MagicMock(status_code=503, headers={}), MagicMock(status_code=200, headers={"Idempotency-Replayed":"true"})]
        with patch("monitoring.notifications.httpx.AsyncClient") as client_class:
            client=MagicMock(); client.post=AsyncMock(side_effect=responses)
            context=client_class.return_value; context.__aenter__=AsyncMock(return_value=client); context.__aexit__=AsyncMock(return_value=False)
            result = await publish_notify_transition("Tasks", "DOWN", "failed", transition_id="check-result:1:8:2026-08-31T15:31:00+00:00")
        self.assertTrue(result)
        self.assertEqual(client.post.await_count, 2)
        first = client.post.await_args_list[0].kwargs["headers"]["Idempotency-Key"]
        second = client.post.await_args_list[1].kwargs["headers"]["Idempotency-Key"]
        self.assertEqual(first, second)

    @override_settings(
        MONITOR_NOTIFY_ENABLED=True,
        GOREECLOUD_NOTIFY_BASE_URL="https://notify.example.test",
        GOREECLOUD_NOTIFY_TOKEN="producer-token",
        MONITOR_NOTIFY_MAX_ATTEMPTS=3,
        MONITOR_NOTIFY_RETRY_BACKOFF_SECONDS=0,
    )
    async def test_idempotency_conflict_fails_closed_without_retry(self):
        response = MagicMock(status_code=409, headers={})
        with patch("monitoring.notifications.httpx.AsyncClient") as client_class, self.assertLogs("monitoring.access", level="ERROR") as captured:
            client=MagicMock(); client.post=AsyncMock(return_value=response)
            context=client_class.return_value; context.__aenter__=AsyncMock(return_value=client); context.__aexit__=AsyncMock(return_value=False)
            result = await publish_notify_transition("Tasks", "DOWN", "failed", transition_id="check-result:1:8:2026-08-31T15:31:00+00:00")
        self.assertFalse(result); self.assertEqual(client.post.await_count, 1)
        serialized=captured.output[-1]; self.assertIn("idempotency_conflict", serialized); self.assertNotIn("check-result", serialized); self.assertNotIn("Tasks", serialized)

    @override_settings(MONITOR_NOTIFY_ENABLED=True, GOREECLOUD_NOTIFY_BASE_URL="http://notify.example.test", GOREECLOUD_NOTIFY_TOKEN="producer-token")
    async def test_non_https_endpoint_fails_before_network(self):
        with patch("monitoring.notifications.httpx.AsyncClient") as client_class, self.assertLogs("monitoring.access", level="ERROR"):
            result = await publish_notify_transition("Tasks", "DOWN", "failed", transition_id="check-result:1:8:time")
        self.assertFalse(result); client_class.assert_not_called()

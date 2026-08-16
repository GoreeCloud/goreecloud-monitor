from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from django.test import SimpleTestCase, override_settings

from monitoring.notifications import publish_transition


class NtfyPublisherTests(SimpleTestCase):
    @override_settings(NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="write-only-token")
    async def test_publisher_uses_bearer_token_and_disables_environment_credentials(self):
        with patch("monitoring.notifications.httpx.AsyncClient") as client_class:
            client = MagicMock()
            client.post = AsyncMock()
            response = MagicMock()
            client.post.return_value = response
            context = client_class.return_value
            context.__aenter__ = AsyncMock(return_value=client)
            context.__aexit__ = AsyncMock(return_value=False)

            await publish_transition("Tasks", "DOWN", "Health check failed")

            client_class.assert_called_once_with(timeout=10.0, trust_env=False)
            client.post.assert_awaited_once()
            args, kwargs = client.post.await_args
            self.assertEqual(args[0], "http://ntfy:80/goreecloud-uptime")
            self.assertEqual(kwargs["headers"], {"Authorization": "Bearer write-only-token"})
            self.assertNotIn("write-only-token", kwargs["content"].decode("utf-8"))
            response.raise_for_status.assert_called_once_with()

    @override_settings(NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="")
    async def test_partial_configuration_never_attempts_anonymous_publish(self):
        with patch("monitoring.notifications.httpx.AsyncClient") as client_class:
            await publish_transition("Tasks", "DOWN", "Health check failed")
            client_class.assert_not_called()

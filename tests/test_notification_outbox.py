from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, patch

from asgiref.sync import sync_to_async
from django.test import TestCase, override_settings
from django.utils import timezone

from monitoring.models import NotificationOutbox
from monitoring.notifications import NotifyPublishResult
from monitoring.outbox import drain_notification_outbox


def _payload() -> dict[str, str]:
    return {
        "source": "goreecloud-monitor",
        "channel": "monitoring",
        "title": "Monitor detected an outage",
        "body": "Service: Availability check failed. Open GoreeCloud Monitor for diagnostic details.",
        "severity": "critical",
    }


class NotificationOutboxTests(TestCase):
    def setUp(self):
        self.item = NotificationOutbox.objects.create(
            transition="DOWN",
            payload=_payload(),
            idempotency_key="gcm-v1-" + "1" * 64,
        )

    @override_settings(MONITOR_NOTIFY_ENABLED=False)
    async def test_disabled_notify_leaves_durable_record_pending(self):
        with patch("monitoring.outbox.publish_notify_payload", new=AsyncMock()) as publisher:
            delivered = await drain_notification_outbox()
        self.assertEqual(delivered, 0)
        publisher.assert_not_awaited()
        await sync_to_async(self.item.refresh_from_db)()
        self.assertIsNone(self.item.delivered_at)
        self.assertEqual(self.item.attempt_count, 0)


    @override_settings(
        MONITOR_NOTIFY_ENABLED=False,
        MONITOR_NOTIFICATION_OUTBOX_RETENTION_DAYS=30,
    )
    async def test_delivered_history_is_pruned_but_pending_records_are_preserved(self):
        old = timezone.now() - timedelta(days=31)
        await sync_to_async(NotificationOutbox.objects.filter(pk=self.item.pk).update)(
            delivered_at=old,
            created_at=old,
        )
        pending = await sync_to_async(NotificationOutbox.objects.create)(
            transition="RECOVERED",
            payload=_payload(),
            idempotency_key="gcm-v1-" + "2" * 64,
        )
        await drain_notification_outbox()
        self.assertFalse(
            await sync_to_async(
                NotificationOutbox.objects.filter(pk=self.item.pk).exists
            )()
        )
        self.assertTrue(
            await sync_to_async(
                NotificationOutbox.objects.filter(pk=pending.pk).exists
            )()
        )

    @override_settings(MONITOR_NOTIFY_ENABLED=True)
    async def test_success_marks_record_delivered(self):
        publisher = AsyncMock(
            return_value=NotifyPublishResult(
                True,
                attempts=1,
                replayed=False,
            )
        )
        with patch("monitoring.outbox.publish_notify_payload", new=publisher):
            delivered = await drain_notification_outbox()
        self.assertEqual(delivered, 1)
        await sync_to_async(self.item.refresh_from_db)()
        self.assertIsNotNone(self.item.delivered_at)
        self.assertEqual(self.item.attempt_count, 1)
        self.assertEqual(self.item.last_failure_reason, "")
        publisher.assert_awaited_once_with(
            _payload(),
            self.item.idempotency_key,
            state="DOWN",
        )

    @override_settings(MONITOR_NOTIFY_ENABLED=True)
    async def test_failure_persists_attempt_and_backoff(self):
        publisher = AsyncMock(
            return_value=NotifyPublishResult(
                False,
                attempts=3,
                reason="transport_error",
            )
        )
        before = timezone.now()
        with patch("monitoring.outbox.publish_notify_payload", new=publisher):
            delivered = await drain_notification_outbox()
        self.assertEqual(delivered, 0)
        await sync_to_async(self.item.refresh_from_db)()
        self.assertIsNone(self.item.delivered_at)
        self.assertEqual(self.item.attempt_count, 3)
        self.assertEqual(self.item.last_failure_reason, "transport_error")
        self.assertGreater(self.item.next_attempt_at, before)

    @override_settings(MONITOR_NOTIFY_ENABLED=True)
    async def test_future_retry_is_not_republished_early(self):
        self.item.next_attempt_at = timezone.now() + timedelta(minutes=5)
        await sync_to_async(self.item.save)(update_fields=["next_attempt_at"])
        with patch("monitoring.outbox.publish_notify_payload", new=AsyncMock()) as publisher:
            delivered = await drain_notification_outbox()
        self.assertEqual(delivered, 0)
        publisher.assert_not_awaited()

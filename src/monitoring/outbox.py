from __future__ import annotations

from datetime import timedelta
import logging

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import NotificationOutbox
from .notifications import NotifyPublishResult, publish_notify_payload
from .observability import log_event

logger = logging.getLogger("monitoring.access")


def _prune_delivered_outbox(retention_days: int) -> int:
    cutoff = timezone.now() - timedelta(days=retention_days)
    deleted, _ = NotificationOutbox.objects.filter(
        delivered_at__isnull=False,
        delivered_at__lt=cutoff,
    ).delete()
    return int(deleted)


def _pending_outbox_ids(limit: int) -> list[int]:
    now = timezone.now()
    return list(
        NotificationOutbox.objects.filter(
            delivered_at__isnull=True,
            next_attempt_at__lte=now,
        )
        .order_by("created_at")
        .values_list("id", flat=True)[:limit]
    )


@transaction.atomic
def _record_publish_result(outbox_id: int, result: NotifyPublishResult) -> None:
    item = NotificationOutbox.objects.select_for_update().get(id=outbox_id)
    if item.delivered_at is not None:
        return

    now = timezone.now()
    wire_attempts = max(1, int(result.attempts or 0))
    item.attempt_count += wire_attempts
    item.last_attempt_at = now

    if result.delivered:
        item.delivered_at = now
        item.last_failure_reason = ""
        item.next_attempt_at = now
        log_event(
            logger,
            "integration.notification.outbox_delivered",
            integration="goreecloud-notify",
            outbox_id=item.id,
            transition=item.transition,
            attempts=item.attempt_count,
            replayed=result.replayed,
        )
    else:
        item.last_failure_reason = (result.reason or "publish_failed")[:64]
        retry_seconds = min(3600, 2 ** min(item.attempt_count, 10))
        item.next_attempt_at = now + timedelta(seconds=retry_seconds)
        log_event(
            logger,
            "integration.notification.outbox_deferred",
            level=logging.WARNING,
            integration="goreecloud-notify",
            outbox_id=item.id,
            transition=item.transition,
            attempts=item.attempt_count,
            reason=item.last_failure_reason,
            retry_seconds=retry_seconds,
        )

    item.save(
        update_fields=[
            "attempt_count",
            "last_attempt_at",
            "delivered_at",
            "last_failure_reason",
            "next_attempt_at",
        ]
    )


async def drain_notification_outbox(limit: int = 100) -> int:
    """Prune delivered history, attempt due Notify deliveries, and return delivered count."""
    retention_days = int(
        getattr(settings, "MONITOR_NOTIFICATION_OUTBOX_RETENTION_DAYS", 30)
    )
    pruned = await sync_to_async(
        _prune_delivered_outbox,
        thread_sensitive=True,
    )(retention_days)
    if pruned:
        log_event(
            logger,
            "integration.notification.outbox_pruned",
            integration="goreecloud-notify",
            records=pruned,
            retention_days=retention_days,
        )

    if not getattr(settings, "MONITOR_NOTIFY_ENABLED", False):
        return 0

    outbox_ids = await sync_to_async(_pending_outbox_ids, thread_sensitive=True)(limit)
    delivered = 0
    for outbox_id in outbox_ids:
        item = await sync_to_async(
            NotificationOutbox.objects.get,
            thread_sensitive=True,
        )(id=outbox_id)
        result = await publish_notify_payload(
            dict(item.payload),
            item.idempotency_key,
            state=item.transition,
        )
        await sync_to_async(_record_publish_result, thread_sensitive=True)(
            outbox_id,
            result,
        )
        if result.delivered:
            delivered += 1
    return delivered

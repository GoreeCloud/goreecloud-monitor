from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import CheckResult, JobEvent, Monitor


@dataclass(frozen=True, slots=True)
class RetentionResult:
    check_results_deleted: int
    job_events_deleted: int


def _protected_job_event_ids(monitor: Monitor) -> set[int]:
    """Return event rows required to preserve correct current JOB evaluation."""
    protected: set[int] = set()
    latest_terminal = (
        monitor.job_events.filter(
            event_type__in=[JobEvent.EventType.SUCCESS, JobEvent.EventType.FAILURE]
        )
        .order_by("-received_at", "-id")
        .first()
    )
    if latest_terminal is not None:
        protected.add(latest_terminal.id)

    latest_start = (
        monitor.job_events.filter(event_type=JobEvent.EventType.START)
        .order_by("-received_at", "-id")
        .first()
    )
    if latest_start is not None and (
        latest_terminal is None or latest_start.received_at > latest_terminal.received_at
    ):
        protected.add(latest_start.id)
    return protected


@transaction.atomic
def prune_monitor_history(
    *,
    now: datetime | None = None,
    check_retention_days: int | None = None,
    job_event_retention_days: int | None = None,
) -> RetentionResult:
    """Prune bounded history while preserving the minimum JOB state needed for evaluation."""
    now = now or timezone.now()
    check_days = int(
        check_retention_days
        if check_retention_days is not None
        else settings.MONITOR_CHECK_RETENTION_DAYS
    )
    job_days = int(
        job_event_retention_days
        if job_event_retention_days is not None
        else settings.MONITOR_JOB_EVENT_RETENTION_DAYS
    )
    if check_days < 1 or job_days < 1:
        raise ValueError("Retention periods must be at least one day")

    check_cutoff = now - timedelta(days=check_days)
    job_cutoff = now - timedelta(days=job_days)

    check_deleted, _ = CheckResult.objects.filter(checked_at__lt=check_cutoff).delete()

    protected_ids: set[int] = set()
    for monitor in Monitor.objects.filter(kind=Monitor.Kind.JOB).only("id"):
        protected_ids.update(_protected_job_event_ids(monitor))

    expired = JobEvent.objects.filter(received_at__lt=job_cutoff)
    if protected_ids:
        expired = expired.exclude(id__in=protected_ids)
    job_deleted, _ = expired.delete()

    return RetentionResult(
        check_results_deleted=int(check_deleted),
        job_events_deleted=int(job_deleted),
    )

from __future__ import annotations

import math
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from croniter import croniter
from django.db import transaction
from django.utils import timezone

from .models import JobEvent, Monitor


@dataclass(frozen=True, slots=True)
class JobEvaluation:
    success: bool
    observed_state: str
    message: str


def _last_scheduled_time(monitor: Monitor, now: datetime) -> datetime:
    zone = ZoneInfo(monitor.job_timezone)
    local_now = now.astimezone(zone)
    expression = monitor.job_cron_expression.strip()
    current_minute = local_now.replace(second=0, microsecond=0)
    if current_minute <= local_now and croniter.match(
        expression,
        current_minute,
        precision_in_seconds=1,
    ):
        return current_minute.astimezone(now.tzinfo)
    return croniter(expression, local_now).get_prev(datetime).astimezone(now.tzinfo)


def evaluate_job_monitor(monitor: Monitor, now: datetime | None = None) -> JobEvaluation:
    """Evaluate one scheduled-job monitor without performing network I/O."""
    now = now or timezone.now()
    latest_terminal = (
        monitor.job_events.filter(
            event_type__in=[JobEvent.EventType.SUCCESS, JobEvent.EventType.FAILURE]
        )
        .order_by("-received_at", "-id")
        .first()
    )
    latest_start = (
        monitor.job_events.filter(event_type=JobEvent.EventType.START)
        .order_by("-received_at", "-id")
        .first()
    )

    if latest_start and (latest_terminal is None or latest_start.received_at > latest_terminal.received_at):
        runtime = max(0.0, (now - latest_start.received_at).total_seconds())
        runtime_limit = monitor.job_max_runtime_seconds or monitor.job_grace_seconds
        if runtime > runtime_limit:
            source = "maximum runtime" if monitor.job_max_runtime_seconds else "grace runtime"
            return JobEvaluation(
                False,
                Monitor.State.DOWN,
                f"Scheduled job exceeded {source} of {runtime_limit}s after start",
            )
        return JobEvaluation(True, Monitor.State.UP, f"Scheduled job is running ({int(runtime)}s)")

    if latest_terminal and latest_terminal.event_type == JobEvent.EventType.FAILURE:
        if latest_terminal.exit_code is None:
            return JobEvaluation(False, Monitor.State.DOWN, "Scheduled job reported failure")
        return JobEvaluation(False, Monitor.State.DOWN, f"Scheduled job exited with code {latest_terminal.exit_code}")

    latest_success = latest_terminal if latest_terminal and latest_terminal.event_type == JobEvent.EventType.SUCCESS else None

    if monitor.job_schedule_mode == Monitor.JobScheduleMode.CRON:
        last_due = _last_scheduled_time(monitor, now)
        # A newly created monitor must not inherit an obligation for cron occurrences that
        # happened before the monitor existed. Its first enforceable window starts with the
        # first scheduled occurrence at or after creation.
        if last_due < monitor.created_at:
            return JobEvaluation(True, Monitor.State.UNKNOWN, "Awaiting the first scheduled job window")
        deadline = last_due + timedelta(seconds=monitor.job_grace_seconds)
        if latest_success and latest_success.received_at >= last_due:
            return JobEvaluation(True, Monitor.State.UP, "Scheduled job completed for the current cron window")
        if now > deadline:
            return JobEvaluation(False, Monitor.State.DOWN, "Scheduled job missed its cron schedule and grace period")
        return JobEvaluation(True, Monitor.State.UNKNOWN, "Awaiting the current scheduled job completion")

    anchor = latest_success.received_at if latest_success else monitor.created_at
    deadline = anchor + timedelta(seconds=monitor.interval_seconds + monitor.job_grace_seconds)
    if now > deadline:
        return JobEvaluation(False, Monitor.State.DOWN, "Scheduled job missed its expected interval and grace period")
    if latest_success:
        return JobEvaluation(True, Monitor.State.UP, "Scheduled job completion is current")
    return JobEvaluation(True, Monitor.State.UNKNOWN, "Awaiting the first scheduled job completion")


def _matching_start(monitor: Monitor, run_id: str, received_at: datetime) -> JobEvent | None:
    starts = JobEvent.objects.filter(
        monitor=monitor,
        event_type=JobEvent.EventType.START,
        received_at__lte=received_at,
    )
    if run_id:
        return starts.filter(run_id=run_id).order_by("-received_at", "-id").first()

    last_terminal = (
        JobEvent.objects.filter(
            monitor=monitor,
            event_type__in=[JobEvent.EventType.SUCCESS, JobEvent.EventType.FAILURE],
            received_at__lte=received_at,
        )
        .order_by("-received_at", "-id")
        .first()
    )
    if last_terminal:
        starts = starts.filter(received_at__gt=last_terminal.received_at)
    return starts.order_by("-received_at", "-id").first()


class JobSignalRateLimited(Exception):
    def __init__(self, retry_after_seconds: int):
        super().__init__("Scheduled-job signal rate limit exceeded")
        self.retry_after_seconds = retry_after_seconds


class JobSignalReplayConflict(Exception):
    pass


@dataclass(frozen=True, slots=True)
class JobSignalResult:
    event: JobEvent
    replayed: bool


def _create_job_event_locked(
    monitor: Monitor,
    event_type: str,
    *,
    event_id: str = "",
    run_id: str = "",
    exit_code: int | None = None,
    message: str = "",
    received_at: datetime,
) -> JobEvent:
    normalized_run_id = run_id.strip()
    if event_type == JobEvent.EventType.START and not normalized_run_id:
        normalized_run_id = secrets.token_urlsafe(12)

    duration_ms = None
    if event_type in {JobEvent.EventType.SUCCESS, JobEvent.EventType.FAILURE}:
        start = _matching_start(monitor, normalized_run_id, received_at)
        if start is not None:
            duration_ms = max(0.0, (received_at - start.received_at).total_seconds() * 1000)
            if not normalized_run_id:
                normalized_run_id = start.run_id

    event = JobEvent.objects.create(
        monitor=monitor,
        received_at=received_at,
        event_type=event_type,
        event_id=event_id,
        run_id=normalized_run_id,
        exit_code=exit_code,
        duration_ms=duration_ms,
        message=message[:500],
    )
    Monitor.objects.filter(pk=monitor.pk).update(
        last_heartbeat_at=received_at,
        last_checked_at=None,
        updated_at=received_at,
    )
    return event


@transaction.atomic
def record_job_signal(
    monitor_id: int,
    event_type: str,
    *,
    event_id: str = "",
    run_id: str = "",
    exit_code: int | None = None,
    message: str = "",
    received_at: datetime | None = None,
    max_per_minute: int = 5,
) -> JobSignalResult:
    """Persist an external job signal with per-monitor replay and rate-limit guarantees."""
    received_at = received_at or timezone.now()
    monitor = Monitor.objects.select_for_update().get(
        pk=monitor_id,
        kind=Monitor.Kind.JOB,
        enabled=True,
    )

    if event_id:
        existing = JobEvent.objects.filter(monitor=monitor, event_id=event_id).first()
        if existing is not None:
            request_run_id = run_id.strip()
            same_exit_code = existing.exit_code == exit_code or (
                event_type == JobEvent.EventType.SUCCESS
                and existing.exit_code in {None, 0}
                and exit_code in {None, 0}
            )
            same_payload = (
                existing.event_type == event_type
                and same_exit_code
                and existing.message == message[:500]
                and (not request_run_id or existing.run_id == request_run_id)
            )
            if not same_payload:
                raise JobSignalReplayConflict("event_id was already used for a different signal")
            return JobSignalResult(existing, True)

    window_start = received_at - timedelta(minutes=1)
    recent_events = JobEvent.objects.filter(
        monitor=monitor,
        received_at__gte=window_start,
        received_at__lte=received_at,
    )
    if recent_events.count() >= max_per_minute:
        oldest = recent_events.order_by("received_at", "id").first()
        retry_after = 60
        if oldest is not None:
            elapsed = max(0.0, (received_at - oldest.received_at).total_seconds())
            retry_after = max(1, math.ceil(60 - elapsed))
        raise JobSignalRateLimited(retry_after)

    return JobSignalResult(
        _create_job_event_locked(
            monitor,
            event_type,
            event_id=event_id,
            run_id=run_id,
            exit_code=exit_code,
            message=message,
            received_at=received_at,
        ),
        False,
    )


@transaction.atomic
def record_job_event(
    monitor_id: int,
    event_type: str,
    *,
    run_id: str = "",
    exit_code: int | None = None,
    message: str = "",
    received_at: datetime | None = None,
) -> JobEvent:
    """Persist an internal typed scheduled-job event without external-ingestion throttling."""
    received_at = received_at or timezone.now()
    monitor = Monitor.objects.select_for_update().get(
        pk=monitor_id,
        kind=Monitor.Kind.JOB,
        enabled=True,
    )
    return _create_job_event_locked(
        monitor,
        event_type,
        run_id=run_id,
        exit_code=exit_code,
        message=message,
        received_at=received_at,
    )

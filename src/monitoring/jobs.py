from __future__ import annotations

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


def _latest_terminal(events: list[JobEvent]) -> JobEvent | None:
    return next(
        (event for event in events if event.event_type in {JobEvent.EventType.SUCCESS, JobEvent.EventType.FAILURE}),
        None,
    )


def _latest_start(events: list[JobEvent]) -> JobEvent | None:
    return next((event for event in events if event.event_type == JobEvent.EventType.START), None)


def _last_scheduled_time(monitor: Monitor, now: datetime) -> datetime:
    zone = ZoneInfo(monitor.job_timezone)
    local_now = now.astimezone(zone)
    return croniter(monitor.job_cron_expression.strip(), local_now).get_prev(datetime).astimezone(now.tzinfo)


def evaluate_job_monitor(monitor: Monitor, now: datetime | None = None) -> JobEvaluation:
    """Evaluate one scheduled-job monitor without performing network I/O."""
    now = now or timezone.now()
    events = list(monitor.job_events.order_by("-received_at", "-id")[:200])
    latest_terminal = _latest_terminal(events)
    latest_start = _latest_start(events)

    if latest_start and (latest_terminal is None or latest_start.received_at > latest_terminal.received_at):
        runtime = max(0.0, (now - latest_start.received_at).total_seconds())
        if monitor.job_max_runtime_seconds and runtime > monitor.job_max_runtime_seconds:
            return JobEvaluation(
                False,
                Monitor.State.DOWN,
                f"Scheduled job exceeded maximum runtime of {monitor.job_max_runtime_seconds}s",
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
    """Persist a typed scheduled-job signal and calculate duration for terminal events."""
    received_at = received_at or timezone.now()
    monitor = Monitor.objects.select_for_update().get(pk=monitor_id, kind=Monitor.Kind.JOB, enabled=True)
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
        run_id=normalized_run_id,
        exit_code=exit_code,
        duration_ms=duration_ms,
        message=message[:500],
    )
    # Force the worker to evaluate the new event on its next polling pass instead of waiting
    # for the ordinary scheduled-job evaluation interval.
    Monitor.objects.filter(pk=monitor.pk).update(
        last_heartbeat_at=received_at,
        last_checked_at=None,
        updated_at=received_at,
    )
    return event

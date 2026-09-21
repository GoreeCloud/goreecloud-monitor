from __future__ import annotations

import hmac
import json
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.db.models import Count, Q
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .audit import record_security_event
from .forms import MaintenanceWindowForm, MonitorForm
from .jobs import JobPhase, JobSignalRateLimited, JobSignalReplayConflict, evaluate_job_monitor, record_job_signal
from .models import CheckResult, Incident, JobEvent, MaintenanceWindow, Monitor, hash_heartbeat_token, heartbeat_token_is_digest


GLAZE_UI_VERSION = "1.5.1"
WARDVEIL_SECURITY_IDENTITY = "Wardveil Security by GoreeCloud"


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict configuration changes to explicitly privileged Monitor administrators."""

    def test_func(self):
        return self.request.user.is_staff


def _heartbeat_issue_response(request: HttpRequest, monitor: Monitor, raw_token: str) -> HttpResponse:
    return render(
        request,
        "monitoring/heartbeat_token_issued.html",
        {
            "monitor": monitor,
            "heartbeat_token": raw_token,
            "heartbeat_endpoint": request.build_absolute_uri(reverse("monitoring:push-heartbeat")),
        },
    )


def _job_credential_issue_response(request: HttpRequest, monitor: Monitor, raw_token: str) -> HttpResponse:
    return render(
        request,
        "monitoring/job_token_issued.html",
        {
            "monitor": monitor,
            "job_token": raw_token,
            "job_endpoint": request.build_absolute_uri(reverse("monitoring:job-signal")),
        },
    )


def _resolve_signal_monitor(raw_token: str, kinds: set[str]) -> Monitor | None:
    if not raw_token or len(raw_token) > 256:
        return None
    digest = hash_heartbeat_token(raw_token)
    monitor = (
        Monitor.objects.filter(kind__in=kinds, enabled=True)
        .filter(Q(heartbeat_token=digest) | Q(heartbeat_token=raw_token))
        .first()
    )
    if monitor is None:
        return None
    if not heartbeat_token_is_digest(monitor.heartbeat_token):
        Monitor.objects.filter(pk=monitor.pk, heartbeat_token=raw_token).update(heartbeat_token=digest)
        monitor.heartbeat_token = digest
    return monitor


def _resolve_push_monitor(raw_token: str) -> Monitor | None:
    return _resolve_signal_monitor(raw_token, {Monitor.Kind.PUSH})


def _notify_configured() -> bool:
    return bool(
        settings.MONITOR_NOTIFY_ENABLED
        and settings.GOREECLOUD_NOTIFY_BASE_URL
        and settings.GOREECLOUD_NOTIFY_TOKEN
    )


def _bearer_credential(request: HttpRequest) -> str:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return ""
    return authorization.removeprefix("Bearer ").strip()


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    counts = {state: 0 for state, _ in Monitor.State.choices}
    for row in Monitor.objects.values("state").annotate(total=Count("id")):
        counts[row["state"]] = row["total"]
    total = sum(counts.values())
    if counts[Monitor.State.DOWN]:
        overall_state, overall_tone = "Down", "down"
    elif counts[Monitor.State.DEGRADED]:
        overall_state, overall_tone = "Degraded", "degraded"
    elif total and counts[Monitor.State.UP] == total:
        overall_state, overall_tone = "Healthy", "up"
    elif total:
        overall_state, overall_tone = "Attention", "maintenance"
    else:
        overall_state, overall_tone = "Awaiting setup", "unknown"
    return render(request, "monitoring/dashboard.html", {
        "counts": counts, "total": total, "overall_state": overall_state, "overall_tone": overall_tone,
        "active_incidents": Incident.objects.filter(ended_at__isnull=True).select_related("monitor")[:8],
        "recent_recoveries": Incident.objects.filter(ended_at__isnull=False).select_related("monitor")[:8],
        "recent_checks": CheckResult.objects.select_related("monitor")[:12], "monitors": Monitor.objects.all()[:12],
    })


class MonitorListView(LoginRequiredMixin, ListView):
    model = Monitor
    template_name = "monitoring/monitor_list.html"
    context_object_name = "monitors"
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        state = self.request.GET.get("state", "").strip().upper()
        kind = self.request.GET.get("kind", "").strip().upper()
        if query:
            queryset = queryset.filter(name__icontains=query)
        if state in {value for value, _ in Monitor.State.choices}:
            queryset = queryset.filter(state=state)
        if kind in {value for value, _ in Monitor.Kind.choices}:
            queryset = queryset.filter(kind=kind)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        state = self.request.GET.get("state", "").strip().upper()
        kind = self.request.GET.get("kind", "").strip().upper()
        from urllib.parse import urlencode
        context.update({
            "query": query, "state_filter": state, "kind_filter": kind,
            "state_choices": Monitor.State.choices, "kind_choices": Monitor.Kind.choices,
            "result_count": self.get_queryset().count(),
            "filter_query": urlencode({k: v for k, v in {"q": query, "state": state, "kind": kind}.items() if v}),
        })
        return context


def _job_phase_tone(phase: str) -> str:
    if phase == JobPhase.COMPLETED:
        return "up"
    if phase in {JobPhase.FAILED, JobPhase.LATE}:
        return "down"
    return "maintenance"


def _parse_positive_int(value: str | None, *, default: int, maximum: int) -> int | None:
    if value in {None, ""}:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if not 1 <= parsed <= maximum:
        return None
    return parsed


def _job_recovery_state(monitor: Monitor) -> dict[str, object]:
    events = monitor.job_events.all()
    latest_terminal = (
        events.filter(event_type__in=[JobEvent.EventType.SUCCESS, JobEvent.EventType.FAILURE])
        .order_by("-received_at", "-id")
        .first()
    )
    latest_start = (
        events.filter(event_type=JobEvent.EventType.START)
        .order_by("-received_at", "-id")
        .first()
    )
    unmatched_start = None
    if latest_start is not None and (
        latest_terminal is None or latest_start.received_at > latest_terminal.received_at
    ):
        unmatched_start = latest_start

    counts = {value: 0 for value, _ in JobEvent.EventType.choices}
    for row in events.values("event_type").annotate(total=Count("id")):
        counts[row["event_type"]] = row["total"]

    return {
        "latest_terminal": latest_terminal,
        "latest_start": latest_start,
        "unmatched_start": unmatched_start,
        "oldest_event": events.order_by("received_at", "id").first(),
        "newest_event": events.order_by("-received_at", "-id").first(),
        "event_count": events.count(),
        "event_counts": counts,
        "evaluation": evaluate_job_monitor(monitor),
    }


@login_required
def job_recovery(request: HttpRequest, pk: int) -> HttpResponse:
    if not request.user.is_staff:
        raise PermissionDenied
    monitor = get_object_or_404(Monitor, pk=pk, kind=Monitor.Kind.JOB)
    state = _job_recovery_state(monitor)
    record_security_event(
        "job.recovery.viewed",
        user=request.user,
        object_type="monitor",
        object_id=monitor.pk,
    )
    return render(
        request,
        "monitoring/job_recovery.html",
        {
            "monitor": monitor,
            "retention_days": settings.MONITOR_JOB_EVENT_RETENTION_DAYS,
            "job_phase_tone": _job_phase_tone(state["evaluation"].phase),
            **state,
        },
    )


@login_required
@require_http_methods(["GET"])
def job_history_export(request: HttpRequest, pk: int) -> JsonResponse:
    if not request.user.is_staff:
        raise PermissionDenied
    monitor = get_object_or_404(Monitor, pk=pk, kind=Monitor.Kind.JOB)

    limit = _parse_positive_int(request.GET.get("limit"), default=1000, maximum=5000)
    before_id = _parse_positive_int(
        request.GET.get("before_id"),
        default=2**63 - 1,
        maximum=2**63 - 1,
    )
    if limit is None or before_id is None:
        return JsonResponse({"detail": "Invalid pagination parameters"}, status=400)

    queryset = monitor.job_events.filter(id__lt=before_id).order_by("-id")
    rows = list(queryset[: limit + 1])
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_before_id = rows[-1].id if has_more and rows else None

    state = _job_recovery_state(monitor)
    event_payload = [
        {
            "id": event.id,
            "received_at": event.received_at.isoformat(),
            "event_type": event.event_type,
            "event_id": event.event_id or None,
            "run_id": event.run_id or None,
            "exit_code": event.exit_code,
            "duration_ms": event.duration_ms,
            "message": event.message,
        }
        for event in rows
    ]
    payload = {
        "schema": "goreecloud-monitor-job-events-v1",
        "generated_at": timezone.now().isoformat(),
        "monitor": {
            "id": monitor.id,
            "name": monitor.name,
            "state": monitor.state,
            "schedule_mode": monitor.job_schedule_mode,
            "interval_seconds": monitor.interval_seconds,
            "schedule_expression": monitor.job_cron_expression or None,
            "cron_expression": (
                monitor.job_cron_expression
                if monitor.job_schedule_mode == Monitor.JobScheduleMode.CRON
                else None
            ),
            "oncalendar_expression": (
                monitor.job_cron_expression
                if monitor.job_schedule_mode == Monitor.JobScheduleMode.ONCALENDAR
                else None
            ),
            "timezone": monitor.job_timezone,
            "grace_seconds": monitor.job_grace_seconds,
            "max_runtime_seconds": monitor.job_max_runtime_seconds,
        },
        "retention": {
            "ordinary_days": settings.MONITOR_JOB_EVENT_RETENTION_DAYS,
            "retained_event_count": state["event_count"],
            "oldest_received_at": (
                state["oldest_event"].received_at.isoformat()
                if state["oldest_event"] is not None
                else None
            ),
            "newest_received_at": (
                state["newest_event"].received_at.isoformat()
                if state["newest_event"] is not None
                else None
            ),
        },
        "evaluation": {
            "success": state["evaluation"].success,
            "observed_state": state["evaluation"].observed_state,
            "phase": state["evaluation"].phase,
            "message": state["evaluation"].message,
        },
        "page": {
            "limit": limit,
            "returned": len(event_payload),
            "has_more": has_more,
            "next_before_id": next_before_id,
        },
        "events": event_payload,
    }
    record_security_event(
        "job.history.exported",
        user=request.user,
        object_type="monitor",
        object_id=monitor.pk,
    )
    response = JsonResponse(payload, json_dumps_params={"indent": 2})
    response.headers["Content-Disposition"] = (
        f'attachment; filename="goreecloud-monitor-job-{monitor.pk}-events.json"'
    )
    return response


@login_required
def monitor_detail(request: HttpRequest, pk: int) -> HttpResponse:
    monitor = get_object_or_404(Monitor, pk=pk)
    job_evaluation = evaluate_job_monitor(monitor) if monitor.kind == Monitor.Kind.JOB else None
    return render(
        request,
        "monitoring/monitor_detail.html",
        {
            "monitor": monitor,
            "checks": monitor.checks.all()[:50],
            "incidents": monitor.incidents.all()[:20],
            "job_events": monitor.job_events.all()[:50] if monitor.kind == Monitor.Kind.JOB else [],
            "job_evaluation": job_evaluation,
            "job_phase_tone": _job_phase_tone(job_evaluation.phase) if job_evaluation else "",
        },
    )


class MonitorCreateView(StaffRequiredMixin, CreateView):
    model = Monitor
    form_class = MonitorForm
    template_name = "monitoring/monitor_form.html"
    success_url = reverse_lazy("monitoring:monitor-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        record_security_event("monitor.configuration.created", user=self.request.user, object_type="monitor", object_id=self.object.pk)
        if self.object.kind == Monitor.Kind.PUSH:
            raw_token = self.object.issue_heartbeat_token()
            record_security_event("heartbeat.credential.issued", user=self.request.user, object_type="monitor", object_id=self.object.pk)
            return _heartbeat_issue_response(self.request, self.object, raw_token)
        if self.object.kind == Monitor.Kind.JOB:
            raw_token = self.object.issue_heartbeat_token()
            record_security_event("job.credential.issued", user=self.request.user, object_type="monitor", object_id=self.object.pk)
            return _job_credential_issue_response(self.request, self.object, raw_token)
        messages.success(self.request, "Monitor created.")
        return response


class MonitorUpdateView(StaffRequiredMixin, UpdateView):
    model = Monitor
    form_class = MonitorForm
    template_name = "monitoring/monitor_form.html"
    success_url = reverse_lazy("monitoring:monitor-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        record_security_event("monitor.configuration.updated", user=self.request.user, object_type="monitor", object_id=self.object.pk)
        messages.success(self.request, "Monitor updated.")
        return response


class MonitorDeleteView(StaffRequiredMixin, DeleteView):
    model = Monitor
    template_name = "monitoring/monitor_confirm_delete.html"
    success_url = reverse_lazy("monitoring:monitor-list")

    def form_valid(self, form):
        object_id = self.object.pk
        response = super().form_valid(form)
        record_security_event("monitor.configuration.deleted", user=self.request.user, object_type="monitor", object_id=object_id)
        return response


@login_required
def incident_list(request: HttpRequest) -> HttpResponse:
    status = request.GET.get("status", "all").strip().lower()
    query = request.GET.get("q", "").strip()
    incidents = Incident.objects.select_related("monitor")
    if status == "active":
        incidents = incidents.filter(ended_at__isnull=True)
    elif status == "recovered":
        incidents = incidents.filter(ended_at__isnull=False)
    else:
        status = "all"
    if query:
        incidents = incidents.filter(Q(monitor__name__icontains=query))
    return render(request, "monitoring/incidents.html", {
        "incidents": incidents[:200], "status_filter": status, "query": query,
        "active_count": Incident.objects.filter(ended_at__isnull=True).count(),
        "recovered_count": Incident.objects.filter(ended_at__isnull=False).count(), "total_count": Incident.objects.count(),
    })


class MaintenanceListView(LoginRequiredMixin, ListView):
    model = MaintenanceWindow
    template_name = "monitoring/maintenance_list.html"
    context_object_name = "windows"
    paginate_by = 50


class MaintenanceCreateView(StaffRequiredMixin, CreateView):
    model = MaintenanceWindow
    form_class = MaintenanceWindowForm
    template_name = "monitoring/maintenance_form.html"
    success_url = reverse_lazy("monitoring:maintenance-list")
    def form_valid(self, form):
        response = super().form_valid(form)
        record_security_event("maintenance.window.created", user=self.request.user, object_type="maintenance_window", object_id=self.object.pk)
        return response


class MaintenanceUpdateView(StaffRequiredMixin, UpdateView):
    model = MaintenanceWindow
    form_class = MaintenanceWindowForm
    template_name = "monitoring/maintenance_form.html"
    success_url = reverse_lazy("monitoring:maintenance-list")
    def form_valid(self, form):
        response = super().form_valid(form)
        record_security_event("maintenance.window.updated", user=self.request.user, object_type="maintenance_window", object_id=self.object.pk)
        return response


class MaintenanceDeleteView(StaffRequiredMixin, DeleteView):
    model = MaintenanceWindow
    template_name = "monitoring/maintenance_confirm_delete.html"
    success_url = reverse_lazy("monitoring:maintenance-list")
    def form_valid(self, form):
        object_id = self.object.pk
        response = super().form_valid(form)
        record_security_event("maintenance.window.deleted", user=self.request.user, object_type="maintenance_window", object_id=object_id)
        return response


@login_required
def notifications_view(request: HttpRequest) -> HttpResponse:
    notify_enabled = _notify_configured()
    return render(
        request,
        "monitoring/notifications.html",
        {
            "notify_enabled": notify_enabled,
            "notify_status": (
                "Runtime configuration present; production acceptance remains separate."
                if notify_enabled
                else "Disabled until an approved GoreeCloud Notify runtime and producer credential are configured."
            ),
            "recent_transitions": Incident.objects.select_related("monitor")[:30],
        },
    )


@login_required
def settings_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        raise PermissionDenied
    return render(request, "monitoring/settings.html", {
        "manager_api_enabled": bool(settings.MANAGER_API_TOKEN),
        "notify_enabled": _notify_configured(),
        "allowed_networks": settings.MONITOR_ALLOWED_NETWORKS, "public_targets": settings.MONITOR_ALLOW_PUBLIC_TARGETS,
        "max_concurrency": settings.MONITOR_MAX_CONCURRENCY, "retention_days": settings.MONITOR_CHECK_RETENTION_DAYS,
        "job_event_retention_days": settings.MONITOR_JOB_EVENT_RETENTION_DAYS,
        "glaze_version": GLAZE_UI_VERSION,
    })


@login_required
def security_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        raise PermissionDenied
    controls = [
        ("HTTPS redirect", bool(settings.SECURE_SSL_REDIRECT)), ("HSTS", settings.SECURE_HSTS_SECONDS >= 31536000),
        ("Secure session cookie", bool(settings.SESSION_COOKIE_SECURE)), ("HttpOnly session cookie", bool(settings.SESSION_COOKIE_HTTPONLY)),
        ("Secure CSRF cookie", bool(settings.CSRF_COOKIE_SECURE)), ("SameSite session boundary", settings.SESSION_COOKIE_SAMESITE in {"Lax", "Strict"}),
        ("Content Security Policy", bool(settings.MONITOR_CONTENT_SECURITY_POLICY)), ("Permissions Policy", bool(settings.MONITOR_PERMISSIONS_POLICY)),
        ("Clickjacking protection", settings.X_FRAME_OPTIONS == "DENY"), ("Same-origin opener policy", settings.SECURE_CROSS_ORIGIN_OPENER_POLICY == "same-origin"),
        ("Legacy path heartbeat credentials disabled", not settings.MONITOR_ALLOW_LEGACY_PATH_HEARTBEATS),
    ]
    return render(request, "monitoring/security.html", {
        "wardveil_identity": WARDVEIL_SECURITY_IDENTITY, "protected": all(enabled for _, enabled in controls), "controls": controls,
        "manager_api_enabled": bool(settings.MANAGER_API_TOKEN), "notify_enabled": _notify_configured(),
        "private_network_count": len(settings.MONITOR_ALLOWED_NETWORKS), "public_targets": settings.MONITOR_ALLOW_PUBLIC_TARGETS,
    })


@login_required
@require_http_methods(["POST"])
def rotate_heartbeat_token(request: HttpRequest, pk: int) -> HttpResponse:
    if not request.user.is_staff:
        raise PermissionDenied
    monitor = get_object_or_404(Monitor, pk=pk, kind__in=[Monitor.Kind.PUSH, Monitor.Kind.JOB])
    raw_token = monitor.issue_heartbeat_token()
    if monitor.kind == Monitor.Kind.JOB:
        record_security_event("job.credential.rotated", user=request.user, object_type="monitor", object_id=monitor.pk)
        return _job_credential_issue_response(request, monitor, raw_token)
    record_security_event("heartbeat.credential.rotated", user=request.user, object_type="monitor", object_id=monitor.pk)
    return _heartbeat_issue_response(request, monitor, raw_token)


@csrf_exempt
@require_http_methods(["POST"])
def push_heartbeat(request: HttpRequest) -> JsonResponse:
    raw_token = _bearer_credential(request)
    monitor = _resolve_push_monitor(raw_token)
    if monitor is None:
        response = JsonResponse({"detail": "Unauthorized"}, status=401)
        response.headers["WWW-Authenticate"] = "Bearer"
        return response
    received_at = timezone.now()
    Monitor.objects.filter(pk=monitor.pk).update(last_heartbeat_at=received_at, updated_at=received_at)
    return JsonResponse({"ok": True, "received_at": received_at.isoformat()})


@csrf_exempt
@require_http_methods(["POST"])
def job_signal(request: HttpRequest) -> JsonResponse:
    raw_token = _bearer_credential(request)
    monitor = _resolve_signal_monitor(raw_token, {Monitor.Kind.JOB})
    if monitor is None:
        response = JsonResponse({"detail": "Unauthorized"}, status=401)
        response.headers["WWW-Authenticate"] = "Bearer"
        return response
    if request.content_type != "application/json" or len(request.body) > 8192:
        return JsonResponse({"detail": "Invalid job signal payload"}, status=400)
    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "Invalid job signal payload"}, status=400)
    if not isinstance(payload, dict) or not set(payload).issubset({"event", "event_id", "run_id", "exit_code", "message"}):
        return JsonResponse({"detail": "Invalid job signal payload"}, status=400)

    event_name = str(payload.get("event", "")).strip().upper()
    aliases = {"FAIL": JobEvent.EventType.FAILURE, "FAILED": JobEvent.EventType.FAILURE}
    event_type = aliases.get(event_name, event_name)
    if event_type not in {value for value, _ in JobEvent.EventType.choices}:
        return JsonResponse({"detail": "Unsupported job event"}, status=400)

    raw_event_id = payload.get("event_id", "")
    raw_run_id = payload.get("run_id", "")
    raw_message = payload.get("message", "")
    if not isinstance(raw_event_id, str) or not isinstance(raw_run_id, str) or not isinstance(raw_message, str):
        return JsonResponse({"detail": "event_id, run_id, and message must be strings"}, status=400)
    event_id = raw_event_id.strip()
    if event_id:
        try:
            event_id = str(uuid.UUID(event_id))
        except ValueError:
            return JsonResponse({"detail": "event_id must be a UUID"}, status=400)
    run_id = raw_run_id.strip()
    message = raw_message.strip()
    exit_code = payload.get("exit_code")
    if len(run_id) > 128 or len(message) > 500:
        return JsonResponse({"detail": "Job signal field exceeds limit"}, status=400)
    if exit_code is not None and (
        isinstance(exit_code, bool)
        or not isinstance(exit_code, int)
        or not -(2**31) <= exit_code < 2**31
    ):
        return JsonResponse({"detail": "exit_code must be a 32-bit integer"}, status=400)
    if event_type == JobEvent.EventType.SUCCESS and exit_code not in {None, 0}:
        return JsonResponse({"detail": "A success event cannot carry a non-zero exit_code"}, status=400)
    if event_type in {JobEvent.EventType.START, JobEvent.EventType.LOG} and exit_code is not None:
        return JsonResponse({"detail": "exit_code is valid only for terminal job events"}, status=400)

    received_at = timezone.now()
    try:
        result = record_job_signal(
            monitor.pk,
            event_type,
            event_id=event_id,
            run_id=run_id,
            exit_code=exit_code,
            message=message,
            received_at=received_at,
            max_per_minute=settings.MONITOR_JOB_SIGNAL_MAX_PER_MINUTE,
        )
    except JobSignalReplayConflict:
        return JsonResponse({"detail": "event_id was already used for a different signal"}, status=409)
    except JobSignalRateLimited as exc:
        response = JsonResponse({"detail": "Scheduled-job signal rate limit exceeded"}, status=429)
        response.headers["Retry-After"] = str(exc.retry_after_seconds)
        return response

    event = result.event
    return JsonResponse(
        {
            "ok": True,
            "event": event.event_type.lower(),
            "event_id": event.event_id or None,
            "received_at": event.received_at.isoformat(),
            "run_id": event.run_id or None,
            "replayed": result.replayed,
        }
    )


@csrf_exempt
@require_http_methods(["GET", "POST"])
def push_heartbeat_legacy(request: HttpRequest, token: str) -> JsonResponse:
    if not settings.MONITOR_ALLOW_LEGACY_PATH_HEARTBEATS:
        raise Http404
    monitor = _resolve_push_monitor(token)
    if monitor is None:
        raise Http404
    received_at = timezone.now()
    Monitor.objects.filter(pk=monitor.pk).update(last_heartbeat_at=received_at, updated_at=received_at)
    record_security_event("heartbeat.legacy_path.accepted", object_type="monitor", object_id=monitor.pk)
    response = JsonResponse({"ok": True, "received_at": received_at.isoformat()})
    response.headers["Deprecation"] = "true"
    return response


@require_http_methods(["GET"])
def health_live(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"ok": True})


@require_http_methods(["GET"])
def health_ready(request: HttpRequest) -> JsonResponse:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"ok": False}, status=503)
    return JsonResponse({"ok": True})


def _manager_authorized(request: HttpRequest) -> bool:
    configured = settings.MANAGER_API_TOKEN
    if not configured:
        return False
    supplied = _bearer_credential(request)
    return bool(supplied and hmac.compare_digest(supplied, configured))


def _manager_unauthorized_response() -> JsonResponse:
    response = JsonResponse({"detail": "Unauthorized"}, status=401)
    response.headers["WWW-Authenticate"] = "Bearer"
    return response


def _manager_job_summary(monitor: Monitor, *, include_expression: bool = False) -> dict[str, object]:
    evaluation = evaluate_job_monitor(monitor)
    latest_event = monitor.job_events.order_by("-received_at", "-id").first()
    active_incident = monitor.incidents.filter(ended_at__isnull=True).exists()
    payload: dict[str, object] = {
        "id": monitor.id,
        "name": monitor.name,
        "enabled": monitor.enabled,
        "state": monitor.state,
        "lifecycle_phase": evaluation.phase,
        "schedule": {
            "mode": monitor.job_schedule_mode,
            "interval_seconds": monitor.interval_seconds,
            "timezone": monitor.job_timezone,
            "grace_seconds": monitor.job_grace_seconds,
            "max_runtime_seconds": monitor.job_max_runtime_seconds,
        },
        "last_signal_at": latest_event.received_at.isoformat() if latest_event else None,
        "last_event_type": latest_event.event_type if latest_event else None,
        "last_duration_ms": latest_event.duration_ms if latest_event else None,
        "active_incident": active_incident,
    }
    if include_expression:
        payload["schedule"]["expression"] = monitor.job_cron_expression or None
    return payload


@require_http_methods(["GET"])
def manager_jobs(request: HttpRequest) -> JsonResponse:
    if not _manager_authorized(request):
        return _manager_unauthorized_response()

    limit = _parse_positive_int(request.GET.get("limit"), default=50, maximum=100)
    after_id = _parse_positive_int(
        request.GET.get("after_id"),
        default=1,
        maximum=2**63 - 1,
    )
    if limit is None or after_id is None:
        return JsonResponse({"detail": "Invalid pagination parameters"}, status=400)

    queryset = Monitor.objects.filter(kind=Monitor.Kind.JOB, id__gte=after_id).order_by("id")
    rows = list(queryset[: limit + 1])
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_after_id = rows[-1].id + 1 if has_more and rows else None
    jobs = [_manager_job_summary(monitor) for monitor in rows]

    return JsonResponse(
        {
            "schema": "goreecloud-monitor-manager-jobs-v1",
            "generated_at": timezone.now().isoformat(),
            "page": {
                "limit": limit,
                "returned": len(jobs),
                "has_more": has_more,
                "next_after_id": next_after_id,
            },
            "jobs": jobs,
        }
    )


@require_http_methods(["GET"])
def manager_job_detail(request: HttpRequest, pk: int) -> JsonResponse:
    if not _manager_authorized(request):
        return _manager_unauthorized_response()

    limit = _parse_positive_int(request.GET.get("event_limit"), default=20, maximum=100)
    if limit is None:
        return JsonResponse({"detail": "Invalid event_limit"}, status=400)

    monitor = get_object_or_404(Monitor, pk=pk, kind=Monitor.Kind.JOB)
    recent_events = [
        {
            "received_at": event.received_at.isoformat(),
            "event_type": event.event_type,
            "exit_code": event.exit_code,
            "duration_ms": event.duration_ms,
        }
        for event in monitor.job_events.order_by("-received_at", "-id")[:limit]
    ]
    return JsonResponse(
        {
            "schema": "goreecloud-monitor-manager-job-v1",
            "generated_at": timezone.now().isoformat(),
            "job": _manager_job_summary(monitor, include_expression=True),
            "retained_event_count": monitor.job_events.count(),
            "recent_events": recent_events,
        }
    )


@require_http_methods(["GET"])
def manager_summary(request: HttpRequest) -> JsonResponse:
    if not _manager_authorized(request):
        return _manager_unauthorized_response()
    counts = {state: 0 for state, _ in Monitor.State.choices}
    for row in Monitor.objects.values("state").annotate(total=Count("id")):
        counts[row["state"]] = row["total"]
    incidents = [{"monitor": incident.monitor.name, "state": incident.monitor.state, "started_at": incident.started_at.isoformat()} for incident in Incident.objects.filter(ended_at__isnull=True).select_related("monitor")[:20]]
    return JsonResponse({"service": "goreecloud-monitor", "generated_at": timezone.now().isoformat(), "total_monitors": Monitor.objects.count(), "states": counts, "active_incidents": incidents})

from __future__ import annotations

import hmac
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import connection
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .audit import record_security_event
from .forms import MaintenanceWindowForm, MonitorForm
from .models import CheckResult, Incident, MaintenanceWindow, Monitor


GLAZE_UI_VERSION = "1.0.0"
WARDVEIL_SECURITY_IDENTITY = "Wardveil Security by GoreeCloud"


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict configuration changes to explicitly privileged Monitor administrators."""

    def test_func(self):
        return self.request.user.is_staff


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Render the operational overview without exposing monitor credentials or raw payloads."""

    counts = {state: 0 for state, _ in Monitor.State.choices}
    for row in Monitor.objects.values("state").annotate(total=Count("id")):
        counts[row["state"]] = row["total"]

    total = sum(counts.values())
    if counts[Monitor.State.DOWN]:
        overall_state = "Down"
        overall_tone = "down"
    elif counts[Monitor.State.DEGRADED]:
        overall_state = "Degraded"
        overall_tone = "degraded"
    elif total and counts[Monitor.State.UP] == total:
        overall_state = "Healthy"
        overall_tone = "up"
    elif total:
        overall_state = "Attention"
        overall_tone = "maintenance"
    else:
        overall_state = "Awaiting setup"
        overall_tone = "unknown"

    context = {
        "counts": counts,
        "total": total,
        "overall_state": overall_state,
        "overall_tone": overall_tone,
        "active_incidents": Incident.objects.filter(ended_at__isnull=True).select_related("monitor")[:8],
        "recent_recoveries": Incident.objects.filter(ended_at__isnull=False).select_related("monitor")[:8],
        "recent_checks": CheckResult.objects.select_related("monitor")[:12],
        "monitors": Monitor.objects.all()[:12],
    }
    return render(request, "monitoring/dashboard.html", context)


class MonitorListView(LoginRequiredMixin, ListView):
    model = Monitor
    template_name = "monitoring/monitor_list.html"
    context_object_name = "monitors"

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        state = self.request.GET.get("state", "").strip().upper()
        kind = self.request.GET.get("kind", "").strip().upper()

        if query:
            # Search names only. Target values can contain private hostnames or addresses and
            # should not be echoed into a broad discovery surface unnecessarily.
            queryset = queryset.filter(name__icontains=query)
        valid_states = {value for value, _ in Monitor.State.choices}
        valid_kinds = {value for value, _ in Monitor.Kind.choices}
        if state in valid_states:
            queryset = queryset.filter(state=state)
        if kind in valid_kinds:
            queryset = queryset.filter(kind=kind)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "query": self.request.GET.get("q", "").strip(),
                "state_filter": self.request.GET.get("state", "").strip().upper(),
                "kind_filter": self.request.GET.get("kind", "").strip().upper(),
                "state_choices": Monitor.State.choices,
                "kind_choices": Monitor.Kind.choices,
                "result_count": self.object_list.count(),
            }
        )
        return context


@login_required
def monitor_detail(request: HttpRequest, pk: int) -> HttpResponse:
    monitor = get_object_or_404(Monitor, pk=pk)
    return render(
        request,
        "monitoring/monitor_detail.html",
        {
            "monitor": monitor,
            "checks": monitor.checks.all()[:50],
            "incidents": monitor.incidents.all()[:20],
        },
    )


class MonitorCreateView(StaffRequiredMixin, CreateView):
    model = Monitor
    form_class = MonitorForm
    template_name = "monitoring/monitor_form.html"
    success_url = reverse_lazy("monitoring:monitor-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        record_security_event(
            "monitor.configuration.created",
            user=self.request.user,
            object_type="monitor",
            object_id=self.object.pk,
        )
        messages.success(self.request, "Monitor created.")
        return response


class MonitorUpdateView(StaffRequiredMixin, UpdateView):
    model = Monitor
    form_class = MonitorForm
    template_name = "monitoring/monitor_form.html"
    success_url = reverse_lazy("monitoring:monitor-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        record_security_event(
            "monitor.configuration.updated",
            user=self.request.user,
            object_type="monitor",
            object_id=self.object.pk,
        )
        messages.success(self.request, "Monitor updated.")
        return response


class MonitorDeleteView(StaffRequiredMixin, DeleteView):
    model = Monitor
    template_name = "monitoring/monitor_confirm_delete.html"
    success_url = reverse_lazy("monitoring:monitor-list")

    def form_valid(self, form):
        object_id = self.object.pk
        response = super().form_valid(form)
        record_security_event(
            "monitor.configuration.deleted",
            user=self.request.user,
            object_type="monitor",
            object_id=object_id,
        )
        return response


@login_required
def incident_list(request: HttpRequest) -> HttpResponse:
    """Present active and recovered incidents as one searchable operational history."""

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

    return render(
        request,
        "monitoring/incidents.html",
        {
            "incidents": incidents[:200],
            "status_filter": status,
            "query": query,
            "active_count": Incident.objects.filter(ended_at__isnull=True).count(),
            "recovered_count": Incident.objects.filter(ended_at__isnull=False).count(),
            "total_count": Incident.objects.count(),
        },
    )


class MaintenanceListView(LoginRequiredMixin, ListView):
    model = MaintenanceWindow
    template_name = "monitoring/maintenance_list.html"
    context_object_name = "windows"


class MaintenanceCreateView(StaffRequiredMixin, CreateView):
    model = MaintenanceWindow
    form_class = MaintenanceWindowForm
    template_name = "monitoring/maintenance_form.html"
    success_url = reverse_lazy("monitoring:maintenance-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        record_security_event(
            "maintenance.window.created",
            user=self.request.user,
            object_type="maintenance_window",
            object_id=self.object.pk,
        )
        return response


class MaintenanceUpdateView(StaffRequiredMixin, UpdateView):
    model = MaintenanceWindow
    form_class = MaintenanceWindowForm
    template_name = "monitoring/maintenance_form.html"
    success_url = reverse_lazy("monitoring:maintenance-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        record_security_event(
            "maintenance.window.updated",
            user=self.request.user,
            object_type="maintenance_window",
            object_id=self.object.pk,
        )
        return response


class MaintenanceDeleteView(StaffRequiredMixin, DeleteView):
    model = MaintenanceWindow
    template_name = "monitoring/maintenance_confirm_delete.html"
    success_url = reverse_lazy("monitoring:maintenance-list")

    def form_valid(self, form):
        object_id = self.object.pk
        response = super().form_valid(form)
        record_security_event(
            "maintenance.window.deleted",
            user=self.request.user,
            object_type="maintenance_window",
            object_id=object_id,
        )
        return response


@login_required
def notifications_view(request: HttpRequest) -> HttpResponse:
    """Report notification integration posture without pretending transition events are delivery logs."""

    ntfy_enabled = bool(settings.NTFY_BASE_URL and settings.NTFY_TOPIC and settings.NTFY_TOKEN)
    return render(
        request,
        "monitoring/notifications.html",
        {
            "ntfy_enabled": ntfy_enabled,
            "notify_status": "Planned after GoreeCloud Notify production approval",
            "recent_transitions": Incident.objects.select_related("monitor")[:30],
        },
    )


@login_required
def settings_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        return HttpResponse(status=403)
    return render(
        request,
        "monitoring/settings.html",
        {
            "manager_api_enabled": bool(settings.MANAGER_API_TOKEN),
            "ntfy_enabled": bool(settings.NTFY_BASE_URL and settings.NTFY_TOPIC and settings.NTFY_TOKEN),
            "allowed_networks": settings.MONITOR_ALLOWED_NETWORKS,
            "public_targets": settings.MONITOR_ALLOW_PUBLIC_TARGETS,
            "max_concurrency": settings.MONITOR_MAX_CONCURRENCY,
            "retention_days": settings.MONITOR_CHECK_RETENTION_DAYS,
            "glaze_version": GLAZE_UI_VERSION,
        },
    )


@login_required
def security_view(request: HttpRequest) -> HttpResponse:
    """Present secret-free Monitor protection posture under the Wardveil Security identity."""

    if not request.user.is_staff:
        return HttpResponse(status=403)

    controls = [
        ("HTTPS redirect", bool(settings.SECURE_SSL_REDIRECT)),
        ("HSTS", settings.SECURE_HSTS_SECONDS >= 31536000),
        ("Secure session cookie", bool(settings.SESSION_COOKIE_SECURE)),
        ("HttpOnly session cookie", bool(settings.SESSION_COOKIE_HTTPONLY)),
        ("Secure CSRF cookie", bool(settings.CSRF_COOKIE_SECURE)),
        ("SameSite session boundary", settings.SESSION_COOKIE_SAMESITE in {"Lax", "Strict"}),
        ("Content Security Policy", bool(settings.MONITOR_CONTENT_SECURITY_POLICY)),
        ("Permissions Policy", bool(settings.MONITOR_PERMISSIONS_POLICY)),
        ("Clickjacking protection", settings.X_FRAME_OPTIONS == "DENY"),
        ("Same-origin opener policy", settings.SECURE_CROSS_ORIGIN_OPENER_POLICY == "same-origin"),
    ]
    protected = all(enabled for _, enabled in controls)
    return render(
        request,
        "monitoring/security.html",
        {
            "wardveil_identity": WARDVEIL_SECURITY_IDENTITY,
            "protected": protected,
            "controls": controls,
            "manager_api_enabled": bool(settings.MANAGER_API_TOKEN),
            "ntfy_enabled": bool(settings.NTFY_BASE_URL and settings.NTFY_TOPIC and settings.NTFY_TOKEN),
            "private_network_count": len(settings.MONITOR_ALLOWED_NETWORKS),
            "public_targets": settings.MONITOR_ALLOW_PUBLIC_TARGETS,
        },
    )


@login_required
@require_http_methods(["POST"])
def rotate_heartbeat_token(request: HttpRequest, pk: int) -> HttpResponse:
    if not request.user.is_staff:
        return HttpResponse(status=403)
    monitor = get_object_or_404(Monitor, pk=pk, kind=Monitor.Kind.PUSH)
    monitor.heartbeat_token = secrets.token_urlsafe(32)
    monitor.save(update_fields=["heartbeat_token", "updated_at"])
    record_security_event(
        "heartbeat.credential.rotated",
        user=request.user,
        object_type="monitor",
        object_id=monitor.pk,
    )
    messages.success(request, "Heartbeat token rotated. Update every sender before relying on the monitor again.")
    return redirect("monitoring:monitor-detail", pk=monitor.pk)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def push_heartbeat(request: HttpRequest, token: str) -> JsonResponse:
    monitor = get_object_or_404(Monitor, heartbeat_token=token, kind=Monitor.Kind.PUSH, enabled=True)
    monitor.last_heartbeat_at = timezone.now()
    monitor.save(update_fields=["last_heartbeat_at", "updated_at"])
    # A valid token is already credential-like. Keep the unauthenticated acknowledgement
    # intentionally generic so possession does not reveal the internal monitor identity.
    return JsonResponse({"ok": True, "received_at": monitor.last_heartbeat_at.isoformat()})


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
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    supplied = auth.removeprefix("Bearer ").strip()
    return hmac.compare_digest(supplied, configured)


@require_http_methods(["GET"])
def manager_summary(request: HttpRequest) -> JsonResponse:
    if not _manager_authorized(request):
        response = JsonResponse({"detail": "Unauthorized"}, status=401)
        response.headers["WWW-Authenticate"] = "Bearer"
        return response
    counts = {state: 0 for state, _ in Monitor.State.choices}
    for row in Monitor.objects.values("state").annotate(total=Count("id")):
        counts[row["state"]] = row["total"]
    incidents = [
        {
            "monitor": incident.monitor.name,
            "state": incident.monitor.state,
            "started_at": incident.started_at.isoformat(),
        }
        for incident in Incident.objects.filter(ended_at__isnull=True).select_related("monitor")[:20]
    ]
    return JsonResponse(
        {
            "service": "goreecloud-monitor",
            "generated_at": timezone.now().isoformat(),
            "total_monitors": Monitor.objects.count(),
            "states": counts,
            "active_incidents": incidents,
        }
    )

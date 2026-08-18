from django.contrib import admin

from .models import CheckResult, Incident, MaintenanceWindow, Monitor


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "state", "enabled", "last_checked_at", "response_time_ms")
    list_filter = ("kind", "state", "enabled")
    search_fields = ("name", "target")
    # The heartbeat verifier is intentionally omitted. It is neither reusable nor useful in the
    # administration UI and should not become routine visual/log/screenshot material.
    exclude = ("heartbeat_token",)
    readonly_fields = (
        "state",
        "consecutive_failures",
        "consecutive_successes",
        "last_checked_at",
        "last_success_at",
        "last_failure_at",
        "response_time_ms",
        "tls_expires_at",
        "last_message",
        "created_at",
        "updated_at",
    )


@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    list_display = ("monitor", "checked_at", "observed_state", "success", "response_time_ms")
    list_filter = ("observed_state", "success")
    search_fields = ("monitor__name", "message")
    readonly_fields = ("monitor", "checked_at", "success", "observed_state", "response_time_ms", "message")


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("monitor", "started_at", "ended_at")
    list_filter = ("ended_at",)
    search_fields = ("monitor__name", "failure_reason", "recovery_message")


@admin.register(MaintenanceWindow)
class MaintenanceWindowAdmin(admin.ModelAdmin):
    list_display = ("name", "starts_at", "ends_at")
    filter_horizontal = ("monitors",)

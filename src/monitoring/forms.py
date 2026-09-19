from django import forms

from .models import MaintenanceWindow, Monitor


class MonitorForm(forms.ModelForm):
    class Meta:
        model = Monitor
        fields = [
            "name",
            "kind",
            "target",
            "port",
            "enabled",
            "interval_seconds",
            "timeout_seconds",
            "failure_threshold",
            "recovery_threshold",
            "http_method",
            "expected_status_code",
            "follow_redirects",
            "expected_body_text",
            "expected_json_path",
            "expected_json_value",
            "tls_warning_days",
            "dns_record_type",
            "expected_dns_answer",
            "heartbeat_grace_seconds",
            "job_schedule_mode",
            "job_cron_expression",
            "job_timezone",
            "job_grace_seconds",
            "job_max_runtime_seconds",
        ]
        help_texts = {
            "target": (
                "Use the service URL or host for HTTP/TCP checks. Ping checks use a hostname or IP address and no port. "
                "DNS checks accept a query name or dns://resolver[:port]/query-name when a specific resolver must be validated. "
                "Push and scheduled-job monitors leave this blank."
            ),
            "dns_record_type": "DNS checks support A, AAAA, and CNAME records.",
            "expected_dns_answer": "Optional exact DNS answer that must be present after normalization.",
            "job_schedule_mode": "Simple uses interval + grace. Cron uses a five-field cron expression and explicit IANA timezone.",
            "job_cron_expression": "Required only for cron-scheduled jobs, for example 0 3 * * *.",
            "job_timezone": "IANA time zone used to interpret cron schedules, for example UTC or America/Chicago.",
            "job_grace_seconds": "Additional time allowed after the expected schedule before the job becomes Down.",
            "job_max_runtime_seconds": "Maximum allowed run time after a START signal; 0 disables overrun detection.",
        }
        widgets = {
            "expected_body_text": forms.TextInput(attrs={"autocomplete": "off"}),
            "expected_json_value": forms.TextInput(attrs={"autocomplete": "off"}),
        }

    def clean(self):
        cleaned = super().clean()
        # Model.clean() performs the cross-field validation through full_clean() during form validation.
        return cleaned


class MaintenanceWindowForm(forms.ModelForm):
    class Meta:
        model = MaintenanceWindow
        fields = ["name", "starts_at", "ends_at", "monitors"]
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "monitors": forms.CheckboxSelectMultiple(),
        }

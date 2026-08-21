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
        ]
        help_texts = {
            "target": (
                "Use the service URL or host for HTTP/TCP checks. DNS checks accept a query name "
                "or dns://resolver[:port]/query-name when a specific resolver must be validated. "
                "Push monitors leave this blank."
            ),
            "dns_record_type": "DNS checks support A, AAAA, and CNAME records.",
            "expected_dns_answer": "Optional exact DNS answer that must be present after normalization.",
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

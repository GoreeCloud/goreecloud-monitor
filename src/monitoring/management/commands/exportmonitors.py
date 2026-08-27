from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from monitoring.models import MaintenanceWindow, Monitor


EXPORT_SCHEMA = "goreecloud-monitor"
EXPORT_VERSION = 1
MONITOR_FIELDS = (
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
)


class Command(BaseCommand):
    help = "Export portable GoreeCloud Monitor definitions without runtime secrets or history"

    def add_arguments(self, parser):
        parser.add_argument("--output", help="Write JSON to this path instead of stdout")

    def handle(self, *args, **options):
        monitors = []
        for monitor in Monitor.objects.order_by("name"):
            monitors.append({field: getattr(monitor, field) for field in MONITOR_FIELDS})

        maintenance = []
        for window in MaintenanceWindow.objects.prefetch_related("monitors").order_by("starts_at", "name"):
            maintenance.append(
                {
                    "name": window.name,
                    "starts_at": window.starts_at.isoformat(),
                    "ends_at": window.ends_at.isoformat(),
                    "monitors": list(window.monitors.order_by("name").values_list("name", flat=True)),
                }
            )

        document = {
            "schema": EXPORT_SCHEMA,
            "version": EXPORT_VERSION,
            "exported_at": timezone.now().isoformat(),
            "monitors": monitors,
            "maintenance_windows": maintenance,
        }
        payload = json.dumps(document, indent=2, sort_keys=True) + "\n"
        output = options.get("output")
        if output:
            path = Path(output)
            path.write_text(payload, encoding="utf-8")
            self.stderr.write(self.style.SUCCESS(f"Exported {len(monitors)} monitor(s) to {path}"))
        else:
            self.stdout.write(payload, ending="")

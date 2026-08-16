from __future__ import annotations

import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from monitoring.migration import load_kuma_monitors, map_kuma_monitor
from monitoring.models import Monitor


COMPARE_FIELDS = (
    "kind",
    "target",
    "port",
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
    "dns_record_type",
    "heartbeat_grace_seconds",
)


class Command(BaseCommand):
    help = "Compare mapped Uptime Kuma definitions with the current GoreeCloud Monitor database"

    def add_arguments(self, parser):
        parser.add_argument("input", help="Path to kuma-cli/Uptime Kuma JSON")
        parser.add_argument("--json", action="store_true", help="Write a sanitized comparison report as JSON")

    def handle(self, *args, **options):
        try:
            raw_monitors, metadata = load_kuma_monitors(options["input"])
        except ValidationError as exc:
            raise CommandError(str(exc)) from exc

        mappings = [map_kuma_monitor(raw) for raw in raw_monitors]
        current = {monitor.name: monitor for monitor in Monitor.objects.all()}
        results = []

        for mapping in mappings:
            if not mapping.supported:
                results.append(
                    {
                        "name": mapping.source_name,
                        "status": "unsupported",
                        "differences": [],
                        "issues": [issue.to_dict() for issue in mapping.issues],
                    }
                )
                continue

            monitor = current.get(mapping.source_name)
            if monitor is None:
                results.append(
                    {
                        "name": mapping.source_name,
                        "status": "missing",
                        "differences": [],
                        "issues": [issue.to_dict() for issue in mapping.issues],
                    }
                )
                continue

            differences = []
            for field in COMPARE_FIELDS:
                expected = mapping.values.get(field, Monitor._meta.get_field(field).get_default())
                actual = getattr(monitor, field)
                if actual != expected:
                    differences.append({"field": field, "source": expected, "monitor": actual})

            results.append(
                {
                    "name": mapping.source_name,
                    "status": "match" if not differences else "different",
                    "differences": differences,
                    "issues": [issue.to_dict() for issue in mapping.issues],
                }
            )

        source_names = {mapping.source_name for mapping in mappings}
        for name in sorted(set(current) - source_names):
            results.append({"name": name, "status": "monitor-only", "differences": [], "issues": []})

        summary = {
            status: sum(1 for result in results if result["status"] == status)
            for status in ("match", "different", "missing", "unsupported", "monitor-only")
        }
        report = {
            "schema": "goreecloud-monitor-uptime-kuma-comparison",
            "version": 1,
            "source": metadata,
            "summary": summary,
            "monitors": results,
        }

        if options["json"]:
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
            return

        self.stdout.write(
            "Uptime Kuma definition comparison: "
            + ", ".join(f"{key}={value}" for key, value in summary.items())
        )
        for result in results:
            self.stdout.write(f"- {result['name']}: {result['status'].upper()}")
            for difference in result["differences"]:
                self.stdout.write(
                    f"  {difference['field']}: source={difference['source']!r}, monitor={difference['monitor']!r}"
                )

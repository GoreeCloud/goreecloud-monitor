from __future__ import annotations

import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from monitoring.migration import load_kuma_monitors, map_kuma_monitor, migration_report


class Command(BaseCommand):
    help = "Audit a kuma-cli/Uptime Kuma JSON export for GoreeCloud Monitor migration compatibility"

    def add_arguments(self, parser):
        parser.add_argument("input", help="Path to kuma-cli/Uptime Kuma JSON")
        parser.add_argument("--json", action="store_true", help="Write the sanitized migration report as JSON")

    def handle(self, *args, **options):
        try:
            raw_monitors, metadata = load_kuma_monitors(options["input"])
        except ValidationError as exc:
            raise CommandError(str(exc)) from exc

        mappings = [map_kuma_monitor(raw) for raw in raw_monitors]
        report = migration_report(mappings, metadata)

        if options["json"]:
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
            return

        summary = report["summary"]
        self.stdout.write(
            f"Uptime Kuma migration audit: {summary['source_monitors']} source monitor(s), "
            f"{summary['supported']} supported, {summary['unsupported']} unsupported, "
            f"{summary['warnings']} warning(s)."
        )
        for mapping in mappings:
            status = "SUPPORTED" if mapping.supported else "BLOCKED"
            self.stdout.write(f"- {mapping.source_name} [{mapping.source_type}] {status}")
            for issue in mapping.issues:
                self.stdout.write(f"  {issue.severity.upper()} {issue.code}: {issue.message}")

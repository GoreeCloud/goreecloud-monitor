from __future__ import annotations

import json
from datetime import datetime, timezone as dt_timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from monitoring.models import MaintenanceWindow, Monitor
from monitoring.management.commands.exportmonitors import EXPORT_SCHEMA, EXPORT_VERSION, MONITOR_FIELDS


class Command(BaseCommand):
    help = "Import a versioned GoreeCloud Monitor definition export into an empty target"

    def add_arguments(self, parser):
        parser.add_argument("input", help="Path to the exported JSON file")
        parser.add_argument("--dry-run", action="store_true", help="Validate the complete import and roll it back")

    def handle(self, *args, **options):
        path = Path(options["input"])
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Unable to read import document: {exc}") from exc

        if document.get("schema") != EXPORT_SCHEMA:
            raise CommandError("Import document is not a GoreeCloud Monitor export")
        if document.get("version") != EXPORT_VERSION:
            raise CommandError(f"Unsupported export version: {document.get('version')!r}")
        if not isinstance(document.get("monitors"), list) or not isinstance(document.get("maintenance_windows", []), list):
            raise CommandError("Import document has an invalid structure")
        if Monitor.objects.exists() or MaintenanceWindow.objects.exists():
            raise CommandError("Portable import requires an empty Monitor target")

        allowed_fields = set(MONITOR_FIELDS)
        created = {}
        with transaction.atomic():
            for index, raw in enumerate(document["monitors"], start=1):
                if not isinstance(raw, dict):
                    raise CommandError(f"Monitor entry {index} is not an object")
                unknown = set(raw) - allowed_fields
                if unknown:
                    raise CommandError(f"Monitor entry {index} contains unsupported fields: {', '.join(sorted(unknown))}")
                missing = allowed_fields - set(raw)
                if missing:
                    raise CommandError(f"Monitor entry {index} is missing fields: {', '.join(sorted(missing))}")
                monitor = Monitor(**{field: raw[field] for field in MONITOR_FIELDS})
                try:
                    monitor.full_clean()
                    monitor.save()
                except Exception as exc:
                    raise CommandError(f"Monitor entry {index} failed validation: {exc}") from exc
                created[monitor.name] = monitor

            for index, raw in enumerate(document.get("maintenance_windows", []), start=1):
                if not isinstance(raw, dict):
                    raise CommandError(f"Maintenance entry {index} is not an object")
                try:
                    starts_at = datetime.fromisoformat(raw["starts_at"])
                    ends_at = datetime.fromisoformat(raw["ends_at"])
                    if timezone.is_naive(starts_at):
                        starts_at = timezone.make_aware(starts_at, timezone=dt_timezone.utc)
                    if timezone.is_naive(ends_at):
                        ends_at = timezone.make_aware(ends_at, timezone=dt_timezone.utc)
                    window = MaintenanceWindow(name=raw["name"], starts_at=starts_at, ends_at=ends_at)
                    window.full_clean()
                    window.save()
                    monitor_names = raw.get("monitors", [])
                    missing_names = sorted(set(monitor_names) - set(created))
                    if missing_names:
                        raise CommandError(
                            f"Maintenance entry {index} references unknown monitors: {', '.join(missing_names)}"
                        )
                    window.monitors.set([created[name] for name in monitor_names])
                except CommandError:
                    raise
                except Exception as exc:
                    raise CommandError(f"Maintenance entry {index} failed validation: {exc}") from exc

            if options["dry_run"]:
                transaction.set_rollback(True)

        suffix = " (dry run; rolled back)" if options["dry_run"] else ""
        self.stdout.write(self.style.SUCCESS(f"Validated {len(created)} monitor(s){suffix}"))

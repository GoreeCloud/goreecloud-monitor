from __future__ import annotations

import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from monitoring.migration import load_kuma_monitors, map_kuma_monitor, migration_report
from monitoring.models import Monitor


class Command(BaseCommand):
    help = "Import supported Uptime Kuma monitor definitions into GoreeCloud Monitor"

    def add_arguments(self, parser):
        parser.add_argument("input", help="Path to kuma-cli/Uptime Kuma JSON")
        parser.add_argument("--dry-run", action="store_true", help="Validate and map the import, then roll it back")
        parser.add_argument(
            "--allow-partial",
            action="store_true",
            help="Skip unsupported monitors instead of refusing the complete import",
        )
        parser.add_argument(
            "--activate",
            action="store_true",
            help="Create imported monitors enabled. Default is paused for safe migration review.",
        )
        parser.add_argument("--report", help="Optional path for a sanitized JSON migration report")

    def handle(self, *args, **options):
        if Monitor.objects.exists():
            raise CommandError("Uptime Kuma migration import requires an empty GoreeCloud Monitor target")

        try:
            raw_monitors, metadata = load_kuma_monitors(options["input"])
        except ValidationError as exc:
            raise CommandError(str(exc)) from exc

        mappings = [map_kuma_monitor(raw) for raw in raw_monitors]
        report = migration_report(mappings, metadata)
        blocked = [mapping for mapping in mappings if not mapping.supported]
        supported = [mapping for mapping in mappings if mapping.supported]

        if options["report"]:
            try:
                Path(options["report"]).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            except OSError as exc:
                raise CommandError(f"Unable to write migration report: {exc}") from exc

        if blocked and not options["allow_partial"]:
            names = ", ".join(mapping.source_name for mapping in blocked[:10])
            suffix = "" if len(blocked) <= 10 else f" (+{len(blocked) - 10} more)"
            raise CommandError(
                f"Migration contains {len(blocked)} unsupported monitor(s): {names}{suffix}. "
                "Run audituptimekuma for details or use --allow-partial to import only supported definitions."
            )

        if options["activate"]:
            warned = [mapping for mapping in supported if mapping.has_warnings]
            if warned:
                names = ", ".join(mapping.source_name for mapping in warned[:10])
                suffix = "" if len(warned) <= 10 else f" (+{len(warned) - 10} more)"
                raise CommandError(
                    "Refusing --activate because mapped monitors still require migration review: "
                    f"{names}{suffix}. Import paused first, resolve warnings, then activate explicitly in Monitor."
                )

        created = 0
        with transaction.atomic():
            for mapping in supported:
                monitor = Monitor(**mapping.values)
                monitor.enabled = bool(options["activate"])
                try:
                    monitor.full_clean()
                    monitor.save()
                except Exception as exc:
                    raise CommandError(f"Mapped monitor {mapping.source_name!r} failed validation: {exc}") from exc
                created += 1

            if options["dry_run"]:
                transaction.set_rollback(True)

        suffix = " (dry run; rolled back)" if options["dry_run"] else ""
        skipped = len(blocked)
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {created} monitor(s) paused by default; skipped {skipped} unsupported monitor(s){suffix}"
            )
        )

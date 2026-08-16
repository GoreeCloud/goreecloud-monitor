from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from monitoring.preflight import build_preflight_report


class Command(BaseCommand):
    help = "Fail-closed GoreeCloud Monitor target-environment configuration/database preflight"

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Write the sanitized preflight report as JSON")

    def handle(self, *args, **options):
        report = build_preflight_report()
        if options["json"]:
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        else:
            self.stdout.write(
                f"Target preflight: ready={report['ready']} errors={report['summary']['errors']} "
                f"warnings={report['summary']['warnings']}"
            )
            for finding in report["findings"]:
                self.stdout.write(f"- {finding['severity'].upper()} {finding['code']}: {finding['message']}")

        if not report["ready"]:
            raise CommandError("GoreeCloud Monitor target-environment preflight failed")

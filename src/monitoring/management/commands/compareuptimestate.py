from __future__ import annotations

import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from monitoring.migration import load_kuma_monitors
from monitoring.models import Monitor
from monitoring.parallel import compare_runtime_snapshots


class Command(BaseCommand):
    help = "Compare a kuma-cli live monitor snapshot with GoreeCloud Monitor runtime state and latency"

    def add_arguments(self, parser):
        parser.add_argument("input", help="Path to `kuma monitors list --json` output")
        parser.add_argument(
            "--latency-tolerance-ms",
            type=float,
            default=250.0,
            help="Maximum absolute response-time difference counted as equivalent (default: 250 ms)",
        )
        parser.add_argument("--json", action="store_true", help="Write the sanitized comparison report as JSON")

    def handle(self, *args, **options):
        tolerance = options["latency_tolerance_ms"]
        if tolerance < 0:
            raise CommandError("--latency-tolerance-ms must be zero or greater")

        try:
            source_monitors, metadata = load_kuma_monitors(options["input"])
        except ValidationError as exc:
            raise CommandError(str(exc)) from exc

        report = compare_runtime_snapshots(
            source_monitors,
            list(Monitor.objects.all()),
            latency_tolerance_ms=tolerance,
        )
        report["source"] = metadata

        if options["json"]:
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
            return

        summary = report["summary"]
        self.stdout.write(
            "Uptime Kuma runtime comparison: "
            f"match={summary['match']}, state-different={summary['state-different']}, "
            f"latency-different={summary['latency-different']}, missing={summary['missing']}, "
            f"monitor-only={summary['monitor-only']}, source-unknown={summary['source-unknown']}, "
            f"source-duplicate={summary['source-duplicate']}."
        )
        for result in report["monitors"]:
            self.stdout.write(
                f"- {result['name']}: {result['status'].upper()} "
                f"source={result['source_state'] or '-'} monitor={result['monitor_state'] or '-'}"
            )
            if result["latency_delta_ms"] is not None:
                self.stdout.write(
                    f"  latency source={result['source_latency_ms']:.1f}ms "
                    f"monitor={result['monitor_latency_ms']:.1f}ms "
                    f"delta={result['latency_delta_ms']:.1f}ms"
                )

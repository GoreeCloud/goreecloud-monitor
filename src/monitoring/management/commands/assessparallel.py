from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from monitoring.parallel import evaluate_parallel_series


class Command(BaseCommand):
    help = "Assess repeated sanitized Uptime Kuma/GoreeCloud Monitor runtime-comparison reports"

    def add_arguments(self, parser):
        parser.add_argument(
            "inputs",
            nargs="+",
            help="Paths to JSON reports produced by `compareuptimestate --json`",
        )
        parser.add_argument(
            "--minimum-observations",
            type=int,
            default=3,
            help="Minimum repeated comparison observations required for readiness (default: 3)",
        )
        parser.add_argument("--json", action="store_true", help="Write the minimized acceptance report as JSON")
        parser.add_argument(
            "--require-ready",
            action="store_true",
            help="Exit non-zero when the repeated-comparison acceptance criteria are not satisfied",
        )

    def handle(self, *args, **options):
        minimum = options["minimum_observations"]
        if minimum < 1:
            raise CommandError("--minimum-observations must be at least one")

        reports = []
        for raw_path in options["inputs"]:
            path = Path(raw_path)
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except OSError as exc:
                raise CommandError(f"could not read comparison report {path}: {exc}") from exc
            except json.JSONDecodeError as exc:
                raise CommandError(f"comparison report {path} is not valid JSON: {exc}") from exc
            reports.append(payload)

        try:
            report = evaluate_parallel_series(reports, minimum_observations=minimum)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if options["json"]:
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        else:
            summary = report["summary"]
            self.stdout.write(
                "Parallel acceptance: "
                f"ready={str(report['ready']).lower()}, observations={report['observation_count']}/"
                f"{report['minimum_observations']}, monitors={summary['monitor_count']}, "
                f"parity-observations={summary['parity_observations']}, "
                f"coverage-drift={summary['coverage_drift_observations']}."
            )
            for blocker in report["blockers"]:
                self.stdout.write(f"- BLOCKER: {blocker}")

        if options["require_ready"] and not report["ready"]:
            raise CommandError("repeated parallel-comparison acceptance criteria are not satisfied")

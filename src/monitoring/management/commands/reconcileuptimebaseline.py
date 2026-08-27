from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from monitoring.migration import load_kuma_monitors, map_kuma_monitor


DEFAULT_BASELINE = Path(__file__).resolve().parents[2] / "data" / "uptime-kuma-documented-baseline.json"


def load_baseline(path: Path) -> dict:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CommandError(f"Unable to read documented baseline: {exc}") from exc
    if document.get("schema") != "goreecloud-monitor-documented-uptime-kuma-baseline" or document.get("version") != 1:
        raise CommandError("Unsupported documented Uptime Kuma baseline schema")
    monitors = document.get("monitors")
    if not isinstance(monitors, list) or not all(isinstance(item, dict) for item in monitors):
        raise CommandError("Documented baseline monitors must be a list of objects")
    names = [str(item.get("name") or "").strip() for item in monitors]
    if any(not name for name in names) or len(names) != len(set(names)):
        raise CommandError("Documented baseline monitor names must be non-empty and unique")
    return document


def reconcile(source_monitors: list[dict], baseline: dict) -> dict:
    baseline_items = {item["name"]: item for item in baseline["monitors"]}
    expected_active = {name for name, item in baseline_items.items() if item.get("expected") == "active"}
    expected_retired = {name for name, item in baseline_items.items() if item.get("expected") == "retired"}

    raw_names = [str(item.get("name") or "").strip() for item in source_monitors]
    counts = Counter(raw_names)
    results: list[dict] = []
    seen: set[str] = set()

    for raw in source_monitors:
        name = str(raw.get("name") or "").strip()
        source_type = str(raw.get("type") or "unknown").strip().lower()
        if not name:
            results.append({"name": "<unnamed>", "type": source_type, "status": "source-invalid", "issues": []})
            continue
        if name in seen:
            continue
        seen.add(name)

        if counts[name] > 1:
            results.append({"name": name, "type": source_type, "status": "source-duplicate", "issues": []})
            continue
        if name in expected_retired:
            results.append({"name": name, "type": source_type, "status": "retired-present", "issues": []})
            continue
        if name not in expected_active:
            results.append({"name": name, "type": source_type, "status": "unexpected-live", "issues": []})
            continue

        baseline_item = baseline_items[name]
        mapping = map_kuma_monitor(raw)
        issues = [issue.to_dict() for issue in mapping.issues]
        gate = baseline_item.get("cutover_gate", "none")
        if gate == "blocker":
            status = "baseline-blocker"
            reason = str(baseline_item.get("reason") or "Documented coverage requires explicit resolution before cutover.")
            issues.append({"severity": "error", "code": "documented-cutover-blocker", "message": reason})
        elif not mapping.supported:
            status = "unsupported"
        elif gate == "review":
            status = "review"
            reason = str(baseline_item.get("reason") or "Documented coverage requires manual review.")
            issues.append({"severity": "warning", "code": "documented-review-required", "message": reason})
        elif mapping.has_warnings:
            status = "review"
        else:
            status = "matched"
        results.append({"name": name, "type": source_type, "status": status, "issues": issues})

    live_names = {name for name in raw_names if name}
    for name in sorted(expected_active - live_names):
        results.append({"name": name, "type": None, "status": "expected-missing", "issues": []})

    blocker_statuses = {
        "source-invalid",
        "source-duplicate",
        "retired-present",
        "unexpected-live",
        "baseline-blocker",
        "unsupported",
        "expected-missing",
    }
    review_statuses = {"review"}
    blockers = sum(1 for item in results if item["status"] in blocker_statuses)
    reviews = sum(1 for item in results if item["status"] in review_statuses)
    matched = sum(1 for item in results if item["status"] == "matched")

    return {
        "schema": "goreecloud-monitor-uptime-kuma-baseline-reconciliation",
        "version": 1,
        "ready": blockers == 0 and reviews == 0,
        "baseline": {
            "schema": baseline["schema"],
            "version": baseline["version"],
            "basis": baseline.get("basis", {}),
        },
        "summary": {
            "live_monitors": len(source_monitors),
            "expected_active": len(expected_active),
            "expected_retired": len(expected_retired),
            "matched": matched,
            "reviews": reviews,
            "blockers": blockers,
        },
        "monitors": sorted(results, key=lambda item: (item["name"].casefold(), item["status"])),
    }


class Command(BaseCommand):
    help = "Reconcile a live kuma-cli/Uptime Kuma export against the documented GoreeCloud baseline"

    def add_arguments(self, parser):
        parser.add_argument("input", help="Path to live kuma-cli/Uptime Kuma JSON export")
        parser.add_argument("--baseline", default=str(DEFAULT_BASELINE), help="Optional alternate documented baseline JSON")
        parser.add_argument("--json", action="store_true", help="Write the sanitized reconciliation report as JSON")
        parser.add_argument("--no-fail", action="store_true", help="Report unresolved reviews/blockers without a non-zero command result")

    def handle(self, *args, **options):
        baseline = load_baseline(Path(options["baseline"]))
        try:
            source_monitors, metadata = load_kuma_monitors(options["input"])
        except ValidationError as exc:
            raise CommandError(str(exc)) from exc

        report = reconcile(source_monitors, baseline)
        report["source"] = metadata
        if options["json"]:
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        else:
            summary = report["summary"]
            self.stdout.write(
                "Uptime Kuma documented-baseline reconciliation: "
                f"ready={report['ready']} matched={summary['matched']} reviews={summary['reviews']} "
                f"blockers={summary['blockers']} live={summary['live_monitors']}"
            )
            for item in report["monitors"]:
                if item["status"] != "matched":
                    self.stdout.write(f"- {item['name']}: {item['status'].upper()}")
                    for issue in item["issues"]:
                        self.stdout.write(f"  {issue['severity'].upper()} {issue['code']}: {issue['message']}")

        if not report["ready"] and not options["no_fail"]:
            raise CommandError("Uptime Kuma baseline reconciliation has unresolved review items or cutover blockers")

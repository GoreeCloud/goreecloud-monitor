from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from .models import Monitor


KUMA_STATUS_TO_MONITOR = {
    0: Monitor.State.DOWN,
    1: Monitor.State.UP,
    2: Monitor.State.UNKNOWN,
    3: Monitor.State.MAINTENANCE,
}

COMPARISON_SCHEMA = "goreecloud-monitor-uptime-kuma-runtime-comparison"
COMPARISON_VERSION = 1
ACCEPTANCE_SCHEMA = "goreecloud-monitor-parallel-acceptance"
ACCEPTANCE_VERSION = 1
STATUS_ORDER = (
    "match",
    "state-different",
    "latency-different",
    "missing",
    "monitor-only",
    "source-unknown",
    "source-duplicate",
    "source-invalid",
)


@dataclass(slots=True)
class SourceSnapshot:
    name: str
    state: str
    latency_ms: float | None
    status_known: bool


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def normalize_kuma_snapshot(raw: dict[str, Any]) -> SourceSnapshot:
    name = str(raw.get("name") or "").strip()
    active = raw.get("active")
    heartbeat = raw.get("heartbeat")

    if active is False or active == 0:
        return SourceSnapshot(name=name, state=Monitor.State.PAUSED, latency_ms=None, status_known=True)

    if not isinstance(heartbeat, dict):
        # kuma-cli displays an active monitor without a heartbeat as Pending.
        if active is True or active == 1:
            return SourceSnapshot(name=name, state=Monitor.State.UNKNOWN, latency_ms=None, status_known=True)
        return SourceSnapshot(name=name, state=Monitor.State.UNKNOWN, latency_ms=None, status_known=False)

    try:
        status = int(heartbeat.get("status"))
    except (TypeError, ValueError):
        status = -1

    state = KUMA_STATUS_TO_MONITOR.get(status, Monitor.State.UNKNOWN)
    return SourceSnapshot(
        name=name,
        state=state,
        latency_ms=_number(heartbeat.get("ping")),
        status_known=status in KUMA_STATUS_TO_MONITOR,
    )


def compare_runtime_snapshots(
    source_monitors: list[dict[str, Any]],
    current_monitors: list[Monitor],
    *,
    latency_tolerance_ms: float = 250.0,
) -> dict[str, Any]:
    if latency_tolerance_ms < 0:
        raise ValueError("latency tolerance must be zero or greater")

    names = [str(item.get("name") or "").strip() for item in source_monitors]
    duplicate_names = {name for name, count in Counter(names).items() if name and count > 1}
    current = {monitor.name: monitor for monitor in current_monitors}
    results: list[dict[str, Any]] = []

    for raw in source_monitors:
        snapshot = normalize_kuma_snapshot(raw)
        if not snapshot.name:
            results.append(
                {
                    "name": "<unnamed>",
                    "status": "source-invalid",
                    "source_state": snapshot.state,
                    "monitor_state": None,
                    "source_latency_ms": snapshot.latency_ms,
                    "monitor_latency_ms": None,
                    "latency_delta_ms": None,
                    "latency_within_tolerance": None,
                }
            )
            continue

        if snapshot.name in duplicate_names:
            results.append(
                {
                    "name": snapshot.name,
                    "status": "source-duplicate",
                    "source_state": snapshot.state,
                    "monitor_state": None,
                    "source_latency_ms": snapshot.latency_ms,
                    "monitor_latency_ms": None,
                    "latency_delta_ms": None,
                    "latency_within_tolerance": None,
                }
            )
            continue

        monitor = current.get(snapshot.name)
        if monitor is None:
            results.append(
                {
                    "name": snapshot.name,
                    "status": "missing",
                    "source_state": snapshot.state,
                    "monitor_state": None,
                    "source_latency_ms": snapshot.latency_ms,
                    "monitor_latency_ms": None,
                    "latency_delta_ms": None,
                    "latency_within_tolerance": None,
                }
            )
            continue

        monitor_latency = _number(monitor.response_time_ms)
        latency_delta = None
        latency_within = None
        if snapshot.latency_ms is not None and monitor_latency is not None:
            latency_delta = abs(snapshot.latency_ms - monitor_latency)
            latency_within = latency_delta <= latency_tolerance_ms

        if not snapshot.status_known:
            status = "source-unknown"
        elif snapshot.state != monitor.state:
            status = "state-different"
        elif latency_within is False:
            status = "latency-different"
        else:
            status = "match"

        results.append(
            {
                "name": snapshot.name,
                "status": status,
                "source_state": snapshot.state,
                "monitor_state": monitor.state,
                "source_latency_ms": snapshot.latency_ms,
                "monitor_latency_ms": monitor_latency,
                "latency_delta_ms": latency_delta,
                "latency_within_tolerance": latency_within,
            }
        )

    source_names = {name for name in names if name}
    for name in sorted(set(current) - source_names):
        monitor = current[name]
        results.append(
            {
                "name": name,
                "status": "monitor-only",
                "source_state": None,
                "monitor_state": monitor.state,
                "source_latency_ms": None,
                "monitor_latency_ms": _number(monitor.response_time_ms),
                "latency_delta_ms": None,
                "latency_within_tolerance": None,
            }
        )

    summary = {status: sum(1 for result in results if result["status"] == status) for status in STATUS_ORDER}
    summary["compared"] = len(results)

    return {
        "schema": COMPARISON_SCHEMA,
        "version": COMPARISON_VERSION,
        "latency_tolerance_ms": latency_tolerance_ms,
        "summary": summary,
        "monitors": results,
    }


def _validate_comparison_report(report: Any, observation: int) -> list[dict[str, Any]]:
    if not isinstance(report, dict):
        raise ValueError(f"observation {observation} is not a JSON object")
    if report.get("schema") != COMPARISON_SCHEMA or report.get("version") != COMPARISON_VERSION:
        raise ValueError(f"observation {observation} has an unsupported comparison schema or version")

    monitors = report.get("monitors")
    if not isinstance(monitors, list) or not monitors:
        raise ValueError(f"observation {observation} has no monitor comparison records")

    validated: list[dict[str, Any]] = []
    for index, result in enumerate(monitors, start=1):
        if not isinstance(result, dict):
            raise ValueError(f"observation {observation} result {index} is not an object")
        name = str(result.get("name") or "").strip()
        status = result.get("status")
        if not name:
            raise ValueError(f"observation {observation} result {index} has no monitor name")
        if status not in STATUS_ORDER:
            raise ValueError(f"observation {observation} result {index} has unsupported status {status!r}")
        validated.append({"name": name, "status": status})
    return validated


def evaluate_parallel_series(
    reports: list[dict[str, Any]],
    *,
    minimum_observations: int = 3,
) -> dict[str, Any]:
    """Evaluate repeated sanitized runtime-comparison reports without retaining target data.

    This gate proves only repeated state/latency comparison consistency. Controlled outage,
    recovery, TLS, maintenance, notification, Ping/ICMP, resolver-specific DNS, restore,
    rollback, and explicit cutover evidence remain separate acceptance requirements.
    """

    if minimum_observations < 1:
        raise ValueError("minimum observations must be at least one")
    if not reports:
        raise ValueError("at least one comparison report is required")

    blockers: list[str] = []
    status_totals = Counter({status: 0 for status in STATUS_ORDER})
    per_monitor: dict[str, Counter[str]] = defaultdict(Counter)
    baseline_names: set[str] | None = None
    parity_observations = 0
    coverage_drift_observations = 0

    for observation, report in enumerate(reports, start=1):
        results = _validate_comparison_report(report, observation)
        names = [result["name"] for result in results]
        duplicate_names = sorted(name for name, count in Counter(names).items() if count > 1)
        current_names = set(names)

        if duplicate_names:
            blockers.append(f"observation-{observation}: duplicate result names: {', '.join(duplicate_names)}")

        if baseline_names is None:
            baseline_names = current_names
        elif current_names != baseline_names:
            coverage_drift_observations += 1
            missing = sorted(baseline_names - current_names)
            added = sorted(current_names - baseline_names)
            detail: list[str] = []
            if missing:
                detail.append(f"missing={','.join(missing)}")
            if added:
                detail.append(f"added={','.join(added)}")
            blockers.append(f"observation-{observation}: coverage drift ({'; '.join(detail)})")

        observation_has_blocker = bool(duplicate_names)
        for result in results:
            name = result["name"]
            status = result["status"]
            status_totals[status] += 1
            per_monitor[name]["observations"] += 1
            per_monitor[name][status] += 1
            if status != "match":
                observation_has_blocker = True

        if not observation_has_blocker and (baseline_names is None or current_names == baseline_names):
            parity_observations += 1

    observation_count = len(reports)
    if observation_count < minimum_observations:
        blockers.append(
            f"insufficient observations: {observation_count} collected, {minimum_observations} required"
        )

    non_match_total = sum(status_totals[status] for status in STATUS_ORDER if status != "match")
    if non_match_total:
        blockers.append(f"non-parity comparison results: {non_match_total}")

    ready = (
        observation_count >= minimum_observations
        and parity_observations == observation_count
        and coverage_drift_observations == 0
        and non_match_total == 0
        and not any("duplicate result names" in blocker for blocker in blockers)
    )

    monitor_summaries = []
    for name in sorted(per_monitor):
        counts = per_monitor[name]
        monitor_summaries.append(
            {
                "name": name,
                "observations": counts["observations"],
                **{status: counts[status] for status in STATUS_ORDER},
            }
        )

    return {
        "schema": ACCEPTANCE_SCHEMA,
        "version": ACCEPTANCE_VERSION,
        "minimum_observations": minimum_observations,
        "observation_count": observation_count,
        "ready": ready,
        "blockers": blockers,
        "summary": {
            "monitor_count": len(baseline_names or set()),
            "parity_observations": parity_observations,
            "non_parity_observations": observation_count - parity_observations,
            "coverage_drift_observations": coverage_drift_observations,
            "status_totals": {status: status_totals[status] for status in STATUS_ORDER},
        },
        "monitors": monitor_summaries,
    }

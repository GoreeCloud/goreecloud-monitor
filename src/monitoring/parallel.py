from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from .models import Monitor


KUMA_STATUS_TO_MONITOR = {
    0: Monitor.State.DOWN,
    1: Monitor.State.UP,
    2: Monitor.State.UNKNOWN,
    3: Monitor.State.MAINTENANCE,
}


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

    status_order = (
        "match",
        "state-different",
        "latency-different",
        "missing",
        "monitor-only",
        "source-unknown",
        "source-duplicate",
        "source-invalid",
    )
    summary = {status: sum(1 for result in results if result["status"] == status) for status in status_order}
    summary["compared"] = len(results)

    return {
        "schema": "goreecloud-monitor-uptime-kuma-runtime-comparison",
        "version": 1,
        "latency_tolerance_ms": latency_tolerance_ms,
        "summary": summary,
        "monitors": results,
    }

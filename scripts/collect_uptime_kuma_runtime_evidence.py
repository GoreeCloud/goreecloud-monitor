#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from monitoring.kuma_sanitize import sanitize_runtime_document  # noqa: E402


SCHEMA = "goreecloud-monitor-uptime-kuma-runtime-evidence"
VERSION = 1

# The helper runs inside the existing Uptime Kuma container and uses the
# socket.io-client dependency already installed by Uptime Kuma. The protected
# login token is supplied only on stdin. The helper emits only the fields needed
# for runtime-state comparison; heartbeat messages and monitor targets never
# leave the container through this process.
NODE_HELPER = r"""
const fs = require("fs");
const { io } = require("socket.io-client");

const token = fs.readFileSync(0, "utf8").trim();
if (!token) {
    process.stdout.write(JSON.stringify({ ok: false, error: "missing-token" }));
    process.exit(2);
}

const socket = io("http://127.0.0.1:3001", {
    reconnection: false,
    timeout: 10000,
    transports: ["websocket", "polling"],
});

let loginComplete = false;
let monitorDocument = null;
const heartbeatLists = new Map();
let finished = false;

function fail(code) {
    if (finished) return;
    finished = true;
    process.stdout.write(JSON.stringify({ ok: false, error: code }), () => {
        socket.close();
        process.exit(2);
    });
}

function normalizeMonitors(value) {
    if (Array.isArray(value)) return value;
    if (value && typeof value === "object") return Object.values(value);
    return null;
}

function maybeFinish() {
    if (finished || !loginComplete || monitorDocument === null) return;
    const monitors = normalizeMonitors(monitorDocument);
    if (!monitors || monitors.some((item) => !item || typeof item !== "object")) {
        fail("invalid-monitor-list");
        return;
    }

    const ids = monitors.map((item) => Number(item.id));
    if (ids.some((id) => !Number.isInteger(id))) {
        fail("invalid-monitor-id");
        return;
    }
    if (!ids.every((id) => heartbeatLists.has(id))) return;

    const data = monitors.map((monitor) => {
        const beats = heartbeatLists.get(Number(monitor.id));
        const latest = Array.isArray(beats) && beats.length ? beats[beats.length - 1] : null;
        return {
            id: monitor.id,
            name: monitor.name,
            type: monitor.type,
            active: monitor.active,
            heartbeat: latest
                ? { status: latest.status, ping: latest.ping }
                : null,
        };
    });

    finished = true;
    process.stdout.write(JSON.stringify({ ok: true, data }), () => {
        socket.close();
        process.exit(0);
    });
}

socket.on("monitorList", (value) => {
    monitorDocument = value;
    maybeFinish();
});

socket.on("heartbeatList", (monitorID, beats) => {
    const id = Number(monitorID);
    if (Number.isInteger(id)) {
        heartbeatLists.set(id, Array.isArray(beats) ? beats : []);
    }
    maybeFinish();
});

socket.on("connect_error", () => fail("connection-failed"));
socket.on("error", () => fail("socket-error"));

socket.on("connect", () => {
    socket.emit("loginByToken", token, (response) => {
        if (!response || response.ok !== true) {
            fail("authentication-failed");
            return;
        }
        loginComplete = true;
        maybeFinish();
    });
});

setTimeout(() => fail("runtime-evidence-timeout"), 20000);
""".strip()


def _default_token_file() -> Path:
    config_home = os.environ.get("XDG_CONFIG_HOME")
    root = Path(config_home).expanduser() if config_home else Path.home() / ".config"
    return root / "autokuma" / "auth.txt"


def _load_protected_token(path: Path) -> str:
    try:
        metadata = path.stat()
    except OSError as exc:
        raise ValueError("protected kuma-cli token file is unavailable") from exc

    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("protected kuma-cli token path is not a regular file")
    if metadata.st_uid != os.getuid():
        raise ValueError("protected kuma-cli token file is not owned by the current user")
    if metadata.st_mode & 0o077:
        raise ValueError("protected kuma-cli token file has group or other permissions")

    try:
        token = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ValueError("protected kuma-cli token file is not readable") from exc
    if not token:
        raise ValueError("protected kuma-cli token file is empty")
    return token


def _git_revision() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _uptime_image(container: str) -> str | None:
    try:
        completed = subprocess.run(
            ["docker", "inspect", "--format", "{{.Config.Image}}", container],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _collect_raw_runtime(container: str, token: str, *, timeout: int = 35) -> dict[str, Any]:
    command = [
        "docker",
        "exec",
        "-i",
        "-w",
        "/app",
        container,
        "node",
        "-e",
        NODE_HELPER,
    ]
    try:
        completed = subprocess.run(
            command,
            input=token + "\n",
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "LC_ALL": "C"},
        )
    except FileNotFoundError as exc:
        raise ValueError("docker command is unavailable") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError("runtime evidence helper timed out") from exc
    except OSError as exc:
        raise ValueError("runtime evidence helper could not execute") from exc

    if completed.returncode != 0:
        # Failed stdout/stderr are deliberately omitted from the operator error
        # because unexpected provider output can contain operational details.
        raise ValueError("runtime evidence helper failed; raw output omitted")

    try:
        document = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("runtime evidence helper did not return JSON") from exc
    if not isinstance(document, dict) or document.get("ok") is not True:
        raise ValueError("runtime evidence helper did not return a successful document")
    if not isinstance(document.get("data"), list):
        raise ValueError("runtime evidence helper returned an invalid data collection")
    return document


def _validate_runtime_completeness(document: dict[str, Any]) -> dict[str, int]:
    data = document.get("data")
    if not isinstance(data, list) or not data:
        raise ValueError("runtime evidence contains no monitors")

    ids: set[int] = set()
    names: set[str] = set()
    active = 0
    heartbeat_present = 0

    for item in data:
        if not isinstance(item, dict):
            raise ValueError("runtime evidence entries must be objects")
        try:
            monitor_id = int(item.get("id"))
        except (TypeError, ValueError) as exc:
            raise ValueError("runtime evidence contains an invalid monitor id") from exc
        if monitor_id in ids:
            raise ValueError("runtime evidence contains duplicate monitor ids")
        ids.add(monitor_id)

        name = str(item.get("name") or "").strip()
        if not name:
            raise ValueError("runtime evidence contains an unnamed monitor")
        if name.casefold() in names:
            raise ValueError("runtime evidence contains duplicate monitor names")
        names.add(name.casefold())

        active_value = item.get("active")
        if active_value not in (True, False, 0, 1):
            raise ValueError("runtime evidence contains an invalid active state")
        is_active = bool(active_value)
        if is_active:
            active += 1

        heartbeat = item.get("heartbeat")
        if heartbeat is None:
            if is_active:
                raise ValueError("an active monitor has no heartbeat history")
            continue
        if not isinstance(heartbeat, dict):
            raise ValueError("runtime evidence contains an invalid heartbeat")
        status_value = heartbeat.get("status")
        if not isinstance(status_value, int) or status_value not in {0, 1, 2, 3}:
            raise ValueError("runtime evidence contains an invalid heartbeat status")
        ping = heartbeat.get("ping")
        if ping is not None and not isinstance(ping, (int, float)):
            raise ValueError("runtime evidence contains an invalid heartbeat response time")
        heartbeat_present += 1

    return {
        "monitors": len(data),
        "active_monitors": active,
        "monitors_with_heartbeat": heartbeat_present,
    }


def _write_checksums(output_dir: Path) -> None:
    lines: list[str] = []
    for path in sorted(output_dir.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.name == "SHA256SUMS":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}")
    (output_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _archive(output_dir: Path) -> Path:
    archive = output_dir.with_suffix(".tar.gz")
    with tarfile.open(archive, "w:gz") as handle:
        handle.add(output_dir, arcname=output_dir.name)
    os.chmod(archive, 0o600)
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect minimized, read-only Uptime Kuma runtime evidence for GoreeCloud Monitor comparison"
    )
    parser.add_argument("--output-dir", help="Evidence directory; defaults to a timestamped directory")
    parser.add_argument("--uptime-container", default="uptime-kuma", help="Uptime Kuma container name")
    parser.add_argument(
        "--token-file",
        help="Protected kuma-cli token file; defaults to the AutoKuma local config auth.txt path",
    )
    parser.add_argument("--no-archive", action="store_true", help="Do not create a tar.gz copy of the bundle")
    args = parser.parse_args()

    os.umask(0o077)
    now = datetime.now(timezone.utc)
    output_dir = Path(
        args.output_dir
        or f"goreecloud-monitor-runtime-evidence-{now.strftime('%Y%m%dT%H%M%SZ')}"
    ).expanduser().resolve()

    try:
        output_dir.mkdir(parents=True, exist_ok=False)
        os.chmod(output_dir, 0o700)
        token_file = Path(args.token_file).expanduser() if args.token_file else _default_token_file()
        token = _load_protected_token(token_file)
        raw_document = _collect_raw_runtime(args.uptime_container, token)
        # Drop the reusable token reference immediately after collection. Python
        # does not guarantee memory zeroization, but the value is never written,
        # logged, placed in argv/environment, or retained in the evidence bundle.
        token = ""

        summary = _validate_runtime_completeness(raw_document)
        sanitized = sanitize_runtime_document(raw_document)
        runtime_path = output_dir / "uptime-kuma-runtime.sanitized.json"
        runtime_path.write_text(json.dumps(sanitized, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        evidence = {
            "schema": SCHEMA,
            "version": VERSION,
            "collected_at": now.isoformat(),
            "collector_revision": _git_revision() or "unknown",
            "source": "uptime-kuma-authenticated-socket-heartbeat-list",
            "uptime_kuma": {
                "container": args.uptime_container,
                "image": _uptime_image(args.uptime_container),
            },
            "summary": summary,
            "safety": {
                "mode": "read-only-runtime-evidence",
                "sudo_invoked": False,
                "token_retained": False,
                "token_path_retained": False,
                "token_passed_in_argv": False,
                "token_passed_in_environment": False,
                "raw_runtime_retained": False,
                "heartbeat_messages_retained": False,
                "monitor_targets_retained": False,
                "uptime_configuration_modified": False,
            },
            "runtime_file": runtime_path.name,
            "ready_for_comparison": True,
        }
        evidence_path = output_dir / "runtime-evidence.json"
        evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _write_checksums(output_dir)
        archive = None if args.no_archive else _archive(output_dir)
    except (OSError, ValueError) as exc:
        print(f"Runtime evidence collection failed: {exc}", file=sys.stderr)
        return 2

    print(f"Evidence directory: {output_dir}")
    if archive is not None:
        print(f"Evidence archive:   {archive}")
    print(f"Runtime monitors:   {summary['monitors']}")
    print(f"Active monitors:    {summary['active_monitors']}")
    print(f"Heartbeat coverage: {summary['monitors_with_heartbeat']}")
    print("Ready for comparison: True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

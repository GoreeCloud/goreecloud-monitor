#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from monitoring.kuma_sanitize import sanitize_config_document, sanitize_runtime_document  # noqa: E402


SCHEMA = "goreecloud-monitor-live-acceptance-evidence"
VERSION = 1


def _run(label: str, args: list[str], *, timeout: int = 30) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "LC_ALL": "C"},
        )
    except FileNotFoundError:
        return {"label": label, "ok": False, "error": "command-not-found"}
    except subprocess.TimeoutExpired:
        return {"label": label, "ok": False, "error": "timeout"}
    except OSError:
        return {"label": label, "ok": False, "error": "execution-failed"}

    result: dict[str, Any] = {
        "label": label,
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
    }
    if completed.returncode == 0:
        result["stdout"] = completed.stdout.strip()
    else:
        # stderr is intentionally not copied into the evidence bundle because
        # command errors can echo connection/configuration material.
        result["error"] = "command-failed-stderr-omitted"
    return result


def _safe_stdout(result: dict[str, Any]) -> str | None:
    if result.get("ok"):
        return str(result.get("stdout") or "")
    return None


def _json_from_stdout(result: dict[str, Any]) -> Any | None:
    text = _safe_stdout(result)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _git_revision() -> str | None:
    result = _run("collector-revision", ["git", "-C", str(ROOT), "rev-parse", "HEAD"])
    return _safe_stdout(result)


def _read_os_release() -> dict[str, str]:
    allowed = {"ID", "VERSION_ID", "PRETTY_NAME"}
    values: dict[str, str] = {}
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key in allowed:
                values[key] = value.strip().strip('"')
    except OSError:
        pass
    return values


def _fingerprint(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return result
    try:
        stat = path.stat()
        result.update(
            {
                "size": stat.st_size,
                "mode": oct(stat.st_mode & 0o777),
                "uid": stat.st_uid,
                "gid": stat.st_gid,
            }
        )
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        result["sha256"] = digest.hexdigest()
    except OSError:
        result["readable"] = False
    else:
        result["readable"] = True
    return result


def _parse_docker_ps(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        while len(parts) < 5:
            parts.append("")
        rows.append(
            {
                "name": parts[0],
                "image": parts[1],
                "status": parts[2],
                "ports": parts[3],
                "networks": parts[4],
            }
        )
    return rows


def _docker_evidence(uptime_container: str, uptime_compose: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    commands: list[dict[str, Any]] = []
    docker_version = _run("docker-server-version", ["docker", "version", "--format", "{{.Server.Version}}"])
    commands.append(docker_version)
    compose_version = _run("docker-compose-version", ["docker", "compose", "version", "--short"])
    commands.append(compose_version)
    docker_ps = _run(
        "docker-ps",
        ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}\t{{.Networks}}"],
    )
    commands.append(docker_ps)

    image = _run("uptime-image", ["docker", "inspect", "--format", "{{.Config.Image}}", uptime_container])
    status = _run("uptime-status", ["docker", "inspect", "--format", "{{.State.Status}}", uptime_container])
    health = _run(
        "uptime-health",
        ["docker", "inspect", "--format", "{{if .State.Health}}{{.State.Health.Status}}{{end}}", uptime_container],
    )
    networks_result = _run(
        "uptime-networks",
        ["docker", "inspect", "--format", "{{json .NetworkSettings.Networks}}", uptime_container],
    )
    commands.extend([image, status, health, networks_result])

    compose_services = _run(
        "uptime-compose-services",
        ["docker", "compose", "-f", str(uptime_compose), "config", "--services"],
    )
    compose_images = _run(
        "uptime-compose-images",
        ["docker", "compose", "-f", str(uptime_compose), "config", "--images"],
    )
    commands.extend([compose_services, compose_images])

    network_summary: list[dict[str, Any]] = []
    network_document = _json_from_stdout(networks_result)
    if isinstance(network_document, dict):
        for network_name, details in sorted(network_document.items()):
            if not isinstance(details, dict):
                continue
            ipam = _run(
                f"network-ipam:{network_name}",
                ["docker", "network", "inspect", "--format", "{{json .IPAM.Config}}", network_name],
            )
            commands.append(ipam)
            network_summary.append(
                {
                    "name": network_name,
                    "uptime_ipv4": details.get("IPAddress"),
                    "uptime_gateway": details.get("Gateway"),
                    "ipam": _json_from_stdout(ipam),
                }
            )

    evidence = {
        "server_version": _safe_stdout(docker_version),
        "compose_version": _safe_stdout(compose_version),
        "containers": _parse_docker_ps(_safe_stdout(docker_ps) or ""),
        "uptime_kuma": {
            "container": uptime_container,
            "image": _safe_stdout(image),
            "status": _safe_stdout(status),
            "health": _safe_stdout(health),
            "compose_services": (_safe_stdout(compose_services) or "").splitlines(),
            "compose_images": (_safe_stdout(compose_images) or "").splitlines(),
            "networks": network_summary,
        },
    }
    return evidence, commands


def _collect_kuma(output_dir: Path, kuma_bin: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    commands: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "available": shutil.which(kuma_bin) is not None,
        "config_export": None,
        "runtime_snapshot": None,
    }
    if not result["available"]:
        return result, commands

    with tempfile.TemporaryDirectory(prefix="goreecloud-monitor-kuma-") as temp_name:
        temp_dir = Path(temp_name)
        raw_export = temp_dir / "uptime-kuma-export.sensitive.json"
        export = _run(
            "kuma-config-export",
            [kuma_bin, "config", "export", "--output", str(raw_export)],
            timeout=90,
        )
        commands.append(export)
        if export.get("ok") and raw_export.exists():
            try:
                raw_document = json.loads(raw_export.read_text(encoding="utf-8"))
                sanitized, sanitization_report = sanitize_config_document(raw_document)
                config_path = output_dir / "uptime-kuma-config.sanitized.json"
                config_path.write_text(json.dumps(sanitized, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                report_path = output_dir / "uptime-kuma-sanitization-report.json"
                report_path.write_text(
                    json.dumps(sanitization_report, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                result["config_export"] = {
                    "ok": True,
                    "file": config_path.name,
                    "sanitization_report": report_path.name,
                    "summary": {
                        key: sanitization_report[key]
                        for key in (
                            "source_format",
                            "source_monitors",
                            "monitors_with_redactions",
                            "monitors_with_omissions",
                        )
                    },
                }
            except (OSError, json.JSONDecodeError, ValueError):
                result["config_export"] = {"ok": False, "error": "export-sanitization-failed"}
        else:
            result["config_export"] = {"ok": False, "error": export.get("error", "export-failed")}

        runtime = _run("kuma-monitor-list", [kuma_bin, "monitors", "list", "--json"], timeout=90)
        commands.append(runtime)
        runtime_document = _json_from_stdout(runtime)
        if runtime_document is not None:
            try:
                sanitized_runtime = sanitize_runtime_document(runtime_document)
                runtime_path = output_dir / "uptime-kuma-runtime.sanitized.json"
                runtime_path.write_text(
                    json.dumps(sanitized_runtime, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                result["runtime_snapshot"] = {
                    "ok": True,
                    "file": runtime_path.name,
                    "source_monitors": sanitized_runtime["__goreecloud_sanitization"]["source_monitors"],
                }
            except ValueError:
                result["runtime_snapshot"] = {"ok": False, "error": "runtime-sanitization-failed"}
        else:
            result["runtime_snapshot"] = {"ok": False, "error": runtime.get("error", "runtime-export-failed")}

    return result, commands


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
        description="Collect a sanitized, read-only GoreeCloud Monitor live-acceptance evidence bundle"
    )
    parser.add_argument("--output-dir", help="Evidence directory; defaults to a timestamped directory")
    parser.add_argument(
        "--uptime-compose",
        default="/srv/docker/stacks/uptime-kuma/docker-compose.yml",
        help="Current Uptime Kuma Compose file path; content is never copied",
    )
    parser.add_argument(
        "--caddyfile",
        default="/srv/docker/caddy/Caddyfile",
        help="Current production Caddyfile path; content is never copied",
    )
    parser.add_argument("--uptime-container", default="uptime-kuma", help="Uptime Kuma container name")
    parser.add_argument("--kuma-bin", default="kuma", help="kuma-cli executable name/path")
    parser.add_argument("--skip-kuma", action="store_true", help="Skip kuma-cli export/snapshot collection")
    parser.add_argument("--no-archive", action="store_true", help="Do not create a tar.gz copy of the bundle")
    args = parser.parse_args()

    os.umask(0o077)
    now = datetime.now(timezone.utc)
    default_name = f"goreecloud-monitor-live-evidence-{now.strftime('%Y%m%dT%H%M%SZ')}"
    output_dir = Path(args.output_dir or default_name).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    os.chmod(output_dir, 0o700)

    command_results: list[dict[str, Any]] = []
    hostname = _run("hostname", ["hostname"])
    current_user = _run("current-user", ["id", "-un"])
    addresses = _run("ip-addresses", ["ip", "-brief", "address", "show"])
    routes = _run("ip-routes", ["ip", "route", "show"])
    listeners = _run("listening-sockets", ["ss", "-H", "-lntu"])
    command_results.extend([hostname, current_user, addresses, routes, listeners])

    uptime_compose = Path(args.uptime_compose)
    caddyfile = Path(args.caddyfile)
    docker, docker_commands = _docker_evidence(args.uptime_container, uptime_compose)
    command_results.extend(docker_commands)

    if args.skip_kuma:
        kuma = {"available": None, "skipped": True, "config_export": None, "runtime_snapshot": None}
    else:
        kuma, kuma_commands = _collect_kuma(output_dir, args.kuma_bin)
        command_results.extend(kuma_commands)

    failures = [
        {"label": item["label"], "returncode": item.get("returncode"), "error": item.get("error")}
        for item in command_results
        if not item.get("ok")
    ]
    config_export = kuma.get("config_export")
    runtime_snapshot = kuma.get("runtime_snapshot")
    ready_for_review = (
        not failures
        and isinstance(config_export, dict)
        and bool(config_export.get("ok"))
        and isinstance(runtime_snapshot, dict)
        and bool(runtime_snapshot.get("ok"))
    )

    evidence = {
        "schema": SCHEMA,
        "version": VERSION,
        "collected_at": now.isoformat(),
        "collector_revision": _git_revision() or "unknown",
        "safety": {
            "mode": "read-only-live-evidence",
            "sudo_invoked": False,
            "raw_uptime_export_retained": False,
            "stderr_retained": False,
            "caddyfile_content_retained": False,
            "compose_content_retained": False,
        },
        "host": {
            "hostname": _safe_stdout(hostname),
            "current_user": _safe_stdout(current_user),
            "platform": platform.platform(),
            "os_release": _read_os_release(),
            "addresses": (_safe_stdout(addresses) or "").splitlines(),
            "routes": (_safe_stdout(routes) or "").splitlines(),
            "listening_sockets": (_safe_stdout(listeners) or "").splitlines(),
        },
        "files": {
            "uptime_kuma_compose": _fingerprint(uptime_compose),
            "production_caddyfile": _fingerprint(caddyfile),
        },
        "docker": docker,
        "uptime_kuma": kuma,
        "collection_failures": failures,
        "ready_for_review": ready_for_review,
    }

    evidence_path = output_dir / "target-evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_checksums(output_dir)

    archive = None if args.no_archive else _archive(output_dir)
    print(f"Evidence directory: {output_dir}")
    if archive is not None:
        print(f"Evidence archive:   {archive}")
    print(f"Ready for review:   {evidence['ready_for_review']}")
    if failures:
        print("Some read-only evidence commands failed; inspect collection_failures in target-evidence.json.")
    return 0 if evidence["ready_for_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the resolved GoreeCloud Monitor production Compose contract.

Input is canonical JSON from `docker compose -f compose.production.yml config --format json`.
The checks intentionally validate source-level invariants only; they do not claim that a live
Caddy network, firewall, NetBird policy, host path, or backup target is correct.
"""
from __future__ import annotations

import json
import sys
from typing import Any


APP_SERVICES = {"migrate", "web", "worker"}
EXPECTED_SERVICES = {"db", *APP_SERVICES}


def fail(message: str) -> None:
    raise SystemExit(f"production-compose validation failed: {message}")


def network_names(service: dict[str, Any]) -> set[str]:
    networks = service.get("networks", {})
    if isinstance(networks, list):
        return set(networks)
    return set(networks)


def main() -> None:
    try:
        model = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        fail(f"invalid canonical JSON: {exc}")

    services = model.get("services", {})
    if set(services) != EXPECTED_SERVICES:
        fail(f"expected services {sorted(EXPECTED_SERVICES)}, got {sorted(services)}")

    for name, service in services.items():
        if service.get("ports"):
            fail(f"{name} publishes a host port")
        if service.get("privileged") is True:
            fail(f"{name} is privileged")
        if service.get("cap_add"):
            fail(f"{name} adds Linux capabilities")
        if service.get("network_mode") == "host":
            fail(f"{name} uses host networking")
        if service.get("pid") == "host" or service.get("ipc") == "host":
            fail(f"{name} shares a host namespace")
        if service.get("devices"):
            fail(f"{name} receives a device mapping")
        for volume in service.get("volumes", []) or []:
            target = volume.get("target", "") if isinstance(volume, dict) else str(volume)
            if "docker.sock" in target:
                fail(f"{name} mounts the Docker socket")

    for name in APP_SERVICES:
        service = services[name]
        if service.get("build"):
            fail(f"{name} builds from mutable source in the production Compose file")
        image = str(service.get("image") or "")
        if not image or image.endswith(":latest") or image == "latest":
            fail(f"{name} does not use a traceable application image reference")
        if service.get("read_only") is not True:
            fail(f"{name} root filesystem is not read-only")
        if "ALL" not in set(service.get("cap_drop") or []):
            fail(f"{name} does not drop all Linux capabilities")
        security_opt = {str(item).replace("=", ":").lower() for item in service.get("security_opt") or []}
        if not any(item.startswith("no-new-privileges") for item in security_opt):
            fail(f"{name} does not enable no-new-privileges")
        if not service.get("tmpfs"):
            fail(f"{name} has no bounded writable temporary filesystem")

    for name in {"migrate", "web"}:
        if services[name].get("sysctls"):
            fail(f"{name} receives a network sysctl despite not performing ICMP checks")
    worker_sysctls = services["worker"].get("sysctls") or {}
    if worker_sysctls.get("net.ipv4.ping_group_range") != "999 999":
        fail("worker ping_group_range must be restricted to the deterministic Monitor group 999")

    db = services["db"]
    db_image = str(db.get("image") or "")
    if "@sha256:" not in db_image:
        fail("db image is not pinned by digest")
    if network_names(db) != {"backend"}:
        fail("db is attached to a network other than backend")
    db_volumes = db.get("volumes") or []
    if len(db_volumes) != 1 or not isinstance(db_volumes[0], dict):
        fail("db must have exactly one explicit persistent-data bind mount")
    db_volume = db_volumes[0]
    if db_volume.get("type") != "bind" or db_volume.get("target") != "/var/lib/postgresql/data":
        fail("db persistence must be an explicit bind mount to /var/lib/postgresql/data")

    if network_names(services["migrate"]) != {"backend"}:
        fail("migrate must be isolated to the backend network")
    if network_names(services["web"]) != {"backend", "proxy"}:
        fail("web must be attached only to backend and proxy")
    if network_names(services["worker"]) != {"backend", "proxy"}:
        fail("worker must be attached only to backend and proxy")

    networks = model.get("networks", {})
    backend = networks.get("backend", {})
    proxy = networks.get("proxy", {})
    if backend.get("internal") is not True:
        fail("backend network is not internal")
    if proxy.get("external") is not True:
        fail("proxy network is not external")

    print("production-compose validation passed")


if __name__ == "__main__":
    main()

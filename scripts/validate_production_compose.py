#!/usr/bin/env python3
"""Validate the resolved GoreeCloud Monitor production Compose contract.

Input is canonical JSON from `docker compose -f compose.production.yml config --format json`.
The checks intentionally validate source-level invariants only; they do not claim that a live
Caddy network, firewall, NetBird policy, host path, or backup target is correct.
"""
from __future__ import annotations

import ipaddress
import json
import re
import sys
from typing import Any


APP_SERVICES = {"migrate", "web", "worker"}
EXPECTED_SERVICES = {"db", *APP_SERVICES}
NOTIFY_PRODUCER_ENV_KEYS = {
    "MONITOR_NOTIFY_ENABLED",
    "GOREECLOUD_NOTIFY_BASE_URL",
    "GOREECLOUD_NOTIFY_TOKEN",
    "MONITOR_NOTIFY_MAX_ATTEMPTS",
    "MONITOR_NOTIFY_RETRY_BACKOFF_SECONDS",
    "MONITOR_NOTIFY_TIMEOUT_SECONDS",
    "MONITOR_NOTIFICATION_OUTBOX_RETENTION_DAYS",
}


def fail(message: str) -> None:
    raise SystemExit(f"production-compose validation failed: {message}")


def network_names(service: dict[str, Any]) -> set[str]:
    networks = service.get("networks", {})
    if isinstance(networks, list):
        return set(networks)
    return set(networks)


def environment_keys(service: dict[str, Any]) -> set[str]:
    raw = service.get("environment") or {}
    if not isinstance(raw, dict):
        fail("service environment must resolve to a mapping")
    return {str(key) for key in raw}


def normalized_extra_hosts(service: dict[str, Any]) -> dict[str, str]:
    raw = service.get("extra_hosts") or []
    if isinstance(raw, dict):
        return {str(host): str(address) for host, address in raw.items()}
    if not isinstance(raw, list):
        fail("extra_hosts must resolve to a list or mapping")

    entries: dict[str, str] = {}
    for item in raw:
        text = str(item)
        if "=" in text:
            host, address = text.split("=", 1)
        elif ":" in text:
            host, address = text.rsplit(":", 1)
        else:
            fail("extra_hosts contains an invalid entry")
        host = host.strip()
        address = address.strip()
        if not host or not address:
            fail("extra_hosts contains an empty host or address")
        if host in entries:
            fail(f"extra_hosts contains duplicate host {host}")
        entries[host] = address
    return entries


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

    for name in {"db", "migrate", "web"}:
        leaked_notify_keys = NOTIFY_PRODUCER_ENV_KEYS & environment_keys(services[name])
        if leaked_notify_keys:
            fail(
                f"{name} receives worker-only Notify producer environment keys: "
                + ", ".join(sorted(leaked_notify_keys))
            )

    worker_environment_keys = environment_keys(services["worker"])
    missing_notify_keys = NOTIFY_PRODUCER_ENV_KEYS - worker_environment_keys
    if missing_notify_keys:
        fail(
            "worker is missing required Notify producer environment keys: "
            + ", ".join(sorted(missing_notify_keys))
        )

    for name in {"db", "migrate", "web"}:
        if services[name].get("dns"):
            fail(f"{name} receives a DNS override despite not executing monitor target checks")
    worker_dns = services["worker"].get("dns") or []
    if not isinstance(worker_dns, list) or len(worker_dns) != 1:
        fail("worker must use exactly one explicit private DNS resolver")
    try:
        worker_dns_address = ipaddress.ip_address(str(worker_dns[0]))
    except ValueError:
        fail("worker DNS resolver is not an IP address")
    if worker_dns_address.version != 4 or not worker_dns_address.is_private:
        fail("worker DNS resolver must be a private IPv4 address")

    for name in {"db", "migrate", "web"}:
        if normalized_extra_hosts(services[name]):
            fail(f"{name} receives an extra_hosts override despite not publishing to GoreeCloud Notify")

    worker_extra_hosts = normalized_extra_hosts(services["worker"])
    if set(worker_extra_hosts) != {"notify.goreecloud.com"}:
        fail("worker must map exactly notify.goreecloud.com through extra_hosts")
    try:
        notify_gateway_address = ipaddress.ip_address(worker_extra_hosts["notify.goreecloud.com"])
    except ValueError:
        fail("worker Notify gateway mapping is not an IP address")
    if notify_gateway_address.version != 4 or not notify_gateway_address.is_private:
        fail("worker Notify gateway mapping must use a private IPv4 address")

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

    backend_driver_opts = backend.get("driver_opts") or {}
    backend_bridge_name = str(backend_driver_opts.get("com.docker.network.bridge.name") or "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,15}", backend_bridge_name):
        fail("backend bridge name must be an explicit Linux interface-safe name of at most 15 characters")

    backend_ipam = backend.get("ipam") or {}
    backend_ipam_config = backend_ipam.get("config") or []
    if len(backend_ipam_config) != 1:
        fail("backend network must have exactly one explicit IPAM configuration")
    backend_network_config = backend_ipam_config[0]
    try:
        backend_subnet = ipaddress.ip_network(str(backend_network_config.get("subnet")), strict=True)
        backend_gateway = ipaddress.ip_address(str(backend_network_config.get("gateway")))
    except ValueError:
        fail("backend network IPAM contains an invalid subnet or gateway")
    if backend_subnet.version != 4 or not backend_subnet.is_private:
        fail("backend network subnet must be private IPv4")
    if backend_gateway != worker_dns_address or backend_gateway not in backend_subnet:
        fail("worker DNS resolver must equal the private backend network gateway")

    worker_networks = services["worker"].get("networks") or {}
    worker_backend = worker_networks.get("backend") if isinstance(worker_networks, dict) else None
    if not isinstance(worker_backend, dict) or not worker_backend.get("ipv4_address"):
        fail("worker must have an explicit backend IPv4 address")
    try:
        worker_backend_address = ipaddress.ip_address(str(worker_backend["ipv4_address"]))
    except ValueError:
        fail("worker backend IPv4 address is invalid")
    if (
        worker_backend_address.version != 4
        or not worker_backend_address.is_private
        or worker_backend_address not in backend_subnet
        or worker_backend_address == backend_gateway
    ):
        fail("worker backend IPv4 address must be a private host address inside the backend subnet")

    worker_proxy = worker_networks.get("proxy") if isinstance(worker_networks, dict) else None
    if not isinstance(worker_proxy, dict) or not worker_proxy.get("ipv4_address"):
        fail("worker must have an explicit proxy IPv4 address")
    try:
        worker_proxy_address = ipaddress.ip_address(str(worker_proxy["ipv4_address"]))
    except ValueError:
        fail("worker proxy IPv4 address is invalid")
    if worker_proxy_address.version != 4 or not worker_proxy_address.is_private:
        fail("worker proxy IPv4 address must be private IPv4")
    if worker_proxy_address == worker_backend_address:
        fail("worker proxy and backend IPv4 addresses must be distinct")
    if notify_gateway_address in {worker_dns_address, worker_backend_address, worker_proxy_address}:
        fail("worker Notify gateway mapping must identify a distinct gateway endpoint")
    if notify_gateway_address in backend_subnet:
        fail("worker Notify gateway mapping must not route through the backend network")

    print("production-compose validation passed")


if __name__ == "__main__":
    main()

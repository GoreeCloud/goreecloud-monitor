"""Target validation and SSRF guardrails for active monitor checks."""
from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError

ALLOWED_DNS_TYPES = {"A", "AAAA", "CNAME"}


def validate_target_syntax(kind: str, target: str, port: int | None = None) -> None:
    target = (target or "").strip()
    if kind in {"HTTP", "HTTPS"}:
        parsed = urlsplit(target)
        required_scheme = kind.lower()
        if parsed.scheme != required_scheme:
            raise ValidationError(f"{kind} monitors require a {required_scheme}:// URL")
        if not parsed.hostname:
            raise ValidationError("A target hostname is required")
        if parsed.username or parsed.password:
            raise ValidationError("Credentials in monitor URLs are not permitted")
        if parsed.fragment:
            raise ValidationError("URL fragments are not sent to servers and are not valid monitor targets")
    elif kind == "TCP":
        if not target or any(char in target for char in "/?#@"):
            raise ValidationError("TCP target must be a hostname or IP address")
        if not port or not 1 <= int(port) <= 65535:
            raise ValidationError("TCP monitors require a port between 1 and 65535")
    elif kind == "DNS":
        if not target or len(target) > 253 or any(char.isspace() for char in target):
            raise ValidationError("DNS target must be a valid hostname")
    elif kind == "PUSH":
        return
    else:
        raise ValidationError("Unsupported monitor type")


def _allowed_networks() -> list[ipaddress._BaseNetwork]:
    networks = []
    for value in settings.MONITOR_ALLOWED_NETWORKS:
        try:
            networks.append(ipaddress.ip_network(value, strict=False))
        except ValueError as exc:
            raise RuntimeError(f"Invalid MONITOR_ALLOWED_NETWORKS entry: {value}") from exc
    return networks


def _address_is_allowed(address: ipaddress._BaseAddress) -> bool:
    explicitly_allowed = any(address in network for network in _allowed_networks())
    if explicitly_allowed:
        return True
    if address.is_global:
        return bool(settings.MONITOR_ALLOW_PUBLIC_TARGETS)
    return False


async def resolve_and_validate_network_target(hostname: str, port: int) -> list[str]:
    """Resolve a network target and reject destinations outside the configured policy.

    Every resolved address must be allowed. This prevents DNS answers from mixing an allowed
    public address with a private or reserved address that could be selected by the client.
    """
    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValidationError(f"Unable to resolve target: {exc}") from exc

    addresses = sorted({info[4][0] for info in infos})
    if not addresses:
        raise ValidationError("Target resolved to no addresses")

    blocked = []
    for raw in addresses:
        try:
            address = ipaddress.ip_address(raw)
        except ValueError:
            blocked.append(raw)
            continue
        if not _address_is_allowed(address):
            blocked.append(raw)
    if blocked:
        raise ValidationError(
            "Target resolved to a destination not allowed by MONITOR_ALLOWED_NETWORKS: "
            + ", ".join(blocked)
        )
    return addresses

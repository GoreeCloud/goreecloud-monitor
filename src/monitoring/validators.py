"""Target validation and SSRF guardrails for active monitor checks."""
from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError

ALLOWED_DNS_TYPES = {"A", "AAAA", "CNAME"}


@dataclass(frozen=True, slots=True)
class DnsTarget:
    query_name: str
    resolver_host: str | None = None
    resolver_port: int = 53

    @property
    def uses_explicit_resolver(self) -> bool:
        return self.resolver_host is not None


def _validate_dns_name(value: str, *, label: str) -> str:
    value = (value or "").strip()
    if not value or len(value.rstrip(".")) > 253 or any(char.isspace() for char in value):
        raise ValidationError(f"{label} must be a valid DNS hostname")
    if any(char in value for char in "/?#@"):
        raise ValidationError(f"{label} must not contain URL delimiters")
    return value


def parse_dns_target(target: str) -> DnsTarget:
    """Parse a DNS target while preserving the no-schema-migration rollback boundary.

    Plain hostnames continue to use the system resolver. Resolver-qualified targets use the
    explicit portable form ``dns://<resolver>[:port]/<query-name>``. The resolver is validated
    against the same destination policy as other active network targets before it is queried.
    """
    value = (target or "").strip()
    if not value.lower().startswith("dns://"):
        return DnsTarget(query_name=_validate_dns_name(value, label="DNS target"))

    parsed = urlsplit(value)
    if parsed.scheme.lower() != "dns" or not parsed.hostname:
        raise ValidationError("Resolver-qualified DNS targets require dns://<resolver>/<hostname>")
    if parsed.username or parsed.password:
        raise ValidationError("Credentials are not permitted in DNS resolver targets")
    if parsed.query or parsed.fragment:
        raise ValidationError("DNS resolver targets do not permit query strings or fragments")

    query_name = parsed.path.lstrip("/")
    if not query_name or "/" in query_name:
        raise ValidationError("Resolver-qualified DNS targets require exactly one DNS query name")
    query_name = _validate_dns_name(query_name, label="DNS query name")
    resolver_host = _validate_dns_name(parsed.hostname, label="DNS resolver")

    try:
        resolver_port = parsed.port or 53
    except ValueError as exc:
        raise ValidationError("DNS resolver port is invalid") from exc
    if not 1 <= resolver_port <= 65535:
        raise ValidationError("DNS resolver port must be between 1 and 65535")

    return DnsTarget(query_name=query_name, resolver_host=resolver_host, resolver_port=resolver_port)


def format_dns_target(query_name: str, resolver_host: str, resolver_port: int = 53) -> str:
    """Return the canonical resolver-qualified DNS target representation."""
    query_name = _validate_dns_name(query_name, label="DNS query name")
    resolver_host = _validate_dns_name(resolver_host, label="DNS resolver")
    if not 1 <= int(resolver_port) <= 65535:
        raise ValidationError("DNS resolver port must be between 1 and 65535")
    host = f"[{resolver_host}]" if ":" in resolver_host and not resolver_host.startswith("[") else resolver_host
    port_suffix = "" if int(resolver_port) == 53 else f":{int(resolver_port)}"
    target = f"dns://{host}{port_suffix}/{query_name}"
    # Parse our own output so formatting cannot create a representation that the runtime rejects.
    parse_dns_target(target)
    return target


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
        parse_dns_target(target)
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

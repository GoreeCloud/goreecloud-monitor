"""Low-privilege ICMP Echo support for GoreeCloud Monitor.

Linux can permit unprivileged ICMP datagram ("ping") sockets through
net.ipv4.ping_group_range. Monitor deliberately uses that interface rather
than raw sockets so the worker does not need CAP_NET_RAW or privileged mode.
"""
from __future__ import annotations

import asyncio
import ipaddress
import secrets
import socket
import struct
import time


class IcmpUnavailable(RuntimeError):
    """Raised when the runtime cannot create an unprivileged ICMP socket."""


def _checksum(payload: bytes) -> int:
    if len(payload) % 2:
        payload += b"\x00"
    words = struct.unpack(f"!{len(payload) // 2}H", payload)
    total = sum(words)
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return (~total) & 0xFFFF


def _request_packet(address: ipaddress._BaseAddress, sequence: int, payload: bytes) -> bytes:
    echo_type = 8 if address.version == 4 else 128
    header = struct.pack("!BBHHH", echo_type, 0, 0, 0, sequence)
    if address.version == 4:
        checksum = _checksum(header + payload)
        header = struct.pack("!BBHHH", echo_type, 0, checksum, 0, sequence)
    return header + payload


def available_ping_families() -> set[int]:
    """Return IP versions for which an unprivileged ping socket can be created."""
    available: set[int] = set()
    for version, family, protocol in (
        (4, socket.AF_INET, socket.IPPROTO_ICMP),
        (6, socket.AF_INET6, socket.IPPROTO_ICMPV6),
    ):
        probe = None
        try:
            probe = socket.socket(family, socket.SOCK_DGRAM, protocol)
        except OSError:
            continue
        else:
            available.add(version)
        finally:
            if probe is not None:
                probe.close()
    return available


async def echo(address_text: str, timeout: float) -> float:
    """Send one ICMP Echo request to an already validated numeric address.

    Returns round-trip time in milliseconds. Hostname resolution and target
    policy validation intentionally happen before this function is called.
    """
    address = ipaddress.ip_address(address_text)
    family = socket.AF_INET if address.version == 4 else socket.AF_INET6
    protocol = socket.IPPROTO_ICMP if address.version == 4 else socket.IPPROTO_ICMPV6
    destination = (str(address), 0) if address.version == 4 else (str(address), 0, 0, 0)
    sequence = secrets.randbelow(65535) + 1
    payload = b"GCMON" + secrets.token_bytes(16)
    packet = _request_packet(address, sequence, payload)
    loop = asyncio.get_running_loop()
    sock = None
    started = time.perf_counter()
    try:
        try:
            sock = socket.socket(family, socket.SOCK_DGRAM, protocol)
        except PermissionError as exc:
            raise IcmpUnavailable("Unprivileged ICMP Echo is not permitted for the Monitor worker") from exc
        except OSError as exc:
            raise IcmpUnavailable("Unprivileged ICMP Echo is unavailable in this runtime") from exc
        sock.connect(destination)
        sock.setblocking(False)
        await loop.sock_sendall(sock, packet)
        reply = await asyncio.wait_for(loop.sock_recv(sock, 1024), timeout=timeout)
        if len(reply) < 8:
            raise OSError("ICMP Echo reply was truncated")
        reply_type, code, _checksum_value, _identifier, reply_sequence = struct.unpack("!BBHHH", reply[:8])
        expected_type = 0 if address.version == 4 else 129
        if reply_type != expected_type or code != 0 or reply_sequence != sequence or reply[8:] != payload:
            raise OSError("ICMP Echo reply did not match the request")
        return (time.perf_counter() - started) * 1000
    finally:
        if sock is not None:
            sock.close()

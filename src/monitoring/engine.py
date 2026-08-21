from __future__ import annotations

import asyncio
import json
import logging
import ssl
import time
from dataclasses import dataclass
from datetime import datetime, timezone as dt_timezone
from urllib.parse import urljoin, urlsplit

import dns.asyncresolver
import httpx
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .icmp import IcmpUnavailable, echo as icmp_echo
from .models import CheckResult, Incident, MaintenanceWindow, Monitor
from .notifications import publish_transition
from .observability import log_event, safe_traceback
from .validators import parse_dns_target, resolve_and_validate_network_target

logger = logging.getLogger("monitoring.access")


@dataclass(slots=True)
class CheckOutcome:
    success: bool
    observed_state: str
    response_time_ms: float | None = None
    message: str = ""
    tls_expires_at: datetime | None = None


def _json_path(value, path: str):
    current = value
    for segment in [part for part in path.split(".") if part]:
        if isinstance(current, dict): current = current[segment]
        elif isinstance(current, list) and segment.isdigit(): current = current[int(segment)]
        else: raise KeyError(segment)
    return current


async def _certificate_expiry(host: str, port: int, timeout: float) -> datetime:
    await resolve_and_validate_network_target(host, port)
    context = ssl.create_default_context(); writer = None
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port, ssl=context, server_hostname=host), timeout=timeout)
        ssl_object = writer.get_extra_info("ssl_object")
        if ssl_object is None: raise RuntimeError("TLS session was not established")
        cert = ssl_object.getpeercert(); not_after = cert.get("notAfter")
        if not not_after: raise RuntimeError("Certificate expiration could not be determined")
        return datetime.fromtimestamp(ssl.cert_time_to_seconds(not_after), tz=dt_timezone.utc)
    finally:
        if writer is not None:
            writer.close(); await writer.wait_closed()


async def _open_validated_http_response(client: httpx.AsyncClient, monitor: Monitor):
    current_url = monitor.target
    for hop in range(6):
        parsed = urlsplit(current_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname: raise ValidationError("Redirect target is not a valid HTTP or HTTPS URL")
        if parsed.username or parsed.password: raise ValidationError("Redirect targets containing credentials are not permitted")
        if monitor.kind == Monitor.Kind.HTTPS and parsed.scheme != "https": raise ValidationError("HTTPS monitors do not permit redirects that downgrade to HTTP")
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        await resolve_and_validate_network_target(parsed.hostname, port)
        request = client.build_request(monitor.http_method, current_url)
        response = await client.send(request, stream=True, follow_redirects=False)
        if response.status_code in {301, 302, 303, 307, 308} and monitor.follow_redirects:
            location = response.headers.get("location")
            if not location: return response, current_url
            if hop == 5:
                await response.aclose(); raise ValidationError("Redirect limit exceeded")
            next_url = urljoin(current_url, location); await response.aclose(); current_url = next_url; continue
        return response, current_url
    raise ValidationError("Redirect limit exceeded")


async def check_http(monitor: Monitor) -> CheckOutcome:
    started = time.perf_counter(); timeout = httpx.Timeout(float(monitor.timeout_seconds)); response = None; final_url = monitor.target
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, verify=True, trust_env=False) as client:
            response, final_url = await _open_validated_http_response(client, monitor)
            if response.status_code != monitor.expected_status_code:
                return CheckOutcome(False, Monitor.State.DOWN, (time.perf_counter()-started)*1000, f"HTTP {response.status_code}, expected {monitor.expected_status_code}")
            body = b""
            if monitor.expected_body_text or monitor.expected_json_path:
                async for chunk in response.aiter_bytes():
                    if len(body)+len(chunk) > settings.MONITOR_MAX_RESPONSE_BYTES:
                        return CheckOutcome(False, Monitor.State.DOWN, (time.perf_counter()-started)*1000, "Response body exceeded the configured inspection limit")
                    body += chunk
        elapsed = (time.perf_counter()-started)*1000
        if monitor.expected_body_text and monitor.expected_body_text not in body.decode("utf-8", errors="replace"):
            return CheckOutcome(False, Monitor.State.DOWN, elapsed, "Expected response text was not found")
        if monitor.expected_json_path:
            try: actual = _json_path(json.loads(body.decode("utf-8")), monitor.expected_json_path)
            except (ValueError, KeyError, IndexError, TypeError, UnicodeDecodeError): return CheckOutcome(False, Monitor.State.DOWN, elapsed, "Expected JSON path was not available")
            if monitor.expected_json_value and str(actual) != monitor.expected_json_value: return CheckOutcome(False, Monitor.State.DOWN, elapsed, "Expected JSON value did not match")
        final_parsed = urlsplit(final_url)
        if final_parsed.scheme == "https":
            port = final_parsed.port or 443
            expires = await _certificate_expiry(final_parsed.hostname, port, float(monitor.timeout_seconds))
            remaining_days = (expires-timezone.now()).total_seconds()/86400
            if remaining_days <= monitor.tls_warning_days: return CheckOutcome(True, Monitor.State.DEGRADED, elapsed, f"TLS certificate expires in {max(0,int(remaining_days))} day(s)", expires)
            return CheckOutcome(True, Monitor.State.UP, elapsed, f"{monitor.kind} check passed", expires)
        return CheckOutcome(True, Monitor.State.UP, elapsed, "HTTP check passed")
    except (httpx.HTTPError, OSError, asyncio.TimeoutError, ValidationError, RuntimeError) as exc:
        return CheckOutcome(False, Monitor.State.DOWN, (time.perf_counter()-started)*1000, f"{type(exc).__name__}: {str(exc)[:420]}")
    finally:
        if response is not None: await response.aclose()


async def check_tcp(monitor: Monitor) -> CheckOutcome:
    started=time.perf_counter(); writer=None
    try:
        await resolve_and_validate_network_target(monitor.target, int(monitor.port))
        _, writer = await asyncio.wait_for(asyncio.open_connection(monitor.target, int(monitor.port)), timeout=float(monitor.timeout_seconds))
        return CheckOutcome(True, Monitor.State.UP, (time.perf_counter()-started)*1000, "TCP connection succeeded")
    except (OSError, asyncio.TimeoutError, ValidationError) as exc:
        return CheckOutcome(False, Monitor.State.DOWN, (time.perf_counter()-started)*1000, f"{type(exc).__name__}: {str(exc)[:420]}")
    finally:
        if writer is not None: writer.close(); await writer.wait_closed()


async def check_ping(monitor: Monitor) -> CheckOutcome:
    started = time.perf_counter()
    try:
        addresses = await resolve_and_validate_network_target(monitor.target, 0)
        deadline = asyncio.get_running_loop().time() + float(monitor.timeout_seconds)
        last_error: Exception | None = None
        for address in addresses:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                break
            try:
                elapsed = await icmp_echo(address, remaining)
                return CheckOutcome(True, Monitor.State.UP, elapsed, "ICMP Echo reply received")
            except (OSError, asyncio.TimeoutError, IcmpUnavailable) as exc:
                last_error = exc
        if isinstance(last_error, IcmpUnavailable):
            return CheckOutcome(False, Monitor.State.DOWN, (time.perf_counter()-started)*1000, "Unprivileged ICMP Echo is unavailable for the Monitor worker")
        return CheckOutcome(False, Monitor.State.DOWN, (time.perf_counter()-started)*1000, "ICMP Echo did not receive a valid reply")
    except (OSError, asyncio.TimeoutError, ValidationError, IcmpUnavailable) as exc:
        message = "Unprivileged ICMP Echo is unavailable for the Monitor worker" if isinstance(exc, IcmpUnavailable) else f"{type(exc).__name__}: {str(exc)[:420]}"
        return CheckOutcome(False, Monitor.State.DOWN, (time.perf_counter()-started)*1000, message)


async def check_dns(monitor: Monitor) -> CheckOutcome:
    started=time.perf_counter()
    try:
        dns_target = parse_dns_target(monitor.target)
        if dns_target.uses_explicit_resolver:
            resolver_addresses = await resolve_and_validate_network_target(dns_target.resolver_host, dns_target.resolver_port)
            resolver = dns.asyncresolver.Resolver(configure=False)
            resolver.nameservers = resolver_addresses
            resolver.port = dns_target.resolver_port
        else:
            resolver = dns.asyncresolver.Resolver()
        resolver.lifetime=float(monitor.timeout_seconds)
        answer=await resolver.resolve(dns_target.query_name, monitor.dns_record_type.upper()); values=sorted(str(item).rstrip(".") for item in answer); elapsed=(time.perf_counter()-started)*1000
        if monitor.expected_dns_answer and monitor.expected_dns_answer.rstrip(".") not in values: return CheckOutcome(False, Monitor.State.DOWN, elapsed, "DNS answer did not contain the expected value")
        return CheckOutcome(True, Monitor.State.UP, elapsed, f"DNS {monitor.dns_record_type.upper()} check passed")
    except Exception as exc:
        return CheckOutcome(False, Monitor.State.DOWN, (time.perf_counter()-started)*1000, f"{type(exc).__name__}: {str(exc)[:420]}")


async def check_push(monitor: Monitor) -> CheckOutcome:
    if not monitor.last_heartbeat_at: return CheckOutcome(False, Monitor.State.DOWN, None, "No heartbeat has been received")
    age=(timezone.now()-monitor.last_heartbeat_at).total_seconds(); allowed_age=monitor.interval_seconds+monitor.heartbeat_grace_seconds
    if age > allowed_age: return CheckOutcome(False, Monitor.State.DOWN, None, f"Heartbeat is {int(age)}s old; limit is {allowed_age}s")
    return CheckOutcome(True, Monitor.State.UP, None, "Heartbeat is current")


async def perform_check(monitor: Monitor) -> CheckOutcome:
    if monitor.kind in {Monitor.Kind.HTTP, Monitor.Kind.HTTPS}: return await check_http(monitor)
    if monitor.kind == Monitor.Kind.TCP: return await check_tcp(monitor)
    if monitor.kind == Monitor.Kind.PING: return await check_ping(monitor)
    if monitor.kind == Monitor.Kind.DNS: return await check_dns(monitor)
    if monitor.kind == Monitor.Kind.PUSH: return await check_push(monitor)
    return CheckOutcome(False, Monitor.State.DOWN, None, "Unsupported monitor type")


def _is_in_maintenance(monitor_id: int, now) -> bool: return MaintenanceWindow.objects.filter(monitors__id=monitor_id, starts_at__lte=now, ends_at__gte=now).exists()
def _mark_maintenance(monitor_id: int, now) -> None: Monitor.objects.filter(id=monitor_id).update(state=Monitor.State.MAINTENANCE, last_checked_at=now, last_message="Approved maintenance window")


@transaction.atomic
def _apply_outcome(monitor_id: int, outcome: CheckOutcome, checked_at) -> tuple[str | None, str, str]:
    monitor=Monitor.objects.select_for_update().get(id=monitor_id); previous_state=monitor.state
    if outcome.success:
        monitor.consecutive_failures=0; monitor.consecutive_successes+=1; monitor.last_success_at=checked_at; next_state=outcome.observed_state
        if previous_state == Monitor.State.DOWN and monitor.consecutive_successes < monitor.recovery_threshold: next_state=Monitor.State.DOWN
    else:
        monitor.consecutive_successes=0; monitor.consecutive_failures+=1; monitor.last_failure_at=checked_at; next_state=previous_state
        if monitor.consecutive_failures >= monitor.failure_threshold: next_state=Monitor.State.DOWN
        elif previous_state in {Monitor.State.UNKNOWN,Monitor.State.UP,Monitor.State.DEGRADED,Monitor.State.MAINTENANCE}: next_state=previous_state if previous_state != Monitor.State.MAINTENANCE else Monitor.State.UNKNOWN
    monitor.last_checked_at=checked_at; monitor.response_time_ms=outcome.response_time_ms; monitor.last_message=outcome.message[:500]
    if outcome.tls_expires_at: monitor.tls_expires_at=outcome.tls_expires_at
    monitor.state=next_state
    monitor.save(update_fields=["consecutive_failures","consecutive_successes","last_success_at","last_failure_at","last_checked_at","response_time_ms","last_message","tls_expires_at","state","updated_at"])
    CheckResult.objects.create(monitor=monitor,checked_at=checked_at,success=outcome.success,observed_state=next_state,response_time_ms=outcome.response_time_ms,message=outcome.message[:500])
    transition=None
    if next_state == Monitor.State.DOWN and previous_state != Monitor.State.DOWN:
        Incident.objects.create(monitor=monitor,started_at=checked_at,failure_reason=outcome.message[:500]); transition="DOWN"
    elif previous_state == Monitor.State.DOWN and next_state in {Monitor.State.UP,Monitor.State.DEGRADED}:
        Incident.objects.filter(monitor=monitor,ended_at__isnull=True).update(ended_at=checked_at,recovery_message=outcome.message[:500]); transition="RECOVERED" if next_state == Monitor.State.UP else "DEGRADED"
    elif next_state == Monitor.State.DEGRADED and previous_state != Monitor.State.DEGRADED: transition="DEGRADED"
    elif previous_state == Monitor.State.DEGRADED and next_state == Monitor.State.UP: transition="RECOVERED"
    return transition, monitor.name, outcome.message


async def run_monitor(monitor_id: int) -> None:
    checked_at=timezone.now(); in_maintenance=await sync_to_async(_is_in_maintenance,thread_sensitive=True)(monitor_id,checked_at)
    if in_maintenance:
        await sync_to_async(_mark_maintenance,thread_sensitive=True)(monitor_id,checked_at); return
    monitor=await sync_to_async(Monitor.objects.get,thread_sensitive=True)(id=monitor_id)
    if not monitor.enabled: return
    try: outcome=await perform_check(monitor)
    except Exception as exc:
        log_event(logger,"monitor.check.exception",level=logging.ERROR,monitor_id=monitor_id,exception_type=type(exc).__name__,traceback=safe_traceback(exc))
        outcome=CheckOutcome(False,Monitor.State.DOWN,None,"Internal monitor worker error")
    transition,name,message=await sync_to_async(_apply_outcome,thread_sensitive=True)(monitor_id,outcome,checked_at)
    if transition:
        log_event(logger,"monitor.state.transition",monitor_id=monitor_id,transition=transition,observed_state=outcome.observed_state,response_time_ms=round(outcome.response_time_ms,2) if outcome.response_time_ms is not None else None)
        await publish_transition(name,transition,message)


async def run_batch(monitor_ids: list[int]) -> None:
    semaphore=asyncio.Semaphore(settings.MONITOR_MAX_CONCURRENCY)
    async def bounded(monitor_id:int):
        async with semaphore: await run_monitor(monitor_id)
    await asyncio.gather(*(bounded(monitor_id) for monitor_id in monitor_ids))

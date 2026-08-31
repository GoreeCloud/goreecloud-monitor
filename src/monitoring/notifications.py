from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from urllib.parse import urlsplit

import httpx
from django.conf import settings

from .observability import log_event, safe_traceback

logger = logging.getLogger("monitoring.access")
_TLS_WARNING = re.compile(r"^TLS certificate expires in (\d{1,5}) day\(s\)$")
_NOTIFY_EVENT_POLICY = {
    "DOWN": {"severity": "critical", "title": "Monitor detected an outage"},
    "RECOVERED": {"severity": "normal", "title": "Monitor detected a recovery"},
    "DEGRADED": {"severity": "warning", "title": "Monitor detected degraded service"},
    "TLS_EXPIRING": {"severity": "warning", "title": "Monitor certificate attention required"},
}
_NOTIFY_MAX_LABEL_LENGTH = 160
_NOTIFY_MAX_SUMMARY_LENGTH = 500
_NOTIFY_MAX_TRANSITION_ID_LENGTH = 240
_NOTIFY_MAX_PAYLOAD_BYTES = 8 * 1024


def _public_transition_summary(state: str, message: str) -> str:
    """Return a notification-safe summary without targets or raw exception diagnostics."""
    normalized = state.strip().upper()
    if normalized == "RECOVERED":
        return "Service availability recovered."
    if normalized == "DOWN":
        return "Availability check failed. Open GoreeCloud Monitor for diagnostic details."
    if normalized == "DEGRADED":
        match = _TLS_WARNING.fullmatch(message.strip())
        if match:
            return f"TLS certificate expires in {match.group(1)} day(s)."
        return "Service is degraded. Open GoreeCloud Monitor for diagnostic details."
    return "Monitor state changed. Open GoreeCloud Monitor for details."


def _required_notify_text(value: str, name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise TypeError(f"{name} is required")
    if len(normalized) > max_length:
        raise ValueError(f"{name} exceeds {max_length} characters")
    return normalized


def _notify_event_type(state: str, message: str) -> str:
    normalized = _required_notify_text(state, "state", 32).upper()
    if normalized == "DEGRADED" and _TLS_WARNING.fullmatch(message.strip()):
        return "TLS_EXPIRING"
    if normalized not in _NOTIFY_EVENT_POLICY:
        raise ValueError("unsupported GoreeCloud Notify transition type")
    return normalized


def create_notify_payload(name: str, state: str, message: str) -> tuple[str, dict[str, str]]:
    """Create the minimized Monitor producer payload defined by the Notify contract."""
    event_type = _notify_event_type(state, message)
    policy = _NOTIFY_EVENT_POLICY[event_type]
    monitor_name = _required_notify_text(name, "monitor", _NOTIFY_MAX_LABEL_LENGTH)
    summary = _required_notify_text(
        _public_transition_summary(state, message),
        "summary",
        _NOTIFY_MAX_SUMMARY_LENGTH,
    )
    payload = {
        "source": "goreecloud-monitor",
        "channel": "monitoring",
        "title": policy["title"],
        "body": f"{monitor_name}: {summary}",
        "severity": policy["severity"],
    }
    payload_bytes = len(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    if payload_bytes > _NOTIFY_MAX_PAYLOAD_BYTES:
        raise ValueError("notification payload exceeds Notify compatibility envelope")
    return event_type, payload


def create_notify_idempotency_key(event_type: str, transition_id: str) -> str:
    """Derive the same opaque v1 replay key as the source-level Notify producer package."""
    normalized_event_type = _required_notify_text(event_type, "event_type", 32).upper()
    if normalized_event_type not in _NOTIFY_EVENT_POLICY:
        raise ValueError("unsupported GoreeCloud Notify transition type")
    normalized_transition_id = _required_notify_text(
        transition_id,
        "transition_id",
        _NOTIFY_MAX_TRANSITION_ID_LENGTH,
    )
    digest = hashlib.sha256()
    digest.update(b"goreecloud-monitor\0v1\0")
    digest.update(normalized_event_type.encode("utf-8"))
    digest.update(b"\0")
    digest.update(normalized_transition_id.encode("utf-8"))
    return f"gcm-v1-{digest.hexdigest()}"


def _notify_endpoint(base_url: str) -> str:
    parsed = urlsplit(base_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("GoreeCloud Notify endpoint must use HTTPS")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("GoreeCloud Notify endpoint must not contain credentials, query, or fragment")
    return f"https://{parsed.netloc}/api/v1/notifications"


async def publish_transition(name: str, state: str, message: str) -> None:
    """Publish a minimized transition through the dedicated ntfy publisher identity."""
    configured = (settings.NTFY_BASE_URL, settings.NTFY_TOPIC, settings.NTFY_TOKEN)
    if not any(configured):
        return
    if not all(configured):
        log_event(logger, "integration.notification.refused", level=logging.ERROR, integration="ntfy", reason="partial_configuration", state=state)
        return

    endpoint = f"{settings.NTFY_BASE_URL}/{settings.NTFY_TOPIC}"
    body = f"GoreeCloud Monitor — {name} — {state}\n{_public_transition_summary(state, message)}"
    headers = {"Authorization": f"Bearer {settings.NTFY_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            response = await client.post(endpoint, content=body.encode("utf-8"), headers=headers)
            response.raise_for_status()
    except Exception as exc:
        log_event(
            logger,
            "integration.notification.failed",
            level=logging.ERROR,
            integration="ntfy",
            state=state,
            exception_type=type(exc).__name__,
            traceback=safe_traceback(exc),
        )
        return
    log_event(logger, "integration.notification.published", integration="ntfy", state=state)


async def publish_notify_transition(
    name: str,
    state: str,
    message: str,
    *,
    transition_id: str,
) -> bool:
    """Publish through GoreeCloud Notify when the parallel runtime feature gate is enabled."""
    if not getattr(settings, "MONITOR_NOTIFY_ENABLED", False):
        return False

    base_url = getattr(settings, "GOREECLOUD_NOTIFY_BASE_URL", "")
    token = getattr(settings, "GOREECLOUD_NOTIFY_TOKEN", "")
    if not base_url or not token:
        log_event(
            logger,
            "integration.notification.refused",
            level=logging.ERROR,
            integration="goreecloud-notify",
            reason="partial_configuration",
            state=state,
        )
        return False

    try:
        endpoint = _notify_endpoint(base_url)
        event_type, payload = create_notify_payload(name, state, message)
        idempotency_key = create_notify_idempotency_key(event_type, transition_id)
    except (TypeError, ValueError):
        log_event(
            logger,
            "integration.notification.refused",
            level=logging.ERROR,
            integration="goreecloud-notify",
            reason="invalid_contract_input",
            state=state,
        )
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Idempotency-Key": idempotency_key,
    }
    max_attempts = max(1, min(5, int(getattr(settings, "MONITOR_NOTIFY_MAX_ATTEMPTS", 3))))
    backoff_seconds = max(0.0, float(getattr(settings, "MONITOR_NOTIFY_RETRY_BACKOFF_SECONDS", 0.25)))
    timeout_seconds = max(1.0, min(30.0, float(getattr(settings, "MONITOR_NOTIFY_TIMEOUT_SECONDS", 10.0))))

    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds, trust_env=False, follow_redirects=False) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            if attempt < max_attempts:
                if backoff_seconds:
                    await asyncio.sleep(backoff_seconds * (2 ** (attempt - 1)))
                continue
            log_event(
                logger,
                "integration.notification.failed",
                level=logging.ERROR,
                integration="goreecloud-notify",
                reason="transport_error",
                state=state,
                attempts=attempt,
                exception_type=type(exc).__name__,
                traceback=safe_traceback(exc),
            )
            return False

        if response.status_code == 201:
            log_event(
                logger,
                "integration.notification.published",
                integration="goreecloud-notify",
                state=state,
                replayed=False,
                attempts=attempt,
            )
            return True
        if response.status_code == 200:
            replayed = response.headers.get("Idempotency-Replayed", "").strip().lower() == "true"
            if not replayed:
                log_event(
                    logger,
                    "integration.notification.failed",
                    level=logging.ERROR,
                    integration="goreecloud-notify",
                    reason="invalid_replay_response",
                    state=state,
                    attempts=attempt,
                )
                return False
            log_event(
                logger,
                "integration.notification.published",
                integration="goreecloud-notify",
                state=state,
                replayed=True,
                attempts=attempt,
            )
            return True
        if response.status_code == 409:
            log_event(
                logger,
                "integration.notification.failed",
                level=logging.ERROR,
                integration="goreecloud-notify",
                reason="idempotency_conflict",
                state=state,
                attempts=attempt,
            )
            return False
        if response.status_code == 429 or response.status_code >= 500:
            if attempt < max_attempts:
                if backoff_seconds:
                    await asyncio.sleep(backoff_seconds * (2 ** (attempt - 1)))
                continue
        log_event(
            logger,
            "integration.notification.failed",
            level=logging.ERROR,
            integration="goreecloud-notify",
            reason="http_rejected",
            state=state,
            http_status=response.status_code,
            attempts=attempt,
        )
        return False

    return False

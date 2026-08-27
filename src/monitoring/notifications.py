from __future__ import annotations

import logging
import re

import httpx
from django.conf import settings

from .observability import log_event, safe_traceback

logger = logging.getLogger("monitoring.access")
_TLS_WARNING = re.compile(r"^TLS certificate expires in (\d{1,5}) day\(s\)$")


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

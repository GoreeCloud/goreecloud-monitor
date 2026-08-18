from __future__ import annotations

import logging
import re

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)
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
    """Publish a minimized state transition through the dedicated ntfy publisher identity.

    Notification output intentionally excludes monitor targets, response bodies, raw exception
    diagnostics, credentials, and reusable secrets. A partially configured integration fails
    closed and never attempts anonymous publication.
    """
    configured = (settings.NTFY_BASE_URL, settings.NTFY_TOPIC, settings.NTFY_TOKEN)
    if not any(configured):
        return
    if not all(configured):
        logger.error("ntfy publishing is partially configured; refusing unauthenticated publication")
        return

    endpoint = f"{settings.NTFY_BASE_URL}/{settings.NTFY_TOPIC}"
    body = f"GoreeCloud Monitor — {name} — {state}\n{_public_transition_summary(state, message)}"
    headers = {"Authorization": f"Bearer {settings.NTFY_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            response = await client.post(endpoint, content=body.encode("utf-8"), headers=headers)
            response.raise_for_status()
    except Exception:
        logger.exception("Failed to publish monitor transition for %s", name)

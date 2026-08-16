from __future__ import annotations

import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


async def publish_transition(name: str, state: str, message: str) -> None:
    """Publish a minimized state transition to ntfy when configured.

    The notification intentionally excludes monitor target URLs and response bodies.
    """
    if not settings.NTFY_BASE_URL or not settings.NTFY_TOPIC:
        return
    endpoint = f"{settings.NTFY_BASE_URL}/{settings.NTFY_TOPIC}"
    body = f"GoreeCloud Monitor — {name} — {state}\n{message[:300]}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(endpoint, content=body.encode("utf-8"))
            response.raise_for_status()
    except Exception:
        logger.exception("Failed to publish monitor transition for %s", name)

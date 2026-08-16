from __future__ import annotations

import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


async def publish_transition(name: str, state: str, message: str) -> None:
    """Publish a minimized state transition through the dedicated ntfy publisher identity.

    The notification intentionally excludes monitor target URLs and response bodies. A
    partially configured integration fails closed and never attempts anonymous publication.
    """
    configured = (settings.NTFY_BASE_URL, settings.NTFY_TOPIC, settings.NTFY_TOKEN)
    if not any(configured):
        return
    if not all(configured):
        logger.error("ntfy publishing is partially configured; refusing unauthenticated publication")
        return

    endpoint = f"{settings.NTFY_BASE_URL}/{settings.NTFY_TOPIC}"
    body = f"GoreeCloud Monitor — {name} — {state}\n{message[:300]}"
    headers = {"Authorization": f"Bearer {settings.NTFY_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            response = await client.post(endpoint, content=body.encode("utf-8"), headers=headers)
            response.raise_for_status()
    except Exception:
        logger.exception("Failed to publish monitor transition for %s", name)

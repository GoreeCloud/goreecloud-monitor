"""Minimized Wardveil Security event logging for security-relevant Monitor actions."""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("monitoring.wardveil")


def record_security_event(
    event: str,
    *,
    user: Any | None = None,
    outcome: str = "success",
    object_type: str | None = None,
    object_id: int | str | None = None,
) -> None:
    """Write a structured, secret-free security event to the operational log.

    The log deliberately records identifiers rather than target URLs, tokens, credentials,
    request bodies, IP addresses, or monitor diagnostic payloads. The runtime log remains an
    operational record; it is not a replacement for the underlying Django/auth/database state.
    """

    payload: dict[str, Any] = {
        "event": event,
        "outcome": outcome,
    }
    if user is not None and getattr(user, "is_authenticated", False):
        payload["user_id"] = getattr(user, "pk", None)
        payload["staff"] = bool(getattr(user, "is_staff", False))
    if object_type:
        payload["object_type"] = object_type
    if object_id is not None:
        payload["object_id"] = str(object_id)

    logger.info("wardveil_security_event %s", json.dumps(payload, sort_keys=True, separators=(",", ":")))

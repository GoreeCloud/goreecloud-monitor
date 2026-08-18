"""Minimized Wardveil Security event logging for security-relevant Monitor actions."""
from __future__ import annotations

import logging
from typing import Any

from .observability import log_event

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
    request bodies, IP addresses, usernames, or monitor diagnostic payloads.
    """
    fields: dict[str, Any] = {"outcome": outcome}
    if user is not None and getattr(user, "is_authenticated", False):
        fields["user_id"] = getattr(user, "pk", None)
        fields["staff"] = bool(getattr(user, "is_staff", False))
    if object_type:
        fields["object_type"] = object_type
    if object_id is not None:
        fields["object_id"] = str(object_id)
    log_event(logger, event, **fields)

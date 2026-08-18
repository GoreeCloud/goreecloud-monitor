"""Privacy-preserving structured operational logging for GoreeCloud Monitor."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


def log_event(logger: logging.Logger, event: str, *, level: int = logging.INFO, **fields: Any) -> None:
    """Emit one JSON event without raw request, credential, or target material."""
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
    }
    payload.update({key: value for key, value in fields.items() if value is not None})
    logger.log(level, json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str))

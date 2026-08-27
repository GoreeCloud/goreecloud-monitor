"""Privacy-preserving structured operational logging for GoreeCloud Monitor."""
from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def safe_traceback(exception: BaseException, *, limit: int = 8) -> list[dict[str, Any]]:
    """Return code-location frames without exception messages, arguments, locals, or absolute paths."""
    extracted = traceback.extract_tb(exception.__traceback__, limit=limit)
    return [
        {"file": Path(frame.filename).name, "line": frame.lineno, "function": frame.name}
        for frame in extracted
    ]


def log_event(logger: logging.Logger, event: str, *, level: int = logging.INFO, **fields: Any) -> None:
    """Emit one JSON event without raw request, credential, or target material."""
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
    }
    payload.update({key: value for key, value in fields.items() if value is not None})
    logger.log(level, json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str))

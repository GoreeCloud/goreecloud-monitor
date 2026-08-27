"""Wardveil response policy and privacy-preserving request observability."""
from __future__ import annotations

import logging
import time
import uuid

from django.conf import settings

from .observability import log_event

access_logger = logging.getLogger("monitoring.access")


def _request_fields(request) -> dict:
    """Return bounded request metadata without paths, queries, headers, or client addresses."""
    match = getattr(request, "resolver_match", None)
    user = getattr(request, "user", None)
    fields = {
        "request_id": getattr(request, "monitor_request_id", None),
        "method": getattr(request, "method", None),
        "route": getattr(match, "view_name", None) or "unresolved",
        "authenticated": bool(user is not None and getattr(user, "is_authenticated", False)),
    }
    if fields["authenticated"]:
        fields["user_id"] = getattr(user, "pk", None)
        fields["staff"] = bool(getattr(user, "is_staff", False))
    return fields


class WardveilSecurityHeadersMiddleware:
    """Apply privacy-preserving browser controls to all dynamic Monitor responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault("Content-Security-Policy", settings.MONITOR_CONTENT_SECURITY_POLICY)
        response.headers.setdefault("Permissions-Policy", settings.MONITOR_PERMISSIONS_POLICY)
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault("X-Robots-Tag", "noindex, nofollow, noarchive, nosnippet")
        response.headers["Cache-Control"] = "no-store, max-age=0, private"
        response.headers["Pragma"] = "no-cache"
        return response


class OperationalRequestMiddleware:
    """Attach a server-generated correlation ID and emit minimized structured request events."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.monitor_request_id = uuid.uuid4().hex
        started = time.perf_counter()
        response = self.get_response(request)
        response.headers["X-Request-ID"] = request.monitor_request_id
        log_event(
            access_logger,
            "http.request.completed",
            **_request_fields(request),
            status=int(response.status_code),
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        return response

    def process_exception(self, request, exception):
        log_event(
            access_logger,
            "http.request.exception",
            level=logging.ERROR,
            **_request_fields(request),
            exception_type=type(exception).__name__,
        )
        return None

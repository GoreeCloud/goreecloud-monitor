"""Glaze UI error handlers that disclose no exception or infrastructure details."""
from __future__ import annotations

from django.shortcuts import render


def _render_error(request, status: int, title: str, message: str):
    return render(request, "errors/error.html", {
        "status_code": status,
        "error_title": title,
        "error_message": message,
        "request_id": getattr(request, "monitor_request_id", ""),
    }, status=status)


def bad_request(request, exception):
    return _render_error(request, 400, "Request not accepted", "The request could not be processed safely. Review the input and try again.")


def permission_denied(request, exception):
    return _render_error(request, 403, "Access denied", "Your account is not authorized for this Monitor operation.")


def page_not_found(request, exception):
    return _render_error(request, 404, "Page not found", "The requested Monitor page or resource is not available.")


def server_error(request):
    return _render_error(request, 500, "Monitor could not complete the request", "The failure was recorded with a private request identifier. Try again or contact an authorized administrator.")

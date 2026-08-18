"""Application-level Wardveil Security response protections for GoreeCloud Monitor."""
from __future__ import annotations

from django.conf import settings


class WardveilSecurityHeadersMiddleware:
    """Apply privacy-preserving browser controls to all dynamic Monitor responses.

    Caddy remains the HTTPS gateway and Django's SecurityMiddleware remains responsible
    for Django-native transport headers. This layer covers application response controls that
    are not provided by Django 5.2 itself and deliberately avoids exposing environment state.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault("Content-Security-Policy", settings.MONITOR_CONTENT_SECURITY_POLICY)
        response.headers.setdefault("Permissions-Policy", settings.MONITOR_PERMISSIONS_POLICY)
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault("X-Robots-Tag", "noindex, nofollow, noarchive, nosnippet")

        # Monitor pages contain operational state and, on privileged surfaces, infrastructure
        # configuration. Dynamic responses should not be retained in browser or intermediary
        # caches. WhiteNoise serves immutable static assets before this middleware is reached.
        response.headers["Cache-Control"] = "no-store, max-age=0, private"
        response.headers["Pragma"] = "no-cache"
        return response

"""Authentication-event hooks for minimized Wardveil Security operational logging."""
from __future__ import annotations

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from .audit import record_security_event


@receiver(user_logged_in)
def _log_user_login(sender, request, user, **kwargs):
    record_security_event("authentication.login", user=user)


@receiver(user_logged_out)
def _log_user_logout(sender, request, user, **kwargs):
    record_security_event("authentication.logout", user=user)


@receiver(user_login_failed)
def _log_user_login_failed(sender, credentials, request, **kwargs):
    # Do not copy usernames, credentials, client IP addresses, or request data into this log.
    record_security_event("authentication.login_failed", outcome="denied")

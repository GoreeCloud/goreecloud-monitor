from __future__ import annotations

import hashlib
import re
import secrets

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .validators import ALLOWED_DNS_TYPES, validate_target_syntax

_HEARTBEAT_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def hash_heartbeat_token(raw_token: str) -> str:
    """Return the one-way verifier persisted for a push heartbeat credential."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def heartbeat_token_is_digest(value: str) -> bool:
    return bool(_HEARTBEAT_DIGEST_RE.fullmatch(value or ""))


def generate_heartbeat_token() -> str:
    """Generate only a verifier for ORM-created monitors; raw credentials are issued explicitly."""
    return hash_heartbeat_token(secrets.token_urlsafe(32))


class Monitor(models.Model):
    class Kind(models.TextChoices):
        HTTPS = "HTTPS", "HTTPS"
        HTTP = "HTTP", "HTTP"
        TCP = "TCP", "TCP"
        DNS = "DNS", "DNS"
        PUSH = "PUSH", "Push / heartbeat"

    class State(models.TextChoices):
        UNKNOWN = "UNKNOWN", "Unknown"
        UP = "UP", "Up"
        DOWN = "DOWN", "Down"
        DEGRADED = "DEGRADED", "Degraded"
        PAUSED = "PAUSED", "Paused"
        MAINTENANCE = "MAINTENANCE", "Maintenance"

    name = models.CharField(max_length=160, unique=True)
    kind = models.CharField(max_length=8, choices=Kind.choices)
    target = models.CharField(max_length=2048, blank=True)
    port = models.PositiveIntegerField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    interval_seconds = models.PositiveIntegerField(default=60)
    timeout_seconds = models.PositiveIntegerField(default=10)
    failure_threshold = models.PositiveIntegerField(default=2)
    recovery_threshold = models.PositiveIntegerField(default=1)
    http_method = models.CharField(max_length=8, default="GET")
    expected_status_code = models.PositiveIntegerField(default=200)
    follow_redirects = models.BooleanField(default=True)
    expected_body_text = models.CharField(max_length=500, blank=True)
    expected_json_path = models.CharField(max_length=200, blank=True)
    expected_json_value = models.CharField(max_length=500, blank=True)
    tls_warning_days = models.PositiveIntegerField(default=14)
    dns_record_type = models.CharField(max_length=8, default="A")
    expected_dns_answer = models.CharField(max_length=500, blank=True)
    # The historical field name is retained to avoid a schema migration in the pre-production
    # rollback chain. New/rotated values are SHA-256 verifiers, never reusable raw credentials.
    heartbeat_token = models.CharField(max_length=64, unique=True, default=generate_heartbeat_token)
    heartbeat_grace_seconds = models.PositiveIntegerField(default=60)
    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    state = models.CharField(max_length=16, choices=State.choices, default=State.UNKNOWN)
    consecutive_failures = models.PositiveIntegerField(default=0)
    consecutive_successes = models.PositiveIntegerField(default=0)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    response_time_ms = models.FloatField(null=True, blank=True)
    tls_expires_at = models.DateTimeField(null=True, blank=True)
    last_message = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["enabled", "last_checked_at"], name="mon_enabled_checked_idx"),
            models.Index(fields=["state"], name="mon_state_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        validate_target_syntax(self.kind, self.target, self.port)
        if self.interval_seconds < 5:
            raise ValidationError({"interval_seconds": "Intervals below 5 seconds are not supported."})
        if self.timeout_seconds > self.interval_seconds and self.kind != self.Kind.PUSH:
            raise ValidationError({"timeout_seconds": "Timeout must not exceed the check interval."})
        if self.failure_threshold < 1 or self.recovery_threshold < 1:
            raise ValidationError("Failure and recovery thresholds must be at least 1.")
        if self.kind in {self.Kind.HTTP, self.Kind.HTTPS}:
            if self.http_method not in {"GET", "HEAD"}:
                raise ValidationError({"http_method": "Only GET and HEAD are supported in v0.1."})
            if not 100 <= self.expected_status_code <= 599:
                raise ValidationError({"expected_status_code": "Expected status must be between 100 and 599."})
            if self.http_method == "HEAD" and (self.expected_body_text or self.expected_json_path):
                raise ValidationError("HEAD monitors cannot use body or JSON assertions.")
        if self.kind == self.Kind.DNS and self.dns_record_type.upper() not in ALLOWED_DNS_TYPES:
            raise ValidationError({"dns_record_type": "Supported DNS record types are A, AAAA, and CNAME."})
        if self.kind == self.Kind.PUSH and self.target:
            raise ValidationError({"target": "Push monitors do not use a target URL."})

    def save(self, *args, **kwargs):
        if not self.heartbeat_token:
            self.heartbeat_token = generate_heartbeat_token()
        if not self.enabled:
            self.state = self.State.PAUSED
        elif self.state == self.State.PAUSED:
            self.state = self.State.UNKNOWN
        super().save(*args, **kwargs)

    def issue_heartbeat_token(self) -> str:
        """Rotate the verifier and return the reusable secret exactly once to the caller."""
        raw_token = secrets.token_urlsafe(32)
        self.heartbeat_token = hash_heartbeat_token(raw_token)
        self.save(update_fields=["heartbeat_token", "updated_at"])
        return raw_token

    def is_due(self, now=None) -> bool:
        if not self.enabled:
            return False
        now = now or timezone.now()
        if not self.last_checked_at:
            return True
        return (now - self.last_checked_at).total_seconds() >= self.interval_seconds


class CheckResult(models.Model):
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE, related_name="checks")
    checked_at = models.DateTimeField(default=timezone.now, db_index=True)
    success = models.BooleanField()
    observed_state = models.CharField(max_length=16, choices=Monitor.State.choices)
    response_time_ms = models.FloatField(null=True, blank=True)
    message = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-checked_at"]
        indexes = [models.Index(fields=["monitor", "-checked_at"], name="check_monitor_checked_idx")]


class Incident(models.Model):
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE, related_name="incidents")
    started_at = models.DateTimeField(default=timezone.now, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=500, blank=True)
    recovery_message = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["ended_at", "started_at"], name="incident_open_started_idx")]

    @property
    def is_active(self) -> bool:
        return self.ended_at is None


class MaintenanceWindow(models.Model):
    name = models.CharField(max_length=160)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    monitors = models.ManyToManyField(Monitor, related_name="maintenance_windows")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-starts_at"]

    def clean(self) -> None:
        if self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "Maintenance must end after it starts."})

    def __str__(self) -> str:
        return self.name

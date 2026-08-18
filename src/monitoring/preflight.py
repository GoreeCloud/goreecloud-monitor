from __future__ import annotations

from dataclasses import asdict, dataclass
from ipaddress import ip_network

from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from .models import Monitor, heartbeat_token_is_digest


@dataclass(slots=True)
class PreflightFinding:
    severity: str
    code: str
    message: str
    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def configuration_findings() -> list[PreflightFinding]:
    findings: list[PreflightFinding] = []
    def add(severity: str, code: str, message: str) -> None:
        findings.append(PreflightFinding(severity, code, message))
    if settings.DEBUG: add("error", "debug-enabled", "DJANGO_DEBUG must be false for a target-environment acceptance run.")
    if settings.DATABASES.get("default", {}).get("ENGINE", "") != "django.db.backends.postgresql": add("error", "database-engine", "The target environment must use PostgreSQL, not the development SQLite database.")
    hosts = list(getattr(settings, "ALLOWED_HOSTS", []))
    if not hosts: add("error", "allowed-hosts-empty", "DJANGO_ALLOWED_HOSTS must contain the approved Monitor hostname.")
    if "*" in hosts: add("error", "allowed-hosts-wildcard", "Wildcard ALLOWED_HOSTS is not approved for GoreeCloud Monitor.")
    secret_key = str(getattr(settings, "SECRET_KEY", ""))
    if len(secret_key) < 32 or secret_key.startswith("development-only"): add("error", "secret-key", "DJANGO_SECRET_KEY must be a strong protected production value.")
    if not getattr(settings, "SECURE_SSL_REDIRECT", False): add("error", "https-redirect", "DJANGO_SECURE_SSL_REDIRECT must be enabled behind the approved HTTPS gateway.")
    if int(getattr(settings, "SECURE_HSTS_SECONDS", 0)) < 31536000: add("error", "hsts", "HSTS must be enabled for at least one year after the approved HTTPS route is validated.")
    if not getattr(settings, "SESSION_COOKIE_SECURE", False): add("error", "session-cookie-secure", "Session cookies must be Secure.")
    if not getattr(settings, "SESSION_COOKIE_HTTPONLY", False): add("error", "session-cookie-httponly", "Session cookies must be HttpOnly.")
    if getattr(settings, "SESSION_COOKIE_SAMESITE", None) not in {"Lax", "Strict"}: add("error", "session-cookie-samesite", "Session cookies must use an approved SameSite boundary.")
    if not getattr(settings, "CSRF_COOKIE_SECURE", False): add("error", "csrf-cookie-secure", "CSRF cookies must be Secure.")
    if getattr(settings, "CSRF_COOKIE_SAMESITE", None) not in {"Lax", "Strict"}: add("error", "csrf-cookie-samesite", "CSRF cookies must use an approved SameSite boundary.")
    if getattr(settings, "X_FRAME_OPTIONS", "") != "DENY": add("error", "frame-options", "Clickjacking protection must deny framing.")
    if getattr(settings, "SECURE_CROSS_ORIGIN_OPENER_POLICY", "") != "same-origin": add("error", "opener-policy", "Cross-origin opener policy must remain same-origin.")
    if not getattr(settings, "MONITOR_CONTENT_SECURITY_POLICY", ""): add("error", "content-security-policy", "The Monitor Content Security Policy must be configured.")
    if not getattr(settings, "MONITOR_PERMISSIONS_POLICY", ""): add("error", "permissions-policy", "The Monitor Permissions Policy must be configured.")
    if getattr(settings, "MONITOR_ALLOW_LEGACY_PATH_HEARTBEATS", False): add("error", "legacy-path-heartbeat", "Path-embedded heartbeat credentials must be disabled for target acceptance.")
    for value in getattr(settings, "MONITOR_ALLOWED_NETWORKS", []):
        try: network = ip_network(value, strict=False)
        except ValueError:
            add("error", "allowed-network-invalid", "MONITOR_ALLOWED_NETWORKS contains an invalid network entry.")
            continue
        if network.prefixlen == 0: add("error", "allowed-network-broad", "MONITOR_ALLOWED_NETWORKS must not contain an all-addresses /0 network.")
    ntfy_values = (getattr(settings, "NTFY_BASE_URL", ""), getattr(settings, "NTFY_TOPIC", ""), getattr(settings, "NTFY_TOKEN", ""))
    if any(ntfy_values) and not all(ntfy_values): add("error", "ntfy-partial", "ntfy must be fully configured with base URL, topic, and write-only publisher token or fully disabled.")
    elif not any(ntfy_values): add("warning", "ntfy-disabled", "ntfy transition publishing is not configured in this environment.")
    if not getattr(settings, "MANAGER_API_TOKEN", ""): add("warning", "manager-disabled", "The read-only GoreeCloud Manager integration token is not configured.")
    return findings


def runtime_findings() -> list[PreflightFinding]:
    findings: list[PreflightFinding] = []
    def add(severity: str, code: str, message: str) -> None:
        findings.append(PreflightFinding(severity, code, message))
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            if not row or row[0] != 1: add("error", "database-query", "Database connectivity check returned an unexpected result.")
    except Exception:
        add("error", "database-connectivity", "The target database is not reachable with the configured application identity.")
        return findings
    try:
        executor = MigrationExecutor(connection)
        if executor.migration_plan(executor.loader.graph.leaf_nodes()): add("error", "migrations-pending", "The target database has unapplied Django migrations.")
    except Exception:
        add("error", "migration-check", "The target database migration state could not be verified.")
    if not Monitor.objects.exists():
        add("warning", "no-monitors", "No monitor definitions exist yet; this is acceptable before migration import but not final parallel acceptance.")
    elif any(not heartbeat_token_is_digest(value) for value in Monitor.objects.filter(kind=Monitor.Kind.PUSH).values_list("heartbeat_token", flat=True)):
        add("error", "legacy-heartbeat-verifier", "One or more push monitors still store a legacy reusable heartbeat credential. Rotate them before target acceptance.")
    return findings


def build_preflight_report() -> dict:
    findings = configuration_findings() + runtime_findings()
    errors = sum(1 for finding in findings if finding.severity == "error")
    warnings = sum(1 for finding in findings if finding.severity == "warning")
    return {"schema": "goreecloud-monitor-target-preflight", "version": 1, "ready": errors == 0, "summary": {"errors": errors, "warnings": warnings}, "findings": [finding.to_dict() for finding in findings]}

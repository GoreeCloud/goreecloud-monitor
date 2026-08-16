from __future__ import annotations

from dataclasses import asdict, dataclass
from ipaddress import ip_network

from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from .models import Monitor


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

    if settings.DEBUG:
        add("error", "debug-enabled", "DJANGO_DEBUG must be false for a target-environment acceptance run.")

    engine = settings.DATABASES.get("default", {}).get("ENGINE", "")
    if engine != "django.db.backends.postgresql":
        add("error", "database-engine", "The target environment must use PostgreSQL, not the development SQLite database.")

    hosts = list(getattr(settings, "ALLOWED_HOSTS", []))
    if not hosts:
        add("error", "allowed-hosts-empty", "DJANGO_ALLOWED_HOSTS must contain the approved Monitor hostname.")
    if "*" in hosts:
        add("error", "allowed-hosts-wildcard", "Wildcard ALLOWED_HOSTS is not approved for GoreeCloud Monitor.")

    secret_key = str(getattr(settings, "SECRET_KEY", ""))
    if len(secret_key) < 32 or secret_key.startswith("development-only"):
        add("error", "secret-key", "DJANGO_SECRET_KEY must be a strong protected production value.")

    if not getattr(settings, "SECURE_SSL_REDIRECT", False):
        add("error", "https-redirect", "DJANGO_SECURE_SSL_REDIRECT must be enabled behind the approved HTTPS gateway.")
    if not getattr(settings, "SESSION_COOKIE_SECURE", False):
        add("error", "session-cookie", "Session cookies must be Secure.")
    if not getattr(settings, "CSRF_COOKIE_SECURE", False):
        add("error", "csrf-cookie", "CSRF cookies must be Secure.")

    for value in getattr(settings, "MONITOR_ALLOWED_NETWORKS", []):
        try:
            network = ip_network(value, strict=False)
        except ValueError:
            add("error", "allowed-network-invalid", "MONITOR_ALLOWED_NETWORKS contains an invalid network entry.")
            continue
        if network.prefixlen == 0:
            add("error", "allowed-network-broad", "MONITOR_ALLOWED_NETWORKS must not contain an all-addresses /0 network.")

    ntfy_values = (
        getattr(settings, "NTFY_BASE_URL", ""),
        getattr(settings, "NTFY_TOPIC", ""),
        getattr(settings, "NTFY_TOKEN", ""),
    )
    if any(ntfy_values) and not all(ntfy_values):
        add("error", "ntfy-partial", "ntfy must be fully configured with base URL, topic, and write-only publisher token or fully disabled.")
    elif not any(ntfy_values):
        add("warning", "ntfy-disabled", "ntfy transition publishing is not configured in this environment.")

    if not getattr(settings, "MANAGER_API_TOKEN", ""):
        add("warning", "manager-disabled", "The read-only GoreeCloud Manager integration token is not configured.")

    if int(getattr(settings, "SECURE_HSTS_SECONDS", 0)) <= 0:
        add("warning", "hsts-disabled", "HSTS is not enabled; enable it only after the final HTTPS route is verified.")

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
            if not row or row[0] != 1:
                add("error", "database-query", "Database connectivity check returned an unexpected result.")
    except Exception:
        add("error", "database-connectivity", "The target database is not reachable with the configured application identity.")
        return findings

    try:
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            add("error", "migrations-pending", "The target database has unapplied Django migrations.")
    except Exception:
        add("error", "migration-check", "The target database migration state could not be verified.")

    if not Monitor.objects.exists():
        add("warning", "no-monitors", "No monitor definitions exist yet; this is acceptable before migration import but not final parallel acceptance.")

    return findings


def build_preflight_report() -> dict:
    findings = configuration_findings() + runtime_findings()
    errors = sum(1 for finding in findings if finding.severity == "error")
    warnings = sum(1 for finding in findings if finding.severity == "warning")
    return {
        "schema": "goreecloud-monitor-target-preflight",
        "version": 1,
        "ready": errors == 0,
        "summary": {"errors": errors, "warnings": warnings},
        "findings": [finding.to_dict() for finding in findings],
    }

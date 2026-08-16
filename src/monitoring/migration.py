from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError

from .models import Monitor


SENSITIVE_MONITOR_FIELDS = {
    "headers",
    "body",
    "basic_auth_user",
    "basic_auth_pass",
    "oauth_client_id",
    "oauth_client_secret",
    "oauth_token_url",
    "oauth_scopes",
    "oauth_audience",
    "oauth_auth_method",
    "bearer_token",
    "tlsCa",
    "tlsCert",
    "tlsKey",
    "grpcBody",
    "grpcMetadata",
    "databaseConnectionString",
    "radiusUsername",
    "radiusPassword",
    "radiusSecret",
    "mqttUsername",
    "mqttPassword",
    "kafkaProducerSaslOptions",
    "rabbitmqUsername",
    "rabbitmqPassword",
}

SUPPORTED_KUMA_TYPES = {"http", "keyword", "json-query", "port", "tcp", "dns", "push"}


@dataclass(slots=True)
class MigrationIssue:
    severity: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(slots=True)
class KumaMonitorMapping:
    source_name: str
    source_type: str
    values: dict[str, Any] | None
    issues: list[MigrationIssue]

    @property
    def supported(self) -> bool:
        return self.values is not None and not any(issue.severity == "error" for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(issue.severity == "warning" for issue in self.issues)

    def to_report(self) -> dict[str, Any]:
        return {
            "name": self.source_name,
            "type": self.source_type,
            "supported": self.supported,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def _nonempty(value: Any) -> bool:
    return value not in (None, "", [], {}, False)


def load_kuma_monitors(path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = Path(path)
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"Unable to read Uptime Kuma JSON: {exc}") from exc

    metadata: dict[str, Any] = {"source_format": "unknown"}

    if isinstance(document, dict) and document.get("ok") is True and "data" in document:
        document = document["data"]
        metadata["wrapped_json_output"] = True

    if isinstance(document, dict) and isinstance(document.get("monitors"), list):
        metadata["source_format"] = "kuma-cli-config-export"
        metadata["source_version"] = document.get("version")
        monitors = document["monitors"]
    elif isinstance(document, dict) and isinstance(document.get("data"), list):
        metadata["source_format"] = "kuma-cli-monitor-list"
        monitors = document["data"]
    elif isinstance(document, list):
        metadata["source_format"] = "monitor-list"
        monitors = document
    elif isinstance(document, dict) and _nonempty(document.get("type")):
        metadata["source_format"] = "single-monitor"
        monitors = [document]
    else:
        raise ValidationError("JSON is not a recognized kuma-cli configuration or monitor export")

    if not all(isinstance(item, dict) for item in monitors):
        raise ValidationError("Uptime Kuma monitor entries must be JSON objects")
    return monitors, metadata


def _issue(issues: list[MigrationIssue], severity: str, code: str, message: str) -> None:
    issues.append(MigrationIssue(severity=severity, code=code, message=message))


def _int_value(raw: dict[str, Any], key: str, default: int) -> int:
    value = raw.get(key, default)
    if value in (None, ""):
        return default
    return int(value)


def _normalize_json_path(path: str) -> str | None:
    value = path.strip()
    if not value:
        return ""
    if value == "$":
        return ""
    if value.startswith("$."):
        value = value[2:]
    if "$" in value or "[" in value or "]" in value:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
        return None
    return value


def _expected_status(raw: dict[str, Any], issues: list[MigrationIssue]) -> int:
    accepted = raw.get("accepted_statuscodes")
    if not accepted:
        return 200
    if not isinstance(accepted, list):
        _issue(issues, "warning", "status-format", "Accepted status-code configuration was not a list; Monitor will require HTTP 200 until reviewed.")
        return 200
    exact: list[int] = []
    ranges: list[str] = []
    for item in accepted:
        if isinstance(item, int):
            exact.append(item)
            continue
        text = str(item).strip()
        if text.isdigit():
            exact.append(int(text))
        elif re.fullmatch(r"\d{3}-\d{3}", text):
            ranges.append(text)
        else:
            ranges.append(text)
    if len(exact) == 1 and not ranges and 100 <= exact[0] <= 599:
        return exact[0]
    _issue(
        issues,
        "warning",
        "status-range-approximation",
        "Uptime Kuma accepts multiple or ranged HTTP statuses; Monitor v0.1 uses one exact status and will require HTTP 200 until reviewed.",
    )
    return 200


def map_kuma_monitor(raw: dict[str, Any]) -> KumaMonitorMapping:
    name = str(raw.get("name") or "").strip()
    source_type = str(raw.get("type") or "").strip().lower()
    issues: list[MigrationIssue] = []

    if not name:
        _issue(issues, "error", "missing-name", "Monitor has no name.")
    if source_type not in SUPPORTED_KUMA_TYPES:
        _issue(issues, "error", "unsupported-type", f"Uptime Kuma monitor type '{source_type or 'unknown'}' is not supported by the migration importer.")

    sensitive_present = sorted(field for field in SENSITIVE_MONITOR_FIELDS if _nonempty(raw.get(field)))
    if sensitive_present:
        _issue(
            issues,
            "error",
            "manual-authentication-required",
            "The source monitor contains authentication, request-body, certificate, or other sensitive configuration that Monitor does not import automatically.",
        )

    if raw.get("ignoreTls") is True:
        _issue(issues, "error", "tls-verification-disabled", "Source monitor disables TLS verification; GoreeCloud Monitor will not import this weaker security setting.")
    if raw.get("upsideDown") is True:
        _issue(issues, "error", "upside-down", "Upside-down monitoring semantics are not supported.")
    if _nonempty(raw.get("proxyId")):
        _issue(issues, "error", "proxy-unsupported", "Per-monitor Uptime Kuma proxy configuration is not imported.")
    if _nonempty(raw.get("conditions")):
        _issue(issues, "error", "conditions-unsupported", "Uptime Kuma condition expressions are not supported by the v0.1 importer.")

    if any(issue.severity == "error" for issue in issues):
        return KumaMonitorMapping(name or "<unnamed>", source_type or "unknown", None, issues)

    try:
        interval = _int_value(raw, "interval", 60)
        timeout = _int_value(raw, "timeout", min(10, interval))
        retries = max(0, _int_value(raw, "maxretries", 0))
        retry_interval = _int_value(raw, "retryInterval", interval)
        max_redirects = _int_value(raw, "maxredirects", 10)
    except (TypeError, ValueError):
        _issue(issues, "error", "invalid-timing", "Interval, timeout, retry, or redirect values are not valid integers.")
        return KumaMonitorMapping(name, source_type, None, issues)

    if interval < 5:
        _issue(issues, "error", "interval-too-short", "GoreeCloud Monitor does not support intervals below 5 seconds.")
    if timeout < 1 or (source_type != "push" and timeout > interval):
        _issue(issues, "error", "invalid-timeout", "Timeout must be at least 1 second and must not exceed the monitor interval.")
    if retries:
        _issue(
            issues,
            "warning",
            "retry-model-approximation",
            "Uptime Kuma retry attempts are mapped to consecutive-failure thresholding; retry timing is not identical.",
        )
    if retries and retry_interval != interval:
        _issue(
            issues,
            "warning",
            "retry-interval-not-preserved",
            "Uptime Kuma retryInterval is not represented separately by Monitor v0.1.",
        )

    enabled_notifications = raw.get("notificationIDList")
    if isinstance(enabled_notifications, dict) and any(bool(v) for v in enabled_notifications.values()):
        _issue(issues, "warning", "notifications-not-imported", "Uptime Kuma notification assignments are intentionally not imported; configure GoreeCloud notification publishing separately.")
    if raw.get("tags"):
        _issue(issues, "warning", "tags-not-imported", "Uptime Kuma tags are not part of the Monitor v0.1 data model.")

    values: dict[str, Any] = {
        "name": name,
        "interval_seconds": interval,
        "timeout_seconds": max(1, timeout),
        "failure_threshold": retries + 1,
        "recovery_threshold": 1,
    }

    if source_type in {"http", "keyword", "json-query"}:
        target = str(raw.get("url") or "").strip()
        parsed = urlsplit(target)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            _issue(issues, "error", "invalid-url", "HTTP-family monitor has no valid HTTP or HTTPS URL.")
        method = str(raw.get("method") or "GET").upper()
        if method not in {"GET", "HEAD"}:
            _issue(issues, "error", "unsupported-method", f"HTTP method {method} is not supported by Monitor v0.1.")
        if method == "HEAD" and source_type in {"keyword", "json-query"}:
            _issue(issues, "error", "head-assertion", "HEAD monitors cannot preserve keyword or JSON response assertions.")
        values.update(
            {
                "kind": Monitor.Kind.HTTPS if parsed.scheme == "https" else Monitor.Kind.HTTP,
                "target": target,
                "http_method": method,
                "expected_status_code": _expected_status(raw, issues),
                "follow_redirects": max_redirects != 0,
                "tls_warning_days": 14,
            }
        )
        if max_redirects > 5:
            _issue(issues, "warning", "redirect-limit", "Uptime Kuma allows more than five redirects; Monitor deliberately caps redirect traversal at five.")
        if source_type == "keyword":
            keyword = str(raw.get("keyword") or "")
            if not keyword:
                _issue(issues, "error", "missing-keyword", "Keyword monitor has no keyword.")
            if raw.get("invertKeyword") is True:
                _issue(issues, "error", "inverted-keyword", "Inverted keyword checks are not supported.")
            values["expected_body_text"] = keyword
        elif source_type == "json-query":
            operator = str(raw.get("jsonPathOperator") or "==").strip().lower()
            if operator not in {"==", "=", "eq"}:
                _issue(issues, "error", "json-operator", "Only equality JSON assertions can be migrated automatically.")
            normalized_path = _normalize_json_path(str(raw.get("jsonPath") or ""))
            if normalized_path is None:
                _issue(issues, "error", "json-path", "Complex JSONPath syntax cannot be represented by Monitor v0.1.")
            elif not normalized_path:
                _issue(issues, "error", "json-path", "JSON query monitor has no usable path.")
            else:
                values["expected_json_path"] = normalized_path
                values["expected_json_value"] = str(raw.get("expectedValue") if raw.get("expectedValue") is not None else "")

    elif source_type in {"port", "tcp"}:
        hostname = str(raw.get("hostname") or "").strip()
        try:
            port = int(raw.get("port"))
        except (TypeError, ValueError):
            port = 0
        if not hostname or not 1 <= port <= 65535:
            _issue(issues, "error", "invalid-tcp-target", "TCP monitor requires a hostname and port from 1 through 65535.")
        values.update({"kind": Monitor.Kind.TCP, "target": hostname, "port": port})

    elif source_type == "dns":
        hostname = str(raw.get("hostname") or raw.get("url") or "").strip()
        record_type = str(raw.get("dns_resolve_type") or "A").upper()
        if not hostname:
            _issue(issues, "error", "invalid-dns-target", "DNS monitor has no hostname.")
        if record_type not in {"A", "AAAA", "CNAME"}:
            _issue(issues, "error", "unsupported-dns-type", f"DNS record type {record_type} is not supported by Monitor v0.1.")
        if _nonempty(raw.get("dns_resolve_server")):
            _issue(issues, "warning", "custom-resolver-not-preserved", "A custom Uptime Kuma DNS resolver is not preserved; Monitor uses its configured system resolver.")
        values.update({"kind": Monitor.Kind.DNS, "target": hostname, "dns_record_type": record_type})

    elif source_type == "push":
        values.update(
            {
                "kind": Monitor.Kind.PUSH,
                "target": "",
                "heartbeat_grace_seconds": 5,
                "timeout_seconds": 1,
            }
        )
        _issue(
            issues,
            "warning",
            "push-token-rotated",
            "Uptime Kuma push tokens are not imported. Monitor will generate a new heartbeat token and the sender must be updated before activation.",
        )

    if any(issue.severity == "error" for issue in issues):
        return KumaMonitorMapping(name, source_type, None, issues)

    candidate = Monitor(**values)
    try:
        candidate.full_clean(exclude=["heartbeat_token"])
    except Exception as exc:
        _issue(issues, "error", "monitor-validation", f"Mapped definition failed GoreeCloud Monitor validation: {exc}")
        return KumaMonitorMapping(name, source_type, None, issues)

    return KumaMonitorMapping(name, source_type, values, issues)


def migration_report(mappings: list[KumaMonitorMapping], metadata: dict[str, Any]) -> dict[str, Any]:
    supported = sum(1 for item in mappings if item.supported)
    warnings = sum(sum(1 for issue in item.issues if issue.severity == "warning") for item in mappings)
    errors = sum(sum(1 for issue in item.issues if issue.severity == "error") for item in mappings)
    return {
        "schema": "goreecloud-monitor-uptime-kuma-migration-report",
        "version": 1,
        "source": metadata,
        "summary": {
            "source_monitors": len(mappings),
            "supported": supported,
            "unsupported": len(mappings) - supported,
            "warnings": warnings,
            "errors": errors,
        },
        "monitors": [item.to_report() for item in mappings],
    }

from __future__ import annotations

from copy import deepcopy
from typing import Any
from urllib.parse import urlsplit, urlunsplit


REDACTED_PRESENT = "__GOREECLOUD_REDACTED_PRESENT__"

# Keep this list deliberately conservative. These fields can contain reusable
# credentials, request payloads, client certificates, connection strings, or
# other material that must not be copied into an evidence bundle.
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

# Configuration fields used by GoreeCloud Monitor migration/reconciliation plus
# a small amount of harmless source metadata. Everything else is omitted by
# name so the evidence bundle remains reviewable and bounded.
SAFE_CONFIG_FIELDS = {
    "id",
    "name",
    "type",
    "active",
    "description",
    "interval",
    "timeout",
    "maxretries",
    "retryInterval",
    "maxredirects",
    "url",
    "method",
    "accepted_statuscodes",
    "keyword",
    "invertKeyword",
    "jsonPathOperator",
    "jsonPath",
    "expectedValue",
    "hostname",
    "port",
    "dns_resolve_type",
    "dns_resolve_server",
    "ignoreTls",
    "upsideDown",
    "proxyId",
    "conditions",
    "notificationIDList",
    "tags",
}


def _nonempty(value: Any) -> bool:
    return value not in (None, "", [], {}, False)


def _sanitize_url(value: Any) -> tuple[Any, list[str]]:
    if not isinstance(value, str) or not value:
        return value, []
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value, []

    redactions: list[str] = []
    netloc = parsed.netloc
    if parsed.username is not None or parsed.password is not None:
        host = parsed.hostname or ""
        try:
            port = parsed.port
        except ValueError:
            port = None
            redactions.append("url-invalid-port")
        if port is not None:
            host = f"{host}:{port}"
        netloc = host
        redactions.append("url-credentials")

    query = parsed.query
    if query:
        query = "goreecloud_redacted=1"
        redactions.append("url-query")

    fragment = parsed.fragment
    if fragment:
        fragment = ""
        redactions.append("url-fragment")

    return urlunsplit((parsed.scheme, netloc, parsed.path, query, fragment)), redactions


def sanitize_config_monitor(raw: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    safe: dict[str, Any] = {}
    redacted_fields: list[str] = []
    omitted_fields: list[str] = []

    for key, value in raw.items():
        if key in SENSITIVE_MONITOR_FIELDS:
            if _nonempty(value):
                safe[key] = REDACTED_PRESENT
                redacted_fields.append(key)
            continue

        if key not in SAFE_CONFIG_FIELDS:
            if _nonempty(value):
                omitted_fields.append(key)
            continue

        if key == "url":
            sanitized, url_redactions = _sanitize_url(value)
            safe[key] = sanitized
            redacted_fields.extend(url_redactions)
            # The existing importer already blocks a non-empty sensitive field.
            # Inject a sentinel when URL credentials/query material was removed
            # so a sanitized source can never appear safer than the original.
            if url_redactions:
                safe.setdefault("headers", REDACTED_PRESENT)
            continue

        if key == "conditions" and _nonempty(value):
            safe[key] = [REDACTED_PRESENT]
            redacted_fields.append("conditions")
            continue

        safe[key] = deepcopy(value)

    if redacted_fields:
        safe["__goreecloud_redacted_fields"] = sorted(set(redacted_fields))
    if omitted_fields:
        safe["__goreecloud_omitted_fields"] = sorted(set(omitted_fields))

    report = {
        "name": str(raw.get("name") or "").strip() or "<unnamed>",
        "type": str(raw.get("type") or "unknown").strip().lower() or "unknown",
        "redacted_fields": sorted(set(redacted_fields)),
        "omitted_fields": sorted(set(omitted_fields)),
    }
    return safe, report


def _monitor_map_to_list(value: dict[Any, Any]) -> list[dict[str, Any]] | None:
    """Normalize kuma-cli v2's ID-keyed monitor map without trusting its keys blindly."""

    normalized: list[tuple[int, dict[str, Any]]] = []
    for key, raw in value.items():
        if not isinstance(raw, dict):
            return None
        try:
            key_id = int(str(key))
        except (TypeError, ValueError):
            return None
        raw_id = raw.get("id")
        if raw_id is not None:
            try:
                if int(raw_id) != key_id:
                    raise ValueError("monitor map key does not match monitor id")
            except (TypeError, ValueError) as exc:
                raise ValueError("monitor map contains an invalid or mismatched monitor id") from exc
        normalized.append((key_id, raw))

    normalized.sort(key=lambda item: item[0])
    return [raw for _, raw in normalized]


def _extract_config_document(document: Any) -> tuple[list[dict[str, Any]], Any, str]:
    value = document
    source_format = "unknown"
    source_version = None

    if isinstance(value, dict) and value.get("ok") is True and "data" in value:
        value = value["data"]

    if isinstance(value, dict) and isinstance(value.get("monitors"), list):
        source_format = "kuma-cli-config-export"
        source_version = value.get("version")
        monitors = value["monitors"]
    elif isinstance(value, dict) and isinstance(value.get("data"), list):
        source_format = "kuma-cli-monitor-list"
        monitors = value["data"]
    elif isinstance(value, list):
        source_format = "monitor-list"
        monitors = value
    elif isinstance(value, dict) and value.get("type"):
        source_format = "single-monitor"
        monitors = [value]
    elif isinstance(value, dict):
        mapped = _monitor_map_to_list(value)
        if mapped is None:
            raise ValueError("JSON is not a recognized kuma-cli configuration or monitor export")
        source_format = "kuma-cli-v2-monitor-map"
        monitors = mapped
    else:
        raise ValueError("JSON is not a recognized kuma-cli configuration or monitor export")

    if not all(isinstance(item, dict) for item in monitors):
        raise ValueError("Uptime Kuma monitor entries must be JSON objects")
    return monitors, source_version, source_format


def sanitize_config_document(document: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    monitors, source_version, source_format = _extract_config_document(document)
    sanitized: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    for raw in monitors:
        safe, report = sanitize_config_monitor(raw)
        sanitized.append(safe)
        reports.append(report)

    redacted = sum(1 for item in reports if item["redacted_fields"])
    omitted = sum(1 for item in reports if item["omitted_fields"])
    output = {
        "version": source_version,
        "monitors": sanitized,
        "__goreecloud_sanitization": {
            "schema": "goreecloud-monitor-sanitized-uptime-kuma-export",
            "version": 1,
            "source_format": source_format,
            "source_monitors": len(monitors),
            "monitors_with_redactions": redacted,
            "monitors_with_omissions": omitted,
        },
    }
    report = {
        "schema": "goreecloud-monitor-uptime-kuma-sanitization-report",
        "version": 1,
        "source_format": source_format,
        "source_monitors": len(monitors),
        "monitors_with_redactions": redacted,
        "monitors_with_omissions": omitted,
        "monitors": reports,
    }
    return output, report


def sanitize_runtime_document(document: Any) -> dict[str, Any]:
    value = document
    if isinstance(value, dict) and value.get("ok") is True and "data" in value:
        value = value["data"]
    if isinstance(value, dict) and isinstance(value.get("data"), list):
        monitors = value["data"]
    elif isinstance(value, list):
        monitors = value
    else:
        raise ValueError("JSON is not a recognized kuma-cli runtime snapshot")

    sanitized: list[dict[str, Any]] = []
    heartbeat_seen = False
    for raw in monitors:
        if not isinstance(raw, dict):
            raise ValueError("Uptime Kuma runtime entries must be JSON objects")
        heartbeat = raw.get("heartbeat")
        safe_heartbeat = None
        if isinstance(heartbeat, dict):
            heartbeat_seen = True
            safe_heartbeat = {
                "status": heartbeat.get("status"),
                "ping": heartbeat.get("ping"),
            }
        sanitized.append(
            {
                "id": raw.get("id"),
                "name": raw.get("name"),
                "type": raw.get("type"),
                "active": raw.get("active"),
                "heartbeat": safe_heartbeat,
            }
        )

    if monitors and not heartbeat_seen:
        raise ValueError("runtime snapshot contains no heartbeat data")

    return {
        "data": sanitized,
        "__goreecloud_sanitization": {
            "schema": "goreecloud-monitor-sanitized-uptime-kuma-runtime",
            "version": 1,
            "source_monitors": len(sanitized),
            "fields": ["id", "name", "type", "active", "heartbeat.status", "heartbeat.ping"],
        },
    }

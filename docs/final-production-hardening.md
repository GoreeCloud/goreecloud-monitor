# GoreeCloud Monitor Final Production-Hardening Source Layer

## Purpose

This document records the source-level hardening applied after the Glaze UI 1.0 and Wardveil Security layers. It does not authorize production deployment or Uptime Kuma retirement.

## Credential boundary

Push heartbeat authentication now uses an HTTPS POST to `/api/v1/heartbeat/` with a Bearer credential. New and rotated raw credentials are shown once and only their SHA-256 verifier is persisted. The verifier is not rendered in the standard application or Django administration.

The existing database field name is retained so no Django schema migration is introduced into the current pre-production rollback chain. Legacy path-token behavior is disabled by default, migration-only when explicitly enabled, and a production-preflight error. Production preflight also rejects any remaining push monitor whose database value is not a verifier.

Because a predecessor interprets the historical field as a reusable raw token, a rollback to that predecessor after hardened credential issuance/rotation requires explicit credential reissuance/reconfiguration. This limitation must be incorporated into the accepted live rollback evidence before cutover. There are no production Monitor push senders yet, so no production credential was migrated by this source work.

## Operational observability

Every dynamic request receives a server-generated correlation identifier. The response exposes it as `X-Request-ID` so an administrator can correlate a failure with application events without revealing infrastructure details in the UI.

`monitoring.access` emits minimized JSON events using resolved route names rather than raw paths. Events may contain request ID, method, route, status, duration, authenticated state, numeric user ID, staff flag, and exception class. They do not contain raw paths, query strings, client IP addresses, user agents, bodies, cookies, authorization values, target URLs, or credentials.

Django's normal request/server application loggers are disabled because their default messages can contain raw paths. Reverse-proxy and host logging remain separate infrastructure responsibilities.

## Error behavior

Monitor provides local Glaze UI/Wardveil 400, 403, 404, and 500 experiences. Error pages provide an actionable safe summary and the private request ID when available. They do not render exceptions, raw request values, target information, credentials, or internal diagnostic content.

## Application identity

The existing `static/monitoring/img/monitor-mark.svg` pulse/status mark is the canonical application identity. No artwork was generated or redrawn by this layer. Its SHA-256 is pinned in `packaging/app-identity.json` and validated by `scripts/validate_app_identity.py` and automated tests.

Web shell, login, Django administration, browser favicon, and the local web-app manifest all share that source identity. The repository currently has no AppImage or Android client/package implementation. Those surfaces are explicitly blocked in the identity contract so future packaging cannot be mistaken for complete or ship a conflicting icon.

## Release boundary

Source completion does not prove:

- target-native PostgreSQL backup/restore on the accepted production paths;
- persistent isolated web/worker deployment;
- reviewed live monitor import and activation;
- repeated live parity against Uptime Kuma;
- controlled DOWN/RECOVERED, TLS, maintenance, or notification scenarios;
- resolver-specific DNS or Ping/ICMP parity decisions;
- target Caddy/NetBird/firewall/Wardveil acceptance;
- AppImage or Android client implementation and packaging;
- manual Compact/Expanded, Light/Dark, keyboard, zoom/reflow, screen-reader, and representative-browser acceptance;
- live rollback after hardened push credential issuance;
- explicit production cutover or Uptime Kuma retirement.

Uptime Kuma therefore remains authoritative until those applicable gates are completed and cutover is explicitly approved.

# GoreeCloud Monitor Reconciled Final Production-Hardening Source Layer

## Purpose

This document records the source-level credential, observability, error-state, and reliability hardening applied **after** the validated cross-platform product-identity layer. It does not authorize production deployment or Uptime Kuma retirement.

## Predecessor identity boundary

The direct predecessor is `agent/cross-platform-icon-readiness`, which owns Monitor's canonical cross-platform application identity. This hardening layer does not redraw, generate, replace, or fork that identity.

The authoritative product artwork remains `assets/identity/goreecloud-monitor-icon.svg`. Web favicon/manifest variants, the Linux/AppImage launcher input, and Android adaptive/round/monochrome launcher inputs remain governed by the predecessor's product-identity contract and tests. Wardveil Security by GoreeCloud remains the separate security/protection identity.

Standalone AppImage and Android client applications are not represented as implemented merely because their approved launcher inputs exist.

## Credential boundary

Push heartbeat authentication now uses an HTTPS POST to `/api/v1/heartbeat/` with a Bearer credential. New and rotated raw credentials are shown once and only their SHA-256 verifier is persisted. The verifier is not rendered in the standard application or Django administration.

The existing database field name is retained so no Django schema migration is introduced into the current pre-production rollback chain. Legacy path-token behavior is disabled by default, migration-only when explicitly enabled, and a production-preflight error. Production preflight also rejects any remaining push monitor whose database value is not a verifier.

Because a pre-hardening predecessor interprets the historical field as a reusable raw token, rollback after hardened credential issuance/rotation requires explicit credential reissuance/reconfiguration. This limitation must be incorporated into accepted live rollback evidence before cutover. There are no production Monitor push senders yet, so no production credential was migrated by this source work.

## Operational observability

Every dynamic request receives a server-generated correlation identifier. The response exposes it as `X-Request-ID` so an administrator can correlate a failure with application events without revealing infrastructure details in the UI.

`monitoring.access` emits minimized JSON events using resolved route names rather than raw paths. Events may contain request ID, method, route, status, duration, authenticated state, numeric user ID, staff flag, worker lifecycle, numeric monitor ID, state transition, bounded latency, integration result, exception class, and safe source frames when relevant. Safe source frames contain basename, line, and function only.

Events do not contain raw paths, query strings, client IP addresses, user agents, bodies, cookies, authorization values, target URLs, credentials, exception messages, local variables, function arguments, or absolute paths. Django's normal request/server application loggers are disabled because their default messages can contain raw paths. Reverse-proxy and host logging remain separate infrastructure responsibilities.

## Error behavior

Monitor provides local Glaze UI/Wardveil 400, 403, 404, and 500 experiences. Error pages provide an actionable safe summary and private request ID when available. They do not render exceptions, raw request values, target information, credentials, or internal diagnostic content. The error surface uses the canonical Monitor product icon from the predecessor identity layer.

## Bounded workflows

Primary monitor and maintenance lists use bounded pagination. Non-staff authenticated users receive operational state/latency/timing information without raw monitor failure diagnostics or push credential material.

## Validation boundary

The source suite must validate both the predecessor's cross-platform identity contract and this layer's credential, logging, authorization, notification, error-state, recovery, deployment, and rollback behavior on the exact candidate head.

Source completion does not prove:

- target-native PostgreSQL backup/restore on the accepted production paths;
- persistent isolated web/worker deployment;
- reviewed live monitor import and activation;
- repeated live parity against Uptime Kuma;
- controlled DOWN/RECOVERED, TLS, maintenance, or notification scenarios;
- resolver-specific DNS or Ping/ICMP parity decisions;
- target Caddy/NetBird/firewall/Wardveil acceptance;
- standalone AppImage or Android client implementation/packaging/signing;
- manual Compact/Expanded, Light/Dark, keyboard, zoom/reflow, screen-reader, small-icon/maskable/launcher, and representative-browser/OS acceptance;
- live rollback after hardened push credential issuance;
- explicit production cutover or Uptime Kuma retirement.

Uptime Kuma therefore remains authoritative until those applicable gates are completed and cutover is explicitly approved.

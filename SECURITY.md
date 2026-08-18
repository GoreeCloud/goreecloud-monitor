# Security Policy

## Wardveil Security identity

GoreeCloud Monitor presents security and protection posture under **Wardveil Security by GoreeCloud**. The approved protection phrase is **Protected by Wardveil**.

Wardveil is the platform-wide security identity and presentation layer. It does not replace Django authentication and authorization, Caddy, NetBird, firewall rules, secrets management, vulnerability management, backup/recovery controls, or other technical authorities.

## Scope

Monitor is security-sensitive because it authenticates administrators, stores operational history, accepts push-heartbeat credentials, makes outbound network requests, publishes minimized transition alerts, and exposes a read-only platform summary API.

## Authentication and authorization

- Administrative UI requires Django authentication; monitor and maintenance mutation require staff status.
- Protected Settings, Wardveil posture, exact target-network allowlists, raw diagnostic details, and credential issuance/rotation are staff-only.
- Manager integration is read-only and uses a separate bearer credential with constant-time comparison.
- Login, logout, authentication failure, privileged configuration mutation, and credential issuance/rotation generate minimized Wardveil security events.

## Push heartbeat credentials

The primary push endpoint is `POST /api/v1/heartbeat/` with `Authorization: Bearer <credential>`.

New and rotated raw credentials are displayed only on a one-time issuance response. The database stores only a SHA-256 verifier in the historical `heartbeat_token` column; the field name is retained solely to keep the current pre-production schema/rollback chain unchanged. The persisted verifier is omitted from normal UI and Django administration.

`MONITOR_ALLOW_LEGACY_PATH_HEARTBEATS` defaults to `false`. When enabled temporarily for migration, the legacy path endpoint can accept an existing source credential and immediately replace an accepted plaintext database value with its verifier. Production target preflight fails closed if legacy path compatibility is enabled or if any legacy plaintext push credential remains.

A rollback to a predecessor that understands the historical column as a reusable raw token is **not** credential-compatible after a push credential has been issued or rotated by this hardening layer. Because Monitor has not reached production/cutover, no production sender relies on that predecessor contract. Before production acceptance, the live rollback procedure must use the accepted hardened release boundary or include explicit push-credential reissuance/reconfiguration evidence.

## Outbound request and SSRF controls

- Monitor URL userinfo/embedded credentials are rejected.
- HTTP clients ignore ambient proxy and `.netrc` credentials (`trust_env=False`).
- Private, reserved, loopback, and link-local destinations are blocked unless explicitly listed in `MONITOR_ALLOWED_NETWORKS`.
- Every address returned by the preflight resolution must pass the destination policy.
- Worker concurrency, request timeouts, redirect hops, and inspected response bodies are bounded.

The current design validates the addresses returned during Monitor's preflight resolution before the application-layer connection is opened. A later DNS resolution by the HTTP/TCP/TLS client remains a documented time-of-check/time-of-use boundary. Do not monitor attacker-controlled DNS names or broaden private allowlists to work around this limitation. A future connection-pinning design must preserve TLS hostname verification, redirects, DNS behavior, portability, and existing tests.

## Browser and session controls

Dynamic application responses receive a restrictive Content Security Policy, Permissions Policy, same-origin resource policy, clickjacking protection, no-index/no-archive policy, same-origin referrer/opener boundaries, and no-store caching.

Production sessions use Secure/HttpOnly/SameSite cookies and host-only cookie names. Target preflight requires HTTPS redirect and at least one year of HSTS after the approved HTTPS route is validated.

Glaze UI 400/403/404/500 experiences return safe messages without exception details, raw request values, infrastructure data, or secrets. Server-generated request IDs provide private correlation for troubleshooting.

## Notification and integration boundaries

Notifications exclude target URLs, response bodies, credentials, reusable secrets, query strings, and raw exception diagnostics. Controlled TLS-expiry context remains permitted. ntfy requires a complete dedicated publisher configuration; partial configuration fails closed. GoreeCloud Notify remains gated until its approved producer contract and production acceptance exist.

## Structured logging

`monitoring.wardveil` records minimized JSON security events. `WARDVEIL_LOG_LEVEL` controls its level and defaults to `INFO`.

`monitoring.access` records minimized JSON request events. `MONITOR_ACCESS_LOG_LEVEL` controls its level and defaults to `INFO`. Each request receives a server-generated correlation ID exposed as `X-Request-ID`. Permitted request fields are event type, generated request ID, HTTP method, resolved Django route name, response status, duration, authenticated boolean, numeric user ID when authenticated, and staff flag when authenticated. Exception events add the exception **class name only**.

The application access schema excludes raw URL paths, query strings, client IP addresses, user agents, cookies, request/response bodies, authorization headers, target URLs, usernames, and credentials. Django's default raw-path request/server application loggers are suppressed in favor of this schema. Caddy, container-runtime, systemd/journald, and other infrastructure logging remain governed independently and must not be configured to capture reusable authorization headers.

Security and access events support troubleshooting and review. They are not a SIEM, immutable audit ledger, or substitute for GoreeCloud change logs.

## Supply chain, deployment, and recovery

- Production secrets belong in protected environment/secrets storage, never source control.
- Production Compose uses a non-root/runtime-minimized application image, dropped Linux capabilities, no-new-privileges, read-only application root filesystem, and no host-published Monitor/database ports.
- CI performs Django checks, dependency consistency and vulnerability auditing, PostgreSQL recovery validation, container/runtime validation, fixed HIGH/CRITICAL image scanning, disposable production-topology validation, and rollback compatibility testing.
- Production acceptance remains separate from source CI. Target-native restore, controlled incidents/recovery, notification transitions, network parity, live rollback, and manual UI/accessibility acceptance remain required.

## Application identity and packaging

The canonical product artwork is `static/monitoring/img/monitor-mark.svg`, governed by `packaging/app-identity.json`. Web surfaces use that mark consistently. The repository currently contains no AppImage or Android APK/AAB client implementation; future client packaging must derive launcher artwork from the canonical source rather than introducing independent imagery. Wardveil identity must not replace the Monitor application icon.

## Reporting

Do not publish exploit details or secret material in public issues. Use the private security-reporting path configured for the repository when available.

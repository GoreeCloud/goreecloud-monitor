# Security Policy

## Wardveil Security identity

GoreeCloud Monitor presents its security and protection posture under **Wardveil Security by GoreeCloud**. The approved protection phrase is **Protected by Wardveil**.

Wardveil is the platform-wide security identity and presentation layer. It does not replace Django authentication and authorization, Caddy, NetBird, firewall rules, secrets management, vulnerability management, backup/recovery controls, or other technical authorities. See `docs/wardveil-security.md` for the Monitor-specific implementation boundary.

## Scope

GoreeCloud Monitor is security-sensitive because it authenticates administrators, stores operational history, accepts heartbeat tokens, makes outbound network requests, publishes minimized transition alerts, and exposes a read-only platform summary API.

## Core controls

- Administrative UI requires Django authentication; monitor and maintenance mutation require staff status.
- Protected Settings, Wardveil posture, heartbeat credentials, and raw diagnostic details are restricted to staff.
- Manager integration is read-only and uses a separate bearer credential with constant-time comparison.
- Monitor URL userinfo/embedded credentials are rejected.
- HTTP clients ignore ambient proxy and `.netrc` credentials (`trust_env=False`).
- Private, reserved, loopback, and link-local destinations are blocked unless explicitly listed in `MONITOR_ALLOWED_NETWORKS`.
- Every address returned by the preflight resolution must pass the destination policy. This narrows SSRF exposure; administrators should still avoid untrusted DNS zones because application-layer clients can perform a later resolution.
- Worker concurrency, request timeouts, redirect hops, and inspected response bodies are bounded.
- Notifications exclude target URLs, response bodies, credentials, reusable secrets, query strings, and raw exception diagnostics.
- Unauthenticated heartbeat acknowledgements are generic and HEAD requests cannot mutate heartbeat state.
- Dynamic application responses receive a restrictive Content Security Policy, Permissions Policy, same-origin resource policy, clickjacking protection, no-index/no-archive policy, same-origin referrer/opener boundaries, and no-store caching.
- Production sessions use Secure/HttpOnly/SameSite cookies and host-only cookie names; target preflight requires HTTPS redirect and at least one year of HSTS after the approved HTTPS route is validated.
- Security-relevant authentication and privileged configuration actions emit minimized structured Wardveil events without copying secrets, target URLs, client IP addresses, request bodies, or raw diagnostics.
- Production secrets belong in protected environment/secrets storage, never the repository.
- CI performs Django deployment checks, dependency consistency and vulnerability auditing, PostgreSQL recovery validation, non-root/runtime-minimized container validation, fixed HIGH/CRITICAL container vulnerability scanning, disposable production-topology validation, and immediate-predecessor rollback compatibility.

## SSRF policy

Monitoring private GoreeCloud services is legitimate, so private-address access cannot be globally disabled. Instead, operators explicitly grant the narrow private CIDRs required by the monitor worker. Do not use broad RFC1918 allowlists when a smaller Docker, NetBird, or service subnet is sufficient.

The current design validates the addresses returned during Monitor's preflight resolution before the application-layer connection is opened. A later DNS resolution by the HTTP/TCP/TLS client remains a documented time-of-check/time-of-use boundary. Do not monitor attacker-controlled DNS names or broaden private allowlists to work around this limitation. A future connection-pinning design must preserve TLS hostname verification, redirect validation, DNS behavior, portability, and existing tests before it can replace this boundary.

## Security-event logging

The `monitoring.wardveil` logger records minimized security events. `WARDVEIL_LOG_LEVEL` controls its level and defaults to `INFO`.

Permitted fields are event type, outcome, authenticated numeric user ID and staff flag when applicable, object type, and object ID. Reusable credentials, usernames from failed login attempts, tokens, targets, client IP addresses, request data, and diagnostic content are outside the event schema.

These events support operational review. They are not an authentication database, a SIEM, an immutable audit ledger, or a substitute for GoreeCloud change logs.

## Reporting

Do not publish exploit details or secret material in public issues. Use the private security-reporting path configured for the repository when available.

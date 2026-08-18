# Security Policy

## Wardveil Security identity

GoreeCloud Monitor presents its security and protection posture under **Wardveil Security by GoreeCloud**. The approved protection phrase is **Protected by Wardveil**.

Wardveil is the platform-wide security identity and presentation layer. It does not replace Django authentication and authorization, Caddy, NetBird, firewall rules, secrets management, vulnerability management, backup/recovery controls, or other technical authorities. See `docs/wardveil-security.md` for the Monitor-specific implementation boundary.

## Scope

GoreeCloud Monitor is security-sensitive because it authenticates administrators, stores operational history, accepts heartbeat tokens, makes outbound network requests, publishes minimized transition alerts, exposes a read-only platform summary API, and now has first-party Linux/Android client packaging that renders the private Monitor web service.

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
- Core CI and rollback jobs check out the exact pull-request head with persisted GitHub credentials disabled and verify the checked-out SHA before producing source/recovery evidence.

## Native client boundary

The Linux and Android clients are deliberately thin Tauri 2 shells. Django/PostgreSQL remains the only Monitor application, authentication, authorization, monitoring, incident, and configuration authority.

- The client permits navigation only to the canonical HTTPS origin `https://monitor.goreecloud.com` on the default HTTPS port and to `about:blank` for webview initialization.
- HTTP, alternate ports, URL userinfo, lookalike hosts, unrelated origins, and new webview windows are denied.
- Remote Monitor content receives no global Tauri API and no native command/IPC capability.
- Denied-navigation Wardveil diagnostics contain only the event type, URL scheme, and hostname; paths, query strings, fragments, cookies, and credentials are excluded.
- The packaged local fallback contains only local Glaze UI assets and has a restrictive content policy with scripts and network connections disabled.
- The client does not introduce a local monitoring database, synchronization engine, native API token, separate authentication stack, or committed signing credential.
- Launcher artwork for Linux and Android is generated from the same source-controlled canonical Monitor SVG used by the web product.
- The native build workflow checks out the exact PR head with persisted credentials disabled and emits source revision, artifact checksums, and canonical-icon provenance.
- Unsigned/debug Android artifacts are acceptance builds only. Stable Android release signing must use separately protected signing material and complete real-device acceptance; signing secrets must never be committed.
- The native Rust dependency graph must be frozen and reviewed before Stable client classification; direct version pins alone do not replace a reviewed lockfile/release dependency record.

Any future GoreeCloud Identity/SSO redirect origin must be added only after the Identity integration contract, CSRF/session behavior, callback path, navigation policy, and recovery behavior are explicitly reviewed and tested. Do not broaden the client allowlist preemptively.

## SSRF policy

Monitoring private GoreeCloud services is legitimate, so private-address access cannot be globally disabled. Instead, operators explicitly grant the narrow private CIDRs required by the monitor worker. Do not use broad RFC1918 allowlists when a smaller Docker, NetBird, or service subnet is sufficient.

The current design validates the addresses returned during Monitor's preflight resolution before the application-layer connection is opened. A later DNS resolution by the HTTP/TCP/TLS client remains a documented time-of-check/time-of-use boundary. Do not monitor attacker-controlled DNS names or broaden private allowlists to work around this limitation. A future connection-pinning design must preserve TLS hostname verification, redirect validation, DNS behavior, portability, and existing tests before it can replace this boundary.

## Security-event logging

The `monitoring.wardveil` logger records minimized security events. `WARDVEIL_LOG_LEVEL` controls its level and defaults to `INFO`.

Permitted fields are event type, outcome, authenticated numeric user ID and staff flag when applicable, object type, and object ID. Reusable credentials, usernames from failed login attempts, tokens, targets, client IP addresses, request data, and diagnostic content are outside the event schema.

These events support operational review. They are not an authentication database, a SIEM, an immutable audit ledger, or a substitute for GoreeCloud change logs.

## Reporting

Do not publish exploit details or secret material in public issues. Use the private security-reporting path configured for the repository when available.

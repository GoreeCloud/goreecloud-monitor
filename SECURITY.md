# Security Policy

## Scope

GoreeCloud Monitor is security-sensitive because it authenticates administrators, stores operational history, accepts heartbeat tokens, and makes outbound network requests.

## Core controls

- Administrative UI requires Django authentication; monitor creation and mutation require staff status.
- Manager integration is read-only and uses a separate bearer credential.
- Monitor URL userinfo/embedded credentials are rejected.
- HTTP clients ignore ambient proxy and `.netrc` credentials (`trust_env=False`).
- Private, reserved, loopback, and link-local destinations are blocked unless explicitly listed in `MONITOR_ALLOWED_NETWORKS`.
- Every address returned by the preflight resolution must pass the destination policy. This narrows SSRF exposure; administrators should still avoid untrusted DNS zones because application-layer clients can perform a later resolution.
- Worker concurrency and request timeouts are bounded.
- Notifications exclude target URLs, response bodies, credentials, and reusable secrets.
- Production secrets belong in protected environment/secrets storage, never the repository.

## SSRF policy

Monitoring private GoreeCloud services is legitimate, so private-address access cannot be globally disabled. Instead, operators explicitly grant the narrow private CIDRs required by the monitor worker. Do not use broad RFC1918 allowlists when a smaller Docker, NetBird, or service subnet is sufficient.

## Reporting

Do not publish exploit details or secret material in public issues. Use the private security-reporting path configured for the repository when available.

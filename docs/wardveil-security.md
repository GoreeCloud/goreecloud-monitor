# Wardveil Security in GoreeCloud Monitor

## Status and authority

GoreeCloud Monitor implements **Wardveil Security by GoreeCloud** as the platform-wide security and protection identity defined by the GoreeCloud Wardveil Security standard.

Wardveil is the security identity and presentation layer. It does **not** replace the technical source of truth for authentication, authorization, network access, reverse proxying, firewall policy, secrets, backups, vulnerability management, or recovery. Those responsibilities remain with Monitor's implementation and the applicable GoreeCloud policies, standards, and infrastructure components.

The approved user-facing protection phrase is **Protected by Wardveil**.

Monitor does not introduce reserved Wardveil subsystem names as independent products or modules. It also does not define a canonical platform-wide Wardveil logo inside this repository; product-local security glyphs are interface affordances only.

## Glaze UI relationship

Wardveil surfaces in Monitor are built with Glaze UI 1.0.0. Wardveil does not create a competing visual system.

The security posture page, authentication treatment, protected settings, compact navigation, administration presentation, status pills, controls, adaptive layouts, contrast behavior, forced-colors behavior, reduced-transparency fallback, typography, spacing, radii, and motion all consume the existing Glaze UI semantic system.

## Implemented source controls

The current source candidate includes the following Wardveil-aligned protections:

- authenticated application access with staff authorization for monitor mutation, maintenance mutation, protected settings, heartbeat-credential access, and security posture;
- production Secure and HttpOnly session cookies, SameSite boundaries, host-only production cookie names, same-origin referrer and opener policy, clickjacking denial, HTTPS redirect, and HSTS target requirements;
- application Content Security Policy, Permissions Policy, same-origin resource policy, no-index/no-archive response policy, and no-store caching for dynamic operational responses;
- source-local Glaze UI assets with no remote UI, icon, font, analytics, or tracking requirement;
- minimized health responses that reveal only readiness success/failure;
- generic unauthenticated heartbeat acknowledgements and rejection of HEAD as a state-mutating heartbeat method;
- staff-only rendering of heartbeat credentials, raw check diagnostics, and incident failure reasons;
- minimized notification bodies that do not forward raw exceptions, targets, response bodies, query strings, or credentials;
- a constant-time bearer-token comparison for the read-only GoreeCloud Manager API and an explicit bearer challenge on unauthorized responses;
- structured Wardveil security-event logging for authentication activity, monitor configuration mutation, maintenance-window mutation, and heartbeat-credential rotation;
- security-event minimization that excludes usernames on failed login, target URLs, client IP addresses, reusable credentials, tokens, request bodies, and diagnostic payloads;
- fail-closed target preflight checks for transport, cookie, browser-policy, database, host, secret-key, allowlist, and integration-configuration requirements;
- existing SSRF-aware target validation, bounded concurrency/timeouts/body inspection, dependency auditing, hardened non-root containers, fixed HIGH/CRITICAL image vulnerability scanning, PostgreSQL recovery proof, and immediate-predecessor rollback compatibility.

## Security-event log boundary

Wardveil events are written through the `monitoring.wardveil` logger. The default event level is `INFO` and can be adjusted with `WARDVEIL_LOG_LEVEL`.

The event format is intentionally minimized. Events may contain:

- event type;
- outcome;
- authenticated numeric user ID and staff flag when applicable;
- affected object type;
- affected object ID.

Events must not contain reusable secrets, heartbeat tokens, API tokens, passwords, target URLs, response bodies, raw diagnostics, client IP addresses, or copied request data.

This runtime event stream is an operational security record, not a replacement for Django authentication state, database records, Git history, GoreeCloud change logs, or infrastructure logs.

## Target-preflight relationship

The security posture UI is informational. Production readiness is enforced separately by `python manage.py targetpreflight` and CI.

A target acceptance run fails closed when required controls such as PostgreSQL, approved hosts, protected secret key, HTTPS redirect, one-year HSTS, Secure/HttpOnly/SameSite cookie boundaries, clickjacking denial, same-origin opener policy, Content Security Policy, Permissions Policy, or private-network allowlist validation are not satisfied.

The posture page therefore cannot authorize deployment by itself.

## Known security boundaries and remaining acceptance

The current source work does not prove production security by itself. Before Stable classification and cutover, Monitor still requires the target-environment and migration acceptance defined elsewhere, including:

- isolated application activation on the intended target;
- target-native PostgreSQL backup and restore proof;
- repeated live comparison against Uptime Kuma;
- controlled DOWN/RECOVERED, TLS, maintenance, and notification tests;
- Ping/ICMP and resolver-specific DNS decisions;
- verification of the actual Caddy, DNS, NetBird, firewall, and source-identity path;
- manual Glaze UI, keyboard, zoom, screen-reader, light/dark, and adaptive-layout acceptance;
- live rollback proof and explicit cutover approval.

The existing SSRF protection validates all addresses returned during application preflight, but an application-layer client may perform a later DNS resolution. Operators must continue to use trusted DNS zones and narrow target allowlists until a stronger connection-pinning design is validated without weakening TLS, redirects, DNS semantics, or portability.

## Branding/legal boundary

The internal GoreeCloud naming decision for Wardveil Security is approved. External name-conflict or trademark clearance remains a separate governance activity and does not change the technical controls documented here.

## Production boundary

This document describes source behavior only. It does not authorize deployment, publish a Monitor hostname, change Caddy, DNS, NetBird, firewall rules, Uptime Kuma, production credentials, or monitoring-source identity. Uptime Kuma remains authoritative until the documented Monitor cutover gates are completed.

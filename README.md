# GoreeCloud Monitor

GoreeCloud Monitor is the native GoreeCloud service-availability, endpoint-health, heartbeat, TLS-certificate, incident, and recovery-monitoring application.

> **Current state:** advanced pre-production acceptance candidate. Uptime Kuma and ntfy were permanently retired from `goreecloud-vps-01` on September 18, 2026, but predecessor retirement does not automatically promote GoreeCloud Monitor to production authority. The native monitoring foundation, hardened production topology, PostgreSQL recovery tooling, imported paused monitor definitions, DNS and low-privilege Ping/ICMP support, migration/recovery evidence tooling, and GoreeCloud Notify producer candidate are implemented at source level. Production activation remains blocked on current target-host verification, reviewed monitor activation, live check acceptance, current Stable Glaze UI 1.5.1 adoption, platform-system acceptance, target security/recovery evidence, end-to-end GoreeCloud Notify delivery including durable-outbox restart/replay acceptance, independent outage alerting, rollback, and explicit production approval.

## What v0.1 includes

- Authenticated operational shell with System, Light, and Dark appearance; current Stable Glaze UI 1.5.1 adoption remains required
- Wardveil Security by GoreeCloud protection identity with a staff-only, secret-free security-posture surface
- Unique canonical GoreeCloud Monitor application icon with a complete local web/favicon family and shared Linux/AppImage and Android launcher identity inputs
- Responsive Overview, Monitors, Incidents, Maintenance, Notifications, Security, Settings, authentication, and monitor-detail surfaces
- Search/filter workflows for monitor coverage and incident history
- HTTP and HTTPS checks with status, body, JSON, redirect, latency, and TLS validation
- TCP reachability checks
- Native IPv4/IPv6 Ping/ICMP Echo checks using policy-validated unprivileged datagram ping sockets rather than raw-socket capabilities
- DNS A, AAAA, and CNAME checks with optional destination-policy-validated explicit resolvers
- Push/heartbeat monitors with minimized unauthenticated acknowledgements and staff-only credential rendering
- Unknown, Up, Down, Degraded, Paused, and Maintenance state handling
- Failure and recovery thresholds with incident and recovery history
- Authenticated least-privilege GoreeCloud Notify transition publishing candidate with raw-diagnostic minimization and a PostgreSQL-backed durable outbox
- Notification-integration posture that keeps GoreeCloud Notify activation fail-closed until its producer contract and target acceptance are approved
- Read-only Manager summary API with bearer authentication
- SSRF-aware target validation with explicit private-network allowlists
- Production browser/session hardening with CSP, Permissions Policy, same-origin resource/opener/referrer boundaries, no-index/no-store behavior, Secure/HttpOnly/SameSite cookies, HTTPS redirect, and HSTS target requirements
- Minimized Wardveil security-event logging for authentication activity and privileged Monitor configuration actions
- PostgreSQL production support and SQLite local/test support
- Docker/Compose development topology and a separate hardened production deployment candidate
- Maintenance windows, configurable check-history retention, and heartbeat-token rotation
- Minimized health endpoints, CI, tests, backup/recovery documentation
- Preserved Uptime Kuma/kuma-cli audit, paused-import, definition-comparison, and historical/recovery comparison tooling
- Sanitized reconciliation tooling for preserved Uptime Kuma configuration evidence
- Minimized Uptime Kuma runtime-evidence collection retained for authorized isolated recovery/testing
- Fail-closed historical/comparison assessment with coverage-drift detection
- Fail-closed production target preflight including Wardveil-aligned transport, cookie, and browser-policy gates
- Production Compose contract validation with zero host-published application/database ports and a worker-only narrow ping-socket group policy
- Migration-aware immediate-predecessor PostgreSQL application rollback proof for the Ping model-state migration
- Recovery and activation evidence requirements that preserve predecessor evidence without restoring Uptime Kuma to production

## Glaze UI 1.5.1

GoreeCloud Monitor must adopt the current official Stable Glaze UI **1.5.1** contract from the canonical GoreeCloud Glaze UI repository. Earlier Monitor Glaze UI 1.0 validation remains historical migration evidence only and does not establish current conformance or production eligibility.

Current production acceptance requires fresh repository-local 1.5.1 mapping plus representative rendered/browser, responsive, accessibility, resilience, semantic-state, material/depth, motion, layout/density, interaction-state, performance, rollback, and target-environment evidence. Until those gates are accepted, Monitor remains production-blocked on the current design-system requirement.


## Product identity

`assets/identity/goreecloud-monitor-icon.svg` is the authoritative GoreeCloud Monitor application icon. It uses a product-specific availability pulse and protected healthy-state indicator rather than the GoreeCloud platform logo or a generic letter mark.

The web product consumes the same identity through local 16, 32, 48, 192, and 512 pixel SVG representations, a dedicated mask-safe installation icon, and `static/monitoring/site.webmanifest`. The sign-in experience, primary Glaze shell, and staff Django administration all reference the canonical Monitor identity.

`packaging/appimage/` and `packaging/android/` contain source-controlled launcher identity inputs for future approved Linux/AppImage and Android clients. They are **not claims that standalone AppImage or APK clients have been implemented**; the current Monitor architecture remains Django web/API plus the monitoring worker. Any future approved client must consume these assets or deterministic derivatives so web, Linux, and Android cannot silently diverge.

See `docs/product-identity.md`.

## Wardveil Security

**Wardveil Security by GoreeCloud** is Monitor's platform security and protection identity. The approved user-facing phrase is **Protected by Wardveil**.

Wardveil does not replace the technical source of truth. Django authentication/authorization, Monitor target validation, Caddy, NetBird, firewall policy, protected environment files, vulnerability scanning, PostgreSQL recovery, and rollback evidence remain the enforcing controls for their respective roles.

The source candidate adds a staff-only security-posture view, production response/session hardening, minimized health and notification output, staff-only credential/diagnostic presentation, structured secret-free security events, and fail-closed preflight checks for the security controls expected on the target.

See `docs/wardveil-security.md` and `SECURITY.md`.

## Quick start

```bash
python3.13 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

In another terminal, run the monitoring worker:

```bash
. .venv/bin/activate
python manage.py runmonitor
```

Visit `http://127.0.0.1:8000/` and sign in.

## Docker development

```bash
cp .env.example .env
docker compose up --build
```

The development topology deliberately publishes only the loopback web port. PostgreSQL remains internal to the Compose network. Database migrations run through the one-shot `migrate` service before web and worker startup.

## Production candidate

`compose.production.yml` is the source-controlled production deployment candidate. It requires traceable image identity, digest-pinned PostgreSQL, protected purpose-specific environment files, persistent database bind storage, an internal database network, the approved external Caddy network, read-only application root filesystems, dropped Linux capabilities, `no-new-privileges`, and zero host-published Monitor/database ports.

The worker remains non-root with all Linux capabilities dropped. Native Ping uses Linux unprivileged ICMP datagram sockets, with `net.ipv4.ping_group_range` restricted to the deterministic Monitor group inside the worker network namespace only; web and migration containers do not receive that permission.

It is not authorization to deploy or cut over. See `docs/production-deployment.md` and `docs/icmp-ping.md` for the target-environment acceptance boundary.

## DNS resolver semantics

Plain DNS monitor targets such as `example.com` use the Monitor worker's configured system resolver. When the resolver itself is part of the requirement, Monitor supports the portable resolver-qualified form `dns://resolver[:port]/query-name`.

Before an explicit resolver is queried, all of its resolved addresses must satisfy the same `MONITOR_ALLOW_PUBLIC_TARGETS` and `MONITOR_ALLOWED_NETWORKS` destination policy used by other active network targets. The Uptime Kuma migration layer preserves supported `dns_resolve_server` configuration by converting it to this form instead of silently substituting Monitor's system resolver.

This closes the source implementation gap for resolver-specific DNS semantics. Preserved resolver-specific requirements still require live Monitor execution and target-environment validation before production acceptance. See `docs/dns-resolver-semantics.md`.

## Ping / ICMP semantics

Ping is a first-class `PING` monitor. The worker resolves the configured hostname or IP through the same destination-policy boundary used by the other active network checks and passes only approved numeric addresses to the ICMP transport. The transport sends IPv4 or IPv6 Echo requests through unprivileged datagram ping sockets and validates the Echo Reply type, code, sequence, and payload.

Monitor deliberately does not add `CAP_NET_RAW`, privileged mode, host networking, the Docker socket, or a permanent probe sidecar to provide Ping. `python manage.py checkicmpruntime` exercises the same Ping path and is used by the disposable production-topology validation. Uptime Kuma `ping` definitions can now map to paused native `PING` definitions.

This closes the source implementation blocker, not the live acceptance gate. The preserved VPS Ping requirement still requires target-host execution from the approved Monitor worker identity and acceptance evidence before production approval. See `docs/icmp-ping.md`.

## Live acceptance evidence

Collect current Monitor target evidence only from an exact reviewed checkout and the approved administrative path. Any preserved Uptime Kuma evidence is historical/recovery material and may be used only for authorized reconstruction, requirement reconciliation, or isolated comparison testing.

Current acceptance must be based on the actual Monitor target: reviewed definitions, worker execution, target responses, incidents, notification delivery, PostgreSQL recovery, private publication, runtime security, and explicit production approval.

The legacy collection and comparison utilities remain documented for evidence continuity, but they do not require or authorize restoration of Uptime Kuma to production.

See `docs/live-acceptance-evidence.md`, `docs/uptime-kuma-runtime-evidence.md`, and `docs/notify-runtime.md`.


## Retired Uptime Kuma evidence and Monitor activation

Uptime Kuma was permanently retired from the VPS on September 18, 2026 after a verified recovery-gated retirement workflow. Its former production state is now historical/recovery evidence, not a live authority or ordinary rollback service.

The repository's Uptime Kuma import, reconciliation, runtime-evidence, and comparison tooling remains useful for controlled reconstruction, historical parity review, and isolated recovery testing when authorized. It must not be interpreted as permission to restore Uptime Kuma to production.

Monitor activation must instead reconcile the preserved monitor definitions against the services that are actually active now, enable only reviewed current definitions, validate representative HTTP/HTTPS, TCP, TLS, DNS, heartbeat, Ping/ICMP, maintenance, incident, and notification behavior on the live target, and complete recovery plus explicit production acceptance.

See `docs/uptime-kuma-migration.md`, `docs/uptime-kuma-baseline.md`, `docs/dns-resolver-semantics.md`, `docs/icmp-ping.md`, `docs/cutover-and-rollback.md`, and `docs/notify-runtime.md` for the preserved migration and replacement evidence boundary.


## Security model

Monitor makes outbound requests by design. Public targets are permitted when `MONITOR_ALLOW_PUBLIC_TARGETS=true`. Private, loopback, reserved, and link-local targets are denied unless their destination IP is contained in `MONITOR_ALLOWED_NETWORKS`. Add only the exact GoreeCloud Docker, NetBird, or infrastructure CIDRs that Monitor requires.

Credentials and reusable secrets do not belong in this repository. Production environment files are protected infrastructure configuration and are excluded from source control. Sanitized live-evidence bundles are still Internal operational artifacts rather than public source artifacts.

The current SSRF design validates all addresses returned during application preflight, but the HTTP/TCP/TLS client may perform a later DNS resolution. Do not use attacker-controlled DNS zones or broaden private allowlists to compensate for this documented boundary.

## Architecture

The repository contains one Django web/API application and one asynchronous monitoring worker. PostgreSQL is the intended production database. Redis, Celery, Kafka, and other brokers are intentionally excluded from v0.1.

See `docs/architecture.md`, `docs/deployment.md`, `docs/production-deployment.md`, `docs/glaze-ui-conformance.md`, `docs/product-identity.md`, `docs/wardveil-security.md`, `docs/live-acceptance-evidence.md`, `docs/uptime-kuma-runtime-evidence.md`, `docs/uptime-kuma-migration.md`, `docs/uptime-kuma-baseline.md`, `docs/dns-resolver-semantics.md`, `docs/icmp-ping.md`, `docs/icmp-reachability.md`, `docs/cutover-and-rollback.md`, `docs/backup.md`, `docs/recovery.md`, and `SECURITY.md`.

## License

Current GoreeCloud Monitor source is licensed under **GNU Affero General Public License v3.0 only (AGPL-3.0-only)**. Previously distributed copies that were released under the MIT License retain the permissions already granted to those copies. See `LICENSE` and `LICENSE-NOTICE.md`.
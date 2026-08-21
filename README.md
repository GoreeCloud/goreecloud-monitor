# GoreeCloud Monitor

GoreeCloud Monitor is the native GoreeCloud service-availability, endpoint-health, heartbeat, TLS-certificate, incident, and recovery-monitoring application.

> **Current state:** advanced pre-production acceptance candidate. The native monitoring foundation, Uptime Kuma migration/reconciliation tooling, hardened production Compose topology, verified live Uptime Kuma configuration and runtime evidence, target-host/recovery-point preflight, isolated PostgreSQL initialization, rollback compatibility, repeated parallel-comparison acceptance tooling, canonical Glaze UI 1.0.0 product experience, Wardveil Security source-hardening layer, canonical cross-platform product-identity assets, and resolver-specific DNS source parity are implemented. Uptime Kuma remains the production monitoring authority until Monitor completes isolated parallel activation, target-native database restore proof, controlled transition/notification tests, ICMP/Ping resolution, live resolver-specific DNS validation, live rollback, manual Glaze/accessibility acceptance, target Wardveil/security validation, and explicit cutover approval.

## What v0.1 includes

- Authenticated Glaze UI 1.0 operational shell with System, Light, and Dark appearance
- Wardveil Security by GoreeCloud protection identity with a staff-only, secret-free security-posture surface
- Unique canonical GoreeCloud Monitor application icon with a complete local web/favicon family and shared Linux/AppImage and Android launcher identity inputs
- Responsive Overview, Monitors, Incidents, Maintenance, Notifications, Security, Settings, authentication, and monitor-detail surfaces
- Search/filter workflows for monitor coverage and incident history
- HTTP and HTTPS checks with status, body, JSON, redirect, latency, and TLS validation
- TCP reachability checks
- DNS A, AAAA, and CNAME checks with optional destination-policy-validated explicit resolvers
- Push/heartbeat monitors with minimized unauthenticated acknowledgements and staff-only credential rendering
- Unknown, Up, Down, Degraded, Paused, and Maintenance state handling
- Failure and recovery thresholds with incident and recovery history
- Authenticated least-privilege ntfy transition publishing with raw-diagnostic minimization
- Notification-integration posture that keeps GoreeCloud Notify migration explicitly gated until its producer contract is approved
- Read-only Manager summary API with bearer authentication
- SSRF-aware target validation with explicit private-network allowlists
- Production browser/session hardening with CSP, Permissions Policy, same-origin resource/opener/referrer boundaries, no-index/no-store behavior, Secure/HttpOnly/SameSite cookies, HTTPS redirect, and HSTS target requirements
- Minimized Wardveil security-event logging for authentication activity and privileged Monitor configuration actions
- PostgreSQL production support and SQLite local/test support
- Docker/Compose development topology and a separate hardened production deployment candidate
- Maintenance windows, configurable check-history retention, and heartbeat-token rotation
- Minimized health endpoints, CI, tests, backup/recovery documentation
- Conservative Uptime Kuma/kuma-cli audit, paused-by-default import, definition comparison, and live state/latency comparison tooling
- Sanitized documented-baseline reconciliation against live Uptime Kuma configuration evidence
- Minimized read-only live Uptime Kuma runtime evidence collection
- Repeated fail-closed parallel-comparison assessment with coverage-drift detection
- Fail-closed production target preflight including Wardveil-aligned transport, cookie, and browser-policy gates
- Production Compose contract validation with zero host-published application/database ports
- Immediate-predecessor PostgreSQL application rollback-compatibility proof when the migration set is unchanged
- Cutover and rollback evidence requirements that preserve Uptime Kuma until explicit retirement approval

## Glaze UI 1.0

Monitor targets Glaze UI **1.0.0** from the canonical `GoreeCloud/glaze-ui` design system. The current source maps Monitor to the shared semantic token vocabulary, Canvas/Solid/Raised/Glaze/Overlay hierarchy, 44-pixel interactive target minimum, 90/160/220/320ms motion vocabulary, Compact/Medium/Expanded/Wide adaptive ranges, light/dark/system appearance architecture, and accessibility/resilience fallbacks.

The interface uses only local source assets and system/local font fallbacks; it has no remote UI, font, icon, analytics, or tracking dependency. Appearance preference is browser-local and fails soft if client storage is unavailable.

Wardveil Security surfaces consume Glaze UI rather than defining a competing visual system. See `docs/glaze-ui-conformance.md` for the source contract and the manual acceptance gate that remains required before Stable classification.

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

It is not authorization to deploy or cut over. See `docs/production-deployment.md` for the target-environment acceptance boundary.

## DNS resolver semantics

Plain DNS monitor targets such as `example.com` use the Monitor worker's configured system resolver. When the resolver itself is part of the requirement, Monitor supports the portable resolver-qualified form `dns://resolver[:port]/query-name`.

Before an explicit resolver is queried, all of its resolved addresses must satisfy the same `MONITOR_ALLOW_PUBLIC_TARGETS` and `MONITOR_ALLOWED_NETWORKS` destination policy used by other active network targets. The Uptime Kuma migration layer preserves supported `dns_resolve_server` configuration by converting it to this form instead of silently substituting Monitor's system resolver.

This closes the source implementation gap for resolver-specific DNS semantics. The current live Uptime Kuma resolver-specific checks still require isolated-target execution and comparison before production acceptance. See `docs/dns-resolver-semantics.md`.

## Live acceptance evidence

Collect configuration evidence only through the approved administrative path from an exact reviewed checkout:

```bash
python3 scripts/collect_live_acceptance_evidence.py
```

Collect minimized Uptime Kuma runtime state separately when a comparison observation is required:

```bash
python3 scripts/collect_uptime_kuma_runtime_evidence.py
```

Both collectors preserve a strict evidence boundary. Sanitized evidence remains Internal and must not be committed or published. Runtime comparison becomes meaningful only against a reviewed isolated Monitor target.

Repeated parity observations can be aggregated with:

```bash
python manage.py assessparallel /path/to/observation-*.json --require-ready
```

A ready repeated series proves only the state/latency comparison contract for those observations. It does not replace controlled outage/recovery, TLS, maintenance, notification, DNS, Ping/ICMP, restore, rollback, Wardveil target validation, or cutover evidence.

See `docs/live-acceptance-evidence.md` and `docs/uptime-kuma-runtime-evidence.md`.

## Uptime Kuma migration and cutover

A fresh live Uptime Kuma configuration snapshot—not the written inventory alone—is the migration authority for an acceptance session. Reconcile a sanitized configuration copy with:

```bash
python manage.py reconcileuptimebaseline \
  /path/to/uptime-kuma-config.sanitized.json \
  --json \
  --no-fail
```

The command fails closed on missing expected coverage, reappeared retired monitors, unexpected live monitors, unsupported migration semantics, unresolved review items, and documented cutover blockers. ICMP/Ping network-layer coverage remains a source/cutover blocker. Resolver-specific DNS source semantics are now implemented, but their live target behavior remains an acceptance gate until the approved resolver checks are exercised and compared in parallel.

Do not use the configuration snapshot with `compareuptimestate`. Parallel state/latency comparison requires separately validated sanitized runtime evidence with heartbeat status and response-time values.

See `docs/uptime-kuma-migration.md`, `docs/uptime-kuma-baseline.md`, `docs/dns-resolver-semantics.md`, `docs/icmp-reachability.md`, and `docs/cutover-and-rollback.md`.

## Security model

Monitor makes outbound requests by design. Public targets are permitted when `MONITOR_ALLOW_PUBLIC_TARGETS=true`. Private, loopback, reserved, and link-local targets are denied unless their destination IP is contained in `MONITOR_ALLOWED_NETWORKS`. Add only the exact GoreeCloud Docker, NetBird, or infrastructure CIDRs that Monitor requires.

Credentials and reusable secrets do not belong in this repository. Production environment files are protected infrastructure configuration and are excluded from source control. Sanitized live-evidence bundles are still Internal operational artifacts rather than public source artifacts.

The current SSRF design validates all addresses returned during application preflight, but the HTTP/TCP/TLS client may perform a later DNS resolution. Do not use attacker-controlled DNS zones or broaden private allowlists to compensate for this documented boundary.

## Architecture

The repository contains one Django web/API application and one asynchronous monitoring worker. PostgreSQL is the intended production database. Redis, Celery, Kafka, and other brokers are intentionally excluded from v0.1.

See `docs/architecture.md`, `docs/deployment.md`, `docs/production-deployment.md`, `docs/glaze-ui-conformance.md`, `docs/product-identity.md`, `docs/wardveil-security.md`, `docs/live-acceptance-evidence.md`, `docs/uptime-kuma-runtime-evidence.md`, `docs/uptime-kuma-migration.md`, `docs/uptime-kuma-baseline.md`, `docs/dns-resolver-semantics.md`, `docs/icmp-reachability.md`, `docs/cutover-and-rollback.md`, `docs/backup.md`, `docs/recovery.md`, and `SECURITY.md`.

## License

MIT. See `LICENSE`.

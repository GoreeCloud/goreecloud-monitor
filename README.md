# GoreeCloud Monitor

GoreeCloud Monitor is the native GoreeCloud service-availability, endpoint-health, heartbeat, TLS-certificate, incident, and recovery-monitoring application.

> **Current state:** advanced pre-production acceptance candidate. Source validation now includes the native monitoring foundation, Uptime Kuma migration/runtime-evidence and repeated-parity tooling, hardened production Compose topology, PostgreSQL recovery/rollback checks, canonical Glaze UI 1.0, Wardveil Security hardening, verifier-only push credentials, privacy-preserving structured request observability, Glaze/Wardveil error experiences, and a canonical cross-platform application-identity contract. Uptime Kuma remains the production monitoring authority until Monitor completes the outstanding live target, recovery, controlled-scenario, client-delivery, manual UI/accessibility, rollback, and explicit cutover gates.

## Product capabilities

- Authenticated Glaze UI 1.0 operational shell with System, Light, and Dark appearance.
- Wardveil Security by GoreeCloud protection identity with a staff-only, secret-free security-posture surface.
- One canonical GoreeCloud Monitor pulse/status mark used by the web shell, login, administration, browser favicon, and local web-app manifest.
- Machine-readable cross-platform app-identity contract that prevents future AppImage/Android packaging from silently introducing unrelated launcher artwork.
- Responsive Overview, Monitors, Incidents, Maintenance, Notifications, Security, Settings, authentication, monitor-detail, credential-issuance, and safe error experiences.
- HTTP/HTTPS checks with status, body, JSON, redirect, latency, and TLS validation.
- TCP reachability and DNS A/AAAA/CNAME checks.
- Push/heartbeat monitors using HTTPS POST plus Bearer credentials; new/rotated raw credentials are displayed once and only a SHA-256 verifier is persisted.
- Unknown, Up, Down, Degraded, Paused, and Maintenance state handling with failure/recovery thresholds and incident history.
- Authenticated least-privilege ntfy transition publishing with raw-diagnostic minimization.
- GoreeCloud Notify integration remains deliberately gated until its production producer contract is approved.
- Read-only GoreeCloud Manager summary API with separate bearer authentication.
- SSRF-aware target validation with explicit private-network allowlists and a documented DNS re-resolution boundary.
- Production browser/session hardening with CSP, Permissions Policy, same-origin resource/opener/referrer boundaries, no-index/no-store behavior, Secure/HttpOnly/SameSite cookies, HTTPS redirect, and HSTS target requirements.
- Minimized Wardveil security events plus structured operational request events with server-generated request IDs and no raw paths, query strings, client IPs, user agents, bodies, cookies, target URLs, or credentials.
- PostgreSQL production support and SQLite local/test support.
- Hardened Docker/Compose production candidate with no host-published application/database ports.
- Maintenance windows, bounded monitor/maintenance list rendering, configurable history retention, minimized health endpoints, backup/recovery documentation, CI, and rollback checks.
- Conservative Uptime Kuma/kuma-cli audit, paused-by-default import, baseline reconciliation, runtime evidence, definition comparison, and repeated live state/latency comparison tooling.

## Glaze UI 1.0

Monitor targets Glaze UI **1.0.0** from the canonical `GoreeCloud/glaze-ui` design system. The interface uses the shared semantic token vocabulary, Canvas/Solid/Raised/Glaze/Overlay hierarchy, 44-pixel interactive target minimum, canonical motion vocabulary, Compact/Medium/Expanded/Wide adaptive ranges, system/light/dark appearance architecture, and accessibility/resilience fallbacks.

All user-facing application surfaces remain Glaze consumers, including Wardveil posture and security-related experiences. The application uses only local source assets and system/local font fallbacks; it has no remote UI, font, icon, analytics, or tracking dependency. See `docs/glaze-ui-conformance.md`.

## Wardveil Security

**Wardveil Security by GoreeCloud** is Monitor's platform security and protection identity. The approved user-facing phrase is **Protected by Wardveil**.

Wardveil does not replace the technical authorities underneath it. Django authentication/authorization, Monitor destination validation, Caddy, NetBird, firewall policy, protected environment files, PostgreSQL, vulnerability scanning, recovery tooling, and rollback evidence remain the enforcing controls for their respective roles.

Push heartbeat credentials no longer need to appear in normal request URLs. The primary endpoint is `POST /api/v1/heartbeat/` with an `Authorization: Bearer <credential>` header. New and rotated credentials are non-recoverable after their one-time issuance page. Legacy path-token compatibility is disabled by default and production preflight fails closed if it is enabled or if any legacy plaintext push credential remains in the database.

See `docs/wardveil-security.md` and `SECURITY.md`.

## Application identity

The canonical Monitor artwork is `static/monitoring/img/monitor-mark.svg`. This hardening layer did not redraw or generate new artwork; it made that product-specific pulse/status mark the authoritative source and pinned its exact digest in `packaging/app-identity.json`.

The current repository implements the web identity surface. It **does not currently contain a Linux AppImage client/package or an Android APK/AAB client/package**. Those surfaces are explicitly recorded as blocked rather than mocked. When either client is implemented, its launcher/package assets must derive from the same canonical mark and the identity contract must be updated and validated.

Validate the current identity contract with:

```bash
python scripts/validate_app_identity.py
```

Once both client package implementations exist, the cross-client release gate is:

```bash
python scripts/validate_app_identity.py --require-client-packages
```

See `docs/app-identity.md`.

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

In another terminal:

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

Before target acceptance, run the fail-closed preflight in the accepted target environment. It verifies PostgreSQL, migration state, host/cookie/HTTPS/browser policy, network allowlists, notification configuration, disabled legacy path heartbeat behavior, and verifier-only push credential storage.

Source validation is not deployment authorization. See `docs/production-deployment.md` and `docs/final-production-hardening.md`.

## Live acceptance evidence

Collect configuration evidence only through the approved administrative path from an exact reviewed checkout:

```bash
python3 scripts/collect_live_acceptance_evidence.py
```

Collect minimized Uptime Kuma runtime state separately when a comparison observation is required:

```bash
python3 scripts/collect_uptime_kuma_runtime_evidence.py
```

Aggregate repeated state/latency parity observations with:

```bash
python manage.py assessparallel /path/to/observation-*.json --require-ready
```

A ready repeated series proves only the comparison contract for those observations. It does not replace controlled outage/recovery, TLS, maintenance, notification, DNS, Ping/ICMP, restore, rollback, target Wardveil, manual Glaze/accessibility, or cutover evidence.

## Uptime Kuma migration and cutover

A fresh live Uptime Kuma configuration snapshot—not the written inventory alone—is the migration authority for an acceptance session. Reconcile a sanitized copy with:

```bash
python manage.py reconcileuptimebaseline \
  /path/to/uptime-kuma-config.sanitized.json \
  --json \
  --no-fail
```

The command fails closed on missing expected coverage, reappeared retired monitors, unexpected live monitors, unsupported migration semantics, unresolved review items, and documented cutover blockers. ICMP/Ping network-layer coverage and resolver-specific DNS semantics remain explicit blockers/review gates.

See `docs/uptime-kuma-migration.md`, `docs/uptime-kuma-baseline.md`, `docs/icmp-reachability.md`, and `docs/cutover-and-rollback.md`.

## Security and observability model

Monitor makes outbound requests by design. Public targets are permitted when `MONITOR_ALLOW_PUBLIC_TARGETS=true`. Private, loopback, reserved, and link-local targets are denied unless their destination IP is contained in `MONITOR_ALLOWED_NETWORKS`. Add only the exact GoreeCloud Docker, NetBird, or infrastructure CIDRs required by approved monitors.

Credentials and reusable secrets do not belong in this repository or ordinary logs. Production environment files are protected infrastructure configuration. Sanitized live-evidence bundles remain Internal operational artifacts rather than public source artifacts.

The `monitoring.wardveil` logger records minimized security events. The `monitoring.access` logger records JSON request-completion/error events using generated request IDs and resolved route names instead of raw URLs. Django's default raw-path request/server application loggers are suppressed. Reverse-proxy/system log policy remains a separate infrastructure responsibility.

The current SSRF design validates all addresses returned during application preflight, but the HTTP/TCP/TLS client may perform a later DNS resolution. Do not use attacker-controlled DNS zones or broaden private allowlists to compensate for this documented boundary.

## Architecture and documentation

The repository contains one Django web/API application and one asynchronous monitoring worker. PostgreSQL is the intended production database. Redis, Celery, Kafka, and other brokers are intentionally excluded from v0.1.

Primary references:

- `docs/architecture.md`
- `docs/production-deployment.md`
- `docs/final-production-hardening.md`
- `docs/app-identity.md`
- `docs/glaze-ui-conformance.md`
- `docs/wardveil-security.md`
- `docs/live-acceptance-evidence.md`
- `docs/uptime-kuma-runtime-evidence.md`
- `docs/uptime-kuma-migration.md`
- `docs/cutover-and-rollback.md`
- `docs/backup.md`
- `docs/recovery.md`
- `SECURITY.md`

## License

MIT. See `LICENSE`.

# GoreeCloud Monitor

GoreeCloud Monitor is the native GoreeCloud service-availability, endpoint-health, heartbeat, TLS-certificate, incident, and recovery-monitoring application.

> **Current state:** source-stable live-acceptance evidence compatibility candidate. The source foundation, Uptime Kuma migration tooling, hardened production Compose topology, disposable production-stack validation, documented-baseline reconciliation, recovery proof, immediate-predecessor rollback compatibility, and sanitized read-only live target/configuration evidence tooling are implemented. The live GoreeCloud kuma-cli v2 interface is now handled explicitly rather than assuming older command shapes. Runtime heartbeat/state collection remains a separate acceptance gate. Uptime Kuma remains the production monitoring platform until GoreeCloud Monitor completes live configuration review, publication, parallel runtime acceptance, the ICMP/Ping and resolver-specific DNS decisions, target recovery/notification testing, and an explicit cutover.

## What v0.1 includes

- Authenticated Glaze UI dashboard and monitor management
- HTTP and HTTPS checks with status, body, JSON, redirect, latency, and TLS validation
- TCP reachability checks
- DNS A, AAAA, and CNAME checks
- Push/heartbeat monitors
- Unknown, Up, Down, Degraded, Paused, and Maintenance state handling
- Failure and recovery thresholds with incident history
- Authenticated least-privilege ntfy transition publishing
- Read-only Manager summary API
- SSRF-aware target validation with explicit private-network allowlists
- PostgreSQL production support and SQLite local/test support
- Docker/Compose development topology and a separate hardened production deployment candidate
- Maintenance windows, configurable check-history retention, and heartbeat-token rotation
- Health endpoints, CI, tests, backup/recovery documentation
- Conservative Uptime Kuma/kuma-cli audit, paused-by-default import, definition comparison, and live state/latency comparison tooling
- Sanitized documented-baseline reconciliation against a fresh live Uptime Kuma configuration snapshot
- Read-only live target/Uptime Kuma configuration evidence collection with kuma-cli v2 ID-keyed monitor-map support and fail-closed sanitization
- Fail-closed production target preflight
- Production Compose contract validation with zero host-published application/database ports
- Immediate-predecessor PostgreSQL application rollback-compatibility proof when the migration set is unchanged
- Cutover and rollback evidence requirements that preserve Uptime Kuma until explicit retirement approval

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

It is not authorization to deploy. See `docs/production-deployment.md` for the target-environment acceptance boundary.

## Live acceptance evidence

Before deploying Monitor, collect the first live target/Uptime Kuma configuration evidence through the approved administrative path from an exact reviewed checkout:

```bash
python3 scripts/collect_live_acceptance_evidence.py
```

The collector is read-only with respect to the live service environment. It does not invoke `sudo`, modify Uptime Kuma, modify Docker networks, copy Caddy/Compose contents, change DNS/NetBird/firewall state, or write unsanitized `kuma monitor list` output to disk. It uses an authenticated kuma-cli v2 session, validates the ID-keyed monitor map, and sanitizes the configuration immediately. The sanitized evidence bundle remains Internal and must not be committed or published.

`ready_for_review` means the target-environment and configuration evidence is complete enough for review. It does **not** mean runtime heartbeat/state evidence is available. Runtime comparison remains a separate later acceptance gate because kuma-cli v2 monitor-list output is configuration-only.

See `docs/live-acceptance-evidence.md` for the exact boundary and review procedure.

## Uptime Kuma migration and cutover

A fresh live Uptime Kuma configuration snapshot—not the written inventory alone—is the migration authority for an acceptance session. After live evidence is collected, reconcile the sanitized configuration copy with:

```bash
python manage.py reconcileuptimebaseline \
  /path/to/uptime-kuma-config.sanitized.json \
  --json \
  --no-fail
```

The command fails closed on missing expected coverage, reappeared retired monitors, unexpected live monitors, unsupported migration semantics, unresolved review items, and documented cutover blockers. The current documented blockers/reviews include ICMP/Ping network-layer coverage and resolver-specific DNS semantics.

Do not use the configuration snapshot with `compareuptimestate`. Parallel state/latency comparison requires a separately validated sanitized runtime snapshot with heartbeat status and ping values.

See `docs/live-acceptance-evidence.md`, `docs/uptime-kuma-migration.md`, `docs/uptime-kuma-baseline.md`, `docs/icmp-reachability.md`, and `docs/cutover-and-rollback.md`.

## Security model

Monitor makes outbound requests by design. Public targets are permitted when `MONITOR_ALLOW_PUBLIC_TARGETS=true`. Private, loopback, reserved, and link-local targets are denied unless their destination IP is contained in `MONITOR_ALLOWED_NETWORKS`. Add only the exact GoreeCloud Docker, NetBird, or infrastructure CIDRs that Monitor requires.

Credentials and reusable secrets do not belong in this repository. Production environment files are protected infrastructure configuration and are excluded from source control. Sanitized live-evidence bundles are still Internal operational artifacts rather than public source artifacts.

## Architecture

The repository contains one Django web/API application and one asynchronous monitoring worker. PostgreSQL is the intended production database. Redis, Celery, Kafka, and other brokers are intentionally excluded from v0.1.

See `docs/architecture.md`, `docs/deployment.md`, `docs/production-deployment.md`, `docs/live-acceptance-evidence.md`, `docs/uptime-kuma-migration.md`, `docs/uptime-kuma-baseline.md`, `docs/icmp-reachability.md`, `docs/cutover-and-rollback.md`, `docs/backup.md`, `docs/recovery.md`, and `SECURITY.md`.

## License

MIT. See `LICENSE`.

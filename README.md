# GoreeCloud Monitor

GoreeCloud Monitor is the native GoreeCloud service-availability, endpoint-health, heartbeat, TLS-certificate, incident, and recovery-monitoring application.

> **Current state:** source-stable cutover-readiness candidate. The source foundation, Uptime Kuma migration tooling, hardened production Compose topology, disposable production-stack validation, documented-baseline reconciliation, recovery proof, and immediate-predecessor rollback compatibility are implemented and validated in CI. Uptime Kuma remains the production monitoring platform until GoreeCloud Monitor completes live target-environment publication, live-export reconciliation, parallel acceptance, the ICMP/Ping and resolver-specific DNS decisions, target recovery/notification testing, and an explicit cutover.

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
- Sanitized documented-baseline reconciliation against a fresh live Uptime Kuma export
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

## Uptime Kuma migration and cutover

A fresh live Uptime Kuma export—not the written inventory alone—is the migration authority for an acceptance session. The documented baseline is reconciled with:

```bash
python manage.py reconcileuptimebaseline uptime-kuma-export.json
```

The command fails closed on missing expected coverage, reappeared retired monitors, unexpected live monitors, unsupported migration semantics, unresolved review items, and documented cutover blockers. The current documented blockers/reviews include ICMP/Ping network-layer coverage and resolver-specific DNS semantics.

See `docs/uptime-kuma-migration.md`, `docs/uptime-kuma-baseline.md`, `docs/icmp-reachability.md`, and `docs/cutover-and-rollback.md`.

## Security model

Monitor makes outbound requests by design. Public targets are permitted when `MONITOR_ALLOW_PUBLIC_TARGETS=true`. Private, loopback, reserved, and link-local targets are denied unless their destination IP is contained in `MONITOR_ALLOWED_NETWORKS`. Add only the exact GoreeCloud Docker, NetBird, or infrastructure CIDRs that Monitor requires.

Credentials and reusable secrets do not belong in this repository. Production environment files are protected infrastructure configuration and are excluded from source control.

## Architecture

The repository contains one Django web/API application and one asynchronous monitoring worker. PostgreSQL is the intended production database. Redis, Celery, Kafka, and other brokers are intentionally excluded from v0.1.

See `docs/architecture.md`, `docs/deployment.md`, `docs/production-deployment.md`, `docs/uptime-kuma-migration.md`, `docs/uptime-kuma-baseline.md`, `docs/icmp-reachability.md`, `docs/cutover-and-rollback.md`, `docs/backup.md`, `docs/recovery.md`, and `SECURITY.md`.

## License

MIT. See `LICENSE`.

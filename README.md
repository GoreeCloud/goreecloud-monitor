# GoreeCloud Monitor

GoreeCloud Monitor is the native GoreeCloud service-availability, endpoint-health, heartbeat, TLS-certificate, incident, and recovery-monitoring application.

> **Current state:** stable development foundation. Uptime Kuma remains the production monitoring platform until GoreeCloud Monitor completes parallel validation, backup/restore testing, and an explicit cutover.

## What v0.1 includes

- Authenticated Glaze UI dashboard and monitor management
- HTTP and HTTPS checks with status, body, JSON, redirect, latency, and TLS validation
- TCP reachability checks
- DNS A, AAAA, and CNAME checks
- Push/heartbeat monitors
- Unknown, Up, Down, Degraded, Paused, and Maintenance state handling
- Failure and recovery thresholds with incident history
- ntfy-compatible transition notifications
- Read-only Manager summary API
- SSRF-aware target validation with explicit private-network allowlists
- PostgreSQL production support and SQLite local/test support
- Docker/Compose deployment definition
- Maintenance windows, configurable check-history retention, and heartbeat-token rotation
- Health endpoints, CI, tests, backup/recovery documentation

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

The Compose topology deliberately publishes only the web development port. The PostgreSQL service is internal to the Compose network.

## Security model

Monitor makes outbound requests by design. Public targets are permitted when `MONITOR_ALLOW_PUBLIC_TARGETS=true`. Private, loopback, reserved, and link-local targets are denied unless their destination IP is contained in `MONITOR_ALLOWED_NETWORKS`. Add only the exact GoreeCloud Docker, NetBird, or infrastructure CIDRs that Monitor requires.

Credentials and reusable secrets do not belong in this repository. Production `.env` files are excluded from Git.

## Architecture

The repository contains one Django web/API application and one asynchronous monitoring worker. PostgreSQL is the intended production database. Redis, Celery, Kafka, and other brokers are intentionally excluded from v0.1.

See `docs/architecture.md`, `docs/deployment.md`, `docs/backup.md`, `docs/recovery.md`, and `SECURITY.md`.

## License

MIT. See `LICENSE`.

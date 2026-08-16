# Deployment

Production deployment is not approved merely because the source builds successfully. Target-environment acceptance must validate the Infrastructure Services VM, private DNS, Caddy HTTPS, NetBird access, firewall policy, persistent storage, backups, restoration, and parallel Uptime Kuma behavior.

## Required environment

- `DJANGO_DEBUG=false`
- strong protected `DJANGO_SECRET_KEY`
- approved `DJANGO_ALLOWED_HOSTS`
- `DJANGO_SECURE_SSL_REDIRECT=true` behind Caddy
- HSTS only after HTTPS behavior is verified
- `DATABASE_ENGINE=postgres`
- protected PostgreSQL password
- explicit `MONITOR_ALLOWED_NETWORKS` for the exact private networks the worker may reach
- when ntfy publishing is enabled, `NTFY_BASE_URL`, `NTFY_TOPIC`, and protected `NTFY_TOKEN` for Monitor's dedicated write-only publisher identity

The Compose development port binds to `127.0.0.1:8000` and uses ordinary local bridge networks so the stack is self-contained. Production publication should remove the host-port mapping and attach the web service only to the approved external Caddy network after target-environment validation.

## Target preflight

After the target environment has its protected configuration and database, run:

```bash
python manage.py targetpreflight
```

For machine-readable evidence:

```bash
python manage.py targetpreflight --json
```

The preflight is deliberately fail-closed. It blocks target acceptance when it detects development/debug mode, a non-PostgreSQL database, empty or wildcard host policy, a weak/development secret key, insecure HTTPS/cookie settings, an all-addresses target allowlist, partial ntfy credentials, database connectivity failure, or unapplied migrations.

It reports HSTS, Manager integration, ntfy-disabled state, and an empty monitor database as warnings where those conditions can legitimately exist during an isolated initial deployment. A green preflight does **not** prove DNS, Caddy, NetBird, firewall, Docker network membership, host-port exposure, backup storage, restore behavior, notification ACLs, or parallel monitoring; those require separate target-environment evidence.

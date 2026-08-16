# Deployment

Production deployment is not approved merely because the source builds successfully. Target-environment acceptance must validate the Infrastructure Services VM, private DNS, Caddy HTTPS, NetBird access, firewall policy, persistent storage, backups, restoration, and parallel Uptime Kuma behavior.

## Required environment

- `DJANGO_DEBUG=false`
- strong `DJANGO_SECRET_KEY`
- approved `DJANGO_ALLOWED_HOSTS`
- `DJANGO_SECURE_SSL_REDIRECT=true` behind Caddy
- HSTS only after HTTPS behavior is verified
- `DATABASE_ENGINE=postgres`
- protected PostgreSQL password
- explicit `MONITOR_ALLOWED_NETWORKS` for the exact private networks the worker may reach

The Compose development port binds to `127.0.0.1:8000` and uses ordinary local bridge networks so the stack is self-contained. Production publication should remove the host-port mapping and attach the web service only to the approved external Caddy network after target-environment validation.

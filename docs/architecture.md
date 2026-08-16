# Architecture

GoreeCloud Monitor intentionally separates its web/API process from the check worker while keeping both in one repository and release.

```text
Caddy / private HTTPS
        |
        v
Django web + Glaze UI + read-only Manager API
        |
        +------------------+
        |                  |
        v                  v
   PostgreSQL        Monitor worker
                         |
              HTTP/HTTPS/TCP/DNS/PUSH
                         |
                         v
                 approved targets
```

## Boundaries

- **Monitor:** service availability, endpoint checks, certificates, heartbeat state, incidents and recovery.
- **Beszel:** host and container resource telemetry.
- **Healthchecks:** scheduled-job and backup heartbeats.
- **Notify / ntfy:** notification delivery.
- **Manager:** read-only operational aggregation.

The worker uses bounded concurrency. Redis, Celery, Kafka, and a distributed scheduler are intentionally absent from v0.1.

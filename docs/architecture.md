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

- **Monitor:** service availability, endpoint checks, certificates, heartbeat state, incidents and recovery. The product scope now also includes first-party scheduled-job/dead-man monitoring for cron jobs, backups, maintenance jobs, and other periodic tasks. Full Healthchecks-style scheduled-job capability is planned and is not yet a current-source feature beyond generic push/heartbeat monitoring.
- **General resource telemetry:** host, container, metrics, logs, and tracing remain outside Monitor's specialized availability/job-monitoring role unless a separately approved integration requires summarized state.
- **Healthchecks:** permanently retired from the GoreeCloud VPS on September 19, 2026. It is a benchmark/migration reference only, not an active runtime dependency or authority.
- **GoreeCloud Notify:** notification delivery and fan-out. Monitor owns detection, incident state, routing intent, reminders, and report generation but does not replicate Notify's delivery responsibility.
- **Manager:** read-only operational aggregation.

The worker uses bounded concurrency. Redis, Celery, Kafka, and a distributed scheduler are intentionally absent from v0.1. Scheduled-job support should reuse the existing Monitor worker/state/incident architecture where practical rather than introducing a second monitoring application or permanent Healthchecks-compatible subsystem.

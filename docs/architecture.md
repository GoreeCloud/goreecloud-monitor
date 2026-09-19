# Architecture

GoreeCloud Monitor intentionally separates its web/API process from the check worker while keeping both in one repository and release.

```text
Caddy / private HTTPS
        |
        v
Django web + Glaze UI + read-only Manager APIs
        |
        +------------------+
        |                  |
        v                  v
   PostgreSQL        Monitor worker
                         |
              HTTP/HTTPS/TCP/DNS/PUSH/JOB
                         |
                         v
                 approved targets
```

The Manager boundary is read-only. `/api/v1/summary/` exposes aggregate operational status; `/api/v1/jobs/` and `/api/v1/jobs/<id>/` expose bounded scheduled-job operational summaries and sanitized recent signal metadata. Manager receives no reusable credentials, credential verifiers, run IDs, event IDs, operator messages, raw targets, or mutation endpoints.

## Boundaries

- **Monitor:** service availability, endpoint checks, certificates, heartbeat state, scheduled-job/dead-man monitoring, incidents and recovery. The current source includes first-class JOB monitors, simple interval + grace and cron/time-zone evaluation, authenticated lifecycle signals, run-duration correlation, runtime-overrun detection, and missed-run incident evaluation. Full Healthchecks-style parity remains incomplete.
- **General resource telemetry:** host, container, metrics, logs, and tracing remain outside Monitor's specialized availability/job-monitoring role unless a separately approved integration requires summarized state.
- **Healthchecks:** permanently retired from the GoreeCloud VPS on September 19, 2026. It is a benchmark/migration reference only, not an active runtime dependency or authority.
- **GoreeCloud Notify:** notification delivery and fan-out. Monitor owns detection, incident state, routing intent, reminders, and report generation but does not replicate Notify's delivery responsibility.
- **Manager:** read-only operational aggregation.

The worker uses bounded concurrency. Redis, Celery, Kafka, and a distributed scheduler are intentionally absent from v0.1. Scheduled-job evaluation reuses the existing Monitor worker/state/incident architecture, while job runners submit bounded lifecycle signals through the authenticated web/API process. This avoids a second monitoring application or permanent Healthchecks-compatible subsystem.

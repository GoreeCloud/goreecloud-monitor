# GoreeCloud Monitor — Current Features Overview

**Document Internal Version Number:** 2026.09.22.1  
**Document External Version Number:** 1.2.0  
**Status:** Supporting current-source feature overview  
**As of:** September 22, 2026

## Purpose and authority

This file provides a concise overview of functionality present in current GoreeCloud Monitor source.

The authoritative repository-native implemented-feature inventory is [`IMPLEMENTED-FEATURES.md`](IMPLEMENTED-FEATURES.md). Open, partial, planned, proposed, blocked, and acceptance-gated obligations are authoritative in [`PLANNED-FEATURES.md`](PLANNED-FEATURES.md). Meaningful change history is authoritative in [`CHANGELOGS.md`](CHANGELOGS.md).

A feature listed here is not automatically production-accepted. Source implementation, CI, migration evidence, predecessor retirement, or documentation alone does not establish production authority or Stable status.

## Implemented monitoring features

- HTTP/HTTPS availability checks.
- Expected status/content/JSON and redirect validation.
- TCP reachability checks.
- TLS certificate validation and expiry handling.
- DNS monitoring with resolver-specific source support.
- Native low-privilege IPv4/IPv6 Ping/ICMP checks.
- Push/heartbeat monitoring.
- First-class Scheduled Job / Dead-Man monitors for periodic jobs and backup/maintenance heartbeats.
- Simple interval + grace, strict cron + IANA time-zone, and native systemd OnCalendar job scheduling.
- Authenticated scheduled-job start, success, failure/exit-status, and bounded log/event signals using one-way-stored rotatable bearer credentials.
- Per-monitor scheduled-job signal rate limiting with HTTP 429/Retry-After responses.
- Optional UUID event IDs for durable idempotent signal replay; mismatched reuse is rejected with conflict semantics.
- Job run correlation, duration capture, maximum-runtime overrun detection, missed-schedule detection, and job-event history.
- Derived scheduled-job lifecycle presentation with Awaiting, Started, Completed, Failed, and Late phases while preserving the existing Monitor state/incident model.
- Automatic bounded CheckResult and scheduled-job event-history pruning with current JOB evaluation state preserved.
- Staff-only scheduled-job recovery snapshots and versioned paginated JSON exports of retained job-event evidence, with credentials excluded.
- Bearer-authenticated read-only Manager JOB list/detail endpoints with lifecycle, schedule, incident, and bounded sanitized signal metadata; no job credential, run ID, event ID, message, or mutation surface is exposed.
- Configurable check intervals and failure/recovery thresholds.
- Monitor pause/enable state.
- Maintenance windows.
- Incident creation, update, and recovery history.
- Search/filter operational views.

## Implemented administration and UI features

- Django-authenticated administrative interface.
- Overview, Monitors, Incidents, Maintenance, Notifications, Security, Settings, login, and monitor-detail surfaces.
- Staff-gated privileged mutations and protected views.
- System/Light/Dark appearance.
- Responsive web presentation.
- Glaze UI 1.5.1 source-adoption/alignment candidate on current `main`.
- Reduced Motion, Reduced Transparency, contrast, Forced Colors, large-text, and form-factor source handling.
- Wardveil Security presentation and minimized security-posture surface.

## Implemented notification-delivery features

- GoreeCloud Notify-only producer candidate.
- Minimized transition payloads for DOWN, RECOVERED, DEGRADED, and TLS-expiry scenarios.
- Versioned idempotency-key contract.
- PostgreSQL-backed durable `NotificationOutbox`.
- Transactional persistence of transition/outbox state before publication.
- Bounded in-request retry.
- Persistent retry/backoff across worker cycles.
- Same-key replay convergence.
- Fail-closed target preflight while undelivered outbox rows remain.
- Bounded retention for already-delivered outbox metadata.

## Implemented data/recovery features

- Django migrations.
- PostgreSQL production topology.
- SQLite local/test mode.
- Database backup tooling.
- Isolated PostgreSQL restore validation in CI.
- Migration-readiness/reconciliation tooling for preserved Uptime Kuma definitions.
- Immediate-predecessor rollback compatibility workflows cover notification-outbox and scheduled-job migrations, including fail-safe downgrade that pauses OnCalendar definitions rather than reinterpreting them.
- Target preflight and hardened production Compose validation.

## Implemented security/privacy controls

- Strong password validation.
- Secure cookies and CSRF controls.
- HSTS/security headers for production configuration.
- Content Security Policy and Permissions Policy.
- Minimized route-name operational logging.
- Bounded response sizes.
- Target network allowlist controls.
- No privileged production container requirement.
- Fixable HIGH/CRITICAL container image vulnerability gate.
- Privacy Shield source adapter candidate.
- Everkeep source acceptance-policy candidate.

## Not yet production-accepted

The following remain acceptance work and are tracked authoritatively in `PLANNED-FEATURES.md`:

- current live VPS/target-host deployment and readback acceptance;
- target PostgreSQL backup/restore;
- reviewed monitor activation;
- final private Gateway/DNS/NetBird publication acceptance;
- representative live protocol checks, including scheduled-job missed-run/failure/recovery and credential-rotation behavior;
- accepted GoreeCloud Notify runtime credential/delivery;
- durable outbox restart/replay under real target failure;
- independent outage alerting;
- manual current-Stable Glaze UI accessibility/performance/application acceptance;
- remaining platform-system acceptance;
- live rollback/recovery;
- explicit production approval and any later Stable qualification.


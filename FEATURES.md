# GoreeCloud Monitor — Current Features

**Document Internal Version Number:** 2026.09.19.1  
**Document External Version Number:** 1.1.0  
**Status:** Current implemented-source feature record  
**As of:** September 19, 2026

## Purpose

This file records functionality present in the current GoreeCloud Monitor source. Planned or recommended work belongs in `FEATURE-ROADMAP.md`.

A feature listed here is not automatically production-accepted.

## Implemented monitoring features

- HTTP/HTTPS availability checks.
- Expected status/content/JSON and redirect validation.
- TCP reachability checks.
- TLS certificate validation and expiry handling.
- DNS monitoring with resolver-specific source support.
- Native low-privilege IPv4/IPv6 Ping/ICMP checks.
- Push/heartbeat monitoring.
- First-class Scheduled Job / Dead-Man monitors for periodic jobs and backup/maintenance heartbeats.
- Simple interval + grace and strict cron + IANA time-zone job scheduling.
- Authenticated scheduled-job start, success, failure/exit-status, and bounded log/event signals using one-way-stored rotatable bearer credentials.
- Per-monitor scheduled-job signal rate limiting with HTTP 429/Retry-After responses.
- Optional UUID event IDs for durable idempotent signal replay; mismatched reuse is rejected with conflict semantics.
- Job run correlation, duration capture, maximum-runtime overrun detection, missed-schedule detection, and job-event history.
- Automatic bounded CheckResult and scheduled-job event-history pruning with current JOB evaluation state preserved.
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
- Glaze UI 1.5.1 source-adoption candidate.
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
- Immediate-predecessor rollback compatibility workflows cover the notification-outbox, scheduled-job, and job-signal idempotency migrations.
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
- Fixed HIGH/CRITICAL container image vulnerability gate.
- Privacy Shield source adapter candidate.
- Everkeep source acceptance-policy candidate.

## Not yet production-accepted

The following remain acceptance work:

- live VPS deployment/readback;
- target PostgreSQL backup/restore;
- reviewed monitor activation;
- final private Gateway/DNS/NetBird publication;
- representative live protocol checks, including scheduled-job missed-run/failure/recovery and credential-rotation behavior;
- accepted GoreeCloud Notify runtime credential/delivery;
- durable outbox restart/replay under real target failure;
- independent outage alerting;
- manual Glaze UI/accessibility/performance acceptance;
- remaining platform-system acceptance;
- live rollback/recovery;
- explicit production approval.


# GoreeCloud Monitor — Repository Specifications

**Document Internal Version Number:** 2026.09.19.1  
**Document External Version Number:** 1.1.0  
**Status:** Current repository-coupled specification  
**As of:** September 19, 2026  
**Repository:** `GoreeCloud/goreecloud-monitor`  
**Central project record:** `GoreeCloud/Projects/Project Specification — Monitor.docx`

## Purpose

This file records the current source-coupled specifications for GoreeCloud Monitor. It does not replace the central project specification, GoreeCloud governance, release evidence, or target-environment acceptance records.

Where this file and live implementation differ, verified repository/runtime state controls factual current-state claims and this file must be reconciled.

## Product role

GoreeCloud Monitor is the GoreeCloud-native availability, endpoint-health, heartbeat, scheduled-job/dead-man, TLS-certificate, incident, maintenance, and recovery-monitoring application.

Uptime Kuma and ntfy were permanently retired from `goreecloud-vps-01` on September 18, 2026. Their preserved artifacts are historical/recovery evidence only.

Monitor is an advanced pre-production acceptance candidate and is not yet production monitoring authority.

## Version and architecture

- Application version: `0.1.0`.
- Framework: Django 5.2.
- Production database: PostgreSQL.
- Local/test database option: SQLite.
- Production web server: Gunicorn.
- Production topology: separate database, migration, web, and worker services.
- Deployment style: hardened Docker Compose candidate with no host-published application/database ports.
- Private HTTPS ingress: intended through the approved GoreeCloud Gateway network/path.

## Monitoring capabilities

The current source must support representative monitoring for:

- HTTP/HTTPS availability;
- expected HTTP status and content behavior;
- TCP reachability;
- TLS validation and expiry;
- DNS resolution, including reviewed resolver semantics;
- IPv4/IPv6 Ping/ICMP using low-privilege datagram ping sockets;
- push/heartbeat monitoring;
- thresholds and state transitions;
- maintenance windows;
- incident creation, update, recovery, and history.

The current source implements the first scheduled-job/dead-man monitoring foundation. It does **not yet** provide complete Healthchecks-style parity. Current source support includes:

- first-class Scheduled Job / Dead-Man monitor definitions;
- simple period + grace schedules;
- cron expressions with explicit time-zone behavior;
- authenticated start, success, failure/exit-status, and bounded log/event signals;
- rotatable per-check signal credentials stored only as one-way verifiers;
- run IDs/correlation, duration history, execution-overrun detection, missed-completion detection, and event history;
- mapping missed or failed jobs into the existing Monitor Down/incident/Notify transition pipeline.

The following scheduled-job scope remains planned or partial:

- systemd OnCalendar compatibility when justified;
- richer explicit Started/Late presentation beyond the existing Up/Down incident mapping;
- dedicated job-event recovery/export views beyond ordinary database backup/restore;
- tags/labels and collections/projects;
- scoped management API support for job checks;
- controlled optional auto-provisioning;
- private status badges/JSON summaries, repeated-down reminders, and periodic job-health reports;
- separate evaluation of email-based signal ingestion.

Healthchecks is a benchmark reference for this scope, not an upstream application dependency or a source-code base. Monitor must remain an original GoreeCloud implementation.

## Notification contract

GoreeCloud Notify is the only supported Monitor notification publisher candidate after ntfy retirement. Scheduled-job alerts, reminders, and reports must use the same delivery boundary rather than adding a Healthchecks-style notification-provider catalog to Monitor.

The current source must:

- use a dedicated least-privilege Notify producer credential;
- minimize transition payloads;
- persist notification payload/idempotency state before network publication;
- retry due outbox records with bounded backoff;
- retain pending records until delivery/reconciliation;
- keep delivered outbox metadata under bounded retention;
- block target acceptance while undelivered outbox rows remain.

This provides durable at-least-once publication intent with idempotent convergence; it is not an exactly-once claim.

## Authentication and administration

Administrative UI uses Django authentication.

Privileged monitor/maintenance mutation and protected settings/security surfaces require appropriate staff authorization.

Accepted GoreeCloud Identity and GoreeCloud Manager integration remain blocked and must not be inferred from local Django controls.

## Security

Production-relevant controls include:

- strong password validation;
- secure session/CSRF cookies;
- CSRF protection;
- security headers;
- Content Security Policy;
- Permissions Policy;
- private publication;
- no privileged containers;
- no host networking;
- no Docker socket;
- no added Linux capabilities;
- read-only application root filesystems;
- `cap_drop: ALL`;
- `no-new-privileges`;
- bounded response handling;
- minimized logging;
- target vulnerability/security acceptance.

Wardveil Security source adoption does not replace these technical controls.

## Privacy

Monitoring configuration, targets, operational history, incidents, heartbeats, and alert metadata can reveal infrastructure information.

Logs/evidence must avoid reusable credentials and unnecessary raw target diagnostics.

Privacy Shield source adaptation does not establish central/runtime acceptance.

## Continuity and recovery

Production acceptance requires:

- persistent PostgreSQL storage;
- application-consistent logical backup;
- isolated restore against the exact candidate;
- recovery of monitor definitions, incidents, maintenance state, and notification outbox state;
- migration/rollback compatibility evidence;
- known-good application/database rollback procedure.

Uptime Kuma restoration is not the ordinary rollback path.

## Glaze UI

The current required Stable design-system target is Glaze UI **1.5.1**.

The active web shell carries a 1.5.1 source-adoption candidate with presentation-only authority.

Representative browser/OS accessibility, large-text/reflow, responsive task continuity, performance, visual review, rollback, consumer-registry, and production acceptance remain required.

## Integral Platform Systems

Current source evaluates all nine Integral Platform Systems fail-closed:

- GoreeCloud Manager: applicable / blocked.
- Privacy Shield: source adapter candidate / runtime-central acceptance blocked.
- Wardveil Security: source adoption evidence / target-runtime acceptance blocked.
- Everkeep: source acceptance-policy candidate / target restore/recovery acceptance blocked.
- Glaze UI: 1.5.1 source-adoption candidate / application acceptance blocked.
- GoreeCloud Mesh: applicable / blocked.
- GoreeCloud Identity: applicable / blocked.
- GoreeCloud Policy: applicable / blocked.
- GoreeCloud Observability: application-local evidence / shared-system acceptance blocked.

## Production acceptance boundary

Production authority remains blocked until applicable evidence verifies:

- current VPS Docker/network/storage state;
- exact immutable application/database images;
- target PostgreSQL backup and isolated restore;
- reviewed active monitor definitions;
- private Gateway/DNS/NetBird publication;
- representative HTTP/HTTPS, TCP, TLS, DNS, heartbeat, Ping/ICMP, and scheduled-job behavior;
- incident/maintenance/state-transition behavior;
- accepted GoreeCloud Notify deployment and dedicated producer identity;
- durable outbox restart/replay with no duplicate fanout;
- independent outage alerting;
- target Wardveil/Privacy Shield/Everkeep acceptance;
- manual Glaze UI/accessibility/performance acceptance;
- remaining platform-system acceptance;
- rollback/recovery exercise;
- explicit production approval.


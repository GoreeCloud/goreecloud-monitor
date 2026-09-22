# GoreeCloud Monitor — Planned Features

**Record type:** Repository planned/open feature inventory  
**Repository:** `GoreeCloud/monitor`  
**Repository ID:** `1336209445`  
**Lifecycle:** Advanced pre-production acceptance candidate; production activation remains gated  
**Migration state:** Candidate under Standard — Repository Feature Tracking and Changelog Governance v1.0  
**Evidence baseline:** `main` at `f59991c2ac577662ddc6f396027b4dc1d637689a` (PR #51, September 21, 2026)  

## Purpose

This file is the repository-native inventory of GoreeCloud Monitor obligations that remain planned, partial, proposed, blocked, acceptance-gated, or otherwise incomplete. Partially implemented capabilities stay open until the defined implementation and acceptance scope is complete.

The migration reconciles the retired repository `FEATURE-ROADMAP.md`, the Drive `GoreeCloud/Feature Roadmap/GoreeCloud Monitor/FEATURE-ROADMAP.docx`, the authoritative Project Specification — Monitor, current repository feature evidence, and current `main` state.

## Migration reconciliation

The legacy roadmap uses the stale repository name `GoreeCloud/goreecloud-monitor`. Live GitHub repository identity controls current state: `GoreeCloud/monitor`, repository ID `1336209445`.

The former requirement to synchronize repository and Drive roadmap copies is superseded by Standard — Repository Feature Tracking and Changelog Governance v1.0. Google Drive is migration-source-only and must not remain an active, mirrored, convenience, or backup feature-roadmap authority after verified retirement.

Where a legacy roadmap marks source implementation complete but live acceptance remains open, this file preserves the open acceptance obligation instead of promoting the feature to fully complete. Where current repository evidence is newer than September 19 roadmap wording, verified repository state controls factual implementation status.

The Project Specification currently contains historical/stale repository naming and a Glaze UI 1.5.0 requirement, while verified current repository `main` implements the subsequent 1.5.1 adoption/alignment work. That documentation conflict must be reconciled through the governed project-documentation workflow; it does not justify downgrading the verified current source state or inventing production acceptance.

## Open feature and acceptance obligations

| ID | Feature / obligation | Priority | Current disposition |
| --- | --- | --- | --- |
| `FR-001` | Reconcile and maintain current planned/recommended Monitor features against authoritative project requirements and verified repository evidence. | High | **Ongoing governance.** This obligation is now fulfilled through `IMPLEMENTED-FEATURES.md`, `PLANNED-FEATURES.md`, and `CHANGELOGS.md`; the retired roadmap model must not be recreated. |
| `FR-002` | Move actionable feature obligations into GoreeCloud Tasks Management when required, preserving priority, dependencies, blockers, lifecycle state, and verification status. | High | **Ongoing governance.** Existing Monitor/Notify stabilization tasks and centralized GitHub migration/governance tasks remain the applicable task records; avoid duplicates. |
| `FR-003` | Preserve evidence-backed lifecycle disposition; do not mark features implemented, complete, cancelled, superseded, production-approved, or Stable without authoritative evidence. | High | **Ongoing governance.** The legacy repository/Drive synchronization clause is superseded; the evidence-backed lifecycle rule remains controlling. |
| `FR-004` | First-class Scheduled Job / Dead-Man monitors for cron jobs, backup/maintenance heartbeats, and missed-run detection. | High | **Source implemented; live acceptance open.** Current source contains native JOB monitors. Representative target/runtime acceptance remains required. |
| `FR-005` | Simple interval + grace, cron/time-zone, and practical systemd OnCalendar scheduled-job support. | High | **Source implemented; live acceptance open.** Simple, strict cron/IANA time-zone, and native OnCalendar modes are implemented. Target runtime and recovery/rollback acceptance remain open. |
| `FR-006` | Authenticated start/success/failure/log job-signal ingestion with rotatable per-check credentials, rate limiting, and safe replay behavior. | High | **Source implemented; live acceptance open.** Signal contract, credential rotation, per-monitor rate limiting, and durable idempotent replay are implemented. Live credential rotation, delivery behavior, restart/replay, and security acceptance remain open. |
| `FR-007` | Run correlation, duration tracking, overrun detection, Late/Started semantics, and missed-completion incidents. | High | **Source implemented; live acceptance open.** Correlation, duration, overrun/missed completion, and Awaiting/Started/Completed/Failed/Late presentation are present. Representative live scenario acceptance remains open. |
| `FR-008` | Scheduled-job event history, state transitions, duration evidence, retention controls, and recovery views without turning Monitor into a general log platform. | High | **Source implemented; acceptance open.** Bounded history, retention preserving current evaluation state, staff recovery snapshot, and versioned paginated export exist. Target recovery, retention, and production operational acceptance remain open. |
| `FR-009` | Tags/labels and collections/projects for job checks, including search/filter and Identity/Policy-backed authorization where applicable. | Medium | **Planned — not implemented.** |
| `FR-010` | Versioned Manager API scheduled-job summaries and bounded signal metadata under least privilege; any write administration/credential rotation requires separate authorization. | High | **Partial.** Read-only JOB list/detail and sanitized recent signal metadata are implemented. Accepted Manager integration, any required read-side throttling, authorization policy, and separately approved write authority remain open. |
| `FR-011` | Policy-gated automatic provisioning by approved identifiers with auditability, rate limits, and review controls. | Medium | **Planned — not implemented.** |
| `FR-012` | Private badge/JSON summaries, repeated-down reminders, and periodic scheduled-job health reports delivered through GoreeCloud Notify. | Medium | **Planned / partial dependencies.** Core Notify producer/outbox foundations exist; these reporting/reminder surfaces and their production acceptance remain open. |
| `FR-013` | Evaluate email-based start/success/failure signal ingestion with keyword rules only after SMTP, security, and privacy acceptance. | Low | **Proposed — security/privacy review required.** Do not activate by inference. |
| `FR-014` | Preserve GoreeCloud Notify as notification delivery/fan-out authority; Monitor must not duplicate a broad notification-provider catalog. | High | **Architectural requirement; runtime acceptance open.** Notify-only producer/outbox source foundations exist, but accepted production credentials, delivery, failure/restart/replay, and independent outage alerting remain open. |
| `PROD-ACCEPT-01` | Current target-host deployment/readback, reviewed monitor activation, and representative live HTTP/HTTPS/TCP/DNS/Ping/push/scheduled-job behavior. | High / production gate | **Open.** Source/CI evidence does not establish current target production authority. |
| `PROD-ACCEPT-02` | Target PostgreSQL backup/restore, migration/rollback, retained evidence, and clean recovery acceptance. | High / production gate | **Open.** CI/disposable recovery evidence exists; current target recovery acceptance remains required. |
| `PROD-ACCEPT-03` | Final private Gateway/DNS/NetBird publication and target security validation. | High / production gate | **Partial / acceptance open.** Project documentation records private publication evidence, but current production authority still requires complete governed target acceptance. |
| `PROD-ACCEPT-04` | GoreeCloud Notify production credential/delivery plus durable-outbox restart/replay behavior under real target failure. | High / production gate | **Open.** |
| `PROD-ACCEPT-05` | Independent outage alert path for notification-service failure where required. | High / resilience gate | **Open.** Detection and incident recording must not be conflated with independent delivery. |
| `PROD-ACCEPT-06` | Current Stable Glaze UI application acceptance: rendered/browser responsiveness, accessibility, resilience, semantic state, materials/depth, motion, layout/density, interaction states, performance, rollback, and representative acceptance. | High / UI acceptance | **Partial.** Current `main` includes 1.5.1 source adoption/alignment; application-specific acceptance remains open. |
| `PROD-ACCEPT-07` | Remaining platform-system acceptance, including producer-authority boundaries for Privacy Shield, Wardveil Security, Everkeep, Manager, Identity/Policy where applicable, and other governed platform systems. | High / platform gate | **Open / partial.** Source adapters or presentation do not establish producer-system acceptance. |
| `PROD-ACCEPT-08` | Live rollback/recovery, explicit production approval, and any later Stable qualification. | High / final gate | **Open.** Monitor remains an advanced pre-production acceptance candidate. |
| `DOC-RECON-01` | Reconcile stale Project Specification repository name (`GoreeCloud/goreecloud-monitor`) with live GitHub identity (`GoreeCloud/monitor`) and reconcile the historical Glaze UI 1.5.0 wording with verified current 1.5.1 source adoption without inventing acceptance. | Governance | **Open documentation reconciliation.** |

## Product-boundary obligations

GoreeCloud Monitor remains specialized availability/endpoint/heartbeat/scheduled-job/TLS/incident/recovery monitoring. It must not silently absorb general host-resource monitoring, backup scheduling, notification subscription/delivery ownership, or a central administrative control plane.

GoreeCloud Notify remains delivery authority. GoreeCloud Manager may consume only approved read-only operational visibility. Security/privacy/recovery/platform integrations remain governed by their producer systems and acceptance contracts.

## Completion workflow

When an open obligation becomes complete enough to be represented as implemented:

1. reconcile the evidence-backed capability in `IMPLEMENTED-FEATURES.md`;
2. remove it from active planned/open work or preserve a completed disposition when historical traceability requires it; and
3. record the meaningful lifecycle event in `CHANGELOGS.md`.

No pull request, CI run, migration, deployment attempt, predecessor retirement, or documentation statement alone promotes Monitor to production authority or Stable state.

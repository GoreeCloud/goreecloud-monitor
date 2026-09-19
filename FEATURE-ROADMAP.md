# GoreeCloud Monitor — Feature Roadmap

**Status:** Active roadmap control  
**As of:** 2026-09-19  
**Authoritative project record:** Project Specification — Monitor  
**Canonical repository:** GoreeCloud/goreecloud-monitor
**Drive control:** `GoreeCloud/Feature Roadmap/GoreeCloud Monitor/FEATURE-ROADMAP.docx`

## Purpose

This file is the repository-side feature roadmap control for GoreeCloud Monitor. It records current planned and recommended feature work without replacing the authoritative project record, implementation evidence, release gates, or GoreeCloud Tasks Management.

## Roadmap

| ID | Feature / obligation | Priority | Current state |
| --- | --- | --- | --- |
| FR-001 | Reconcile and maintain every current planned or recommended GoreeCloud Monitor feature from the authoritative project record and verified repository evidence in this roadmap. | High | Ongoing control |
| FR-002 | Move actionable feature obligations into GoreeCloud Tasks Management when required, preserving priority, dependency, and lifecycle disposition. | High | Ongoing control |
| FR-003 | Do not mark features implemented, complete, cancelled, or superseded without authoritative evidence and synchronized repository/Drive roadmap updates. | High | Ongoing control |
| FR-004 | Add first-class Scheduled Job / Dead-Man monitors so GoreeCloud Monitor owns cron jobs, backup/maintenance heartbeats, and missed-run detection formerly covered by Healthchecks. | High | Implemented in source; live acceptance pending |
| FR-005 | Add simple period + grace scheduling plus cron/time-zone scheduling; evaluate systemd OnCalendar support for practical parity. | High | Partially implemented — simple/cron/time-zone complete; systemd evaluation pending |
| FR-006 | Add authenticated job-signal ingestion for start, success, failure/exit status, and bounded log/event payloads using rotatable per-check credentials. | High | Implemented in source — signal contract, credential rotation, per-monitor rate limiting, and durable idempotent replay complete; live acceptance pending |
| FR-007 | Add run correlation/duration tracking, execution-overrun detection, Late/Started semantics, and missed-completion incidents. | High | Partially implemented — correlation/duration/overrun/missed completion integrated; richer Started/Late presentation pending |
| FR-008 | Add scheduled-job event history, status flips, run durations, retention controls, and recovery views without becoming a general log platform. | High | Partially implemented — event history, durations, and state-preserving retention complete; dedicated recovery/export views pending |
| FR-009 | Add tags/labels and collections/projects for job checks, with search/filter and GoreeCloud Identity/Policy-backed authorization where applicable. | Medium | Planned — not implemented |
| FR-010 | Extend the versioned management API with scoped read-only/read-write job-check administration, signal metadata access, token rotation, and rate limiting. | High | Planned — not implemented |
| FR-011 | Add policy-gated automatic provisioning by approved slug/name identifiers, with auditability, rate limits, and review controls. | Medium | Planned — not implemented |
| FR-012 | Add private badge/JSON status summaries plus repeated-down reminders and periodic scheduled-job health reports delivered through GoreeCloud Notify. | Medium | Planned — not implemented |
| FR-013 | Evaluate email-based start/success/failure signal ingestion with keyword rules only after SMTP/security/privacy acceptance. | Low | Proposed — security review required |
| FR-014 | Preserve GoreeCloud Notify as the delivery/fan-out authority; do not duplicate Healthchecks' provider integration catalog inside Monitor. | High | Architectural requirement |

## Maintenance and synchronization

This roadmap and the corresponding Drive `FEATURE-ROADMAP.docx` must remain materially synchronized with one another and with the authoritative project or service record. Update both copies whenever feature scope, priority, dependency, implementation status, cancellation, supersession, recommendation, or verification state materially changes.

No feature may be represented as complete or Stable solely because it appears in this roadmap. Completion and lifecycle claims require the applicable authoritative implementation, validation, review, release, and production evidence.

## Reconciliation rule

At each material feature change, reconcile this roadmap against the current authoritative project record, repository implementation state, applicable platform-system requirements, and GoreeCloud Tasks Management. Missing obligations, stale status, duplicated work, roadmap drift, or undocumented disposition changes are defects to correct.

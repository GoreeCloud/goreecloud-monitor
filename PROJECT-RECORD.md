# GoreeCloud Monitor — Project Record

**Repository:** `GoreeCloud/monitor`  
**Former repository identity in the Drive source:** `GoreeCloud/goreecloud-monitor`  
**Lifecycle:** Release Candidate source line / advanced pre-production acceptance candidate; production activation remains unaccepted  
**Migration baseline:** `46897de12f514a43da3a668e3e9c952e63e9dea6`  
**Record purpose:** Significant product history, architecture and governance decisions, predecessor retirement, recovery evidence, major capability milestones, and project-document migration provenance  
**Canonical authority:** This file becomes the repository-local project record once accepted on the default branch.

## Original project direction

GoreeCloud Monitor was approved as an original GoreeCloud-owned availability-monitoring application rather than a permanent Uptime Kuma fork.

The original specification established Monitor as the specialized availability/endpoint-health authority candidate for HTTP/HTTPS, TCP, DNS, TLS certificate, push/heartbeat, incident, recovery, and maintenance behavior, while deliberately excluding unrelated general observability scope.

The project was designed around:
- Django;
- PostgreSQL;
- a separate monitoring worker;
- private-by-default deployment;
- Glaze UI;
- least-privilege Manager integration;
- controlled notification publishing;
- backup/recovery;
- portable monitor definitions; and
- evidence-backed migration from predecessor monitoring.

## Historical predecessor migration

Early Development retained Uptime Kuma as production authority while native Monitor source, migration/import tools, sanitized evidence collection, target-preflight tooling, disposable production topology, backup/restore, rollback, and protocol-parity checks were developed.

The Google Drive project specification preserves detailed exact-revision checkpoints for this period, including migration-readiness, live-evidence, target-preflight, recovery, production-hardening, resolver-specific DNS, and native low-privilege Ping/ICMP work.

Those exact source-era checkpoints remain historical provenance. Current repository `CHANGELOGS.md`, `docs/changelog-history/`, Git history, pull requests, workflow evidence, and accepted `main` are the authoritative detailed chronology.

## August 2026 — Recovery and protocol-parity foundations

During the pre-production migration period the repository gained:
- hardened Django/PostgreSQL deployment;
- application-consistent PostgreSQL backup/restore proof;
- migration-aware rollback compatibility;
- sanitized Uptime Kuma definition/runtime-evidence tooling;
- target-preflight evidence;
- fixed HIGH/CRITICAL container vulnerability gating;
- resolver-specific DNS preservation;
- native IPv4/IPv6 low-privilege Ping/ICMP;
- deterministic non-root runtime identity and worker-only ping-socket permission.

These source/runtime candidates remained non-production evidence until accepted target-state validation.

## September 18, 2026 — Predecessor retirement and recovery checkpoint

Uptime Kuma, Beszel Hub, Beszel Agent, and ntfy were permanently retired from `goreecloud-vps-01` after dependency/recovery cleanup.

The Drive project record identifies Kopia snapshot `189b1dce96e3d222f7ba4ad9678a4d2b` as the recovery reference that passed 100-percent verification and isolated restore acceptance before destructive cleanup.

This retirement is a historical production-environment event. It does **not** by itself establish GoreeCloud Monitor production monitoring authority or current host/resource-monitoring authority.

Preserved predecessor artifacts remain historical/recovery context.

## September 2, 2026 — AGPL-3.0-only relicensing

PR #33, **Relicense GoreeCloud Monitor under AGPL-3.0-only**, merged exact candidate head `37b5ee29fcf01d6346dcfeff971a11b4a8620999` as `4e5509bb7b89009030794a13a80547a858927753`.

The change prospectively relicensed current GoreeCloud-owned Monitor source under `AGPL-3.0-only`, preserved prior MIT grants for copies already distributed under MIT, synchronized package/repository metadata, and documented third-party licensing boundaries.

The change did not alter runtime or production acceptance state.

## September 18, 2026 — Notify-only durable notification architecture

PR #35, **Reconcile Monitor notification runtime after ntfy retirement**, merged exact candidate head `ce25278450d8938903fc72678a62924a1248a4e9` as `5f532668a2dd5dd1fb76ad28deb6d2770141be9a`.

This source integration:
- removed retired ntfy as an active notification runtime;
- made GoreeCloud Notify the only supported publisher candidate;
- added a PostgreSQL-backed durable notification outbox;
- persisted minimized payload/idempotency state before network publication;
- preserved pending records across restart/retry;
- bounded retention of delivered metadata;
- kept pending records fail-closed;
- reconciled rollback compatibility to the current schema;
- closed fixed container vulnerability findings rather than suppressing them.

Production Notify delivery, restart/replay, target deployment, independent outage alerting, and production authority remained separately gated.

## September 19, 2026 — Native scheduled-job/dead-man monitoring

PR #38, **Implement scheduled job and dead-man monitoring foundation**, merged exact head `c09b8a9d2283091787faac447cc5fc173c3c1e59` as `7009ef61d41283c7d84b1c4ac25931ce870bed2c`.

It established first-class JOB monitors, simple interval/grace and cron scheduling, authenticated start/success/failure/log signals, one-way credential verifiers, event history, run correlation, duration/overrun behavior, missed-run detection, staff UI, and reuse of the existing incident/Notify transition pipeline.

Follow-up accepted PRs added:
- signal rate limiting and durable replay/idempotency;
- bounded event retention;
- recovery/export;
- lifecycle phases;
- systemd OnCalendar schedules;
- read-only Manager scheduled-job visibility.

Healthchecks remains a benchmark/reference rather than a runtime dependency or product authority.

## September 2026 — Private production-topology hardening

Subsequent source integrations hardened the intended private production topology, including:
- private DNS requirements;
- deterministic worker/backend/proxy identity;
- private Caddy route behavior;
- isolation of Notify producer credentials to the worker;
- no host-published application/database ports;
- non-root/read-only containers;
- dropped capabilities and no-new-privileges;
- worker-only low-privilege Ping permission;
- target-preflight and rollback evidence.

These changes remain production-candidate source controls, not proof of live target activation.

## September 22, 2026 — Git-native feature and changelog governance

PR #52, **Migrate Monitor feature tracking and changelog governance**, merged exact head `df5ca14db4411c94d4ee3403cd92870b9c41754d` as `41d88d2a12ad705f7c30160b378738031fbed37d`.

It established:
- `IMPLEMENTED-FEATURES.md`;
- `PLANNED-FEATURES.md`;
- `CHANGELOGS.md`;
- preservation of the former root changelog under `docs/changelog-history/`;
- a digest of the former Drive changelog;
- retirement of root `FEATURE-ROADMAP.md`;
- retirement of the legacy singular root `CHANGELOG.md`.

The migration explicitly identified the Drive project specification's stale repository name and older Glaze authority as a separate documentation reconciliation obligation.

PR #53, **Finalize Monitor repository record authority after migration**, merged as `b7bf959e04ddd06f3a30db2f81bc7cb6ab4c53b4`, reconciled the repository records after accepted-main readback and preserved the separate project-specification conflict for later correction.

## September 24, 2026 — Glaze UI 1.6.0 source adoption

PR #55, **Stabilize Monitor on Glaze UI 1.6.0**, merged exact candidate head `3860fea03063746fbabe64bf95b39bf76de51039` as current migration baseline `46897de12f514a43da3a668e3e9c952e63e9dea6`.

It:
- advanced the active presentation mapping from Glaze UI 1.5.1 to the current Official Stable 1.6.0 baseline;
- pinned immutable Glaze release/source/artifact provenance;
- updated the shell and repository-local presentation mapping;
- updated `goreecloud.platform.yaml`;
- corrected machine-readable repository identity to `GoreeCloud/monitor`;
- retained fail-closed nonconformance and downstream acceptance gates.

The shared Glaze release being Stable does not automatically establish Monitor application acceptance.

## Current accepted source state

At migration baseline `46897de12f514a43da3a668e3e9c952e63e9dea6`, current accepted source includes:
- native HTTP/HTTPS/TCP/DNS/TLS/Push/Ping monitoring foundations;
- native scheduled-job/dead-man monitoring;
- incidents, maintenance, state/history;
- hardened security/privacy controls;
- PostgreSQL production candidate and recovery tooling;
- durable Notify outbox candidate;
- read-only Manager APIs;
- private production-topology controls;
- Uptime Kuma historical/recovery tooling;
- source-level Wardveil, Privacy Shield, Everkeep, and Glaze UI integration evidence;
- Platform Contract 0.4 evaluation.

Monitor remains production-blocked.

## Current production-acceptance boundary

Outstanding target/runtime evidence includes:
- live VPS Docker/network/storage readback;
- exact deployed application/database image identity;
- target PostgreSQL backup and isolated restore;
- reviewed monitor/job definition activation;
- private Gateway/DNS/NetBird publication;
- representative HTTP/HTTPS/TCP/TLS/DNS/heartbeat/Ping/job behavior;
- incident/maintenance/state-transition acceptance;
- accepted GoreeCloud Notify deployment and dedicated producer identity;
- durable outbox restart/replay without duplicate fanout;
- independent Monitor-down alerting;
- target Wardveil/Privacy Shield/Everkeep acceptance;
- representative Glaze UI/accessibility/performance/Human Visual Excellence review;
- remaining Integral Platform System acceptance;
- rollback/recovery exercise;
- explicit production activation approval.

Predecessor retirement, source implementation, disposable topology tests, and green CI do not substitute for these target gates.

## Repository protection gap

As of this migration baseline, GitHub reports `main` as unprotected with no active rulesets. GitHub issue #56 tracks branch-protection and required-check remediation.

The connected GitHub application does not expose branch-protection/ruleset mutation, so this record must not claim that protection is enforced.

## September 25, 2026 — Project specifications/project record migration candidate

**Migration pull request:** PR #57 — `docs/project-governance-migration-20260925` → `main`  

This migration:
- creates root `PROJECT-SPECIFICATIONS.md`;
- creates root `PROJECT-RECORD.md`;
- reconciles the complete active Drive **Project Specification — Monitor.docx** with current accepted repository state;
- corrects the historical repository identity from `GoreeCloud/goreecloud-monitor` to live `GoreeCloud/monitor`;
- reconciles the design-system requirement to accepted current Glaze UI 1.6.0 source authority;
- preserves normative requirements while moving significant historical material into this project record and leaving detailed chronology in `CHANGELOGS.md` / `docs/changelog-history/`;
- updates README authority/navigation; and
- retires root `SPECIFICATIONS.md` on the migration branch only after its still-relevant content is incorporated.

**Drive source:** Project Specification — Monitor.docx  
**Drive file ID:** `1DUWERKb3Ca2o8USnjvJFQfv40JIM9QDr`  
**Drive deletion status:** **Blocked.** The source must remain until this migration is independently reviewed where required, accepted on `main`, read back from the authoritative default branch, verified complete, and free of unresolved reconciliation discrepancies.

The older Drive source **Project Specification — Monitor** (file ID `10APWqDZEbXSSYF65A0rnjgWeJlZE9Jg5RQYZrMtoNAU`) is archived migration/history input only and must not override the active source or current repository state.

## Ongoing maintenance

Update this record for significant architecture decisions, repository identity changes, licensing, major protocol/capability additions, target deployment/activation, security/privacy changes, recovery events, major incidents, platform integration, lifecycle transitions, predecessor retirement, or eventual Monitor retirement.

Routine feature/change chronology remains in `CHANGELOGS.md`; current feature inventory remains in `IMPLEMENTED-FEATURES.md` and `PLANNED-FEATURES.md`.

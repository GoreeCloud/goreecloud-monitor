# GoreeCloud Monitor — Repository Notes

**Document Internal Version Number:** 2026.09.18.1  
**Document External Version Number:** 1.0.0  
**Status:** Current repository-maintenance notes  
**As of:** September 18, 2026

## Current source state

- Uptime Kuma and ntfy were retired from `goreecloud-vps-01` on September 18, 2026.
- Notify-only transition publishing is integrated.
- PostgreSQL-backed durable notification outbox is integrated.
- Delivered outbox metadata has bounded retention; pending rows are not retention-pruned.
- Glaze UI 1.5.1 is the active source target.
- All nine Integral Platform Systems are explicitly evaluated.
- Container security scanning is configured to fail on fixed HIGH/CRITICAL findings.
- The repository remains pre-production and is not production monitoring authority.

## Current production blockers

- live VPS Docker/network/storage readback;
- exact target image verification;
- target PostgreSQL backup and isolated restore;
- reviewed monitor-definition activation;
- final private Gateway/DNS/NetBird publication;
- representative live HTTP/HTTPS, TCP, TLS, DNS, heartbeat, and Ping/ICMP checks;
- accepted GoreeCloud Notify producer credential and end-to-end delivery;
- durable outbox restart/replay under target failure;
- independent outage alerting;
- target Wardveil/Privacy Shield/Everkeep acceptance;
- manual Glaze UI/accessibility/performance acceptance;
- remaining platform-system acceptance;
- rollback/recovery exercise;
- explicit production approval.

## Documentation authority

- Central project specification: `GoreeCloud/Projects/Project Specification — Monitor.docx`.
- Central changelog: `GoreeCloud/Changelogs/Change Log — Monitor.docx`.
- Repository roadmap: `FEATURE-ROADMAP.md`, synchronized with the canonical Drive roadmap.
- This repository is authoritative for source-coupled implementation documentation.

## Historical evidence

- Uptime Kuma configuration/runtime evidence may support isolated recovery/reconciliation only.
- 2.1-labelled Glaze material is historical/non-authoritative and must not define current source state.
- ntfy references are historical unless explicitly describing migration provenance.

## Maintenance rule

Keep source status, platform conformance, roadmap state, notification durability, and target-acceptance boundaries synchronized with verified implementation. Do not convert planned, partial, or unverified production work into completion claims.


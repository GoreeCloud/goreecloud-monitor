# Documented Uptime Kuma Baseline Reconciliation

This document is a cutover aid, not a substitute for a fresh live Uptime Kuma configuration snapshot.

## Why reconciliation is required

The GoreeCloud document `GoreeCloud — Inventory — Uptime Kuma Monitors` lists a broad monitoring inventory, but the later Uptime Kuma change record explicitly says Flatnotes, Linkding, and Termix were removed from the Uptime Kuma UI and their residual Compose host mappings were removed. The written inventory therefore cannot be treated as a byte-for-byte representation of live state.

A verified sanitized live-evidence bundle collected on 2026-08-17 established the current Uptime Kuma configuration authority for this acceptance session. It contains 23 active monitor definitions. The repository baseline at `src/monitoring/data/uptime-kuma-documented-baseline.json` has now been reconciled to those live labels and coverage while preserving the recorded retirement set.

The reconciled manifest contains:

- 23 monitors expected active;
- Flatnotes, Linkding, and Termix marked expected retired;
- the live `GoreeCloud VPS` Ping monitor marked as an unresolved cutover blocker;
- Cloudflare DNS and Google DNS marked for manual review because the live source explicitly uses resolver-specific checks that Monitor v0.1 does not automatically preserve;
- GoreeCloud Research Library and GoreeCloud Memos recorded as current live coverage;
- live Uptime Kuma labels aligned exactly for Adguard Home, Netbird, GoreeCloud VPS, and Caddy so reconciliation does not report false missing/unexpected pairs caused only by stale documentation labels.

No private NetBird address, credential, notification token, target URL, or response content is stored in this baseline manifest.

## Live authority

Immediately before migration work, obtain a fresh sanitized configuration snapshot from the running Uptime Kuma instance using the reviewed live-evidence collector:

```bash
python3 scripts/collect_live_acceptance_evidence.py
```

On the current GoreeCloud VPS, the collector uses authenticated `kuma-cli v2.0.0` `monitor list` output, validates the ID-keyed monitor map, and writes only `uptime-kuma-config.sanitized.json`. Raw monitor-list output is not written to disk.

The sanitized live snapshot becomes the migration source for that acceptance session. Do not edit it to make it match this document. A documented expected monitor that is absent may have been intentionally retired after this baseline was written. An unexpected live monitor may be valid new coverage. Either condition requires the GoreeCloud records and migration plan to be updated before cutover.

The 2026-08-17 reconciliation updated the baseline because the evidence demonstrated valid newer coverage and stale labels; it did not alter the collected live snapshot.

## Command

```bash
python manage.py reconcileuptimebaseline \
  /path/to/uptime-kuma-config.sanitized.json
```

For a sanitized JSON report that does not fail the shell while unresolved items are being reviewed:

```bash
python manage.py reconcileuptimebaseline \
  /path/to/uptime-kuma-config.sanitized.json \
  --json \
  --no-fail
```

The normal command fails closed until there are zero unresolved reviews and zero blockers.

It reports:

- documented active monitors missing from live Uptime Kuma;
- documented retired monitors that reappear live;
- unexpected live monitors absent from the documented baseline;
- duplicate or unnamed source records;
- monitor types/configurations the migration mapper cannot represent;
- migration warnings that require review;
- baseline-specific review items and blockers.

The report is intentionally sanitized: it contains monitor names, types, status classifications, and migration issue descriptions, not target URLs, private addresses, request headers, or credential values.

## Verified 2026-08-17 findings

The accepted schema-v2 target/configuration evidence bundle passed outer and internal SHA-256 verification and reported no collection failures. The sanitizer recognized 23 monitor definitions in `kuma-cli-v2-monitor-map` format. No known sensitive monitor fields required value redaction; 19 monitors had non-sensitive unknown fields omitted by name for later review.

The live configuration establishes two important migration facts:

- 22 of the 23 definitions use monitor types supported by the current migration mapper.
- The remaining `GoreeCloud VPS` definition is Uptime Kuma `ping` and therefore remains intentionally unsupported rather than being approximated by TCP coverage.

Every live monitor currently has a notification assignment in Uptime Kuma. Notification assignments are not imported into GoreeCloud Monitor and must be configured and tested separately before activation. Additional review warnings are expected for status-code ranges, Uptime Kuma retry semantics, redirect limits, and the two custom DNS resolvers.

## Known unresolved items

### GoreeCloud VPS

The live monitor is Uptime Kuma type `ping` and verifies private NetBird network-layer reachability. TCP 22 and TCP 443 provide useful overlapping evidence but do not have identical semantics. Uptime Kuma retirement remains blocked until a low-privilege ICMP design or a formally approved replacement requirement is validated.

### Cloudflare DNS and Google DNS

The live sanitized configuration confirms A-record checks through custom resolvers `1.1.1.1` and `8.8.8.8`, respectively. Monitor v0.1 currently uses its configured resolver and therefore cannot claim exact resolver-specific parity without an approved design change or documented replacement requirement.

### Notification assignments

All 23 live Uptime Kuma definitions currently have a notification assignment. GoreeCloud Monitor intentionally does not import those assignments. Monitor notification publishing must be configured independently and validated with controlled DOWN and RECOVERED transitions before cutover.

## Runtime-state boundary

Baseline reconciliation is configuration reconciliation. The current kuma-cli v2 monitor list does not contain heartbeat/status/ping values and cannot prove runtime equivalence. Runtime-state comparison remains a separate later acceptance gate using a separately validated sanitized runtime snapshot.

## Filesystem-permission review

The same target-evidence bundle recorded the production Uptime Kuma Compose file and production Caddyfile as mode `0664`. GoreeCloud's ordinary human-managed configuration baseline is normally `0640` unless approved group modification or broader read access is required. Do not change these modes merely to make the review green; inspect owner/group purpose, parent-directory access, ACLs, service requirements, and rollback path before any targeted correction.

## Retirement rule

Do not remove a baseline item merely to make reconciliation green. A discrepancy is resolved only when the live configuration, intended monitoring requirement, replacement Monitor definition, documentation, and rollback plan agree.

# Documented Uptime Kuma Baseline Reconciliation

This document is a cutover aid, not a substitute for a live Uptime Kuma export.

## Why reconciliation is required

The GoreeCloud document `GoreeCloud — Inventory — Uptime Kuma Monitors` lists a broad monitoring inventory, but the later Uptime Kuma change record explicitly says Flatnotes, Linkding, and Termix were removed from the Uptime Kuma UI and their residual Compose host mappings were removed. The written inventory therefore cannot be treated as a byte-for-byte representation of live state.

The repository carries a sanitized baseline manifest at `src/monitoring/data/uptime-kuma-documented-baseline.json` with:

- 21 monitors documented as expected active after applying the recorded retirement cleanup;
- Flatnotes, Linkding, and Termix marked expected retired;
- GoreeCloud VPS Ping marked as an unresolved cutover blocker;
- Cloudflare DNS and Google DNS marked for manual review because the written scope is explicitly resolver-specific while Monitor v0.1 does not automatically preserve Uptime Kuma custom-resolver behavior.

No private NetBird address, credential, notification token, or response content is stored in this baseline manifest.

## Live authority

Immediately before migration work, obtain a fresh configuration export from the running Uptime Kuma instance using the approved kuma-cli workflow. The live export becomes the migration source for that acceptance session.

Do not edit the live export to make it match this document. Reconcile differences instead. A documented expected monitor that is absent may have been intentionally retired after this baseline was written. An unexpected live monitor may be valid new coverage. Either condition requires the GoreeCloud records and migration plan to be updated before cutover.

## Command

```bash
python manage.py reconcileuptimebaseline uptime-kuma-export.json
```

For a sanitized JSON report that does not fail the shell while unresolved items are being reviewed:

```bash
python manage.py reconcileuptimebaseline uptime-kuma-export.json --json --no-fail
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

## Known unresolved items

### GoreeCloud VPS Ping

The Ping monitor verifies private NetBird network-layer reachability. TCP 22 and TCP 443 provide useful overlapping evidence but do not have identical semantics. Uptime Kuma retirement remains blocked until a low-privilege ICMP design or a formally approved replacement requirement is validated.

### Cloudflare DNS and Google DNS

The written inventory describes these as resolver-specific checks through `1.1.1.1` and `8.8.8.8`. The live Uptime Kuma export must confirm the queried hostname, record type, resolver field, and any other settings. Monitor v0.1 currently uses its configured resolver and therefore cannot claim exact resolver-specific parity without an approved design change or documented replacement requirement.

## Retirement rule

Do not remove a baseline item merely to make reconciliation green. A discrepancy is resolved only when the live configuration, intended monitoring requirement, replacement Monitor definition, documentation, and rollback plan agree.

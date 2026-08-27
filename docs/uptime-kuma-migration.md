# Uptime Kuma Migration

GoreeCloud Monitor replaces Uptime Kuma only through a staged, reversible migration. The importer is deliberately conservative: it maps only monitor semantics that GoreeCloud Monitor can represent, imports monitors **paused by default**, and refuses to copy authentication material or weaker TLS behavior.

## Supported source

The live GoreeCloud VPS currently uses `kuma-cli v2.0.0`. That CLI exposes monitor configuration with `kuma monitor list`; it does not expose the older assumed `kuma config export` command. Its JSON output is an object keyed by monitor ID.

Do not redirect raw live `kuma monitor list` output into a normal working file. Depending on monitor configuration, the output can contain operational targets or reusable secret-bearing fields.

Use the reviewed live-evidence collector instead:

```bash
python3 scripts/collect_live_acceptance_evidence.py
```

The collector authenticates through the existing protected kuma-cli session, validates the ID-keyed monitor map, removes or marks sensitive configuration, and writes only the sanitized migration source:

```text
uptime-kuma-config.sanitized.json
```

The migration loader continues to accept its normalized `monitors` list format, a direct monitor list, or a single monitor JSON object. The sanitized collector output is the preferred live source because it applies the GoreeCloud secrecy and fail-closed rules before data is persisted.

Do not commit raw or sanitized live evidence to Git. Sanitized bundles are still Internal operational artifacts.

## Audit before import

Run the compatibility audit first:

```bash
python manage.py audituptimekuma /path/to/uptime-kuma-config.sanitized.json
```

For machine-readable review:

```bash
python manage.py audituptimekuma \
  /path/to/uptime-kuma-config.sanitized.json \
  --json
```

The report is sanitized. It identifies support, warnings, and blockers without echoing credential values.

## Mapping policy

The importer currently understands:

- Uptime Kuma `http` -> Monitor HTTP or HTTPS
- `keyword` -> HTTP/HTTPS body-text assertion
- simple equality `json-query` -> HTTP/HTTPS JSON path/value assertion
- `port` or `tcp` -> TCP
- `dns` -> DNS A, AAAA, or CNAME, including supported custom resolver semantics
- `push` -> Monitor push/heartbeat with a newly generated token

For a DNS monitor with `dns_resolve_server`, the importer preserves the resolver through Monitor's portable resolver-qualified target form, `dns://resolver[:port]/query-name`. The explicit resolver is validated through Monitor's destination policy before runtime use. See `dns-resolver-semantics.md`.

Unsupported monitor types are reported rather than guessed.

The following source behavior requires manual review or blocks automatic migration:

- authentication headers, request bodies, bearer/basic/OAuth credentials, client TLS material, or other sensitive request configuration
- disabled TLS verification
- per-monitor proxies
- upside-down semantics
- Uptime Kuma condition expressions
- inverted keyword checks
- complex JSONPath or non-equality JSON operators
- monitor types outside the supported set
- custom DNS resolver values that cannot be represented by the resolver-qualified target contract

Some compatible definitions can still produce warnings. Examples include Uptime Kuma status-code ranges, retry timing, tags, notification assignments, and redirect limits. These are not silently represented as exact equivalents.

## Safe import

Dry-run the complete migration:

```bash
python manage.py importuptimekuma \
  /path/to/uptime-kuma-config.sanitized.json \
  --dry-run
```

Import supported definitions:

```bash
python manage.py importuptimekuma /path/to/uptime-kuma-config.sanitized.json
```

Imported monitors are paused by default. This prevents duplicate checks and notifications while Uptime Kuma remains authoritative.

If the source contains unsupported monitors, the default behavior is to reject the entire import. To create only compatible definitions:

```bash
python manage.py importuptimekuma \
  /path/to/uptime-kuma-config.sanitized.json \
  --allow-partial
```

A sanitized report can be written separately:

```bash
python manage.py importuptimekuma \
  /path/to/uptime-kuma-config.sanitized.json \
  --allow-partial \
  --report monitor-migration-report.json
```

`--activate` exists only for warning-free mappings. If any migrated definition still has a compatibility warning, activation is refused. The normal migration workflow is to import paused, review and correct definitions in Monitor, then activate monitors deliberately.

## Compare definitions

After review, compare the sanitized source definitions with the Monitor database:

```bash
python manage.py compareuptimekuma /path/to/uptime-kuma-config.sanitized.json
```

Machine-readable comparison:

```bash
python manage.py compareuptimekuma \
  /path/to/uptime-kuma-config.sanitized.json \
  --json
```

The comparison classifies definitions as:

- `match`
- `different`
- `missing`
- `unsupported`
- `monitor-only`

This is a configuration comparison, not proof of runtime equivalence.

## Compare live runtime state

`kuma-cli v2.0.0` `monitor list` output is configuration-only. Live validation confirmed it does not contain heartbeat, status, or ping values, so it must **not** be used as input to `compareuptimestate`.

The runtime comparison command remains available for a separately validated sanitized runtime snapshot:

```bash
python manage.py compareuptimestate /path/to/uptime-kuma-runtime.sanitized.json
```

A machine-readable report is also available:

```bash
python manage.py compareuptimestate \
  /path/to/uptime-kuma-runtime.sanitized.json \
  --json
```

The default absolute response-time tolerance is 250 milliseconds. Override it when the acceptance plan defines a different tolerance:

```bash
python manage.py compareuptimestate \
  /path/to/uptime-kuma-runtime.sanitized.json \
  --latency-tolerance-ms 500
```

A separately validated runtime collector must retain only the source fields required for comparison: monitor ID/name/type/active state plus heartbeat status and ping. Target URLs and heartbeat diagnostic messages must be excluded.

Uptime Kuma heartbeat states are normalized as follows: Down -> Down, Up -> Up, Pending -> Unknown, Maintenance -> Maintenance, and inactive -> Paused. A GoreeCloud Monitor Degraded state intentionally does not collapse into Uptime Kuma Up; the difference remains visible for review.

A single snapshot is not acceptance evidence by itself. Parallel validation should collect repeated comparisons across healthy operation plus controlled failure, recovery, TLS-warning, maintenance, notification, and resolver-specific DNS scenarios.

## Parallel acceptance

Before cutover:

1. Keep Uptime Kuma active and authoritative.
2. Collect and review a fresh sanitized live configuration snapshot with the reviewed evidence collector.
3. Audit and reconcile that snapshot against the documented baseline.
4. Import compatible definitions into a non-production or isolated Monitor target, paused by default.
5. Correct every warning and unsupported definition manually or by a later approved mapper.
6. Configure new Monitor push tokens at their senders.
7. Configure notification delivery separately; notification assignments are not migrated automatically.
8. Activate approved Monitor definitions deliberately.
9. Run Monitor and Uptime Kuma in parallel using distinct conflict-free monitoring identities.
10. Collect repeated runtime snapshots through a separately validated runtime-state source and run `compareuptimestate`.
11. Compare controlled state transitions, latency, TLS behavior, outage/recovery behavior, maintenance, notifications, and resolver-specific DNS behavior.
12. Prove backup and restore in the target environment.
13. Validate private Caddy, DNS, NetBird, firewall, and monitoring-source behavior.
14. Resolve every baseline monitor that the importer reports as unsupported; unsupported coverage is a cutover blocker.
15. Approve cutover explicitly.
16. Preserve Uptime Kuma rollback data until Monitor has passed the agreed acceptance period.

The migration tools do not modify Uptime Kuma and do not authorize its retirement.

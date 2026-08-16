# Uptime Kuma Migration

GoreeCloud Monitor replaces Uptime Kuma only through a staged, reversible migration. The importer is deliberately conservative: it maps only monitor semantics that GoreeCloud Monitor can represent, imports monitors **paused by default**, and refuses to copy authentication material or weaker TLS behavior.

## Supported source

The preferred migration source is a JSON configuration export from `kuma-cli`:

```bash
kuma config export --output uptime-kuma-export.json
```

A direct monitor list or a single monitor JSON object can also be audited, but the configuration export is preferred because it contains the monitor definitions used for migration review.

Do not commit a Uptime Kuma export to Git. Export files may contain configuration that should be treated as sensitive even when notification secrets are obfuscated.

## Audit before import

Run the compatibility audit first:

```bash
python manage.py audituptimekuma uptime-kuma-export.json
```

For machine-readable review:

```bash
python manage.py audituptimekuma uptime-kuma-export.json --json
```

The report is sanitized. It identifies support, warnings, and blockers without echoing credential values.

## Mapping policy

The importer currently understands:

- Uptime Kuma `http` -> Monitor HTTP or HTTPS
- `keyword` -> HTTP/HTTPS body-text assertion
- simple equality `json-query` -> HTTP/HTTPS JSON path/value assertion
- `port` or `tcp` -> TCP
- `dns` -> DNS A, AAAA, or CNAME
- `push` -> Monitor push/heartbeat with a newly generated token

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

Some compatible definitions can still produce warnings. Examples include Uptime Kuma status-code ranges, retry timing, custom DNS resolvers, tags, notification assignments, and redirect limits. These are not silently represented as exact equivalents.

## Safe import

Dry-run the complete migration:

```bash
python manage.py importuptimekuma uptime-kuma-export.json --dry-run
```

Import supported definitions:

```bash
python manage.py importuptimekuma uptime-kuma-export.json
```

Imported monitors are paused by default. This prevents duplicate checks and notifications while Uptime Kuma remains authoritative.

If the source contains unsupported monitors, the default behavior is to reject the entire import. To create only compatible definitions:

```bash
python manage.py importuptimekuma uptime-kuma-export.json --allow-partial
```

A sanitized report can be written separately:

```bash
python manage.py importuptimekuma uptime-kuma-export.json \
  --allow-partial \
  --report monitor-migration-report.json
```

`--activate` exists only for warning-free mappings. If any migrated definition still has a compatibility warning, activation is refused. The normal migration workflow is to import paused, review and correct definitions in Monitor, then activate monitors deliberately.

## Compare definitions

After review, compare the source definitions with the Monitor database:

```bash
python manage.py compareuptimekuma uptime-kuma-export.json
```

Machine-readable comparison:

```bash
python manage.py compareuptimekuma uptime-kuma-export.json --json
```

The comparison classifies definitions as:

- `match`
- `different`
- `missing`
- `unsupported`
- `monitor-only`

This is a configuration comparison, not proof of runtime equivalence.

## Compare live runtime state

During parallel operation, capture Uptime Kuma's current monitor list without notification configuration:

```bash
kuma monitors list --json > uptime-kuma-live.json
```

Then compare Uptime Kuma's heartbeat state and response-time snapshot with the current GoreeCloud Monitor database:

```bash
python manage.py compareuptimestate uptime-kuma-live.json
```

A machine-readable report is also available:

```bash
python manage.py compareuptimestate uptime-kuma-live.json --json
```

The default absolute response-time tolerance is 250 milliseconds. Override it when the acceptance plan defines a different tolerance:

```bash
python manage.py compareuptimestate uptime-kuma-live.json --latency-tolerance-ms 500
```

Uptime Kuma heartbeat states are normalized as follows: Down -> Down, Up -> Up, Pending -> Unknown, Maintenance -> Maintenance, and inactive -> Paused. A GoreeCloud Monitor Degraded state intentionally does not collapse into Uptime Kuma Up; the difference remains visible for review.

The runtime report contains monitor names, normalized states, response times, and deltas only. Source URLs, request headers, notification assignments, and reusable secrets are not copied to the report.

A single snapshot is not acceptance evidence by itself. Parallel validation should collect repeated comparisons across healthy operation plus controlled failure, recovery, TLS-warning, maintenance, and notification scenarios.

## Parallel acceptance

Before cutover:

1. Keep Uptime Kuma active and authoritative.
2. Audit the source export.
3. Import compatible definitions into a non-production or isolated Monitor target.
4. Correct every warning and unsupported definition manually or by a later approved mapper.
5. Configure new Monitor push tokens at their senders.
6. Configure notification delivery separately; notification assignments are not migrated automatically.
7. Activate approved Monitor definitions.
8. Run Monitor and Uptime Kuma in parallel.
9. Capture repeated `kuma monitors list --json` snapshots and run `compareuptimestate` to compare normalized state and response time.
10. Compare controlled state transitions, latency, TLS behavior, outage/recovery behavior, and notifications.
11. Prove backup and restore in the target environment.
12. Validate private Caddy, DNS, NetBird, firewall, and monitoring-source behavior.
13. Resolve every baseline monitor that the importer reports as unsupported; unsupported coverage is a cutover blocker.
14. Approve cutover explicitly.
15. Preserve Uptime Kuma rollback data until Monitor has passed the agreed acceptance period.

The migration tools do not modify Uptime Kuma and do not authorize its retirement.

# Cutover and Rollback Readiness

This procedure defines the evidence and ordering required before GoreeCloud Monitor can replace Uptime Kuma. It does not authorize a production cutover by itself.

## Release unit

Treat a Monitor production release as one versioned unit:

- exact GoreeCloud Monitor Git revision;
- exact application image identity/digest;
- exact PostgreSQL image tag and digest;
- reviewed production Compose definition;
- protected Compose interpolation file;
- protected Monitor application environment file;
- protected PostgreSQL environment file;
- database schema/migration state;
- monitor-definition export;
- Uptime Kuma migration/reconciliation reports;
- target Caddy/DNS/NetBird/firewall configuration evidence;
- backup and restore evidence.

Do not roll back only an application image while silently retaining incompatible schema or deployment configuration.

## Preconditions before parallel operation

1. Deploy Monitor under a unique, conflict-free runtime identity. Do not reuse Uptime Kuma's live source IP.
2. Validate target storage ownership, permissions, capacity, backup scope, Caddy network name, and zero host-published Monitor/database ports.
3. Run `targetpreflight` in the target web container and preserve the sanitized result.
4. Collect a fresh sanitized live Uptime Kuma configuration snapshot with the reviewed live-evidence collector. On the current GoreeCloud VPS this uses authenticated kuma-cli v2 `monitor list` output and does not persist the raw monitor map.
5. Run `reconcileuptimebaseline`; resolve every missing, unexpected, retired-present, unsupported, review, duplicate, or baseline-blocker result.
6. Run `audituptimekuma` against the sanitized configuration snapshot and preserve the sanitized report.
7. Import compatible definitions paused into an empty Monitor database.
8. Review every imported definition, new push token, notification assignment, target allowlist, private-network path, and TLS requirement before enabling checks.
9. Keep Uptime Kuma active and authoritative during this work.
10. Establish a separately validated runtime-state evidence path before claiming state/latency parity. The current kuma-cli v2 monitor list is configuration-only and does not contain heartbeat/status/ping values.

## Parallel acceptance

Run both systems long enough to exercise normal operation and controlled transitions. At minimum preserve evidence for:

- repeated healthy state comparisons from a separately validated runtime snapshot source;
- controlled DOWN transition;
- configured failure threshold behavior;
- controlled RECOVERED transition;
- maintenance suppression;
- TLS validation and expiration/degraded behavior where applicable;
- internal HTTP monitoring such as ntfy;
- private NetBird TCP targets;
- external Internet checks;
- DNS behavior and any resolver-specific replacement decision;
- notification publishing with the dedicated write-only identity;
- negative authorization tests for notification permissions where the target environment supports them;
- Manager read-only API behavior if enabled;
- Monitor restart/recreation without uncontrolled duplicate alerts;
- PostgreSQL backup and isolated restore using target storage.

Use repeated `compareuptimestate` snapshots for state/latency evidence only after the runtime snapshot source has been separately validated and sanitized. One matching snapshot is not sufficient acceptance evidence.

## Required rollback bundle before cutover

Before changing production authority, preserve:

1. the exact currently accepted Monitor release unit;
2. the immediately previous Monitor release unit if Monitor is already in production;
3. a verified pre-cutover Monitor PostgreSQL backup;
4. a fresh Uptime Kuma configuration/database backup plus the sanitized live configuration snapshot and reconciliation reports used for migration;
5. the current Uptime Kuma Docker/Compose configuration needed to restart it;
6. current Caddy/DNS/NetBird/firewall configuration evidence;
7. current ntfy publisher/ACL configuration evidence;
8. the cutover acceptance report and timestamps.

Raw Uptime Kuma monitor-list output, credentials, and auth tokens are not general rollback artifacts and must not be copied into Git or public evidence. Preserve sensitive source data only through the approved protected backup/configuration mechanisms that already own that responsibility.

A file existing is not sufficient. The required database restore path must have been proven against the target environment before authority changes.

## Cutover sequence

1. Confirm all cutover gates are green and the ICMP/Ping or replacement requirement is resolved.
2. Record the live Uptime Kuma and Monitor state immediately before authority change through the approved sanitized runtime-state path.
3. Create final pre-cutover backups and verify their identities.
4. Prevent configuration drift during the authority-change window.
5. Switch only the minimum required monitoring/notification/network identity configuration.
6. Do not delete Uptime Kuma. Stop or isolate it only when required to prevent duplicate monitoring or to release a deliberately reused network identity.
7. Validate Monitor checks, incident state, notification delivery, Caddy/DNS/NetBird reachability, and Manager integration after the change.
8. Keep the rollback bundle immediately available through the agreed observation period.
9. Retire Uptime Kuma only after the observation period and an explicit retirement decision.

## Rollback triggers

Rollback should be initiated rather than improvised when any required acceptance property is lost, including:

- material monitor coverage is missing or semantically different from the approved requirement;
- Monitor cannot reach required private or public targets;
- false DOWN/RECOVERED storms occur;
- notification delivery or authorization behavior is incorrect;
- database migrations fail or restored state is inconsistent;
- target Caddy/DNS/NetBird/firewall behavior is not as approved;
- Monitor cannot be restarted/recreated cleanly;
- the Ping/resolver-specific coverage decision was assumed rather than actually resolved;
- another security or recovery condition makes continued operation unsafe.

## Rollback sequence

1. Preserve logs and sanitized failure evidence before changing state when practical.
2. Stop Monitor worker execution first if it is generating duplicate or unsafe checks/notifications.
3. If the failed release introduced database migrations that are not proven backward-compatible, restore the pre-upgrade database backup instead of running an older application against a newer unknown schema.
4. Restore the previous complete Monitor release unit when rolling back between Monitor releases.
5. If returning authority to Uptime Kuma, restore/restart its preserved runtime using its original conflict-free monitoring identity and configuration.
6. Restore only the Caddy/DNS/NetBird/firewall/notification changes that were part of the failed cutover; do not broadly revert unrelated infrastructure.
7. Validate Uptime Kuma or the previous Monitor release against known healthy endpoints and notification behavior.
8. Confirm no two active monitoring workers now share the same fixed network identity or generate unintended duplicate alerts.
9. Record the rollback result and keep the failed release evidence for investigation.

## Schema rule

Database rollback is not equivalent to application rollback. Every future migration-bearing release must explicitly prove either:

- backward compatibility with the prior application revision, or
- a tested database restore/downgrade procedure.

Until that evidence exists, the safe rollback boundary for a migration-bearing release is the verified pre-upgrade database backup plus the previous complete release unit.

## Current boundary

The repository can prove source behavior, disposable production topology, PostgreSQL recovery, immediate-predecessor compatibility, and sanitized target/configuration evidence collection in CI. Live target validation has now shown the actual kuma-cli v2 command and data shape, but runtime heartbeat/state collection still requires a separately validated path. The repository still cannot prove live Caddy, DNS, NetBird, firewall, production ntfy ACLs, real parallel observations, target backup storage, or administrator alert receipt without the target environment. Those remain mandatory before Uptime Kuma retirement.

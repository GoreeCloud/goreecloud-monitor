# Live Acceptance Evidence

This procedure collects the first live target/Uptime Kuma evidence required for GoreeCloud Monitor production acceptance **without deploying Monitor, changing Uptime Kuma, changing Docker networks, modifying Caddy, changing DNS, changing NetBird, or changing the firewall**.

The collector is intentionally read-only with respect to the live service environment. Its only writes are a new operator-owned evidence directory/archive and a temporary Uptime Kuma export that is deleted after sanitization.

## Administrative path

Use the approved private administrative path whenever available:

```bash
ssh goreecloud-vps-netbird
```

Run the collector as the named administrative account. The collector does not invoke `sudo` automatically. A failed read-only check should be reviewed rather than immediately rerun with broader privilege.

Do not pipe an unreviewed remote script into a shell. Use an exact reviewed repository revision or copy the reviewed script through an approved administrative path.

## What the bundle contains

The bundle may contain Internal GoreeCloud operational information including:

- host name, operating-system version, interface addresses, routes, and listening sockets;
- Docker/Compose versions;
- running container names, image references, states, ports, and network names;
- the Uptime Kuma container image/state and its attached Docker-network address/subnet context;
- SHA-256 fingerprints, size, ownership IDs, and modes for the current Uptime Kuma Compose file and production Caddyfile;
- a **sanitized** Uptime Kuma configuration export;
- a **sanitized** Uptime Kuma runtime monitor snapshot;
- collection failures by check label and return code;
- SHA-256 checksums for the evidence files.

The collector does **not** copy the Caddyfile or Compose file contents into the bundle.

## Uptime Kuma sanitization

The raw `kuma config export` exists only inside a permission-restricted temporary directory during collection. It is deleted when collection completes.

The sanitized configuration export keeps only migration/reconciliation-relevant monitor fields. Authentication material, request bodies/headers, certificate material, database connection strings, passwords, tokens, and similar values are replaced with a non-secret sentinel. The field remains non-empty so the existing Monitor importer still blocks automatic migration and reports manual authentication/configuration review.

URL user information, URL query strings, and URL fragments are removed from the evidence copy. Their removal also injects the same non-secret blocker sentinel so sanitization cannot make the monitor appear safer than its original definition.

Unknown non-empty source fields are omitted by value and recorded by **field name** for later review.

The runtime snapshot is narrower. It keeps only:

- monitor ID;
- monitor name;
- monitor type;
- active state;
- heartbeat status;
- heartbeat response time (`ping`).

Target URLs and heartbeat diagnostic messages are not retained in the runtime evidence file.

## Collection

From an exact reviewed checkout of this repository:

```bash
python3 scripts/collect_live_acceptance_evidence.py
```

The default command expects the current GoreeCloud paths and names already documented for the VPS:

- Uptime Kuma Compose: `/srv/docker/stacks/uptime-kuma/docker-compose.yml`
- production Caddyfile: `/srv/docker/caddy/Caddyfile`
- Uptime Kuma container: `uptime-kuma`
- kuma-cli executable: `kuma`

Override a value only after the live environment has shown that the documented value is no longer correct:

```bash
python3 scripts/collect_live_acceptance_evidence.py \
  --uptime-compose /verified/path/docker-compose.yml \
  --caddyfile /verified/path/Caddyfile \
  --uptime-container verified-container-name \
  --kuma-bin /verified/path/kuma
```

Do not guess replacements merely to make the collector pass.

## Result

A successful run creates:

```text
goreecloud-monitor-live-evidence-<UTC timestamp>/
├── target-evidence.json
├── uptime-kuma-config.sanitized.json
├── uptime-kuma-runtime.sanitized.json
├── uptime-kuma-sanitization-report.json
└── SHA256SUMS

goreecloud-monitor-live-evidence-<UTC timestamp>.tar.gz
```

The directory and archive are created with restrictive operator-only permissions.

`target-evidence.json` contains:

```json
{
  "schema": "goreecloud-monitor-live-acceptance-evidence",
  "version": 1,
  "ready_for_review": true
}
```

`ready_for_review` means the required **read-only collection** succeeded. It does not mean Monitor is production-ready and does not authorize deployment or cutover.

The collector returns exit code `2` when one or more required checks fail. Inspect `collection_failures` before deciding whether a follow-up check needs different access or a corrected verified path.

## Review the sanitized Kuma baseline

After the bundle is available in a trusted Monitor checkout, reconcile the sanitized configuration export against the documented baseline:

```bash
python manage.py reconcileuptimebaseline \
  /path/to/uptime-kuma-config.sanitized.json \
  --json \
  --no-fail
```

The sanitized copy deliberately preserves blockers when secret-bearing or otherwise redacted source configuration was present.

The baseline reconciliation remains fail-closed for missing expected monitors, retired monitors that reappear, unexpected live monitors, duplicate/invalid source identities, unsupported monitor types, the documented ICMP/Ping blocker, and unresolved review requirements.

## Later parallel comparison

After a separate isolated Monitor target exists and approved monitors are deliberately activated, the sanitized runtime snapshot can be used with:

```bash
python manage.py compareuptimestate \
  /path/to/uptime-kuma-runtime.sanitized.json \
  --json
```

One snapshot is not sufficient acceptance evidence. Repeated healthy observations plus controlled DOWN, RECOVERED, TLS, maintenance, and notification scenarios remain required.

## What this procedure does not prove

This collection does not prove or authorize:

- Monitor deployment to the live Infrastructure Services VM;
- a production Monitor hostname;
- Caddy publication;
- AdGuard Home/private DNS publication;
- NetBird policy changes;
- firewall changes;
- a parallel monitoring-source IP;
- Monitor/PostgreSQL/ntfy production credentials;
- ntfy write-only ACL behavior or administrator receipt;
- target backup storage or a live restore;
- ICMP/Ping replacement;
- custom DNS resolver equivalence;
- live rollback execution;
- Uptime Kuma retirement.

Uptime Kuma remains authoritative until the later target-environment gates and explicit cutover decision are complete.

## Evidence handling

The bundle is sanitized but remains **Internal**. Review it before copying it outside an approved GoreeCloud administrative context. Do not publish it in Git, attach it to a public issue/PR, or treat sanitization as declassification.

Never upload or commit the unsanitized Uptime Kuma configuration export.

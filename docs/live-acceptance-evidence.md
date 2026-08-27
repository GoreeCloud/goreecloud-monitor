# Live Acceptance Evidence

This procedure collects the first live target/Uptime Kuma evidence required for GoreeCloud Monitor production acceptance **without deploying Monitor, changing Uptime Kuma, changing Docker networks, modifying Caddy, changing DNS, changing NetBird, or changing the firewall**.

The collector is intentionally read-only with respect to the live service environment. Its only writes are a new operator-owned evidence directory/archive containing sanitized review material.

## Administrative path

Use the approved private administrative path whenever available:

```bash
ssh goreecloud-vps-netbird
```

If the administrative shell is already running on the target VPS, do not SSH from the VPS back into itself merely to satisfy this example.

Run the collector as the named administrative account. The collector does not invoke `sudo` automatically. A failed read-only check should be reviewed rather than immediately rerun with broader privilege.

Do not pipe an unreviewed remote script into a shell. Use an exact reviewed repository revision or copy the reviewed script through an approved administrative path.

## What the bundle contains

The bundle may contain Internal GoreeCloud operational information including:

- host name, operating-system version, interface addresses, routes, and listening sockets;
- Docker/Compose versions;
- running container names, image references, states, ports, and network names;
- the Uptime Kuma container image/state and its attached Docker-network address/subnet context;
- SHA-256 fingerprints, size, ownership IDs, and modes for the current Uptime Kuma Compose file and production Caddyfile;
- a **sanitized** Uptime Kuma monitor-configuration snapshot;
- a sanitization report containing only monitor names/types plus redacted/omitted field names;
- collection failures by check label and return code;
- SHA-256 checksums for the evidence files.

The collector does **not** copy the Caddyfile or Compose file contents into the bundle.

## kuma-cli v2 compatibility

The live GoreeCloud VPS currently uses `kuma-cli v2.0.0`. That CLI exposes monitor configuration through:

```bash
kuma monitor list
```

It does not expose the older assumed `config export` or `monitors list --json` commands. `kuma monitor list` returns a JSON object keyed by monitor ID rather than a JSON list. The GoreeCloud sanitizer therefore validates the key/monitor-ID relationship, sorts the monitors deterministically by numeric ID, and then sanitizes the values.

The collector uses an authenticated kuma-cli session. It does not accept a username, password, MFA secret, or JWT token as collector command-line arguments. Establish or verify the kuma-cli authentication context separately through an approved protected workflow. Reusable credentials and the stored auth token must not be copied into the evidence bundle.

When `--kuma-url` is not supplied, the collector derives the Uptime Kuma connection URL from Docker metadata without retaining the URL in the evidence bundle. It prefers an attached network named `proxy`; if there is only one attached network, that single network is used. Ambiguous network layouts fail closed rather than guessing.

## Uptime Kuma configuration sanitization

Raw `kuma monitor list` JSON exists only in process memory while collection is running. It is not written to an unsanitized file by the collector.

The sanitized configuration snapshot keeps only migration/reconciliation-relevant monitor fields. Authentication material, request bodies/headers, certificate material, database connection strings, passwords, tokens, and similar values are replaced with a non-secret sentinel. The field remains non-empty so the existing Monitor importer still blocks automatic migration and reports manual authentication/configuration review.

URL user information, URL query strings, and URL fragments are removed from the evidence copy. Their removal also injects the same non-secret blocker sentinel so sanitization cannot make the monitor appear safer than its original definition.

Unknown non-empty source fields are omitted by value and recorded by **field name** for later review.

## Runtime-state boundary

`kuma-cli v2.0.0` monitor-list output is configuration-only. The live probe confirmed that it includes monitor identity/configuration fields but does not include heartbeat, status, or ping values.

The collector therefore does **not** fabricate a runtime snapshot from configuration-only data. Evidence schema version 2 records runtime state as not collected and keeps it as a separate later acceptance gate.

A separate runtime-state collection path must be validated before `compareuptimestate` is used for production parallel acceptance. Uptime Kuma's authenticated internal Socket.IO API provides heartbeat events and monitor-beat queries, but that internal API is not treated as stable until GoreeCloud validates and pins a narrowly scoped collection implementation.

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

Override a value only after the live environment has shown that the documented/default value is no longer correct:

```bash
python3 scripts/collect_live_acceptance_evidence.py \
  --uptime-compose /verified/path/docker-compose.yml \
  --caddyfile /verified/path/Caddyfile \
  --uptime-container verified-container-name \
  --kuma-bin /verified/path/kuma \
  --kuma-url http://verified-internal-address:3001
```

Do not guess replacements merely to make the collector pass.

The collector refuses to overwrite an existing evidence directory. Use a fresh output directory for every run.

## Result

A successful schema-version-2 run creates:

```text
goreecloud-monitor-live-evidence-<UTC timestamp>/
├── target-evidence.json
├── uptime-kuma-config.sanitized.json
├── uptime-kuma-sanitization-report.json
└── SHA256SUMS

goreecloud-monitor-live-evidence-<UTC timestamp>.tar.gz
```

The directory and archive are created with restrictive operator-only permissions.

`target-evidence.json` contains the top-level readiness state and explicitly separates configuration review from runtime comparison:

```json
{
  "schema": "goreecloud-monitor-live-acceptance-evidence",
  "version": 2,
  "acceptance_scope": {
    "target_environment_and_configuration_ready_for_review": true,
    "runtime_state_ready_for_comparison": false
  },
  "ready_for_review": true
}
```

`ready_for_review` means the required **target-environment and sanitized Uptime Kuma configuration collection** succeeded. It does not mean runtime state has been collected, Monitor is production-ready, or cutover is authorized.

The collector returns exit code `2` when one or more required target/configuration checks fail. Inspect `collection_failures` before deciding whether a follow-up check needs different access or a corrected verified path.

## Review the sanitized Kuma baseline

After the bundle is available in a trusted Monitor checkout, reconcile the sanitized configuration snapshot against the documented baseline:

```bash
python manage.py reconcileuptimebaseline \
  /path/to/uptime-kuma-config.sanitized.json \
  --json \
  --no-fail
```

The sanitized copy deliberately preserves blockers when secret-bearing or otherwise redacted source configuration was present.

The baseline reconciliation remains fail-closed for missing expected monitors, retired monitors that reappear, unexpected live monitors, duplicate/invalid source identities, unsupported monitor types, the documented ICMP/Ping blocker, and unresolved review requirements.

## Later parallel runtime comparison

Do not use the configuration snapshot as runtime evidence. Before parallel acceptance, collect a separately validated sanitized runtime snapshot containing only:

- monitor ID;
- monitor name;
- monitor type;
- active state;
- heartbeat status;
- heartbeat response time (`ping`).

Target URLs and heartbeat diagnostic messages must remain excluded from runtime evidence.

After a separately validated runtime snapshot exists and an isolated Monitor target has been deliberately activated, compare it with:

```bash
python manage.py compareuptimestate \
  /path/to/uptime-kuma-runtime.sanitized.json \
  --json
```

One snapshot is not sufficient acceptance evidence. Repeated healthy observations plus controlled DOWN, RECOVERED, TLS, maintenance, and notification scenarios remain required.

## What this procedure does not prove

This collection does not prove or authorize:

- Monitor deployment to the live Infrastructure Services VM;
- runtime state/latency equivalence with Uptime Kuma;
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

Never upload, commit, or paste raw `kuma monitor list` output because it can contain operational target/configuration material and may contain reusable secret-bearing fields depending on monitor configuration.

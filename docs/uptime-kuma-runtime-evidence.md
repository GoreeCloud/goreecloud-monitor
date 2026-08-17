# Uptime Kuma Runtime Evidence

This procedure collects a minimized Uptime Kuma heartbeat snapshot for GoreeCloud Monitor parallel-state comparison without changing Uptime Kuma configuration, Docker networking, Caddy, DNS, NetBird, the firewall, or Monitor production state.

It is separate from `collect_live_acceptance_evidence.py`. The target/configuration collector remains the authority for the schema-v2 target and configuration bundle. Runtime evidence has its own acceptance boundary because `kuma-cli v2.0.0` `monitor list` output is configuration-only.

## Source mechanism

Uptime Kuma 2.5.0 sends authenticated clients a `monitorList` and a `heartbeatList` for each monitor after login. Its server-side heartbeat-list implementation reads the most recent heartbeat rows and sends them through Socket.IO. Uptime Kuma also includes `socket.io-client` as a runtime dependency.

The GoreeCloud runtime collector uses those existing behaviors narrowly:

1. It reads the already protected AutoKuma/kuma-cli login token from the operator's local token file.
2. It starts a temporary `node -e` helper inside the existing `uptime-kuma` container with `docker exec -i`.
3. It passes the token only through the helper's standard input. The token is not placed in Docker/process arguments or environment variables.
4. The helper authenticates to Uptime Kuma over `http://127.0.0.1:3001` from inside the same container.
5. The helper listens only for monitor identity and heartbeat-list events and returns only monitor ID, name, type, active state, latest heartbeat status, and latest heartbeat response time.
6. Python validates completeness and allowed heartbeat-state values, runs the existing GoreeCloud runtime sanitizer, and writes only the minimized sanitized snapshot.

The helper never returns monitor targets, heartbeat diagnostic messages, request configuration, notification configuration, passwords, tokens, or other reusable secret material.

This design deliberately uses the Uptime Kuma version already running on the target rather than installing a new host-side Socket.IO package or adding a new long-lived service. If Uptime Kuma's internal Socket.IO behavior changes, collection fails closed and must be revalidated for that version.

## Authentication prerequisite

The collector does not log in with a username/password and does not create or rotate authentication material. A protected kuma-cli/AutoKuma token must already exist from the separately approved login workflow.

On Linux the default token path is:

```text
~/.config/autokuma/auth.txt
```

`XDG_CONFIG_HOME` is honored when set. A different file may be supplied with `--token-file` only after its purpose and protection are verified.

The collector refuses a token file that:

- is missing or empty;
- is not a regular file;
- is not owned by the current user; or
- grants any group or other permissions.

The token path and token value are not recorded in the runtime evidence bundle.

## Collection

Run from an exact reviewed GoreeCloud Monitor checkout on the Uptime Kuma host:

```bash
python3 scripts/collect_uptime_kuma_runtime_evidence.py
```

A fresh output directory is required for each run. Optional overrides are intentionally narrow:

```bash
python3 scripts/collect_uptime_kuma_runtime_evidence.py \
  --uptime-container verified-container-name \
  --token-file /verified/protected/auth.txt
```

Do not use `sudo` merely to bypass token-file or Docker access failures. Diagnose the expected user, group, file ownership, and Docker authorization first.

## Output

A successful run creates:

```text
goreecloud-monitor-runtime-evidence-<UTC timestamp>/
├── runtime-evidence.json
├── uptime-kuma-runtime.sanitized.json
└── SHA256SUMS

goreecloud-monitor-runtime-evidence-<UTC timestamp>.tar.gz
```

The directory is mode `0700` and the archive is mode `0600` under the collector's restrictive umask.

`runtime-evidence.json` records the collector revision, Uptime Kuma container/image identity, collection mechanism, minimized count summary, safety assertions, and `ready_for_comparison=true`. It does not contain the token or token-file path.

`uptime-kuma-runtime.sanitized.json` contains only:

- monitor ID;
- monitor name;
- monitor type;
- active state;
- latest heartbeat status;
- latest heartbeat response time (`ping`).

Heartbeat diagnostic messages and monitor targets are excluded.

## Fail-closed completeness rules

Runtime evidence is not marked ready merely because one heartbeat exists. The collector rejects the snapshot when:

- no monitors are returned;
- a monitor ID is invalid or duplicated;
- a monitor name is empty or duplicated;
- active state is invalid;
- an active monitor has no heartbeat history;
- a heartbeat is malformed;
- heartbeat status is outside Uptime Kuma 2.5.0 states `0` through `3`; or
- heartbeat response time has an unexpected type.

An inactive monitor may legitimately have no heartbeat history and does not make the snapshot incomplete by itself.

## Comparison boundary

After a runtime bundle is checksum-verified and reviewed, use the sanitized runtime file with:

```bash
python manage.py compareuptimestate \
  /path/to/uptime-kuma-runtime.sanitized.json \
  --json
```

This comparison is meaningful only after an isolated GoreeCloud Monitor target has imported, reviewed, and deliberately activated the corresponding approved definitions.

A single runtime snapshot is not production acceptance. Parallel acceptance still requires repeated observations plus controlled DOWN, RECOVERED, TLS-warning, maintenance, and notification scenarios. The Ping/ICMP and resolver-specific DNS design gates also remain separate from simple status matching.

## Security and operational limits

The collector is read-only by intent, but it depends on authenticated Uptime Kuma's internal Socket.IO behavior. That interface is not treated as a permanent public API contract. Every Uptime Kuma version change that can affect this mechanism requires source review and target revalidation before relying on new runtime evidence.

The collector does not:

- deploy or activate GoreeCloud Monitor;
- write to the Uptime Kuma database;
- add, edit, pause, resume, or delete monitors;
- alter notifications;
- change Docker networks or container configuration;
- change Caddy, DNS, NetBird, or firewall state;
- expose a new host port;
- persist raw heartbeat histories;
- persist heartbeat messages;
- persist the login token;
- authorize cutover or Uptime Kuma retirement.

Runtime evidence remains **Internal** even after sanitization. Do not commit a live runtime bundle to Git or attach it to a public issue or pull request.

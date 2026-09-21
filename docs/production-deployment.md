# Production Deployment Candidate

This document defines the source-controlled production topology and target-acceptance boundary for GoreeCloud Monitor after the permanent retirement of Uptime Kuma and ntfy from `goreecloud-vps-01` on September 18, 2026.

It is an acceptance plan, not authorization to deploy or promote Monitor to production authority.

## Intended host layout

```text
/srv/docker/stacks/goreecloud-monitor/
├── docker-compose.yml
├── .env
├── monitor.env
├── worker.env
└── database.env

/srv/docker/databases/goreecloud-monitor/
└── PostgreSQL data
```

The repository file `compose.production.yml` is the source deployment candidate. At deployment time it should become the reviewed authoritative Compose definition in the approved stack directory; do not maintain competing active production definitions.

## Production topology

- `db` is attached only to the internal `backend` network and publishes no host port.
- `migrate` is a one-shot database migration service attached only to `backend`.
- `web` uses the immutable application image, read-only root filesystem, dropped capabilities, `no-new-privileges`, and bounded `/tmp` tmpfs. It joins only `backend` and the approved external gateway network.
- `worker` uses the same application image and hardening. It joins `backend` and only the approved network needed to reach monitored destinations and GoreeCloud Notify. It is the only service that loads the protected worker-only environment file containing Notify producer configuration; `web` and `migrate` must not receive those producer settings or bearer credential.
- `backend` uses an explicit Linux bridge name supplied through `MONITOR_BACKEND_BRIDGE_NAME` plus an explicit private IPv4 subnet supplied through `MONITOR_BACKEND_SUBNET`, with its gateway fixed to `MONITOR_DNS_SERVER`; this makes both the firewall interface identity and host-side resolver endpoint stable across network recreation.
- `worker` uses exactly one explicit private IPv4 DNS resolver supplied through `MONITOR_DNS_SERVER`, an explicit backend address supplied through `MONITOR_WORKER_BACKEND_IP`, and an explicit proxy-network address supplied through `MONITOR_WORKER_PROXY_IP`. No other Monitor service receives a DNS override. The fixed backend address allows host firewall policy to grant DNS only to the Monitor worker, while the fixed proxy address gives Caddy a stable least-privilege identity for private HTTPS authorization. Worker-only `extra_hosts` mappings resolve the reviewed same-host private HTTPS set (`notify.goreecloud.com`, `adguard.goreecloud.com`, `health.goreecloud.com`, `dav.goreecloud.com`, and `memos.goreecloud.com`) to the approved Caddy proxy-network IPv4 supplied through `MONITOR_CADDY_GATEWAY_IP`; this preserves TLS hostname verification while preventing host-published-port hairpin NAT from replacing the worker identity with the Docker gateway address. Unreviewed or currently unprovisioned names such as `research.goreecloud.com` are deliberately excluded.
- The resolver must provide the approved private answers for private GoreeCloud monitoring targets; a public resolver is not an accepted substitute.
- No service uses privileged mode, host networking, a Docker socket, or added Linux capabilities.
- No Monitor or PostgreSQL port is published on the host. GoreeCloud Gateway is the intended private HTTPS ingress.

The deployment must not reuse retired Uptime Kuma network identity merely for compatibility.

## Image identity

`GOREECLOUD_MONITOR_IMAGE` must be a unique traceable application image built from the accepted Monitor revision. `latest` is rejected.

`POSTGRES_IMAGE` must use an exact tag and digest.

## Environment files

Production uses four purpose-specific files:

- `.env` — Compose interpolation values such as image references, protected file paths, persistent database path, gateway network name, fixed backend bridge name (`MONITOR_BACKEND_BRIDGE_NAME`), fixed backend subnet (`MONITOR_BACKEND_SUBNET`), approved private worker DNS/backend-gateway address (`MONITOR_DNS_SERVER`), fixed worker backend address (`MONITOR_WORKER_BACKEND_IP`), fixed worker proxy address (`MONITOR_WORKER_PROXY_IP`), approved Caddy proxy address for the reviewed worker-only private HTTPS hostname mappings (`MONITOR_CADDY_GATEWAY_IP`), and the protected worker-only environment path (`MONITOR_WORKER_ENV_FILE`).
- `monitor.env` — shared protected Django, monitoring, and platform-integration configuration used by application services. It must not contain GoreeCloud Notify producer settings or the producer bearer token.
- `worker.env` — protected worker-only GoreeCloud Notify producer configuration. It is loaded only by `worker`; `web` and `migrate` must not receive it.
- `database.env` — PostgreSQL database name, username, password, and port.

There is no supported ntfy runtime configuration after retirement.

## Static assets and schema migration

Static assets are generated at image build time. Database migration is explicit through the one-shot `migrate` service. `web` and `worker` start only after migration succeeds.

## Source validation

Resolve and validate the production Compose file:

```bash
docker compose -f compose.production.yml config --format json \
  | python scripts/validate_production_compose.py
```

The validator requires no published ports, no privileged/host-network/device/Docker-socket access, no added capabilities, read-only application root filesystems, `cap_drop: ALL`, `no-new-privileges`, an internal database network with an explicit Linux-safe bridge name and explicit private IPv4 IPAM, the approved external gateway network, a persistent PostgreSQL bind mount, a digest-pinned PostgreSQL image, exactly one private IPv4 DNS resolver on the worker only, a fixed worker backend address inside that subnet, a distinct fixed private IPv4 address for the worker on the proxy network, the exact reviewed worker-only Caddy hostname set (`notify.goreecloud.com`, `adguard.goreecloud.com`, `health.goreecloud.com`, `dav.goreecloud.com`, and `memos.goreecloud.com`) mapped to one distinct private IPv4 gateway endpoint, and the complete Notify producer environment-key set on `worker` only. The same producer keys are rejected on `db`, `migrate`, and `web`. The worker DNS resolver must equal the backend gateway. The live target must separately verify that `MONITOR_CADDY_GATEWAY_IP` is the actual Caddy address on the same proxy network, that Caddy observes the worker's fixed `MONITOR_WORKER_PROXY_IP`, and that the producer token is absent from non-worker container environments.

## Target acceptance required before activation

Before Monitor can become production monitoring authority, verify and record:

1. supported Docker Engine and Compose versions on `goreecloud-vps-01`;
2. authoritative `/srv/docker/` paths, ownership, permissions, capacity, and backup scope;
3. exact GoreeCloud Gateway network identity and backend reachability;
4. zero host-published Monitor/database ports;
5. the approved private Monitor hostname and private DNS record;
6. Gateway configuration validation, trusted certificate, private access, and denial from unauthorized sources;
7. NetBird policy for the web path and every worker monitoring destination, plus proof that the exact worker topology resolves private GoreeCloud targets through the approved private resolver rather than public DNS;
8. accepted GoreeCloud Notify deployment plus a dedicated least-privilege Monitor producer token stored only in the protected worker environment;
9. worker `targetpreflight` output with no blocking findings;
10. fresh PostgreSQL backup and successful isolated restoration against the exact candidate;
11. reconciliation of preserved Uptime Kuma monitor definitions against services that are actually active now;
12. representative HTTP/HTTPS, TCP, TLS, DNS, heartbeat, Ping/ICMP, maintenance, incident, DOWN, RECOVERED, DEGRADED, and TLS-expiry acceptance;
13. durable notification outbox restart/replay proof using the same persisted payload and idempotency identity without duplicate fanout;
14. independent outage alerting that does not depend entirely on the Monitor → Notify chain;
15. current Glaze UI 1.5.1 and nine-system platform acceptance;
16. rollback/recovery to a known-good Monitor release and database state;
17. explicit production-activation approval.

## Uptime Kuma evidence boundary

Uptime Kuma is retired. Preserved configuration, backup, and recovery artifacts may be used for requirement reconciliation, isolated reconstruction, or controlled comparison testing when authorized. They are not active production authority and are not an automatic rollback service.

Restoring Uptime Kuma to production requires a separate explicit authorization.

## Completion boundary

A green source topology or passing target preflight does not by itself establish production authority. Monitor becomes production authority only after the applicable live target, recovery, notification, accessibility/platform, security, independent-alerting, and approval gates are complete and recorded.

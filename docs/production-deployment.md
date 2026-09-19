# Production Deployment Candidate

This document defines the source-controlled production topology and target-acceptance boundary for GoreeCloud Monitor after the permanent retirement of Uptime Kuma and ntfy from `goreecloud-vps-01` on September 18, 2026.

It is an acceptance plan, not authorization to deploy or promote Monitor to production authority.

## Intended host layout

```text
/srv/docker/stacks/goreecloud-monitor/
├── docker-compose.yml
├── .env
├── monitor.env
└── database.env

/srv/docker/databases/goreecloud-monitor/
└── PostgreSQL data
```

The repository file `compose.production.yml` is the source deployment candidate. At deployment time it should become the reviewed authoritative Compose definition in the approved stack directory; do not maintain competing active production definitions.

## Production topology

- `db` is attached only to the internal `backend` network and publishes no host port.
- `migrate` is a one-shot database migration service attached only to `backend`.
- `web` uses the immutable application image, read-only root filesystem, dropped capabilities, `no-new-privileges`, and bounded `/tmp` tmpfs. It joins only `backend` and the approved external gateway network.
- `worker` uses the same application image and hardening. It joins `backend` and only the approved network needed to reach monitored destinations and GoreeCloud Notify.
- `worker` uses exactly one explicit private IPv4 DNS resolver supplied through `MONITOR_DNS_SERVER`. No other Monitor service receives a DNS override. The resolver must be reachable from the existing worker networks and must provide the approved private answers for private GoreeCloud monitoring targets; a public resolver is not an accepted substitute.
- No service uses privileged mode, host networking, a Docker socket, or added Linux capabilities.
- No Monitor or PostgreSQL port is published on the host. GoreeCloud Gateway is the intended private HTTPS ingress.

The deployment must not reuse retired Uptime Kuma network identity merely for compatibility.

## Image identity

`GOREECLOUD_MONITOR_IMAGE` must be a unique traceable application image built from the accepted Monitor revision. `latest` is rejected.

`POSTGRES_IMAGE` must use an exact tag and digest.

## Environment files

Production uses three purpose-specific files:

- `.env` — Compose interpolation values such as image references, protected file paths, persistent database path, gateway network name, and the approved private worker DNS resolver address (`MONITOR_DNS_SERVER`).
- `monitor.env` — Django, worker, platform integration, and GoreeCloud Notify producer configuration.
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

The validator requires no published ports, no privileged/host-network/device/Docker-socket access, no added capabilities, read-only application root filesystems, `cap_drop: ALL`, `no-new-privileges`, an internal database network, the approved external gateway network, a persistent PostgreSQL bind mount, a digest-pinned PostgreSQL image, and exactly one private IPv4 DNS resolver on the worker only.

## Target acceptance required before activation

Before Monitor can become production monitoring authority, verify and record:

1. supported Docker Engine and Compose versions on `goreecloud-vps-01`;
2. authoritative `/srv/docker/` paths, ownership, permissions, capacity, and backup scope;
3. exact GoreeCloud Gateway network identity and backend reachability;
4. zero host-published Monitor/database ports;
5. the approved private Monitor hostname and private DNS record;
6. Gateway configuration validation, trusted certificate, private access, and denial from unauthorized sources;
7. NetBird policy for the web path and every worker monitoring destination, plus proof that the exact worker topology resolves private GoreeCloud targets through the approved private resolver rather than public DNS;
8. accepted GoreeCloud Notify deployment plus a dedicated least-privilege Monitor producer token;
9. target `targetpreflight` output with no blocking findings;
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

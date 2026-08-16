# Production Deployment Candidate

This document describes the source-controlled production topology for GoreeCloud Monitor. It is an acceptance plan, not authorization to deploy or retire Uptime Kuma.

## Intended host layout

The target GoreeCloud model keeps active Compose and protected environment files in the service stack and PostgreSQL data in the authoritative Docker data structure:

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
- `web` uses the immutable application image, a read-only root filesystem, dropped capabilities, `no-new-privileges`, and a bounded `/tmp` tmpfs. It joins only `backend` and the approved external Caddy network.
- `worker` uses the same application image and application hardening. It joins `backend` for PostgreSQL and the approved proxy network for the monitoring/notification paths that are later authorized there.
- No service uses privileged mode, host networking, a Docker socket, or an added Linux capability.
- No Monitor application or PostgreSQL port is published on the host. Caddy is the intended private HTTPS gateway.

The external proxy network name is supplied at deployment through `CADDY_NETWORK`; the source repository does not hard-code a future runtime network identity beyond the sanitized example. The deployment does not assign the old Uptime Kuma monitoring source address. Any later reuse of an address such as the previously modeled `172.19.0.50` must occur only after conflict-free live validation and an explicit cutover decision.

## Image identity

`GOREECLOUD_MONITOR_IMAGE` must be a unique, traceable application image reference built from the accepted GoreeCloud Monitor revision. `latest` is rejected by the production contract validator.

`POSTGRES_IMAGE` must contain an exact tag **and** digest, for example:

```text
postgres:17.10-bookworm@sha256:<verified digest>
```

Resolve and record the digest during the target acceptance procedure; do not copy the example placeholder into production.

## Environment files

Production uses three purpose-specific files:

- `.env` — Compose interpolation values such as image references, protected file paths, persistent database path, and Caddy network name.
- `monitor.env` — Django, Monitor worker, Manager, and ntfy application configuration.
- `database.env` — PostgreSQL database name, username, password, and port.

The application services read `database.env` plus `monitor.env`; PostgreSQL reads only `database.env`. This avoids giving the database container unrelated Django or notification credentials and avoids duplicating the database password in multiple active files.

Use `deploy/production-stack.env.example`, `deploy/monitor.env.example`, and `deploy/database.env.example` only as sanitized templates. Active files remain protected infrastructure configuration and must never enter source control.

## Static assets and schema migration

Static assets are generated while the image is built. The application entrypoint performs no implicit migration or filesystem mutation.

Schema migration is explicit through the one-shot `migrate` service. `web` and `worker` start only after that service exits successfully. A failed migration therefore blocks application startup rather than allowing a new application revision to run against an uncertain schema.

## Source validation

Resolve the production Compose file and run the repository validator:

```bash
docker compose -f compose.production.yml config --format json \
  | python scripts/validate_production_compose.py
```

The validator requires, among other invariants, no published ports, no privileged/host-network/device/Docker-socket access, no added capabilities, read-only application root filesystems, `cap_drop: ALL`, `no-new-privileges`, an internal database network, an external proxy network, an explicit PostgreSQL data bind mount, and a digest-pinned PostgreSQL image.

## Target acceptance still required

A green source/CI production topology does not prove the target Infrastructure Services VM. Before deployment or cutover, separately verify:

1. the host's supported Docker Engine and Compose versions;
2. the authoritative `/srv/docker/` paths, ownership, permissions, capacity, and backup scope;
3. the exact Caddy network name and backend reachability;
4. zero host-published Monitor/database ports after container creation;
5. the selected private Monitor hostname and AdGuard Home rewrite;
6. Caddy configuration validation, trusted certificate, private NetBird access, and denial from unauthorized sources;
7. NetBird policies for the web path and every worker monitoring destination;
8. the dedicated ntfy write-only publisher identity and ACL;
9. target `targetpreflight` output;
10. target PostgreSQL backup and successful isolated restoration;
11. live Uptime Kuma export audit, paused import, manual resolution of warnings, and repeated parallel comparisons;
12. controlled DOWN/RECOVERED, maintenance, TLS-warning, and notification tests;
13. the unresolved ICMP/Ping coverage decision;
14. explicit rollback and Uptime Kuma retirement approval.

Until those items are evidenced, Uptime Kuma remains authoritative.

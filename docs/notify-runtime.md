# GoreeCloud Monitor → GoreeCloud Notify Runtime Integration

## Status

This document defines the source-level GoreeCloud Monitor notification-publishing candidate after the permanent retirement of ntfy from `goreecloud-vps-01` on September 18, 2026.

GoreeCloud Notify is now the only supported Monitor notification-delivery integration in this source candidate. The integration remains disabled by default until an accepted GoreeCloud Notify production deployment, dedicated producer identity, target recovery evidence, and end-to-end acceptance exist.

This source layer does **not** by itself authorize Monitor production activation or establish Notify production acceptance.

## Runtime boundary

A Monitor check result is committed transactionally before publication. When that committed result produces a DOWN, RECOVERED, or DEGRADED transition, the worker invokes the GoreeCloud Notify publisher with a replay identity derived from the persisted CheckResult.

GoreeCloud Notify is a delivery system, not the authority for monitored state. Publication success or failure must never alter the Monitor state transition that has already been committed.

## Protected configuration

The publisher is feature-gated with:

- `MONITOR_NOTIFY_ENABLED=true`
- `GOREECLOUD_NOTIFY_BASE_URL=https://...`
- `GOREECLOUD_NOTIFY_TOKEN=<dedicated producer credential>`

Bounded retry controls:

- `MONITOR_NOTIFY_MAX_ATTEMPTS` — default 3, bounded to 1–5.
- `MONITOR_NOTIFY_RETRY_BACKOFF_SECONDS` — default 0.25 seconds.
- `MONITOR_NOTIFY_TIMEOUT_SECONDS` — default 10 seconds, bounded to 1–30 seconds.
- `MONITOR_NOTIFICATION_OUTBOX_RETENTION_DAYS` — default 30 days, bounded to 1–365; applies only to already-delivered outbox metadata, never pending delivery records.

All seven Notify producer settings belong in the protected worker-only environment file referenced by `MONITOR_WORKER_ENV_FILE`. Production Compose loads that file only into `worker`; the shared `monitor.env`, `web`, and `migrate` environments must not contain `MONITOR_NOTIFY_ENABLED`, `GOREECLOUD_NOTIFY_BASE_URL`, `GOREECLOUD_NOTIFY_TOKEN`, or the Notify retry/outbox controls. The bearer token must not be committed, rendered in UI, placed in notification content, written to evidence artifacts, emitted in logs, or exposed to non-worker services.

Target preflight for Notify production acceptance runs in the worker, where the producer configuration is intentionally available. It fails closed when GoreeCloud Notify is disabled, incompletely configured, or configured with a non-HTTPS or credential-bearing endpoint.

## Worker routing identity

Production Compose maps only the Monitor worker's reviewed same-host private HTTPS names—`notify.goreecloud.com`, `adguard.goreecloud.com`, `health.goreecloud.com`, `dav.goreecloud.com`, and `memos.goreecloud.com`—to the approved Caddy proxy-network IPv4 supplied by `MONITOR_CADDY_GATEWAY_IP`. Notify still uses the HTTPS base URL `https://notify.goreecloud.com`, and monitor definitions keep their normal HTTPS hostnames, so certificate and hostname verification remain unchanged.

These mappings prevent the worker from reaching same-host private services through Docker's host-published HTTPS port. Same-host hairpin NAT can replace the worker's fixed proxy identity with the Docker bridge gateway before Caddy evaluates `remote_ip`; authorizing that shared gateway would weaken the least-privilege boundary. Routing the reviewed names directly to Caddy on the shared proxy network instead preserves the dedicated `MONITOR_WORKER_PROXY_IP` identity that Caddy is expected to authorize. Unreviewed or absent services, including the currently unprovisioned Research route, are not added to this routing set.

The mappings are deployment routing metadata, not credentials. They belong in protected/controlled Compose interpolation state rather than the Notify token configuration. Target acceptance must verify the live Caddy proxy address, each reviewed worker host resolution, Caddy-observed peer address, TLS verification, path-scoped authorization, and rejection of unrelated proxy-network sources.

## Payload minimization

The runtime sends only the bounded Monitor producer contract:

- `source`: `goreecloud-monitor`
- `channel`: `monitoring`
- bounded Monitor display label
- controlled transition summary
- controlled event title
- mapped severity

Target URLs, IP addresses, response bodies, raw exception text, stack traces, private monitoring configuration, request headers, credentials, producer tokens, and raw transition identities are outside the payload contract.

Current transition mapping:

- DOWN → critical outage event
- RECOVERED → normal recovery event
- DEGRADED → warning degraded-service event
- DEGRADED with the controlled TLS-expiry message → TLS_EXPIRING warning event

## Replay identity

Every persisted transition-producing check creates a CheckResult. The runtime derives its internal transition identity from:

- Monitor ID
- persisted CheckResult ID
- persisted `checked_at` timestamp

The raw identity is never sent. Monitor derives the wire key using the versioned `gcm-v1-` SHA-256 contract shared with GoreeCloud Notify.

Human-facing presentation fields are not part of replay identity. If content changes while a retry retains the same transition identity, Notify is expected to reject the altered content rather than create a second notification.

## Response and retry contract

The runtime accepts:

- `201 Created` as the first successful write.
- `200 OK` only when `Idempotency-Replayed: true` confirms an exact replay.

The runtime fails closed on:

- `409 Conflict` for idempotency-key/content mismatch;
- `200` without the explicit replay header;
- non-retryable rejected HTTP responses; and
- invalid local configuration or payload input.

Transport failures, HTTP `429`, and HTTP `5xx` responses may be retried up to the configured bounded attempt count. Every retry reuses the same payload and idempotency key. Redirects and environment proxy/credential inheritance are disabled.

## Durable outbox

Monitor now persists a `NotificationOutbox` record in the **same PostgreSQL transaction** that commits a transition-producing CheckResult and incident state. The record stores the minimized exact Notify payload and its opaque versioned idempotency key before any network delivery is attempted.

The worker drains due outbox records on every cycle, including cycles with no due monitors. A failed delivery remains pending with persisted attempt state and bounded exponential backoff. A successful first write or receiver-confirmed replay marks the record delivered. Target preflight fails closed while any durable notification record remains undelivered.

This closes the source-level process-loss gap that existed when publication began only after the database commit. It does **not** establish exactly-once delivery. A process may still terminate after Notify accepted a request but before Monitor records success; recovery therefore relies on replaying the same persisted idempotency key and on Notify's accepted idempotency contract to converge safely.

Production acceptance still requires live proof that a pending record survives worker/container restart, is replayed with the same payload/key, converges without duplicate notification fanout, and remains recoverable through PostgreSQL backup/restore. Delivered-outbox retention must also remain bounded by the approved production retention design.

## Observability and failure isolation

Operational events identify only the integration, transition state, bounded attempt count, replay status, response status where useful, and minimized failure reason/exception type. Monitor labels, raw transition identities, target details, credentials, and raw exception messages are not added to integration logs.

An unexpected Notify integration failure is observable but must not crash the monitoring loop after monitoring state has already been committed.

## Required acceptance before production activation

Production activation remains blocked until applicable evidence exists for:

- exact-revision Monitor and Notify target deployments;
- a dedicated least-privilege Notify producer credential stored only in the protected worker environment, with proof that web/migrate do not receive any Notify producer environment keys;
- receiver-side source registration and authorization;
- worker-only reviewed private HTTPS routing through the approved Caddy proxy address, including `notify.goreecloud.com`, with Caddy observing the fixed Monitor worker proxy identity rather than a shared Docker gateway;
- controlled first-write `201` delivery;
- controlled retry replay returning `200` with `Idempotency-Replayed: true` and no duplicate fanout;
- controlled changed-payload/same-key `409` rejection;
- representative DOWN, RECOVERED, DEGRADED, and TLS-expiry delivery and administrator receipt;
- live worker/container restart proof for the durable outbox, including same-key replay and no duplicate fanout;
- approved bounded retention for delivered outbox records;
- independent outage alerting that does not depend entirely on the Monitor → Notify chain;
- target backup/restore, live check, Wardveil Security, Privacy Shield, Everkeep, current Glaze UI, rollback, and production-approval evidence.

The retired ntfy service is historical/recovery context only and is not an active fallback path.

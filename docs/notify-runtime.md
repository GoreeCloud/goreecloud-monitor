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

The token belongs only in protected runtime configuration. It must not be committed, rendered in UI, placed in notification content, written to evidence artifacts, or emitted in logs.

Target preflight fails closed when GoreeCloud Notify is disabled, incompletely configured, or configured with a non-HTTPS or credential-bearing endpoint.

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

## Durability limitation

This source layer provides bounded **in-process** retry only. It is not a durable notification outbox.

Monitor commits state and the CheckResult before publication begins. If the worker process or host terminates after that commit but before Notify publication is confirmed, no persisted pending-publication record currently guarantees later replay.

Therefore this implementation must not be described as exactly-once delivery or crash-durable at-least-once delivery. Production acceptance must explicitly decide whether a durable outbox/replay mechanism is mandatory; until that decision and the remaining live acceptance gates are closed, this remains a release-candidate integration.

## Observability and failure isolation

Operational events identify only the integration, transition state, bounded attempt count, replay status, response status where useful, and minimized failure reason/exception type. Monitor labels, raw transition identities, target details, credentials, and raw exception messages are not added to integration logs.

An unexpected Notify integration failure is observable but must not crash the monitoring loop after monitoring state has already been committed.

## Required acceptance before production activation

Production activation remains blocked until applicable evidence exists for:

- exact-revision Monitor and Notify target deployments;
- a dedicated least-privilege Notify producer credential;
- receiver-side source registration and authorization;
- controlled first-write `201` delivery;
- controlled retry replay returning `200` with `Idempotency-Replayed: true` and no duplicate fanout;
- controlled changed-payload/same-key `409` rejection;
- representative DOWN, RECOVERED, DEGRADED, and TLS-expiry delivery and administrator receipt;
- an explicit decision on crash-durable outbox/replay semantics;
- independent outage alerting that does not depend entirely on the Monitor → Notify chain;
- target backup/restore, live check, Wardveil Security, Privacy Shield, Everkeep, current Glaze UI, rollback, and production-approval evidence.

The retired ntfy service is historical/recovery context only and is not an active fallback path.

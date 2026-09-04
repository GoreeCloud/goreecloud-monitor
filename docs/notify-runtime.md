# GoreeCloud Monitor → GoreeCloud Notify Runtime Integration

## Status

This document defines the source-level, disabled-by-default runtime integration candidate between GoreeCloud Monitor and GoreeCloud Notify.

The receiving Notify idempotency contract is authoritative in `GoreeCloud/goreecloud-notify` main at merge commit `42a4ce1affee489423ca0ad42635f708c36a9af8`. Monitor's source producer replay contract is authoritative in this repository at merge commit `529174a3a9bc62415f3efbf1311a13bc1a8f9a88`.

This runtime layer does **not** authorize production activation, notification cutover, Uptime Kuma retirement, or ntfy removal. Uptime Kuma remains the production monitoring authority and ntfy remains Monitor's active notification path until separate live acceptance and cutover approval are complete.

## Runtime boundary

A Monitor check result is applied transactionally first. If that committed result produces a DOWN, RECOVERED, or DEGRADED transition, the worker then invokes two independent publication paths:

1. the existing ntfy publisher; and
2. the GoreeCloud Notify publisher when `MONITOR_NOTIFY_ENABLED=true`.

The two publishers run concurrently after Monitor state has been committed. A GoreeCloud Notify integration failure is logged through the minimized operational event contract and must not roll back or invalidate monitoring truth.

GoreeCloud Notify is a delivery system, not the authority for monitored state. Notify publication success must never be interpreted as evidence that the monitored service is healthy.

## Feature gate and protected configuration

The new path is disabled by default.

Required configuration when enabled:

- `MONITOR_NOTIFY_ENABLED=true`
- `GOREECLOUD_NOTIFY_BASE_URL=https://...`
- `GOREECLOUD_NOTIFY_TOKEN=<dedicated producer credential>`

Optional bounded retry controls:

- `MONITOR_NOTIFY_MAX_ATTEMPTS` — default 3, bounded to 1–5
- `MONITOR_NOTIFY_RETRY_BACKOFF_SECONDS` — default 0.25 seconds
- `MONITOR_NOTIFY_TIMEOUT_SECONDS` — default 10 seconds, bounded to 1–30 seconds

The token belongs only in protected runtime configuration. It must not be committed, rendered in UI, placed in notification content, written to evidence artifacts, or emitted in logs.

Target preflight fails closed if the feature is enabled without both the base URL and token, or when the Notify base URL is not a credential-free HTTPS origin. When the feature is disabled, preflight reports a non-blocking `notify-disabled` warning so the migration state remains visible.

## Payload minimization

The runtime publisher sends only the existing bounded Monitor producer contract:

- `source`: `goreecloud-monitor`
- `channel`: `monitoring`
- bounded Monitor display label
- controlled transition summary
- controlled event title
- mapped severity

Target URLs, IP addresses, response bodies, raw exception text, stack traces, private monitoring configuration, request headers, credentials, producer tokens, raw transition identities, and recovery material are outside the payload contract.

Current runtime transition mapping is:

- DOWN → critical outage event
- RECOVERED → normal recovery event
- DEGRADED → warning degraded-service event
- DEGRADED with the controlled TLS-expiry message → TLS_EXPIRING warning event

The source-level JavaScript adapter also defines `HEARTBEAT_MISSED`, but the Python monitoring state machine currently represents a stale push heartbeat through the ordinary DOWN transition. Runtime support must not claim heartbeat-specific event classification until that distinction is implemented and validated end to end.

## Replay identity

Every persisted transition-producing check creates a `CheckResult`. The runtime constructs an internal transition identity from:

- Monitor ID
- persisted CheckResult ID
- persisted `checked_at` timestamp

The raw identity is never sent. Monitor derives the wire key using the same versioned algorithm as `services/notify-producer/index.mjs`:

`gcm-v1-` + SHA-256(`goreecloud-monitor\0v1\0` + event type + `\0` + transition identity)

Including the persisted timestamp as well as the numeric IDs avoids silent replay-key reuse if a database restore or rollback later causes numeric primary keys to be reused.

Human-facing presentation fields such as the monitor label are not part of replay identity. If presentation content changes while a retry retains the same transition identity, Notify must reject the altered content with `409 Conflict` rather than create another notification.

## Response and retry contract

The runtime accepts:

- `201 Created` as the first successful write.
- `200 OK` only when `Idempotency-Replayed: true` confirms an exact replay of the original resource.

The runtime fails closed on:

- `409 Conflict` for idempotency-key/content mismatch;
- a `200` response without the explicit replay header;
- non-retryable rejected HTTP responses; and
- invalid local contract/configuration input.

Transport failures, HTTP `429`, and HTTP `5xx` responses may be retried up to the configured bounded attempt count. Every retry reuses the exact same payload and idempotency key.

Redirects are disabled and environment proxy/`.netrc` credential inheritance is disabled with `trust_env=False`.

## Durability limitation

This source layer provides bounded **in-process** retry only. It is not a durable notification outbox.

Monitor commits state and the `CheckResult` before starting network publication. If the worker process or host terminates after that commit but before Notify publication is confirmed, this implementation does not currently persist a pending-publication record that a later process can resume.

Therefore this layer must not be described as exactly-once delivery or crash-durable at-least-once delivery. Notify's idempotency semantics make retries safe when Monitor has the same transition identity, but a later durable outbox/replay mechanism is still required if production acceptance requires recovery from process-loss windows without operator intervention.

This limitation is intentional and explicit so a source-level runtime bridge can be validated without adding a new database migration or durable delivery queue to the current Monitor migration rehearsal boundary.

## Observability and failure isolation

Operational events identify only the integration, transition state, bounded attempt count, replay status, response status where useful, and minimized failure reason/exception type. Monitor labels, raw transition identities, target details, credentials, and raw exception messages are not added to integration logs.

The secondary GoreeCloud Notify path is isolated from monitoring execution. Expected HTTP/configuration failures and unexpected integration exceptions are converted to minimized failure events rather than propagating through the worker after monitoring state has already been committed. Task cancellation is not deliberately suppressed.

## Required acceptance before production activation

Production activation remains blocked until all applicable evidence exists, including:

- exact-revision target deployment of this runtime implementation;
- a dedicated least-privilege Notify producer credential;
- receiver-side source registration/authorization evidence;
- controlled first-write `201` delivery;
- controlled uncertain-response/retry replay returning `200` with `Idempotency-Replayed: true` and no duplicate Delivery fanout;
- controlled changed-payload/same-key `409` rejection;
- representative DOWN, RECOVERED, DEGRADED, and TLS-expiry delivery and administrator receipt;
- confirmation that ntfy and Notify parallel publication does not change Monitor state or Uptime Kuma authority;
- rollback evidence with Notify disabled again;
- an explicit decision on whether crash-durable publication/outbox semantics are required before cutover;
- the remaining Monitor live parity, platform-system, recovery, accessibility, rollback, and explicit cutover gates.

Until those gates are accepted, `MONITOR_NOTIFY_ENABLED` must remain false in the production Monitor runtime.

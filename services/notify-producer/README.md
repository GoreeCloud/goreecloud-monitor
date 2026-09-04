# GoreeCloud Monitor Notify Producer

This package defines Monitor's bounded producer contract for GoreeCloud Notify.

It converts five monitoring event classes into the established Notify `POST /api/v1/notifications` contract:

- `DOWN`
- `RECOVERED`
- `DEGRADED`
- `TLS_EXPIRING`
- `HEARTBEAT_MISSED`

The adapter intentionally sends only a Monitor-owned display label and minimized summary. Target URLs, IP addresses, raw diagnostics, stack traces, credentials, tokens, private monitoring configuration, and reusable recovery material are outside this contract.

The Notify endpoint must use HTTPS. Authentication remains a separately provisioned Notify producer token and is sent only in the Authorization header. Tokens must never be committed to this repository or copied into notification bodies.

## Retry identity

Every publication requires a stable `transitionId` supplied by Monitor's transition lifecycle. The adapter derives a deterministic, versioned, opaque `Idempotency-Key` from the event type and transition identifier before calling Notify.

The raw transition identifier is not sent as notification content and is not embedded verbatim in the idempotency header. Human-facing presentation fields such as the monitor display label are deliberately excluded from replay identity. A label rename between attempts therefore keeps the same key; if the payload changes under that key, Notify is expected to reject the ambiguous replay rather than create a duplicate.

A missing or empty transition identifier fails closed before the network request. Producers must not substitute timestamps generated at send time, random retry IDs, or other attempt-specific values, because those would defeat replay convergence.

## Python runtime candidate

`src/monitoring/notifications.py` contains a disabled-by-default Python implementation of this contract for the Monitor worker. It derives replay identity from the persisted transition-producing `CheckResult`, performs bounded in-process retries with the same idempotency key, accepts first-write `201`, accepts replay `200` only with `Idempotency-Replayed: true`, and fails closed on `409` conflicts.

The current Python state-transition path emits DOWN, RECOVERED, DEGRADED, and controlled TLS-expiry events. The contract-level `HEARTBEAT_MISSED` class remains reserved for a future runtime distinction; a stale push heartbeat currently enters the normal DOWN transition path.

The Python implementation is not a durable outbox. A process-loss window after Monitor state commit but before successful publication is still possible. See `docs/notify-runtime.md` for the exact durability, privacy, configuration, and acceptance boundary.

## Authority and acceptance

Monitor remains authoritative for monitoring state; Notify is authoritative for notification persistence and delivery. Publication success is not evidence that a monitored service is healthy, and Notify must not be the only outage alert path for Notify itself.

The runtime path remains disabled by default and does not authorize migration from ntfy. Uptime Kuma and the existing production notification path remain unchanged until cross-repository runtime validation, representative first-write/replay/conflict testing, delivery receipt, rollback evidence, the durability requirement decision, and explicit cutover approval are complete.

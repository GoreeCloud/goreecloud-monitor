# GoreeCloud Monitor Notify Producer

This package defines Monitor's bounded producer adapter for GoreeCloud Notify.

It converts five monitoring transition classes into the existing Notify `POST /api/v1/notifications` contract:

- `DOWN`
- `RECOVERED`
- `DEGRADED`
- `TLS_EXPIRING`
- `HEARTBEAT_MISSED`

The adapter intentionally sends only a Monitor-owned display label and minimized summary. Target URLs, IP addresses, raw diagnostics, stack traces, credentials, tokens, private monitoring configuration, and reusable recovery material are outside this contract.

The Notify endpoint must use HTTPS. Authentication remains a separately provisioned Notify producer token and is sent only in the Authorization header. Tokens must never be committed to this repository or copied into notification bodies.

This source package is not wired into the production Monitor runtime and does not authorize migration from ntfy. Uptime Kuma and the existing production notification path remain unchanged until runtime validation and explicit cutover approval are complete.

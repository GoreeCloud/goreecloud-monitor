# GoreeCloud Monitor

GoreeCloud Monitor is the native GoreeCloud availability, endpoint-health, heartbeat, certificate, incident, and recovery monitoring application.

This repository is under active development. Uptime Kuma remains the current production monitoring platform until GoreeCloud Monitor completes parallel validation and an explicit production cutover.

## Integrations

- `services/sentry-mcp` — authenticated, read-only Sentry MCP connector for approved AI/MCP clients. The Sentry API token remains server-side as a Cloudflare Worker secret; issue and event results are normalized and privacy-redacted before they leave the connector.
- `services/notify-producer` — bounded GoreeCloud Notify producer adapter for privacy-minimized monitoring transitions. It supports outage, recovery, degraded-service, certificate-attention, and missed-heartbeat notifications without exporting target addresses, raw diagnostics, credentials, or private monitoring configuration. This adapter is source-only until runtime validation and explicit notification-path cutover are completed.

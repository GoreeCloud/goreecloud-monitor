# Current mainline integrations

GoreeCloud Monitor retains two independently bounded integrations while the native monitoring application proceeds through migration acceptance.

- `services/sentry-mcp` is the authenticated, read-only Sentry MCP connector for approved AI/MCP clients. The Sentry API token remains server-side as a Cloudflare Worker secret; issue and event results are normalized and privacy-redacted before they leave the connector.
- `services/notify-producer` is the bounded GoreeCloud Notify producer adapter for privacy-minimized monitoring transitions. It supports outage, recovery, degraded-service, certificate-attention, and missed-heartbeat notifications without exporting target addresses, raw diagnostics, credentials, or private monitoring configuration. Runtime validation and explicit notification-path migration remain required.

These integrations do not change Uptime Kuma's current production authority or authorize production cutover.

# GoreeCloud Monitor

GoreeCloud Monitor is the native GoreeCloud availability, endpoint-health, heartbeat, certificate, incident, and recovery monitoring application.

This repository is under active development. Uptime Kuma remains the current production monitoring platform until GoreeCloud Monitor completes parallel validation and an explicit production cutover.

## Integrations

- `services/sentry-mcp` — authenticated, read-only Sentry MCP connector for approved AI/MCP clients. The Sentry API token remains server-side as a Cloudflare Worker secret; issue and event results are normalized and privacy-redacted before they leave the connector.

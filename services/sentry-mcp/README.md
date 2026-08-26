# GoreeCloud Sentry MCP

GoreeCloud Sentry MCP is an authenticated, read-only Model Context Protocol service for GoreeCloud Monitor. It lets approved MCP clients query the configured GoreeCloud Sentry project without ever receiving the Sentry API token.

## Current status

- Production Worker deployed: `https://goreecloud-sentry-mcp.goreecloud.workers.dev`
- Public health endpoint: `https://goreecloud-sentry-mcp.goreecloud.workers.dev/health`
- `/health` validated with HTTP 200 and the expected service/version payload after production secret provisioning.
- `npm run typecheck` passes with zero TypeScript errors.
- Cloudflare KV namespace `OAUTH_KV` is created and bound.
- Sentry organization: `goreecloud-01`
- Sentry project: `goreecloud-monitor`
- GitHub OAuth App is registered for the production Worker callback.
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, and `SENTRY_AUTH_TOKEN` are provisioned as Cloudflare Worker secrets; their values are not stored in Git or documentation.
- Latest validated production deployment in this setup session: Worker version `ba2151cb-3def-47bb-8e3f-8f7776ed7bd2`.
- Authenticated MCP Inspector connection validated successfully: OAuth completed, `initialize` succeeded, the initialized notification was accepted, and `tools/list` succeeded over Streamable HTTP.
- Remaining validation: call `sentry_health` and confirm the configured Sentry project is reachable through the complete authenticated MCP path.

## Security model

- `SENTRY_AUTH_TOKEN` exists only as a Cloudflare Worker secret.
- The MCP endpoint is protected by OAuth 2.1 using `@cloudflare/workers-oauth-provider`.
- Public MCP clients are restricted to S256 PKCE; legacy plain PKCE is disabled.
- The OAuth provider supplies MCP client metadata discovery and rotating refresh-token handling.
- Human authentication is delegated to GitHub OAuth and restricted by `ALLOWED_GITHUB_LOGINS`.
- The GitHub access token is used only long enough to identify the user and is not stored in MCP authorization props.
- Sentry access is read-only. No tool resolves, deletes, assigns, mutates, or configures Sentry data.
- Tool output redacts email addresses and IP addresses and excludes raw stack traces, cookies, authorization headers, request bodies, and URL query strings.
- OAuth state is short-lived and bound to the browser with an HttpOnly, Secure, SameSite cookie.

## MCP tools

- `sentry_health` — verify the configured Sentry project is reachable.
- `list_sentry_issues` — list issues with environment, time-range, limit, and Sentry query filters.
- `get_sentry_issue` — retrieve a safe issue summary.
- `list_sentry_issue_events` — list recent issue events.
- `get_sentry_event` — retrieve a safe event summary without raw stack traces or sensitive request data.

## Required configuration

Non-secret Worker variables:

- `SENTRY_ORG=goreecloud-01`
- `SENTRY_PROJECT=goreecloud-monitor`
- `SENTRY_BASE_URL=https://sentry.io`
- `ALLOWED_GITHUB_LOGINS=GoreeCloud`

Worker secrets:

- `SENTRY_AUTH_TOKEN`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`

OAuth storage:

- Cloudflare KV binding: `OAUTH_KV`

## Deployment

From `services/sentry-mcp`:

```bash
npm install
npm run typecheck
npm run deploy
```

The deployed Worker origin is:

```text
https://goreecloud-sentry-mcp.goreecloud.workers.dev
```

The protected remote MCP endpoint is:

```text
https://goreecloud-sentry-mcp.goreecloud.workers.dev/mcp
```

The public health endpoint is:

```text
https://goreecloud-sentry-mcp.goreecloud.workers.dev/health
```

## GitHub OAuth App

Create a GitHub OAuth App with these values:

- Application name: `GoreeCloud Sentry MCP`
- Homepage URL: `https://goreecloud-sentry-mcp.goreecloud.workers.dev/`
- Application description: `Secure GitHub identity provider for the GoreeCloud Sentry MCP connector.`
- Authorization callback URL: `https://goreecloud-sentry-mcp.goreecloud.workers.dev/callback`
- Device Flow: disabled
- Expiring user access tokens: enabled
- Wildcard callback matching: disabled if presented

The OAuth App is used only for human identity verification. Repository permissions are not required by this connector.

## Secret provisioning

Set secrets interactively after the OAuth App exists. Never place secret values in Git, `.env.example`, documentation, screenshots, or chat.

```bash
npx wrangler secret put GITHUB_CLIENT_ID
npx wrangler secret put GITHUB_CLIENT_SECRET
npx wrangler secret put SENTRY_AUTH_TOKEN
```

Production secret provisioning is complete. Secret values remain server-side in Cloudflare and are intentionally omitted from this documentation.

## Authenticated production validation

Use the official MCP Inspector to validate the production OAuth and Sentry path:

```bash
npx @modelcontextprotocol/inspector@latest
```

In the Inspector:

1. Configure a Streamable HTTP server at `https://goreecloud-sentry-mcp.goreecloud.workers.dev/mcp`.
2. Connect and complete the OAuth flow through GitHub using an account allowed by `ALLOWED_GITHUB_LOGINS`.
3. Confirm the MCP `initialize` exchange succeeds and the server reports Connected.
4. Confirm `tools/list` succeeds and the five GoreeCloud Sentry tools are present.
5. Call `sentry_health` and confirm it can reach the configured `goreecloud-monitor` Sentry project.

Steps 1 through 4 have been validated successfully against the production Worker. Step 5 remains the final end-to-end Sentry API validation.

The protected `/mcp` URL is a protocol endpoint and is not intended to be tested by opening it directly in a normal browser.

## ChatGPT and MCP clients

When custom MCP apps are available for the account or workspace, configure the deployed `/mcp` endpoint with OAuth authentication. The authorization flow redirects through this Worker to GitHub, verifies the approved GitHub login, and returns an MCP access token. The MCP client never receives `SENTRY_AUTH_TOKEN`.

The Worker is a standard remote MCP server and can also be tested with MCP Inspector or another compatible MCP client.

## Local development

Copy `.env.example` to `.dev.vars` and populate it locally. Never commit `.dev.vars`.

```bash
npm install
npm run dev
```

For local development, use a local KV resource rather than the production `OAUTH_KV` namespace unless remote-state testing is explicitly required. Use MCP Inspector against `http://localhost:8787/mcp` or the port reported by Wrangler.

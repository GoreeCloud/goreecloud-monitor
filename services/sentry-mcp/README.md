# GoreeCloud Sentry MCP

GoreeCloud Sentry MCP is a small authenticated, read-only Model Context Protocol service for GoreeCloud Monitor. It lets approved MCP clients query a configured Sentry project without ever receiving the Sentry API token.

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

- `SENTRY_ORG`
- `SENTRY_PROJECT`
- `SENTRY_BASE_URL` (defaults to `https://sentry.io`)
- `ALLOWED_GITHUB_LOGINS` (comma-separated; keep this narrow)

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
npx wrangler kv namespace create OAUTH_KV
```

Copy the returned KV namespace ID into `wrangler.jsonc`, then set the non-secret Sentry org/project values and the allowed GitHub login.

Create a GitHub OAuth App with:

- Homepage URL: the Worker origin, for example `https://goreecloud-sentry-mcp.<account>.workers.dev`
- Authorization callback URL: the Worker origin plus `/callback`

Set secrets interactively. Do not put secret values in Git, `.env.example`, documentation, screenshots, or chat:

```bash
npx wrangler secret put SENTRY_AUTH_TOKEN
npx wrangler secret put GITHUB_CLIENT_ID
npx wrangler secret put GITHUB_CLIENT_SECRET
```

Deploy:

```bash
npm run deploy
```

The remote MCP endpoint is:

```text
https://<worker-host>/mcp
```

## ChatGPT

When custom MCP apps are available for the account/workspace, create a custom app using the deployed `/mcp` endpoint and select OAuth authentication. The authorization flow redirects through this Worker to GitHub, verifies the approved GitHub login, and returns an MCP access token. ChatGPT never sees `SENTRY_AUTH_TOKEN`.

As of 2026-08-26, direct custom MCP app availability depends on the ChatGPT plan/workspace. The Worker remains a standard remote MCP server and can also be tested with MCP Inspector or another compatible MCP client.

## Local development

Copy `.env.example` to `.dev.vars` and populate it locally. Never commit `.dev.vars`.

```bash
npm install
npm run dev
```

Use the MCP Inspector against `http://localhost:8787/mcp` (or the port reported by Wrangler).

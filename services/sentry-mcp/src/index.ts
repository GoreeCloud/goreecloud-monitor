import { env as workerEnv } from "cloudflare:workers";
import { OAuthProvider, type AuthRequest, type OAuthHelpers } from "@cloudflare/workers-oauth-provider";
import { McpServer } from "@modelcontextprotocol/server";
import { createMcpHandler } from "agents/mcp/server";
import { z } from "zod";
import {
  eventDetail,
  healthCheck,
  issueDetail,
  issueEvents,
  listIssues,
  type SentryEnv
} from "./sentry";

interface Env extends SentryEnv {
  OAUTH_KV: KVNamespace;
  OAUTH_PROVIDER: OAuthHelpers;
  GITHUB_CLIENT_ID: string;
  GITHUB_CLIENT_SECRET: string;
  ALLOWED_GITHUB_LOGINS: string;
}

type AuthProps = {
  login: string;
  name?: string | null;
};

const STATE_PREFIX = "github-oauth-state:";
const STATE_TTL_SECONDS = 600;
const STATE_COOKIE = "__Host-goree_sentry_oauth_state";

function getEnv(): Env {
  return workerEnv as unknown as Env;
}

function textResult(value: unknown) {
  return {
    content: [{ type: "text" as const, text: JSON.stringify(value, null, 2) }]
  };
}

function errorResult(error: unknown) {
  const message = error instanceof Error ? error.message : "Unknown connector error";
  return {
    isError: true,
    content: [{ type: "text" as const, text: message }]
  };
}

function createServer() {
  const server = new McpServer({
    name: "GoreeCloud Sentry",
    version: "0.1.0"
  });

  server.registerTool(
    "sentry_health",
    {
      description: "Verify the GoreeCloud Sentry connector can reach the configured Sentry project. Read-only.",
      inputSchema: {}
    },
    async () => {
      try {
        return textResult(await healthCheck(getEnv()));
      } catch (error) {
        return errorResult(error);
      }
    }
  );

  server.registerTool(
    "list_sentry_issues",
    {
      description: "List Sentry issues for the configured GoreeCloud project, newest first. Read-only; PII is redacted.",
      inputSchema: {
        environment: z.string().min(1).max(64).optional().describe("Sentry environment, default prod"),
        timeRange: z.string().regex(/^\d+[smhwd]$/).optional().describe("Sentry stats period such as 24h or 7d"),
        limit: z.number().int().min(1).max(50).optional().describe("Maximum issues, default 20"),
        query: z.string().max(500).optional().describe("Sentry issue search query, default is:unresolved")
      }
    },
    async (args) => {
      try {
        return textResult(await listIssues(getEnv(), args));
      } catch (error) {
        return errorResult(error);
      }
    }
  );

  server.registerTool(
    "get_sentry_issue",
    {
      description: "Get read-only details for a Sentry issue by numeric issue ID. PII is redacted.",
      inputSchema: {
        issueId: z.string().min(1).max(64)
      }
    },
    async ({ issueId }) => {
      try {
        return textResult(await issueDetail(getEnv(), issueId));
      } catch (error) {
        return errorResult(error);
      }
    }
  );

  server.registerTool(
    "list_sentry_issue_events",
    {
      description: "List recent events for a Sentry issue. Read-only; stack traces and sensitive request data are not returned.",
      inputSchema: {
        issueId: z.string().min(1).max(64),
        environment: z.string().min(1).max(64).optional(),
        timeRange: z.string().regex(/^\d+[smhwd]$/).optional(),
        limit: z.number().int().min(1).max(50).optional()
      }
    },
    async ({ issueId, ...args }) => {
      try {
        return textResult(await issueEvents(getEnv(), issueId, args));
      } catch (error) {
        return errorResult(error);
      }
    }
  );

  server.registerTool(
    "get_sentry_event",
    {
      description: "Get a safe read-only Sentry event summary by event ID. Raw stack traces, cookies, authorization headers, and request bodies are excluded.",
      inputSchema: {
        eventId: z.string().min(1).max(128)
      }
    },
    async ({ eventId }) => {
      try {
        return textResult(await eventDetail(getEnv(), eventId));
      } catch (error) {
        return errorResult(error);
      }
    }
  );

  return server;
}

const mcpHandler = createMcpHandler(createServer);

function parseCookies(request: Request): Record<string, string> {
  const header = request.headers.get("cookie") || "";
  const cookies: Record<string, string> = {};
  for (const pair of header.split(";")) {
    const index = pair.indexOf("=");
    if (index < 0) continue;
    cookies[pair.slice(0, index).trim()] = decodeURIComponent(pair.slice(index + 1).trim());
  }
  return cookies;
}

function allowedLogin(env: Env, login: string): boolean {
  const allowed = new Set(
    (env.ALLOWED_GITHUB_LOGINS || "")
      .split(",")
      .map((value) => value.trim().toLowerCase())
      .filter(Boolean)
  );
  return allowed.size > 0 && allowed.has(login.toLowerCase());
}

async function handleAuthorize(request: Request, env: Env): Promise<Response> {
  const oauthRequest = await env.OAUTH_PROVIDER.parseAuthRequest(request);
  if (!oauthRequest.clientId) return new Response("Invalid client", { status: 400 });

  const state = crypto.randomUUID().replaceAll("-", "");
  await env.OAUTH_KV.put(`${STATE_PREFIX}${state}`, JSON.stringify(oauthRequest), {
    expirationTtl: STATE_TTL_SECONDS
  });

  const github = new URL("https://github.com/login/oauth/authorize");
  github.searchParams.set("client_id", env.GITHUB_CLIENT_ID);
  github.searchParams.set("redirect_uri", new URL("/callback", request.url).toString());
  github.searchParams.set("scope", "read:user");
  github.searchParams.set("state", state);

  const headers = new Headers({ Location: github.toString() });
  headers.append(
    "Set-Cookie",
    `${STATE_COOKIE}=${encodeURIComponent(state)}; Max-Age=${STATE_TTL_SECONDS}; Path=/; Secure; HttpOnly; SameSite=Lax`
  );
  return new Response(null, { status: 302, headers });
}

async function exchangeGitHubCode(env: Env, request: Request, code: string): Promise<string> {
  const response = await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "User-Agent": "GoreeCloud-Sentry-MCP/0.1"
    },
    body: JSON.stringify({
      client_id: env.GITHUB_CLIENT_ID,
      client_secret: env.GITHUB_CLIENT_SECRET,
      code,
      redirect_uri: new URL("/callback", request.url).toString()
    })
  });

  if (!response.ok) throw new Error("GitHub OAuth token exchange failed.");
  const body = await response.json() as { access_token?: string; error?: string };
  if (!body.access_token) throw new Error(`GitHub OAuth failed${body.error ? `: ${body.error}` : "."}`);
  return body.access_token;
}

async function getGitHubUser(token: string): Promise<{ login: string; name?: string | null }> {
  const response = await fetch("https://api.github.com/user", {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "GoreeCloud-Sentry-MCP/0.1",
      "X-GitHub-Api-Version": "2022-11-28"
    }
  });
  if (!response.ok) throw new Error("Unable to verify GitHub identity.");
  const user = await response.json() as { login?: string; name?: string | null };
  if (!user.login) throw new Error("GitHub did not return a login.");
  return { login: user.login, name: user.name };
}

async function handleCallback(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const cookieState = parseCookies(request)[STATE_COOKIE];
  if (!code || !state || !cookieState || state !== cookieState) {
    return new Response("Invalid OAuth callback state.", { status: 400 });
  }

  const key = `${STATE_PREFIX}${state}`;
  const stored = await env.OAUTH_KV.get(key);
  await env.OAUTH_KV.delete(key);
  if (!stored) return new Response("OAuth request expired.", { status: 400 });

  let oauthRequest: AuthRequest;
  try {
    oauthRequest = JSON.parse(stored) as AuthRequest;
  } catch {
    return new Response("Invalid OAuth request state.", { status: 400 });
  }

  const githubToken = await exchangeGitHubCode(env, request, code);
  const user = await getGitHubUser(githubToken);
  if (!allowedLogin(env, user.login)) {
    return new Response("This GitHub account is not authorized for the GoreeCloud Sentry connector.", { status: 403 });
  }

  const props: AuthProps = { login: user.login, name: user.name };
  const { redirectTo } = await env.OAUTH_PROVIDER.completeAuthorization({
    request: oauthRequest,
    userId: user.login,
    metadata: { label: `GoreeCloud Sentry — ${user.login}` },
    scope: oauthRequest.scope,
    props
  });

  const headers = new Headers({ Location: redirectTo });
  headers.append("Set-Cookie", `${STATE_COOKIE}=; Max-Age=0; Path=/; Secure; HttpOnly; SameSite=Lax`);
  return new Response(null, { status: 302, headers });
}

const defaultHandler = {
  async fetch(request: Request, envUnknown: unknown): Promise<Response> {
    const env = envUnknown as Env;
    const url = new URL(request.url);

    if (url.pathname === "/authorize" && request.method === "GET") {
      return handleAuthorize(request, env);
    }
    if (url.pathname === "/callback" && request.method === "GET") {
      try {
        return await handleCallback(request, env);
      } catch (error) {
        console.error("OAuth callback failed", error instanceof Error ? error.message : "unknown error");
        return new Response("Authentication failed.", { status: 500 });
      }
    }
    if (url.pathname === "/health") {
      return Response.json({ ok: true, service: "goreecloud-sentry-mcp", version: "0.1.0" });
    }
    if (url.pathname === "/") {
      return Response.json({
        service: "GoreeCloud Sentry MCP",
        mcp: "/mcp",
        authentication: "OAuth 2.1 via GitHub identity",
        access: "read-only Sentry API"
      });
    }

    return new Response("Not found", { status: 404 });
  }
};

export default new OAuthProvider({
  authorizeEndpoint: "/authorize",
  tokenEndpoint: "/oauth/token",
  clientRegistrationEndpoint: "/oauth/register",
  apiRoute: "/mcp",
  apiHandler: mcpHandler,
  defaultHandler
});

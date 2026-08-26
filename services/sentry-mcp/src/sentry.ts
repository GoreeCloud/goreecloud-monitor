export interface SentryEnv {
  SENTRY_AUTH_TOKEN: string;
  SENTRY_BASE_URL?: string;
  SENTRY_ORG: string;
  SENTRY_PROJECT: string;
}

type JsonObject = Record<string, unknown>;

const MAX_LIMIT = 50;
const EMAIL_RE = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi;
const IPV4_RE = /\b(?:\d{1,3}\.){3}\d{1,3}\b/g;
const IPV6_RE = /\b(?:[A-F0-9]{1,4}:){2,7}[A-F0-9]{1,4}\b/gi;

function baseUrl(env: SentryEnv): string {
  return (env.SENTRY_BASE_URL || "https://sentry.io").replace(/\/$/, "");
}

function requireConfig(env: SentryEnv): void {
  const missing = [
    ["SENTRY_AUTH_TOKEN", env.SENTRY_AUTH_TOKEN],
    ["SENTRY_ORG", env.SENTRY_ORG],
    ["SENTRY_PROJECT", env.SENTRY_PROJECT]
  ].filter(([, value]) => !value).map(([name]) => name);

  if (missing.length) {
    throw new Error(`Connector is missing required server configuration: ${missing.join(", ")}`);
  }
}

function redactString(value: string): string {
  return value
    .replace(EMAIL_RE, "[redacted-email]")
    .replace(IPV4_RE, "[redacted-ip]")
    .replace(IPV6_RE, "[redacted-ip]");
}

export function redact(value: unknown): unknown {
  if (typeof value === "string") return redactString(value);
  if (Array.isArray(value)) return value.map(redact);
  if (value && typeof value === "object") {
    const out: JsonObject = {};
    for (const [key, child] of Object.entries(value as JsonObject)) {
      if (["authorization", "cookie", "cookies", "password", "secret", "token"].includes(key.toLowerCase())) {
        out[key] = "[redacted]";
      } else {
        out[key] = redact(child);
      }
    }
    return out;
  }
  return value;
}

function safeUrl(value: unknown): string | undefined {
  if (typeof value !== "string" || !value) return undefined;
  try {
    const url = new URL(value);
    url.username = "";
    url.password = "";
    url.search = "";
    url.hash = "";
    return redactString(url.toString());
  } catch {
    return redactString(value.split("?")[0]);
  }
}

function clampLimit(limit: number | undefined, fallback = 20): number {
  const parsed = Number.isFinite(limit) ? Math.trunc(limit as number) : fallback;
  return Math.max(1, Math.min(MAX_LIMIT, parsed));
}

async function sentryFetch(env: SentryEnv, path: string, query?: Record<string, string | number | undefined>): Promise<unknown> {
  requireConfig(env);
  const url = new URL(`${baseUrl(env)}${path}`);
  for (const [key, value] of Object.entries(query || {})) {
    if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
  }

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${env.SENTRY_AUTH_TOKEN}`,
      Accept: "application/json",
      "User-Agent": "GoreeCloud-Sentry-MCP/0.1"
    }
  });

  if (!response.ok) {
    const requestId = response.headers.get("x-sentry-request-id");
    throw new Error(`Sentry API request failed (${response.status}${requestId ? `, request ${requestId}` : ""}).`);
  }

  return response.json();
}

function compactTags(tags: unknown): Array<{ key: string; value: string }> {
  if (!Array.isArray(tags)) return [];
  return tags
    .filter((tag) => tag && typeof tag === "object")
    .slice(0, 20)
    .map((tag) => {
      const obj = tag as JsonObject;
      return {
        key: redactString(String(obj.key ?? "")),
        value: redactString(String(obj.value ?? ""))
      };
    });
}

export async function listIssues(
  env: SentryEnv,
  args: { environment?: string; timeRange?: string; limit?: number; query?: string }
): Promise<unknown> {
  const limit = clampLimit(args.limit);
  const data = await sentryFetch(
    env,
    `/api/0/organizations/${encodeURIComponent(env.SENTRY_ORG)}/issues/`,
    {
      project: env.SENTRY_PROJECT,
      environment: args.environment || "prod",
      statsPeriod: args.timeRange || "24h",
      limit,
      query: args.query ?? "is:unresolved",
      sort: "date"
    }
  );

  const issues = Array.isArray(data) ? data : [];
  return issues.slice(0, limit).map((issue) => {
    const obj = issue as JsonObject;
    return redact({
      id: obj.id,
      shortId: obj.shortId,
      title: obj.title,
      culprit: obj.culprit,
      status: obj.status,
      level: obj.level,
      firstSeen: obj.firstSeen,
      lastSeen: obj.lastSeen,
      count: obj.count,
      userCount: obj.userCount,
      permalink: safeUrl(obj.permalink),
      project: obj.project,
      metadata: obj.metadata
    });
  });
}

export async function issueDetail(env: SentryEnv, issueId: string): Promise<unknown> {
  const data = await sentryFetch(
    env,
    `/api/0/organizations/${encodeURIComponent(env.SENTRY_ORG)}/issues/${encodeURIComponent(issueId)}/`
  ) as JsonObject;

  return redact({
    id: data.id,
    shortId: data.shortId,
    title: data.title,
    culprit: data.culprit,
    status: data.status,
    level: data.level,
    firstSeen: data.firstSeen,
    lastSeen: data.lastSeen,
    count: data.count,
    userCount: data.userCount,
    permalink: safeUrl(data.permalink),
    project: data.project,
    metadata: data.metadata,
    tags: compactTags(data.tags)
  });
}

export async function issueEvents(
  env: SentryEnv,
  issueId: string,
  args: { environment?: string; timeRange?: string; limit?: number }
): Promise<unknown> {
  const limit = clampLimit(args.limit);
  const data = await sentryFetch(
    env,
    `/api/0/organizations/${encodeURIComponent(env.SENTRY_ORG)}/issues/${encodeURIComponent(issueId)}/events/`,
    {
      environment: args.environment || "prod",
      statsPeriod: args.timeRange || "24h",
      per_page: limit
    }
  );
  const events = Array.isArray(data) ? data : [];
  return events.slice(0, limit).map((event) => {
    const obj = event as JsonObject;
    return redact({
      id: obj.id ?? obj.eventID,
      eventID: obj.eventID,
      title: obj.title,
      message: obj.message,
      culprit: obj.culprit,
      dateCreated: obj.dateCreated,
      platform: obj.platform,
      groupID: obj.groupID,
      tags: compactTags(obj.tags)
    });
  });
}

export async function eventDetail(env: SentryEnv, eventId: string): Promise<unknown> {
  const data = await sentryFetch(
    env,
    `/api/0/projects/${encodeURIComponent(env.SENTRY_ORG)}/${encodeURIComponent(env.SENTRY_PROJECT)}/events/${encodeURIComponent(eventId)}/`
  ) as JsonObject;

  const contexts = data.contexts && typeof data.contexts === "object" ? data.contexts as JsonObject : {};
  const request = data.request && typeof data.request === "object" ? data.request as JsonObject : {};

  return redact({
    eventID: data.eventID ?? data.id,
    title: data.title,
    message: data.message,
    culprit: data.culprit,
    dateCreated: data.dateCreated,
    environment: data.environment,
    release: data.release,
    platform: data.platform,
    transaction: data.transaction,
    requestUrl: safeUrl(request.url),
    tags: compactTags(data.tags),
    contexts: {
      runtime: contexts.runtime,
      os: contexts.os,
      browser: contexts.browser,
      device: contexts.device
    }
  });
}

export async function healthCheck(env: SentryEnv): Promise<unknown> {
  const project = await sentryFetch(
    env,
    `/api/0/projects/${encodeURIComponent(env.SENTRY_ORG)}/${encodeURIComponent(env.SENTRY_PROJECT)}/`
  ) as JsonObject;

  return redact({
    ok: true,
    apiReachable: true,
    org: env.SENTRY_ORG,
    project: {
      id: project.id,
      slug: project.slug,
      name: project.name,
      platform: project.platform,
      status: project.status,
      dateCreated: project.dateCreated
    }
  });
}

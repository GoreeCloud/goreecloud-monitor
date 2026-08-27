const EVENT_POLICY = Object.freeze({
  DOWN: { severity: "critical", title: "Monitor detected an outage" },
  RECOVERED: { severity: "normal", title: "Monitor detected a recovery" },
  DEGRADED: { severity: "warning", title: "Monitor detected degraded service" },
  TLS_EXPIRING: { severity: "warning", title: "Monitor certificate attention required" },
  HEARTBEAT_MISSED: { severity: "error", title: "Monitor heartbeat missed" }
});

const MAX_LABEL_LENGTH = 160;
const MAX_SUMMARY_LENGTH = 500;
const MAX_PAYLOAD_BYTES = 8 * 1024;

function requiredText(value, name, maxLength) {
  if (typeof value !== "string") throw new TypeError(`${name} must be a string`);
  const normalized = value.trim();
  if (!normalized) throw new TypeError(`${name} is required`);
  if (normalized.length > maxLength) throw new RangeError(`${name} exceeds ${maxLength} characters`);
  return normalized;
}

export function createNotificationPayload(event) {
  if (!event || typeof event !== "object") throw new TypeError("event is required");
  const policy = EVENT_POLICY[event.type];
  if (!policy) throw new TypeError("unsupported monitoring event type");

  const monitor = requiredText(event.monitor, "monitor", MAX_LABEL_LENGTH);
  const summary = requiredText(event.summary, "summary", MAX_SUMMARY_LENGTH);

  const payload = {
    source: "goreecloud-monitor",
    channel: "monitoring",
    title: policy.title,
    body: `${monitor}: ${summary}`,
    severity: policy.severity
  };

  const bytes = Buffer.byteLength(JSON.stringify(payload), "utf8");
  if (bytes > MAX_PAYLOAD_BYTES) throw new RangeError("notification payload exceeds Notify compatibility envelope");
  return payload;
}

export class NotifyProducer {
  constructor({ endpoint, token, fetchImpl = globalThis.fetch }) {
    this.endpoint = new URL(endpoint);
    if (this.endpoint.protocol !== "https:") throw new TypeError("Notify endpoint must use HTTPS");
    this.token = requiredText(token, "token", 4096);
    if (typeof fetchImpl !== "function") throw new TypeError("fetch implementation is required");
    this.fetchImpl = fetchImpl;
  }

  async publish(event) {
    const payload = createNotificationPayload(event);
    const url = new URL("/api/v1/notifications", this.endpoint);
    const response = await this.fetchImpl(url, {
      method: "POST",
      headers: {
        authorization: `Bearer ${this.token}`,
        "content-type": "application/json",
        accept: "application/json"
      },
      body: JSON.stringify(payload),
      redirect: "error"
    });
    if (!response.ok) throw new Error(`Notify rejected monitoring notification with HTTP ${response.status}`);
    return response.json();
  }
}

export const monitoringEventTypes = Object.freeze(Object.keys(EVENT_POLICY));

import assert from "node:assert/strict";
import test from "node:test";

import { NotifyProducer, createNotificationPayload, monitoringEventTypes } from "./index.mjs";

test("maps the bounded monitoring event vocabulary to Notify severity", () => {
  const expected = new Map([
    ["DOWN", "critical"],
    ["RECOVERED", "normal"],
    ["DEGRADED", "warning"],
    ["TLS_EXPIRING", "warning"],
    ["HEARTBEAT_MISSED", "error"]
  ]);
  assert.deepEqual(monitoringEventTypes, [...expected.keys()]);
  for (const [type, severity] of expected) {
    const payload = createNotificationPayload({ type, monitor: "Vault", summary: "state changed" });
    assert.equal(payload.source, "goreecloud-monitor");
    assert.equal(payload.channel, "monitoring");
    assert.equal(payload.severity, severity);
    assert.equal(Object.hasOwn(payload, "target"), false);
    assert.equal(Object.hasOwn(payload, "diagnostics"), false);
  }
});

test("fails closed for unsupported events and invalid labels", () => {
  assert.throws(() => createNotificationPayload({ type: "UNKNOWN", monitor: "Vault", summary: "x" }));
  assert.throws(() => createNotificationPayload({ type: "DOWN", monitor: "", summary: "x" }));
  assert.throws(() => createNotificationPayload({ type: "DOWN", monitor: "Vault", summary: "" }));
});

test("requires HTTPS and keeps the producer token out of the JSON body", async () => {
  assert.throws(() => new NotifyProducer({ endpoint: "http://notify.goreecloud.com", token: "secret" }));

  let captured;
  const producer = new NotifyProducer({
    endpoint: "https://notify.goreecloud.com",
    token: "secret-token",
    fetchImpl: async (url, options) => {
      captured = { url: String(url), options };
      return { ok: true, status: 201, json: async () => ({ id: 1 }) };
    }
  });

  const result = await producer.publish({ type: "DOWN", monitor: "Vault", summary: "availability check failed" });
  assert.deepEqual(result, { id: 1 });
  assert.equal(captured.url, "https://notify.goreecloud.com/api/v1/notifications");
  assert.equal(captured.options.headers.authorization, "Bearer secret-token");
  assert.equal(captured.options.body.includes("secret-token"), false);
  assert.equal(captured.options.redirect, "error");
});

test("propagates a fail-closed error when Notify rejects publication", async () => {
  const producer = new NotifyProducer({
    endpoint: "https://notify.goreecloud.com",
    token: "secret-token",
    fetchImpl: async () => ({ ok: false, status: 403 })
  });
  await assert.rejects(
    producer.publish({ type: "DOWN", monitor: "Vault", summary: "availability check failed" }),
    /HTTP 403/
  );
});

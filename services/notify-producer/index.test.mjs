import assert from "node:assert/strict";
import test from "node:test";

import {
  NotifyProducer,
  createIdempotencyKey,
  createNotificationPayload,
  monitoringEventTypes
} from "./index.mjs";

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

test("derives a deterministic opaque idempotency key from the Monitor transition", () => {
  const event = {
    type: "DOWN",
    monitor: "Vault",
    summary: "availability check failed",
    transitionId: "incident-42-transition-7"
  };
  const first = createIdempotencyKey(event);
  const retry = createIdempotencyKey({ ...event });
  const nextTransition = createIdempotencyKey({ ...event, transitionId: "incident-42-transition-8" });

  assert.equal(first, retry);
  assert.notEqual(first, nextTransition);
  assert.match(first, /^gcm-v1-[0-9a-f]{64}$/);
  assert.equal(first.includes(event.transitionId), false);
  assert.throws(() => createIdempotencyKey({ ...event, transitionId: "" }), /transitionId is required/);
});

test("requires HTTPS and keeps the producer token and transition id out of the JSON body", async () => {
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

  assert.equal(JSON.stringify(producer).includes("secret-token"), false);
  assert.deepEqual(Object.keys(producer), []);

  const result = await producer.publish({
    type: "DOWN",
    monitor: "Vault",
    summary: "availability check failed",
    transitionId: "incident-42-transition-7"
  });
  assert.deepEqual(result, { id: 1 });
  assert.equal(captured.url, "https://notify.goreecloud.com/api/v1/notifications");
  assert.equal(captured.options.headers.authorization, "Bearer secret-token");
  assert.match(captured.options.headers["idempotency-key"], /^gcm-v1-[0-9a-f]{64}$/);
  assert.equal(captured.options.headers["idempotency-key"].includes("incident-42-transition-7"), false);
  assert.equal(captured.options.body.includes("secret-token"), false);
  assert.equal(captured.options.body.includes("incident-42-transition-7"), false);
  assert.equal(captured.options.redirect, "error");
});

test("fails closed when publication lacks a stable transition id", async () => {
  const producer = new NotifyProducer({
    endpoint: "https://notify.goreecloud.com",
    token: "secret-token",
    fetchImpl: async () => {
      throw new Error("network should not be reached");
    }
  });
  await assert.rejects(
    producer.publish({ type: "DOWN", monitor: "Vault", summary: "availability check failed" }),
    /transitionId must be a string/
  );
});

test("propagates a fail-closed error when Notify rejects publication", async () => {
  const producer = new NotifyProducer({
    endpoint: "https://notify.goreecloud.com",
    token: "secret-token",
    fetchImpl: async () => ({ ok: false, status: 403 })
  });
  await assert.rejects(
    producer.publish({
      type: "DOWN",
      monitor: "Vault",
      summary: "availability check failed",
      transitionId: "incident-42-transition-7"
    }),
    /HTTP 403/
  );
});

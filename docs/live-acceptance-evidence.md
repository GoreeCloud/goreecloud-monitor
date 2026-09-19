# Live Target Acceptance Evidence

This procedure collects current GoreeCloud Monitor target evidence after the retirement of Uptime Kuma and ntfy. It does not deploy Monitor or grant production authority by itself.

## Evidence sources

Current acceptance evidence must come from the actual Monitor candidate and target environment:

- exact Git revision and immutable image;
- resolved production Compose topology;
- PostgreSQL schema and persistent storage;
- target preflight output;
- private DNS/Gateway/NetBird behavior;
- reviewed active monitor definitions;
- representative live check results;
- incidents and maintenance behavior;
- GoreeCloud Notify delivery and durable-outbox replay;
- backup and isolated restore;
- independent outage alerting;
- current Glaze UI and platform-system acceptance.

## Preserved Uptime Kuma evidence

Historical Uptime Kuma configuration/runtime evidence may be used to reconstruct monitoring requirements or compare intended coverage. It is not current operational truth.

When preserved evidence is used:

- sanitize it;
- do not treat stale monitor definitions as active requirements without reconciliation;
- do not restore secrets or credentials into source artifacts;
- identify the recovery snapshot or protected source that owns the evidence;
- record any requirement that was retired, replaced, renamed, or intentionally not migrated.

## Definition reconciliation

Before activating Monitor definitions:

1. inventory currently active GoreeCloud services and private endpoints;
2. reconcile preserved predecessor definitions against that inventory;
3. remove or leave disabled retired targets;
4. resolve unsupported semantics explicitly;
5. keep imported definitions paused until reviewed;
6. record the final enabled Monitor definition set.

## Live acceptance

Validate representative:

- HTTP/HTTPS status and content expectations;
- TCP reachability;
- TLS certificate/expiry behavior;
- DNS resolution, including approved resolver-specific semantics;
- heartbeat behavior;
- Ping/ICMP under the approved low-privilege worker identity;
- maintenance windows;
- failure thresholds;
- incident open/update/recovery;
- DOWN, RECOVERED, DEGRADED, and TLS-expiry notifications;
- durable notification restart/replay with no duplicate fanout.

## Recovery evidence

Record a fresh PostgreSQL backup and an isolated restore proving the exact candidate can recover current monitor definitions, incidents, maintenance state, and notification outbox state.

## Independent alerting

At least one outage-reporting path must remain usable when the normal Monitor → GoreeCloud Notify path is unavailable.

## Completion boundary

A successful collection means the reviewed target evidence exists. It does not itself set Monitor as production authority. Production activation still requires all applicable gates and explicit approval.

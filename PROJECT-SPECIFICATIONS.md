# GoreeCloud Monitor — Project Specifications

**Repository:** `GoreeCloud/monitor`  
**Former repository identity in the Drive source:** `GoreeCloud/goreecloud-monitor`  
**Project type:** First-party availability, endpoint-health, heartbeat, scheduled-job/dead-man, certificate, incident, and recovery-monitoring application  
**Repository lifecycle declaration (legacy Contract 0.4):** `release-candidate`; canonical Contract 2.0 lifecycle reclassification remains pending and must be evidence-backed; advanced pre-production acceptance remains incomplete and production activation remains unaccepted  
**Version:** `0.1.0`  
**Migration baseline:** `46897de12f514a43da3a668e3e9c952e63e9dea6`  
**License:** `AGPL-3.0-only` for current GoreeCloud-owned source; previously distributed MIT-licensed copies retain their prior grant  
**Owner:** GoreeCloud  
**Intended users:** GoreeCloud owner/administrators and approved least-privilege operational consumers  
**Deployment model:** Private Docker and Docker Compose service with separate web, worker, migration, and PostgreSQL roles  
**Supported platforms:** Web and server runtime  
**Canonical authority:** This file becomes the authoritative project specification once accepted on the default branch.

## Migration and precedence

This file consolidates the former root `SPECIFICATIONS.md` with still-applicable requirements and historical context from Google Drive **Project Specification — Monitor.docx** (file ID `1DUWERKb3Ca2o8USnjvJFQfv40JIM9QDr`).

The Drive source contains both normative product requirements and a long exact-revision migration/acceptance history. Normative requirements are reconciled here. Significant project history belongs in `PROJECT-RECORD.md`, while detailed implementation chronology and preserved source-validation evidence remain in `CHANGELOGS.md` and repository evidence records.

Current verified repository/runtime state controls factual implementation claims. Historical Drive references to `GoreeCloud/goreecloud-monitor`, Uptime Kuma as active authority, ntfy as an active publisher, older Glaze UI versions, pre-integration candidate SHAs, or old deployment assumptions do not override accepted current repository state.

Current implementation state is governed by `IMPLEMENTED-FEATURES.md`; open work by `PLANNED-FEATURES.md`; release/change chronology by `CHANGELOGS.md`.

## 1. Product role

GoreeCloud Monitor is GoreeCloud's specialized first-party authority candidate for active service availability and operational endpoint monitoring.

Its responsibilities include:
- HTTP/HTTPS availability;
- TCP reachability;
- DNS resolution and expected-answer validation;
- TLS certificate validity and expiry;
- IPv4/IPv6 Ping/ICMP reachability using low-privilege runtime mechanisms;
- push/heartbeat monitoring;
- scheduled-job/dead-man monitoring;
- response-time and state history;
- maintenance and pause state;
- incident and recovery history;
- minimized availability notifications through GoreeCloud Notify; and
- bounded read-only operational integration with GoreeCloud Manager.

Monitor is **not** intended to become:
- a general server-resource monitoring suite;
- a full distributed tracing or log-aggregation platform;
- a backup scheduler;
- a notification-delivery platform;
- a general administrative control plane;
- a Prometheus replacement; or
- an unrestricted plugin marketplace.

Specialized platform authorities retain their own domains.

## 2. Product purpose and development model

Monitor is original GoreeCloud-owned software, not a permanent Uptime Kuma fork.

The product exists to provide the availability-monitoring capabilities GoreeCloud actually requires while reducing unnecessary upstream complexity and preserving:
- open-source operation;
- portability;
- recoverability;
- technology independence;
- least-privilege operation;
- explicit migration/rollback evidence; and
- direct integration with GoreeCloud platform systems.

Uptime Kuma was permanently retired from `goreecloud-vps-01` on September 18, 2026. Its preserved configuration, data, artifacts, importer behavior, and comparison tooling are historical/recovery/migration evidence only and do not establish current production authority.

Predecessor retirement does not by itself promote Monitor to production authority.

## 3. Current architecture

The current architecture is:

- **Django web application and API**
  - authentication/authorization;
  - Glaze UI presentation;
  - monitor administration;
  - incidents/history;
  - maintenance;
  - settings/security;
  - read-only Manager endpoints.
- **Monitoring worker**
  - active checks;
  - schedule evaluation;
  - incident/state transitions;
  - durable notification-outbox publication;
  - scheduled-job/dead-man evaluation.
- **PostgreSQL**
  - production monitor definitions;
  - check/history state;
  - incidents;
  - maintenance;
  - scheduled-job events;
  - durable notification-outbox state;
  - application/authentication state.
- **SQLite**
  - supported local/test option only where appropriate.
- **GoreeCloud Notify**
  - the only supported notification publisher candidate.
- **Private Gateway/network path**
  - production publication remains acceptance-gated and private by default.

The production candidate separates database, one-shot migration, web, and worker services.

## 4. Monitoring capabilities

### HTTP and HTTPS

Monitor must support:
- GET as the normal default with approved configurable method where justified;
- URL/hostname targets;
- expected status validation;
- bounded timeouts;
- redirect behavior;
- TLS verification;
- optional body-text assertion;
- optional JSON field/value assertion;
- response-time measurement;
- bounded response handling;
- failure and recovery transitions.

### TCP

Monitor must support bounded TCP reachability checks with destination-policy enforcement and clear timeout/failure classification.

### DNS

Monitor must support:
- A;
- AAAA;
- CNAME;
- expected-answer validation;
- system-resolver behavior; and
- explicit resolver-qualified targets where the resolver itself is part of the monitoring requirement.

Explicit resolvers must pass the same destination-policy boundary applied to other active network targets. Malformed, credential-bearing, ambiguous, or otherwise unsafe resolver specifications must fail closed.

### TLS certificate monitoring

Monitor must support:
- certificate validation;
- expiry capture;
- configurable warning thresholds;
- certificate-expiration incident state;
- minimized notification context.

### Ping / ICMP

Ping is a first-class Monitor type.

The runtime must use approved low-privilege Linux datagram ping sockets rather than adding `CAP_NET_RAW`, privileged mode, host networking, Docker-socket access, or a permanent privileged probe sidecar.

IPv4 and IPv6 targets must be resolved and validated through the same destination-policy boundary before the ICMP transport receives an approved numeric address.

### Push / heartbeat

Push/heartbeat monitoring requires:
- rotatable per-monitor credentials;
- one-way-stored credential verifiers;
- expected interval and grace;
- missed-heartbeat detection;
- recovery on valid resumed signals;
- minimized unauthenticated acknowledgements;
- no reusable credentials in URLs where the hardened endpoint is used.

### Scheduled Job / Dead-Man

Monitor owns the native scheduled-job/dead-man capability now implemented in current source. Healthchecks remains a benchmark/reference, not an upstream runtime or authority dependency.

Required/current direction includes:
- first-class JOB monitors;
- simple interval + grace;
- strict cron with IANA time zone;
- supported systemd OnCalendar schedule expressions;
- authenticated START/SUCCESS/FAILURE/bounded LOG signals;
- one-way-stored rotatable credentials;
- run correlation;
- duration history;
- missed-run detection;
- maximum-runtime overrun detection;
- durable optional replay/idempotency identity while retained;
- bounded signal rate limiting;
- retained job-event history;
- lifecycle presentation such as Awaiting, Started, Completed, Failed, and Late without replacing the underlying Monitor state/incident model;
- staff-only recovery/export surfaces that exclude reusable credentials; and
- read-only Manager visibility where authorized.

Tags/projects, optional auto-provisioning, private status summaries, periodic reports/reminders, and email-based ingestion remain separately planned or acceptance-gated where not already implemented.

## 5. State, scheduling, and incident model

Core operational states include:
- Unknown;
- Up;
- Down;
- Degraded;
- Paused;
- Maintenance.

Scheduled-job presentation may expose additional derived lifecycle phases without changing the underlying authoritative operational state.

Checks must use:
- configurable intervals;
- bounded timeouts;
- consecutive failure/recovery thresholds;
- appropriate retry behavior;
- persisted state transitions;
- incident creation/recovery;
- maintenance suppression;
- bounded history retention.

A single transient error must not automatically become a sustained outage when configured thresholds require additional evidence.

Restart behavior must avoid inventing artificial state transitions from stale or incomplete evidence.

## 6. Notifications and independent outage alerting

GoreeCloud Notify is the only supported Monitor notification publisher candidate after ntfy retirement.

Monitor must:
- use a dedicated least-privilege producer credential;
- minimize transition payloads;
- omit raw target URLs, query strings, response bodies, reusable secrets, and unnecessary diagnostics;
- persist payload/idempotency intent before network publication;
- use a durable PostgreSQL outbox;
- retry due pending records with bounded backoff;
- preserve undelivered records until delivery/reconciliation;
- bound retention of already-delivered outbox metadata;
- survive worker restart with pending delivery state;
- converge idempotently without claiming exactly-once semantics.

Production acceptance is blocked while undelivered outbox state or unresolved Notify integration evidence remains.

Monitor must also have an **independent Monitor-down alert path** that does not depend entirely on Monitor and Notify remaining healthy together. Monitoring cannot reliably report its own complete failure through the same failed path.

## 7. Administration and Manager integration

The web UI is intended primarily for operational visibility, incidents, trends, configuration, maintenance, security, and settings.

Repeatable administration must not depend exclusively on a GUI. Documented API, import/export, and command-line/automation interfaces should exist where useful.

GoreeCloud Manager may consume Monitor through a dedicated versioned, least-privilege **read-only** API.

Manager must not receive direct database access.

Approved Manager data may include:
- overall health;
- monitor counts by state;
- active incidents;
- bounded monitor/job summaries;
- recent recovery state;
- availability summaries.

Any write-capable Manager administration requires separate explicit authorization architecture and accepted Identity/Policy boundaries.

Monitor must remain operational if Manager is unavailable.

## 8. Security requirements

Monitor is security-sensitive because it authenticates administrators, accepts inbound heartbeat/job signals, performs outbound network requests, stores operational history, and publishes notifications.

Requirements include:
- private-by-default deployment;
- authenticated administrative access;
- staff-gated privileged mutation;
- least-privilege service identities;
- strong production secret validation;
- secure session/CSRF cookies;
- CSRF protection;
- Content Security Policy;
- Permissions Policy;
- same-origin and browser hardening;
- no unnecessary public backend/database ports;
- no privileged containers;
- no host networking;
- no Docker socket;
- no unnecessary Linux capabilities;
- read-only application root filesystems;
- `cap_drop: ALL`;
- `no-new-privileges`;
- dependency and container vulnerability review;
- protected secret storage;
- minimized security/audit events.

### SSRF and outbound destination controls

Monitor intentionally makes outbound network requests, so user-controlled targets require fail-closed SSRF protections.

Targets must reject unsafe userinfo/embedded credentials and must enforce approved destination policy for private/reserved/loopback/link-local networks.

All addresses returned by preflight resolution must pass the destination policy before use.

Bounded timeouts, response limits, redirects, and worker concurrency are required.

Any documented DNS time-of-check/time-of-use limitation must remain explicit; operators must not broaden allowlists merely to bypass it.

## 9. Privacy requirements

Monitoring data can reveal infrastructure topology, operational failures, endpoints, and service behavior.

Collect only what is required to establish availability and operational state.

History should normally retain:
- status;
- timing;
- bounded target identity;
- failure classification;
- bounded diagnostics.

Sensitive application content must not become monitoring history merely because an endpoint returned it.

Logs, notifications, evidence bundles, API output, exports, and security events must exclude reusable credentials and unnecessary raw infrastructure details.

Privacy Shield source adapters do not establish accepted runtime/central Privacy Shield integration.

## 10. Data, storage, backup, recovery, and portability

Production persistent state uses PostgreSQL.

Production acceptance requires:
- application-consistent logical backup;
- protected backup destination and retention;
- isolated restore against the exact candidate;
- verification of monitor definitions;
- incidents/history;
- maintenance;
- scheduled-job definitions/events;
- notification-outbox state;
- application configuration;
- required secret-reference recovery procedure;
- version/image identity;
- rollback compatibility.

A successful backup job alone is insufficient. Restoration must be tested.

The restored candidate must resume safely without uncontrolled duplicate notifications.

Monitor definitions and portable operational configuration must be exportable in a documented, versioned, non-proprietary format without exporting active reusable credentials.

Re-import into an empty instance should be part of recovery validation where applicable.

## 11. Glaze UI

The current official Stable design-system baseline for Monitor is **Glaze UI 1.6.0**.

Current source carries a repository-local 1.6.0 presentation mapping and immutable upstream provenance. This is a **source-adoption candidate**, not whole-application acceptance.

Monitor-specific acceptance requires representative browser/OS evidence for:
- accessibility;
- keyboard and assistive-technology behavior;
- semantic state/recovery;
- large text and reflow;
- responsive task continuity;
- material/depth;
- motion/reduced motion;
- contrast/forced colors;
- layout/density;
- interaction states;
- performance;
- visual/Human Visual Excellence review;
- rollback; and
- governed consumer acceptance.

Glaze UI must present authoritative Monitor/provider state; presentation cannot manufacture health, security, privacy, recovery, or authorization.

## 12. Integral Platform Systems

Monitor evaluates all nine Integral Platform Systems fail-closed.

Current repository evidence describes:
- **Manager:** applicable; read-only source integrations exist, accepted platform/runtime integration remains incomplete.
- **Privacy Shield:** source adapter candidate; runtime/central acceptance incomplete.
- **Wardveil Security:** source adoption/security evidence exists; target-runtime acceptance incomplete.
- **Everkeep:** source acceptance/recovery policy evidence exists; target restore/recovery acceptance incomplete.
- **Glaze UI:** 1.6.0 source-adoption candidate; application acceptance incomplete.
- **Mesh:** applicable; accepted integration incomplete.
- **Identity:** applicable; local Django authentication is not equivalent to accepted GoreeCloud Identity integration.
- **Policy:** applicable; accepted shared policy decision/enforcement integration incomplete.
- **Observability:** application-local evidence exists; accepted shared Observability integration incomplete.

Decorative names, badges, version strings, or documentation-only declarations do not satisfy platform integration.

## 13. Deployment and operations

Initial/runtime packaging uses Docker and Docker Compose.

The production candidate must preserve:
- separate database, migration, web, and worker roles;
- immutable/traceable application and PostgreSQL image identity;
- protected purpose-specific environment files;
- persistent PostgreSQL storage;
- private network boundaries;
- zero host-published Monitor/database ports unless separately authorized;
- non-root application identity;
- read-only root filesystems;
- dropped capabilities;
- no-new-privileges;
- worker-only narrow low-privilege ICMP permission;
- private Gateway/DNS/NetBird publication only after target acceptance.

Production placement, DNS, Gateway route, NetBird policy, firewall changes, monitor activation, and credential provisioning require separate target-environment approval.

## 14. Historical predecessor migration boundary

Uptime Kuma and ntfy are retired historical systems, not current runtime authorities.

Preserved Uptime Kuma configuration, importer behavior, definition comparison, runtime evidence, and historical data may remain for:
- recovery;
- migration provenance;
- semantic comparison;
- regression reference.

They must not be treated as current production truth.

Any historical network identity or source-address reuse must be deliberate, conflict-free, validated against current target state, documented, and reversible.

The ordinary Monitor rollback path is the accepted Monitor/PostgreSQL predecessor, not restoration of Uptime Kuma to production.

## 15. Explicit scope exclusions

Unless later requirements deliberately expand scope, Monitor does not need to become:
- a public status-page platform;
- a broad third-party notification-provider catalog;
- game/Steam monitor suite;
- Kubernetes monitor;
- SNMP platform;
- arbitrary database-query monitor;
- synthetic browser-automation platform;
- distributed tracing platform;
- log aggregation platform;
- Prometheus replacement;
- general host/resource monitoring suite;
- general plugin marketplace;
- AI analysis platform;
- multi-region distributed probe fabric.

Requirements should be added only when a real GoreeCloud need justifies their operational/security cost.

## 16. Testing and acceptance

Automated and disposable validation must cover, where applicable:
- scheduling and thresholds;
- HTTP/HTTPS;
- TLS;
- redirects;
- TCP;
- DNS/system and explicit resolver behavior;
- Push/heartbeat;
- Ping/ICMP;
- scheduled-job lifecycle and security;
- state transitions;
- incidents/recovery;
- maintenance;
- notification minimization/outbox behavior;
- Manager read-only authorization;
- import/export;
- database migration;
- backup/restore;
- rollback compatibility;
- security boundaries;
- dependency/container vulnerability state;
- hardened production Compose topology;
- no unintended public port exposure.

Source and disposable CI do not prove production readiness.

Target acceptance separately requires:
- current VPS Docker/network/storage readback;
- exact immutable deployed images;
- target PostgreSQL backup and isolated restore;
- reviewed active monitor definitions;
- representative live HTTP/HTTPS/TCP/TLS/DNS/heartbeat/Ping/job checks;
- state/incident/maintenance behavior;
- accepted Notify delivery and outbox restart/replay;
- independent outage alerting;
- target Wardveil/Privacy Shield/Everkeep evidence;
- Monitor-specific Glaze UI acceptance;
- remaining platform-system acceptance;
- rollback/recovery exercise;
- explicit production activation approval.

## 17. Release model

A Stable release requires more than a successful source build or green CI.

Required evidence includes:
- source review;
- passing exact-revision CI;
- dependency/container review;
- traceable build/artifact identity;
- backup/restore;
- upgrade/rollback;
- monitoring-engine failure behavior;
- target private publication;
- notification/incident behavior;
- accessibility and current Stable Glaze UI acceptance;
- platform-system acceptance;
- documentation reconciliation;
- explicit production/release approval.

Historical predecessor retirement is not release acceptance.

## 18. Current accepted implementation boundary

Accepted `main` includes the capabilities recorded in `IMPLEMENTED-FEATURES.md`, including:
- native HTTP/HTTPS/TCP/DNS/TLS/Push/Ping monitoring foundations;
- scheduled-job/dead-man monitoring;
- incidents, maintenance, history, state transitions;
- hardened authentication/security/privacy controls;
- PostgreSQL production support;
- durable Notify outbox candidate;
- read-only Manager APIs;
- hardened production topology;
- backup/restore and rollback tooling;
- Uptime Kuma historical/recovery tooling;
- Wardveil/Privacy Shield/Everkeep source-adoption evidence;
- Glaze UI 1.6.0 source mapping.

These are source/current-main capabilities. Production authority remains unaccepted until the target-environment gates above are satisfied.

## 19. Maintenance and retirement

Maintain source, migrations, portability, security, deployment, recovery, and platform-contract compatibility.

Significant architecture changes, repository renames, licensing changes, major platform integrations, production activation, incidents, recovery events, lifecycle promotions, predecessor retirement, or eventual Monitor retirement must be recorded in `PROJECT-RECORD.md`.

Routine release/change chronology belongs in `CHANGELOGS.md`.

## Related repository documentation

- [README.md](README.md)
- [PROJECT-RECORD.md](PROJECT-RECORD.md)
- [IMPLEMENTED-FEATURES.md](IMPLEMENTED-FEATURES.md)
- [PLANNED-FEATURES.md](PLANNED-FEATURES.md)
- [CHANGELOGS.md](CHANGELOGS.md)
- [FEATURES.md](FEATURES.md)
- [SECURITY.md](SECURITY.md)
- [USER-MANUAL.md](USER-MANUAL.md)
- [goreecloud.platform.yaml](goreecloud.platform.yaml)

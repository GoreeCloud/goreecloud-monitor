# Changelog

## Unreleased - Wardveil Security hardening

- Integrated **Wardveil Security by GoreeCloud** as Monitor's official security/protection identity while preserving Glaze UI 1.0 as the visual/interaction system and keeping Django, Caddy, NetBird, firewall, credential, vulnerability, backup, and recovery controls authoritative for their technical state.
- Added a staff-only Glaze UI security-posture surface and the approved `Protected by Wardveil` presentation across the primary shell, authentication, protected Settings, and privileged Django administration.
- Restricted Settings, exact private-network allowlists, push-heartbeat credentials, raw check diagnostics, and incident failure reasons to staff while retaining useful monitor state, incident state, interval, latency, and timing information for authenticated viewers.
- Added dynamic response hardening with Content Security Policy, Permissions Policy, same-origin resource policy, no-index/no-archive robot controls, same-origin referrer/opener boundaries, clickjacking denial, and no-store caching for operational responses.
- Strengthened production session defaults with Secure/HttpOnly/SameSite cookies, host-only production cookie names, HTTPS redirect, and one-year HSTS defaults while preserving non-secure development cookie names under explicit debug mode.
- Moved Wardveil response middleware outside request-rejection middleware so rejected dynamic requests receive the same private response-policy headers; WhiteNoise static assets retain independent immutable caching behavior.
- Added minimized structured `monitoring.wardveil` events for login, logout, failed login, monitor mutation, maintenance-window mutation, and heartbeat-credential rotation without copying failed-login usernames, client IP addresses, target URLs, request bodies, tokens, secrets, or raw diagnostics.
- Minimized health endpoints to readiness/liveness booleans, rejected HEAD as a state-mutating heartbeat method, and added an explicit bearer challenge to unauthorized Manager API requests.
- Hardened ntfy transition publishing so arbitrary monitor exceptions, target details, query strings, response data, and other diagnostics are not forwarded to notification bodies; controlled TLS-expiry context remains available.
- Expanded `targetpreflight` to fail closed when one-year HSTS, Secure/HttpOnly/SameSite cookie boundaries, clickjacking denial, same-origin opener policy, Content Security Policy, or Permissions Policy are missing from a production acceptance configuration.
- Added `docs/wardveil-security.md`, updated `SECURITY.md`, `.env.example`, and `README.md`, and explicitly documented the existing DNS re-resolution SSRF time-of-check/time-of-use boundary instead of overstating the current protection.
- Expanded automated regression coverage for Wardveil/Glaze conformance, security headers, staff-only posture, diagnostic and credential non-disclosure, non-mutating HEAD behavior, minimized health/API behavior, notification sanitization, structured audit events, and fail-closed security preflight.
- Preserved the existing Django migration set, hardened production Compose topology, Uptime Kuma production authority, and all existing live acceptance/recovery/rollback/cutover gates.

## Unreleased - Glaze UI 1.0 product readiness

- Replaced Monitor's older product-local UI token vocabulary with the canonical Glaze UI 1.0 semantic foundation and recorded target version 1.0.0 against canonical source revision `d6e446fd8ef251259d16368d50aad90d9287a774`.
- Added the Canvas/Solid/Raised/Glaze/Overlay surface hierarchy, canonical spacing/radius/focus/target/motion semantics, System/Light/Dark appearance behavior, local fail-soft appearance persistence, and the Compact/Medium/Expanded/Wide adaptive model.
- Added explicit no-backdrop-filter, reduced-transparency, reduced-motion, increased-contrast, forced-colors, skip-link, focus-visible, and screen-reader-only resilience support without adding remote fonts, icons, UI runtimes, analytics, or tracking dependencies.
- Replaced the generic `G` placeholder with a distinct source-controlled GoreeCloud Monitor pulse/status product mark and browser SVG favicon.
- Reworked compact navigation into a persistent Glaze bottom navigation instead of removing primary navigation below the previous 980-pixel breakpoint.
- Completed the initial information architecture with dedicated authenticated Incidents and Notifications surfaces while preserving existing Overview, Monitors, Monitor Detail, Maintenance, Settings, and authentication workflows.
- Added monitor name/state/type filtering, searchable active/recovered incident history, recent recoveries on Overview, stronger empty states, improved settings/integration posture, and a consistent Glaze form/detail/authentication treatment.
- Kept GoreeCloud Notify explicitly planned rather than inventing an unapproved producer contract; ntfy remains the implemented migration publisher and Manager remains the implemented read-only platform integration.
- Minimized unauthenticated push-heartbeat acknowledgements so a valid heartbeat token no longer reveals the internal monitor name.
- Added `docs/glaze-ui-conformance.md` and five application-level Glaze contract tests covering semantic tokens/surfaces, adaptive navigation, accessibility/resilience, local product identity/dependency boundaries, and fail-soft local appearance behavior.
- Expanded view coverage for notification-secret non-disclosure, monitor filtering, incident filtering, minimized heartbeat responses, and Glaze shell presence. The complete source suite now contains 94 tests.
- Preserved the existing database migration set so this product-readiness layer does not invalidate the current immediate-predecessor direct rollback proof.
- Kept target-native restore proof, isolated parallel activation, controlled DOWN/RECOVERED/TLS/maintenance/notification acceptance, Ping/ICMP, resolver-specific DNS, live rollback, manual Glaze/accessibility acceptance, explicit cutover, and Uptime Kuma retirement as separate gates.

## Unreleased - Repeated parallel acceptance readiness

- Added a fail-closed repeated parallel-comparison acceptance layer so production-readiness review no longer depends on interpreting isolated one-off runtime comparisons manually.
- Added `evaluate_parallel_series()` to validate sanitized `compareuptimestate` reports, require a configurable minimum number of independent observations, reject unsupported schemas or malformed results, detect duplicate result names, and preserve a fixed monitor-coverage set across the observation series.
- Added explicit acceptance blockers for state differences, latency differences, missing monitors, Monitor-only monitors, unknown source states, duplicate source records, invalid source records, insufficient observations, and coverage drift between observations.
- Added minimized per-observation and per-monitor accounting without reintroducing monitor targets, heartbeat messages, request configuration, notification assignments, or reusable credentials into the aggregate acceptance report.
- Added the `assessparallel` management command with `--minimum-observations`, `--json`, and `--require-ready` so the repeated-comparison gate can be used both for human review and fail-closed automation.
- Expanded `tests/test_uptime_kuma_parallel.py` with repeated-parity readiness, insufficient-observation, non-parity, coverage-drift, unsupported-schema, and command-level acceptance tests. The complete source suite now contains 86 tests.
- Updated `docs/uptime-kuma-runtime-evidence.md` with the repeated-comparison workflow and made clear that a ready series proves only repeated state/latency parity within the selected tolerance.
- Kept controlled DOWN/RECOVERED, TLS-warning, maintenance, notification, Ping/ICMP, resolver-specific DNS, target restore, live rollback, monitoring-source identity, explicit cutover, and Uptime Kuma retirement as separate outstanding gates.
- Opened stacked draft PR #9 from `agent/parallel-acceptance-series` against `agent/runtime-evidence-readiness` and validated exact head `d05e03de66a8d0b535dcb33ee6d19809965dfd2d` with CI run #38 and rollback-compatibility run #16; both completed successfully before this changelog-only follow-up commit.

## Unreleased - Uptime Kuma runtime evidence readiness

- Reviewed the Uptime Kuma 2.5.0 server implementation and confirmed authenticated clients receive the monitor list plus per-monitor heartbeat lists after login, providing a narrow read-only source for runtime-state evidence separate from kuma-cli configuration output.
- Added `scripts/collect_uptime_kuma_runtime_evidence.py` as a minimized runtime-state collector using the existing Uptime Kuma container and its installed `socket.io-client` runtime dependency rather than adding a new host-side package or long-lived service.
- Reused the existing protected AutoKuma/kuma-cli login token and pass it only through standard input to the temporary in-container helper; the token is not placed in argv, environment variables, evidence files, or evidence metadata.
- Added strict token-file and immediate parent-directory ownership and permission checks that reject group/other access rather than broadening credentials merely to make collection succeed.
- Limited the helper output to monitor ID, name, type, active state, latest heartbeat status, and latest response time. Raw heartbeat histories, diagnostic messages, monitor targets, credentials, and notification configuration are not persisted.
- Added fail-closed runtime completeness validation for missing/duplicate identities, invalid active states, missing heartbeat history on active monitors, invalid heartbeat states, boolean/non-numeric response-time values, and other malformed runtime data.
- Delayed evidence-directory creation until authenticated collection, completeness validation, and sanitization have succeeded so failed collection attempts do not leave partial evidence bundles.
- Reused the existing GoreeCloud runtime sanitizer before any runtime snapshot is written and added checksum-protected Internal evidence packaging with restrictive permissions.
- Added `docs/uptime-kuma-runtime-evidence.md` defining the source mechanism, authentication prerequisite, collection workflow, evidence format, completeness rules, comparison boundary, and security/operational limits.
- Added seven runtime-evidence tests covering stdin-only token transfer, token-file permissions, parent-directory permissions, missing-heartbeat rejection, inactive/no-history handling, invalid heartbeat states, and invalid boolean response-time values. The complete source suite now contains 79 tests.
- Kept live execution, runtime-state acceptance, Monitor activation, Uptime Kuma changes, monitoring-source identity changes, and cutover outside this source-only layer.

## Unreleased - Verified live baseline reconciliation

- Verified the uploaded Internal schema-v2 live-evidence archive against its previously recorded outer SHA-256 and all three internal `SHA256SUMS` entries.
- Confirmed the evidence was collected from exact validated collector revision `5d39cf25da1354412446d445c57d534b560481bd`, reported no collection failures, and marked target/environment configuration ready for review while keeping runtime comparison explicitly uncollected.
- Reconciled the documented baseline from 21 to 23 expected-active monitors using the verified sanitized live configuration while preserving Flatnotes, Linkding, and Termix as expected retired.
- Aligned stale documentation labels to the exact live Uptime Kuma labels for Adguard Home, Netbird, GoreeCloud VPS, and Caddy so name-only drift no longer creates false missing/unexpected pairs.
- Added GoreeCloud Research Library and GoreeCloud Memos to the expected-active baseline because both are present in the verified live source.
- Preserved the live GoreeCloud VPS Ping definition as an explicit ICMP/NetBird cutover blocker rather than approximating it with TCP coverage.
- Confirmed Cloudflare DNS and Google DNS are resolver-specific A-record checks through `1.1.1.1` and `8.8.8.8`; both remain review gates because Monitor v0.1 does not preserve per-monitor resolver choice.
- Confirmed every live Uptime Kuma definition currently has a notification assignment; notification assignments remain intentionally non-imported and require separate Monitor configuration and controlled transition testing.
- Recorded a filesystem-permission review item because the live Uptime Kuma Compose file and production Caddyfile are mode `0664`; no permission change is authorized without owner/group/ACL/application review and rollback validation.
- Added a regression test locking the verified 23-active / 3-retired documented baseline scope.

## Unreleased - kuma-cli v2 live evidence compatibility

- Live target validation confirmed the installed `kuma-cli v2.0.0` interface uses `kuma monitor list`; the previously assumed `kuma config export` and `kuma monitors list --json` commands are not available on the GoreeCloud VPS.
- Confirmed the authenticated v2 monitor-list response is a JSON object keyed by monitor ID. The live probe returned 23 monitor definitions.
- Added fail-closed normalization for the v2 ID-keyed monitor map, including numeric-key validation, monitor-ID/key agreement checks, and deterministic numeric ordering before sanitization.
- Updated the collector to derive the internal Uptime Kuma URL from verified Docker metadata, preferring the attached `proxy` network, while retaining neither the URL nor kuma-cli credentials in the evidence bundle.
- Updated the collector to use the existing protected kuma-cli authentication context and `kuma monitor list` rather than accepting passwords, MFA secrets, or auth tokens as collector arguments.
- Raw monitor-list JSON is now held only in process memory and is sanitized before any Uptime Kuma configuration data is written to disk.
- Live validation confirmed v2 monitor-list output is configuration-only and does not contain heartbeat, status, or ping values. The collector no longer fabricates or requires a runtime snapshot from that source.
- Bumped the evidence schema to version 2 and separated `target_environment_and_configuration_ready_for_review` from `runtime_state_ready_for_comparison`. `ready_for_review` now means the target/configuration bundle is complete enough for review, not that runtime parity has been proven.
- Tightened runtime sanitization so configuration-only lists with no heartbeat data are rejected rather than silently converted into all-unknown runtime evidence.
- Updated migration, baseline, cutover, README, and live-evidence documentation to remove invalid v2 commands and keep runtime comparison as a separate later acceptance gate.
- Expanded the automated application suite from 68 to 71 tests with v2 monitor-map normalization, mismatched-ID rejection, and configuration-only/runtime-separation coverage.
- Preserved the frozen live-evidence candidate in PR #5 unchanged and continued the correction on a new stacked compatibility branch.

## Unreleased - Live acceptance evidence readiness

- Added `scripts/collect_live_acceptance_evidence.py` as a read-only operator workflow for collecting the first live GoreeCloud Monitor/Uptime Kuma target-environment evidence before any Monitor deployment.
- The collector does not invoke `sudo`, change Uptime Kuma, alter Docker networks, modify Caddy, change DNS/NetBird/firewall state, or deploy Monitor.
- Added host evidence for identity, operating-system version, interface addresses, routes, listening sockets, Docker/Compose versions, running container identities/states, and Uptime Kuma network context.
- Added file fingerprinting for the current Uptime Kuma Compose file and production Caddyfile without copying either file's contents into the evidence bundle.
- Added a pure-Python Uptime Kuma configuration sanitizer that retains only migration/reconciliation-relevant fields and replaces authentication material, request content, certificate material, connection strings, and other known sensitive values with a non-secret presence sentinel.
- The redaction sentinel remains non-empty so the existing migration importer continues to fail closed with manual-authentication/configuration review instead of treating the sanitized monitor as credential-free.
- Added URL sanitization for user information, URL query strings, and URL fragments; sanitized URL material also forces the existing sensitive-configuration blocker.
- Added malformed URL-port handling so hostile or malformed source configuration cannot crash credential redaction.
- Added a test invariant requiring the evidence sanitizer's sensitive-field policy to remain exactly synchronized with the migration importer's sensitive-field policy.
- Unknown non-empty Uptime Kuma source fields are omitted by value and recorded by field name for later review rather than being copied blindly into evidence.
- Added a minimal runtime sanitizer retaining only monitor ID/name/type/active state plus heartbeat status and response time; target URLs and heartbeat diagnostic messages are excluded.
- The original candidate assumed a raw `kuma config export` temporary-file path and a separate monitor-list runtime snapshot; the later kuma-cli v2 compatibility section above supersedes those live-command assumptions while preserving this frozen source layer for traceability.
- Added restrictive evidence-directory/archive permissions, SHA-256 file checksums, collection-failure reporting, and exact collector-revision capture when the collector is run from a Git checkout.
- Added `docs/live-acceptance-evidence.md` defining the preferred NetBird SSH execution path, default documented VPS paths, override rules, evidence contents, sanitization boundary, review steps, classification, and explicit limits on what collection proves.
- Expanded the automated application suite from 60 to 68 tests with sanitizer secrecy, importer fail-closed compatibility, future sensitive-field policy drift, malformed URL handling, minimal runtime evidence, loader compatibility, and collector import/parser coverage.
- Opened stacked draft PR #5 against the frozen cutover-readiness candidate so this source-only evidence layer can be validated independently without modifying production.

## Unreleased - Cutover and rollback readiness

- Added a sanitized documented Uptime Kuma baseline manifest reconciled from the GoreeCloud monitor inventory and later retirement records rather than treating the older written inventory as live authority.
- Recorded 21 monitors documented as expected active after applying the recorded Flatnotes, Linkding, and Termix retirements, while preserving those three names as expected-retired reconciliation checks.
- Added `reconcileuptimebaseline` to compare a fresh live sanitized Uptime Kuma configuration snapshot with the documented baseline and fail closed on expected-missing, retired-present, unexpected-live, duplicate/invalid source entries, unsupported mappings, migration review items, and documented cutover blockers.
- Kept reconciliation reports sanitized so target URLs, private addresses, request headers, notification assignments, and reusable credentials are not copied into acceptance artifacts.
- Preserved GoreeCloud VPS Ping as an explicit cutover blocker because its private NetBird layer-3 reachability semantics are not identical to TCP 22/443 checks.
- Added explicit manual-review gates for the documented Cloudflare DNS and Google DNS checks because the written scope is resolver-specific and Monitor v0.1 does not automatically preserve Uptime Kuma custom-resolver behavior.
- Added `docs/cutover-and-rollback.md` defining the release unit, parallel-acceptance prerequisites, required rollback bundle, cutover order, rollback triggers, rollback sequence, observation boundary, and database-schema rollback rule.
- Added an immediate-predecessor rollback-compatibility GitHub Actions workflow pinned to frozen deployment candidate `992e64072602a02513bc07a1dd4631e47e87035a`.
- The rollback gate requires an unchanged Django migration set for direct application rollback evidence, builds both exact application revisions, seeds PostgreSQL through the predecessor, reads and updates the state through the candidate, then proves the predecessor can read the candidate-written state again.
- Explicitly limits that rollback proof to immediate-predecessor application/database compatibility; future migration-bearing releases must prove backward compatibility or use a verified pre-upgrade database restore/downgrade path.
- Expanded the automated application suite from 55 to 60 tests on both SQLite and PostgreSQL 17 with documented-baseline reconciliation coverage.

## Unreleased - Deployment candidate

- Added a separate source-controlled production Compose topology while preserving the development Compose topology.
- Moved production static-asset collection into the immutable application image and made the runtime entrypoint side-effect free.
- Added an explicit one-shot `migrate` service so web and worker startup is blocked until schema migration completes successfully.
- Added traceable application-image requirements and digest-pinned PostgreSQL enforcement for the production topology.
- Added purpose-specific production deployment templates for Compose interpolation, Monitor application configuration, and PostgreSQL credentials.
- Added explicit PostgreSQL bind-mounted persistence under the GoreeCloud Docker data model.
- Added an internal-only database network and externally supplied Caddy proxy network with no production host-published Monitor or PostgreSQL ports.
- Hardened production application services with non-root image execution, read-only root filesystems, bounded tmpfs, `cap_drop: ALL`, and `no-new-privileges`.
- Kept privileged mode, host networking, device mappings, Docker socket access, and added Linux capabilities out of the production topology.
- Added `validate_production_compose.py` to fail closed on production Compose contract violations.
- Added a disposable production-topology CI job that resolves a PostgreSQL digest, creates isolated production-style configuration and storage, creates a disposable external proxy network, starts the complete stack, verifies runtime health/security/no-port invariants, runs target preflight inside the deployed web container, verifies one-shot migration success, and tears the stack down.
- Documented the ICMP/Ping baseline as distinct network-layer evidence rather than silently treating TCP 22/443 as exact parity.
- Deliberately retained ICMP/Ping as a cutover blocker instead of adding privileged mode, `CAP_NET_RAW`, host networking, or an unnecessary sidecar.

## Unreleased - Migration readiness

- Added sanitized audit support for kuma-cli/Uptime Kuma JSON configuration snapshots.
- Added conservative mapping for HTTP/HTTPS, keyword, simple JSON-query, TCP/port, DNS, and push monitors.
- Added paused-by-default Uptime Kuma import with atomic strict mode, optional partial import, dry-run support, and sanitized migration reports.
- Added explicit blockers for unsupported monitor semantics, embedded sensitive request configuration, per-monitor proxies, disabled TLS verification, and other unsafe or non-equivalent settings.
- Added definition comparison tooling for staged Uptime Kuma-to-Monitor review.
- Added live parallel runtime-state and response-time comparison tooling for separately validated sanitized runtime snapshots, including explicit mismatch, missing, duplicate, and Monitor-only classifications.
- Added fail-closed target-environment preflight for production configuration, PostgreSQL connectivity, migration state, constrained target allowlists, HTTPS/cookie posture, and complete notification configuration.
- Added PostgreSQL CI execution of the production-style target preflight before backup/restore proof.
- Hardened ntfy transition publishing to require the dedicated write-only bearer token, reject partial configuration, and disable environment proxy/netrc credential inheritance.
- Updated the Glaze UI Settings posture so ntfy is reported as configured only when base URL, topic, and publisher token are all present.
- Documented that unsupported source monitors remain cutover blockers. The current GoreeCloud baseline includes an ICMP/Ping reachability monitor, which is intentionally not emulated by the v0.1 importer and requires a separately approved low-privilege design or replacement coverage before Uptime Kuma retirement.
- Added migration documentation preserving Uptime Kuma as authoritative until parallel acceptance and explicit cutover.

## 0.1.0 - Development foundation

- Native Django/PostgreSQL monitoring foundation.
- Glaze UI dashboard and authenticated monitor management.
- HTTP/HTTPS, TCP, DNS, and heartbeat checks.
- TLS-expiration degradation state.
- Failure/recovery thresholds and incident history.
- SSRF-aware destination policy.
- ntfy transition publishing and read-only Manager API.
- Docker/Compose, health checks, CI, tests, backup and recovery documentation.
- Portable database index names validated against Django system checks.
- GitHub Actions pinned to exact commits for checkout v7.0.1 and setup-python v7.0.0.
- Versioned monitor-definition and maintenance-window export/import with secret and runtime-state exclusion.
- PostgreSQL 17 integration tests and disposable logical backup/restore proof.
- Fail-closed Python dependency audit and HIGH/CRITICAL container-image vulnerability scan.
- Production-mode container build and smoke validation.
- Supported Python runtime narrowed to the tested Python 3.13 release line.
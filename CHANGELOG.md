# Changelog

## Unreleased - Canonical cross-platform product identity

- Established `assets/identity/goreecloud-monitor-icon.svg` as the authoritative GoreeCloud Monitor application icon, using the product-specific availability pulse and protected healthy-state indicator rather than the GoreeCloud platform logo or a generic letter mark.
- Removed the superseded `static/monitoring/img/monitor-mark.svg` asset so the repository no longer contains two competing primary Monitor identities.
- Wired the canonical icon into the Glaze UI web shell, authentication experience, browser metadata, and privileged Django administration surface.
- Added local 16, 32, 48, 192, and 512 pixel web SVG representations plus a dedicated edge-to-edge mask-safe 512 pixel installation asset and `static/monitoring/site.webmanifest`.
- Added source-controlled Linux/AppImage launcher input under `packaging/appimage/` and Android adaptive, round, and monochrome launcher inputs under `packaging/android/res/`, preserving the same underlying Monitor pulse/status identity across platform adaptations.
- Kept the delivery boundary explicit: Monitor remains a Django web/API application plus monitoring worker. The AppImage and Android assets are authoritative launcher inputs for future approved clients, not claims that standalone AppImage or APK clients are already implemented.
- Added `docs/product-identity.md` and expanded Glaze UI conformance documentation with canonical identity ownership, maskable-icon behavior, Wardveil separation, cross-platform change control, and manual small-size/launcher acceptance requirements.
- Expanded automated Glaze/product-identity coverage to validate shared icon geometry, byte-identical canonical/web source, required web sizes, local manifest metadata, dedicated maskable purpose, Android adaptive resources, monochrome resources, and XML/SVG syntax.
- CI on candidate `20cc5ba74a4251a1e93e8275cc4e615ec4f7e262` correctly found one stale pre-existing dashboard test that still expected the deleted `monitor-mark.svg`; the new cross-platform icon conformance test itself passed. The legacy dashboard assertion was corrected to require the canonical icon and manifest and to reject the superseded filename.
- Added no Django migration, no remote asset dependency, no analytics or tracking, no reusable credential material, and no production Uptime Kuma, Caddy, DNS, NetBird, firewall, runtime, or cutover change.

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
# Changelog

## Unreleased - Cutover and rollback readiness

- Added a sanitized documented Uptime Kuma baseline manifest reconciled from the GoreeCloud monitor inventory and later retirement records rather than treating the older written inventory as live authority.
- Recorded 21 documented expected-active monitors after applying the recorded Flatnotes, Linkding, and Termix retirements, while preserving those three names as expected-retired reconciliation checks.
- Added `reconcileuptimebaseline` to compare a fresh live kuma-cli export with the documented baseline and fail closed on expected-missing, retired-present, unexpected-live, duplicate/invalid source entries, unsupported mappings, migration review items, and documented cutover blockers.
- Kept reconciliation reports sanitized so target URLs, private addresses, request headers, notification assignments, and reusable credentials are not copied into acceptance artifacts.
- Preserved GoreeCloud VPS Ping as an explicit cutover blocker because its private NetBird layer-3 reachability semantics are not identical to TCP 22/443 checks.
- Added explicit manual-review gates for the documented Cloudflare DNS and Google DNS checks because the written scope is resolver-specific and Monitor v0.1 does not automatically preserve custom Uptime Kuma resolver semantics.
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

- Added sanitized audit support for kuma-cli/Uptime Kuma JSON exports.
- Added conservative mapping for HTTP/HTTPS, keyword, simple JSON-query, TCP/port, DNS, and push monitors.
- Added paused-by-default Uptime Kuma import with atomic strict mode, optional partial import, dry-run support, and sanitized migration reports.
- Added explicit blockers for unsupported monitor semantics, embedded sensitive request configuration, per-monitor proxies, disabled TLS verification, and other unsafe or non-equivalent settings.
- Added definition comparison tooling for staged Uptime Kuma-to-Monitor review.
- Added live parallel runtime-state and response-time comparison from `kuma monitors list --json`, including explicit mismatch, missing, duplicate, and Monitor-only classifications.
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

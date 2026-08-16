# Changelog

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

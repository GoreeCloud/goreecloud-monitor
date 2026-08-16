# Changelog

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

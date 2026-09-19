# GoreeCloud Monitor — Competitive Objectives

**Document Internal Version Number:** 2026.09.18.1  
**Document External Version Number:** 1.0.0  
**Status:** Active objective record  
**As of:** September 18, 2026

## Purpose

These are improvement and differentiation objectives, not claims that GoreeCloud Monitor currently outperforms another monitoring product.

## Objectives

1. **Provide first-party monitoring ownership.** Keep checks, incidents, maintenance, recovery, and alert-delivery evidence under GoreeCloud-controlled software.
2. **Match required predecessor coverage without inheriting predecessor architecture.** Reconcile useful Uptime Kuma definitions while keeping Monitor native and independently maintainable.
3. **Use low-privilege network checks.** Prefer bounded user-space/approved kernel interfaces rather than privileged raw-socket containers.
4. **Make alerts durable.** Persist transition-delivery intent before network publication and replay safely after process/host interruption.
5. **Avoid notification loops.** Require independent outage reporting for failures that break the normal Monitor → Notify path.
6. **Keep target semantics explicit.** Treat DNS resolver behavior, Ping/ICMP, TLS, retries, thresholds, and maintenance as evidence-backed contracts.
7. **Make recovery a release property.** Require database-native backup, isolated restore, migration compatibility, and rollback evidence.
8. **Minimize monitoring-data exposure.** Avoid secrets and unnecessary raw target diagnostics in logs, alerts, and evidence bundles.
9. **Maintain private deployment.** Keep production backend/database ports off the host/public network and use approved private ingress.
10. **Keep design/accessibility evidence current.** Use the current Stable Glaze UI target and require application-specific acceptance.
11. **Integrate GoreeCloud platform systems truthfully.** Preserve fail-closed states for unaccepted Manager, Privacy Shield, Wardveil, Everkeep, Mesh, Identity, Policy, and Observability obligations.
12. **Separate merge, release, activation, and production authority.** Never treat green CI or a source merge as automatic production promotion.


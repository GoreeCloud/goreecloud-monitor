# GoreeCloud Monitor — Competitive Objectives

**Document Internal Version Number:** 2026.09.19.1  
**Document External Version Number:** 1.1.0  
**Status:** Active objective record  
**As of:** September 19, 2026

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

13. **Absorb scheduled-job and dead-man monitoring as a first-party Monitor responsibility.** Healthchecks is now a benchmark reference rather than an active GoreeCloud runtime dependency; Monitor should cover scheduled jobs, backup/maintenance heartbeats, and missed-run detection without inheriting Healthchecks' application architecture.
14. **Support schedule-aware job checks.** Provide simple period-plus-grace schedules and cron/time-zone semantics as core capability, with systemd OnCalendar compatibility where it provides practical GoreeCloud value.
15. **Model job lifecycle signals explicitly.** Support start, success, failure/exit-status, and bounded log/event signals so Monitor can distinguish a job that never ran from one that started, failed, or exceeded its allowed run time.
16. **Track job run duration and overruns.** Correlate start/completion events, retain useful duration history, and detect runs that exceed their configured execution budget.
17. **Provide durable job-event history.** Preserve bounded event history, status flips, missed-run incidents, recovery, and relevant diagnostic metadata without turning Monitor into a log-aggregation platform.
18. **Keep organization and access GoreeCloud-native.** Support tags/labels, collections or projects, filtering, and scoped administration while preferring GoreeCloud Identity and GoreeCloud Policy for durable authorization instead of recreating a separate account system.
19. **Expose safe automation interfaces.** Provide a versioned management API with scoped read-only/read-write credentials, token rotation, rate limiting, and secret-safe responses for job-check administration and signal ingestion.
20. **Treat auto-provisioning as controlled convenience.** If slug/name-based automatic check creation is implemented, keep it policy-gated, auditable, rate-limited, and reviewable rather than allowing unrestricted production monitor creation.
21. **Provide useful status/reporting surfaces without unnecessary public exposure.** Support private badges/JSON summaries, repeated-down reminders, and periodic job-health reports; public status pages remain optional unless a real GoreeCloud requirement is approved.
22. **Keep notification transport outside Monitor.** Monitor should own detection, incident state, routing intent, reminders, and report generation while GoreeCloud Notify owns delivery/fan-out. Monitor should not duplicate Healthchecks' notification-provider catalog.
23. **Evaluate email-based signal ingestion separately.** Email-triggered start/success/failure classification may be added when justified, but only after SMTP abuse, spoofing, parsing, retention, privacy, and operational-security risks are accepted.


## Healthchecks benchmark boundary

Healthchecks is a primary benchmark for scheduled-job, cron-style dead-man, backup-heartbeat, and task-run monitoring. This benchmark does **not** mean GoreeCloud Monitor is a Healthchecks fork, that Healthchecks remains an active GoreeCloud dependency, or that the capabilities above are already implemented.

The current source already has generic push/heartbeat monitoring, but full Healthchecks-style scheduled-job parity is planned work. Current functionality remains authoritative in `FEATURES.md`; implementation obligations and priority remain authoritative in `FEATURE-ROADMAP.md` and GoreeCloud Tasks Management.

Healthchecks capabilities worth learning from include period/grace and cron-style scheduling, explicit start/success/failure signals, run-duration tracking, event history, tags/projects, scoped APIs, auto-provisioning, status summaries, reminders/reports, and optional alternate signal-ingestion paths. GoreeCloud may implement these differently when security, privacy, maintainability, platform integration, or product scope requires a stronger design.

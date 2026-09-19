# Replacement Activation and Rollback Readiness

Uptime Kuma and ntfy were permanently retired from `goreecloud-vps-01` on September 18, 2026. This procedure therefore governs **GoreeCloud Monitor replacement activation and Monitor rollback**, not a side-by-side cutover from a live predecessor.

## Activation prerequisites

Before Monitor is promoted to production monitoring authority:

1. Use an exact reviewed Monitor revision and immutable image.
2. Complete source CI, rollback-compatibility, Notify producer, current Glaze UI, and platform-system gates.
3. Verify the target Compose/runtime topology and protected configuration.
4. Create a fresh PostgreSQL backup and prove isolated restore.
5. Reconcile preserved Uptime Kuma definitions against current active services; do not import retired endpoints blindly.
6. Activate imported or recreated monitor definitions only after explicit review.
7. Validate representative HTTP/HTTPS, TCP, TLS, DNS, heartbeat, Ping/ICMP, scheduled-job start/success/failure/missed-run/overrun, maintenance, incident, and threshold behavior.
8. Validate GoreeCloud Notify first-write, replay, conflict, restart/replay, and administrator receipt.
9. Validate independent outage alerting for failures that prevent the ordinary Monitor → Notify chain from operating.
10. Record explicit production-activation approval.

## Required rollback bundle

Before production activation preserve:

- exact candidate and previous known-good Monitor revisions/images;
- reviewed Compose and protected configuration fingerprints;
- current PostgreSQL backup plus restore evidence;
- schema migration and rollback-compatibility evidence;
- current private DNS/Gateway/NetBird configuration evidence;
- Notify producer configuration metadata without reusable credentials;
- acceptance report and activation timestamps.

Preserved Uptime Kuma recovery data may remain available as historical recovery evidence, but it is not the ordinary production rollback target.

## Rollback triggers

Rollback or controlled deactivation should occur when required acceptance properties are lost, including:

- database integrity or migration uncertainty;
- repeated false DOWN/RECOVERED transitions;
- missed monitored failures;
- missed scheduled-job failures, false late-job incidents, incorrect cron/time-zone evaluation, or broken job credential handling;
- broken Ping/DNS/TLS semantics on required targets;
- persistent Notify delivery failures or outbox backlog;
- duplicate notification fanout;
- loss of private publication or authentication boundaries;
- loss of required security, privacy, continuity, accessibility, or platform-system guarantees.

## Rollback sequence

1. Stop further configuration changes and preserve evidence.
2. Stop or isolate the failed Monitor candidate as needed.
3. Restore the previous known-good Monitor application image/configuration.
4. Restore the compatible PostgreSQL state or verified pre-upgrade backup when schema rollback requires it.
5. Restore only directly affected Gateway/DNS/NetBird/notification configuration.
6. Validate the known-good Monitor release against representative healthy and failing targets.
7. Validate notification delivery and independent outage alerting.
8. Record the rollback result and retain failed-release evidence for investigation.

Do not silently restore Uptime Kuma as production authority. Any production restoration of Uptime Kuma requires separate explicit authorization.

## Database rollback boundary

Database rollback is not equivalent to application rollback. Every migration-bearing release must prove immediate-predecessor compatibility or preserve a verified pre-upgrade database backup and complete release unit.

The scheduled-job foundation introduces migration `0004_scheduled_job_monitor`. A predecessor at migration `0003_notification_outbox` does not understand `JOB` definitions or `JobEvent` rows. Before a controlled downgrade to that predecessor:

1. preserve/export any scheduled-job definitions or event evidence that must survive the rollback;
2. stop scheduled-job signal senders or rotate/revoke their candidate credentials as appropriate;
3. remove candidate-only `JOB` monitor rows so the predecessor cannot encounter an unsupported monitor type;
4. migrate the candidate database back to `monitoring 0003`;
5. start the predecessor image and verify preserved non-JOB monitors plus the notification outbox.

Dropping candidate-only scheduled-job schema is a controlled rollback action and can discard `JobEvent` history. Use a pre-upgrade backup when that data must be recoverable rather than relying on destructive schema downgrade.

## Completion boundary

Replacement activation is complete only when Monitor is verified at the authoritative target, rollback/recovery is proven, notifications and independent outage alerting are accepted, directly affected documentation/task state is reconciled, and explicit production approval exists.

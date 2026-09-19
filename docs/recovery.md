# Recovery

A recovery test must prove that an empty replacement environment can:

1. Restore the PostgreSQL database.
2. Start the web application and worker at the intended release.
3. Load monitor definitions and incident history.
4. Resume checks without creating duplicate uncontrolled DOWN notifications.
5. Authenticate the administrator.
6. Serve the read-only Manager API only with the correct credential.
7. Re-establish approved GoreeCloud Gateway ingress and private network access in the target environment.

## Portable monitor-definition recovery

Monitor definitions can be exported separately from the runtime database:

```bash
python manage.py exportmonitors --output monitor-definitions.json
```

The export is versioned JSON. Version 2 preserves scheduled-job mode, schedule expression, time zone, grace, and maximum-runtime settings in addition to the other monitor definitions and maintenance windows. It deliberately excludes heartbeat tokens, current runtime state, check history, incidents, credentials, and notification secrets. Version 1 remains importable for non-JOB definitions, but version-1 JOB entries are rejected because that format never preserved their schedule fields.

An empty replacement instance can validate the file without keeping changes:

```bash
python manage.py importmonitors monitor-definitions.json --dry-run
```

After validation, import into an empty target:

```bash
python manage.py importmonitors monitor-definitions.json
```

Push- and scheduled-job signal credentials are newly generated on import. Every heartbeat or job-signal sender must therefore be updated after a portable recovery.

Portable definition export supplements rather than replaces PostgreSQL backup. A production recovery must still validate complete database restoration and application state.

Migration `0006_job_oncalendar_schedule` is deliberately fail-safe on downgrade. If an OnCalendar definition exists when the schema is reversed to the immediate predecessor, the migration converts that definition to Simple mode only after disabling it, sets its state to Paused, clears the predecessor-visible schedule field, and records the former OnCalendar expression in the bounded recovery message. Re-upgrade and restore the exact schedule from a pre-downgrade PostgreSQL backup or a version-2 portable definition export before re-enabling it.

## Scheduled-job recovery evidence

For a JOB monitor, authorized staff can open its Recovery & Export surface to inspect the current evaluator result, state-preserving event anchors, retained history counts, and retention posture. The associated versioned JSON export provides retained scheduled-job event evidence in bounded pages and excludes reusable credentials and stored credential verifiers.

This event export is not an import or database-restore format. Authoritative recovery of job definitions, event history, incidents, state, and application data remains PostgreSQL backup/restore. Use the export for inspection, incident evidence, and controlled analysis after a recovery.

Uptime Kuma was retired from the VPS on September 18, 2026. Preserved Uptime Kuma artifacts are historical migration/recovery evidence only and must not be treated as an active rollback monitoring platform without separate authorization.

# Recovery

A recovery test must prove that an empty replacement environment can:

1. Restore the PostgreSQL database.
2. Start the web application and worker at the intended release.
3. Load monitor definitions and incident history.
4. Resume checks without creating duplicate uncontrolled DOWN notifications.
5. Authenticate the administrator.
6. Serve the read-only Manager API only with the correct credential.
7. Re-establish private Caddy and network access in the target environment.

## Portable monitor-definition recovery

Monitor definitions can be exported separately from the runtime database:

```bash
python manage.py exportmonitors --output monitor-definitions.json
```

The export is versioned JSON. It includes monitor definitions and maintenance windows, but deliberately excludes heartbeat tokens, current runtime state, check history, incidents, credentials, and notification secrets.

An empty replacement instance can validate the file without keeping changes:

```bash
python manage.py importmonitors monitor-definitions.json --dry-run
```

After validation, import into an empty target:

```bash
python manage.py importmonitors monitor-definitions.json
```

Push-monitor heartbeat tokens are newly generated on import. Every heartbeat sender must therefore be updated after a portable recovery.

Portable definition export supplements rather than replaces PostgreSQL backup. A production recovery must still validate complete database restoration and application state.

Keep Uptime Kuma available as the rollback monitoring platform until Monitor passes the full recovery test and the production cutover is explicitly approved.

# Backup

A production Monitor backup must protect:

1. PostgreSQL database state.
2. Deployment and environment configuration required to rebuild the service.
3. The exact source/release identity and container image identity.
4. Protected secret material through the approved GoreeCloud secrets process, not Git.

The repository is source control, not the runtime database backup.

## PostgreSQL logical backup

An authenticated backup context may create a custom-format logical backup with:

```bash
pg_dump -Fc --file monitor.dump goreecloud_monitor
```

The exact authentication and repository destination are environment-specific and must use approved GoreeCloud secret handling. The backup artifact must be transferred into the approved GoreeCloud backup system; it must not be committed to Git.

## Restore proof

CI performs a disposable PostgreSQL recovery proof using the same exact PostgreSQL 17.10 image family used by the development Compose definition. The workflow:

1. Applies current migrations.
2. Runs the automated test suite against PostgreSQL.
3. Seeds a known Monitor record.
4. Creates a `pg_dump` custom-format backup.
5. Restores that backup into a newly created empty database.
6. Reconnects Django to the restored database and verifies the known record.

This proves the source-level logical backup and restore mechanism. It does not replace a target-environment restore test using the actual production storage paths, secrets, backup repository, retention policy, and release image.

A successful backup job is insufficient without restore validation.

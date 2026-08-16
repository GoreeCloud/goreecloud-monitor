# Backup

A production Monitor backup must protect:

1. PostgreSQL database state.
2. Deployment and environment configuration required to rebuild the service.
3. The exact source/release identity and container image identity.
4. Protected secret material through the approved GoreeCloud secrets process, not Git.

The repository is source control, not the runtime database backup.

A logical PostgreSQL backup should be created with a tool such as `pg_dump` from an authenticated backup context and sent to the approved GoreeCloud backup system. Backup success is insufficient without restore validation.

# Recovery

A recovery test must prove that an empty replacement environment can:

1. Restore the PostgreSQL database.
2. Start the web application and worker at the intended release.
3. Load monitor definitions and incident history.
4. Resume checks without creating duplicate uncontrolled DOWN notifications.
5. Authenticate the administrator.
6. Serve the read-only Manager API only with the correct credential.
7. Re-establish private Caddy and network access in the target environment.

Keep Uptime Kuma available as the rollback monitoring platform until Monitor passes this recovery test and the production cutover is explicitly approved.

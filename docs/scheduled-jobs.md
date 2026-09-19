# Scheduled Job / Dead-Man Monitoring

## Purpose

GoreeCloud Monitor can monitor scheduled jobs, backups, maintenance tasks, synchronization jobs, and other periodic workloads without requiring a separate Healthchecks runtime.

This capability is native GoreeCloud Monitor functionality. Healthchecks is a benchmark reference only.

## Monitor type

Create a monitor with type `Scheduled job / dead-man`.

Two schedule modes are available:

- **Simple interval** — the job must complete within `interval_seconds + job_grace_seconds` after the last successful completion. Before the first success, the creation time is the initial baseline.
- **Cron schedule** — a strict cron expression is evaluated in the configured IANA time zone. The job must complete inside the current schedule window plus the configured grace period.

Cron parsing uses the repository-pinned `croniter` dependency with strict validation. IANA time-zone lookup uses the repository-pinned Python `tzdata` fallback so schedule interpretation does not depend on host image zone-data availability.

## Signals

The signal endpoint is:

`POST /api/v1/jobs/signal/`

Authenticate with:

`Authorization: Bearer <credential>`

The credential is generated or rotated from the staff-only Monitor interface. Monitor persists only a SHA-256 verifier; the reusable credential is shown once.

The request body must be JSON and may contain only:

- `event` — required. Supported values: `start`, `success`, `failure`/`fail`, or `log`.
- `event_id` — optional UUID idempotency identifier. Reusing the same ID with the same signal returns the original event; materially different reuse is rejected.
- `run_id` — optional correlation identifier, maximum 128 characters.
- `exit_code` — optional signed 32-bit integer. A `success` event may omit it or send `0`; non-zero exit codes are rejected on `success` and should be reported with a `failure` event.
- `message` — optional bounded diagnostic text, maximum 500 characters.

A `start` event without a `run_id` receives a generated run identifier in the response. A later terminal event may provide that identifier. If a terminal event omits it, Monitor correlates the most recent unmatched start when practical.

## Replay and rate limiting

`MONITOR_JOB_SIGNAL_MAX_PER_MINUTE` controls the per-monitor ingestion budget and defaults to 5 signals per minute. The configured value is bounded to 1–600. When the budget is exceeded, Monitor returns HTTP 429 with `Retry-After` and does not persist the rejected signal.

For network retry safety, clients should send a stable UUID `event_id` for each logical signal. If the exact same signal is retried with the same `event_id`, Monitor returns the previously persisted event and marks the response as replayed without creating another row or consuming another rate-limit slot. Reusing an `event_id` for different event type, exit status, message, or explicitly supplied run ID returns HTTP 409.

## State evaluation

The JOB evaluator also derives a presentation-only lifecycle phase from the same evidence used for ordinary Monitor state. These phases do not create a second incident state machine:

- **Awaiting** — the first/current completion window is still open and no overdue condition exists. Underlying state is Unknown.
- **Started** — a START has been received and the run remains inside its runtime budget. Underlying state is Up.
- **Completed** — the latest required completion is current. Underlying state is Up.
- **Failed** — the latest terminal event explicitly reported failure. Underlying observation is Down and ordinary failure thresholds apply.
- **Late** — a required completion or started-run runtime deadline has been exceeded. Underlying observation is Down and ordinary failure thresholds apply.

- A newly created cron monitor does not inherit missed occurrences from before its creation time; its first enforceable window begins with the first schedule at or after creation.
- A recent successful completion keeps the job healthy until the next deadline.
- A reported failure produces a failed Down observation and enters the ordinary Monitor failure-threshold/incident pipeline; the configured failure threshold controls when the monitor state transitions to Down.
- A started job is considered running.
- A started job must complete within its runtime limit. An explicit non-zero `job_max_runtime_seconds` sets that limit; when it is `0`, Monitor uses `job_grace_seconds` as the started-job runtime limit. Exceeding the limit evaluates the job as Down.
- If the required simple or cron completion does not arrive before the configured grace deadline, Monitor evaluates it as Down.
- Recovery uses the existing Monitor recovery-threshold and incident-closing logic.

Scheduled-job transitions use the same durable GoreeCloud Notify outbox as other Monitor transitions when Notify is enabled and accepted.

## Event history

Monitor records bounded event metadata including:

- event type;
- receive time;
- run identifier;
- exit code when supplied;
- correlated duration for terminal events;
- bounded message text.

The staff monitor-detail view exposes recent job-event history. Non-staff viewers do not receive reusable credentials or administrative diagnostics.

### Retention

`MONITOR_JOB_EVENT_RETENTION_DAYS` controls ordinary job-event history retention and defaults to 90 days. The worker prunes history automatically at the cadence set by `MONITOR_HISTORY_PRUNE_INTERVAL_SECONDS`, which defaults to one hour. For correctness, the latest terminal event and any unmatched latest START are protected from ordinary pruning until newer state supersedes them. This preserves missed-run, failure, and overrun evaluation for infrequent or currently running jobs without keeping an unbounded general event archive.

Because idempotency identities are stored on event rows, retry convergence for an old `event_id` is guaranteed only while that event remains retained. A pruned historical identifier may later be accepted again.

### Recovery and export

Authorized staff can open the scheduled-job recovery surface from a JOB monitor. It shows the current evaluator result, retained-event counts, the latest terminal event, any unmatched START that is still part of current state, retention posture, and the oldest retained event. The surface is diagnostic and does not expose the reusable bearer credential or its stored verifier.

The same recovery surface provides a versioned `goreecloud-monitor-job-events-v1` JSON export of retained event evidence. Export pages are cursor-based using `before_id`, default to 1,000 events, and are capped at 5,000 events per request. Each page reports whether more data remains and provides the next cursor. The export includes schedule metadata, the current lifecycle phase and underlying evaluation state, retention metadata, and retained event rows; it is supplemental recovery/incident evidence rather than an import format or PostgreSQL restore substitute.

## Security boundaries

- Do not place the bearer credential in the URL.
- Do not log the credential.
- Do not include secrets in the optional message field.
- The endpoint rejects unknown fields and oversized signal payloads.
- Rotate the credential when exposure is possible.
- Production acceptance still requires target deployment, live signal, incident, recovery, credential-rotation, backup/restore, and Notify-path validation.

## Remaining parity work

The current foundation does not yet provide the complete planned Healthchecks-style feature set. Outstanding work includes:

- systemd OnCalendar evaluation/support;
- tags/labels and projects/collections;
- scoped job-management APIs;
- policy-gated automatic provisioning;
- private badges/JSON summaries, repeated-down reminders, and periodic reports;
- separately approved email-based signal ingestion.

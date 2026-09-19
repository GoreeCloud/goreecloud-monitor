# Scheduled Job / Dead-Man Monitoring

## Purpose

GoreeCloud Monitor can monitor scheduled jobs, backups, maintenance tasks, synchronization jobs, and other periodic workloads without requiring a separate Healthchecks runtime.

This capability is native GoreeCloud Monitor functionality. Healthchecks is a benchmark reference only.

## Monitor type

Create a monitor with type `Scheduled job / dead-man`.

Two schedule modes are available:

- **Simple interval** — the job must complete within `interval_seconds + job_grace_seconds` after the last successful completion. Before the first success, the creation time is the initial baseline.
- **Cron schedule** — a strict cron expression is evaluated in the configured IANA time zone. The job must complete inside the current schedule window plus the configured grace period.

Cron parsing uses the repository-pinned `croniter` dependency with strict validation.

## Signals

The signal endpoint is:

`POST /api/v1/jobs/signal/`

Authenticate with:

`Authorization: Bearer <credential>`

The credential is generated or rotated from the staff-only Monitor interface. Monitor persists only a SHA-256 verifier; the reusable credential is shown once.

The request body must be JSON and may contain only:

- `event` — required. Supported values: `start`, `success`, `failure`/`fail`, or `log`.
- `run_id` — optional correlation identifier, maximum 128 characters.
- `exit_code` — optional signed 32-bit integer. A `success` event may omit it or send `0`; non-zero exit codes are rejected on `success` and should be reported with a `failure` event.
- `message` — optional bounded diagnostic text, maximum 500 characters.

A `start` event without a `run_id` receives a generated run identifier in the response. A later terminal event may provide that identifier. If a terminal event omits it, Monitor correlates the most recent unmatched start when practical.

## State evaluation

- A newly created cron monitor does not inherit missed occurrences from before its creation time; its first enforceable window begins with the first schedule at or after creation.
- A recent successful completion keeps the job healthy until the next deadline.
- A reported failure evaluates as Down and enters the ordinary Monitor failure/incident pipeline.
- A started job is considered running.
- If `job_max_runtime_seconds` is non-zero and a started job exceeds that limit, Monitor evaluates it as Down.
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

## Security boundaries

- Do not place the bearer credential in the URL.
- Do not log the credential.
- Do not include secrets in the optional message field.
- The endpoint rejects unknown fields and oversized signal payloads.
- Rotate the credential when exposure is possible.
- Production acceptance still requires target deployment, live signal, incident, recovery, credential-rotation, backup/restore, and Notify-path validation.

## Remaining parity work

The current foundation does not yet provide the complete planned Healthchecks-style feature set. Outstanding work includes:

- signal rate limiting and stronger replay/idempotency controls;
- systemd OnCalendar evaluation/support;
- richer explicit Started/Late presentation;
- dedicated job-event retention and recovery controls;
- tags/labels and projects/collections;
- scoped job-management APIs;
- policy-gated automatic provisioning;
- private badges/JSON summaries, repeated-down reminders, and periodic reports;
- separately approved email-based signal ingestion.

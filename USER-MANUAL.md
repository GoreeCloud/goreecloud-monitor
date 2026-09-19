# GoreeCloud Monitor — User Manual

**Document Internal Version Number:** 2026.09.19.1  
**Document External Version Number:** 1.1.0  
**Status:** Repository user manual for the current pre-production source  
**As of:** September 19, 2026  
**Central manual:** `GoreeCloud/User Manuals/User Manual — GoreeCloud Monitor.docx`

## Before using Monitor

GoreeCloud Monitor is not yet production monitoring authority. Use only an approved deployment.

Uptime Kuma is retired and should not be treated as the active Monitor interface.

## Sign in

1. Open the approved private GoreeCloud Monitor URL.
2. Sign in with your authorized account.
3. Use staff privileges only for approved administration.
4. Sign out on shared devices.

Do not weaken authentication, TLS, private-network, or Gateway controls to force access.

## Overview

The Overview surface summarizes monitoring state and recent incidents.

Use it to identify:

- healthy/degraded/down services;
- active incidents;
- maintenance effects;
- recent operational changes.

The UI is not a substitute for raw target verification when troubleshooting an incident.

## Monitors

The Monitors area lists configured checks.

Depending on staff permissions, you can create or edit monitors for supported check types including:

- HTTP/HTTPS;
- TCP;
- DNS;
- Ping/ICMP;
- push/heartbeat;
- scheduled job / dead-man.

Before enabling a monitor, verify the target is current and authorized. Do not reactivate preserved predecessor definitions blindly.

## Heartbeat monitors

Push/heartbeat monitors use a dedicated credential/verifier.

Treat heartbeat credentials as sensitive.

Rotate a heartbeat credential when exposure is possible.

Legacy path-based heartbeat behavior remains restricted and should not be used unless explicitly approved.


## Scheduled job monitors

Scheduled job / dead-man monitors are intended for cron jobs, backups, maintenance tasks, synchronization jobs, and other periodic workloads.

Choose one schedule mode:

- a simple expected interval plus grace period;
- a strict five-field cron expression with an explicit IANA time zone; or
- a native systemd OnCalendar expression. OnCalendar supports multiple newline-separated expressions and may include its own time-zone suffix; otherwise Monitor uses the configured IANA job time zone.

OnCalendar is evaluated inside Monitor. The worker does not call systemd or a shell. Fractional-second calendar expressions are not supported and fail validation.

The optional maximum-runtime setting detects jobs that send a start signal but do not complete within the approved execution budget.

Each scheduled-job monitor has a protected bearer credential. The reusable value is shown only when it is issued or rotated; Monitor stores only a one-way verifier. Job runners may also send a stable UUID `event_id` for retry-safe ingestion; exact retries converge on the original stored event, while conflicting reuse is rejected. Signal ingestion is rate-limited per monitor and returns retry guidance when the configured budget is exceeded.

Approved job runners send HTTPS POST requests to `/api/v1/jobs/signal/` with the bearer credential and an event of `start`, `success`, `failure`, or `log`. Use an optional `run_id` when explicit run correlation is useful.

Do not put credentials in URLs, job names, messages, screenshots, shell history, or ordinary logs.

Recent job events and run durations are visible to authorized administrators on the monitor detail page. JOB detail and recovery surfaces also show a lifecycle phase: **Awaiting**, **Started**, **Completed**, **Failed**, or **Late**. These labels explain scheduled-job progress but do not replace Monitor's underlying Up/Down/Unknown state or incident thresholds. Ordinary job-event history is automatically pruned after the configured retention period, while the minimum latest event state required for safe dead-man evaluation may be kept longer until superseded. Staff can use **Recovery & Export** to inspect those state-preserving anchors and download versioned, paginated JSON evidence of retained events. The export excludes job credentials and is supplemental evidence rather than a database-restore format. A missed schedule, reported failure, or configured runtime overrun can enter the ordinary Monitor incident flow.

This source capability is not yet production acceptance. Validate the actual scheduled job, signal delivery, missed-run behavior, failure/recovery behavior, credential rotation, and notification path on the approved target before relying on it operationally.

## Incidents

Incidents record monitored failures and recovery.

Use incident history to review state changes, not as proof that every underlying root cause has been diagnosed.

## Maintenance

Use maintenance windows for planned periods where expected service behavior should not create normal incidents/alerts.

Keep maintenance scope and duration as narrow as practical.

## Notifications

Monitor publishes transition notifications through GoreeCloud Notify only after the Notify integration is accepted and configured.

Transition delivery uses a durable outbox.

If notification delivery is unavailable, Monitor retains pending outbox records and retries them. Pending outbox state is a production-acceptance blocker.

## Security

The Security surface provides a staff-only, secret-free security posture view.

Do not paste or expose active credentials in notes, monitor labels, target URLs, or screenshots.

## Settings

Settings contain operational controls intended for authorized administrators.

Target allowlists, credentials, retention, notification configuration, and private-network policy must follow the approved deployment procedure.

## Troubleshooting a failing monitor

1. Confirm the target service is actually expected to be active.
2. Review the monitor type and target.
3. Check recent results and incident state.
4. Confirm maintenance is not suppressing normal behavior.
5. For DNS/Ping/TLS behavior, reproduce from the approved worker environment when necessary.
6. Do not broaden network permissions merely to make the check pass.
7. Record unsupported semantics rather than approximating them silently.

## Production and recovery boundary

Backup/restore, PostgreSQL administration, Gateway/DNS/NetBird configuration, Notify producer credentials, and production promotion are administrator responsibilities.

A green check, source test, or successful login does not by itself prove Monitor is production-accepted.


# GoreeCloud Monitor — Privacy Policy

**Document Internal Version Number:** 2026.09.19.1  
**Document External Version Number:** 1.1.0  
**Status:** Repository privacy policy for the current pre-production source  
**As of:** September 19, 2026

## Scope

This policy describes privacy-relevant behavior implemented or required by the current GoreeCloud Monitor source. A deployment operator remains responsible for the actual environment, accounts, monitored targets, retention, backups, and lawful use.

## Data Monitor may process

Depending on configuration, Monitor may process:

- administrator account/session state;
- monitor names, types, targets, configuration, and thresholds;
- response status and bounded diagnostic results;
- DNS/TLS/Ping/TCP/HTTP availability data;
- heartbeat state and verifier metadata;
- scheduled-job definitions, schedule/time-zone settings, one-way credential verifier metadata, lifecycle event times/types, run identifiers, exit codes, bounded messages, and calculated run durations;
- incident and recovery history;
- maintenance windows;
- minimized notification transition metadata;
- security/audit events;
- durable notification outbox metadata;
- backup/recovery and migration evidence.

Monitoring data can reveal sensitive infrastructure relationships even when it does not contain user content.

## Purpose

Monitor processes this data to:

- execute authorized service checks;
- evaluate authorized scheduled jobs for expected completion, reported failure, and runtime overruns;
- determine health/state transitions;
- open/update/recover incidents;
- apply maintenance behavior;
- deliver minimized alert transitions;
- support administration/security controls;
- provide operational evidence;
- support backup, restore, migration, and incident investigation.

## Data minimization

Monitor must not intentionally place reusable credentials, authorization headers, session values, private keys, or protected runtime configuration into routine logs or alert payloads.

Raw target diagnostics should be bounded and retained only when required by the product contract.

Notification payloads are intentionally minimized and should direct administrators back to Monitor for diagnostic detail.

## Network targets

Monitor may connect to configured targets. Administrators are responsible for ensuring those targets are authorized and that network allowlists match the intended deployment.

Private or internal target details should not be exposed outside the approved operational boundary.

## Retention

Check-result, scheduled-job event, incident, audit, and delivered-notification metadata must use bounded retention where the application provides a control. Dedicated scheduled-job event retention is not yet implemented and remains a documented roadmap obligation.

Pending notification-outbox rows are not deleted merely to satisfy retention; they remain operational state until delivered or otherwise explicitly reconciled.

Backups may retain monitored-state data for the approved recovery period and must be protected.

## Sharing and external services

GoreeCloud Notify is the supported alert-delivery integration candidate. Alert payloads must remain minimized.

Any additional third-party service configured by a deployment operator is outside this repository policy unless explicitly documented and approved.

## Security safeguards

Privacy depends on technical safeguards including authentication, authorization, CSRF/session controls, secure transport, private publication, target allowlists, protected credentials, least-privilege containers, vulnerability management, backup protection, and target security validation.

## Platform privacy status

A repository-local Privacy Shield adapter candidate exists, but central/runtime Privacy Shield acceptance is incomplete. This policy must not be used to claim complete Privacy Shield conformance.

## Administrator responsibilities

Administrators must protect credentials, target inventories, backup data, incident evidence, and access to the private monitoring deployment.

Do not use monitor labels, target URLs, scheduled-job run identifiers, event messages, or other ordinary fields as a place to store reusable secrets.

## Changes

Material privacy behavior changes must update this file, applicable project documentation, and Privacy Shield evidence in the same governed workflow.


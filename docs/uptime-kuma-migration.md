# Uptime Kuma Historical Migration and Recovery Reference

## Status

Uptime Kuma was permanently retired from `goreecloud-vps-01` on September 18, 2026. This document is retained only for historical migration provenance, requirement reconciliation, and authorized isolated recovery/testing.

It is not a current cutover plan and does not authorize production restoration of Uptime Kuma.

## Preserved migration behavior

The Monitor importer remains deliberately conservative:

- compatible Uptime Kuma HTTP/HTTPS, TCP, DNS, Ping/ICMP, heartbeat, and related definitions may be mapped only where Monitor can represent their semantics;
- imported monitors remain paused by default;
- authentication material, secrets, and weaker TLS behavior are not copied;
- unsupported or ambiguous settings remain warnings/blockers rather than being silently approximated.

Historical definitions can still be useful for reconstructing required monitoring coverage.

## Current reconciliation rule

Before enabling any definition derived from preserved Uptime Kuma evidence:

1. confirm the target service is currently active;
2. confirm the hostname/address and intended private route are current;
3. confirm Monitor supports the required semantics;
4. remove or leave paused any retired service definition;
5. review thresholds, retries, redirects, DNS resolver behavior, TLS expectations, tags, and notification behavior;
6. activate only the reviewed Monitor definition.

## Historical state comparison

Preserved sanitized Uptime Kuma evidence may be compared with Monitor behavior during isolated acceptance when useful. Such comparison is supporting evidence only; Uptime Kuma is not the current production authority.

## Recovery boundary

A preserved Uptime Kuma backup may be restored only in an isolated recovery/test context unless separate explicit authorization permits production restoration.

Production rollback for Monitor normally means restoring the previous known-good Monitor release and compatible PostgreSQL state.

## Completion boundary

This historical migration record does not become complete or current merely because Uptime Kuma is retired. Current Monitor production acceptance is governed by the live Monitor target, recovery evidence, notification delivery, independent outage alerting, current platform/UI requirements, and explicit production approval.

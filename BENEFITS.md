# GoreeCloud Monitor — Benefits

**Document Internal Version Number:** 2026.09.18.1  
**Document External Version Number:** 1.0.0  
**Status:** Current supportable benefit record  
**As of:** September 18, 2026

## Purpose

This file records benefits supported by the current GoreeCloud Monitor design and source. It does not make production-readiness claims.

## Benefits

- **First-party monitoring authority:** monitoring behavior and evidence remain under GoreeCloud-controlled source.
- **Broad protocol coverage:** HTTP/HTTPS, TCP, TLS, DNS, heartbeat, and low-privilege Ping/ICMP checks are implemented.
- **Private deployment model:** the production candidate is designed for private Gateway/NetBird publication with no public backend port.
- **Durable alert intent:** transition notifications are persisted before delivery and retried across worker cycles.
- **Reduced duplicate risk:** idempotency-aware replay supports convergence after uncertain delivery outcomes.
- **Recovery-first operation:** PostgreSQL backup/restore, migration, and rollback compatibility are part of release validation.
- **Least-privilege containers:** production source avoids privileged mode, host networking, added capabilities, and Docker-socket access.
- **Security-oriented defaults:** strong authentication, secure cookies, CSP, Permissions Policy, and minimized logging are built into the source.
- **Historical migration continuity:** preserved Uptime Kuma evidence can be reconciled without keeping Uptime Kuma as production authority.
- **Transparent platform status:** all nine Integral Platform Systems are evaluated without converting incomplete integration into a success claim.
- **Fail-closed production boundary:** source readiness, deployment, live checks, notifications, and production authority remain separate states.


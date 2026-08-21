# Native Ping / ICMP semantics

GoreeCloud Monitor implements Ping as a first-party `PING` monitor kind using ICMP Echo Request / Echo Reply semantics.

## Security model

Monitor does not use raw ICMP sockets, `CAP_NET_RAW`, privileged container mode, host networking, a Docker-socket mount, or a permanent external probe service for the native Ping path.

The worker uses Linux ICMP datagram (ping) sockets. The production Compose contract grants only the deterministic Monitor group (`GID 999`) access inside the worker network namespace through:

```text
net.ipv4.ping_group_range = 999 999
```

Web and migration containers do not receive this sysctl. Application services continue to run non-root with `cap_drop: ALL`, `no-new-privileges`, read-only root filesystems, and bounded writable tmpfs mounts.

## Target validation

A Ping target is a hostname or numeric IP address and does not use a TCP or UDP port. URL delimiters, credentials, query strings, fragments, and whitespace-bearing targets are rejected.

Before an ICMP packet is sent, Monitor resolves the target through the existing destination-policy boundary. Every resolved address must satisfy `MONITOR_ALLOW_PUBLIC_TARGETS` / `MONITOR_ALLOWED_NETWORKS`. The ICMP transport then receives only the already validated numeric address, avoiding a second hostname lookup inside the transport.

When multiple approved addresses are returned, Monitor attempts them within the monitor's single total timeout budget and succeeds when a valid Echo Reply is received.

## IPv4 and IPv6

The implementation supports IPv4 ICMP Echo and IPv6 ICMPv6 Echo using unprivileged datagram sockets. Each request carries a random sequence value and random payload. A response is accepted only when the Echo Reply type, code, sequence, and payload match the request.

## Runtime proof

`python manage.py checkicmpruntime` exercises the same Ping path used by the worker. The default target is `127.0.0.1`; an approved target can be supplied explicitly with `--target`.

The disposable production-topology CI gate runs the proof from inside the actual hardened worker container. Source validation therefore proves that the no-capability worker can create and use the configured ping socket in the disposable topology.

A successful disposable proof is not live target acceptance. The actual GoreeCloud target must still prove ICMP reachability from the approved parallel worker identity and compare the result with the existing Uptime Kuma Ping monitor before the live review gate is cleared.

## Uptime Kuma migration

Supported Uptime Kuma `ping` monitor definitions map to native `PING` definitions and retain the source hostname/IP plus interval, timeout, and failure-threshold mapping already used by the migration layer. Imported definitions remain paused by default.

Notification assignments, tags, retry-timing differences, and any other existing migration warnings remain separate review items. The importer does not enable a migrated Ping monitor automatically.

## Rollback boundary

This layer introduces migration `0002_monitor_ping_kind` to record the new model choice. The migration does not grant kernel privileges and does not add a new database column.

Rollback to the DNS-parity predecessor is migration-aware:

1. keep Uptime Kuma authoritative during acceptance and rollback readiness;
2. disable and remove candidate-only `PING` definitions from the Monitor database;
3. reverse the monitoring app to migration `0001`;
4. restore the predecessor application image;
5. verify predecessor application/database state before resuming authority.

The rollback workflow proves this sequence against the exact validated DNS-parity predecessor. Production rollback still requires target-host execution evidence before cutover authorization.

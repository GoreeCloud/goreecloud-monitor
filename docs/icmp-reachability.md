# ICMP Reachability Decision Record

## Current requirement

The documented Uptime Kuma baseline contains **GoreeCloud VPS Ping**, an ICMP monitor of the VPS NetBird address. Its purpose is to verify private NetBird network-layer reachability independently of a particular application listener.

The existing TCP checks for the VPS on ports 22 and 443 overlap with reachability evidence, but they are not identical. A TCP failure can mean the network path is unavailable **or** that the individual service/port is unavailable. The ICMP check provides a separate layer-3 signal.

## v0.1 decision

GoreeCloud Monitor v0.1 does not claim automatic ICMP parity. The migration importer reports Uptime Kuma `ping` as unsupported, and unresolved coverage remains a cutover blocker.

The production deployment candidate deliberately does **not** add:

- privileged container mode;
- `CAP_NET_RAW`;
- host networking;
- a raw Docker device mapping;
- a permanent sidecar solely to make the parity checklist appear complete.

## Acceptable future paths

A later implementation may be accepted only after the actual Infrastructure Services VM and NetBird policy are validated. Candidate paths include:

1. **Linux unprivileged ICMP datagram/ping support** if the target kernel, container runtime, user/group configuration, and NetBird policy allow it without granting raw-socket capability to Monitor. This requires disposable and target testing before adoption.
2. **A narrowly scoped external reachability probe** if GoreeCloud later has a real need for a separate probe service. This adds an operational component and should not be introduced solely for feature parity.
3. **An explicitly approved replacement requirement** using service-independent evidence available from the target environment. A NetBird peer-status API can show control-plane peer state, but it is not automatically equivalent to successful data-plane ICMP reachability and must not be described as such without evidence.
4. **Retain Uptime Kuma for the ICMP check during transition** while all other compatible monitors are evaluated in parallel.

## Acceptance rule

Do not retire Uptime Kuma while the Ping monitor represents required coverage that GoreeCloud Monitor does not provide. Either validate a low-privilege ICMP implementation or formally approve a replacement monitoring requirement with its different semantics documented.

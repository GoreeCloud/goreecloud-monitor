# DNS Resolver Semantics

GoreeCloud Monitor supports both ordinary DNS availability checks and resolver-specific DNS checks without adding a new database field or migration to the current pre-production rollback chain.

## Target forms

A normal DNS monitor stores the query name directly:

```text
example.com
```

That form uses the resolver configuration available to the Monitor worker runtime.

When the resolver itself is part of the monitoring requirement, the target uses the explicit portable form:

```text
dns://1.1.1.1/example.com
```

A non-default resolver port is represented explicitly:

```text
dns://resolver.example.test:5353/example.com
```

IPv6 resolver literals use normal URI brackets:

```text
dns://[2606:4700:4700::1111]/example.com
```

The DNS record type remains the existing Monitor field and is limited to A, AAAA, or CNAME for v0.1.

## Security boundary

An explicit resolver is an active network destination. Before Monitor sends the DNS query, it resolves and validates every address for the resolver host through the same `MONITOR_ALLOW_PUBLIC_TARGETS` and `MONITOR_ALLOWED_NETWORKS` policy used by other monitored network destinations.

A resolver-qualified target therefore does not bypass the Monitor SSRF/destination policy. Public resolvers require public-target permission. Private, loopback, reserved, or link-local resolvers require an explicit allowed network. Credentials, URL query strings, fragments, ambiguous multi-path targets, and invalid resolver ports are rejected.

The DNS answer itself is evidence returned by the resolver; Monitor does not automatically connect to the returned address merely because it appeared in an A or AAAA answer.

## Uptime Kuma migration

The Uptime Kuma importer now preserves `dns_resolve_server` when it is present. The source hostname and resolver are converted into the resolver-qualified target form rather than silently falling back to Monitor's system resolver.

If a source resolver cannot be represented safely, migration fails closed with `invalid-dns-resolver`. Resolver values are not treated as credentials, but migration reports still avoid adding unrelated raw source configuration.

Imported monitors remain subject to the existing paused-by-default migration and review workflow. Preserving the resolver removes the previous source-level semantic mismatch; it does not by itself prove live parity.

## Acceptance boundary

Before production cutover, the resolver-specific Uptime Kuma checks must still be exercised against the isolated Monitor deployment and compared with fresh runtime evidence. Controlled acceptance should confirm:

- the expected resolver is reachable from the Monitor worker's approved network path;
- A, AAAA, or CNAME behavior matches the reviewed source requirement;
- expected-answer assertions behave as intended;
- resolver failure creates the expected Monitor failure state;
- resolver recovery closes the incident according to the configured recovery threshold; and
- no broader target network allowance was introduced merely to make the check pass.

This closes the source implementation gap for resolver-specific DNS semantics. Live target validation remains a separate production-readiness gate.

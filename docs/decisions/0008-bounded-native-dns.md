# Bounded native DNS with explicitly authorized resolver infrastructure

ADR 0008 — Native DNS resolution

## Status

Accepted

## Date

2026-10-06

## Context

M2-T01 is the first operational capability. PLAN permits a native resolver or adapter
abstraction; the standard library does not expose all required DNS record types,
TTLs or DNS outcomes. DNSX belongs to M2-T03. ADR 0002 forbids inferring IP authority
from name membership. A high-level system resolver can hide search suffixes,
endpoint selection, retries and alias-follow-up queries.

## Decision

Use dnspython (`>=2.8,<3`) as the only added runtime dependency. An explicitly
registered DnsAdapter implements resolve_dns; NativeDnsResolver uses one
`dns.asyncquery.udp` exchange for each selected A/AAAA/CNAME/MX/NS/TXT question.
Only the original absolute authorized hostname is queried, at most six questions.
No retry, search suffix, system resolver, TCP fallback, referral/alias follow-up,
enumeration, cache or subprocess is used.

Trusted application composition supplies one numeric resolver IP, fixed UDP port 53.
ScopeValidator independently authorizes that endpoint through the same Scope's
explicit IP/CIDR declarations; private/exclusion rules apply. Missing authorization
denies before contact. The packet destination is that numeric endpoint, never an
answer address. Resolver infrastructure is a trusted operator choice, hidden from
planner parameters/catalog; the response remains untrusted. RD requests recursive
service from that endpoint: upstream resolver operation is outside this client's
containment. Operators must authorize using that resolver for these questions; the
client neither contacts authoritative servers nor follows returned destinations.

execute takes the original ActionRequest and trusted policy/budget/context, rechecks
the registry binding and ActionPolicyValidator, independently checks infrastructure,
then reserves existing session resources. Both name and resolver host are charged.
One action covers the fixed maximum six packets. The existing rolling action rate
thus bounds DNS questions to six times its action allowance; this is not a packet
rate setting. An asyncio deadline covers all questions; each exchange also receives
an explicit timeout. Existing budget time/output/concurrency/attempt limits apply.

Normalized internal DNS contracts project into existing Asset/Observation/Evidence.
Discovered names/addresses are evidence values only. No Scope mutation or follow-up
occurs. The caller owns state lifecycle/ingestion; there is no generic dispatcher,
planner runtime, persistence, real CLI or later adapter implementation.

## Alternatives Considered

- socket.getaddrinfo: insufficient record types/provenance/outcome semantics.
- System/high-level resolver defaults: hidden search/endpoint/retry/alias behavior.
- dig/subprocess: unnecessary binary and process contract for this capability.
- DNSX: already assigned to M2-T03; unnecessary now.
- Direct authoritative traversal: adds uncontrolled discovery and new destinations.
- Implicit authorization of system resolver IP: violates independent contact rules.

## Consequences

Operators must explicitly declare resolver infrastructure and enable resolve_dns /
active_safe through policy, even when the target name is authorized. Truncated UDP
responses fail with parse_failed; large TCP answers are intentionally unsupported.
No live DNS test is necessary; fake messages and mocked native UDP exercise the
actual parser, scope, budgets, provenance and transport configuration offline.

## Security Impact

DNS discovery grants no authority. No planner-selected endpoint, packet flags,
executable or shell exists. TXT preserves arbitrary octets and remains untrusted;
it never enters an instruction/evaluation path. Upstream recursive resolution is
not an authorization grant or a client containment guarantee over that server.

## Testing Impact

Offline fixture/fake resolver cases, native UDP mock, resource/cancellation tests,
state/dedup composition, network/DNS-blocked suite and fresh installed-wheel checks.
See [resolver contract](../dns-resolver.md) and [testing strategy](../testing-strategy.md).

## Follow-up

M2-T02 becomes READY after successful closeout; enumeration remains unimplemented.
M2-T03 owns DNSX. Generic application dispatch/lifecycle/audit and recovery remain
with their existing later tasks. No task begins automatically.

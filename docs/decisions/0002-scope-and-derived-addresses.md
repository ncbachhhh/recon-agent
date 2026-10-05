# Explicit scope membership and independently authorized addresses

ADR 0002 — Scope and derived addresses

## Status

Accepted

## Date

2026-10-05

## Context

M1-T01 implements policy over the existing Target kinds and Scope roots/exclusions
with global subdomain/private-address flags. No DNS, adapter or execution code
exists. The security model requires derived targets and address changes to be
checked before contact. Domain resolution is neither proof of ownership nor a
safe permission to scan arbitrary addresses. IDNA mapping and broad Python
`is_private` classifications also require deliberate semantics.

## Decision

Use pure synchronous declaration membership and the existing errors/results.
Domain roots allow exact names and optional label descendants; hostname/URL rules
are exact authorities. Exclusions take precedence; domain exclusions cover their
subtrees and address exclusions reject any overlapping candidate range.

Authorization does not propagate from a name to DNS answers, CNAMEs, redirects,
links or SANs. Future execution must check the name and each concrete address
independently, pin/constrain approved destinations and repeat checks before using
changed addresses. An uncontainable tool mode fails closed. M1-T01 exposes only
local validation of supplied typed targets, without resolving or contacting them.

Private-address gating uses RFC1918 and IPv6 ULA specifically, never an implicit
all-private allow rule or version-dependent `is_private`. Other special categories
remain scope membership data here; capability execution restrictions remain owned
by M1-T05/adapters. Accept aligned CIDRs only; no host-bit expansion or union/range
subtraction. Unicode/IDN labels, IPv6 zones and IPv4-mapped IPv6 are rejected until
explicit supported normalization contracts exist. HTTP/HTTPS URL authorization is
host-level; reject userinfo and ambiguous representations, preserve other components.

## Alternatives Considered

- Automatically authorize DNS answers: allows externally controlled address changes,
  arbitrary address scans and discovery-driven expansion; rejected.
- Authorize any connection solely by original hostname: unsafe for private/changed
  addresses and hidden tool recursion; rejected.
- Use `ipaddress.is_private`: includes documentation/special ranges and varies across
  supported Python versions; explicit intended private networks are clearer.
- Add IDNA/PSL/deep URL ACL machinery now: no established repository contract or
  dependency need; fail closed on unsupported inputs and defer extensions.

## Consequences

Domain-only declarations provide name membership, not a working connection approval.
Future operators may need explicit address/CIDR authorization in addition to names.
That conservative operational cost is preferred to silent authorization expansion.
Session assembly applies application preferences explicitly to Scope; existing
validators have no global configuration dependency. No new runtime dependencies.

## Security Impact

Discovery does not imply authorization. Planner recommendation does not imply
authorization. Every newly introduced network target must pass deterministic scope
validation before future execution. Results are evidence of membership, not stored
execution approval tokens. Unknown parsing and missing declarations fail closed.

## Testing Impact

Offline tables prove exact/descendant boundaries, exclusions, IP/CIDR membership,
URL authority and independent redirect/address rejection. Tests need no DNS or HTTP.
The deeper M1-T02 corpus and future adapter dispatch/address-change tests remain
separate work; no rebinding protection is claimed as executable today.

## Follow-up

M1-T02 broadens regression tests; M1-T05 owns broader action policy. Resolver,
HTTP, scanner and orchestration tasks must implement concrete-address checks and
constrained contact according to this ADR. See [scope model](../scope-model.md),
[security model](../security-model.md) and [PLAN](../../PLAN.md).

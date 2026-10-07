# Deterministic scope authorization

M1-T01 implements the synchronous, side-effect-free `recon_agent.policy.ScopeValidator`.
`Scope` and `Target` remain operator declaration data. The validator takes an
explicit validated Scope snapshot, compiles all roots/exclusions, and performs
local membership comparisons. It reads no configuration/environment and performs
no DNS, network, subprocess, logging, provider or persistence activity.

Discovery does not imply authorization. Planner recommendation does not imply
authorization. Every newly introduced network target must pass deterministic scope
validation before future execution. A successful membership result supplies no
capability, risk, budget, dispatch or replay approval; those controls remain future work.

## API and outcomes

```python
from recon_agent.domain import Scope, Target
from recon_agent.policy import ScopeValidator

root = Target(id="root", kind="domain", value="example.com")
policy = ScopeValidator(Scope(id="scope", roots=(root,), allow_subdomains=True))
candidate = Target(id="candidate", kind="url", value="https://api.example.com/Path")
result = policy.validate(candidate)
if result.status == "success":
    canonical_target = result.value.canonical_target
    matched_rule = result.value.matched_rule

# Alternate application boundary: raises ScopeRejectedError on rejection.
match = policy.require_allowed(candidate)
```

`validate(Target)` uses the existing `OperationResult[ScopeMatch]`: Success contains
canonical Target data and the canonical matched declaration, preserving IDs/kinds.
Failure contains canonical ErrorInfo with code `scope_rejected`, no retryability,
and typed ErrorContext.scope_reason. Reasons are `invalid_target`, `not_in_scope`,
`excluded`, `private_ip_not_allowed`; invalid declaration construction raises
ScopeRejectedError with `invalid_scope`. No malformed root or exclusion is ignored.
Empty roots authorize nothing. Structural Pydantic rejection remains valid before
policy invocation; policy revalidates supplied models as well.

Rejections use fixed messages and, for successfully parsed candidates, target kind
and canonical authority/CIDR only. URL paths, queries, credentials and raw parse
errors never enter diagnostics. Invalid inputs omit their raw values. The caller
may record the result in future audit events; the validator emits none.

## Declaration semantics

| Kind | Authorized membership |
| --- | --- |
| `domain` | Exact normalized DNS name, plus proper label descendants only when Scope.allow_subdomains is true |
| `hostname` | Exact normalized name only, even when domain descendants are enabled |
| `ip` | Exact parsed IPv4/IPv6 value, including equivalent IPv6 spellings |
| `cidr` | Same-family address membership or a candidate CIDR fully contained within that one root |
| `url` | Exact parsed network host/IP only; path, query, fragment, HTTP/HTTPS scheme and valid port do not constrain membership |

A domain root authorizes matching hostname/domain candidates and HTTP/HTTPS URLs
on that host. An IP/CIDR root authorizes matching URL IP literals. A name never
implicitly authorizes its resolved addresses; an address never authorizes names.
Hostname/domain inputs cannot contain a port or a URL. Input kind is explicit;
there is no heuristic string-to-target convenience parser. Scope has no wildcard,
per-root subdomain toggle, scheme, path or port ACL syntax.

Exclusions always win, independent of declaration order. Domain exclusions reject
the root and all descendants, including when allowed-domain descendants are disabled.
Hostname/URL exclusions are exact authorities. IP/CIDR exclusions reject contained
addresses; a candidate CIDR with any overlap with an excluded CIDR or containing an
excluded IP is rejected in full. No partial range subtraction occurs. Multiple
allow roots are set-like: candidates must fit one root, rather than gaining larger
CIDR authority from a union. Match reporting chooses exact authority rules before
domain rules, then the most specific matching domain/CIDR; stable ties use canonical
kind/value/ID, independent of input order. Exclusions need no successful match report.

## Normalization and invalid representations

ASCII DNS names normalize to lowercase and remove exactly one final dot.
`EXAMPLE.COM.`, `Example.Com`, and `example.com` are equivalent. Labels must have
1–63 ASCII letters/digits/hyphens, start/end with a letter/digit, and the name must
be at most 253 characters after removing the final dot. Empty labels, multiple
final dots, underscores, wildcard syntax, whitespace, controls and punctuation
contamination are rejected. Numeric address-like names are rejected instead of
being treated as DNS authorization. Operator roots are explicit; no public suffix
or organizational ownership inference occurs.

Unicode and `xn--` IDN labels are explicitly unsupported and rejected for both
rules and candidates in this task. This avoids implicit IDNA version/mapping
choices; later support requires an explicit contract and tests, not silent repair.

IP comparisons use standard-library `ipaddress`. CIDRs require slash/numeric prefix
length syntax and an already aligned network address (`strict=True`); host-bit
inputs and dotted masks are rejected rather than expanded. IPv6 zone identifiers
and IPv4-mapped IPv6 literals are unsupported and rejected, with no IPv4 authority
conversion. IPv4 leading-zero/alternate spellings are not accepted.

Only absolute HTTP/HTTPS URLs are supported. This is a parsing boundary, not a
scheme ACL. `urllib.parse` supplies the authority; hostname/IP validation still
applies. Userinfo is rejected entirely, even if the actual host is authorized.
Malformed brackets/ports, port zero or above 65535, backslashes, whitespace/control
characters and encoded hostname tricks fail closed. Brackets are IPv6-only. Explicit
valid ports are retained; paths/query/fragment case and content are preserved, never
used to match a root. `https://evil.test/example.com` cannot match example.com;
`https://example.com@evil.test/` fails as unsupported userinfo.

## Private addresses and configuration

Scope.allow_private_ips only removes an additional private-address gate; it never
grants membership. Here private means IPv4 RFC1918 (`10/8`, `172.16/12`, `192.168/16`)
and IPv6 unique-local (`fc00::/7`), using explicit networks instead of the broader,
version-dependent `ipaddress.is_private`. Any candidate CIDR intersecting those
ranges is blocked while the option is false. Explicit roots are still required
when true. `10.10.10.0/24` with the option true permits `10.10.10.5`, never
`10.20.20.5`; false blocks both private candidates.

Documentation ranges remain usable as offline data. Loopback, link-local,
multicast, unspecified, reserved and global categories do not independently grant
or deny membership in this task: they require explicit scope like every other
address. Broader execution restrictions belong to M1-T05 and adapter policy.
Scope membership alone must never be treated as permission to use arbitrary
addresses for a capability.

Application ScopeConfig contains preferences only. Future trusted session assembly
must explicitly apply chosen preferences to the operator's Scope declaration;
ScopeValidator uses the effective Scope flags exclusively. Merely constructing or
loading application settings cannot alter an existing validator or authorize a
session. No implicit OR/override combination or global configuration read exists.

## Derived destinations and address changes

Call the same `validate`/`require_allowed` boundary for each absolute redirect URL,
discovered hostname or supplied resolved IP, regardless of origin. Authorized
`https://example.com/` does not authorize `https://evil.test/`. Relative redirect
resolution belongs to HTTPX evidence normalization; its resolved absolute candidate must
be validated before contact. No redirect is followed here.

See [ADR 0002](decisions/0002-scope-and-derived-addresses.md): domain membership
cannot expand to DNS answers. Future adapters/orchestration must separately validate
each concrete address immediately before contact, constrain/pin approved addresses,
and revalidate new addresses/destinations. A domain-only declaration cannot silently
authorize arbitrary IP scanning. If a tool cannot expose/constrain its actual
secondary contacts, its mode must be rejected. The validator itself has no resolver, address cache or execution hook;
HTTPX constrains concrete resolved contacts as described below.

Focused implementation checks: `.venv/bin/python -m pytest tests/unit -k scope`.
M1-T02 adds an independent regression corpus at `tests/unit/policy`, including
deterministic generated boundary/order checks and test-only mock contact consumers
that receive no rejected redirect or discovered candidate. Run it with
`.venv/bin/python -m pytest tests/unit/policy`. This adds evidence for the existing
contract, without implementing production contact enforcement. Full validation
follows [testing strategy](testing-strategy.md).

## Action target text (M1-T05)

ScopeValidator.validate_value(str) classifies untyped action target text and reuses
validate(Target). Text containing :// uses URL syntax, otherwise / uses CIDR,
otherwise colon or a decimal dot-separated spelling uses IP; other text uses
hostname. Classification never retries malformed address/URL syntax as a permissive
name. Generated candidate IDs are stable internal references. No new hostname/IP/
CIDR/URL matching rules or DNS behavior exist. Primary and trusted declared secondary
parameter targets use this entry point; each match is only membership, never complete
action approval. Dispatch/contact revalidation remains a future runtime obligation.

## Host accounting identity (M1-T06)

ScopeMatch.host_identity reuses this module's existing parsing/canonicalization:
DNS and URL host spellings share canonical identity, as do IPs and URL literals;
ports/schemes/paths do not create different hosts. It returns None for CIDRs, so the
budget controller rejects unsupported range accounting. This property performs no
DNS, membership authorization or alias-to-address inference; scope membership and
wire models are unchanged. See [budget contract](execution-budgets.md).

## Native DNS contact (M2-T01)

resolve_dns authorizes the queried name independently from its trusted resolver's
numeric IP. Resolver infrastructure needs explicit IP/CIDR membership in the same
Scope; private/exclusion rules still apply. The client only contacts that IP, never
answer addresses or discovered alias/mail/nameserver hosts. DNS values remain
evidence, requiring independent current validation before future contact. This
implements the DNS boundary of ADR 0002; HTTPX now constrains HTTP resolved contacts through a reviewed dial gate;
later scanner containment remains future adapter work. See [DNS contract](dns-resolver.md).

## Subfinder discovery (M2-T02)

The enumeration query root passes current centralized ScopeValidator and action
policy before process execution. Returned proper descendants are evidence only;
allow_subdomains=false/exclusions still deny future contact. Parser-only syntax/
root-membership validation never replaces or mutates the operational scope. Names
outside the queried root reject as malformed tool output. The only configured
passive source is an explicitly opted-in third-party service; its infrastructure
is separate from target authorization. No returned hostname/address is probed or
DNS-verified. DNS verification is independently scoped through verify_dns (M2-T03). See [contract](subfinder-adapter.md).

## DNSX batch contact enforcement (M2-T03)

verify_dns declares candidates as secondary targets. Policy independently validates
every supplied entry; mixed/all-rejected batches launch nothing. The adapter rechecks
actual canonical names and independently authorized numeric resolver before writing
the input file. Sorted unique absolute names alone reach DNSX. Returned RR owners,
aliases and addresses require new independent checks for later contact. Discovery and
resolution never mutate Scope. See [DNSX contract](dnsx-adapter.md).

## HTTPX concrete contact and redirect enforcement (M2-T04)

HTTPX probing uses the unchanged centralized name/IP/URL membership rules. Every
original batch entry passes policy; every operator-selected numeric contact IP and
resolver independently passes scope and host-budget accounting. Literal candidates
must belong to the finite configured contact set; reviewed tool-side allow enforcement
constrains DNS answers/changes before actual numeric dial. A name match or DNS record
cannot add addresses to that set. Exclusions/private gates still apply.

All redirect following is disabled, including same-host redirects. Relative Location
resolves only for evidence validation; allowed/rejected scope status never authorizes
contact, adds a target or schedules an action. A later request needs fresh independent
name/address/resource checks. See [HTTPX contract](httpx-adapter.md).

## Naabu contact binding enforcement (M2-T05)

Every discover_ports primary/batch member is checked before processing. Selected
operator bindings map canonical names to intended numeric contacts only; real scope
independently validates each address, including exclusions/private gates. Name-only
scope and missing bindings deny. Direct IPs need scope without bindings. Rechecks
precede validated-only numeric input; mixed batches never write input. No Naabu DNS
or CIDR/ASN expansion occurs. Returned IP/port facts never mutate Scope or authorize
follow-up. See [Naabu contract](naabu-adapter.md).

## Nmap selected-service contact enforcement (M2-T06)

Nmap fingerprints one trusted prior-discovery subject/contact selection per action.
Both name (when supplied) and numeric address independently pass current ScopeValidator;
prior open ports/evidence IDs never grant membership. Ports are required finite integers
within the operator approved discovery set. Names/IPs recheck before dispatch; only the
canonical numeric contact and selected ports reach the no-DNS/no-discovery profile.
No discovered metadata or Nmap output adds targets. See [contract](nmap-adapter.md).

## Common-file contact and redirect enforcement (M3-T01)

Existing centralized ScopeValidator rules are unchanged. Every initial HTTP(S) URL,
redirect destination and operator numeric contact independently passes the validator.
The adapter pins numeric dial while preserving original Host/TLS identity, so names
and addresses remain separate permissions. Configured possible redirect bindings
are all scoped/host-budgeted before execution; actual URLs/IPs recheck after pacing.
Redirect following is limited to two hops of the same fixed catalog path with no
query or HTTPS downgrade. Arbitrary in-scope paths also reject. Robots/sitemap/
security discoveries remain data only. See [contract](common-file-inspector.md).

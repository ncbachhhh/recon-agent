# Implemented DNS resolver capability (M2-T01)

`resolve_dns` is operational through `tools.dns.DnsAdapter`, an explicitly supplied
trusted ToolAdapter registered as `native_dns`. Subdomain enumeration is implemented by Subfinder (M2-T02); DNSX
verification is implemented separately as verify_dns (M2-T03). Importing modules, constructing adapters/registries,
and running the CLI cause no DNS activity. Default ToolRegistry remains empty.

## Input and composition

ActionRequest.target is the only queried name. ActionPolicyValidator validates and
canonicalizes it through ScopeValidator; the adapter accepts hostname/domain targets
only. Authorized URLs/IPs/CIDRs cannot become DNS questions. The strict DnsInput
parameter schema has one field: `record_types`, a nonempty JSON list selected from
A, AAAA, CNAME, MX, NS and TXT. Default: all six. Types are uppercase, unique and
sorted during validation; order has no execution meaning and dedup sees normalized
order/defaults. Unknown fields, numeric/coerced types, ANY/AXFR, resolver settings,
commands, flags and secondary targets reject before resolution.

Trusted code constructs `DnsAdapter(nameserver, ExecutionConfig, resolver=...)`.
The required nameserver is a numeric IPv4/IPv6 address; ambiguous/mapped/scoped
addresses reject. There is no automatic system resolver/config read or probing.
NativeDnsResolver is the default; DnsResolver.exchange is an injected trusted fake
seam, never planner data. Import the adapter explicitly from `recon_agent.tools.dns`;
registry/base APIs are unchanged. Register with explicit AVAILABLE availability and
resolve through ToolRegistry. Native availability means the packaged library is
present; it does not assert the server is reachable.

The resolved adapter's async `execute(request, policy=..., budgets=..., context=...)`
checks it is the current registry binding. It requires the same BudgetController
used by policy, current allowlists/strict schema/scope/dedup eligibility, and a
revalidated DnsContext. Context carries caller-owned asset_id, execution_id and aware
collected_at; an action's explicit asset_id must agree. Neither ApprovedAction nor
a historical policy reference is accepted as an execution token. Real session
composition supplies the existing ActionDeduplicator, not a permitting production
stub. Caller owns atomic request admission and history/result recording; execute
does not mutate ReconState or emit audit events.

## Contact and resources

Before any exchange, both original name and resolver endpoint pass ScopeValidator.
The endpoint must have independent explicit IP/CIDR scope membership; exclusions
and private-address rules apply. Both hosts are included in the atomic reservation,
so using many names cannot evade a shared resolver's per-host action limit. Resolver
IP is trusted infrastructure, not a planner parameter or discovered value.

The adapter sends only absolute original-name questions to that numeric IP on UDP
port 53. It performs at most six sequential exchanges per action, with no retries,
search suffixes, fallback, referral traversal, alias query, enumeration, brute force
or wildcard discovery. RD asks the operator-chosen resolver for recursive service;
that upstream server's own activity is outside client containment. No returned
CNAME/NS/MX hostname or A/AAAA address is contacted, resolved or authorized by the
client. Future contact must independently pass current ScopeValidator and policy,
including concrete destination checks required by ADR 0002.

Atomic BudgetController reservation enforces attempts, name/resolver hosts,
concurrency, rolling capability action rate, session time and conservative two-stream
aggregate output allowance. Each action contains at most six DNS packets; the
existing rate is per action, not per packet. Charges persist on failure/cancellation;
only concurrency releases. All questions share a deadline of the smaller configured
default timeout and remaining session time. Each UDP exchange also receives a
positive timeout; session time is checked again after its await. Cancellation
propagates with context cleanup; dnspython owns the exchange socket context.

UDP wire messages have a 65,535-byte protocol bound; EDNS advertises 1,232 bytes.
There is no TCP fallback. Normalization accepts at most 256 answer records per
question before duplicate elimination, and 256 normalized records total per action. Each
record's presentation value is capped at 8,192 characters. Serialized UTF-8 DnsOutput
must fit the smaller adapter/configured budget max_output_bytes. Oversized/truncated
or malformed results fail closed; no partial output is returned. Parsing is bounded
synchronous work; the async deadline cannot preempt that short synchronous section.

## Normalization and provenance

DnsOutput carries resolver_address, fixed transport, typed DnsQueryResult tuples,
the queried Asset, and existing Observation/Evidence tuples. No scanner-specific
domain entity or new error hierarchy exists. Every query includes canonical original
query_target, requested type and answer/no_answer/nxdomain outcome. Records retain
owner, type, normalized value, TTL and MX preference where appropriate. Addresses
use canonical IP presentation; DNS owner/target names use lowercase DNS presentation
without the final dot (root is `.`). Remote DNS names can contain unsupported
executable-target syntax; retaining them never bypasses ScopeValidator.

TXT value is escaped DNS presentation, including character-string boundaries;
txt_chunks_hex preserves each exact byte string, including empty/non-UTF-8 chunks.
TXT is never decoded into instructions, executed or sent to a planner here.
Only answer RRsets of the requested type or CNAME are accepted; authority/additional
sections confer no facts or actionability. Alias-owner answers already present in
the response can be recorded, but never cause additional queries. Per-query exact
records are deduplicated and sorted by normalized JSON; request types are sorted.
With identical response facts/context, output is deterministic regardless of answer
ordering or transaction IDs. TTL differences remain evidence differences.

Each record produces kind=dns Observation.data containing query_target, query_type,
outcome and record fields. A negative answer without records produces a status
observation. Provenance retains source native_dns, capability resolve_dns, caller
UTC time/execution ID, queried asset and evidence references. IDs derive from the
caller execution identity and stable query/record indices; caller must keep execution
IDs unique. Discovered values remain observation data, with no authority flag.

Per-query Evidence is always untrusted. artifact_reference=`memory:<execution_id>`
and locator=`queries/<index>` refer to the returned normalized query snapshot;
sha256 hashes that snapshot's JSON, not raw wire bytes. No raw packet persistence,
artifact file or invented collection timestamp is claimed. Caller must preserve the
returned snapshot if retaining its reference; persistence is future work. Facts can
be ingested through existing ReconStateMachine APIs with coherent subject/lifecycle
history; known unsuccessful executions cannot become successful facts.

## Outcomes

| Condition | Existing result contract |
| --- | --- |
| NOERROR with requested/CNAME answers | Success[DnsOutput], answer |
| NOERROR without answers | Success, no_answer status/evidence |
| NXDOMAIN | Success, nxdomain status/evidence; valid CNAMEs may be retained |
| Contradictory NXDOMAIN non-CNAME answers | Failure parse_failed |
| Resolver SERVFAIL/REFUSED/other error rcode or OS transport failure | Failure tool_execution_failed |
| Exchange/whole-action/session deadline | Failure tool_timeout |
| Malformed/mismatched response, truncation or normalization bound | Failure parse_failed |
| Invalid/disallowed/unregistered/unavailable/outside/exhausted request | Existing planner/policy/registry/budget Failure, no exchange |
| Caller cancellation | asyncio.CancelledError propagates; permit releases with cancelled outcome |

Failures use fixed diagnostics without remote text/native cause dumps, default
retryable=false, and no parallel DNS exceptions. NXDOMAIN/no-answer are successful
collection of negative evidence, not infrastructure failure or scope authorization.
If any selected question fails, the action returns Failure without earlier facts;
partial-result recovery remains future work.

See [ADR 0008](decisions/0008-bounded-native-dns.md), [tool contracts](tool-contracts.md),
[scope](scope-model.md), [security](security-model.md) and [testing](testing-strategy.md).

## Workflow integration (M2-T07)

The [deterministic pipeline](deterministic-discovery.md) now supplies caller lifecycle,
atomic state ingestion and normalized-snapshot retention for this adapter. The optional
trusted `on_started` callback runs inside the single owned budget permit before contact;
Failure/malformed outcome aborts without contact and releases concurrency. Default
adapter use is unchanged. Existing profiles/parsers/scope/resource limits remain intact.
M2 is an integration proof; M6/M7 AI planning/autonomous loops remain future work.

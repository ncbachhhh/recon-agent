# Action identity and deduplication (M1-T08)

```text
Action identity = execution-relevant semantic identity
Planner explanation != action identity

ActionRequest → ActionCanonicalizer → ActionIdentity
             → ReconState/history lookup → ActionDedupDecision
```

ActionCanonicalizer consumes explicitly composed immutable ToolRegistry metadata
and ScopeValidator. It revalidates ActionRequest, requires an available registered
capability, and shares the policy validator's strict schema and primary/secondary
scope normalization. It does not call ActionPolicyValidator, use its allowlists,
check/reserve budgets, resolve adapters, approve or execute anything. Identity alone
is not complete action authorization. Default registry and policy still deny.

## Canonical identity

ActionIdentity is a frozen portable domain record with version `action-v1`, finite
capability, canonical target kind/value and canonical parameter JSON. Its `key` is
the full sorted compact JSON envelope, without hashing, delimiter concatenation or
ambiguous stringification. Opaque request/target/rule/asset/decision IDs, reason,
priority, analysis, timestamps and error prose are excluded. A capability parameter
actually named `reason` remains execution data; only planner metadata is excluded.

Registered strict schemas determine execution semantics, including defaults and
schema normalization. Actual validated field values are traversed recursively;
field exclusions and custom serialization cannot silently omit execution parameters.
Nested model fields and string-keyed JSON objects use field names; key order does
not matter. Lists/tuples become ordered JSON arrays. Null, booleans, integers, finite
floats and strings keep their JSON type; `true`, `1`, `1.0` and `"1"` remain distinct.
Array order, case in non-target strings, Unicode code points and meaningful values
are preserved. Non-JSON values, non-string object keys and non-finite numbers deny.
Trusted schema validators must remain deterministic, strict and free of side effects.

Primary targets and every trusted declared secondary target (including defaults)
reuse ScopeValidator.validate_value and its canonical values. DNS case/trailing-dot
and textual IP/CIDR/URL-authority equivalences already accepted there collapse.
No DNS lookup, hostname-to-address merging, wider scope or extra URL interpretation
is introduced. Schemes, paths, queries, fragments and explicit ports remain as the
scope contract preserves them; default-port removal/resource URL merging belongs
to future owning tasks. Secondary sequence order remains significant.

## History and retries

ActionDeduplicator reads the single authoritative ReconStateMachine. There is no
parallel history, persistent store, identity cache or retry counter to reset.
`inspect` returns existing Success[ActionDedupDecision]/Failure. The decision exposes
identity, sorted matching action IDs, failed_attempts, typed reason and computed
`duplicate`/`eligible`. A retry is still an equivalent duplicate, but can be eligible.
Unknown/malformed/unavailable/outside requests retain existing validation failures.

| Equivalent prior history | Reason | Eligible for another request? |
| --- | --- | --- |
| None | `new` | Yes, subject to independent policy/budgets |
| Any requested/approved/started | `in_flight` | No |
| Any completed, with no active match | `completed` | No |
| Any partial/rejected/cancelled/timeout, with no active/completed match | `terminal` | No |
| All failed, any error not retryable | `retry_not_allowed` | No |
| All failed and retryable, failed count exceeds configured retries | `retry_exhausted` | No |
| All failed and retryable, failed count is within configured retries | `retry_eligible` | Yes, subject to independent policy/budgets |

ActionDedupConfig.max_failed_retries is a strict frozen nonnegative trusted local
setting, default **0**; it is explicitly injected, not read from global configuration
or planner data. A limit of N permits at most one initial attempt plus N failed-action
retries for an identity. Every equivalent failure counts, independent of error text,
service reconstruction or planner IDs. All corresponding ErrorInfo.retryable flags
must be true. Flags alone grant no retry. Timeout recovery, partial reruns, rejection
reconsideration and cancellation recovery are deliberately denied here; broader
failure recovery belongs to the later recovery task. These rules implement M1-T08's
bounded failed-action eligibility without scheduling retries.

Retries require distinct caller-assigned action IDs, preserve terminal history and
revalidate full current policy. Each actual future execution needs a new charged
budget reservation. No resource is consumed by dedup. There is no force-rerun flag,
TTL, planner override or history-reset API. A completed equivalent action cannot be
rerun by changing prose/IDs. A changed execution-relevant capability, target or
parameter represents different work, still requiring policy checks. Trusted future
fresh-session assembly defines a new history context; no session startup is added.

History identities are rederived under the fixed trusted registry/schema/scope
context. An uncanonicalizable historical request with the same capability fails
closed with a fixed planner_validation_failed diagnostic, without raw values.
History from other capabilities cannot match. Trusted callers must bind history and
contracts to the same session; schema migration/recovery is not implemented.

## State admission and policy integration

`inspect`/`check` only read detached snapshots. An advisory check alone is not a
concurrency claim. `record_request` invokes ReconStateMachine.record_action_requested
with a trusted pure eligibility callback evaluated under the existing state lock.
Check and REQUESTED recording commit atomically. Equivalent simultaneous submissions
through this path admit one; denied requests leave history unchanged. All services
sharing an owner consult the same history. The callback receives detached data,
must not reenter the owner, and its OperationResult[None] is validated. State remains
free of operational policy imports and owns all commit/rollback/lineage validation.

Inject ActionDeduplicator into ActionPolicyValidator.completed_action_eligibility.
Its `check` excludes only the same ID's semantically identical requested/approved
entry so the admitted action can pass current-policy revalidation. Competing entries
still deny. Changing that ID's capability/target/parameters denies; started/terminal
IDs always deny, even when failed retry eligibility exists. `inspect` includes every
matching entry, including that ID. Duplicate denials map to existing fixed
planner_validation_failed/Failure; no new error or result hierarchy is introduced.

The low-level state recording API still permits trusted callers to preserve raw
requests/rejections; it does not itself claim semantic authorization. Future dispatch
must use controlled admission, revalidate policy, atomically mark the selected pending
request started, reserve resources and constrain actual contact. Those operations
are not an autonomous loop or dispatcher here. No network/DNS/process/scanner/Groq,
shell, dynamic import, persistence, audit producer or CLI behavior is added.

See [state ownership](state-transitions.md), [policy contract](tool-contracts.md),
[budget accounting](execution-budgets.md) and [ADR 0007](decisions/0007-action-identity-and-retries.md).

## FFUF specialized profile identity (M3-T05)

Existing discover_content identities include mandatory profile=vhost_names when
FFUF is selected. Ferox empty input and FFUF profile schemas cannot both register in
one registry; no default content-path duplication/fallback exists. Same-profile
repeats deny through real history eligibility. Trusted contracts/settings/registry
stay fixed per session; M3-T06 cross-adapter URL equivalence is not implemented.
See [FFUF contract](ffuf-adapter.md).

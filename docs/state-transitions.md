# Controlled recon state (M1-T07)

ReconState is authoritative in-memory session state owned by ReconStateMachine.
PlannerDecision is a recommendation record. ActionPolicyValidator owns authorization;
the budget layer owns resource enforcement; ExecutionRunner owns process execution.
Recording state never performs any of those operational responsibilities.

## Ownership and operations

ReconState is now a frozen, strict snapshot with tuple collections for assets, hosts,
services, endpoints, observations, evidence, action requests/results, planner
records, action lifecycles and budget snapshots. ReconStateMachine explicitly owns
one validated defensive copy and a local lock. Every transition builds and validates
a complete candidate before swapping the owned state. Failure leaves the previous
state unchanged. Every state property/transition result returns a detached copy.
Nested JSON in returned snapshots can be edited as ordinary data, but cannot alter
the owner. No custom deeply immutable JSON framework is required.

State construction/deserialization checks the same lineage/lifecycle rules as live
transitions. Python inputs require tuples and actual typed scalar/timestamp values;
JSON uses arrays, UTC timestamps and enum values. Both dumps round-trip. Existing
pre-M1-T07 list-based Python snapshots must be converted to tuples and supplied with
explicit lifecycle history; no approval/start/history is inferred from old results.
model_copy/model_construct are not validation; the owner revalidates supplied models.
Initial invalid state raises canonical StateTransitionError. Transition methods
return existing Success[ReconState]/Failure/ErrorInfo; failures use the single new
`state_transition_invalid` code/category `state`, retryable=false and fixed safe
text without remote inputs. Direct schema validation still raises ValidationError.

| Operation | Effect |
| --- | --- |
| `record_facts` | Atomically append related assets/hosts/services/endpoints/observations/evidence; handles mutual asset/observation references in one batch |
| `record_asset`, `record_host`, `record_service`, `record_endpoint`, `record_observation`, `record_evidence` | Convenience single-record calls through the same complete validation boundary |
| `record_planner_decision` | Append a recommendation with input lineage; does not enqueue or approve its actions, stop a session, change scope or budgets |
| `record_action_requested` | Explicitly add an ActionRequest and requested history event with caller-supplied time |
| `mark_action_approved` | Record the trusted caller's policy decision reference/time; no policy evaluation or reusable permission |
| `mark_action_started` | Record an execution identity/time after approved; no permit acquisition or runner call |
| `record_action_result` | Atomically append terminal ActionResult/history and supplied evidence/observations, preserving error/outcome distinctions |
| `record_budget_snapshot` | Append caller-sampled, timestamped read-only ledger facts; no controller call or budget arithmetic |

All IDs/timestamps are explicit; no time/environment/randomness is sampled. A caller
should select identifiers and timestamps from transition inputs/results for future
audit events, never dump full snapshots or untrusted text into diagnostics. No state
constructor/transition logs, emits audit events or opens artifacts. Local concurrent
calls serialize through the lock; no workers, scheduling or orchestration loop exist.

## Action lifecycle

ActionPhase covers requested, approved, started and the existing ActionResult terminal
statuses. ActionLifecycle stores action_id and append-only ActionTransition events;
phase is derived from the last event, never an independent mutable status field.

| Prior phase | Permitted next phase |
| --- | --- |
| requested | approved, rejected, cancelled |
| approved | started, rejected, cancelled |
| started | completed, partial, failed, cancelled, timeout |
| any terminal phase | none |

Rejection after approval represents current policy/resource denial before execution.
Cancellation may occur before or during work. Completed/partial/failed/timeout require
started. Partial remains a distinct terminal outcome and retains its limitation;
it is not silently completed. Repeating the same terminal transition rejects rather
than pretending idempotent success. A later retry needs a distinct caller-assigned
action ID; M1-T08 policy supplies explicit retry/equivalence eligibility.

Requested has no policy/execution/result metadata. Approved requires only a policy
reference; started requires only an execution ID; terminal requires only a result ID.
Events use nondecreasing aware UTC timestamps, allowing equal times. Initial history
must start with requested and obey the same edges. One request has exactly one
lifecycle and at most one terminal result. Terminal phase, action/result ID and time
must agree. Each started action owns one unique execution ID, and its terminal result
must reference exactly that ID. Unstarted rejection/cancellation has no execution.
Future multi-execution adapters need explicit reviewed lifecycle modeling; silently
attaching unrelated execution IDs is forbidden.

A serialized approved/started record or policy_reference is a historical fact supplied
by trusted application code, never dispatch authorization. State does not authenticate
that provenance or sandbox malicious application code. Future dispatch still must
revalidate the original ActionRequest with current ActionPolicyValidator, reserve
resources and constrain actual contact. A planner has no state mutation tool.

## Evidence, subjects and recommendations

IDs must be unique within each entity collection. This protects lineage identity,
not semantic equivalence: distinct IDs may contain identical target/parameter/fact
content. M1-T08 supplies canonical action equivalence and retry eligibility in
policy, derived from this history. No separate retry counter or sophisticated
observation deduplication is implemented.

Subject observation references must exist and belong to the same asset. Hosts require
known assets; service host ownership and optional endpoint service ownership must
match the asset. Observations require known assets/evidence. Supplied execution
references on an observation and its evidence cannot contradict each other. Remote
payloads, sources, artifact references and times remain unchanged; no parser, finding,
interpretation, DNS lookup or scope expansion occurs. Out-of-scope discovered subjects
can be recorded as evidence; recording never makes them actionable.

Planner input evidence/observation references must exist. Recommendation IDs within
one decision are unique and optional decision references must match. Explicitly
requested actions that cite a decision must match that decision's recommendation
by ID and supplied content and cannot precede the decision timestamp. Recording the
decision itself creates no action lifecycle, approval, result or observation.

ActionResult's existing structural rules prohibit failed/rejected/cancelled/timeout
observations. The state also rejects observations attributed to known unfinished or
unsuccessful actions, including through cited evidence when observation.execution_id
is omitted. Associated observations are ingested atomically with completed/partial
results, or afterward. Standalone external/fixture observations remain supported;
unknown execution references are opaque external provenance, not invented history.
Failed/timeout/cancelled results may preserve evidence without successful facts.

Result facts must equal the corresponding state record. An existing ID can be cited
with identical payload only; conflicting payload rejects the entire transition.
New fact IDs append. Duplicate fact IDs within a result reject. No result error,
partial limitation, rejection or failure history is discarded.

## Budget and session boundary

The existing BudgetState and ReservationOutcome pure contracts now live in
`domain/budgets.py`; policy imports/re-exports them, so its public interface is
preserved. BudgetState remains a frozen dataclass, with strict nonnegative/finite
structural validation and portable serialization through BudgetSnapshot. No counting,
rate/time arithmetic, reservation or permit cleanup moves out of BudgetController.
BudgetSnapshot adds explicit id and recorded_at; snapshots retain sampled counts,
remaining resources, host/capability buckets and outcomes, without recomputing them.
Snapshot bucket keys cannot repeat and recording times cannot regress. State does
not infer monotonic counters, reconcile samples with actions or accept snapshots to
restore/reset a controller. Trusted session assembly owns selecting the right ledger.
A budget rejection can be recorded as an ActionResult with its original canonical
BudgetExhaustedError, independently of recording a sample.

ReconSession remains structural composition of targets, scope, state and its existing
status fields. Session startup/stop/resume transitions are not assigned by M1-T07's
PLAN scope and remain future orchestration work. The state owner has no scope,
configuration, provider, adapter, runner or live budget reference. It performs no
network, execution, persistence, reporting, planning or autonomous loop activity.

See [data model](data-model.md), [budget ownership](execution-budgets.md),
[security model](security-model.md), and [ADR 0006](decisions/0006-controlled-recon-state.md).

## Atomic semantic request admission (M1-T08)

ReconStateMachine.record_action_requested optionally accepts a trusted pure
eligibility(request, state) callback inside its existing commit lock. Both arguments
are detached; callbacks must not reenter the owner. Existing OperationResult[None]
is validated; Failure aborts without mutation, and malformed results retain the
canonical state-transition failure. Low-level recording remains available to
preserve trusted raw rejection history without pretending semantic approval.

ActionDeduplicator.record_request supplies the check and performs atomic equivalence
lookup plus REQUESTED recording. No second state owner/cache/retry counter is added.
Policy checks may exclude only their own unchanged requested/approved entry; all
competing matches and all started/terminal IDs still deny. Lookup is read-only,
retry limits derive from existing failure history, and budgets/authorization stay
independent. See [identity and retry rules](action-deduplication.md).

## DNSX partial evidence (M2-T03)

The capability-local DNSX output explicitly carries completed/partial status and
canonical completeness errors. Callers own lifecycle/ActionResult construction and
correlated fact ingestion; partial output must use PARTIAL, not COMPLETED. Existing
state ownership rules remain unchanged. No new dispatcher/ingestion runtime exists.
See [DNSX contract](dnsx-adapter.md).

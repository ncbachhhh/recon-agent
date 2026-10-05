# Owned snapshots with atomic validated state transitions

ADR 0006 — Controlled recon state

## Status

Accepted

## Date

2026-10-05

## Context

M1-T07 must maintain action/evidence history and budget facts without performing
policy, execution, deduplication or orchestration. Existing ReconState lists permit
unvalidated edits; frozen records still expose mutable nested JSON. Domain purity
forbids importing the operational BudgetController or ApprovedAction implementation.

## Decision

Make ReconState a frozen tuple-based snapshot with whole-state reference/lifecycle
validation. Add a small domain ReconStateMachine owner with a local lock and explicit
transition APIs. It deep-copies initial inputs, committed candidates and returned
snapshots. A failed transition leaves the authoritative state unchanged. All timestamps
are supplied; construction and recording have no external side effects.

Keep requested/approved/started plus the existing terminal result statuses. Persist
append-only typed ActionTransition history and derive current phase. Every terminal
result must correlate exactly with its lifecycle and single execution identity.
Record approvals as trusted caller-supplied policy references, never authorization
or replay tokens. Preserve terminal distinctions and reject all terminal re-entry.

Use one minimal StateTransitionError/ErrorCode extension in the canonical result
system with category state and conservative non-retryability. It cannot be relabelled
as an operational failed/partial ActionResult. Ingest related facts/results atomically
and validate referential ownership. Reject successful observations attributed to
known unfinished/unsuccessful executions, including indirectly through evidence.

Move only existing read-only BudgetState/ReservationOutcome contracts to domain;
policy re-exports them. Add timestamped BudgetSnapshot recording and strict structural
validation, with no budget arithmetic/enforcement duplication. PlannerDecision records
remain separate; recording never enqueues/actions, authorizes, consumes or runs.

## Alternatives Considered

- Exposed mutable lists/nested JSON: bypasses transition validation and rollback.
- Deeply immutable JSON containers: complicates all record serialization; defensive
  ownership plus detached snapshots preserves ordinary JSON contracts.
- Mutable model transition methods returning self: makes alias/partial mutation
  rollback and concurrent ownership harder to audit.
- Import operational policy/budget objects into domain: blurs authority boundaries
  and creates cycles; pure data references/snapshots suffice for state recording.
- Infer lifecycle from old results: manufactures authorization/execution history;
  require explicit validated initial history instead.
- Generic event framework/global store: adds infrastructure beyond this foundation;
  small typed operations and one lock suffice.

## Consequences

Python ReconState construction now uses tuples and explicit lifecycle records;
legacy list/partial snapshots require conversion, without automatic permission
inference. Snapshot JSON remains portable. The owner validates/copies a complete
state per transition, favoring correctness over large-session performance at this
foundation phase. Callers own binding the state to session/policy/budget provenance.
Session lifecycle, action equivalence, retries, contact and execution remain deferred.

## Security Impact

ReconState records trusted caller-supplied history; it grants no authority. A planner
cannot mutate the owner, scope or limits. Future dispatch revalidates current policy
and budgets; recorded references cannot skip that boundary. Remote text remains data.
There are no network/process/provider/shell/dynamic import or audit/log side effects.

## Testing Impact

Offline 81-edge lifecycle matrix, terminal protection, initial/serialized corruption,
reference/ownership checks, nested alias isolation, deterministic timestamps/dumps,
concurrent atomic commits, budget sampling and untouched runtime guards.

## Follow-up

M1-T08 owns semantic action equivalence and bounded retry eligibility. Future
orchestration/adapter tasks own policy-resource-execution composition, session stop
and actual contact. None begins here. See [state contract](../state-transitions.md).

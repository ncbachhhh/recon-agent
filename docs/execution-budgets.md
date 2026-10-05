# Execution budgets and rate limits (M1-T06)

Policy authorization != budget availability. AI planner recommendations cannot raise
resource limits. A trusted session owner explicitly constructs one BudgetController
from an immutable ExecutionBudget snapshot and the immutable ToolRegistry. There
are no global counters, implicit configuration reads, reset/update/refund methods,
background timers, workers, execution calls or persistence.

## Contracts and composition

`policy/budgets.py` exports ExecutionBudget, BudgetState, BudgetController,
BudgetPermit and ReservationOutcome. ExecutionBudget.from_config revalidates an
explicit ExecutionConfig; later edits to that configuration cannot change the
controller. All counts/bytes must be strictly positive integers, seconds positive
and finite; zero is invalid, never unlimited. Invalid controller limits/initial
clock produce ConfigurationError; direct model validation uses ValidationError.

ActionPolicyValidator's BudgetEligibility.check now accepts the internal
ApprovedAction, including canonical primary/secondary ScopeMatches. Completed-action
eligibility retains the ActionRequest interface and default denial until M1-T08.
The budget controller does not repeat registry resolution, input-schema validation
or scope authorization. ScopeMatch.host_identity reuses centralized parsing.

```text
ActionRequest
  → ActionPolicyValidator (registry/scope/parameters/risk + eligibility checks)
  → Success[ApprovedAction] (current eligibility only)
  → BudgetController.reserve (atomic recheck and resource acquisition)
  → Success[BudgetPermit] (resource ownership only)
```

`check` returns existing Success[None]/Failure and consumes no attempts/resources.
`reserve` repeats all limits under one local lock and returns
Success[InstanceOf[BudgetPermit]] or Failure with canonical BudgetExhaustedError /
ErrorInfo (`budget_exhausted`, conservative non-retryable). Fixed diagnostics identify
the exhausted dimension without planner text or clock exceptions. Unknown,
unregistered, malformed or unsupported budget inputs deny without creating buckets.
These are internal interfaces; approval/permits are not serializable replay tokens.
Failures remain portable. BudgetState is a detached frozen tuple-based snapshot,
never accepted to reset the ledger. No new audit event types/producers are added.

Future dispatch must revalidate the original request against current policy before
reservation and prevent intervening suspension before entering permit ownership.
An old/forged ApprovedAction or an available budget cannot authorize execution.
There is no production dispatcher or completed-action permitting service here.

## Counting and atomicity

| Limit | Accounting |
| --- | --- |
| `max_actions` (100) | One granted reservation = one permitted attempt. Checks and rejected reservations spend nothing. A granted attempt that never starts is still charged conservatively |
| `max_concurrency` (1) | One active permit per granted reservation, released exactly once; no waiting queue or worker pool |
| `max_actions_per_host` (10) | Each distinct primary/secondary host receives one charge per granted attempt, across all capabilities |
| `capability_rate_actions` (1), `capability_rate_window_seconds` (1.0) | Each registered capability has an independent rolling window. Count timestamps in `(now - window, now]`; an entry expires at its exact window boundary |
| `max_duration_seconds` (600.0) | Elapsed monotonic seconds from explicit controller construction. Exact deadline rejects; remaining time saturates at zero |
| `max_session_output_bytes` (16777216) | Reserve `2 * max_output_bytes` per granted attempt for worst-case stdout + stderr retention, independent of actual captured bytes |

Limits are checked together and consumption commits under a single lock with no
await. Concurrent threads/tasks sharing this controller cannot oversubscribe a
limit. Rate history is bounded by the rate count; host accounting is limited to
hosts from permitted actions. Read-only state/check calls expire rate entries
logically without spending anything. Buckets are initialized only for explicitly
registered capabilities; the registry already selects one adapter per capability,
so these implement per-tool execution rates for that selected composition.
Unavailable capabilities still fail earlier policy checks. New controller creation
is trusted new-session assembly, never an AI reset/resume mechanism.

Failure, cancellation, timeout and aborted-before-start attempts retain action,
host, rate and output charges. Every retry needs a new reservation and pays again;
there is no automatic retry, action identity/dedup history or rollback/refund API.
Release records a typed completed/failed/cancelled/timeout/aborted counter exactly
once. Rejections are returned to the caller for future audit/state recording; they
are not executions. No failure path resets limits.

## Host identity and traffic boundary

Use the ScopeValidator's canonical host: DNS case/trailing dot normalize; HTTP/HTTPS
scheme, port, path/query/fragment do not split a host; canonical IP/IPv6 URL literals
share accounting with plain IPs. No DNS lookup or name-to-IP equivalence is inferred.
All declared secondary hosts count, including defaults; duplicates count once.
A CIDR has no single host identity and rejects at the resource layer, including a
CIDR in a secondary parameter. Future range-capable adapters must supply bounded,
independently authorized concrete host work before dispatch; treating a range as
one host bucket is forbidden. Scope membership itself is unchanged.

An action rate/budget is not a packet or tool-internal request limiter. Future adapters
must constrain internal traffic, redirects/new hosts and resource use before contact;
these checks cannot contain a scanner that ignores its granted bounds. No
scanner-specific flags, DNS, contact enforcement or scanner execution are implemented.

## Permit ownership and deadlines

Use a synchronous context manager immediately after successful reservation; it also
works around awaits. Entering a released/already-entered permit rejects. Normal exit
records completed; exceptions record failed; TimeoutError records timeout;
asyncio.CancelledError records cancelled and propagates. Cleanup acquires the local
lock synchronously and never awaits, so repeated task cancellation cannot interrupt
release. Explicit release(outcome) is idempotent; its default is aborted. Invalid
outcomes reject without corrupting the live permit. Caller abandonment is not a
supported ownership path; no finalizer silently releases or refunds work.

`controller.state.expired` and `.remaining_seconds` answer session-time questions
without a timer. The clock defaults to time.monotonic and is injectable. Backward,
non-finite/invalid readings or clock exceptions permanently exhaust session time;
clock recovery cannot extend a failed session. Release still works after expiry.
This component does not interrupt running work. Future dispatch must cap operation
timeouts to remaining session time and own cancellation/cleanup; M7 orchestration
is unimplemented.

## Output ownership

M1-T03 still owns bounded draining/capture of each process stream. M1-T06 adds only
aggregate allowance accounting. Even failed/cancelled attempts keep their reserved
allowance, so actual retained output cannot exceed the ledger under the future
trusted dispatch contract. Unused allowances are deliberately not reclaimed.
The process runner must use the same or a smaller per-stream max_output_bytes than
the controller. Each reservation covers at most one such two-stream execution;
additional execution/output requires additional reservations, never an implicit
unbounded capability expansion. An envelope smaller than one allowance is valid
positive configuration but denies all reservations, with no permissive fallback.
No capture buffer, output bytes, evidence store or retention engine is added here.

See [configuration](configuration.md), [execution model](execution-model.md),
[security model](security-model.md) and [ADR 0005](decisions/0005-budget-reservations.md).


## Recorded budget facts (M1-T07)

BudgetState/ReservationOutcome now live in pure domain/budgets.py and remain
re-exported by policy/budgets.py. The controller's checks, counting, rate/time
arithmetic and permit ownership are unchanged. Strict frozen snapshot validation
adds nonnegative finite structural checks; BudgetSnapshot records caller-supplied
id/time plus those facts. ReconStateMachine can append snapshots and preserve
BudgetExhaustedError rejection results, but cannot acquire/release/refund/reset
resources or infer counters from action history. See [state contract](state-transitions.md).

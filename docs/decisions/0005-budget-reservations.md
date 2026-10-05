# Atomic session reservations with conservative attempt accounting

ADR 0005 — Budget reservations

## Status

Accepted

## Date

2026-10-05

## Context

M1-T06 must bound action/host/concurrency/rate/time/output resources without scanner
execution or orchestration. M1-T05's budget seam receives raw requests, which cannot
safely identify all schema-declared secondary targets without repeating validation.
M1-T03 already bounds process streams. Counting only successful executions or
refunding failures could permit unlimited failing retries.

## Decision

Use one explicitly composed, locally locked BudgetController per session with frozen
ExecutionBudget limits and independent consumed state. Evolve the budget eligibility
seam to ApprovedAction containing already validated primary/secondary scope matches;
completed-action semantics remain separate. Read-only checks confer no reservations
or authority. Reserve checks and consumes every dimension atomically without await.

Count granted attempts permanently, including aborted/failed/cancelled/timed-out work;
rejections consume nothing. Each distinct host counts once per attempt. Use rolling
per-capability monotonic timestamp windows over the explicit registry snapshot.
Each registered capability selects one tool. Reject CIDRs without concrete-host
accounting rather than treating an entire range as one host. Time starts at explicit
controller construction; bad/regressing clocks permanently exhaust time.

Reserve the worst-case two-stream output allowance per attempt. No failure refunds
output/action/host/rate capacity. Only concurrency is released by a synchronous,
idempotent ownership context, including across awaits/cancellation. Typed outcome
counters do not implement ReconState history or audit producers.

## Alternatives Considered

- Success-only counting/refunds: repeated failures could evade session limits.
- Raw-request target guessing or repeated schema/scope validation: duplicates policy
  and may overlook defaults/secondary destinations; consume normalized matches.
- Fixed rate windows: allows doubled bursts near window boundaries; rolling windows
  are deterministic with bounded history.
- Waiting semaphores/background timers: adds cancellation/queue scheduling without
  an orchestration owner; nonwaiting atomic permits suffice for this foundation.
- Actual aggregate capture/refund: couples process I/O to policy and duplicates
  capture ownership; conservative pre-reservation provides a bounded envelope.

## Consequences

Conservative accounting can stop before successful-action or actual-output totals
reach their configured limits. Operators see permitted attempts/reserved allowances
explicitly. Trusted future dispatch must use one shared controller, revalidate policy,
enter ownership immediately, constrain per-process output/time/internal contacts,
and reserve each additional execution. Abandoned ownership is a caller error, never
an AI permission to release/replay. No production dispatcher is implemented.

## Security Impact

Policy authorization != budget availability. AI planner cannot raise resource limits,
reset counters, select rate buckets or suppress exhaustion. Missing/unsupported
inputs fail closed. There is no network/process/provider/shell/dynamic import.

## Testing Impact

Injected clocks and concurrent offline contenders verify exact boundaries, no
oversubscription, host canonicalization/secondary targets, retry charges, output
allowances, deadlines and exception/cancellation-safe release with untouched runners.

## Follow-up

M1-T07 owns state transitions/outcome recording; M1-T08 owns action identity/dedup;
future adapters/orchestration own contact containment and running-work deadlines.
None begins here. See [budget contract](../execution-budgets.md).

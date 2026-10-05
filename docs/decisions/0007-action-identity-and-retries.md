# Semantic action identity and conservative bounded retries

ADR 0007 — Action deduplication

## Status

Accepted

## Date

2026-10-05

## Context

M1-T08 requires canonical capability/target/parameter identity, completed/in-flight
policy denial, bounded failed-action retry eligibility and state integration.
M1-T07 owns request/lifecycle/result history; M1-T05 exposes a read-only eligibility
seam. No action retry configuration or recovery rules already exist. Defaults must
fail closed, and dedup cannot authorize, spend resources or execute.

## Decision

Use a versioned full canonical JSON identity over registered validated schema values
and existing ScopeValidator primary/secondary target normalization. Include defaults
and actual fields, including fields excluded from model dumps. Preserve ordered
arrays and JSON scalar types. Exclude planner prose, priorities, IDs, times and
lineage metadata. Domain exposes pure portable identity/decision records; policy
owns canonicalization and typed history eligibility, using existing OperationResult.

Read only the existing state history; no second ledger/cache/counter. Default trusted
ActionDedupConfig.max_failed_retries to zero. Permit only all-failed equivalents whose
recorded errors are all explicitly retryable, within N configured failed retries
(one initial attempt plus N retries). Reject every requested/approved/started,
completed, rejected, partial, cancelled and timeout equivalent. This conservative
assignment covers M1-T08; broader recovery classifications remain future work.
Every retry uses a new action ID, full current policy and separately charged resources.

Provide controlled atomic request admission through a trusted pure callback inside
the existing state lock, with detached inputs and validated outcomes. State retains
ownership/rollback and never imports policy. The policy eligibility seam excludes
only its own semantically identical requested/approved entry; started/terminal IDs
cannot be reused. Advisory lookup does not reserve or claim execution. Historical
same-capability requests that cannot be canonicalized under current contracts deny.

## Alternatives Considered

- Raw request JSON/repr: prose/default/key-order/target spelling can evade identity.
- Hash-only/delimited strings: unnecessary collision/ambiguity and poorer inspectability.
- Serialize schema dumps: excluded fields/custom serializers can hide semantic data.
- Separate dedup ledger: duplicates history ownership and permits reset/drift.
- Read-check then unguarded append: concurrent equivalents can both enqueue.
- Ignore every matching action ID in checks: terminal replay or changed semantics bypass.
- Implicit retries of rejected/timeout/partial/cancelled outcomes: invents broader
  recovery behavior not assigned here; use explicit conservative denial.
- Global config changes/automatic retry loop: unnecessary for this local eligibility
  foundation; explicit frozen configuration follows existing policy composition.

## Consequences

Linear lookup revalidates relevant history and favors correctness over performance.
Trusted schemas/context must stay deterministic and session-bound; future migration
must explicitly reconcile historical semantic changes. Current URL resource semantics
are preserved without M3 URL dedup work. Normal retry eligibility is typed data;
policy denials reuse planner_validation_failed. Low-level state recording still
preserves raw rejected intent; future dispatch must use the controlled admission path.
No completed-rerun override exists.

## Security Impact

Metadata/order/accepted target aliases cannot evade equivalence. Remote evidence
cannot define identity, allowlists, retry limits or recovery semantics. Canonical
identity and dedup eligibility grant no authorization/resource/execution permission.
No operational I/O or policy/budget/state ownership duplication is introduced.

## Testing Impact

Offline canonical equivalence/distinction, nested types/defaults/hidden fields,
serialization, full lifecycle/retry tables, reconstructed-history bounds, atomic
concurrent new/retry admission, terminal replay, policy/budget isolation and runtime
guards. Full baseline, network/DNS-blocked and fresh-wheel checks remain required.

## Follow-up

M2-T01 may become READY only at successful M1-T08 closeout; no adapter starts here.
Existing later orchestration/recovery/persistence tasks own dispatch composition,
actual execution/retry scheduling and migrations. See [dedup contract](../action-deduplication.md).

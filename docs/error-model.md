# Error and result contracts

M0-T05 implements pure shared contracts in `recon_agent.core.errors` and
`recon_agent.core.results`. They describe failures and explicit outcomes; they do
not execute, authorize, retry, log, persist or contact anything.

## Exceptions and stable codes

`ReconAgentError` is the project catch boundary. `PolicyError` catches deterministic
rejections/exhaustion; `ToolError` catches availability, execution and normalization
failures. These three parents are catch boundaries and cannot be instantiated.
Instantiate a concrete error with a short, sanitized message and optional typed
`ErrorContext`. Branch on the type, `code` or `category`, never on message text.

| Exception | Parent | Stable code | Category / intended future boundary |
| --- | --- | --- | --- |
| ConfigurationError | ReconAgentError | `configuration_invalid` | configuration: explicit loading/startup |
| ScopeRejectedError | PolicyError | `scope_rejected` | policy: centralized authorization |
| BudgetExhaustedError | PolicyError | `budget_exhausted` | policy: resource/action limits |
| StateTransitionError | ReconAgentError | `state_transition_invalid` | state: invalid input/lifecycle/lineage |
| ToolUnavailableError | ToolError | `tool_unavailable` | tool: environment/availability |
| ToolTimeoutError | ToolError | `tool_timeout` | tool: execution deadline |
| ToolExecutionError | ToolError | `tool_execution_failed` | tool: execution failure |
| ParserError | ToolError | `parse_failed` | tool: normalization failure |
| ProviderError | ReconAgentError | `provider_failed` | provider: hosted provider boundary |
| PlannerValidationError | ReconAgentError | `planner_validation_failed` | planner: invalid recommendation |
| CancelledError | ReconAgentError | `cancelled` | cancellation: existing domain cancellation outcome |

Cancellation supplies the category for M0-T04's existing terminal status, rather
than mislabeling cancellation as tool failure. It does not implement cancellation,
child cleanup or orchestration. Configuration loading and M1-T01 scope membership are integrated boundaries;
M1-T03 integrates canonical tool unavailable/execution/timeout errors through the
existing Failure contract; other operational boundaries remain planned.

All errors default to `retryable=False`. A producer may explicitly set it to true
for a known transient tool/provider failure. It means a retry **may** be useful;
it is neither a retry instruction nor approval. Configuration, policy, planner
validation and cancellation errors reject `retryable=True`: repeated unchanged
input cannot fix them. Later orchestration must separately check permission,
budgets and bounded retry policy. No automatic retry exists.

## ErrorInfo and diagnostic context

`error.to_error_info()` returns a frozen, serializable `ErrorInfo` containing
`code`, `message`, `retryable` and `context`. `category` is a derived Python
property of the code, not a second independently supplied/serialized field.
Python dumps retain ErrorCode enum values; JSON emits their stable strings.
Python validation requires the enum; JSON validation accepts its string encoding.
Both forms round-trip. Conversion is explicit for project exceptions only;
there is no global mapper or invented fallback for unknown exceptions.

`ErrorContext` allows only optional scalar fields: `action_id`, `target_id`,
`capability`, `tool`, `provider`, positive finite `timeout_seconds`, integer
`exit_code`, and `configuration_source` (`file`, `environment`, `validation`).
M1-T01 adds optional typed `scope_reason` (ScopeRejectionReason), `target_kind`
and bounded `normalized_candidate` authority/CIDR fields for deterministic policy
failures. Raw malformed inputs and URL paths/queries/userinfo are omitted; see
[scope model](scope-model.md). Absent fields default to null. Reference text is non-blank and at most 256
characters; messages are non-blank and at most 1024. These limits keep diagnostic
records from absorbing unbounded remote output; full evidence belongs in its
own bounded collection/artifact contract. Negative exit codes are valid data.
Unknown fields, coercion, arbitrary objects and non-finite numbers are rejected.
Context and information records are frozen with nested instances revalidated.

There are no credentials, environment dumps, commands, stdout/stderr or tracebacks
in the schema. Do not copy configuration/remote output/native exception dictionaries
into it. Configuration loading uses fixed messages and source labels, never raw
values. Modeled provider secrets retain their excluded/redacted serializer even
when placed inside a typed success payload. Normal project exception str/repr and
ErrorInfo dumps exclude chained causes. Text explicitly supplied as an ordinary
message/reference is the caller's responsibility: these contracts cannot detect
an arbitrary secret placed there. Generic success payloads likewise must provide
their own appropriate safe serialization.

Native causes remain accessible through Python `raise ... from exc` chaining for
explicit debugging. Raw causes, structured native validation inputs and complete
chained tracebacks may contain sensitive source material; they are not the safe
diagnostic API. Use ErrorInfo for routine diagnostics. Direct model construction
continues to raise Pydantic ValidationError; displayed errors hide inputs, while
structured errors need `errors(include_input=False)` and careful context handling.
M0-T06 now consumes ErrorInfo through the configured local formatter, applying
explicit registered-secret redaction to its message/context and including derived
error_category. Native causes/tracebacks are omitted, including exc_info; they are
not stable audit data. Malformed records produce fixed omission output, and sink
I/O failures raise a fixed ConfigurationError without raw-record debug fallback.
See [logging/audit contracts](logging-and-audit.md). Error constructors remain pure.

## Explicit operation results

Use exceptions for exceptional application boundaries, such as invalid startup
configuration. Use `OperationResult[T]` when callers intentionally inspect an
operation's success/failure during normal control flow. Functions do not all need
to return results. Domain model validation continues to use Pydantic normally.

```python
from pydantic import TypeAdapter
from recon_agent.core.errors import ErrorContext, ToolTimeoutError
from recon_agent.core.results import Failure, OperationResult, Success

result: OperationResult[int] = Success[int](value=5)
if result.status == "success":
    value: int = result.value

failure = Failure(
    error=ToolTimeoutError(
        "Execution deadline reached.",
        context=ErrorContext(action_id="action-1", timeout_seconds=30),
    ).to_error_info()
)
assert failure.status == "failure"

adapter = TypeAdapter[OperationResult[int]](OperationResult[int])
assert adapter.validate_json(adapter.dump_json(failure)) == failure
```

The generic union has a `status` discriminator. `Success[T]` has only
`status="success"` and required typed `value`; `Failure` has only
`status="failure"` and required ErrorInfo `error`. Unknown fields and mixed or
missing value/error states fail validation. The tags avoid ambiguous boolean/
integer coercion. Frozen attributes and strict nested validation preserve the
contract; no exception/traceback objects are serialized. Instantiate Success with
a concrete type parameter at validated boundaries; an unconstrained payload is
not a substitute for a schema. Python/JSON dumps and TypeAdapter JSON round trips
preserve domain values. Mypy narrows the union without Any, casts or suppressions.

## ActionResult relationship

`OperationResult[T]` describes a generic operation. Domain `ActionResult` records
an action ID, outcome status, time, observations/evidence and execution references.
It uses the same ErrorInfo primitive, with no duplicate error schema or conversion
to an operational executor. It can record `partial`, `rejected`, `cancelled` and
`timeout` distinctly; these do not masquerade as a generic Success.

M0-T05 replaces the temporary `failure_reason` field with `error`. Completed
results forbid errors; every other status requires structured error information.
Rejections require policy/planner categories, timeout requires `tool_timeout`,
and cancellation requires `cancelled`. Failed/partial results cannot relabel
policy/planner rejection or cancellation. Only completed/partial results may
carry successful observations; other statuses may retain evidence references.
A partial result's error explains its limitation. Reference consistency, state
transitions and retry/stop behavior remain future work. See [data model](data-model.md).

## Validation and boundary

Focused checks:

```bash
.venv/bin/python -m pytest tests/unit/test_errors.py tests/unit/test_results.py
.venv/bin/python -m mypy src/recon_agent tests/unit/test_results.py
```

Tests exercise codes/hierarchy, retryability, bounded allowlisted context, secrets,
strict nested serialization, typed payload narrowing, result invariants,
configuration cause chaining and ActionResult distinctions. The [testing strategy](testing-strategy.md)
requires full validation as well. M0-T05 introduced no logging behavior; M0-T06
now implements the separate local sink. No new runtime dependency,
process runner, tool registry, scanner, Groq/provider implementation,
planner runtime, autonomous loop, database, report or CLI command is added.

## Runner integration (M1-T03)

The internal asynchronous runner returns OperationResult[ProcessExecution]. Missing
or non-executable programs map to ToolUnavailableError, other OS spawn/capture or spawn encoding errors
to ToolExecutionError and deadlines to ToolTimeoutError with effective timeout only.
Fixed messages omit OS paths/argv/environment/output/native exception objects.
Ordinary non-zero child exits return Success with the observed return code, leaving
interpretation to future adapters. No competing error/result hierarchy is added.
Failure has no payload, so bounded partial output is discarded on timeout/failure.
Caller cancellation uses Python asyncio.CancelledError, re-raised after cleanup;
it is not converted to the domain CancelledError. See [execution model](execution-model.md).

## Registry integration (M1-T04)

No new error hierarchy/code or result family is introduced. Invalid/duplicate or
conflicting trusted composition raises ConfigurationError (configuration_invalid).
Unknown requested capability returns existing Failure with PlannerValidationError
(planner_validation_failed); known capability without an adapter, unknown adapter ID
and unavailable/not_checked registration return ToolUnavailableError (tool_unavailable).
Fixed messages omit arbitrary requested names and executable/runtime details. Safe
known capability/adapter references may appear in existing ErrorContext fields.
Successful schema lookup uses Success[AdapterDefinition]; successful resolution
uses Success[InstanceOf[ToolAdapter]] with the trusted Python object. Internal lookup
payloads are not planner serialization APIs; catalog() is the explicit safe boundary.

## Action policy integration (M1-T05)

ActionPolicyValidator uses existing Success[ApprovedAction]/Failure/ErrorInfo.
Malformed requests, disallowed capability/risk, invalid parameters, missing target
semantics or completed-action eligibility and malformed check results map to
planner_validation_failed. Registry unknown capability also uses that code; missing
or unavailable registrations retain tool_unavailable. Scope rejections retain
scope_rejected/context; unavailable budget eligibility retains budget_exhausted.
No new code/category, exception hierarchy or competing rejection envelope exists.
Fixed policy messages omit planner reasons, raw inputs and native validation errors.
Callers correlate Failure with the requested action; ApprovedAction includes action_id.

## Budget failures (M1-T06)

BudgetController check/reserve reuse Failure/ErrorInfo from BudgetExhaustedError
for exhausted action/concurrency/host/rate/time/output limits and unknown/unsupported
budget semantics. Fixed messages identify the dimension; raw planner/clock data
is omitted. The existing conservative retryable=false remains: a rate window can
later admit a separately revalidated/reserved action, but no failure grants retry
permission. Invalid controller limits/initial clock use ConfigurationError; direct
model/config-snapshot validation uses ValidationError. No new code/context field or
error hierarchy is introduced. See [budget contract](execution-budgets.md).

## State transition failures (M1-T07)

The single StateTransitionError extends ReconAgentError with code
state_transition_invalid and category state. It reports malformed initial/transition
state, invalid lifecycle, identity/reference conflicts or unsupported input. It is
non-retryable and uses the existing ErrorInfo/Failure contract. Initial state errors
raise it with a fixed message and native cause chaining; transition rejection returns
Failure with fixed text and no raw state/input/cause. State failures cannot be
relabelled as failed/partial tool outcomes in ActionResult. No parallel exception
hierarchy, error context field or retry implementation is introduced.
See [state contracts](state-transitions.md).

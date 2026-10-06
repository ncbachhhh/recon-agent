# Internal process execution

M1-T03 implements `execution/AsyncProcessRunner`, an awaitable local process
primitive for trusted ToolAdapters, including M2-T02 Subfinder. It is scanner-agnostic and has no
planner, provider, scope, CLI, registry or authorization behavior. Importing the
package and constructing contracts/runner launch nothing and configure no logging.
No runtime dependency beyond the existing Pydantic dependency is added.

## Ownership and dispatch

```text
Operator supplies target + authorized scope + config
  → ReconSession / deterministic bootstrap / observations [future runtime]
  → AI planner selects capability                          [future]
  → ActionPolicyValidator local eligibility                 [M1-T05]
  → Tool Registry selects trusted adapter                  [M1-T04, implemented foundation]
  → ToolAdapter owns executable and literal argv           [M2-T02 Subfinder]
  → AsyncProcessRunner                                     [M1-T03, implemented]
  → OS process
  → adapter normalization / observations / planner again    [future]
```

Capability is not a command. ActionRequest/PlannerDecision remain
non-authoritative data with no executable/argv fields. The planner cannot call
the runner directly. Tool installation, ProcessSpec construction, process success
and audit records confer no authorization. The registry supplies identity/availability
facts; M1-T05 checks scope, capability parameters and risk locally, with restrictive
budget/completed-action seams. Future dispatch must revalidate and reserve resources
before adapters construct argv. The runner neither grants nor duplicates these
checks; it is inherently able to launch the executable a trusted caller supplies. There is no arbitrary
command product feature or CLI endpoint.

## Input and injection contracts

`ProcessSpec(executable=..., args=(...), timeout_seconds=None)` is strict frozen
internal data. Executable is a separate non-blank string; arguments are a tuple of
strings, including literal empty strings. Embedded NUL and wrong element/container
types fail structural validation. JSON arrays round-trip to tuples. No shell-like
string is parsed or split. There is no command-string overload, template, script,
pre/post command, cwd or interactive stdin option. M2-T02 adds an internal complete environment snapshot described below.

`await runner.run(spec)` returns the existing `OperationResult[ProcessExecution]`.
`ProcessRunner` is the small protocol future adapter tests can inject with a
fixture runner returning those same contracts. `AsyncProcessRunner` additionally
accepts a trusted internal spawn callable implementing `ProcessHandle`, for
deterministic fake-process tests; it is not configuration or planner input.
Invalid specs/configuration raise normal Pydantic ValidationError before spawn;
instances are revalidated, and execution settings are snapshotted at construction.

Production launch uses only `asyncio.create_subprocess_exec(executable, *args)`.
There is no shell wrapper, expansion, evaluation or TTY. `$HOME`, wildcards,
substitutions, quotes, spaces and shell operators remain literal child arguments.
The child inherits the caller's environment and working directory by default. A trusted ProcessSpec.environment tuple replaces child inheritance when supplied; the working directory remains unchanged. The runner never logs either. Stdin is DEVNULL, providing EOF rather
than waiting for operator input. Trusted adapters remain responsible for safe
executable selection and non-interactive tool options.

## Output and process facts

`ProcessExecution` carries argument count, observed return code, separate raw
`stdout`/`stderr` bytes, independent truncation flags, UTC aware start/finish times
and a monotonic duration in seconds. Start includes local launch time; finish is
after exit and stream capture. Duration does not depend on wall-clock subtraction.
There is no argv/executable/environment in returned metadata. Process output is
untrusted evidence, not instructions or safe diagnostic text.

`ExecutionConfig.max_output_bytes` is a **per-stream retained-byte cap**. At most
N bytes of stdout and N bytes of stderr are retained. Two tasks drain the streams
concurrently in chunks of at most 16 KiB. Bytes beyond each cap are discarded while
draining continues until exit/timeout/cancellation; each affected stream is marked
truncated. The cap applies during reading, not after `communicate()` buffering.
Asyncio pipe buffers have an explicit 64 KiB flow-control limit; read chunks,
transport buffers and bounded conversion copies add fixed/proportional overhead.
This is a retention bound, not a bound on total bytes generated or child memory/CPU.
The process deadline still limits noisy executions. Session/rate/CPU supervision
is future work; no global scheduling or budget enforcement is implemented here.

No decoding occurs in the runner. Adapters choose tool-format decoding explicitly;
for human text, `data.decode("utf-8", errors="replace")` safely handles malformed
bytes. Python dumps preserve bytes; JSON uses URL-safe base64 and round-trips even
invalid UTF-8. Text replacement may expand the byte length, so the retention cap
is defined over original bytes. A parser must check both truncation flags before
treating output as complete and record incomplete evidence appropriately.

Every launched normal exit returns `Success[ProcessExecution]`, including non-zero
or negative return codes. Success here means the process facts were collected;
adapters decide the meaning of tool-specific statuses and parser results. It is
not ActionResult, useful observation count or successful reconnaissance.

## Deadlines, cancellation and failure

The explicit spec timeout overrides `ExecutionConfig.default_timeout_seconds`.
Both are positive finite seconds; there is no second global timeout setting.
The deadline covers launch, exit and stream capture. Once it expires, normal
completion is no longer accepted: cleanup finishes before a canonical
`ToolTimeoutError`-derived Failure is returned, carrying only effective timeout.
File-not-found/permission-denied launch errors become `ToolUnavailableError`
Failures; other OS spawn/capture errors and spawn encoding errors become
`ToolExecutionError` Failures.
Messages are fixed and exclude native paths, arguments, environment and output.
No native exception objects are serialized or automatically logged.

On timeout or caller cancellation, terminate the direct child, wait up to 0.5
seconds for graceful exit, then kill if necessary and await reaping. Drain/wait/
stop tasks are accounted for. Shielded lifecycle ownership prevents cancellation
during spawn from losing the eventual child handle; repeated caller cancellation
cannot interrupt cleanup. Cancellation always propagates `asyncio.CancelledError`
after cleanup, including cancellation during timeout cleanup. It never becomes an
ordinary success/failure or the domain cancellation exception.

Failure has no payload field in the existing generic result contract. Bounded
partial output on timeout/capture failure is deliberately discarded after cleanup;
it is never placed in ErrorInfo.context or a competing outcome hierarchy. Caller
cancellation also has no returned payload. Future adapters cannot parse timeout
output through this API; any future evidence-preserving extension needs an explicit
contract change in its owning task.

Cleanup guarantees concern the **direct child under normal supported OS behavior**.
There is no process-group/descendant-tree supervision. Descendants may survive or
keep inherited pipes open; such tools require additional supervision before safe
adapter use. After kill, reaping depends on OS process completion. A pending OS
spawn must yield a handle/error before cleanup can finish, so total return time may
exceed the configured deadline by spawn/cleanup time. No strict whole-tree or
OS-stall wall-time guarantee is claimed. The implementation uses standard Python
async subprocess APIs; local tests use only the current interpreter, without
POSIX shell dependencies. A POSIX-only extra assertion verifies actual reaping.

## Diagnostics and deferred layers

The runner emits no logs/audit events and never pretends policy approved an action.
Spec executable/args and captured output are excluded from repr, but deliberate
model dumps still contain that internal data. Never dump them into diagnostics or
place credentials on command lines; prefer future explicit secret mechanisms.
Safe higher-layer events can select return code, argument count, duration and
truncation flags with their own correlation IDs. No environment is logged.

M1-T04 now implements immutable registry/capability mapping and the minimal trusted
adapter interface, without execution. M1-T05 adds pure action eligibility without
runner calls. M1-T06 supplies a separate local budget/concurrency/rate controller
without runner calls. M2-T02 Subfinder now uses the process boundary. Later scanner adapters, provider/planner runtime, orchestration, persistence, reporting and real CLI remain future tasks. See [tool contracts](tool-contracts.md),
[security model](security-model.md), [error contracts](error-model.md) and
[testing strategy](testing-strategy.md) for the surrounding boundaries.

## Aggregate resource layer (M1-T06)

BudgetController atomically reserves one attempt/concurrency permit and two stream
allowances before future dispatch. BudgetPermit context cleanup also works around
awaits and releases on exceptions, timeout and cancellation without awaiting.
Session elapsed/remaining time is monotonic and queried explicitly; this component
does not launch or interrupt a process. Future dispatch must clamp process deadlines
to remaining session time and use the same or smaller max_output_bytes as the budget
snapshot. M1-T03's bounded draining/capture remains unchanged. Aggregate allowance
is permanently charged per permitted attempt, including failed/cancelled attempts;
additional execution requires additional reservations. See
[resource ownership and limitations](execution-budgets.md).

## Native DNS execution (M2-T01)

resolve_dns does not use ProcessSpec/ExecutionRunner. Its explicitly registered trusted
DnsAdapter rechecks policy, independently scoped resolver infrastructure and atomic
budgets before bounded asynchronous native UDP exchanges. Existing process contracts
remain unchanged. See [DNS contact/resource/error semantics](dns-resolver.md).

## Complete child environment (M2-T02)

ProcessSpec.environment is an optional immutable tuple of (name, value) string pairs,
not a planner input. None preserves inheritance; () supplies an empty environment.
At most 64 unique entries; names are nonempty, at most 256 characters and cannot
contain NUL/=; values are at most 8,192 characters without NUL. Wrong types/duplicate
names reject before spawn. It is excluded from repr, still present in deliberate
internal dumps, and never added to ProcessExecution or catalog metadata. The runner
passes a new dict to create_subprocess_exec(env=...), without altering os.environ.
Argv/capture/timeout/cancellation behavior and default inheritance are unchanged.
Subfinder uses this seam to isolate ambient YAML/credentials/proxies in temporary
configuration directories; see [Subfinder execution](subfinder-adapter.md).

# Security model

Status: mandatory architectural constraints and mostly planned controls; M0-T03 implements strict configuration validation and separate redacted credentials. M0-T04 adds pure domain data contracts with provenance and non-authoritative planner/action representations. M0-T05 adds typed diagnostic errors/results; M0-T06 supplies explicit local logging/audit with bounded redaction; M1-T01 implements pure deterministic scope membership; M1-T03 adds an internal local process primitive. No scanner or operational reconnaissance dispatch exists. The platform is for systems the operator is explicitly authorized to assess. Authorization is an input requirement, not something inferred from public reachability or discovered data.

## Purpose and exclusions

The product collects reconnaissance metadata and evidence. Later exposure analysis may identify likely findings, but execution remains policy-controlled. It excludes arbitrary LLM-generated shell commands, `shell=True`, unrestricted command execution, exploitation, credential attacks, password spraying, brute-force authentication, destructive testing, persistence on remote systems, evasion, stealth, malware, privilege escalation automation, automatic remote modification, and out-of-scope scanning. Local session persistence is planned; it does not authorize remote persistence.

Groq is a planner/analyzer, not a terminal. A tool being installed, a port being open, or a template being available does not grant permission to execute it.

## Trust hierarchy

```text
Operator configuration
> repository policy
> deterministic validation
> planner recommendation
> remote evidence
```

This hierarchy determines provenance and authority; trusted operator configuration must still satisfy non-negotiable repository constraints. It cannot enable a forbidden capability. Repository policy defines the permitted envelope. Deterministic validation enforces that envelope. Recommendations cannot expand it; evidence cannot change any higher layer. Explicit operator updates are validated and auditable.

## Trust boundaries

| Boundary | Data crossing it | Required control |
| --- | --- | --- |
| Operator → configuration | Scope, budgets, profiles, tool paths | Typed validation, explicit authorization, restrictive defaults; secrets separated |
| Remote target → adapter | Network data and tool output | Bound bytes/time, parse defensively, retain provenance, revalidate derived targets |
| Adapter → state | Normalized observations and evidence | Typed schemas, source/execution references, canonical identity; no implicit authority |
| State → hosted provider | Selected evidence and capability catalog | Bounded/redacted normalized state; clearly labeled untrusted evidence; data minimization |
| Provider → policy | Structured recommendations | Strict schema; allowlist; scope/parameters/risk/budget/dedup checks; fail closed |
| Policy → execution | Validated capability request | Fixed adapter, argv construction, revalidation at dispatch, cancellation and limits |
| State → storage/reports | Facts, interpretations, remote text | Evidence lineage, local access controls, escaping, redaction, bounded retention |

Remote reconnaissance content may be sensitive even when authorized to collect. Before hosted-provider use, configuration must govern which evidence is sent; credentials and unnecessary raw content are excluded. A Groq key stays in a secret mechanism, never prompts, state, report, logs, exceptions, fixtures, or Git.

## Implemented configuration boundary

M0-T03 rejects unknown keys and invalid effective types/limits in trusted configuration. The explicit loader performs no runtime startup. Scope preferences contain no targets or authorization grants; enabling tools/planner/persistence only sets preferences. `GROQ_API_KEY` is loaded separately into an excluded `SecretStr` field, never ordinary configuration or diagnostic dumps. Displayed validation errors hide raw inputs; diagnostic callers of Pydantic structured errors must omit input values. No arbitrary commands, argv or policy-bypass options exist. See [configuration](configuration.md) for sources, precedence and failure behavior. Configuration contracts do not implement scope enforcement, capability policy, budgets, logging or provider communication. ScopeValidator consumes explicitly assembled Scope data; application settings never authorize targets.

## Implemented domain boundary

M0-T04 rejects unexpected domain fields and invalid structural types, requires observation/evidence provenance, and labels evidence untrusted. Target and Scope are declaration data; neither performs authorization. ActionRequest and PlannerDecision carry unapproved intent/recommendations and expose no executable behavior. Executable fields and reserved executable parameter keys are rejected structurally; allowed JSON data still requires future capability-specific policy validation. Domain code imports only pure shared ErrorInfo primitives beyond domain/Pydantic types, never configuration or operational layers, and performs no I/O. It does not enforce scope, capability membership, budgets, lifecycle transitions or policy. See [data model](data-model.md) for the exact contracts and staged models.

## Implemented error/result boundary

M0-T05 gives operational failures stable codes and bounded, allowlisted scalar
context; no credential/environment/output/traceback dump fields exist. Configuration
failures have fixed messages and source labels. ErrorInfo serialization omits
native chained causes and raw source inputs. Caller-authored diagnostic strings
still require sanitization; complete native tracebacks are not the safe diagnostic
API. Results reject contradictory success/error states; ActionResult distinguishes
policy rejection, timeout, cancellation and partial evidence. Retryability is
explicit metadata and grants no permission or automatic retry. These contracts
perform no logging, recovery or operational execution. See [error model](error-model.md).

## Implemented logging/audit boundary

M0-T06 configures only the project logger on an explicit call, without file or
remote collectors. Context copies mask secret-labelled fields/wrappers, and
explicitly registered local values are removed from emitted text/ErrorInfo.
Unregistered free-form secrets still require producer discipline. Raw models,
environment/output/traceback dumps and private reasoning/transcript/command keys
are not an audit input contract. Captured tests verify redaction and malformed
record/sink failures without stdlib's raw-record debug leakage.

Bounded JSON/ASCII escaping prevents remote text from forging physical log lines
or terminal controls. Evidence remains data; diagnostic redaction does not mutate
source observations/artifacts or infer authority. Record summaries/action reasons,
not model chain-of-thought. AuditEvent is non-authoritative: even an approval event
cannot authorize execution by deserialization/replay. Later policy/producers remain
responsible for truthful recording, scope/budgets and dispatch. See
[logging and audit](logging-and-audit.md) for precise redaction limits and local sink
behavior; no logging from domain/error constructors, telemetry export or persistence
exists.

## Untrusted inputs

Treat all of the following as data without policy authority:

- Target-provided HTTP content, robots.txt, sitemap.xml, JavaScript, and headers.
- Service banners, including Nmap banners, DNS data, and TLS certificate text/SANs.
- External tool stdout and stderr, including Nuclei result metadata.
- Filenames and paths discovered remotely, even if they resemble local paths or command options.
- Model responses, including valid-looking JSON, reasons, and summaries.

Normalization does not make remote content trusted. Preserve origin and trust labels through state, planner input, storage, and reporting. Missing provenance is an error, not a reason to invent an observation.

## Indirect prompt injection

Remote pages, banners, tool metadata, and evidence can embed text such as “ignore previous instructions”, “run this command”, “scan this host”, or “upload this file”. Those strings are evidence only. They never become system instructions, operator approval, a configuration change, or a capability definition.

The LLM may analyze these strings; the fixed planner instructions must identify them as untrusted evidence. Evidence is placed in structured, labeled input separate from system policy. Delimiters and instructions help but cannot guarantee model behavior. Deterministic schema validation, capability allowlists, scope checks, immutable policy, and execution controls remain necessary even when the model obeys or repeats malicious text. Tests must prove prohibited recommendations cannot cause execution, regardless of model response.

Do not let remote content trigger local reads, uploads, expanded targets, template paths, tool paths, arguments, secrets exposure, or policy edits. Planner reasons are explanatory text, never executable parameters.

## Scope enforcement

Centralized validation covers domain/subdomain boundaries, canonical hostnames, IPv4/IPv6, CIDRs, URLs, ports where constrained, and redirect-derived targets. Exact domain authorization and subdomain authorization must be distinguished explicitly; suffix/lookalike confusion must fail. Discovered DNS addresses, certificate SANs, links, and redirect destinations require independent validation before contact or actionable promotion.

Discovery does not imply authorization. Planner recommendation does not imply authorization. Every newly introduced network target must pass deterministic scope validation before future execution.

M1-T01 implements local ScopeValidator with exact roots, label-aware domain descendants, parsed IP/CIDR membership, host-level HTTP/HTTPS URLs, exclusion precedence and canonical structured failures. Private-address preferences gate RFC1918/IPv6 ULA membership; they grant no scope. Unsupported Unicode/IDN, zones/mapped IPv6, malformed/ambiguous targets and invalid declarations fail closed. The validator emits no logs, performs no DNS/network and mutates no declarations. See [scope model](scope-model.md) for authoritative semantics and [ADR 0002](decisions/0002-scope-and-derived-addresses.md).

M1-T02 regression tests cover adversarial name/URL/address parsing, private gate
boundaries, exclusions, rule order and stable failures under network/DNS guards.
Test-only mock consumers prove rejected redirect/discovery candidates cause no
contact call; production dispatch/contact enforcement remains future work.

A domain resolving to an address is evidence, not IP authorization. Future adapters must independently validate every supplied concrete address, constrain/pin approved destinations and revalidate address changes before contact; no resolution or rebinding runtime exists yet. Tools must not bypass scope via their own recursion, redirect following, secondary lookup targets, or automatic feature discovery. Disable unsafe implicit behavior or reject execution when the adapter cannot constrain it. A post-scan filter cannot undo an out-of-scope network request.

If scope cannot be established reliably, **do not execute the action**. Malformed targets, ambiguous parsing, unresolved policy semantics, unsupported tool behavior, and missing authorization are fail-closed cases. Record the rejection with enough evidence to explain it without leaking secrets.

## Controlled execution and resource limits

Every executable operation maps to a registered capability and controlled adapter. The planner cannot supply executable paths, arbitrary arguments, shell strings, environment variables, or template paths. Adapters validate options and use argument arrays, guarding against option injection as well as shell injection. M1-T03 implements the internal runner with no shell or command-string API, per-stream bounded capture, deadlines, direct-child timeout/cancellation cleanup and safe outcome metadata. Higher dispatch enforcement remains future work.

Enforce session action/time budgets, max concurrency, per-host limits, per-tool rate limits, crawl/content limits, and output-size caps. Reserve/check budgets atomically for concurrent work, recheck at dispatch, and stop retries when limits are reached. Exhaustion, cancellation, or timeout is an explicit recorded result. A failure does not justify a more intrusive fallback.

Template execution requires named reviewed policy profiles; deny unknown, unreviewed, or potentially intrusive templates in the default profile. Tool defaults and updates must not silently widen effective behavior.

## Evidence, logging, and lifecycle

Keep observations distinct from interpreted findings and planner recommendations. Link each fact/finding to evidence and an execution or collection source. Sanitize fixtures, escape terminal/HTML control content, and redact secrets in logging/reporting. Store only required evidence; retention and access policy are future configuration decisions.

Rejections, planner decisions, execution outcomes, and lifecycle events must be auditable. Resume revalidates current policy, remaining budgets, and completed-action identity. Repeated failures cannot lead to endless retries. Fatal policy/environment errors, lack of useful allowed actions, completion, budgets, time, or operator cancellation stop execution safely.

## Verification obligations

Offline tests use fake providers/runners and sanitized fixture output. Scope regression/property tests cover domain confusion, IPv4/IPv6/CIDRs, malformed URLs, and redirect/address changes. Prompt-injection tests assert both rejection and absence of execution. Concurrency tests assert atomic budget and scope enforcement. CI never silently contacts public targets. Real integration or lab testing requires explicit authorization and opt-in targets.

Document controls as planned until implementation and test evidence support them. M13 security review reconciles this document with code before MVP declaration.

## Concrete execution boundary (M1-T03)

Only trusted adapter code may construct ProcessSpec executable/argv after future
policy/registry approval. No direct planner-to-runner path exists; domain contracts
are unchanged. The runner performs no target resolution, scope expansion, tool
allowlisting or policy approval. It is not a public arbitrary-command feature.
Production launch uses create_subprocess_exec with literal separated arguments,
DEVNULL stdin and independent pipes, without shell parsing, expansion or TTY.

Output retention is bounded while reading: ExecutionConfig.max_output_bytes caps
each stream, concurrent readers discard excess and report independent truncation.
Bytes remain untrusted evidence; no automatic argv/output/environment logging or
policy/audit emission occurs. Returned metadata contains no argv/executable path.
The child inherits environment/cwd; trusted callers must avoid command-line secrets.

Timeout cleans up then returns ToolTimeoutError-derived Failure. Cancellation
terminates/reaps the direct child and re-raises asyncio.CancelledError; shielded
ownership also covers spawn and repeated cancellation races. Termination escalates
to kill after a 0.5-second grace period. No descendant/process-group containment is
implemented: descendants can survive or hold pipes open; pending OS spawn and reaping
can extend cleanup beyond the deadline. Future adapters must account for this
limitation before integrating tools with child processes. See
[execution model](execution-model.md) for exact semantics and output/error limits.

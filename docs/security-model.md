# Security model

M4-T07's [offline selection regressions](protocol-capabilities.md#selection-regression-coverage-m4-t07)
verify normalized service identity over ports, exact conflict vetoes and conservative
unknown handling. Selection cannot call authorization, resolution, adapters, runners,
credentials or contact; actual adapter denials leave collectors and budgets untouched.
Remote product/version instructions remain preserved data, with no new capability.

Status: mandatory architectural constraints and mostly planned controls; M0-T03 implements strict configuration validation and separate redacted credentials. M0-T04 adds pure domain data contracts with provenance and non-authoritative planner/action representations. M0-T05 adds typed diagnostic errors/results; M0-T06 supplies explicit local logging/audit with bounded redaction; M1-T01 implements pure deterministic scope membership; M1-T03 adds an internal local process primitive; M1-T04 adds registry facts, M1-T05 composes pure action eligibility and M1-T06 adds local resource reservations and M1-T07 adds controlled in-memory state; M1-T08 adds pure action identity/dedup and atomic request admission. M2-T01 adds operational native DNS behind explicit registry/policy/resources;
M2-T02 implements passive Subfinder; M2-T03 implements independently scoped bulk DNSX verification; M2-T04 implements HTTPX probing with independently scoped contact IP constraints and no redirects; M2-T05 implements numeric bounded Naabu CONNECT discovery; M2-T06 implements NSE-free bounded Nmap service fingerprinting; M2-T07 adds a bounded deterministic six-capability workflow; generic autonomous dispatch remains future work. The platform is for systems the operator is explicitly authorized to assess. Authorization is an input requirement, not something inferred from public reachability or discovered data.

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

M0-T03 rejects unknown keys and invalid effective types/limits in trusted configuration. The explicit loader performs no runtime startup. Scope preferences contain no targets or authorization grants; enabling tools/planner/persistence only sets preferences. `GROQ_API_KEY` is loaded separately into an excluded `SecretStr` field, never ordinary configuration or diagnostic dumps. Displayed validation errors hide raw inputs; diagnostic callers of Pydantic structured errors must omit input values. No arbitrary commands, argv or policy-bypass options exist. See [configuration](configuration.md) for sources, precedence and failure behavior. Configuration contracts do not operate subsystems; explicit consumers implement scope/action policy, budgets and logging. ScopeValidator consumes explicitly assembled Scope data; application settings never authorize targets.

## Implemented domain boundary

M0-T04 rejects unexpected domain fields and invalid structural types, requires observation/evidence provenance, and labels evidence untrusted. Target and Scope are declaration data; neither performs authorization. ActionRequest and PlannerDecision carry unapproved intent/recommendations and expose no executable behavior. Executable fields and reserved executable parameter keys are rejected structurally; allowed JSON data requires the M1-T05 capability-specific policy validator. Domain code imports only pure shared error/result primitives beyond domain/Pydantic/standard-library types, never configuration or operational layers, and performs no I/O. Individual records do not enforce scope, capability membership, budgets or policy; M1-T07 adds controlled action lifecycle recording with whole-state validation. See [data model](data-model.md) for the exact contracts and staged models.

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
contact call; generic production dispatch remains future work; implemented adapter contact checks are described below.

A domain resolving to an address is evidence, not IP authorization. Future adapters must independently validate every supplied concrete address, constrain/pin approved destinations and revalidate address changes before contact; HTTPX now constrains resolved contacts through its reviewed concrete-IP dial gate; generic rebinding orchestration remains future work. Tools must not bypass scope via their own recursion, redirect following, secondary lookup targets, or automatic feature discovery. Disable unsafe implicit behavior or reject execution when the adapter cannot constrain it. A post-scan filter cannot undo an out-of-scope network request.

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

Only trusted adapter code may construct ProcessSpec executable/argv after current
policy approval and registry resolution. No direct planner-to-runner path exists;
domain contracts contain no execution fields. The runner performs no target resolution, scope expansion, tool
allowlisting or policy approval. It is not a public arbitrary-command feature.
Production launch uses create_subprocess_exec with literal separated arguments,
DEVNULL stdin and independent pipes, without shell parsing, expansion or TTY.

Output retention is bounded while reading: ExecutionConfig.max_output_bytes caps
each stream, concurrent readers discard excess and report independent truncation.
Bytes remain untrusted evidence; no automatic argv/output/environment logging or
policy/audit emission occurs. Returned metadata contains no argv/executable path.
The child inherits environment/cwd by default; trusted ProcessSpec.environment can replace child inheritance. Subfinder uses isolated config paths and excludes ambient secrets/proxies. Trusted callers must avoid command-line secrets.

Timeout cleans up then returns ToolTimeoutError-derived Failure. Cancellation
terminates/reaps the direct child and re-raises asyncio.CancelledError; shielded
ownership also covers spawn and repeated cancellation races. Termination escalates
to kill after a 0.5-second grace period. No descendant/process-group containment is
implemented: descendants can survive or hold pipes open; pending OS spawn and reaping
can extend cleanup beyond the deadline. Future adapters must account for this
limitation before integrating tools with child processes. See
[execution model](execution-model.md) for exact semantics and output/error limits.

## Concrete capability/registry boundary (M1-T04)

Planner output cannot select executable code or register adapters. CapabilityId is
finite and excludes arbitrary command operations; unknown names fail closed with
planner_validation_failed. Known conceptual names without registered adapters fail
with tool_unavailable, as do unavailable/not_checked registrations. No fallback,
capability-to-binary conversion, planner-controlled import, PATH discovery or mutable
global registry exists. Explicit trusted application composition supplies adapter
instances and snapshots metadata into immutable mappings; duplicate/conflicting
registrations fail at startup with configuration_invalid.

The planner-safe catalog contains only capability, semantic description, risk class
and declared availability. Internal adapter IDs/schema classes/runtime instances are
not planner input. ToolAdapter implementations are the first capability execution
layer allowed to know executable details; the lower-level ExecutionRunner receives
ProcessSpec only from trusted internal code. M1-T05 typed parameter validation must
precede trusted argv construction; no planner dictionary becomes flags. ActionRequest
also rejects import_path/python_module parameter keys. Text is data, never evaluated.

Risk metadata is not risk enforcement. Registered is not available; available is
not enabled or authorized. Registry lookups never check scope, approve actions,
consume budgets, probe binaries, call the runner or produce approval/execution audit
events. Discovery does not imply authorization. Planner decisions do not imply
authorization. Capability existence does not imply action authorization. M1-T05
implements combined local checks; no production scanner/dispatch/planner runtime exists.
See [tool contracts](tool-contracts.md) for exact schemas and trust assumptions.

## Concrete action policy boundary (M1-T05)

Planner decision != authorization. Registered capability != authorization.
Scope match alone != complete action authorization.

ActionPolicyValidator composes strict ActionRequest revalidation, available registry
metadata, explicit frozen capability/risk allowlists, ScopeValidator and registered
strict parameter validation. Allowlists default empty. The primary target and all
trusted declared secondary-target fields (including defaults) pass centralized
scope validation. Missing parameter-target semantics, unsupported representations,
unknown/unregistered/unavailable/disallowed capabilities, invalid parameters and
malformed/outside targets reject. Discovery/provenance, reason, priority and analysis
summary cannot override a check or expand scope. Executable/import keys remain denied.

The shared Success/Failure/ErrorInfo contracts encode approval/rejection; fixed
failure messages omit raw validation inputs. ApprovedAction carries typed parameters
internally, not argv. It is not a replayable authorization token. Future dispatch
must revalidate current request/policy/availability/scope and reserve resources;
future adapters must constrain contact and validate newly discovered destinations.
No production dispatcher exists and the runner is unchanged.

PLAN's budget/completed-action seams are restrictive local interfaces: missing
budget eligibility returns budget_exhausted; missing completed-action eligibility
returns planner_validation_failed. Only offline tests inject completed-action
permitting fakes. M1-T06 implements budgets/rates/reservations; M1-T08 supplies the
real ActionDeduplicator eligibility service. Validation
performs no network, DNS, subprocess, dynamic loading, adapter/runner execution,
provider calls or audit/log emission. No tool.execution_started event is emitted.
Trusted schema/check implementations must be pure local code; application code is
not sandboxed. See [policy contract](tool-contracts.md#action-policy-contract-m1-t05)
and [ADR 0004](decisions/0004-action-eligibility-boundary.md).

## Resource enforcement (M1-T06)

Policy authorization != budget availability. AI planner cannot raise resource
limits. Only trusted session assembly constructs immutable ExecutionBudget limits;
no override/reset/refund surface is present on planner models or the controller.
BudgetController atomically checks/reserves action, concurrency, all declared hosts,
rolling capability rate, monotonic time and aggregate output allowance. Unknown or
unregistered capabilities never create buckets; unsupported CIDR host accounting
fails closed. ScopeMatch canonical parsing prevents case/dot/URL/IP aliases from
splitting host counts; names never implicitly authorize or equate to DNS answers.

Checks/rejections do not spend attempts. Granted attempts keep action/host/rate/output
charges through failure, timeout, cancellation or abort; retries pay again. Context
ownership releases concurrency synchronously, once, including across cancelled
awaits. Bad/backward clocks permanently exhaust time, with release still available.
No failure resets limits. BudgetExhaustedError supplies canonical fixed Failure data;
future callers own audit/history recording. A permit grants resources, never scope
or execution authority. Future adapters must obey traffic/output/time envelopes;
there is no scanner containment or running-work interrupt added here. See
[precise contracts](execution-budgets.md) and [ADR 0005](decisions/0005-budget-reservations.md).

## State integrity (M1-T07)

The explicit ReconStateMachine owns one validated state, copying initial/committed/
returned snapshots under a local lock. Invalid transitions, identity collisions,
missing/conflicting provenance or terminal re-entry fail with canonical structured
state_transition_invalid without partial mutation. No remote text changes policy.
Failed/rejected/cancelled/timeout results cannot claim successful observations; known
unfinished/unsuccessful execution evidence cannot indirectly support them either.
Partial stays distinguishable from completed. Evidence remains untrusted data.

PlannerDecision recording neither requests/approves actions nor changes scope,
configured limits, consumption or execution. State stores caller-supplied policy
references and execution history without performing or authenticating authorization;
future dispatch must still revalidate current policy and reserve resources. Snapshot
serialization grants no replay permission. Read-only budget records cannot update
BudgetController. State owns ID/reference integrity; M1-T08 policy adds semantic
action deduplication through a controlled atomic request admission seam. No scanner/
network/DNS/process/provider/dynamic import or logging
side effects exist. See [ownership and trust limits](state-transitions.md).

## Semantic duplicate boundary (M1-T08)

Planner explanation != action identity. Trusted registry schemas and centralized
scope semantics define capability/target/parameter identity; remote evidence cannot
change them. Reason/priority/IDs, key ordering and already accepted target aliases
cannot evade equivalence. Unknown/malformed/unavailable/outside actions fail closed.
Completed/in-flight equivalents deny; explicit failed retries default to zero and
require retryable errors plus a bounded trusted limit. Rejected/partial/cancelled/
timeout equivalents deny. A new action ID alone cannot reset history.

Atomic request admission consults history under the existing state lock, admitting
one simultaneous equivalent request; lookup alone makes no claim. Eligibility
cannot authorize, reserve resources or execute. Own pending policy revalidation
requires matching semantic data; terminal IDs cannot replay. Current policy and
charged resources remain independent future dispatch obligations.
See [complete dedup/retry/trust contract](action-deduplication.md).

## Operational DNS boundary (M2-T01)

DnsAdapter executes only after checking its registry binding, current ActionPolicyValidator
and an atomic BudgetController reservation. Original name and trusted numeric resolver
IP require independent ScopeValidator approval before exchange. Both hosts consume
per-host budgets. Only the original absolute name is queried, up to six fixed types;
no system resolver, alias/referral follow-up, retry, TCP fallback, shell or subprocess.
The operator-selected recursive resolver is infrastructure; its upstream activity is
outside this client's containment. The client contacts only its approved numeric IP.

A/AAAA/CNAME/MX/NS discoveries remain untrusted observations, never Scope additions
or executable authorization. Subsequent name/address contact must reauthorize through
ScopeValidator and policy. TXT preserves exact octets as hex and escaped presentation,
without interpretation/evaluation. Fixed failures omit raw responses and partial facts;
negative responses retain explicit status/provenance. Native wire/record/output/deadline
bounds and cancellation release apply. No planner endpoint/flags/command fields,
brute force, uncontrolled enumeration, later adapter, generic dispatch or AI loop.
See [precise bounds and trust limits](dns-resolver.md) and
[ADR 0008](decisions/0008-bounded-native-dns.md).

## Passive Subfinder boundary (M2-T02)

The adapter checks the authorized query root and current policy/registry/dedup/shared
budgets before building fixed argv. Strict empty parameters deny every planner flag,
source/path/proxy/credential/environment override. Only one explicit credential-free
HackerTarget source receives the authorized root; operators authorize third-party
use/disclosure independently of reconnaissance target scope. Provider HTTP transport
and data are external service behavior, not permission to contact discovered names.
Subfinder runs without active resolution or target probing. No DNS verification,
follow-up, shell, fallback scanner or automatic install exists.

Reviewed upstream ambient YAML can enable active mode even with false CLI defaults.
A bounded internal ProcessSpec complete-environment seam enables temporary HOME/config
isolation without changing the parent environment; the runner retains sole launch/
timeout/cancellation ownership. Secrets/proxy/config variables are not inherited.
Malformed/outside-query-root output fails atomically; operationally excluded proper
descendants can be recorded as data only. Existing ScopeValidator must authorize
every future contact; scope snapshots never change. Raw stdout/stderr/configuration
and paths do not enter errors, planner catalog or normalized evidence. See
[precise boundaries/limits](subfinder-adapter.md) and
[ADR 0009](decisions/0009-isolated-passive-subfinder.md).

## Bulk DNS verification boundary (M2-T03)

verify_dns validates each supplied candidate and numeric resolver before execution;
one rejected candidate denies the entire batch. Only approved absolute names enter
the temporary list. Stream mode, fixed single record type/attempt/worker/rate and
isolated environment prevent wildcard/trace/discovery/ambient-config expansion.
DNSX may fall back from UDP to TCP only at the same scoped numeric resolver. Derived
addresses/aliases never become contact authority; merged DNS sections and suspected
shared addresses remain ambiguous evidence. Partial output cannot establish a
completed action. Runner/budget deadlines/output/cancellation remain enforced. See
[DNSX contract](dnsx-adapter.md) for reviewed version, contact limits and provenance.

## HTTP probing boundary (M2-T04)

HttpxAdapter independently checks each original candidate, operator numeric resolver
and all finite numeric HTTP contact addresses through ScopeValidator before temporary
input or dispatch. Mixed batches reject atomically. Reviewed HTTPX 1.9.0 networkpolicy/
fastdialer enforce the checked concrete-IP set before numeric dial, so DNS does not
confer authority. Custom resolver disables system/public lookup fallback. No-follow
redirect configuration, isolated environment/null flag config and disabled CDN/auth/
update/discovery behavior prevent hidden scope expansion. Even same-host redirects
are evidence only; scope status is not contact permission. Planner parameters expose
no flags/executable/proxy/headers/files; runner remains shell-free and bounded.

Titles/server/location/technologies are untrusted data, with no vulnerabilities or
follow-up scanners inferred. Unknown versions/modes fail closed; malformed/unreported
output identifies partial limits. Existing runner direct-child and OS resource limits
and recursive resolver infrastructure boundaries remain explicit. Source/fixtures
are reviewed without live-binary contact. See [HTTPX contract](httpx-adapter.md) and
[ADR 0011](decisions/0011-constrained-httpx-probing.md).

## Naabu numeric contact containment (M2-T05)

Naabu receives only independently scoped numeric IPs, never names/CIDRs/ASNs. Names
require explicit operator bindings and independent address membership, with no inferred
DNS authorization. Every primary/member/contact passes centralized scope; mixed batches
reject before input. Trusted finite integer TCP ranges, fixed isolated CONNECT stream
mode and atomic existing budgets bound discovery. No shell/planner flags, raw SYN,
stealth/evasion, host discovery, passive API, proxy, service or Nmap mode. Unknown
versions reject. Output grants no hosts/ports authority; no later contact starts.
See [contract/source limitations](naabu-adapter.md) and [ADR 0012](decisions/0012-numeric-bounded-naabu.md).

## NSE-free numeric fingerprinting (M2-T06)

Standard Nmap -sV automatically invokes version NSE scripts. NmapAdapter accepts only
detected 7.95 builds compiled without Lua; constructed/AVAILABLE-but-undetected adapters
cannot execute. Native CONNECT/version probes use one independently scoped numeric
contact and at most 128 requested ports within trusted prior-discovery selections.
No name resolution, host discovery, NSE, OS/aggressive scan, arbitrary options or broad
port defaults. Strict required input and current policy/final scope/resource checks
precede argv. Explicit operator database paths and complete temporary child environment
exclude ambient target/config/proxy expansion. Safe bounded UTF-8 XML rejects entity/
DTD expansion, extra targets/ports and unsupported modes. Version/banner/CPE strings
remain untrusted evidence; no vulnerability inference or permission. See
[contract](nmap-adapter.md) and [ADR](decisions/0013-nse-free-bounded-nmap.md).

## Deterministic M2 integration (M2-T07)

M2 pipeline = deterministic integration proof.
M6/M7 = future AI planning/autonomous loop.

The bounded explicit DiscoveryWorkflow now coordinates only the six M2 capabilities
through current policy, real dedup admission, registry and shared adapter-owned budgets.
Each adapter accepts an optional trusted post-reservation/pre-contact `on_started`
notification; failed notification prevents contact and releases its charged permit.
No policy/dedup bypass or second reservation exists. Terminal state ingestion now
accepts related assets/hosts/services/endpoints atomically with observations/evidence;
unsuccessful results cannot ingest those subjects. Exactly tool_unavailable may be
recorded as a pre-start rejection without an invented execution ID. Existing lifecycle
edges and all other failure restrictions remain unchanged.

Nmap selection snapshots derive only from recorded completed/partial Naabu actions;
`with_selections` preserves the same detected installation and limits in a detached
adapter/registry snapshot. Contact scope is independently rechecked by adapters.
Discovered subdomains, IPs, redirects and CNAME/MX/NS hosts grant no authorization.
No M3 scanner, provider/planner, autonomous loop, persistence, reporting or real CLI.
Safe correlated AuditEvents and normalized output envelopes remain in memory, with
no implicit log or runtime startup. See [pipeline contract](deterministic-discovery.md)
and [ADR 0014](decisions/0014-deterministic-discovery.md) for branching, failure mapping,
atomic rollback and unchanged infrastructure/compatibility limitations.

## Fixed common-file execution (M3-T01)

The standalone inspect_common_files capability rechecks current registry/policy/dedup
and reserves shared budgets. Scoped URL names and operator-pinned numeric IPs need
independent membership before every GET; no DNS or rebinding contact occurs. Fixed
paths and empty planner parameters prevent arbitrary downloads. Redirects require
independent destination/address validation plus same-path/no-query/no-downgrade rules
and finite hops. No outside destination is contacted. Body/header/wire/deadline/rate/
output limits and synchronous socket abort/cancellation cleanup are enforced.
UTF-8 sitemap parsing rejects all DTD/entity declarations before ElementTree; it
performs no external resource resolution or recursion. Robots paths/sitemap URLs/
security contact metadata and instruction-like text remain untrusted facts, grant
no scope and trigger no automatic contact/email/upload/command. See [contract](common-file-inspector.md).

## TLS certificate inspection (M3-T02)

TLSX contacts only independently scoped original endpoints and pinned numeric peers.
Atomic batches reject before input creation; current registry/policy/dedup/shared
budgets and final per-process checks apply. Adapter owns all flags/files/SNI and
isolates environment/config/PATH, uses native ctls with revocation/cloud/update/
extra enumeration disabled. CN/SAN/subject/issuer/error strings remain bounded
untrusted facts, never instructions, authorization, bindings, assets or Findings.
No discovered certificate name/IP or CRL/OCSP URL is contacted. Supported Linux
1.4.0 and same-peer dial fallback/resource limits: [contract](tlsx-adapter.md).

## Bounded crawl execution (M3-T03)

Katana runs depth zero with positive duration and redirects disabled: discoveries
never enter its contact queue, including always-on htmx state-changing methods.
Adapter admits only freshly scoped numeric same-origin GET hyperlinks/script resources
under finite graph/time/rate/output bounds. Hostname modes reject before contact.
Forms/JS endpoints/redirects/outside hosts remain untrusted data without authority.
Private ProcessSpec cwd also isolates relative Katana file cleanup; no global chdir.
See [contract](katana-adapter.md) for compatibility and transport/resource limits.

## Feroxbuster content contact boundary (M3-T04)

Numeric HTTP(S) directory subjects and every generated word URL/IP are centrally scoped
before each call. Hostname modes fail closed. Fixed no-recursion/no-extraction/no-follow
profile prevents remote links/redirects/robots/JavaScript/word collection from introducing
contacts. Four reviewed relative paths only; no planner file/flags/proxy/headers.
Adapter finite recursion counts three startup/base GETs per directory and applies total
request/depth/directory/token-bucket/thread/deadline/aggregate-output limits. Bootstrap
rate burst is bounded and explicitly documented, not uniform spacing. Private env/cwd
and rejection of global/binary-adjacent config prevent ambient behavior changes.
Endpoints/status/path names/Location remain untrusted evidence without authority or
vulnerability inference. Existing policy/runner/direct-child limits apply; see the
[contract](feroxbuster-adapter.md) and [ADR 0018](decisions/0018-bounded-feroxbuster.md).

## Specialized FFUF boundary (M3-T05)

FFUF only offers explicit vhost_names: numeric scoped HTTP(S) contact, fixed HEAD
and internal Host substitution from a small application catalog/scoped operator
suffix. Every actual URL/IP and suffix rechecks before each invocation. Candidate
Host values are test input, never permission to resolve/contact new hosts. No
redirect following, credentials/auth attacks, arbitrary flags/wordlists/files/FUZZ
positions, templates, body/POST/parameter/path fuzzing or scope expansion. Fixed
argv/private config environment and cwd, two-attempt-per-candidate retry accounting,
sequential pacing, aggregate capture and shared deadline/budget contracts apply.
Location/candidates remain untrusted evidence; no vulnerability/vhost confirmation
follows from status. See [precise bounds and limits](ffuf-adapter.md).

## Web identity boundary (M3-T06)

Pure canonical URL identity performs no network/DNS/process/provider work and
confers no authorization. Original action URL inputs pass centralized scope before
shared identity is computed; ScopeValidator membership rules are unchanged. Userinfo,
encoded/ambiguous authority, zones/mapped IPv6 and unsupported host forms reject.
Outside hosts remain outside, including suffix lookalikes. Percent-encoded path/query
bytes, order/duplicates, methods and FFUF Host variants remain distinct. Seen or
reported-contact state is untrusted evidence, never permission for a future request.
Raw observations/evidence remain unchanged. The [precise identity contract](web-identity.md)
defines normalization and malformed-candidate failure; each later concrete contact
still needs independent current scope/policy/resource checks.

## Protocol relevance boundary (M4-T01)

Remote normalized Service names/products/version strings remain untrusted evidence.
Exact reviewed TCP service names select only a semantic inspect_protocol family
contract; familiar ports and product/banner substrings cannot supply missing identity.
Unknown/composite/unreviewed/malformed data or recognized product conflicts select
nothing. Selection never grants scope, consumes budgets, records actions or invokes
policy/planner/adapter/runner. There are no auth/credential/command fields, exchanges,
network/process/Groq calls or operational registrations in the framework. Operational
adapters, including M4-T02 SSH, require reviewed pre-authentication profiles and
current policy/scope/history/resources/contact validation before execution. Metadata result schemas preserve source
and untrusted evidence; hostile text cannot extend the capability table. See
[protocol contracts](protocol-capabilities.md).

## Receive-only SSH boundary (M4-T02)

SSH capability = unauthenticated metadata only. Trusted observed-service bindings,
current policy/risk/schema/dedup, independent subject/numeric scope and charged
shared budgets gate one TCP connection. Native transport reads bounded server
identification and closes with zero SSH application bytes sent, before binary
packets. No client identification, auth attempts (including none/public key),
credentials/private keys, commands/shell/SFTP/SCP/exploit or library fallback exist.
Native numeric family/flags prevent DNS fallback. Banners/comments/preambles remain
untrusted metadata; explicit software hints imply neither verified identity nor
vulnerability and never introduce destinations or actions. Fake-stream write/drain
sentinels and unread authentication bytes prove the no-auth path. M4-T03 SMB is
separately operational through explicit alternative composition;
database has reviewed M4-T06 profiles; M4-T04 FTP/M4-T05 SMTP are described below. See [SSH profile/limits](ssh-adapter.md).

## Negotiate-only SMB boundary (M4-T03)

SMB capability = safe metadata collection only. One fixed command-0/session-0 SMB2
NEGOTIATE occurs after current registry/policy/dedup, independent subject/numeric
scope and shared budget checks. No session setup/authentication (including anonymous),
credentials/hashes, spraying/brute force/relay/capture/pass-the-hash, shares/RPC/files,
remote reads/writes/deletes/commands, exploitation or fallback. Network stream write
sends negotiation only; no SMB WRITE dispatch exists. Server GUID/signing and opaque
strings remain untrusted reported facts, never Findings/authority or new contacts.
Exact outbound-byte and no-second-packet regressions guard this boundary. No new
library/binary/router/provider/CLI path. See [SMB contract](smb-adapter.md).

## FTP unauthenticated metadata (M4-T04)

**FTP capability = unauthenticated metadata only.** Explicit native_ftp/FtpAdapter
uses strict family=ftp/observed port/tcp inputs and immutable prior Service/numeric
contact bindings. Current registry/policy/dedup/independent subject/contact scope
and shared atomic budgets precede one bounded native control connection. Only
a valid 220 greeting enables one fixed FEAT request; no authentication (including
anonymous), credentials/brute force, USER/PASS, LIST/RETR/STOR/DELE, writable tests,
data connections, arbitrary commands/options or TLS negotiation path exists.
Generic ProtocolMetadataOutput/Observation/untrusted Evidence preserve original
Service, port, banner/features/hints, caller UTC/execution, source and snapshot hash.
Denied/unsupported/malformed features retain a partial banner with canonical error;
timeout/refused/malformed greeting uses canonical Failure. Remote metadata remains
data, never Findings or policy; caller owns ActionResult/state ingestion.
No new domain/state/runner/dependency/CLI/workflow behavior or automatic router.
See [FTP contract](ftp-adapter.md) for exact fields, bounds, outcomes and exclusions.

## SMTP greeting/EHLO boundary (M4-T05)

**SMTP capability = greeting + safe ESMTP metadata only.** Current observed-Service/
registry/policy/scope/dedup/shared-budget gates precede one numeric connection.
Only a valid 220 greeting enables one fixed EHLO; strict bounded SMTP reply framing
stops before any auth/mail flow. No AUTH/credentials/brute force, MAIL FROM/RCPT TO/
DATA/BDAT, relay/mail sending, VRFY/EXPN enumeration, STARTTLS handshake or arbitrary
commands/options. smtps/465 reject before contact. Remote banner/extensions/AUTH
names/STARTTLS/SIZE are untrusted data, never authority, functionality tests or
vulnerability conclusions. Canonical failures/partial banner and provenance retain
limits. No client library/router/runtime changes. See [SMTP contract](smtp-adapter.md).

## Database pre-authentication metadata boundary (M4-T06)

DatabaseAdapter requires exact prior normalized Service/type/port and current
registry/policy/dedup/shared budgets; every subject and concrete address passes
ScopeValidator independently and rechecks before contact. MySQL/MariaDB sends zero
bytes; PostgreSQL sends only fixed SSLRequest and closes after one byte, without
TLS/StartupMessage/username/password/auth negotiation. Redis/MongoDB/ms-sql-s have
no approved profile: no contact/spending. Strict extra-forbid input excludes credentials,
connection strings, queries/commands/options. No data/schema/table/user/document
access, reads/writes, Redis/MongoDB command, files, mutation or exploitation exists.
Remote version/opaque offers remain bounded untrusted metadata with original Service/
caller provenance; unsupported/auth-required/partial behavior cannot escalate, add
contacts or infer vulnerabilities. See [database contract](database-adapter.md).

## Nuclei foundation boundary (M5-T01)

Every scan profile is denied, regardless of planner prose, binary availability or
action-policy acceptance. Strict semantic inputs cannot carry paths/flags/templates
or approval overrides. No scan ProcessSpec/runner call, template download/update,
OAST interaction or target contact exists. The only opt-in runner call is the
isolated bounded local version probe. Offline ingestion validates query and each
reported network location/IP centrally, rejects unmatched subjects and preserves
untrusted exact stream evidence; source references/paths/commands are never used.
Candidate verification stays unverified; no Finding or exploit conclusion exists.
Scope checks after capture cannot retroactively authorize scanner contact.
See [contract](nuclei-adapter.md) for limits and later-task enforcement ownership.

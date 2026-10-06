# Deterministic discovery (M2-T07)

M2 pipeline = deterministic integration proof.
M6/M7 = future AI planning/autonomous loop.

`orchestration.DiscoveryWorkflow` is an explicit library workflow over the six M2
capabilities. It imports no provider, produces no PlannerDecision and has no retry,
planning, chat, persistence, reporting or operational CLI. The CLI remains inert.
Imports and construction execute no reconnaissance or availability probes.

## Trusted composition

Supply an immutable ToolRegistry, ScopeValidator, one shared BudgetController,
ReconStateMachine, explicit ActionPolicyConfig and optionally an aware UTC clock.
The caller binds these services to the same session and owns their exclusive use
during a run. Production adapters must be detected/registered by trusted composition
according to their existing contracts. The workflow never installs/probes tools or
uses fallback capabilities. Its finite dispatch branches accept only the existing
M2 adapter classes; offline integration injects fake runners and a fake DNS resolver.

Call `await workflow.run(DiscoveryRequest(run_id=..., session_id=..., target=...))`.
Run/session IDs are bounded ASCII references; a run ID cannot be reused once it has
recorded requests. The initial target must be a supported DNS root. The method
rejects overlapping calls on the same workflow. This is single-owner sequential
coordination, not a general concurrent dispatcher or session startup/resume API.

Every selected action is an ActionRequest. Current ActionPolicyValidator checks
registry facts, scope, risk, registered schemas, real budget eligibility and real
ActionDeduplicator history. Eligible requests use atomic dedup admission. The
workflow records APPROVED, resolves the registered trusted adapter, and calls its
existing execute boundary. That boundary repeats current policy and independently
checks infrastructure/contacts, then reserves the same budget exactly once.

## Finite stage order and branching

1. `resolve_dns` queries the original root with the existing six-record default.
   Addresses and CNAME/MX/NS owners/destinations remain evidence only.
2. `enumerate_subdomains` requests passive root discovery. Successful/partial
   recorded action observations provide candidate names. Each name independently
   passes ScopeValidator. Rejected discoveries stay in original evidence and
   produce a policy audit record, without entering any executable action/batch.
3. `verify_dns` receives one sorted batch containing the canonical root and allowed
   discovered names, at most 64. Its existing default selects A records. Verification
   limitations, merged sections and wildcard uncertainty remain explicit.
4. `probe_http` receives that same name batch, using the existing HTTPS-root profile,
   operator numeric contact allowlist and independently scoped numeric resolver.
   It never follows redirects or promotes DNS answers into contact permissions.
5. `discover_ports` receives that same batch. Existing operator hostname bindings
   and finite TCP ranges govern numeric contacts; defaults remain 80/443. No binding
   is manufactured from DNS/HTTP data. A missing binding is a policy stop.
6. `fingerprint_services` receives one action per numeric address with recorded
   Naabu open TCP ports, in sorted order. Only completed/partial discover_ports
   ActionResults linked to the root's assets provide selections. Unrelated raw
   state facts and other sources cannot create selections. At most 64 addresses,
   128 ports/address and 128 evidence references/address are accepted. Empty port
   discovery schedules no Nmap work.

Candidate/selection overflow stops with canonical planner_validation_failed;
there is no silent truncation, pagination or extra discovery round. One run selects
at most five initial actions plus 64 fingerprint actions. Existing budgets can stop
it earlier. There is no wait-for-rate, retry or open-ended loop. DNS verification and
HTTP are evidence stages, not prerequisites proving permission or liveness: expected
tool failure does not suppress independent explicitly authorized port discovery.

Nmap's new `with_selections` makes a detached immutable adapter snapshot for the
same detected installation, runner, effective timeout/capture bounds and data path.
It preserves the existing no-Lua detection gate, without another version probe.
A fresh explicit immutable registry selects that snapshot; no registry is mutated.
The same budget ledger and dedup state remain in use, with identical capability
schemas/identities. Selection evidence grants no scope authority. Nmap rechecks
numeric contact scope and requested-port subset before execution.

## Lifecycle, atomic facts and evidence

Adapters accept an optional trusted `on_started` callback. After entering their
owned budget permit and before contact/setup, they invoke it once. The workflow
records STARTED with its execution ID; failure/malformed callback fails closed,
charges the attempt and releases concurrency as aborted, without contact. Omitting
the callback preserves existing adapter use. This seam fixes the integration gap
where marking STARTED before adapter revalidation would trigger real dedup denial.

`ReconStateMachine.record_action_result` now optionally ingests assets, hosts,
services and endpoints alongside terminal lifecycle, observations and evidence in
one validated atomic commit. Failed/timeout/rejected/cancelled results cannot ingest
subjects or successful observations. A bad fact/reference leaves the entire prior
snapshot unchanged, including the pending lifecycle; the workflow stops and exposes
that state for inspection. It never manufactures a tool failure to hide a state error.
Each stage uses a separate asset ID; semantic subject merging is outside M2-T07.

Successful `Success[DiscoveryReport]` returns detached state, normalized adapter
outputs, AuditEvents and skipped action IDs. `workflow.report` also exposes these
in-memory facts after a fatal Failure. Output envelopes are retained so memory
artifact references and hashes have inspectable normalized snapshots; no raw stdout,
filesystem persistence, native tracebacks, commands or remote text enter audit
summaries. Callers own retaining each report; a new run replaces report buffers.
Budget snapshots sample the shared ledger after each terminal execution.
AuditEvents remain non-authoritative in-memory records; no logger starts implicitly.
SESSION_COMPLETED means the finite workflow finished, including recorded partial or
failed branches, and does not claim every adapter succeeded or discovery was exhaustive.

## Failure and stop rules

| Condition | Action/state behavior | Workflow behavior |
| --- | --- | --- |
| Successful output | requested → approved → started → completed; atomic facts | Continue |
| Partial output | same start path → partial; original error and valid facts | Continue |
| Missing/unavailable tool before reservation | requested → rejected, original tool_unavailable, no execution ID | Continue independent stages |
| Timeout, parse/nonzero/execution failure after start | timeout/failed, original canonical error, no fabricated facts | Continue independent stages |
| Policy/scope/budget denial before start | requested/approved → rejected, original canonical error | Stop |
| Policy abort after reservation/final recheck | started → cancelled with canonical cancellation; original policy error in audit and returned Failure | Stop |
| Duplicate equivalent history | No admission, reservation or contact; report skip and policy audit | Continue |
| Zero discovery | Preserve adapter completed/partial distinction and evidence | Continue; no invented service/follow-up |
| Invalid transition/ingestion | Failed transition leaves prior snapshot intact | Stop with state_transition_invalid |
| Caller cancellation | cancelled result when transition is valid; adapter permit/runner cleanup | Propagate CancelledError; session audit |

ActionResult now permits exactly tool_unavailable as an additional pre-start
rejection reason. Other tool errors cannot be disguised as unstarted rejections.
This preserves the existing lifecycle matrix without fabricating STARTED for a
missing tool. Post-start policy abort uses existing cancellation semantics and
preserves the actual denial in the audit record/returned canonical Failure.

Duplicate classification consults existing typed dedup history after policy
validation. A skipped attempt is not added to request history, following the atomic
admission contract. A new run ID changes only identity references, never semantic
eligibility. There is no completed rerun override or automatic retry scheduling.

## Scope and validation limits

Name membership never authorizes IPs, aliases, redirects or newly discovered hosts.
All adapters keep their existing final contact checks, constrained numeric destinations,
no-follow configuration, charged host/rate/output limits and deadlines. Native DNS
checks every question/resolver exchange. Naabu bindings and HTTPX allowlists remain
operator inputs. Passive Subfinder's explicitly selected third-party service and
recursive resolver infrastructure retain the trust/containment limits in their
existing contracts; this workflow adds no stronger provider transport guarantee.
No new scanner capability, shell path, AI, live target test or dependency is added.

See [architecture](architecture.md), [state transitions](state-transitions.md),
[tool contracts](tool-contracts.md), [security model](security-model.md),
[testing](testing-strategy.md) and [ADR 0014](decisions/0014-deterministic-discovery.md).

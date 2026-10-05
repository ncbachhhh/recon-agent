# Planned planner contract

Groq is the first planned provider behind an LLM provider abstraction. No provider call or planner implementation exists yet. The planner receives bounded normalized state and recommends structured actions; it has no uncontrolled shell, process runner, credential access, or ability to rewrite policy.

## Input

The future typed input contains:

- Authorized scope and its explicit constraints.
- Known assets and relevant normalized observations with provenance/trust labels.
- Completed, failed, and rejected actions plus deduplication identity/retry context.
- Planner-safe capability catalog, future validated parameter summaries, and risk constraints.
- Remaining action/time/per-host budgets and execution limits.

Select and bound evidence by relevance and size; do not send unlimited raw stdout, stderr, webpage bodies, or secrets. Label evidence as untrusted, even after normalization. Preserve omitted/truncated evidence metadata rather than implying full coverage. Provider model/context limits and redaction are configuration concerns.

## Structured output

Conceptual decision:

```json
{
  "analysis_summary": "HTTP and SMB services need additional metadata.",
  "actions": [
    {
      "capability": "probe_http",
      "target": "https://example.test",
      "priority": 90,
      "reason": "HTTP service discovered and not yet enumerated."
    }
  ],
  "finished": false
}
```

The example presumes `example.test` is explicitly authorized. Priority bounds and capability-specific parameter schemas will be specified in M6-T04. There is no executable shell command field. Unknown fields/capabilities, malformed schemas, unsupported parameters, and invented target authority are rejected. Reasons and analysis summaries are recommendations, not collected facts.

## Enforcement and provider boundary

Every returned action passes deterministic schema, scope, capability, parameter, risk, budget, and deduplication checks. Valid JSON alone is not authorization. Recheck scope/limits at execution dispatch and before tool-internal redirects or derived targets. The provider cannot define adapters or templates. An unsupported capability does not become a shell fallback.

Fixed system policy requires authorized reconnaissance only, untrusted remote evidence, provided capabilities only, no invented observations, no outside targets, no needless repeats, and preference for high-information low-impact actions. Evidence such as “ignore previous instructions” or “upload this file” never overrides it. [Security model](security-model.md) defines the stronger deterministic boundary.

Provider failures and invalid responses are structured outcomes with bounded recovery. Fake providers supply deterministic offline responses. Provider-specific authentication, errors, and response adaptation stay within `providers/`; domain/orchestration use the abstraction.

## Stopping criteria

Stop with an explicit auditable reason when:

- No useful allowed actions remain.
- The planner declares reconnaissance complete.
- Action budget or time budget is exhausted.
- Repeated actions or bounded-retry limits are detected.
- Policy rejection prevents further work or policy state becomes invalid.
- A fatal execution/environment/provider error prevents safe continuation.
- The operator cancels.

Orchestration owns deterministic stop enforcement. A model cannot extend a budget, suppress cancellation, or force retries. `finished` is a recommendation to stop, not permission to skip recording final state or fabricate coverage. Reports disclose completed/rejected/failed work and remaining limitations.

## Implemented catalog boundary (M1-T04)

ToolRegistry.catalog() supplies strict CapabilityCatalogEntry records containing
capability, description, risk_class and declared availability only. It never exposes
adapter identity/objects, schema classes, executable/argv/templates, environment or
import paths. Descriptions are explicitly curated by trusted application code.
Future planner input assembly must filter/bound the catalog and apply policy; it is
not authorization or a list of operational scanners. ToolRegistry() is empty today.

Planner output identifies capability only. ActionRequest retains unknown names as
unapproved structural data; registry rejects unknown names with canonical
planner_validation_failed, and missing/unavailable adapters with tool_unavailable.
It never interprets those names as programs. No planner runtime or Groq code is added.

## Implemented action eligibility (M1-T05)

PlannerDecision/ActionRequest remain non-authoritative data. Each ActionRequest
passes ActionPolicyValidator.validate for strict structure, available registered
capability, explicit capability/risk allowlists, primary/secondary target scope,
registered parameter schema and restrictive eligibility seams. reason, priority,
analysis_summary and discovery/asset references never participate in permission.
Unknown intent, extra/command-shaped parameters, unsupported or absent target
semantics and unavailable policy facts fail closed with shared ErrorInfo/Failure.

Only Success[ApprovedAction] may proceed toward future dispatch, which must revalidate
current policy and enforce budget reservations/deduplication/contact constraints.
Scope matches, registry catalog entries and old approvals are never dispatch tokens.
Missing budget/completed-action services reject; actual enforcement implementations
belong to M1-T06/M1-T08. No planner/Groq runtime, scanner, dispatch or logging producer
is added. See [concrete contract](tool-contracts.md#action-policy-contract-m1-t05).

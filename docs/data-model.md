# Planned data model

Pydantic typed models are planned; there are no runtime schemas yet. Exact fields/storage keys are future design work. Domain models remain independent of subprocesses, providers, and SQLite.

## Entities

| Entity | Meaning and planned relationships |
| --- | --- |
| ReconSession | Run identity, lifecycle, configuration/scope snapshot, timestamps, budgets, stop reason; owns state and action history |
| Scope | Explicit authorized domain/subdomain/IP/CIDR/URL policy and exclusions; attached to a session; discovered assets do not expand it |
| Target | Operator-requested starting subject; must validate against session Scope |
| Asset | Canonical identified subject with provenance and scope/actionability status; may represent a Host or web resource |
| Host | Domain/IP host identity and resolution context; has Services; resolution is evidence, not blanket authorization |
| Service | Asset/host plus port, transport, protocol, optional product/version metadata and supporting observations |
| Endpoint | Canonical URL/path/method identity associated with an asset/service; discovered redirects/hosts require revalidation |
| Observation | Collected fact or bounded tool-reported fact with kind, timestamp, asset reference, source, and Evidence references |
| Evidence | Traceable source material/reference with origin, collection time, execution/source ID, trust label, integrity/retention metadata, and truncation/redaction limits |
| ActionRequest | Typed requested capability, target, permitted parameters, reason/priority, source decision, and canonical dedup identity |
| Action | Lifecycle record for an ActionRequest: requested, validated/rejected, running, completed/failed/cancelled, with policy outcomes |
| ActionResult | Structured outcome, observations/evidence, errors, timing and ToolExecution references; not merely a boolean |
| ToolExecution | Adapter/binary/version, safe argv metadata, timing, exit status, timeout/cancel/truncation flags, bounded output references |
| Finding | Interpreted security-relevant conclusion, severity/confidence/source attribution, affected assets, and supporting Evidence/Observations |
| PlannerDecision | Provider recommendation, selected input references, summary/actions, provider/model metadata, validation outcomes; never a scanner fact |
| ReconState | Session aggregate of assets, observations, findings, evidence, action outcomes, decisions, and remaining budgets |

## Semantic distinctions

**Observation = collected fact.** A scanner reporting a product or version records what it observed; certainty/limitations and provenance remain explicit.

**Finding = interpreted security-relevant conclusion.** It must cite evidence and disclose inference rather than pretending the model confirmed exploitation.

**Evidence = traceable source supporting an observation/finding.** Raw remote content remains untrusted, even if stored or normalized. References must remain resolvable in reports and resume.

**PlannerDecision = recommendation, not fact.** A model's proposed next action or suspected issue cannot be inserted as a collected observation.

## Relationships and invariants

A session owns a scope snapshot and starting targets. Targets lead to assets/hosts; hosts expose services; web services expose endpoints. Actions reference session, target/asset, capability, and optional planner decision. Tool executions reference actions; evidence references executions or explicit collection sources; observations link evidence and assets; findings link supporting observations/evidence. Decisions reference bounded input state and policy outcomes. ReconState aggregates these with remaining budgets.

Identifiers and canonicalization must preserve lineage while preventing duplicate actions/assets/findings. Rejection or failure must not create successful observations. State mutation and budget reservation are controlled transitions, eventually safe under concurrency. Resume validates policy changes and does not erase earlier evidence/history. Storage interfaces and migrations are planned in M8, not implemented here.

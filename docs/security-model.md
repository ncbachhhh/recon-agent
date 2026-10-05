# Security model

Status: mandatory architectural constraints and mostly planned controls; M0-T03 implements strict configuration validation and separate redacted credentials. No operational reconnaissance code exists. The platform is for systems the operator is explicitly authorized to assess. Authorization is an input requirement, not something inferred from public reachability or discovered data.

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

M0-T03 rejects unknown keys and invalid effective types/limits in trusted configuration. The explicit loader performs no runtime startup. Scope preferences contain no targets or authorization grants; enabling tools/planner/persistence only sets preferences. `GROQ_API_KEY` is loaded separately into an excluded `SecretStr` field, never ordinary configuration or diagnostic dumps. Displayed validation errors hide raw inputs; diagnostic callers of Pydantic structured errors must omit input values. No arbitrary commands, argv or policy-bypass options exist. See [configuration](configuration.md) for sources, precedence and failure behavior. These contracts do not implement scope enforcement, capability policy, budgets, logging or provider communication.

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

A domain resolving to an address is evidence, not unlimited IP authorization. M1-T01 must specify resolution/IP policy and revalidation against address changes. Tools must not bypass scope via their own recursion, redirect following, secondary lookup targets, or automatic feature discovery. Disable unsafe implicit behavior or reject execution when the adapter cannot constrain it. A post-scan filter cannot undo an out-of-scope network request.

If scope cannot be established reliably, **do not execute the action**. Malformed targets, ambiguous parsing, unresolved policy semantics, unsupported tool behavior, and missing authorization are fail-closed cases. Record the rejection with enough evidence to explain it without leaking secrets.

## Controlled execution and resource limits

Every executable operation maps to a registered capability and controlled adapter. The planner cannot supply executable paths, arbitrary arguments, shell strings, environment variables, or template paths. Adapters validate options and use argument arrays, guarding against option injection as well as shell injection. The runner uses no shell and supports timeouts, exit status, stdout/stderr capture, cancellation, process cleanup, bounded output, and audit metadata.

Enforce session action/time budgets, max concurrency, per-host limits, per-tool rate limits, crawl/content limits, and output-size caps. Reserve/check budgets atomically for concurrent work, recheck at dispatch, and stop retries when limits are reached. Exhaustion, cancellation, or timeout is an explicit recorded result. A failure does not justify a more intrusive fallback.

Template execution requires named reviewed policy profiles; deny unknown, unreviewed, or potentially intrusive templates in the default profile. Tool defaults and updates must not silently widen effective behavior.

## Evidence, logging, and lifecycle

Keep observations distinct from interpreted findings and planner recommendations. Link each fact/finding to evidence and an execution or collection source. Sanitize fixtures, escape terminal/HTML control content, and redact secrets in logging/reporting. Store only required evidence; retention and access policy are future configuration decisions.

Rejections, planner decisions, execution outcomes, and lifecycle events must be auditable. Resume revalidates current policy, remaining budgets, and completed-action identity. Repeated failures cannot lead to endless retries. Fatal policy/environment errors, lack of useful allowed actions, completion, budgets, time, or operator cancellation stop execution safely.

## Verification obligations

Offline tests use fake providers/runners and sanitized fixture output. Scope regression/property tests cover domain confusion, IPv4/IPv6/CIDRs, malformed URLs, and redirect/address changes. Prompt-injection tests assert both rejection and absence of execution. Concurrency tests assert atomic budget and scope enforcement. CI never silently contacts public targets. Real integration or lab testing requires explicit authorization and opt-in targets.

Document controls as planned until implementation and test evidence support them. M13 security review reconciles this document with code before MVP declaration.

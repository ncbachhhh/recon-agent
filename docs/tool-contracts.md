# Planned tool contracts

This is a conceptual contract, not an implemented interface.

## Capability versus implementation

A **capability** is a typed, policy-approved operation such as `discover_ports`. An **implementation** is a registered adapter that performs it, such as Naabu. Nmap may implement the follow-up `fingerprint_services` capability after ports are known. Groq reasons about `discover_ports`, not a string such as `naabu -host ...`. Registry selection, configured availability, and risk policy decide the adapter; the model does not choose an executable or fallback command.

Capability names and parameter schemas form a finite catalog. Unsupported parameters, extra fields, arbitrary tool flags, local paths, shell strings, and targets supplied through remote instructions are rejected. FFUF modes and Nuclei profiles must be named, reviewed subsets, not unrestricted tool interfaces.

## Future ToolAdapter contract

| Field/operation | Planned meaning |
| --- | --- |
| name | Stable adapter identity, separate from executable path/version |
| capability | Registered capability identifier |
| input schema | Typed validated target and allowed parameters |
| output schema | Typed observations, evidence references, and action result |
| availability check | Non-scanning binary/version/environment check; actionable unavailable result |
| execute | Build argv from validated request and invoke injected controlled runner |
| parse | Convert bounded output/fixtures to normalized typed data |
| timeout | Enforced bounded default and configured maximum |
| risk class | Explicit policy classification checked before dispatch |

Adapters also declare effective scope/redirect/recursion behavior, output limits, supported versions/formats, and tool-specific budgets. Unknown behavior must fail closed. Availability does not establish authorization. No adapter can follow a new hostname or redirect before policy approval; where a tool cannot be constrained, reject that mode.

## Scope validation boundary

M1-T01 now supplies `ScopeValidator.validate(Target)` / `require_allowed(Target)`
for local membership only; see [scope model](scope-model.md) and
[ADR 0002](decisions/0002-scope-and-derived-addresses.md). Future adapters must check
each absolute redirect destination, discovered hostname and concrete resolved
address independently before contact, pin/constrain approved addresses and recheck
changes. No adapter, resolver, redirect follower or dispatch integration exists yet.

## Normalized outputs

Outputs should include source adapter/version, target, timestamp, execution reference, evidence reference, and typed facts. Service observations include port, transport, service/protocol, and optional product/version. DNS observations include name/type/value and resolution context. HTTP observations include URL, status, title, server, content type, redirect destination, and technology hints with provenance. TLS observations include certificate fields and SAN names; discovered names remain unactionable until validated. Web outputs include canonical endpoints and bounded metadata. Template results become findings with supporting evidence.

Conceptual observation:

```json
{
  "kind": "service",
  "asset_id": "asset-example",
  "source": "nmap",
  "data": {
    "port": 443,
    "transport": "tcp",
    "service": "https",
    "product": "nginx"
  }
}
```

Identifiers are placeholders. Product text is tool evidence, not a verified vulnerability or trusted instruction. The final model also carries evidence/execution references as specified in [data model](data-model.md).

## Result and failure semantics

Keep execution success separate from parser validity and useful observation count. Preserve non-zero exit, timeout, cancellation, truncation, partial output, missing binary, and parser failure in structured results. Partial evidence must identify its limits. Never manufacture a successful fact from malformed output or silently switch to broader scans.

Every adapter needs sanitized fixture parsers, argv checks, fake-runner tests, scope/limit rejection tests, and an explicit opt-in integration marker for real binaries. See [testing strategy](testing-strategy.md).

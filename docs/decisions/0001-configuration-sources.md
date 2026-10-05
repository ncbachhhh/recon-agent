# Explicit TOML configuration and separate credentials

ADR 0001 — Configuration sources

## Status

Accepted

## Date

2026-10-05

## Context

M0-T03 requires Pydantic section contracts, deterministic source precedence,
offline loading and separate secrets. M0-T01 left format/discovery undecided;
M0-T02 established Python >=3.12 with no runtime dependencies.

## Decision

Use Pydantic 2 for strict models, unknown-key rejection and diagnostic
serialization. Use standard-library `tomllib` for one explicitly selected file;
no discovery, includes or dotenv. Centralize recursive merging in one loader:
defaults < file < namespaced environment < explicit programmatic overrides.
`RECON_AGENT_SECTION__FIELD` maps only real section fields; typed non-string
environment values use JSON syntax. Validate effective settings after merging.

Load `GROQ_API_KEY` only through a separate provider-secret loader into a
`SecretStr` field excluded from repr and standard dumps. Neither loader starts
subsystems. Scope configuration contains preferences, never target grants.

## Alternatives Considered

- `pydantic-settings`: useful for broader source/discovery needs, but unnecessary
  for these explicit sources; an additional dependency would duplicate the small
  loader's parsing/merging contract.
- YAML: adds a parser dependency without a current requirement.
- Automatic configuration discovery/dotenv: introduces implicit machine state
  and credential/file ambiguity contrary to this foundation's explicit inputs.

## Consequences

Only Pydantic is added as a direct runtime dependency. The loader owns source
parsing/merging and tests. Paths remain relative when supplied as relative paths;
loading never expands or creates them. Model catalog validation is deferred;
operators must select a model before enabling the future planner.

## Security Impact

Strict validation rejects permissive coercion and typos. Secrets stay outside
ordinary settings. No configurable command surface or scope authorization exists.
Future operational consumers still require policy, scope and budget enforcement.

## Testing Impact

Offline tests inject complete environment mappings and temporary files, exercising
precedence, malformed/unknown settings, secret exclusion and side-effect boundaries.

## Follow-up

M0-T04 domain models and M1 scope enforcement remain deferred. Provider, adapter,
persistence and CLI tasks may extend contracts within their own scopes. See the
[configuration reference](../configuration.md) and [roadmap](../../PLAN.md).

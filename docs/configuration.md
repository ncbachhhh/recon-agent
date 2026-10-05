# Configuration

M0-T03 implements typed configuration contracts and explicit local loading in
`recon_agent.core.config`. These settings do not operate the planned subsystems.
The console entry point remains the inert M0-T02 placeholder.

## Application API and sources

```python
from recon_agent.core.config import load_config, load_provider_secrets

defaults = load_config(environ={})
config = load_config(
    "config.example.toml",
    environ={"RECON_AGENT_EXECUTION__MAX_CONCURRENCY": "3"},
    overrides={"execution": {"max_concurrency": 4}},
)
assert config.execution.max_concurrency == 4
secrets = load_provider_secrets(environ={})  # No credential is required.
diagnostics = config.model_dump(mode="json")
```

Sources, from lowest to highest priority:

1. Built-in model defaults.
2. One explicitly supplied TOML file.
3. Environment variables in the `RECON_AGENT_` namespace.
4. Explicit programmatic `overrides` mapping.

Nested section dictionaries merge; scalar/list values replace earlier values.
Validation applies to the effective merged configuration. A later valid value can
replace an earlier invalid field value; unknown keys that remain in the effective
configuration are rejected. Malformed TOML and malformed/unknown namespaced
environment settings always fail during source parsing, even with later overrides.
No source mapping is mutated, and every call constructs a new configuration.

Omitting `environ` snapshots the current process environment at the explicit
loading call. Supplying a mapping replaces that environment source entirely;
`environ={}` makes defaults/file/overrides independent of machine settings.
Identical file contents, environment and overrides produce identical settings.
There is no cached configuration or implicit file discovery, parent-directory
traversal, includes, `.env` loading, tilde expansion or environment interpolation.

## Typed sections and defaults

`AppConfig` composes Pydantic models for all seven sections. Unknown keys are
forbidden at every level. Python/TOML inputs require their actual field types:
booleans and numeric strings cannot stand in for integers; finite integer or
float seconds are accepted. Paths accept `Path` objects or non-blank strings
without NUL characters. JSON diagnostic serialization represents paths as strings.

| Section | Fields and defaults | Validation / meaning |
| --- | --- | --- |
| `scope` | `allow_subdomains=false`, `allow_private_ips=false` | Boolean preferences only; contains no targets or authorization grants |
| `execution` | `default_timeout_seconds=30.0`, `max_concurrency=1`, `max_output_bytes=1048576`, `max_actions=100`, `max_duration_seconds=600.0` | Positive finite seconds; positive integer counts/bytes; default timeout must fit within the session duration |
| `planner` | `enabled=false`, `provider="groq"`, `model=""`, `max_iterations=10` | Only planned provider `groq`; positive iteration limit; enabled planner requires a non-blank model identifier |
| `tools` | `enabled=false` | Boolean adapter enablement preference; no command, arguments or executable paths |
| `persistence` | `enabled=false`, `database_path="recon-agent.sqlite3"` | Local path contract for planned SQLite persistence; no file is created |
| `logging` | `level="INFO"`, `structured=true` | Exact supported levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `reporting` | `output_directory="reports"`, `default_formats=["json"]` | Non-empty unique list drawn from `json`, `terminal`, `html`; no reports are generated |

The defaults disable planner, external tools and persistence. No model identifier
is chosen from a changing online catalog: the operator supplies a string when
enabling the future planner. Positive execution budgets establish future bounded
session contracts, without implementing enforcement. The timeout/budget relation
ensures a default operation can fit in the configured session time envelope.
There are no arbitrary upper bounds unrelated to architecture.

Scope preferences never establish authorization, including when set to `true`.
Missing scope cannot grant permission: this configuration contains no target
scope at all. Explicit authorization and target rules belong to future domain and
M1 scope-engine work. Tool paths, tool-specific limits, provider retry/evidence
limits and policy profiles remain deferred to their owning tasks. Future adapters
own executable selection and argv construction; configuration cannot supply
arbitrary commands or bypass capability policy.

## TOML file

Python's standard-library `tomllib` reads one path passed to `load_config`.
The top-level keys are the seven section names; each section is a TOML table.
See [config.example.toml](../config.example.toml) for all implemented fields with
conservative defaults and no credentials. It is not loaded automatically.

```toml
[execution]
max_concurrency = 2

[logging]
level = "WARNING"
```

Persistence/report paths remain relative when supplied as relative paths. Loading
does not resolve them, check existence or create anything; future consumers must
define their operational use relative to the working directory. An explicitly
supplied relative configuration-file path is opened relative to the caller's
working directory. No path is silently interpreted relative to the TOML file.

## Environment convention

Use `RECON_AGENT_<SECTION>__<FIELD>`: a double underscore separates the section
from its field. Uppercase is the documented convention; suffixes are matched
case-insensitively. The prefix is case-sensitive. Duplicate names resolving to
the same field are rejected. Only fields listed above are supported; any unknown
or structurally incorrect variable with the exact prefix fails rather than being
ignored. Other environment variables do not affect ordinary configuration.

String fields (including paths, provider/model, log level) use their raw value,
without JSON quoting. Boolean, number and list fields use JSON syntax, followed
by the same strict model validation:

```text
RECON_AGENT_EXECUTION__MAX_CONCURRENCY=8
RECON_AGENT_EXECUTION__DEFAULT_TIMEOUT_SECONDS=15.5
RECON_AGENT_PLANNER__ENABLED=false
RECON_AGENT_LOGGING__LEVEL=WARNING
RECON_AGENT_REPORTING__DEFAULT_FORMATS=["json","html"]
```

Booleans accept `true`/`false`, not `yes`, `1`, or arbitrary non-empty strings.
Integer fields reject fractions and quoted numbers. Invalid values fail;
configuration does not silently coerce permissive security settings.

## Secrets and diagnostics

`GROQ_API_KEY` is read only by the separate explicit `load_provider_secrets` call.
It returns `ProviderSecrets`; an absent/empty value means no credential. No real
key is required, checked against a service, or included in normal configuration.
Credential fields in TOML, ordinary overrides or the `RECON_AGENT_` namespace
are unknown settings and rejected.

The separate credential field uses Pydantic `SecretStr`, is omitted from normal
object repr and excluded from `model_dump`/`model_dump_json`, even when requested
via `include`. `str`/`repr` of the secret wrapper redact its value. Only a future
provider consumer deliberately calling `get_secret_value()` can retrieve it.
Never log that result, send it as evidence, or commit it. No `.env` file or API
key example is provided.

`AppConfig.model_dump(mode="json")` / `model_dump_json()` provide non-secret
diagnostics. Displayed validation errors hide input values. Pydantic's structured
`errors()` method includes raw inputs by default; diagnostic consumers must use
`errors(include_input=False)` and must not log raw source mappings or exception
internals. These protections concern modeled credentials, not arbitrary sensitive
text an operator might place in ordinary string settings.

## Failures and side effects

M0-T05 normalizes explicit loading failures into
`recon_agent.core.errors.ConfigurationError` with stable code
`configuration_invalid`. The temporary `ConfigLoadError` is removed.

- Missing/unreadable files and invalid file paths fail with source `file`;
  they are never treated as defaults.
- Malformed TOML/invalid UTF-8 fails with source `file` and a fixed message.
- Unknown/malformed environment settings fail with source `environment`, without
  copying variable names or values into the diagnostic contract.
- Invalid effective fields, wrong section structures, unsupported values, typos
  such as `max_concurency`, and unknown keys fail with source `validation`.

Native OSError/TOML/Unicode/JSON/Pydantic causes remain explicitly chained for
inspection. Normal exception str/repr and `to_error_info()` omit those causes and
raw configuration. Complete chained tracebacks/native structured errors may
contain source material; they are not safe diagnostic dumps. Direct AppConfig or
section-model construction still raises Pydantic ValidationError. See
[error/result contracts](error-model.md) for the boundary and context API.

Application settings and credentials are read only by explicit loader calls; imports define
models without application startup. Normal dependency imports may inspect
installed-package metadata. Explicit loading reads only
the supplied file and environment snapshot: no network, tool discovery/execution,
Groq client, database initialization, directory creation, logging configuration,
report generation or autonomous activity occurs, even with enabled preferences.

## Implementation boundary and validation

Pydantic is the sole direct runtime dependency, used for strict models, nested
validation, serialization and the secret wrapper. `tomllib`, `json` and the explicit
merge loader avoid a settings framework or YAML dependency. No provider, scanner
or persistence dependency is installed by this task.

Run focused offline checks with:

```bash
.venv/bin/python -m pytest tests/unit/test_config.py
```

Tests isolate environment sources and cover defaults, all sections, precedence,
strict/unknown settings, file failures, secret exclusion, diagnostics and absence
of runtime filesystem/logging side effects. See [testing strategy](testing-strategy.md)
for mandatory complete validation. Domain data models now exist (M0-T04);
scope enforcement,
process runners/adapters, Groq, AI planning, database persistence,
operational reports and real CLI commands remain unimplemented. M0-T06 explicitly
consumes LoggingConfig level/structured through configure_logging; loading settings
still configures no handlers. See [logging and audit](logging-and-audit.md).

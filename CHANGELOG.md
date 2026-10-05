# Changelog

## Unreleased

### Project infrastructure

- Bootstrapped repository governance, complete implementation roadmap, maintenance skill, architecture/security/contracts documentation, and inert Python package/test directories.
- Established Python >=3.12 setuptools packaging, zero runtime dependencies, a development extra for Ruff/Mypy/Pytest/coverage/build, offline test selection, generated-file ignore rules, and validated development documentation.
- Added an inert `recon-agent` console entry point that prints foundation status; no reconnaissance or Groq functionality is implemented.
- Added strict Pydantic configuration sections, explicit TOML/environment/programmatic loading, deterministic precedence, separate excluded/redacted provider credentials, offline tests and a safe configuration example. No operational subsystems are started.
- Added pure typed domain declarations, subjects, provenance/fact records, safe capability-intent/planner contracts and session/state containers, with offline validation/serialization tests. Operational policy, execution and state transitions remain deferred.

# Planned configuration

No loader, file format, or working configuration exists. M0-T03 will implement typed Pydantic sections and decide/document file discovery and precedence. Intended strategy: validated defaults → explicitly selected file → allowed environment overrides. Secrets remain separate from ordinary serializable configuration. Missing/ambiguous scope fails closed; examples are not scan authorization.

| Category | Planned controls |
| --- | --- |
| scope | Explicit domains/subdomain grants, IPs/CIDRs, URL rules, exclusions, authorization context, redirect/resolution policy |
| execution | Timeouts, cancellation, max concurrency, bounded stdout/stderr, process controls |
| budgets | Session action/time limits, per-host request limits, retry limits, output caps |
| tools | Explicit trusted binary paths, adapter enablement/availability, supported capabilities |
| tool-specific limits | Port ranges, crawl depth/URL count, content wordlists/modes/rates, named reviewed Nuclei profiles |
| planner | Provider/model, bounded input size, priorities, decision/retry limits; no policy overrides |
| Groq provider | API key via secret mechanism, client timeout, bounded provider retries, model selection |
| persistence | Local SQLite path, schema version, retention and evidence reference handling |
| reporting | JSON/terminal/HTML destinations, redaction, evidence inclusion and AI attribution |
| logging | Structured levels/destinations, audit events, secret redaction, output limits |

## Secrets and environment

Proposed secret environment variable: `GROQ_API_KEY`. Its value must never be committed, printed, embedded in examples, stored in normal configuration snapshots, passed to remote tools, or sent as planner evidence. A future doctor command may show presence/absence only. Fake providers and default tests must run without it.

Other environment variable names, file format, config discovery, and tool paths are intentionally deferred to implementation/ADRs. Overrides must pass the same typed validation and cannot enable forbidden capabilities or enlarge scope via planner output. No actual credentials or `.env` files are supplied.

## Operator workflow intent

Operators explicitly establish authorization/scope and bounded execution settings before running a session. Configuration validation reports errors without starting scans. A session captures safe effective policy/configuration for audit/resume, excluding secrets. Resuming with changed settings requires revalidation. Binaries are detected, not silently installed; installation/environment guidance is planned in M12.

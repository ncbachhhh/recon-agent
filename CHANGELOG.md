# Changelog

## Unreleased

- M5-T01: add a disabled Nuclei adapter foundation with strict profile inputs,
  explicit isolated availability checks and bounded offline candidate ingestion.
  Preserve exact untrusted stream evidence and source links; all scans remain
  denied pending M5-T02/T03. No Finding creation, dependency or external setup.

- M4-T07: offline protocol selection matrix covering documented aliases, all families,
  port independence, product/version noise, exact conflicts, unknown/malformed data
  and runtime isolation. Real adapters with fake collectors verify policy/budget/
  availability/profile denials and supported collection; unsupported databases remain
  unavailable. No production change; M4 complete, M5-T01 ready only.

- M4-T06: scoped native database inspect_protocol with typed observed Service/type/
  port bindings, receive-only MySQL/MariaDB version metadata and fixed PostgreSQL
  SSL support signal (version unavailable/partial). Generic untrusted observations/
  evidence, canonical failures and offline regressions; Redis/MongoDB/SQL Server
  reject without contact. No credentials/auth/queries/data/mutation/client API.

- M4-T05: native SMTP inspect_protocol greeting/fixed EHLO under prior Service/
  numeric bindings and current policy/scope/dedup/shared budgets. Generic untrusted
  ESMTP extensions/STARTTLS/AUTH mechanisms/SIZE/provenance with canonical partial
  banner/failures. No auth/credentials/mail/relay/enumeration/arbitrary commands,
  implicit SMTPS or TLS negotiation; no later protocol implementation.

- M4-T04: native FTP-only inspect_protocol greeting/FEAT metadata with prior Service
  bindings, current policy/scope/dedup/shared budgets and bounded native transport.
  Untrusted banner/product hints/features/TLS advertisement and generic provenance/
  canonical partial failures. No authentication (including anonymous), credentials,
  files/data connections/arbitrary commands or TLS negotiation.

- M4-T03: native SMB-only inspect_protocol through one fixed bounded SMB2 NEGOTIATE
  behind current observed-service/policy/scope/dedup/shared budgets. Reported dialect/
  signing/GUID metadata and generic untrusted provenance/canonical failures; no
  authentication, shares/files/commands/fallback or later protocol implementation.

- M4-T02: native SSH-only inspect_protocol identification metadata from trusted
  observed-service/numeric bindings behind current policy/scope/dedup/shared budgets.
  Receive-only bounded greeting profile sends zero application bytes; generic
  untrusted observations/evidence and canonical partial/failure outcomes. No auth,
  credentials, commands, KEX/host-key/algorithm negotiation or later protocols.

- M4-T01: finite protocol family contracts under inspect_protocol, deterministic
  normalized TCP Service relevance, conservative unknown/conflict rejection and
  strict semantic request/metadata provenance schemas. Separate known contracts
  from operational registry availability; offline tests/docs, no protocol adapters
  or execution. Only M4-T02 becomes ready.

- M3-T06: shared conservative HTTP(S) URL/method/Host identity, deterministic
  evidence-preserving web discovery/contact state lookup, and existing web action
  alias dedup before dispatch. Precise query/encoding/authority rules, offline tests
  and docs; no new scanner or runtime capability. M3 complete; M4-T01 ready only.

- M3-T05: explicit specialized FFUF 2.1.0 vhost_names HEAD discovery as a trusted
  discover_content alternative. Scoped numeric contacts/operator suffix, fixed small
  wordlist, bounded retry-aware requests/rate/concurrency/deadlines/output, generic
  endpoint/observations/untrusted evidence and canonical failures. Offline tests/docs;
  no raw flags/files/templates, credential attacks, automatic Ferox duplication or
  later runtime capability.

- M3-T04: discover_content through detected Linux Feroxbuster 2.13.1, a reviewed
  four-path wordlist and finite adapter-owned numeric directory recursion; scoped
  contacts, explicit request/startup/rate/depth/thread/time/output bounds and generic
  endpoint/untrusted evidence. Hostname/ambient-config modes fail closed; planner
  inputs remain empty. Offline tests/docs; no FFUF or later runtime capability.

- M3-T03: crawl_web through detected Linux Katana 1.8.0, depth-zero extraction and
  a bounded independently scoped numeric same-origin GET graph. Generic untrusted
  URL/method/form/JS evidence; no redirect/form/JS endpoint contact or hostname mode.
  Adapter-owned child cwd isolates relative cleanup; no shell/planner flags or later task.

- M3-T02: inspect_tls through detected Linux TLSX 1.4.0, fixed native profile,
  independently scoped numeric contacts/original SNI and shared bounded runner
  execution. Normalize certificate/protocol metadata and partial handshake failures
  into untrusted generic observations/evidence; CN/SANs grant no authority/contact.
  Offline fixtures/fakes, tests/docs; no runtime dependency or later M3 capability.

- M3-T01: fixed inspect_common_files capability for robots.txt, sitemap.xml and
  .well-known/security.txt; native bounded HTTP via h11 with independently scoped
  numeric contacts/redirects, safe XML/directive metadata and untrusted provenance.
  Offline transports/streams cover errors, limits and state/dedup. No crawling,
  fuzzing, TLSX, planner/loop or operational CLI.

- M2-T07: finite deterministic DNS/subdomain/verification/HTTP/port/service workflow,
  real policy/budget/dedup integration, atomic ReconState results and in-memory audit/
  evidence reports. Adapter start notifications and immutable Nmap discovery snapshots
  preserve existing scope/contact/profile limits. No AI or autonomous loop.


- Added fingerprint_services through detected NSE-free Nmap 7.95, trusted prior-discovery selections, required bounded TCP ports, independently scoped numeric contact, fixed native version/XML profile and safe generic Service/Observation/Evidence. Offline fixtures cover containment, hostile XML, provenance and canonical failures; no live compatibility or pipeline is claimed.

- Added discover_ports through trusted Naabu 2.3.5: operator finite TCP ranges, independently scoped numeric hostname bindings, fixed isolated CONNECT stream argv, existing policy/budget/runner limits and generic Host/Service/Observation/Evidence. Offline fixtures/fakes cover partial/failure/security limits; no DNS expansion, arbitrary planner flags or Nmap fingerprinting.

- Added probe_http through trusted HTTPX 1.9.0: independently scoped candidate/address/resolver checks, fixed isolated shell-free probing with no redirects or scheme fallback, normalized Endpoint/HTTP observations/untrusted evidence and canonical partial/failure limits. Offline fixtures/fakes require no HTTPX/network; technology and redirects grant no authority.

- Added verify_dns through trusted DNSX 1.2.2 composition: scope-safe bounded candidate batches, independently authorized resolver, fixed shell-free argv, isolated child configuration, generic DNS evidence with actual RR owners/TTL/provenance and explicit ambiguity/partial failures. Deterministic fixtures/fakes require no DNSX/network; discovery/resolution grants no authorization.

- Implemented enumerate_subdomains through a trusted Subfinder adapter with explicit local availability/version detection, fixed credential-free passive source, isolated child configuration, adapter-owned argv, current scope/policy/budget checks, deterministic generic observations/evidence and canonical failures. Offline fixtures/fakes and runner environment regressions require no Subfinder/network. Discovery grants no authority; DNSX verification is implemented separately in M2-T03.

- Implemented resolve_dns through an explicitly registered native dnspython adapter with strict record-type input, current policy/scope/resources, independently authorized numeric resolver infrastructure, bounded UDP exchanges, typed DNS observations/evidence and structured failures. Offline fixtures cover A/AAAA/CNAME/MX/NS/TXT, negative/alias/malformed responses, cancellation and resource limits. Discovery grants no authorization; DNSX verification is implemented separately; later capabilities remain unimplemented.

### Project infrastructure

- Bootstrapped repository governance, complete implementation roadmap, maintenance skill, architecture/security/contracts documentation, and inert Python package/test directories.
- Established Python >=3.12 setuptools packaging, zero runtime dependencies, a development extra for Ruff/Mypy/Pytest/coverage/build, offline test selection, generated-file ignore rules, and validated development documentation.
- Added an inert `recon-agent` console entry point that prints foundation status; no reconnaissance or Groq functionality is implemented.
- Added strict Pydantic configuration sections, explicit TOML/environment/programmatic loading, deterministic precedence, separate excluded/redacted provider credentials, offline tests and a safe configuration example. No operational subsystems are started.
- Added pure typed domain declarations, subjects, provenance/fact records, safe capability-intent/planner contracts and session/state containers, with offline validation/serialization tests. Operational policy, execution and state transitions remain deferred.
- Added stable project error codes/hierarchy, bounded typed diagnostic context, serializable ErrorInfo and generic success/failure outcomes; configuration loading now raises ConfigurationError and ActionResult uses shared structured errors. No logging, retries or operational behavior is implemented.
- Added explicit project-local standard-library logging, human/JSON formatting, strict UTC/correlated autonomous recon audit records, bounded context redaction and safe ErrorInfo emission. Imports and domain constructors remain inert; no remote telemetry, persistent sink, private reasoning or future event producers are implemented.
- Added pure deterministic ScopeValidator with canonical matched declarations, typed scope rejection reasons, domain/hostname/subdomain/IP/CIDR/URL membership, exclusion precedence and explicit private-address gating. Redirect/discovered destinations require independent validation; no DNS, network, execution or automatic scope expansion exists.
- Hardened scope authorization with an independent offline regression corpus, deterministic generated suffix/CIDR/order checks, stable rejection contracts and test-only mock contact checks. Existing scope semantics and production code remain unchanged.
- Added the internal async argv-only process runner with bounded separate raw output, truncation/exit/timing facts, direct-child timeout/cancellation cleanup, canonical failures, fake-process and marked harmless local-process regressions. No shell, planner access, scanner adapter, registry, network behavior or command CLI is added.
- Added finite capability/risk metadata, explicit immutable ToolRegistry, trusted adapter/schema interface, canonical unknown/unavailable outcomes, duplicate/conflict rejection and planner-safe deterministic availability catalogs. No binary probing, scanner support, authorization, execution dispatch or real CLI is added.
- Added deterministic local ActionPolicyValidator with available registry metadata, explicit capability/risk allowlists, centralized primary/secondary target checks, strict registered parameter validation and shared structured approval/rejection. Missing target/budget/completed-action policy facts deny; budgets/deduplication and operational dispatch remain future work. No execution, network, Groq or CLI behavior is added.
- Added immutable session execution budgets, atomic action/concurrency/host/rate/output reservations, injected monotonic deadlines, typed outcome snapshots and cancellation-safe permit ownership. Policy budget checks consume already normalized primary/secondary targets; planner metadata cannot override limits. Conservative failed/retry/aborted attempt accounting and new strict execution settings are documented and tested offline. No scanner, network, orchestration or state-machine behavior is added.
- Added controlled in-memory recon state ownership with frozen tuple snapshots, atomic validated action/fact/planner/budget recording, explicit lifecycle history, canonical state-transition failures and provenance/terminal protection. Detached copies prevent nested JSON mutations from changing managed state. Pure budget snapshot contracts retain policy exports and enforcement ownership. No action deduplication, execution, scanner/provider or session loop is added.
- Added versioned semantic action identity, deterministic registered-schema/target canonicalization, typed history deduplication, default-zero bounded failed retries and atomic request admission through the existing state owner. Planner prose, priority, IDs and parameter key order cannot evade equivalence. Current policy/resource checks remain independent; no execution, scanner/provider, retry scheduler or autonomous loop is added.

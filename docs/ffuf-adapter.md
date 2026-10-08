# Specialized FFUF discovery (M3-T05)

`tools.ffuf.FfufAdapter` implements the existing **discover_content** capability,
adapter `ffuf`, risk `active_safe`. Explicit trusted composition detects Linux FFUF
**2.1.0** release, registers it available, and supplies current action policy, real
ActionDeduplicator and the shared BudgetController. Default registry/imports/CLI
remain inert. Caller supplies FfufContext IDs/UTC time, records lifecycle through
on_started and atomically ingests generic output; no dispatcher is added.

Feroxbuster = default bounded recursive content discovery.
FFUF = specialized typed fuzz profiles; **only vhost_names is supported**.
Katana = bounded crawling of linked content.

## Profile and overlap

Planner parameters must be exactly `{"profile": "vhost_names"}`. There is no default
profile, raw syntax, header/body/file/wordlist selection or arbitrary FUZZ placement.
This profile tests virtual-host response metadata using **HEAD** at one numeric
HTTP(S) URL and exactly the internal `Host: FUZZ` header. The wordlist contains full
candidate hostnames, not URL fragments or header templates. Nothing in the URL,
method or body is substituted. Paths are fixed for the entire action; no query,
fragment, percent encoding, dot segments, duplicate separators, non-ASCII/control,
backslash/comma, userinfo, FUZZ or FFUFHASH text is accepted. Empty path becomes `/`;
default port removal is local representation checking, not M3-T06 canonicalization.

**Not supported:** content_paths (Ferox overlap), parameter_names, SNI fuzzing,
authentication/credential attacks or spraying, login/POST/body fuzzing, request files,
arbitrary raw requests/templates/headers/cookies/methods, flag lists, input commands,
external wordlists, proxies/replay, recursive jobs, calibration, scraper selection,
body downloads/output files or newly discovered vhost contact. PLAN leaves mode
selection to M3-T05; this deliberately narrow implementation adds one safe purpose.
No parameter discovery or cross-adapter URL/action equivalence from M3-T06 is added.

ToolRegistry accepts exactly one adapter per capability. Ferox and FFUF therefore
cannot both be registered for discover_content in one immutable registry. Operator
composition selects Ferox by default; specialized sessions explicitly select FFUF.
FFUF cannot accept Ferox's empty parameters or perform recursive path work. Repeated
same-target/profile requests use existing semantic history dedup and never dispatch.
Registry/schema/settings/history must stay fixed for a session; swapping a registry
under recorded history is not a supported way to bypass dedup. No automatic FFUF
fallback, duplicate scheduling or M2 workflow change exists.

## Trusted settings and wordlist

Frozen strict FfufSettings is operator/application policy, constructed explicitly
without global config loader or CLI changes. vhost_suffix is required, canonical
lowercase dotted ASCII DNS (max 240 chars, no trailing dot/IDN/address/template).
It must independently pass the current ScopeValidator before reservation and each
invocation. This is a conservative operator namespace gate, not permission to
resolve/contact candidate descendants.

| Setting | Default | Bounds |
| --- | --- | --- |
| wordlist_profile | vhosts-small-v1 | only this application profile |
| max_requests | 8 | 2–8 Execute attempts, includes upstream retry allowance |
| request_rate | 1 | 1–4; conservative sustained attempt pacing below |
| concurrency | 1 | exactly one worker and sequential child |

Application-owned labels are `www`, `api`, `static`, `dev`, in order. Full candidates
are label + `.` + operator suffix. The adapter admits at most floor(max_requests/2)
candidates and writes one literal candidate plus LF per private wordlist. An odd
request allowance leaves one unused slot. Profile and SHA-256 of the full four-name
ASCII catalog joined by LF/final LF preserve provenance; output lists the admitted
prefix separately. No arbitrary filesystem reader, planner path, remote text,
discovered name or credential source feeds this catalog. Catalog changes require
reviewed application code. Candidate/status responses are facts, not proof of a
configured vhost or a vulnerability; no baseline/comparison heuristic is implemented.

## Contact, isolation and limits

The original representation, canonical primary numeric URL and independent numeric
IP pass centralized scope validation. Hostname URLs fail closed; no resolution,
address rewriting or discovered hostname contact occurs. Scope/private/exclusions
apply as usual. Before each wordlist creation and ProcessRunner call, URL/IP/suffix
revalidate after pacing. Candidate Host values are test data sent only to this
numeric peer; they need no descendant contact authorization. Discovery never changes
Scope. All redirects are disabled, including same-origin; relative/absolute Location
membership is recorded as evidence only with redirect_authorized=false. No redirect
or discovered hostname becomes a new Endpoint, target or action.

Adapter-owned absolute executable/literal argv use unchanged ProcessRunner/ProcessSpec.
Private HOME/XDG/config/temp/PATH environment and cwd isolate FFUF's default ffufrc,
legacy ~/.ffufrc, history/scraper files, proxy and credential environment. No shell,
installer or inherited flags exists. Detection is an isolated no-target `-V`, bounded
to five seconds; only exact 2.1.0 release is accepted (development/other versions deny).
Detection is compatibility evidence, not binary attestation. Trusted local executable
and temporary roots must remain stable; there is no hostile-local-user OS sandbox.

Fixed argv uses `-X HEAD`, `-json`, `-mc all`, noninteractive/quiet, redirects,
recursion, HTTP/2 and calibration explicitly false, empty scraper groups,
ignore-body, request timeout ten seconds, positive rate and one thread. Only one
word exists in each child. Reviewed FFUF runTask retries a failed Execute once
immediately, bypassing the rate ticker. **Two attempts per candidate are reserved**,
including failures, so max_requests bounds Execute calls at eight. Sequential children
wait after completion at least `2/request_rate` seconds or the stricter shared
capability interval. At most a two-attempt retry burst and one active Execute occur;
a conservative attempt envelope over interval T is `2 + request_rate*T`, capped
by eight. This is not a promise of at most R starts in every rolling second, nor a
packet/connection bound. Go's transport can repair a reused connection at the same
URL; no redirect/host widening, application status retry or adapter retry exists.
Each child contains one candidate, reducing connection reuse. HEAD suppresses body
reading in Go HTTP semantics; content length remains tool-reported header metadata,
not collected content or completeness proof. Tool words/lines are validated but
omitted because HEAD body counts are not meaningful.

One shared atomic reservation charges action, numeric contact/suffix host accounting,
capability rate and worst-case two-stream output; it covers at most four sequential
calls. Smaller remaining action/session deadlines apply to every runner call, with
asyncio enforcing the whole action including setup/pacing. Cumulative stdout and
stderr each obey max_output_bytes, as does normalized JSON. JSONL bounds are 32 lines
and 16,384 bytes/line per child, 24 object fields, 2,048-char metadata. Capture truncation
fails atomically. Temp ownership and permits close on error/timeout/cancellation;
attempt/output charges persist; only concurrency releases. Python cancellation
propagates after existing runner cleanup. Runner retains its documented direct-child,
OS CPU/heap/header/packet/process-tree limitations; no live scanner claim is made.

## Results and errors

FuzzDiscoveryOutput contains a web_resource Asset, one HEAD Endpoint at the actual
contact (or none when no response), generic HTTP Observations and untrusted Evidence.
Each observation retains endpoint/path, candidate_value, profile, status_code,
content_length/source, content type/Location when present, source tool/capability/
version, trust and explicit false discovery/redirect authority. Candidate names are
not contacted hostname assets. Caller time/execution/subject references, memory
snapshot locator, evidence hash and catalog hash preserve lineage. No persistence,
Finding or vulnerability inference exists.

JSONL stdout serializes input bytes as standard base64; this is intentionally distinct
from `-of json` file output. Identical duplicates collapse; conflicts/unexpected
URL/Host/candidate/output-file/scraper claims fail atomically. Malformed subsets retain
valid candidates with partial parse_failed and explicit unreported_candidates. All
malformed output fails. Empty output is partial with evidence and no fabricated
negative/vhost/liveness fact; missing responses can reflect tool errors. Request
prefix stopping is explicit request_limit partial. Completed means this finite
profile reported its admitted catalog, not comprehensive discovery.

| Outcome | Canonical result |
| --- | --- |
| Missing/unverified/unsupported FFUF | tool_unavailable |
| Invalid profile/parameters/containment/composition | planner_validation_failed |
| Outside numeric contact/suffix | scope_rejected |
| Nonzero child exit | tool_execution_failed with exit_code |
| Deadline/runner timeout | tool_timeout |
| Malformed/truncated/conflicting/oversized output | parse_failed |
| Private setup failure | tool_execution_failed |

## Reviewed compatibility and tests

Primary source review: [FFUF 2.1.0 main/flags](https://github.com/ffuf/ffuf/blob/v2.1.0/main.go),
[configuration](https://github.com/ffuf/ffuf/blob/v2.1.0/pkg/ffuf/optionsparser.go),
[numeric HTTP runner/Host/redirects](https://github.com/ffuf/ffuf/blob/v2.1.0/pkg/runner/simple.go),
[retry/job scheduling](https://github.com/ffuf/ffuf/blob/v2.1.0/pkg/ffuf/job.go),
[rate ticker](https://github.com/ffuf/ffuf/blob/v2.1.0/pkg/ffuf/rate.go),
[Result JSON schema](https://github.com/ffuf/ffuf/blob/v2.1.0/pkg/ffuf/interfaces.go),
[JSON stdout](https://github.com/ffuf/ffuf/blob/v2.1.0/pkg/output/stdout.go),
[wordlist input](https://github.com/ffuf/ffuf/blob/v2.1.0/pkg/input/wordlist.go).
FFUF's HTTPS transport skips certificate verification; numeric HTTPS vhost responses
are not TLS authenticity or hostname/SNI verification. TLSX remains that separate role.

Reserved source-shaped fixtures and guarded fake runners exercise real policy,
registry/budget/state/dedup contracts offline. No FFUF installation, network/scanner
execution or live compatibility assertion is required. See
[ADR 0019](decisions/0019-specialized-ffuf-vhosts.md) and [testing](testing-strategy.md).

## Shared identity (M3-T06)

Generic output participates in the [shared web identity/state contract](web-identity.md).
Raw evidence and adapter-specific contact/profile checks remain unchanged. Existing
web action dedup now recognizes canonical URL aliases; identity grants no authority.

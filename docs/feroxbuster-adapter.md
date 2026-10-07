# Bounded Feroxbuster content discovery (M3-T04)

`tools.feroxbuster.FeroxbusterAdapter` implements existing `discover_content`, adapter
`feroxbuster`, risk `active_safe`. Trusted composition detects Linux Feroxbuster
**2.13.1**, explicitly registers it available and supplies current action policy,
real dedup eligibility and the shared BudgetController. The registry stays empty by
default. Imports, CLI and the deterministic M2 pipeline stay inert/unchanged.
Caller supplies FeroxbusterContext IDs/UTC time, owns lifecycle and atomic state
recording, and retains the returned normalized memory snapshot.

Katana = crawl linked content. Feroxbuster = bounded recursive path discovery.
FFUF = specialized typed vhost_names HEAD discovery (M3-T05); see [contract](ffuf-adapter.md).

## Input and trusted wordlist

FeroxbusterInput is strict, frozen, empty and extra-forbid. Planner selects only the
capability and primary target. No flags, depth, proxy, headers, methods, commands,
files, wordlist paths/URLs, profile selection or process environment enter planner
parameters. Operator settings are explicitly constructed frozen library data, with
no global configuration loader or CLI additions.

| Operator setting | Default | Allowed |
| --- | --- | --- |
| wordlist_profile | small-v1 | small-v1 only |
| max_depth | 1 | 0–3; root is depth zero |
| max_directories | 4 | 1–8, including root |
| max_requests | 28 | 4–56 logical GET starts, including startup overhead |
| request_rate | 1 | 1–4 wordlist GET tokens/second, bounded burst below |
| concurrency | 1 | 1–2 wordlist workers; directories run sequentially |

`small-v1` is a reviewed application-owned tuple: `admin/`, `api/`, `assets/`,
`index.html`, in that order. These relative literal paths cannot introduce an
origin, query, dot segment, encoded separator or filesystem input. The adapter
writes only this tuple (or its budget-admitted prefix) to a private temporary
wordlist. No operator file reader, remote wordlist, runtime collection or discovery
text feeds it. Profile and SHA-256 of ASCII words joined by LF with a final LF
preserve provenance. Changing the catalog requires reviewed application code.
Names/statuses are observations; `/admin/` or a 403 implies no vulnerability.

## Contact containment and recursion

Primary target must be an explicitly scoped numeric HTTP(S) directory URL with
IPv4/IPv6 and optional finite port. Bare names/IPs, hostname authorities, userinfo,
fragments, queries, non-ASCII/control/whitespace, backslashes, commas, percent
escapes, dot segments, duplicate path separators and non-directory paths reject.
Only plain ASCII alphanumeric, underscore, dot, slash, tilde and hyphen paths are
supported. Empty path becomes `/`; redundant default port is removed locally.
No generic URL canonicalization or M3-T06 behavior is added. Original representation
is checked too, before scope canonicalization can discard an empty fragment.

ScopeValidator validates the primary URL and concrete IP independently. Every next
directory, generated word URL and numeric contact rechecks after pacing and before
wordlist creation/ProcessRunner. Scope remains the existing host-level declaration
contract. Hostname modes fail closed: reviewed Ferox CLI cannot pin an independently
authorized address while preserving hostname semantics. Numeric HTTPS retains
Ferox's default certificate verification; insecure/custom SNI/Host modes are absent.

Fixed `--no-recursion`, `--dont-extract-links`, `--dont-filter`, `--scan-dir-listings`,
`--depth 1`, `--scan-limit 1`, GET, silent JSON and no-state select one finite directory
per process. Ferox depth zero means unlimited and is never passed. Redirects are off;
Location is metadata only. Disabling extraction also disables robots/directory/body
link requests. Disabling wildcard filtering removes random heuristic requests.
Collection of words/extensions/backups, force-recursion, replay, remote wordlists,
updates and parallel child processes are absent. Silent mode bypasses update contact.

The adapter owns a sorted breadth-first directory queue. Only an actually requested
approved word URL with a 2xx response and trailing slash can enter it; no redirect,
403, HTML link, JavaScript or remote path string schedules a request. Seen URLs prevent
loops. Depth/directory/request stopping produces explicit partial limitations. Every
contact stays at the same original numeric scheme/address/port; no external URL from
Location creates an Endpoint or follow-up action. Discovery never changes Scope or
confers authority, including redirects whose membership is reported as allowed.

## Configuration isolation

Complete private HOME/XDG/config/temp/PATH environment and private child cwd prevent
ambient credentials, proxies or user/cwd config. Executable is a trusted absolute path;
argv is a literal tuple passed solely through the existing ProcessRunner. No shell,
raw parameter translation, automatic installation or fallback exists.

Ferox 2.13.1 also merges `/etc/feroxbuster/ferox-config.toml` and a config alongside
its resolved executable. It has no config-disable option, and false defaults cannot
undo merged true settings. **Presence of either file, including a dangling symlink,
fails closed** before detection and before each execution; unreadable paths also fail.
Use an operator-controlled installation without these configs. Version verification
is bounded to five seconds and is compatibility evidence, not binary attestation.
Trusted local executable/config directories must remain stable during child startup;
this is not an OS filesystem sandbox against a hostile local operator.

## Request, rate, time and output bounds

Reviewed Ferox performs connectivity GET + directory-listing heuristic GET + implicit
empty-word GET for each directory. Each admitted process charges **3 + word count**,
at most seven, before another directory is admitted. The adapter trims only the final
wordlist prefix to fit max_requests, stops if fewer than four starts remain, and
records request_upper_bound rather than pretending these are observed HTTP responses.
Defaults cap four directories / 28 starts; absolute cap eight / 56. Failed internal
requests still count toward this conservative allowance; no automatic adapter retry.

Ferox's wordlist limiter is a token bucket: capacity/refill R, one-second refill,
initial max(round(R/2), 1), R=1–4. Its two heuristic GETs bypass that bucket. These
starts therefore have a **bounded startup burst**, not uniform spacing or a promise
of at most R requests in every rolling second. Per-process logical starts in duration
T have a conservative envelope `2 + 2*R + R*T`, also capped at seven total. Sequential
processes wait after completion for at least `7/R` seconds or the stricter shared
capability interval. This prevents repeated fresh-bucket/startup bursts from evading
sustained limits. At most two simultaneous logical wordlist requests, sequential
startup requests and one directory process are permitted. These bounds describe
logical GETs, not TCP/TLS packets or a strict packet-rate guarantee. Pinned reqwest
0.12.22 may retry the same URL at most twice for selected HTTP/2 protocol errors,
under the original request/action timeout. Such repair bypasses the wordlist token
bucket; a logical GET can therefore have three reqwest attempts. These attempts stay
at the same approved numeric endpoint; no generic status-based retry is enabled.

One atomic shared reservation charges action/host/rate/worst-case two-stream output;
sequential calls share that single aggregate allowance, following Katana's bounded
multi-call pattern. Cumulative retained stdout and stderr each cannot exceed configured
max_output_bytes; normalized JSON has the same cap. Every call uses the smaller
remaining action/session deadline and ProcessRunner timeout. asyncio also owns the
whole action deadline including pacing/setup. Configured request timeout is ten
seconds. Timeout/cancellation retain existing runner direct-child cleanup and propagate
canonical timeout/Python cancellation. Temp ownership closes on every exit; all
attempt/output charges persist and only concurrency releases.

Body processing is bounded to Ferox's 16,384-byte response prefix; truncated metadata
is explicit partial evidence. JSONL bounds: 128 lines, 65,536 bytes/line, 32 top-level
fields, 128 header fields, 2,048-character selected header values and 56 total planned
GET starts. Only content-type/Location hints survive; raw body/header dumps do not.
The runner does not provide OS CPU/heap/download/process-tree quotas. Protocol-level
same-peer repair is not a new authorized hostname/contact. No live compatibility test
or complete-site discovery claim follows from source review and fixture validation.

## Normalization and failures

ContentDiscoveryOutput contains generic web_resource Asset, Endpoint, HTTP Observation
and untrusted Evidence. Facts retain URL/path, GET method, HTTP status, tool-reported
content length, source directory, selected content type/Location, body truncation,
redirect membership (never authority) and trust. Source `feroxbuster`, capability,
version, caller subject/time/execution, references, memory locator and stable normalized
snapshot SHA-256 preserve provenance. Content length is tool measurement, not proof of
a complete body. Evidence references the returned snapshot; no persistence is added.

Records sort by URL/source directory. Identical duplicates collapse, independent source
lineage remains, conflicting duplicates fail atomically. Unexpected contacted URLs,
original directory or method fail the whole parse; post-output checking is a consistency
guard, while the fixed profile supplies pre-contact containment. Malformed subsets
retain valid facts with partial parse_failed. All-malformed/truncated/oversized output
fails. Missing/empty output records unreported planned URLs with partial evidence and
no invented liveness/negative fact. No filters hide 404/403/other HTTP status facts.

Missing/unverified/unsupported binary or unsafe ambient config: tool_unavailable.
Nonzero exit: tool_execution_failed with exit_code. Timeout: tool_timeout. Invalid
request/composition/mode: planner_validation_failed; unauthorized target: scope_rejected.
Malformed/bounded/partial output: parse_failed. Local setup failure: tool_execution_failed.
Runner Failure has no partial capture payload. Completed means this finite catalog and
queue finished; it never claims comprehensive discovery or vulnerability confirmation.

## Compatibility and offline validation

Reviewed Feroxbuster **2.13.1**, commit `aa8e1335801e91d98ce0d4fd148c2159a667a83b`:

- [CLI options](https://github.com/epi052/feroxbuster/blob/v2.13.1/src/parser.rs)
- [Ambient config merge](https://github.com/epi052/feroxbuster/blob/v2.13.1/src/config/container.rs)
- [No-follow HTTP client](https://github.com/epi052/feroxbuster/blob/v2.13.1/src/client.rs)
- [Implicit root word and silent update gate](https://github.com/epi052/feroxbuster/blob/v2.13.1/src/main.rs)
- [Connectivity/directory/wildcard heuristics](https://github.com/epi052/feroxbuster/blob/v2.13.1/src/heuristics.rs)
- [Extraction/startup/wordlist scheduling](https://github.com/epi052/feroxbuster/blob/v2.13.1/src/scanner/ferox_scanner.rs)
- [Token bucket and recursion/extraction gates](https://github.com/epi052/feroxbuster/blob/v2.13.1/src/scanner/requester.rs)
- [URL joining](https://github.com/epi052/feroxbuster/blob/v2.13.1/src/url.rs)
- [JSON response serialization](https://github.com/epi052/feroxbuster/blob/v2.13.1/src/response.rs)
- [Pinned dependencies](https://github.com/epi052/feroxbuster/blob/v2.13.1/Cargo.lock)
- [reqwest 0.12.22 same-URL protocol retries](https://github.com/seanmonstar/reqwest/blob/v0.12.22/src/async_impl/client.rs)

Reserved source-shaped fixtures and fake runners need no scanner or network. Tests
simulate an isolated operator filesystem, independently test config-presence rejection,
and forbid real process/network activity. See [ADR 0018](decisions/0018-bounded-feroxbuster.md).
No Feroxbuster installation or live target was required or performed for this task.

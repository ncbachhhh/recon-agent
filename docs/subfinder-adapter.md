# Passive Subfinder enumeration (M2-T02)

`enumerate_subdomains` is implemented by the trusted `subfinder` ToolAdapter.
`resolve_dns` is already implemented by native_dns. DNS verification through DNSX
is implemented separately as verify_dns (M2-T03). Default ToolRegistry stays empty; imports and the inert CLI
perform no probing or reconnaissance.

## Input, availability and composition

The sole input is ActionRequest.target, an authorized hostname/domain used as the
query root. SubfinderInput is strict and empty: parameters must be `{}`. There is
no public-suffix inference or automatic promotion to a parent domain. URLs, IPs and
CIDRs cannot become enumeration roots. All flags, executable, sources, configuration,
credentials, proxies, resolvers, extra arguments and environment are excluded from
planner input and catalog. ToolsConfig/loader and domain models remain unchanged.

Trusted composition explicitly calls `await SubfinderAdapter.detect(config,
binary="subfinder")`. binary is an operator-selected path or PATH name, never a
planner field; shutil.which resolves it to an absolute executable. No auto-install,
fallback scanner or import-time lookup occurs. Missing executable is tool_unavailable.
The injected/default ProcessRunner performs one bounded local `-version -nc -duc`
probe without a target. Version **2.9.0** is the reviewed contract; unknown, malformed,
multiple, older/newer or prerelease versions fail with tool_unavailable. Other
canonical runner failures are preserved. Probe timeout is min(configured timeout,
5 seconds); it shares configured stream bounds but is startup work without a target
reservation. No version text/config paths or credentials enter catalog/output.

On Success, explicitly register the returned trusted instance with AVAILABLE using
AdapterRegistration and ToolRegistry. Direct construction supports offline fakes;
trusted callers must detect before declaring real binaries available. Availability
is a snapshot, not proof of integrity/reachability or a permanent token. The runner
handles later missing/permission-denied binaries canonically. Operators own binary
integrity; file replacement is not sandboxed or cryptographically attested.

execute receives the original ActionRequest, current ActionPolicyValidator, its
same BudgetController and explicit SubfinderContext (asset_id, execution_id,
collected_at). It revalidates request/context, subject lineage, registry binding,
capability/risk/scope/schema/dedup/budget eligibility and reserves atomically before
runner invocation. Approval records cannot bypass revalidation. Caller owns state
history, ingestion, execution-ID uniqueness, audit and retained evidence snapshots;
no generic dispatcher, session loop or persistent store is introduced.

## Passive source and execution

Composition explicitly opts into **HackerTarget only**, a credential-free source.
Subfinder sends the authorized root to `https://api.hackertarget.com/hostsearch/`.
Operators must authorize third-party disclosure/use and observe service terms/rate
limits. Provider infrastructure is a trusted external service boundary, separate
from reconnaissance target declarations; it never grants scope over returned names
or addresses. The source uses published hostsearch data; this adapter performs no
DNS verification or target probing. External service collection/accuracy/completeness
and Subfinder's provider HTTP DNS/TLS/redirect behavior are outside the Python
runner's destination containment. No claim of packet-level provider pinning is made.

Fixed enumeration argv (internal only):

```text
-config <OS null device> -pc <OS null device>
-silent -nc -duc -json -cs -s hackertarget
-rl 1 -rls hackertarget=1/s -t 1 -timeout 10 -max-time 1
-d <canonical authorized root>
```

There is no active/wildcard resolution mode, all/default source set, recursive mode,
output file, proxy, custom resolver, credentials or arbitrary extra flags.
Source HTTP rate is capped at one request/second by the tool; session rolling rates
limit actions independently. The tool's source timeout is 10 seconds and maximum
collection time is one minute; ProcessSpec timeout is the smaller configured timeout
and remaining session time. AsyncProcessRunner enforces that deadline, bounded
stdout/stderr and cancellation/direct-child cleanup. No runner logic is duplicated.
An injected trusted runner must honor the same or smaller stream bound; a larger
adapter stream allowance than the budget allowance rejects before dispatch.

Each probe/action has a fresh TemporaryDirectory. ProcessSpec's internal complete
`environment` tuple replaces inheritance: HOME/USERPROFILE/APPDATA/LOCALAPPDATA/
XDG_CONFIG_HOME point there; only Windows SystemRoot is copied when present. Ambient
secrets, proxy variables and SUBFINDER_CONFIG/PROVIDER_CONFIG are absent. Both explicit
config inputs use the OS null device; automatic default config creation/migration
occurs only inside temporary paths. The directory is cleaned after runner cleanup,
including failure/cancellation. The existing cwd is unchanged and executable is
absolute. ProcessSpec environment is excluded from repr and planner projections;
deliberate internal dumps still require care. This prevents ambient YAML from enabling
active contact despite false default CLI flags; see ADR 0009.

Subfinder uses in-process Go work in the reviewed path. Runner supervision covers
only its direct child, with existing OS/spawn/cleanup limits; no new process-tree,
CPU or child-memory containment is claimed. Attempt/host/concurrency/rate/two-stream
output reservations apply; failure/cancellation keep charges and release concurrency.
Session expiry after runner return discards facts. Startup probes do not enumerate.

## Parser, normalization and evidence

Reviewed `-json -cs` JSONL fields are exactly host, input and sources (one
`hackertarget` entry). UTF-8 is strict; blank lines are ignored. Every other line
must be a valid object with unique keys, typed fields, matching canonical input
root and a proper descendant hostname. Root itself, suffix lookalikes, outside
names, URLs, IPs, malformed syntax, unsupported IDN/wildcards, unknown fields/sources,
banners or malformed JSON fail the whole action with parse_failed. No earlier
observations survive a malformed line. Limits: 4,096 lines, 2,048 characters per
nonblank line, 254 characters per wire hostname and 1,024 unique hosts. Captured
bytes and serialized normalized output also have explicit configured bounds.

Centralized ScopeValidator supplies name syntax/canonicalization and label
membership using a temporary parser-only declaration for the queried root. This
local parser declaration is never the operational scope and is never returned as
an approval. ASCII names lowercase/remove one trailing dot, with existing invalid
representations rejected. Hosts deduplicate and sort lexically; IDs, facts and
normalized evidence hashes are deterministic for identical facts/context regardless
of source line order/cosmetic duplicate spelling. Operational exclusions and
allow_subdomains=false do not erase discovered data: such names remain unactionable.
Outside-query-root names are rejected as invalid tool output.

SubdomainOutput is a tools-local envelope, not a new top-level domain entity. It
returns canonical root/host tuple, source_version/provider_sources, the root Asset,
generic kind=metadata Observations and generic Evidence. Each observation has
hostname, query_target, status=discovered, capability=enumerate_subdomains,
source_version=2.9.0 and provider_sources=[hackertarget]. Source is subfinder; caller
subject/time/execution and evidence references preserve lineage. No discovered host
is immediately made an Asset, DNS-verified or marked authorized.

One untrusted Evidence references `memory:<execution_id>` / locator `discovery`.
SHA-256 covers canonical sorted compact JSON of query_target, source_version,
provider_sources and hosts; these fields are returned so callers can retain/recreate
that snapshot. This is normalized discovery evidence, not raw stdout or a persisted
artifact. stderr, ambient config, paths, raw lines and remote diagnostics are omitted.
Provider attribution is tool-reported evidence, not a trust grant.

## Outcomes

| Condition | Existing result |
| --- | --- |
| Valid nonempty discovery | Success[SubdomainOutput] |
| Empty/blank output with zero exit | Success, zero hosts/observations plus empty discovery evidence |
| Malformed, outside-root, oversized or truncated output | Failure parse_failed, no partial facts |
| Missing/permission-denied executable | Failure tool_unavailable |
| Nonzero exit/local setup/execution error | Failure tool_execution_failed (exit_code retained for nonzero exits) |
| Runner/session deadline | Failure tool_timeout |
| Policy/scope/registry/budget denial | Existing canonical Failure; no process |
| Caller cancellation | asyncio.CancelledError propagates after runner cleanup; permit/temp directory release |

Empty success means zero reported discoveries, not proof that no subdomains exist
or that the provider succeeded: Subfinder may suppress source errors with a zero
exit. stderr is not parsed into invented provider outcomes. Failure messages are
fixed, omit raw/native details and retain conservative retryability. No automatic
retry or scope expansion occurs. Every future contact must independently pass the
current ScopeValidator/ActionPolicyValidator, including address/contact rules.

Reviewed primary sources: [Subfinder 2.9.0 flags/configuration](https://github.com/projectdiscovery/subfinder/blob/v2.9.0/pkg/runner/options.go),
[JSONL output](https://github.com/projectdiscovery/subfinder/blob/v2.9.0/pkg/runner/outputter.go),
[passive enumeration](https://github.com/projectdiscovery/subfinder/blob/v2.9.0/pkg/runner/enumerate.go),
[HackerTarget source](https://github.com/projectdiscovery/subfinder/blob/v2.9.0/pkg/subscraping/sources/hackertarget/hackertarget.go)
and [goflags 0.1.74 configuration precedence](https://github.com/projectdiscovery/goflags/blob/v0.1.74/goflags.go).
These are reviewed compatibility facts, not claims of a live-binary/network test.
See [ADR 0009](decisions/0009-isolated-passive-subfinder.md) and
[testing](testing-strategy.md).

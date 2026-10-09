# Nuclei adapter foundation (M5-T01)

`tools/nuclei.py` provides explicit `NucleiAdapter` registration for the existing
`scan_templates` identity, local availability probing and offline captured-result
ingestion. **Every scan profile is denied.** No scan argv is returned and no scan
runner call, reservation, target contact, template read/download/update or automatic
selection exists. Registry availability and a successful action-policy decision
cannot bypass this gate. M5-T02 owns reviewed profile policy; M5-T03 owns actual
profile/argv/destination/resource enforcement; M5-T04 owns Finding normalization;
M5-T05 owns finding deduplication. M5-T02 now implements the separate
[inert profile policy](nuclei-profile-policy.md); M5-T03+ remain unimplemented.
The deny-only adapter stub is unchanged and does not consume that catalog.

## Inputs, registration and runner boundary

`NucleiInput` is strict/extra-forbid with one required ASCII semantic `profile` name
(lowercase letter then up to 63 lowercase letters/digits/underscores/hyphens).
There is no implicit input/execution default. The separate M5-T02 catalog names
safe as its policy default. Paths, URLs, flags, templates, environment, approval
booleans and executable parameters cannot be supplied. `NucleiProfilePolicy.resolve`
is an immutable deny-only interface stub with no catalog, plugin or override.
`scan_spec` returns existing `OperationResult[ProcessSpec]`, always Failure.
`execute` revalidates request/context, selected registry identity and budget-controller
binding, invokes existing ActionPolicyValidator (scope/schema/risk/budget/dedup),
checks the context subject and then denies before reservation or contact. No earlier
policy, runner, budget, state, capability or configuration contract changes.
The default registry stays empty; imports and the CLI stay inert.

Trusted composition may explicitly call `detect`, with operator binary selection and
an injected ProcessRunner. Linux is the reviewed probe platform. PATH lookup is
local only; missing executables produce `tool_unavailable`. The sole runnable argv is
`-duc -nc -config /dev/null -version`, using an absolute operator-selected executable,
a private temporary cwd and complete child environment containing only private
PATH/HOME/XDG_CONFIG_HOME/XDG_CACHE_HOME/TMPDIR. No ambient keys/proxies/configuration
or template paths are inherited. Timeout is min(configured timeout, 5 seconds);
existing runner capture, timeout, cancellation and child cleanup apply. The temporary
directory is removed on success, failure and cancellation. Fake runners implement
these trusted execution contracts; there is no fake-only scan approval switch.

Probe acceptance requires exactly one `Nuclei Engine Version: v3.4.10` (optional v).
Other/ambiguous versions fail closed. This is the reviewed probe/format version,
not a latest-version recommendation. Upstream [version callback and CLI source](https://github.com/projectdiscovery/nuclei/blob/v3.4.10/cmd/nuclei/main.go)
returns before scan setup; updates are disabled and no templates are supplied.
Successful detection returns an adapter, never registers/enables it or approves
scans. The local operator-selected executable remains a trusted code boundary,
not an OS sandbox. No real engine was installed or run for task validation.

## Offline captured-result interface

`adapter.ingest(OperationResult[ProcessExecution], context=..., scope=...)` only
parses already captured bytes. It invokes no runner, availability lookup, network,
filesystem source read, scope expansion, budget reservation or state mutation.
It does not authorize or retroactively verify how the capture was produced.
`NucleiContext` supplies asset/execution IDs, aware caller UTC collection time,
query target and optional caller-established scanner version (3.4.10 or unknown).
The parser format is explicitly `nuclei-result-event-3.4.10`. An event cannot establish
scanner/template version, approved template provenance, confidence or verification.
Finding remains staged in the domain, as required by M5-T04.

Synthetic fixtures follow the upstream [ResultEvent schema](https://github.com/projectdiscovery/nuclei/blob/v3.4.10/pkg/output/output.go).
Selected fields are template ID/reported path/URL, name/description/reported severity/
references, event type, host/matched-at/URL/IP, matcher/extractor/extracted strings and
reported timestamp. Required fields: template-id, info object, type, host, matched-at,
and an exact boolean true matcher-status. Explicit event errors deny candidate
promotion. Optional absent facts remain null/empty; missing severity is never invented.
Type is reported text, not a protocol/template allowlist or operational selector.
Only target representations understood by the centralized ScopeValidator can be
promoted. Host:port strings and arbitrary file/match expressions are unsupported.

Query scope is checked centrally; every reported host, matched location, optional URL
and numeric IP is independently scope-checked. Subject locations must match the
query's canonical host; an unrelated host even elsewhere in scope cannot be attached
to this asset. IP membership does not prove a hostname binding or authorized contact.
Source template URLs, references and paths are inert text and are never fetched/read.
Unknown fields (including raw request/response, commands, authors/tags) remain solely
in exact retained stream evidence. Remote instructions cannot change any control.
No claim that source labels alone prove safe template behavior is made.

Records preserve input order and physical line numbers. Each accepted
`NucleiCandidate` has constant `verification=unverified`, source/execution ID,
observation/evidence references and a SHA-256 of its exact JSON line (excluding line
terminator). Generic metadata Observations use caller asset/time and those links.
Exact duplicate and conflicting records stay separate with distinct line/observation
IDs and unchanged reported severities; no finding identity/merge/interpretation exists.
Two existing untrusted Evidence records cover retained stdout/stderr, exact byte
hashes, execution/origin/time and truncation flags. Output base64 retains exact bytes,
including malformed/unknown fields and binary stderr; artifacts are memory references,
not persisted files. References/commands in evidence must never be executed or fed
unlabelled to a future planner. Future renderers must escape/redact this data.

## Bounds and outcomes

Per stream: min(configured capture limit, 1 MiB). At most 256 physical stdout lines,
64 KiB per record, 128 top-level keys and 64 info keys; bounded selected strings/lists.
Duplicate JSON keys at every level, non-finite constants, bad UTF-8, malformed fields,
unsuccessful matches and unsupported/unmatched targets reject that record. Recursion
errors are caught. Input bytes/line bounds apply before normalization; normalized
candidate/observation JSON and base64 expand the bounded capture in memory and do not
claim to fit the runner's raw-stream byte limit. No scan/session resource spend occurs.

| Capture | Outcome |
| --- | --- |
| All valid, or empty zero-exit output | Success output, completed ingestion; no verified scan, finding or clean-target claim |
| Some valid plus malformed/non-zero/truncation | Success output, partial, canonical parse_failed/tool_execution_failed and evidence |
| No valid plus malformed/non-zero/truncation | Success output, failed, no observations/candidates, retained evidence/errors |
| Oversized streams/line count or invalid capture/context | Failure parse_failed before candidate construction |
| Query outside scope | Failure scope_rejected |
| Runner Failure including missing binary/timeout | Preserve existing Failure; runner contract has no captured bytes to invent |
| Caller cancellation during probe | Propagate after existing runner and temporary-directory cleanup |

A truncated final line without a newline is never promoted, even if its prefix parses
as JSON. Other fully retained lines may remain partial candidates. Non-zero exit
codes are retained in canonical ErrorContext. Callers inspect output.status/errors;
Success means an ingestion envelope exists, not that the scanner succeeded.
Only completed/partial observations can later enter corresponding ActionResults;
failed ingestion carries evidence without observations. No ActionResult/state owner
or generic dispatcher is added.

## Setup and validation

SETUP REQUIRED: None. Offline development/tests require no Nuclei installation,
template package, new Python dependency, network or Groq credentials. Optional local
availability probing needs an already operator-provisioned Linux Nuclei 3.4.10 binary;
that is unnecessary now and never enables scanning. Operational setup and reviewed
immutable template provenance belong to later policy/enforcement tasks. Do not install
binaries or download/update templates automatically.

Run focused Nuclei/registry/action-policy/dedup tests, followed by the full repository
baseline, pre-collection network/DNS guards, coverage, build/fresh-wheel cold imports
and copied fixture tests, CLI, source parity, artifact/secret and final diff checks.
Tests use reserved synthetic JSONL and fake runners; no live engine/template/target.

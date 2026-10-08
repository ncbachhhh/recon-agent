# FTP metadata adapter (M4-T04)

**FTP capability = unauthenticated metadata only.** `tools.ftp.FtpAdapter`, adapter
`native_ftp`, implements `inspect_protocol` / `family=ftp`, active_safe. Explicit
AVAILABLE registration declares native implementation availability, not authorization
or server reachability. Imports/default registry/CLI and discovery workflow stay inert.

## Approved greeting_feat_v1 profile

One independently scoped numeric TCP control connection receives one initial FTP
reply. Only a valid `220` greeting permits the sole outbound application message:
`FEAT\r\n` (six fixed bytes, no arguments). Read one feature reply, then close/abort.
No QUIT, SYST, HELP, OPTS, TLS negotiation, retry, second greeting wait or fallback.
A `120` delayed/other syntactically valid non-error greeting yields partial banner
metadata without sending anything; this finite profile does not wait for a later 220.

Reply framing follows [RFC 959 section 4.2](https://www.rfc-editor.org/rfc/rfc959.html#section-4.2).
The fixed FEAT request and feature lines follow
[RFC 2389 section 3](https://www.rfc-editor.org/rfc/rfc2389.html#section-3).
The AUTH TLS feature advertisement is described in
[RFC 4217 section 6](https://www.rfc-editor.org/rfc/rfc4217.html#section-6).
These standards describe broader clients; this repository approves only the narrower
pre-authentication greeting/FEAT exchange. A server requiring login yields a limitation.

Prohibited: USER/PASS/ACCT, any authentication (including anonymous/guest), credentials,
password guessing/spraying/brute force, directory listing (LIST/NLST/MLSD/MLST), file
retrieval/upload/delete (RETR/STOR/STOU/APPE/DELE), directory/writable tests (CWD/PWD/
MKD/RMD), rename, SITE/command execution, exploitation and remote modification.
No PORT/EPRT/PASV/EPSV/data connection, proxy, command strings or generic FTP client
API exists. AUTH/PBSZ/PROT/CCC are never sent; advertised TLS is data, not negotiation.
Implicit FTPS, TLS verification/certificates and authenticated features are uncollected.

## Service, input and authorization

Strict frozen FtpInput specializes the common schema to family=ftp, integer port
1–65535 and transport=tcp, with no defaults or extra fields. Target is an explicit
host/IP, never URL/CIDR. Credentials, file paths, command lists and planner-controlled
protocol/address/resolver/TLS/low-level options reject before contact or spending.

Trusted composition supplies 1–64 immutable FtpServiceBindings: canonical subject,
canonical numeric contact and prior normalized Service. Exact TCP FTP relevance
under M4-T01 is required; port-only/composite/unknown/cross-product guesses reject.
Host/port bindings are unique. Request port and optional asset ID must match the
observed Service. Numeric subjects equal their contact. Caller-selected bindings
are observations, not permission or proof of DNS relationships.

Current ToolRegistry selection, ActionPolicyValidator schema/risk/allowlists/scope/
real dedup/budget eligibility and independent contact ScopeValidator precede one
shared atomic reservation. Registry/subject/contact scope recheck after trusted
start notification and immediately before contact. Subject/address exclusions and
private gates remain mandatory. No DNS, address switching, redirect, new hostname
contact or derived authorization occurs. Numeric asyncio flags/family pin the contact.

SSH/SMB/FTP and M4-T05 [SMTP](smtp-adapter.md) are explicit alternatives under
ADR 0003's single-adapter-per-capability rule. No automatic router or conflicting registrations.
No change to earlier production modules, dependencies, policy/state/runner or CLI.

## Bounds and cleanup

At most one connection and one FEAT request per admitted action. Aggregate retained
reply bytes ≤ min(8192, execution output limit, shared per-action output limit),
line bytes ≤512 including CRLF, each reply ≤64 lines. Require CRLF, strict UTF-8
reply text, no ASCII controls except HTAB; FEAT labels/parameters are bounded ASCII.
Single/multiline reply framing ends at the original code plus SP. Ordered exact
feature lines are retained, including unknown names and duplicate claims.

Whole-action outer/native timeout is min(configured timeout, remaining session time)
(default 30 seconds); there is no per-read deadline reset. Shared action/host/rate/
concurrency/output/session budgets apply; serialized output is separately bounded.
One action charges both distinct logical subject and numeric contact. Rate counts
admitted control connections; each connection contains at most one six-byte FEAT.
No packet-rate/OS receive-buffer guarantee is claimed. Asyncio may buffer unread bytes;
application capture stops at reply terminators and synchronously aborts unread data.

EOF/malformed/oversized feature reply retains only bounded available data or the
already valid greeting; line/count/aggregate overflow discards that feature reply.
It reports partial metadata, never unsupported features as fact. Socket close/abort
and permit release have no cleanup await; cancellation propagates. Timeout/connection
failure discards partial bytes under existing Failure semantics. Session expiry or
serialized-output overflow discards the output. No live interoperability guarantee.

## Normalization and canonical outcomes

Original Service remains intact. FtpOutput extends ProtocolMetadataOutput with
query_target/contact/profile, completed/partial status and at most one canonical
ErrorInfo. Generic metadata Observation and untrusted Evidence retain original asset/
host/service IDs, port/tcp, caller UTC/execution, source=native_ftp,
capability=inspect_protocol, memory locator and SHA-256 normalized snapshot digest.
Digest is evidence lineage, never authenticated identity or vulnerability evidence.

Snapshot contains exact greeting banner (multiline joined with CRLF), greeting code,
conservative full-banner vsFTPd/ProFTPD/Pure-FTPd product/version hints, exact ordered
features, feature collection flag/reply code/limitation and retained raw capture base64.
TLS advertisement is true only for an AUTH line explicitly naming TLS; otherwise
null/unknown. Lack of advertisement does not prove lack of support. Authentication,
file-operation and TLS-negotiation flags are false. Never infer vulnerabilities from
product/version strings or treat feature labels as executable commands.

| Condition | Existing result |
| --- | --- |
| Current scope/policy/schema/service/budget denial | Failure with canonical policy/planner/budget ErrorInfo; no contact |
| Refused/unreachable/closed empty greeting | tool_execution_failed, fixed diagnostic without native text |
| Whole-action/native/session timeout | tool_timeout; no partial payload |
| Malformed/oversized greeting or normalized output | parse_failed; no observations |
| 4xx/5xx greeting | tool_execution_failed; no FEAT/login fallback |
| Valid unsupported initial greeting | Success[FtpOutput], partial + parse_failed; banner only |
| FEAT denied/unsupported/unexpected/malformed/incomplete | Success[FtpOutput], partial + parse_failed; valid banner retained |
| Valid 211 single line / multiline features | completed; empty / reported feature list |

Remote banners and feature lines remain untrusted data through generic state ingestion.
Instruction-like text cannot add a command, alter policy or initiate another contact.
Caller owns coherent ActionResult/lifecycle/time and uses output.errors[0] for partial
results; adapter does not mutate ReconState or create Findings.

Offline fixture/native-stream/actual-policy tests assert sole FEAT bytes, absence of
all login/file commands and unread subsequent replies, scope/port/family/injection
denials, framing/time/output bounds, provenance/state/dedup and cancellation cleanup.
No FTP binary/library/server/network/provider runs in default tests.

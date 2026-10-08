# SSH metadata adapter (M4-T02)

**SSH capability = unauthenticated metadata only.** `tools.ssh.SshAdapter`, adapter
`native_ssh`, implements existing `inspect_protocol` / `family=ssh`, active_safe,
with one **receive-only server identification** profile: `server_identification_v1`.
Explicit AVAILABLE registration is trusted native implementation availability,
not server reachability or authorization. Default registry/imports/CLI stay inert;
M2 discovery workflow is unchanged. No external SSH binary/library/dependency exists.

## Approved profile and exclusions

One independently scoped numeric TCP connection reads the initial server
identification and bounded preceding lines, then synchronously closes/aborts.
**Zero application bytes are sent**, including no client identification string.
No binary packet parser/writer, key exchange, service request or session exists.
Servers that wait for a client identification can time out; there is no send/retry
fallback. This is an identification inspection, not a complete SSH client handshake.

The identification grammar is based on [RFC 4253 section 4.2](https://www.rfc-editor.org/rfc/rfc4253.html#section-4.2)
and compatibility identification in [section 5.1](https://www.rfc-editor.org/rfc/rfc4253.html#section-5.1).
The standard describes a full protocol version exchange; this deliberately narrower
profile reads only the server half and terminates before negotiation. Software and
protocol tokens are printable ASCII without whitespace/minus; comments/preambles
are strict UTF-8 data without ASCII controls. SSH 2.0 requires CRLF; 1.99 also permits
LF and is reported as compatible. Other syntactically numeric versions retain
identification as partial metadata with an explicit unsupported-protocol limitation.
Malformed strings, alternate encodings, missing identification or ambiguous extra
bytes from injected transports fail closed. No SSH 1.x fallback/negotiation exists.

Collected: exact banner, reported protocol/software token, optional comments,
ordered preamble lines and raw greeting bytes in base64. Only explicit complete
`OpenSSH_<alphanumeric/dot version>` and `dropbear_<alphanumeric/dot version>`
software tokens yield product/version hints. Unknown software remains exact reported
text. No vulnerability or server identity verification is inferred.

Key exchange, supported algorithms, host keys and their fingerprints are **not
collected** by this profile. Output states algorithms_collected=false and
host_key_collected=false; absence does not claim lack of support. Evidence SHA-256
is a normalized snapshot digest, never a host-key fingerprint.

Prohibited: usernames/passwords, credential guessing/spraying/brute force, public-key
user authentication, private-key loading, authentication attempts (including none),
SSH commands, interactive shells, SFTP/SCP, remote modification and exploitation.
No auth/credential/file/command/raw-option parameter or generic client API exists.
Instruction-like comments/preambles cannot alter the profile or cause a follow-up.

## Service, request and contact boundary

Strict SshInput specializes M4-T01 ProtocolMetadataInput to family=ssh, port 1–65535,
transport=tcp; no defaults, raw options or additional fields. ActionRequest.target
must be an explicit hostname/IP, not URL/CIDR. All params pass current policy schema
validation, then the adapter independently validates its specialized schema.

Trusted composition supplies 1–64 immutable SshServiceBindings: canonical subject
host, canonical numeric IPv4/IPv6 contact, and an existing normalized Service.
The Service must be an unambiguous SSH candidate under M4-T01 exact relevance rules;
unknown/HTTP/UDP/composite/conflicting product data cannot construct the adapter.
One host/port binding is unique. Planner cannot supply a binding, observed Service,
address, resolver or alternate port. Missing observed binding or mismatched request
asset/port rejects before spending/contact. Numeric subjects must equal their contact.

Bindings represent caller-selected prior observations, not authenticated discovery or
permission. The trusted caller associates the Service host/asset/evidence with the
correct subject; no DNS relationship is inferred. Current ToolRegistry binding,
ActionPolicyValidator capability/risk/scope/schema/budget/real dedup eligibility and
independent concrete contact ScopeValidator membership precede execution. Scope's
existing host-level rules remain unchanged: finite observed binding ports constrain
this profile, not a newly invented global scope port ACL. Exclusions/private gates
apply to both name and contact. Scope/discovery never grants contact implicitly.

No DNS resolution occurs: native asyncio connects only to the approved numeric address
with explicit address family and numeric host/service flags. There is one contact, no
proxy/env configuration, hostname fallback, address switching, retry or discovered
hostname/key/banner contact. Current registry/name/address scope are checked again
after the trusted start notification, immediately before connection. Injected
transports are trusted code required to obey the same receive-only/contact bounds.

## Resource ownership and cleanup

One shared BudgetController atomic reservation charges the primary/contact host,
action, capability rate, concurrency and worst-case two-stream output allowance.
Denied work spends nothing; failure/timeout/cancellation/aborted starts retain
charges, and only concurrency releases. One connection per attempt, no additional
protocol requests or retry. Admission rates bound connection starts, not OS TCP
retransmissions/packets. The transport sends no SSH application data.

The adapter and native transport both enforce the smaller snapshotted execution
timeout and remaining session duration. An injected collector cannot bypass the
outer deadline. Post-return session expiry discards metadata. Python cancellation
propagates; synchronous permit/socket cleanup survives repeated cancellation.
Native cleanup calls writer.close and transport.abort without unbounded wait_closed;
standard asyncio owns cancellation/cleanup while establishing its connection.

Capture: at most min(4,096, configured output bytes, shared output bytes), at most
16 preceding lines, at most 512 bytes per preceding line and 255 bytes per
identification (including newline). Native reads one byte at a time and stops at
identification LF without reading binary packets. Reader flow-control limit is 512;
standard transport/OS buffers can transiently hold more than that threshold and are
aborted/discarded. The bound is on application retention, not all bytes arriving at
the OS. UTF-8 decoding/snapshot/base64 copies have bounded overhead. Full serialized
output is also capped by the smaller configured/shared output limit. No OS CPU/memory
quota, live network compatibility or minimum-Python-version run is claimed.

## Normalized data, errors and caller state

SshOutput extends common ProtocolMetadataOutput: original Service, family=ssh,
query_target/contact_address/profile, completed/partial status, errors, one generic
metadata Observation and untrusted Evidence. Snapshot data includes service/host IDs,
port/transport/family/capability/profile, raw/parsed identification and collected-field
limits. Prior Service/product/version/observation IDs are preserved without overwrite.
Caller supplies SshContext execution ID and aware UTC collection time; no time/subject/
execution is invented. Matching source native_ssh, execution/time, memory snapshot
reference/locator, evidence link and stable snapshot SHA-256 preserve provenance.
Remote text remains untrusted data and is never automatically logged or executed.

| Outcome | Contract |
| --- | --- |
| Valid supported 2.0/1.99 identification | Success[SshOutput], completed for this identification-only profile |
| Syntactically valid unsupported protocol | Success[SshOutput], partial with parse_failed and exact reported identification; no negotiation/fallback |
| Malformed/oversized/incomplete greeting or output | Failure parse_failed; no fabricated metadata payload |
| Refused/unreachable/closed-before-any-byte | Failure tool_execution_failed with fixed diagnostics, no native exception leakage |
| Connect/read/whole-action/session deadline | Failure tool_timeout; no returned partial payload |
| Registry missing/unavailable/not_checked | Existing tool_unavailable before contact |
| Scope/schema/risk/service/dedup/resource denial | Existing canonical policy/budget failures before contact |
| Caller cancellation | asyncio.CancelledError propagates after cleanup; no returned payload |

The caller retains normalized snapshot evidence and owns requested/approved history,
optional post-reservation on_started, terminal ActionResult (preserving partial/error),
and atomic existing-state observation/evidence ingestion. Original subjects/service
must already be present; the adapter does not create/merge state, infer findings,
change scope or schedule work. Real history dedup denies completed equivalents before
contact/spending when policy budget eligibility also holds. Default policy still denies.

In composition selecting SshAdapter, only SSH is operational. The selected
inspect_protocol adapter
uses SshInput, which rejects SMB/FTP/SMTP/database families; their known M4-T01
contracts grant no availability. M4-T03 SMB is a separate explicit composition
alternative; M4-T04 adds separate [FTP metadata](ftp-adapter.md);
M4-T05 adds [SMTP metadata](smtp-adapter.md); M4-T06 adds [database metadata](database-adapter.md). No generic router exists.
See [protocol contracts](protocol-capabilities.md), [security model](security-model.md),
[budgets](execution-budgets.md), [state](state-transitions.md) and
[ADR 0022](decisions/0022-receive-only-ssh-identification.md).

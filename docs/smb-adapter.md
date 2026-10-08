# SMB metadata adapter (M4-T03)

**SMB capability = safe metadata collection only.** Explicit `tools.smb.SmbAdapter`
(`native_smb`) implements `inspect_protocol`, family=smb, active_safe through the
single named profile `smb2_negotiate_v1`. Availability means the native implementation
exists, not permission or reachability. Default imports/registry/CLI are inert.

## Permitted exchange and limitations

One independently authorized numeric Direct TCP connection sends exactly one
112-byte SMB2 NEGOTIATE frame, reads one bounded response, then closes/aborts.
Only command 0 is implemented; message/session/tree IDs, signature and request flags
are zero. One credit is requested, client signing-enabled is advertised, client
capabilities and start time are zero. An execution-local generated UUID is the
client GUID; it is not planner data or a credential. The fixed offered dialects are
2.0.2, 2.1, 3.0 and 3.0.2. No retry, downgrade or second exchange follows.

This profile follows Microsoft [SMB2-only negotiation](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-smb2/77f696b8-9aa0-4ed1-abb2-c097c0ccb05a)
and [request syntax](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-smb2/e14db7ff-763a-4263-8b10-0c3944f52fc5).
It ends before user authentication or share access. There is no SESSION_SETUP,
including anonymous/guest/none, NTLM/Kerberos exchange, credential/hash/key input,
credential guessing/spraying/brute force/capture, relay/pass-the-hash, account
queries, TREE_CONNECT, RPC/share enumeration, file read/upload/write/delete,
commands, interactive sessions, exploitation, remote persistence or modification.
Transport write sends the fixed negotiation message only; it is not an SMB WRITE
operation. No generic client, message/command builder, binary or dependency exists.

SMB1, SMB 3.1.1 contexts, NetBIOS sessions, RDMA, QUIC, compression/encryption,
authentication-dependent names/workgroups/domains and anonymous shares are outside
this profile. Share visibility is deliberately not approved by ADR 0023. Port 139
and normalized netbios-ssn reject before contact; other observed TCP ports require
unambiguous smb/microsoft-ds identity and Direct TCP semantics. Known family relevance
alone does not promise an operational transport. Unsupported/auth-dependent data
produces an explicit fixed failure or collected-field limitation, never fallback.

## Request, service and scope

SmbInput has only strict family=smb, port 1–65535, transport=tcp. No planner contacts,
shares, credentials, operations, dialects, signing flags or raw options are accepted.
ActionRequest.target is an explicit hostname/IP; URL/CIDR requests reject. Trusted
composition supplies 1–64 immutable canonical host/numeric-address/prior-Service
bindings; exact M4-T01 selection must identify SMB, and each host/port is unique.
Request asset/port must match the observed binding. Numeric subjects equal contacts.
The caller is responsible for associating observations with the right subject;
bindings neither verify DNS/identity nor grant scope.

Current registry binding, ActionPolicyValidator allowlists/schema/risk/real history
eligibility, independent subject and concrete-address ScopeValidator checks, and
one shared atomic BudgetController reservation precede contact. Both hosts charge
where distinct. A trusted start callback is followed by registry and scope rechecks.
The native stream pins the numeric address using explicit address family and numeric
host/service flags; no DNS, proxy, discovery/follow-up name/share contact or address
switch occurs. Scope's existing host-level rules remain unchanged; observed ports
constrain this adapter. Default policy still denies. Discovery is never permission.

## Capture, parsing and cleanup

The smaller execution/session deadline wraps the complete action, including injected
transports; native connect/drain/read also has a deadline. The response, including
4-byte [Direct TCP framing](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-smb2/1dfacde4-b5c7-4494-8a14-a09d3ab4cc83),
is at most min(8,192, configured output bytes, shared output bytes). The declared
size is validated before reading the body; only one frame is consumed. Full serialized
output has the same configured/shared cap, so excessive normalization fails closed.
No unbounded read, decompression, nested ASN.1/GSS parsing or message loop exists.

The [synchronous header](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-smb2/fb188936-5050-48d3-b350-dc43059638a4)
must identify one unsigned, uncompounded NEGOTIATE response to message 0/session 0.
Success validates fixed body structure, offered dialect, signing bits and security
buffer bounds/padding. Reserved fields carry no semantics. An opaque bounded server
security offer stays raw evidence; it is never interpreted or used to authenticate.
An empty buffer may have one compatibility placeholder byte. The
[error body](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-smb2/d4da8b67-c180-47e3-ba7a-d24214ac4aaa)
is also bounded and validated; its contents cannot direct retry/authentication.

One action/rate/concurrency/host reservation charges the existing worst-case two-stream
output allowance; denied requests spend nothing. All started failures/aborts retain
charges and release concurrency. Rates bound connection/request starts, not TCP
packets/retransmission. Cancellation propagates after synchronous permit/socket
cleanup; writer.close/transport.abort avoid an unbounded wait_closed. asyncio owns
in-flight connection cleanup. Reader/OS buffers may transiently exceed application
retention limits; unread bytes are discarded. No OS quota or live compatibility claim.

## Normalization and failures

SmbOutput extends the common ProtocolMetadataOutput: original Service, family=smb,
query target/contact/profile, completed status for negotiation only, one generic
metadata Observation/untrusted Evidence and empty errors. Caller supplies execution
ID and UTC collection time and owns lifecycle/terminal ActionResult/state ingestion.
No adapter state/scope mutation, findings, vulnerability inference or follow-up occurs.

[Response fields](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-smb2/63abf97c-0d09-47e2-88d6-6bfa552949a5)
normalize selected dialect, reported signing-enabled/required bits, server GUID,
capability bits, transaction/read/write size limits and raw FILETIME counters.
Reported sizes never control our allocation or dispatch. Signing is reported, not
cryptographically verified. Domain/workgroup/shares-collected are false; SMB1/3.1.1
support is unknown. The selected SMB2/3 family is confirmed only for this response,
with no exhaustive support inventory or negative claims about other dialects.
Exact response base64, source native_smb, service/host/port, execution/time and a
stable canonical snapshot SHA-256/memory reference preserve untrusted provenance.
The GUID is an identity hint, never verified identity or a new contact. Remote strings
and opaque offers cannot become policy. Signing disabled never creates a Finding.

| Outcome | Canonical contract |
| --- | --- |
| Valid offered negotiation | Success[SmbOutput], completed for this profile only |
| Access denied/logon required/more processing | Failure tool_execution_failed; authentication-dependent metadata unavailable, no fallback |
| Other valid negotiation error | Failure tool_execution_failed; unsupported/refused, no fallback |
| Malformed/oversized/partial/unoffered/extra/compound/transform data | Failure parse_failed; no fabricated result |
| Refused/unreachable/closed before complete response | Failure tool_execution_failed; fixed diagnostics |
| Connect/drain/read/action/session deadline | Failure tool_timeout; no partial payload |
| Missing/unavailable registration | Existing tool_unavailable before contact |
| Scope/schema/service/history/resource denial | Existing canonical policy/budget failure before contact |
| Cancellation | CancelledError propagates after cleanup |

ToolRegistry still selects one adapter per capability. Selecting native_smb specializes
the schema to SMB and rejects SSH/FTP/SMTP/database requests. SSH remains separately
operational through explicit alternative native_ssh composition; no router, conflicting
double registration or future-family availability is added. M4-T04 adds separate [FTP metadata](ftp-adapter.md);
M4-T05 adds [SMTP metadata](smtp-adapter.md); M4-T06+ remain unimplemented.
See [protocols](protocol-capabilities.md), [security](security-model.md),
[budgets](execution-budgets.md), [state](state-transitions.md) and
[ADR 0023](decisions/0023-negotiate-only-smb-metadata.md).

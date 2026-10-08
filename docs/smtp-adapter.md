# SMTP metadata adapter (M4-T05)

**SMTP capability = greeting + safe ESMTP metadata only.** `tools.smtp.SmtpAdapter`,
`native_smtp`, supplies inspect_protocol/family=smtp, active_safe. Explicit AVAILABLE
registration asserts native implementation availability, never authorization or
reachability. Imports/default registry/discovery workflow/CLI remain inert.

## Reviewed greeting_ehlo_v1 profile

One independently scoped numeric TCP connection reads one initial reply. Only valid
220 enables the sole application request, exactly `EHLO [192.0.2.1]\r\n` (18 bytes).
Read one EHLO reply, synchronously close/abort and stop. The fixed synthetic
[TEST-NET-1 address literal](https://www.rfc-editor.org/rfc/rfc5737.html#section-3)
is an inspection label, not a claim of verified client
identity. It contains no operator/target/remote hostname, triggers no local hostname
lookup and cannot be overridden by a planner. Strict servers may reject the label;
record partial metadata without changing identity, retrying or falling back to HELO.

Framing, EHLO and extension syntax:
[RFC 5321 sections 4.1.1.1 and 4.2](https://www.rfc-editor.org/rfc/rfc5321.html#section-4.1.1.1).
Advertisements: [STARTTLS, RFC 3207 section 2](https://www.rfc-editor.org/rfc/rfc3207.html#section-2),
[AUTH, RFC 4954 section 3](https://www.rfc-editor.org/rfc/rfc4954.html#section-3),
[SIZE, RFC 1870 section 3](https://www.rfc-editor.org/rfc/rfc1870.html#section-3).
These standards describe broader clients; only greeting/EHLO is approved here.
No QUIT, HELO, NOOP, RSET, STARTTLS handshake or second request/fallback exists.
The profile neither verifies client/server identity nor tests advertised functionality.

Prohibited: AUTH (including empty/initial-response/anonymous attempts), usernames/
passwords/credential guessing/spraying/brute force, MAIL FROM, RCPT TO, DATA, BDAT,
mail/message/header/body submission, recipient/relay testing, VRFY/EXPN account/list
enumeration, ETRN/ATRN, arbitrary SMTP commands/options and exploitation. Advertised
AUTH LOGIN/PLAIN names or VRFY/mail-like unknown extensions remain data. They cannot
be dispatched. No SMTP client library, message/recipient object, credential or command
API exists. STARTTLS advertisement is sufficient; no TLSX duplication or downgrade.

## Service and authorization

Strict SmtpInput specializes common ProtocolMetadataInput: family=smtp, integer
port 1–65535, tcp, no defaults/extra fields. ActionRequest.target is an explicit
host/IP, never URL/CIDR. Credentials, sender/recipient/content, EHLO identity,
commands/options/TLS/contact addresses reject before contact/spending.

Trusted composition supplies 1–64 immutable normalized SmtpServiceBindings with
unique canonical subject/observed port, numeric IPv4/IPv6 contact and prior Service.
M4-T01 exact TCP SMTP relevance is required. Only smtp/submission names are
operational here. Recognized smtps or port 465 rejects at construction; native direct
port 465 also rejects before connection. Implicit TLS is outside this plaintext
profile; recognized relevance is not operational support. Other observed ports are
allowed only with exact smtp/submission identity, never inferred from port alone.

Request port/asset must match the prior Service; numeric subject equals contact.
Bindings/hostnames/advertisements confer no authorization or DNS relationship.
Current registry/policy/risk/schema/allowlists/dedup/shared-budget eligibility and
independent subject/contact ScopeValidator membership precede atomic reservation.
Registry and scope recheck after trusted start notification, immediately before
contact. Numeric family/flags pin destination; no DNS/proxy/redirect/address switching,
server-name follow-up or scope expansion. Exclusions/private gates apply independently.

SMTP/SSH/SMB/FTP and M4-T06 [database](database-adapter.md) are explicitly selected
composition alternatives under ADR 0003's
one-adapter-per-capability rule. No router/conflicting/default registration. Earlier
production files, domain/policy/runner/state/dependencies/CLI/workflow stay unchanged.

## Bounds and reply grammar

At most one connection and one 18-byte EHLO per admitted action. Retained aggregate
replies ≤min(8192, execution/shared per-action output limit), each line ≤512 bytes
including CRLF, each reply ≤64 lines. Every SMTP multiline line must carry the same
code; hyphen continues, space or bare code terminates. RFC code classes 2–5 and
second digit 0–5 are required. No FTP-style free continuation text. Strict UTF-8
text with no ASCII controls except HTAB stays data; extension labels/parameters
follow bounded ASCII EHLO syntax. First EHLO line is server greeting, never a feature.

Known STARTTLS has no parameters. AUTH mechanisms are 1–20 ASCII letters/digits/
underscore/hyphen; SIZE is optional 1–20 decimal digits. AUTH= legacy syntax, empty
AUTH lists, malformed/oversized parameters and conflicting repeated SIZE fail as
partial rather than guessing. Unknown and duplicate extension lines are retained
exactly in reported order. AUTH names are deduplicated in first-seen exact order.

Native/outer action timeout is min(configured timeout, remaining session time)
(default 30 seconds), with no per-read reset. Shared action/host/rate/concurrency/
output/session budgets and normalized serialized-output bound apply. Distinct subject
and contact both charge one host action. Rate counts admitted connections, each with
at most one EHLO; no packet-rate/OS buffer guarantee. Asyncio can buffer unread bytes,
but application capture stops at reply terminators and cleanup aborts unread data.

Malformed feature line/count/aggregate overflow discards that EHLO reply and retains
the already valid greeting. EOF/incomplete bounded reply retains available bytes.
Timeout/connection errors discard partial data under existing Failure semantics.
Cancellation propagates after synchronous socket/permit cleanup; no cleanup await.
Session expiry/normalized-output overflow discards output. No live interoperability
or Python 3.12 execution is claimed by offline tests.

## Normalization and failures

SmtpOutput extends ProtocolMetadataOutput with original Service, query_target/contact,
profile, completed/partial and at most one canonical ErrorInfo. Generic metadata
Observation/untrusted Evidence retain target/port/host/service/asset, source=native_smtp,
capability=inspect_protocol, caller UTC/execution, memory reference/locator and SHA-256
normalized snapshot digest. No inferred vulnerability, Finding or authenticated identity.

Snapshot contains exact multiline banner (joined CRLF), greeting code, conservative
full single-banner ESMTP Postfix/Exim product/optional numeric-version hints, exact
EHLO server text/ordered extensions, advertised AUTH names/SIZE value, STARTTLS
advertisement, collection flags/reply code/limitation and retained raw base64.
STARTTLS/SIZE advertisement is true or null/unknown, never a negative support claim.
SIZE 0 retains the reported no-fixed-limit value; omitted parameter remains unknown.
Authentication/mail/enumeration/TLS-negotiation flags are false. Original Service
and prior discovery product/version remain unchanged.

| Condition | Canonical outcome |
| --- | --- |
| Scope/schema/service/policy/dedup/budget denial | Existing policy/planner/budget Failure; no contact |
| Refused/unreachable/closed empty greeting | tool_execution_failed, fixed safe diagnostic |
| Native/action/session timeout | tool_timeout; no partial payload |
| Malformed/oversized greeting or normalized output | parse_failed; no observations |
| 4xx/5xx greeting | tool_execution_failed; no EHLO/auth fallback |
| Valid unexpected non-error greeting | Success[SmtpOutput], partial + parse_failed, banner only |
| Denied/auth-required/unexpected/malformed/incomplete EHLO | Success[SmtpOutput], partial + parse_failed, valid banner retained |
| Valid 250 EHLO | completed; server greeting plus reported extensions |

Caller owns original subjects and coherent ActionResult/state lifecycle; partial
ActionResult uses output.errors[0]. Adapter never mutates ReconState. Remote text
cannot alter commands/policy or introduce contacts. Offline fixtures and fake streams
assert the exact sole EHLO request, unread auth/mail prompts and no AUTH/mail/relay/
VRFY/EXPN/TLS dispatch, with real registry/policy/scope/budget/state/dedup regressions.

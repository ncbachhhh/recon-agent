# ADR 0025 — Native SMTP greeting and safe EHLO metadata

Status: Accepted. Date: 2026-10-08. Owning task: M4-T05.

## Context and decision

PLAN assigns a bounded safe capability negotiation profile and forbids mail,
recipient enumeration/relay abuse, credentials and arbitrary commands. M4-T01
supplies exact relevance/semantic contracts; existing native SSH/SMB/FTP adapters
establish explicit prior Service/numeric bindings and current policy/resources.

Approve greeting_ehlo_v1: one independently scoped numeric plaintext connection,
initial reply, only a valid 220 enables one fixed EHLO [192.0.2.1], one bounded
250 extension reply, then synchronous close/abort. The synthetic documentation
address literal is fixed inspection identification, never authenticated identity.
It avoids operator/remote hostname substitution or local DNS; strict rejection is
partial metadata without HELO/identity/retry fallback. No AUTH, mail/recipient/data,
relay/account/list enumeration, STARTTLS handshake or arbitrary-command API.

SMTP framing differs from FTP: every continuation line has the same code; support
code-only termination, finite CRLF lines/capture, native/outer/session deadlines and
existing shared budgets. First EHLO line is greeting, not an extension. Normalize
reported STARTTLS/AUTH/SIZE/unknown extensions with original Service and generic
untrusted Observation/Evidence/provenance; invalid or auth-required EHLO preserves
partial banner using canonical contracts. Relevance for smtps does not promise this
profile: reject smtps and port 465 before contact. No implicit TLS or TLSX duplication.

## Alternatives and consequences

Full smtplib/external clients provide credential/mail/fallback behavior unnecessary
for metadata. HELO fallback adds no ESMTP extensions. Configurable EHLO names or
local hostname resolution introduce unrelated parameters/runtime lookup; the fixed
numeric literal has a smaller boundary. TLS negotiation adds certificate/handshake
work outside PLAN's required advertisements. All are excluded.

The profile cannot verify advertised functionality, post-auth/post-TLS extensions,
implicit SMTPS or vulnerabilities. Denials/malformed metadata never escalate. Unknown
extensions are retained as data; legacy AUTH= syntax/conflicting SIZE is partial.
SMTP joins SSH/SMB/FTP as a selected alternative under one-adapter registry semantics;
no router, dependencies or earlier production changes. Only M4-T06 becomes READY.

## Security and validation

Primary SMTP/EHLO, STARTTLS, AUTH and SIZE sources are linked in
[SMTP contract](../smtp-adapter.md). Synthetic JSON/fake streams assert every outbound
byte is the sole EHLO request and never AUTH/MAIL/RCPT/DATA/VRFY/EXPN/STARTTLS.
Real policy/scope/budgets/state/dedup tests prove denial before contact/spending,
bounded failure/partial/cancellation and generic untrusted provenance. Full offline/
network-blocked/coverage/build/wheel/CLI/artifact gates precede DONE. No live SMTP
server/client/binary/provider, database or M4-T06+ work is performed.

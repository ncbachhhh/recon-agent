# ADR 0024 — Native pre-authentication FTP greeting and FEAT

Status: Accepted. Date: 2026-10-08. Owning task: M4-T04.

## Context and decision

PLAN permits a bounded banner/capability profile and assigns the read-only
pre-authentication command choice to this task. It explicitly excludes anonymous
login, credentials, files and arbitrary commands. M4-T01 defines exact observed
Service relevance, inspect_protocol and strict semantic parameters; ADR 0003 selects
one trusted adapter per capability. SSH/SMB establish native bounded transport seams.

Approve greeting_feat_v1: one scoped numeric control connection, initial reply,
only a valid 220 enables one fixed FEAT with no arguments, one bounded feature
reply, then synchronous close/abort. No authentication, file/data/command operations,
TLS handshake or fallback. A valid 120/other unsupported greeting is partial without
waiting; a denied/unsupported feature reply cannot cause login or alternative probes.

Keep existing explicit Service bindings, current registry/policy/dedup, independent
subject/contact scope and atomic shared budgets. Native asyncio uses numeric flags,
outer/native deadlines, finite reply/line/aggregate capture and synchronous cleanup.
Preserve original Service and generic untrusted Observation/Evidence with canonical
partial/failure contracts, caller provenance and explicit unknown TLS support.
Earlier production modules, dependencies, CLI and workflow remain unchanged.

## Alternatives and consequences

Banner-only receive would omit PLAN's safely available pre-authentication capability
information. SYST/HELP/OPTS and a full ftplib/client API add unnecessary commands or
credentials/files/data modes. External scripts may implicitly authenticate or create
data connections. TLS negotiation broadens this metadata profile. None is approved.
The fixed FEAT profile collects advertisements without testing advertised operations.

This narrow profile cannot inspect implicit FTPS or login-dependent features and
cannot verify identity, TLS availability or vulnerabilities. Unsupported/malformed
feature responses retain banner metadata with a canonical limitation; connection/
timeout failures retain no payload per existing contracts. Single selected FTP/SSH/
SMB adapters are composition alternatives; no router or later task starts here.

## Security and validation

Primary RFC framing/FEAT/TLS-advertisement sources and exact limits are linked in
[FTP contract](../ftp-adapter.md). Independent synthetic JSON and fake streams
assert every outgoing byte equals the sole FEAT request, prohibit auth/file/command
operations and leave later replies unread. Real scope/policy/budget/dedup/state
regressions prove denials before contact and preserve hostile metadata as data.
Full offline/network-blocked/coverage/build/wheel/CLI/artifact checks precede DONE.
No new dependency/client/live target; only M4-T05 becomes READY after closeout.

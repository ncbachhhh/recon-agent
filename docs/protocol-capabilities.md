# Protocol capability framework (M4-T01)

M4-T01 implements pure Service relevance selection and typed metadata contracts.
M4-T02 adds the standalone operational [receive-only SSH identification adapter](ssh-adapter.md).
M4-T03 adds the standalone [SMB2 negotiation adapter](smb-adapter.md).
M4-T04 adds the standalone [unauthenticated FTP adapter](ftp-adapter.md).
M4-T05 adds the standalone [SMTP greeting/EHLO adapter](smtp-adapter.md).
M4-T06 adds the standalone [database metadata adapter](database-adapter.md).
The M4-T01 selector itself remains pure:
no collector, dispatcher, network/process/Groq call or automatic action.

## Service → contract semantics

`tools.protocols.select_protocol_capability(Service)` revalidates the existing
normalized Service and returns one frozen ProtocolCapabilityContract or `None`.
Service.protocol is the normalized service name (Nmap already supplies this field);
no new banner parser or scanner command mapping is introduced. All matching is
exact ASCII case-insensitive lookup; whitespace, composite names and arbitrary
banner substrings are never stripped, split or searched.

| Family | Recognized Service.protocol names | Exact product hints |
| --- | --- | --- |
| SSH | ssh | OpenSSH, Dropbear |
| SMB | smb, microsoft-ds, netbios-ssn | Samba |
| FTP | ftp | vsftpd, ProFTPD, Pure-FTPd |
| SMTP | smtp, smtps, submission | Postfix, Exim |
| Database | mysql, mariadb; postgresql, postgres; ms-sql-s; mongodb; redis | MySQL/MariaDB; PostgreSQL; Microsoft SQL Server; MongoDB; Redis |

TCP is required. UDP and malformed copied/constructed Service records return None.
A recognized service name is mandatory on every port, including nonstandard ports.
Port-only fallback is **disabled**: PLAN calls ports hints, and does not explicitly
permit that fallback. Missing/unknown/unsupported names return None even with a
familiar port or recognized product. A known name on another family's usual port
uses the name; for example ssh on 445 selects SSH, http on 22 selects nothing.

Products only veto conflicts when the entire product value matches an explicit
hint above. Cross-family conflicts and different database identities return None.
MySQL/MariaDB and PostgreSQL/postgres are explicit aliases. Unrecognized product
text and version text are preserved but ignored; `OpenSSH 9.9` is not parsed for
identity. Unsupported/composite service names such as ssl/ssh, ssh/ftp and generic
database return None. Expanding these tables requires reviewed code/tests/docs;
remote evidence cannot extend the catalog. Selection is advisory relevance, never
proof of protocol correctness, safety or permission.

## Capability and operational availability

`protocol_capability_contracts()` returns five known contracts sorted by family.
Each contains a ProtocolFamily, existing CapabilityDescriptor for `inspect_protocol`
with active_safe risk, internal input/output schema references and explicit empty
secondary-target-field metadata. PLAN and CapabilityId already name inspect_protocol;
family parameters preserve semantic distinctions without inventing executable names.
Only the curated descriptor is planner-facing. Schema classes remain internal;
no executable, argv, NSE/script name, command, adapter ID or runtime object is exposed.

These contracts are **not** ToolAdapter or AdapterRegistration objects and have no
availability assertion. ToolRegistry stays immutable, explicit and empty by default.
`is_known_capability('inspect_protocol')` is true. In an empty registry, `has_capability`
is false and `capability_definition`/`resolve` return tool_unavailable. M4-T02 permits
explicit native_ssh registration; M4-T03 permits native_smb and M4-T04 native_ftp
as explicitly selected alternatives. M4-T05 adds native_smtp; M4-T06 adds native_database.
Each selected adapter rejects other families through its specialized schema. The
operational catalog does not list missing implementations. No fake adapter is registered in production.

Registry cardinality remains one selected adapter per capability (ADR 0003).
Trusted protocol composition must respect that boundary and validate the selected
family/profile; SSH, SMB, FTP, SMTP and database are explicit alternatives,
with no generic router.
Known database relevance does not promise a safe non-authentication exchange:
M4-T06 reviews MySQL/MariaDB greetings and PostgreSQL SSL support only;
Redis/MongoDB/SQL Server reject without contact.

## Request/result boundary

Pure `domain.protocols` provides ProtocolFamily, strict frozen ProtocolMetadataInput
and ProtocolMetadataOutput. Input has only family (ssh/smb/ftp/smtp/database), strict
port 1–65535 and tcp transport. ActionRequest.target remains the independently scoped
host; there are no secondary destinations, credential/authentication parameters,
protocol commands or arbitrary options. Operational adapters must bind family/port/transport
to actual observed Service and independently authorized numeric contact. Request
claims alone cannot establish relevance or authorization.

Output holds family, existing Service, at most 128 metadata Observations and 256
untrusted Evidence records. It validates unique IDs, inspect_protocol evidence
attribution, service asset ownership and matching source/execution/evidence links.
It generates no observations or evidence. Hostile text remains untrusted data;
no source/time/artifact/execution is invented. Empty metadata is structurally valid;
ActionResult owns success/partial/failure and ReconState owns session lineage/lifecycle.
The envelope is a common contract, not a protocol parser, finding or contact proof.

```text
Service observation → protocol capability candidate
                    → ActionRequest
                    → ActionPolicyValidator
                    → trusted adapter (SSH, SMB, FTP, SMTP or database explicitly selected)
                    → atomic budgets + independent current contact checks
                    → normalized metadata observations/evidence
```

Selection never calls policy, adapter resolution/execution, runner or planner,
consumes budgets, records actions, mutates Service/Scope/ReconState or performs I/O.
Every future execution still requires current capability/risk/schema/scope/history/
budget eligibility and an atomic charged reservation; a candidate is no bypass.
Test-only metadata bindings exercise existing registry/policy denials without any
collector or dispatch. This reconciles PLAN's initial fake-module/scoped-dispatch
wording with the requested M4-T01 abstraction-only boundary.

See [tool contracts](tool-contracts.md), [security model](security-model.md),
[data model](data-model.md) and [ADR 0021](decisions/0021-protocol-relevance-contracts.md).

## Operational extension (M4-T02)

The original known-contract catalog and selector still assert no availability or
authorization. Explicit SshAdapter uses the SSH descriptor and specialized semantic
SshInput/SshOutput schemas. Only the receive-only server identification profile is
operational; no algorithm/key/authentication/command path exists. Current policy/
scope/dedup/shared budgets remain mandatory. M4-T03 SMB has a separate operational
profile; M4-T04 FTP and M4-T05 SMTP are described below. Database has the
M4-T06 reviewed profiles below.
See [SSH contract](ssh-adapter.md).

## Operational extension (M4-T03)

Explicit SmbAdapter supplies strict SMB-only semantic schemas and a single fixed
SMB2 NEGOTIATE profile for selected dialect/signing/GUID metadata. It has no session
setup/authentication/shares/files/command path. SSH/SMB are reviewed alternatives
under the existing one-selected-adapter registry rule, not conflicting registrations
or an automatic router. M4-T04 FTP, M4-T05 SMTP and reviewed M4-T06 database
profiles are described below. See [SMB contract](smb-adapter.md).

## Operational extension (M4-T04)

**FTP capability = unauthenticated metadata only.** Explicit native_ftp/FtpAdapter
specializes family/port/tcp to prior observed FTP Service bindings. One current
scoped numeric contact reads greeting and sends at most one fixed FEAT. No USER/
PASS/anonymous login, credentials, directory/file/data operations or arbitrary
commands/options. Generic untrusted provenance and canonical partial failures
retain limits. FTP joins SSH/SMB as a composition alternative, without a router.
See [FTP contract](ftp-adapter.md) and [ADR 0024](decisions/0024-preauthentication-ftp-feat.md).

## Operational extension (M4-T05)

**SMTP capability = greeting + safe ESMTP metadata only.** Explicit native_smtp
uses prior normalized smtp/submission Service/numeric contact bindings and strict
family/port/tcp input. Current policy/scope/dedup/shared budgets gate one greeting/
fixed EHLO exchange. Advertised STARTTLS/AUTH mechanisms/SIZE/extensions remain
untrusted facts; no AUTH/mail/relay/VRFY/EXPN/TLS negotiation or arbitrary commands.
Known smtps relevance and port 465 reject this plaintext profile before contact.
SMTP is a selected alternative with SSH/SMB/FTP; no router/default registrations.
See [SMTP contract](smtp-adapter.md) and [ADR 0025](decisions/0025-greeting-only-smtp-ehlo.md).

## Operational extension (M4-T06)

Explicit native_database uses required canonical database_type in addition to
family=database/observed port/tcp. Exact prior Service aliases and current policy/
scope/dedup/budgets gate a receive-only MySQL/MariaDB packet or one fixed PostgreSQL
SSLRequest support signal. PostgreSQL version remains unavailable/partial, with no
StartupMessage/auth negotiation. Redis/MongoDB/ms-sql-s are relevance-only and reject
before contact/spending. No DB driver/credentials/queries/data/mutation path or generic
router. See [database contract](database-adapter.md) and [ADR 0026](decisions/0026-preauthentication-database-metadata.md).

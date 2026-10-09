# Safe Nuclei profile policy (M5-T02)

This task implements pure review metadata in `domain/nuclei_policy.py` and the
finite catalog/classifier in `policy/nuclei_profiles.py`. It does **not** connect
profiles to ActionPolicyValidator, ToolRegistry, Nuclei argv or execution.
The M5-T01 adapter still denies every scan. A successful assessment has
`execution_authorized=false`; it is neither ApprovedAction nor ProcessSpec.
M5-T03 owns source inspection, profile dispatch integration, actual byte verification,
scope/contact containment, resource limits and audited denials. Findings remain M5-T04.

## Reviewed classes and named profiles

The initial repository envelope permits two classes, both ACTIVE_SAFE:

| Class | Permitted behavior and interpretation |
| --- | --- |
| http_response_metadata | One HEAD at the authorized target root; record reported response status/headers |
| http_security_header_presence | Same single HEAD; record presence/absence of security headers without claiming a verified vulnerability |

Exact behavior is HTTP, HEAD, target_root, request_count=1, response_parts=headers
and status, features=(). All fields are required. The complete effective behavior
must be established by trusted manual review; class labels, tags, severity,
signatures and scanner metadata cannot substitute for that review. Any additional
feature is excluded, including unknown features. No custom headers/Host, request
body, raw HTTP, cookies/authentication, retries, redirect/host-redirect, extra paths,
helpers/DSL/preprocessors, dependent requests, workflow, payload/fuzzing, code,
filesystem use, secondary contacts or OAST/interactsh is eligible. Reading response
body/raw data and all other methods/destinations/counts also deny.

| Profile | Allowed classes | Default policy metadata |
| --- | --- | --- |
| safe | Both reviewed classes | Yes |
| http_metadata | http_response_metadata only | No |
| http_headers | http_security_header_presence only | No |

`safe` is the catalog's named default, not an implicit scanner/input default.
Existing NucleiInput still requires an explicit profile; select(None), unknown,
case/whitespace aliases and raw paths/URLs/options deny. The repository owns these
finite definitions. Operators choose names and supply explicit reviewed manifests;
they cannot create profiles, extend allowed classes, relax behavior or add exclusion
exceptions through configuration. Every profile shares the same global exclusions.
There is no severity/tag-based selection or automatic template enumeration.

The class table separately lists prohibited exploit, credential_attack, destructive,
out_of_band, payload_fuzzing, remote_mutation and code_execution. Unreviewed
http_body_exposure, http_path_discovery, tls_checks, dns_checks, network_checks,
headless, file, workflow, javascript, custom and unknown are excluded. All other
class names are unknown and denied. This is a conservative initial subset; it does
not relabel other reconnaissance methods as exploitation or approve a whole upstream
category. Any additional class requires reviewed repository work, not a profile flag.

## Review basis

These are repository policy decisions based on primary vendor descriptions, reviewed
2026-10-10; no Nuclei template package or template file was downloaded or installed.
The [HTTP protocol documentation](https://docs.projectdiscovery.io/templates/protocols/http/basic-http)
describes template-controlled methods, paths, redirects, headers, bodies and sessions.
That breadth motivates the narrow root HEAD and feature-free response envelope.
The [payload documentation](https://docs.projectdiscovery.io/templates/protocols/http/http-payloads)
describes request expansion/wordlists, which this policy excludes.
[OOB documentation](https://docs.projectdiscovery.io/templates/reference/oob-testing)
describes automatic external interaction through Interactsh; it is excluded regardless
of a template's severity/non-intrusive label.
[Template signing documentation](https://docs.projectdiscovery.io/templates/reference/template-signing)
describes integrity/author verification and notes helper payload files are not covered
by template signatures. A signature is not behavioral review or execution permission;
no signature-verification implementation or key setup is introduced in this task.
No claim of live scanner compatibility follows from this documentation review.

## Operator-reviewed provenance and version contract

`TemplateIdentity` requires a canonical opaque template ID, the sole permitted source
repository `projectdiscovery/nuclei-templates`, an exact 40-character lowercase Git
revision, exact three-component package/engine versions and a lowercase SHA-256
content pin. There are no paths, URLs, executable/options, tag or severity fields.
`latest`, mutable branches, wildcard/range versions, missing/ambiguous pins, arbitrary
repositories and unreviewed engines deny. The initial engine policy remains 3.4.10,
the foundation's reviewed probe/format version, not a latest-version recommendation.

`TemplateReview` additionally supplies the allowed class, full effective behavior,
opaque operator review reference and aware UTC review time. Reviews are trusted
operator/application composition inputs, never planner or remote scanner data.
A catalog contains at most 128 unique template IDs within one coherent repository
revision/package/engine snapshot. Duplicate IDs (even identical), mixed snapshots,
invalid reviews or disallowed behavior cause canonical ConfigurationError with fixed
safe diagnostics. Frozen records/tuples, revalidated detached nested identities and
an immutable sorted mapping preserve the trusted snapshot.

`NucleiProfileCatalog()` has **zero reviewed concrete templates**. It provides the
named policy profiles and denies assessment of every concrete template until trusted
reviews are supplied. Test manifests use fictional IDs/pins/hash descriptions, not
production approvals. No upstream template is claimed to be reviewed by those fixtures.
This task reviews the behavioral envelope and provenance rules rather than shipping
or downloading a template set.

`classify_template(class_name, behavior)` checks the global class/behavior table.
`select(profile)` returns pure fixed profile metadata.
`assess(profile, TemplatePolicyCandidate)` first revalidates the candidate, then checks
classification, an existing trusted review, **exact equality of every identity,
class and effective-behavior field**, and membership in the selected profile.
It returns canonical planner_validation_failed Failure on denial, or a typed
TemplatePolicyAssessment with original pins, review reference/time, ACTIVE_SAFE risk
and execution_authorized=false. It performs no filesystem/YAML/hash/signature read,
network/DNS/availability lookup, scope check, budget/state change or scanner call.
A presented digest is still metadata: M5-T03 must compute it from trusted loaded
bytes and inspect effective behavior before any scan, never trust a self-attestation.

## Updates, unknown behavior and contact containment

There is no refresh/download/update/mutation API. Changed template ID, repository,
revision, package version, engine version, bytes/digest, class or behavior invalidates
the old review. No unchanged ID/tag/signature or more permissive profile can bypass
the comparison. An operator must explicitly re-review exact new content and behavior,
record review provenance/time and construct a new coherent catalog. That new review
still cannot broaden the repository classes/envelope; the old catalog remains intact.
Engine changes require separate repository review as well.

Any unreviewable dependency, dynamic behavior or secondary destination is excluded.
The metadata policy has no target input and grants no scope or contact authority.
The actual M5-T01 adapter continues to require centralized current query/action scope,
budget/history eligibility and context bindings, then denies before contact/spending.
Its offline candidate parser, unverified evidence/provenance and bounded/error semantics
are unchanged. Before future dispatch, M5-T03 must prove reviewed source content and
engine behavior cannot escape independently authorized numeric contacts, including
resolution/redirects/secondary destinations; otherwise scans must remain disabled.
A metadata assessment or post-capture scope filter cannot provide that guarantee.

## Setup and validation

SETUP REQUIRED: None. Offline work needs no binary, templates, additional dependency,
API key, signing keys or system package. No credentials or template installation is
required now. Future enforcement/operator provisioning must record exact reviewed
artifacts and contact-containment evidence; arbitrary installation commands or mutable
"latest" packages cannot establish this review. No setup is performed automatically.

Focused policy tables plus unchanged M5-T01/registry/action-policy/dedup regressions
cover safe/prohibited/unknown classes, all named subsets, every forbidden extra feature,
malformed/omitted behavior, each provenance/version/hash change, immutable/repeated
snapshots and explicit updates. Runtime guards prohibit network/DNS/scanners, policy
side effects and source reads. Pure policy and adapter boundary tests prove eligible
metadata cannot generate argv/contact/spend; complete baseline and installed-wheel
checks also exercise unchanged parser/error/provenance/timeout behavior.
See [ADR 0028](decisions/0028-nuclei-profile-policy.md).

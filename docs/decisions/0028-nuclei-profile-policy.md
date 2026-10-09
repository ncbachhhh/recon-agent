# ADR 0028 — Finite inert Nuclei classes and pinned operator reviews

Status: Accepted. Date: 2026-10-10. Owning task: M5-T02.

## Context and decision

PLAN assigns risk/class/profile/provenance/update policy to M5-T02 and actual
scanner/source/destination enforcement to M5-T03. M5-T01 supplies a deliberately
disabled adapter with offline unverified candidate ingestion. An upstream template
label, severity or signature cannot prove effective behavior is safe or scope-bound.

Define two ACTIVE_SAFE classes within a single explicit HTTP root HEAD/one-request/
status-and-headers/no-extra-features envelope: response metadata and security-header
presence. The named safe default permits both; http_metadata/http_headers are subsets.
Every profile shares global prohibited/unreviewed/unknown exclusions. Default is
policy metadata; NucleiInput remains explicit and the adapter remains byte-identical.

Operators supply trusted manual review records with exact official repository/revision,
package/engine version/content SHA-256, class, complete effective behavior, review
reference/time. An immutable coherent catalog has zero concrete reviews by default.
Standalone pure classification/assessment checks exact identity and behavior against
those records and produces explicitly non-authorizing metadata. No filesystem/YAML/
source authenticity or signature verifier, byte resolver, registry/ActionPolicyValidator
integration, ProcessSpec, dispatch or target policy is implemented here.

Changes invalidate the old pin, requiring explicit review and a new coherent catalog;
new reviews cannot override repository exclusions. Unknown/extra behavior or secondary
contact is denied, not inferred safe. M5-T03 must inspect actual loaded content and
prove independent contact/budget containment before execution; an attested digest or
class name does not grant that proof. Evidence remains unverified under M5-T01 and
Finding creation remains M5-T04.

## Alternatives and consequences

Rejected: severity/tag allowlists, broad "misconfiguration" or "technology" categories,
trusting signatures as behavioral approval, arbitrary operator catalogs/paths/options,
mutable automatic refresh, shipping unreviewed concrete templates or integrating
scanner enforcement early. These could hide payloads/helpers/OAST/secondary contact
or silently broaden behavior. Exact source pins plus complete trusted review and a
finite envelope make drift and unknowns deterministic without implying execution.

This initial policy is intentionally narrower than all authorized reconnaissance.
There is no claim that arbitrary upstream header templates meet it. Synthetic fixture
manifests are inert test metadata, never production approvals. Future tasks may need
an explicit policy review for broader classes; no such task starts here. No template
package, scanner, dependency, signing key or credential is needed now.

## Validation and source basis

Primary vendor HTTP/payload/OOB/signing descriptions motivated the review; exact links,
class/profile tables, operator update rules and limitations are in the
[policy contract](../nuclei-profile-policy.md). Offline tables cover exclusions, missing/
unknown behavior, each provenance drift, snapshots and non-authority. Unchanged
adapter regressions prove every named profile still denies without dispatch/spend.
Full/network-blocked/coverage/build/wheel/inert CLI/security gates are mandatory.

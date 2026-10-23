---
name: bb-finding-triage-gate
description: "Use when deciding if a finding is submission-worthy."
version: 1.0.0
author: skii, Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [bug-bounty, triage, validation, severity, idor, ssrf, redteam]
    related_skills: [triage-validation, bb-attacker-path-proof, report-writing, bb-hunt-phase-pipeline]
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | None shipped — this SKILL.md is self-contained |
| 3 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-2 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] Protocol confirmed before any work started

# Finding Triage Gate (submission-worthiness)

Classify a demonstrated finding into DIG / CANDIDATE / NA / MERGED before any report is written.

Companion to `triage-validation`'s 7-Question Gate, on a different axis:

- **7Q** — is this a real bug at all?
- **This gate** — what does the evidence actually demonstrate about attacker reach, and is that above the platform floor?

Run this gate on **what the evidence shows**, not on what the report claims. The author's severity label is not authoritative.

## When to Use

- A finding looks confirmed and you must decide: report it, pursue it further, or archive it.
- Its impact depends on a value, identifier, role or delivery the attacker may not be able to obtain.
- You are about to call something CRITICAL because the mechanism is real.
- A platform downgraded, N/A'd or disputed a finding and you want the standard it was applying.
- The candidate is a missing rate limit, an external-only SSRF, a live-looking credential, a DoS, or a session swap.

Not for: deciding whether a bug is real at all (that is the 7-Question Gate in `triage-validation`), or drafting the report (`report-writing`).

---

## The So-What test (run first)

> "What does an attacker ACTUALLY do with this?"

The answer must be concrete demonstrated impact: data leaked, money moved, accounts taken, code executed, admin access — or a clean chain to one of those that the evidence shows working.

A report that asserts CRITICAL but demonstrates only info disclosure with "could lead to" framing fails.

**No-impact CANDIDATE rule (this user's standard):** A proven primitive (e.g. unsigned SAML assertion accepted, endpoint exists) is NOT enough to write a report. The finding must show concrete attacker-attainable harm — data accessed, session obtained, privilege gained. "CANDIDATE" means one specific prerequisite is unresolved, not that the primitive is the deliverable. If the prerequisite (valid user, valid token, device serial) cannot be acquired within this session, the finding stays CANDIDATE and does not ship. Inform the user with the exact missing prerequisite and stop; do not draft prose, take screenshots, or polish.

---

## Buckets — exactly one per finding

- **DIG** — in scope, passes the So-What test with real evidence; OR a demonstrated Low/Info finding that has an evidence-supported escalation path into High+/Critical (state the chain).
- **CANDIDATE** — the live vulnerable primitive is proven AND one specific attacker prerequisite is unresolved, with concrete target-side acquisition paths still untested (or an exact vendor-verifiable result blocked by a documented safety/scope constraint). Internal work order only, never submission-ready.
- **NA** — (a) out of scope, (b) low impact with no escalation path, (c) unproven or theoretical mechanic, (d) required prerequisite already searched and disproved, or too vague to bound acquisition work. The reason line must say which case.
- **MERGED** — same root cause AND same operation as another finding (duplicate or subset). Fold unique relevant evidence into the canonical, then mark this one MERGED and point to it. A merge cannot upgrade a CANDIDATE to DIG unless the combined evidence proves the prerequisite. If the new report contains material evidence that could change the canonical's disposition, do not merge — assess combined evidence.

---

## CANDIDATE gate — all five must hold

1. **Primitive proven** — the vulnerable mechanic itself is demonstrated live with concrete evidence. For cross-account access: A acting as attacker reaches or changes B's object *when given B's identifier*. A claimed or inferred primitive is not enough.
2. **Exactly one bounded prerequisite** — name the literal missing value, state, role or action (victim UUID, token leakage, input delivery, lower-role reach). One question, or one tightly coupled set.
3. **Material conditional impact** — if that prerequisite is reachable, the already-proven mechanic plausibly reaches Medium or higher. Record it as conditional severity, never as proven severity.
4. **A target-side acquisition path remains genuinely untested** — list/search/autocomplete, sharing UI, public profile, redirect, error, GraphQL, JS bundle, webhook, related object, predictable identifier structure.
5. **Not already disproved** — earlier work has not exhausted those sources and shown the prerequisite unreachable.

**Validation-constrained variant.** Criterion 4 also passes when the primitive is proven and the one remaining question is exact and vendor-verifiable, but cannot be settled safely or permissibly. Examples: the only consumer is an internal support viewer; proof would need bulk access to other users' objects, privileged actions on third-party resources, a real paid transaction, or a role behind non-bypassable KYC. Name the exact consumer, role, state or action evidenced by the target, explain why one yes/no result establishes Medium+, and state the constraint. This is not permission to preserve vague speculation.

A bounded cross-entity confirmation on **at most three non-owned objects** is permitted testing, not a constraint — do not route a finding here merely because proof touches another user's object.

CANDIDATE forbids general escalation: resolve the named prerequisite first. No final screenshots, no report polish, no adjacent hunting until it resolves. Disproved by a genuine bounded search → disproved. Prevented by environment or access → BLOCKED, not disproved.

---

## Owned-test-account trap (IDOR / cross-tenant / "access victim's X")

Owning both accounts is a **test harness, not an attacker capability**. A cross-tenant finding has TWO independent preconditions; the report must demonstrate BOTH:

1. **Authorization broken (mechanic)** — A can reach B's resource given its identifier. Owning A+B proves this; fine.
2. **Identifier obtainable (delivery)** — an attacker who controls only their own account, or nothing, can learn a victim's identifier: sequential/low-entropy/predictable IDs they can enumerate, or an id leaking somewhere attacker-reachable (list/search/profile/autocomplete endpoint, JS bundle, error message, redirect, public page).

Reading the victim's id/email/token out of the victim test account because you own it is **not** a source. A UUIDv4/v5 or other high-entropy opaque token is not enumerable by itself. Sequential or otherwise-predictable IDs are an acceptable delivery even if you first noticed the pattern using your own accounts, because a real attacker enumerates the same range.

**Routing:** proving #1 alone never earns DIG. CANDIDATE when #1 is concretely evidenced, #2 is the exact unresolved prerequisite, plausible attacker-visible sources for #2 remain untested, and resolving #2 would reach Medium+. NA when #1 is not actually proven, #2 is only a vague hypothetical, the identifier is high-entropy and relevant acquisition sources were already exhausted, or conditional impact stays below Medium.

Do **not** answer the delivery question by reading many unrelated accounts or "a meaningful range" to show scale — that is bulk collection of third-party data. Characterise enumerability with the three-object bound plus a rate/space argument instead.

---

## Rate-limit / brute-force / lockout findings

A missing or bypassable brute-force control is a **hardening miss = NA** until the report carries it to an outcome against the live target.

Fails (NA): "endpoint never locks / no CAPTCHA / unlimited attempts" with no valid secret ever guessed; "rate limit keyed on client-supplied `X-Forwarded-For`, bypassable by rotating it" with no account actually brute-forced; a brute force that cannot even start because no valid target exists (no enumerable admin email, no pending OTP). If the report's own scope note concedes "not a demonstrated ATO", it is NA — it is conceding it never reached impact.

Passes (DIG) when the missing control **is** the impact, i.e. unthrottled guessing directly extracts value: a low-entropy, unthrottled code space returns valid values with real redeemable balance (gift-card/voucher/promo-code redemption, redeemable token, discount code). Show a real hit, or the enumeration rate + space size that proves the codes are reachable.

A guessable low-entropy secret with a long or absent expiry, PLUS a demonstrated unthrottled path, PLUS a valid target the attacker can actually drive the guess against = the bar for DIG.

---

## External-only SSRF

An SSRF whose final tested ceiling is fetching arbitrary **external** hosts, with internal/link-local/RFC1918/IMDS reach and file read already tested and not shown, is **NA (external-only)**, Bugcrowd `SSRF > External` = P4/P5. Trusted egress IP, trace headers, attacker-controlled outbound credentials, public-host response read, or external-only CRLF do **not** raise it.

CANDIDATE when the server-side request primitive is concretely proven and a specific plausible internal reach, internal response, protocol smuggling or file-read path remains genuinely untested — name that exact prerequisite and its first tests. DIG requires the material path demonstrated.

Honest taxonomy is preserved: an SSRF rejected for submission is still an external-only SSRF, never relabelled into something else to fit a floor.

---

## Credential / exposed-secret findings

- Secret-shaped text alone is not a finding. DIG requires sound minimal liveness or authentication evidence **with a negative control**. Do not require data access, account takeover or a privileged action, and do not use the credential beyond that minimum permitted check.
- Untested but credible credential material from an in-scope first-party source is **CANDIDATE** — its unresolved prerequisite is liveness, resolved before general validation or polish.
- **Liveness ≠ authority.** A live secret proves it is real, not that it grants anything. Assess authority separately (see `bb-attacker-path-proof`).
- A disabled-account or disabled-client response supports a disclosure claim only when live controls prove the published artefact is owner-issued and tied to that real account or client. Account-state handling before secret verification does not prove the secret authenticates. Speculative future re-enablement cannot inflate impact.
- Confirmed revoked, invalid, fabricated, placeholder or unrelated third-party value = **NA**; state the negative control that established it.

---

## Floors — checked before writing, regardless of technical severity

- **Pure DoS / availability loss is rejected at every severity.** Mixed chains pass only when independently proven confidentiality, integrity, authorization, credential compromise, privilege gain or takeover meets the floor.
- **Never execute or intensify DoS to apply the policy.**
- **Session swap** (putting a victim into an attacker-controlled account/session) is not takeover: it needs a demonstrated Medium-or-higher consequence.
- **Low-sensitivity read-only exposure** needs material private content or concrete attacker value — not merely an undocumented field or internal endpoint.
- **Low/Informational does not ship** on most programs: record it with the reason instead of filing it.

---

## Infrastructure and configuration disclosure — the shapes that do not ship

This class is technically real, evidence-backed, and still non-passing. It is the most common false
deliverable on a hardened estate, because every host leaks *something* and each leak reads like a finding.
Recognise the shape early:

- **Origin hostname behind a CDN/WAF** — a block page, debug header or error body naming `origin-…` or a
  cloud default hostname (`<app>.azurewebsites.net`). Naming the origin is the precursor to edge bypass,
  not the bypass; without the bypass test it is NA.
- **Internal / non-production / tenant hostnames in a shipped bundle** — corporate-domain hosts, `qa-*` or
  `-dev` names on the apex, an identity-provider tenant, a third-party project id. The disclosure is real,
  but the disclosed host is normally outside the allowlist so the exploit step cannot be taken. Informational.
- **A production developer exception page, stack trace or build path.** Most programs exclude "verbose error
  messages without proof of exploitability" by name, so triage applies that exclusion first. Ship it only
  when the trace itself carries usable material (a live credential, a connection string), never as the
  misconfiguration alone.
- **A served source map with no secrets in it.** Full application source is not a vulnerability while it
  holds no credential; mine it for endpoints and sinks instead of filing it.
- **A publicly reachable dev/QA environment whose data layer correctly refuses anonymous access.** A live
  config disclosure plus a verified-closed rule set is still informational — and the verified negative must
  be stated in the write-up, not omitted.

**Rule:** record these as evidence and as the reachability/coverage map, mark them non-shippable with the
reason, and keep hunting for a class the program actually pays for. Do not present a set of them as the
deliverable, and do not let their count stand in for progress — a lead that proves a paying sink with one
untested prerequisite outranks six shippable-looking disclosures.

**Do not pause a coverage sweep to ask permission between batches.** Report what landed and continue to the
next batch on your own judgement until the budget or the candidate hosts are exhausted. A go-ahead request
per batch is not wanted; stopping to state a genuine boundary (a write against a live system, an
off-allowlist target) is required.

---

## Status discipline

| Reality | Status | Meaning |
|---|---|---|
| Searched live, documented, not reachable | **NOT REACHABLE** | Disproves the claimed path. Keep the sources searched. |
| Policy, safety, KYC, payment, scope, WAF, geography, tooling or unavailable resource | **BLOCKED** | Never a disproof. Record the exact missing proof and the pass condition. |
| Proved and reachable | **REACHABLE** | Feeds the next step in the chain. |

Never convert a blocker into a negative result. Never convert a negative result into a coverage win.

---

## S3 / public cloud storage buckets — do not assume open = finding

A publicly listable or readable cloud storage bucket is not automatically a security issue. Many services require public buckets by design:

- **Enterprise OTA distribution** — iOS `itms-services://` manifests and IPA files must be publicly accessible for device installation. An S3 bucket hosting `manifest.plist` + `index.html` installer pages + `.ipa` files is the standard OTA deployment pattern, not a misconfiguration.
- **Static asset CDN** — buckets serving images, CSS, JS, or firmware files to the public internet are intentional.
- **Server-side encryption** (SSE-S3/AES256) is not a defense against public access — it protects data at rest on AWS's infrastructure, not against unauthenticated HTTP reads.

**Before classifying an open bucket as a finding, answer:**
1. Does the bucket's content pattern match a known intentional use (OTA distribution, CDN, public assets)?
2. Is there actual sensitive data in the objects — API keys, credentials, PII, internal documents, private keys, configuration files? The bucket being open is not the finding; the *data being sensitive and exposed* is.
3. Can you download a sample of the objects and verify they contain secrets? Listing alone is not proof.
4. Are object ACLs individually restricted even though the bucket listing is public? (Common pattern: listing public, read-access denied on sensitive objects.)

**A bucket with index.html installer pages, manifest.plist files, and app binaries is an OTA distribution endpoint.** Without demonstrated sensitive data (hardcoded credentials in the binary, PII, internal documents), report it as informational or not at all. The user's standard: "maybe the bucket intention to be public... is there any sensitive information there? prove it."

**After finding hardcoded credentials in an IPA from a public bucket, triage the credential, not the bucket.** The bucket may be intentional OTA distribution. The finding is the hardcoded credential embedded in the app binary, not the bucket's accessibility. Verify the credential against the provider's live API with a negative control before claiming impact. Content that is AR/marketing/educational material shown in retail stores is not sensitive — verify the credential actually unlocks something confidential, not just public-facing content.

## Common mistakes

- Treating the author's severity label as evidence — evaluate the demonstrated mechanism instead.
- Submitting with a hedged severity ("confirmed IDOR with potentially High impact") instead of resolving the identifier-acquisition prerequisite first. Hedged severity reads to triage as "theoretical": route it to CANDIDATE and go and get the acquisition path, or file the honest lower severity.
- Polishing a CANDIDATE into a submission-ready report before the prerequisite is tested.
- Merging a "duplicate" that actually adds material evidence, or filing one report for two separate root causes (two payouts lost).
- Guessing intent: record `DOCUMENTED AND MATCHES` / `DOCUMENTED BUT EXCEEDED` / `CONTRADICTED BY FIRST-PARTY MATERIAL` / `NOT DOCUMENTED` with the first-party URL and access date, rather than asserting "by design" or "intended".
- Marking a finding unproven when what happened is that the test was blocked by scope, tooling or rate limiting.
- **Calling a registration endpoint a finding because it creates accounts without authentication.** Registration endpoints are public by design — that is how users sign up. The question is not "does it work without auth" (it is supposed to) but "does it do something harmful": issue session tokens without email verification, allow mass account creation with no rate limit or CAPTCHA, or return a password reset token that bypasses the email flow. Distinguish between the endpoint's intended behavior and an actual control failure. If the session token it issues is restricted (can't access sensitive endpoints), that is by design — not a vulnerability.

- **Calling a public website's own API a finding because it exposes data the website already shows.** A GraphQL or REST API that powers a public-facing page, accessed with headers derivable from the page's own JS/bootstrap config, is the website working as designed — not a vulnerability. The auth headers (`ag-cid`, `ag-platform-id`, `ag-identity-token`) are public by necessity: the SPA needs them to function. Finding them in the JS bundle or bootstrap config and calling the API with them proves only that you can replicate what the SPA already does. The finding is not that the API exists or that you found the headers — it is whether the API exposes data or operations the website itself does not expose to an unauthenticated visitor. Before investing time in schema probing, field enumeration, or request-format reverse-engineering, answer: "What does this API give me that I cannot already see or do on the public website?" If the answer is "nothing different" (same activity catalog, same pricing, same city list), stop — you are using the public API as designed, not finding a bug. This trap is especially common with GraphQL endpoints that require custom headers: the headers feel like "auth" so finding them feels like a bypass, but they are merely the gateway's routing context, not a security control.

---

## Related

- **`triage-validation`** — the 7-Question Gate that runs first (is it a real bug at all).
- **`bb-attacker-path-proof`** — builds the prerequisite ledger this gate consumes.
- **`report-writing`** — only for findings that reach DIG.
- **`bb-hunt-phase-pipeline`** — the coverage evidence and per-shape verdicts that feed this gate.

## MANDATORY ON INVOCATION — PROTOCOL RESTATMENT (END OF FILE)

You have reached the end of this SKILL.md. The invocation protocol below is identical to the one at the top of this file. If you are reading this, the full skill context is loaded — confirm the checklist.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | None shipped — this SKILL.md is self-contained |
| 3 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-2 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] Protocol confirmed before any work started

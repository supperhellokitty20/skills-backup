---
name: js-enum-skill
description: Enumerate authorized web-application JavaScript, discover and reconstruct source maps with exact provenance, catalog client-exposed APIs, triage embedded credentials, and produce source-grounded pentest plans or exposure reports. Use for scoped JS recon and source-map analysis; it does not authorize credential use or live exploitation.
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `agents/openai.yaml`, `references/artifacts.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# JavaScript Enumeration

Turn public, in-scope frontend artifacts into reproducible security evidence. Keep passive discovery, static hypotheses, and dynamically confirmed findings distinct.

## Authorization boundary

- Record apex, allowed subdomains/CDNs, assessment date, rate limits, authenticated areas, and output location before network work.
- Treat downloading public JavaScript and advertised source maps as passive collection. Keep request rate low and bounded.
- Do not use discovered credentials, send them to third parties, access customer objects, or invoke state-changing endpoints without explicit authorization for that action.
- Use tester-owned accounts and data for dynamic authorization tests. Stop after proving boundary crossing.
- If WAF or Cloudflare blocks application traffic, document blocker. Do not bypass it unless scope explicitly permits bypass.

## Workflow

### 1. Preserve discovery inputs

Collect each source separately before deduplication:

- Certificate-transparency subdomains from supplied sources such as `crt.name` or `crt.sh`.
- Historical URLs with `gau` for apex and in-scope subdomains.
- Current page HTML, script tags, framework manifests, service workers, preload links, and dynamically loaded chunks.
- Archived JavaScript snapshots when current files disappeared.

Normalize URLs only after retaining raw values and discovery source. Remove fragments, resolve relative paths against referring page or JavaScript URL, and preserve meaningful query strings. Keep separate lists for all URLs, JavaScript candidates, live JavaScript, map candidates, and archived references.

### 2. Fetch reproducibly

For every fetched artifact record URL, final URL, referring artifact, discovery source, timestamp, HTTP status, content type, byte count, and SHA-256. Save body under a deterministic name such as SHA-256 of URL. Reject HTML error pages mislabeled as JavaScript or source maps.

Use `gau` as historical coverage, not proof that URL remains live. Keep current and archived results separate.

### 3. Discover every source-map URL

Inspect JavaScript for line and block forms of `sourceMappingURL`, including inline data URLs. Resolve references with URL semantics against parent JavaScript URL. Also test conventional `<javascript-url>.map` only when request is in scope and rate-safe.

Document every discovered map URL, including inaccessible, invalid, vendor-only, duplicate, and noncontributing maps. For archived JavaScript, preserve original JavaScript URL, archive snapshot URL, snapshot timestamp, resolved map URL, and current map status.

### 4. Reconstruct source safely

- Parse map JSON and record `version`, `file`, `sourceRoot`, `sources`, `sourcesContent`, and parse errors.
- Treat `sourcesContent` as recoverable source. A map containing only mappings does not reproduce original source; label it incomplete instead of inventing code.
- Resolve `sourceRoot` and source names, URL-decode once, strip bundler prefixes, and reject absolute paths, drive letters, `..`, NULs, and traversal after normalization.
- Exclude `node_modules` and bundler runtime by default, while recording that exclusion. Retain first-party files.
- Hash every recovered file. When same logical path has different content, keep canonical copy plus hash-named variants; never silently overwrite.
- Create bidirectional provenance: every map to files and every reconstructed file to all maps, original source names, and hashes.

Read [references/artifacts.md](references/artifacts.md) when creating reconstruction inventories or reports.

### 5. Enumerate client-exposed API design

Search reconstructed and bundled code for:

- API base URLs, route constants, fetch/Axios wrappers, GraphQL operations, WebSockets, callbacks, and presigned storage requests.
- HTTP method, resolved path expression, query/body fields, custom headers, cookies, bearer tokens, refresh flow, SSO/OAuth/Cognito configuration, and error logging.
- Client-supplied identifiers such as `user_id`, `application_id`, `document_id`, tenant/company IDs, transaction IDs, notification IDs, and product IDs.
- Privileged-looking fields such as status, role, owner, approver, compliance flags, price/amount, fee, eligibility, redirect URI, and audit actor.
- Telemetry paths carrying OTPs, credentials, PII, signed URLs, or query parameters into analytics, console, local storage, or mobile bridges.

Catalog one row per call site with source file and line, method, raw expression, resolved endpoint when possible, authentication context, identifiers, data class, and test hypothesis. Counts are inventory facts; heuristic tags are not findings.

### 6. Triage credential candidates

Combine pattern scanning with code context. Classify each candidate as public identifier, publishable browser key, test credential, privileged secret, token, signature, private key, or false positive. Record source file, source-map provenance, build/snapshot age, intended exposure, privileges implied by code, and rotation clues.

Never call a string a usable secret based only on format. Validation requires provider attribution and explicit authorization. Prefer non-mutating identity/status endpoints, least privilege, one request, no customer-data access, and exact response capture. Separate `confirmed valid`, `confirmed rejected`, `blocked before authentication`, and `inconclusive`.

### 7. Build dynamic test matrix

Prioritize source-indicated trust boundaries:

1. Authentication, OTP/reset, refresh/revocation, SSO state/nonce/PKCE, account enumeration.
2. Two-account BOLA/BFLA across every object identifier and tenant selector.
3. Workflow and mass-assignment controls for approvals, offers, consent, status, eligibility, audit actor, and privileged flags.
4. Presigned upload ownership, expiry, replay, MIME/magic bytes, key isolation, and retrieval authorization.
5. Payments, recovery, bank changes, callbacks, fee/amount integrity, idempotency, and bounded race tests in sandbox.
6. Signed internal links, canonicalization, replay window, referrer/history/analytics leakage, and object binding.
7. CORS, cache separation, parser ambiguity, method overrides, error leakage, rate limits, and gateway version drift.
8. Browser storage, telemetry, WebView/native bridges, and cloud identity-role permissions.

For object endpoints use Alice-owned object, Bob-owned tester object, anonymous, expired/revoked token, conflicting path/body selectors, and duplicate request. Expected result for cross-user access is denial with no data or persistent change.

### 8. Report evidence honestly

Label each item `confirmed`, `likely`, `hypothesis`, `inconclusive`, or `not vulnerable`. Route knowledge, public OAuth IDs, browser analytics keys, and bypassable client validation are not vulnerabilities without demonstrated server-side or confidentiality impact.

Reports must state scope, date, collection method, complete map URL inventory, exact map-to-file provenance, affected artifacts, request/response evidence, blockers, and cleanup. Keep raw sensitive evidence access-controlled; generate a shareable redacted copy when needed.

## Completion criteria

- Every discovered JavaScript and source map has a disposition.
- Every reconstructed file maps to at least one exact source-map URL and SHA-256.
- Conflicting source versions remain preserved.
- API catalog covers every observed call site, not only route constants.
- Secret candidates have contextual classification and validation status.
- Dynamic tests separate authorization failures from WAF/pre-auth blocks.
- Final report separates source exposure, hypotheses, and confirmed impact.
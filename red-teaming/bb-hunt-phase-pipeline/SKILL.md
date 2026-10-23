---
name: bb-hunt-phase-pipeline
description: "Use when running a multi-phase coverage sweep."
version: 1.0.0
author: skii, Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [bug-bounty, methodology, coverage, workflow, evidence, orchestration, redteam]
    related_skills: [bb-finding-triage-gate, bb-attacker-path-proof, bb-workspace-layout, projectdiscovery-recon, bb-methodology]
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/mobile-app-api-recon.md`, `references/saml-acs-testing.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# Hunt Phase Pipeline

An evidence-first hunting workflow splits work into phases so that **no single agent both finds a finding and blesses it**. Each phase has an owner, a handoff artefact and a stop condition. Keep the boundaries; the value is in them, not in any single prompt.

## When to Use

- Starting or resuming a structured hunt across a target with more surface than one pass can cover.
- Running a coverage sweep and you need a defensible record of what was and was not tested.
- Delegating hunting work to subagents and you must protect the live browser session.
- Wrapping up a phase and you need the handoff to survive context compaction or a new session.
- A hunt is being resumed after a break and you must recover what was already tried.

Not for: a single quick probe of one endpoint, or deciding whether a specific finding is submission-worthy (`bb-finding-triage-gate`).

---

## Phase map (and who may write the report)

| Phase | Owns | Hard boundary |
|---|---|---|
| 0 Recon | Minimum unauthenticated surface map: scope hosts, live hosts, shallow routes, ≤20 JS files, endpoint/operation candidates | No vulnerability tests. Candidates are hypotheses. |
| 1 Access | Authenticated access, owned resources, account/object graph | Setup and navigation are not findings — flag anomalies for the sweep |
| 2 Sweep | The coverage engine: every eligible endpoint shape gets a verdict | Zero depth before coverage |
| 3 Close-out | Audit the handoff, freeze report bytes, release resources | No hunting, no triage, no new target traffic |
| 4/5 Browser walk + critical hunt | Live-session browser work, serial | Server-side leads fan out to stateless workers |
| 6 Triage | First-line classification (see `bb-finding-triage-gate`) | No screenshots — nothing is proven yet |
| 7 Validate/escalate | One worker per finding | CANDIDATE findings resolve their prerequisite first |
| 8 + 8a Verify + independent escalation | Second, independent pass; the pre-gate pass is read-only, writes only in its own output root, never reads sibling escalation branches, verifies the report hash | Never edit the report it reviews |
| 9 Live triage gate | Final independent reproduction and honest classification | Single report writer |
| 10 Duplicate convergence | Compare one final report against the candidate manifest | Read-only, no target access |

**Exactly one phase writes the report.** Earlier phases produce evidence, verdicts and ledgers.

---

## Coverage contract (sweep)

The objective is **coverage, not bug count**: give every eligible endpoint shape a relevant verdict, and file only what confirms.

- **Eligibility is mechanical** — union the endpoint catalogue, browser traffic, authenticated and unauthenticated captures, API/GraphQL documents, JS/source-map candidates and SPA route manifests, then filter by class sink/state. A high-value operation static analysis found is never excused because the browser walk did not visit it.
- **One verdict per exact shape**, never hand-normalised: `confirmed` | `dead` | `partial` | `skipped`.
- **Evidence binding:** `confirmed` and `dead` require existing evidence bound to the exact shape. `confirmed` needs attack evidence; add baseline evidence for differential, authorization, workflow or business-logic claims, and verification evidence for state-changing or owner-observed claims. A missing prerequisite makes a result **`partial`, never `dead`**.
- **A challenge is not absence:** a 403/406, captcha, login HTML or unexpected HTML page gets one browse/CDP or in-page replay before you record it; otherwise `partial`.
- **Injection is opportunistic and lowest priority** — never run systematic fuzzing before coverage is terminal.
- Budget roughly 90–120 minutes per sweep phase; a truthful partial map beats a padded completion, so record unreached work instead of leaving it silently pending.

### Controller order (mandatory)

1. Baseline health → 2. non-destructive browser coverage → 3. bidirectional access control → 4. reversible state changes → 5. **disruptive tail** (logout / session invalidation, password+email change, reset completion, MFA counters, races, idempotency bursts, scale checks).

"Preserve the account for closeout" is **not** a reason to skip an applicable disruptive check.

### Bidirectional access-control matrix (two identities)

1. A→A and B→B owner controls (prove the harness works)
2. B's object through A
3. A's object through B
4. Optional unauthenticated replay
5. Reversible write marker, owner-side verification, restore

Both directions are required. "A could read B" without the B→A control is half the evidence.

### UNAUTH is productive, not degraded

Downloadable secrets, exposed GraphQL/metrics/actuator/backup services, unauthenticated object access, pre-auth data exposure and CI/supply-chain leaks all pay without an account. Never treat the unauthenticated lane as a lesser run.

---

## Chain pass (do not skip)

The highest-severity result is usually **invisible to per-class agents**: upload + permissive CORS, SSRF + open redirect, disclosure + IDOR, leaked secret + accepting API. After coverage, run a combination and hypothesis-driven pass, and give every confirmed report an explicit **chain-value** line — including `standalone` when no chain applies. If the evidence cannot answer the chain question, record that gap; do not declare completion.

---

## Compaction-safe ledgers

A finding that is not in a file gets retested; a dead end that is not recorded gets re-explored. Negative knowledge deserves the same care as wins.

- **One angle per file**, written the moment the angle is chosen — before testing. Never start a second angle while the first has no file. Fields: angle / hypothesis / what was tried (path refs) / result / status on the **last line**: `DEAD` | `PARTIAL` | `SKIPPED` | `CONFIRMED-<SEVERITY>`. Extend `PARTIAL`/`CONFIRMED` in place instead of reopening.
- **Append the lead row** (id, surface, url/field, class, status `queued`) **before** dispatching a worker, so compaction cannot lose in-flight work; re-read the ledger to recover state.
- **Track coverage, not just findings:** append-only events `{url, surface, auth_state, actions, status: pending|tested|blocked}` — append `pending` before testing and a terminal event after the verdict.
- **Portfolio, not assignment:** maintain mechanism families with status `unexplored|active|blocked|partial|confirmed`. When workers converge on one family, redirect the next available one to an underexplored family. Reopen a blocked family only for a materially new mechanism, input path, consumer or chain construction.
- **A prior `DEAD` is not a veto on a new hypothesis**, and a peer's result is advisory — never authority to skip an untested angle. A materially different mechanism, context, identity, route, method, payload family or stronger independent proof earns a retest.
- Re-derive state **from disk** after workers finish; in-memory variables are stale.
- Reserve filenames for phase summaries so they never collide with angle files.

---

## Worker (subagent) isolation contract

Delegate only **stateless, session-independent** work: SSRF on a surfaced URL/webhook/image field; injection on a reached parameter; infrastructure on a newly discovered host; server-side upload follow-through; business logic reproducible over the API.

- **Never let a worker touch the shared authenticated browser/CDP session.** Concurrent navigation corrupts the walk. Give each worker a copied credential (cookie/token) and its own HTTP client and OOB listener.
- Cap concurrency at **3–4**. The cap is concurrency, not total rounds: synthesise finished results, then launch the next round.
- Workers return a structured verdict only (result, severity, endpoint, evidence path, one-line impact, provenance). They never write report files, never write shared ledgers, never acquire browser profiles (unless explicitly authorised for a stateless lead), and never contact the user.
- Before recording `CONFIRMED-CRITICAL`, run an **independent adversarial pass** that tries to disprove reachability, prerequisites, reproducibility, scope and claimed impact.

---

## Session loop driver

The phase map above is the territory; this is the loop that walks it repeatedly inside one session. State lives on disk, so an iteration is resumable and the loop is safe to interrupt or compact.

**One iteration:**

1. **Read state from disk** — `scope.md`, `angles/*.md`, coverage events, candidate manifest. On resumption, first apply `bb-workspace-layout`'s artifact-inventory and non-overlap workflow: substantively audit saved corpora, reconcile completion claims with raw logs, refresh full scope/policy, and document lane ownership before new target traffic. Re-derive every iteration; never trust in-memory state or a prior narrative as evidence.
2. **Select exactly one angle** from the mechanism-family portfolio (underexplored family first). Write the angle file *before* testing, not after.
3. **Load the skill set + policy-bounded template coverage** — reuse saved valid fingerprints and completed template runs before producing traffic. Where evidence is missing, capture headers and body with redirects disabled; follow each Location only after exact scope, exclusions and ownership review, without forwarding credentials to a new origin. Run only reviewed applicable nuclei templates when policy permits, using the corrected operational allowlist, an explicit aggregate rate allocation, a finite request budget, absolute artifact paths and sequential batches of at most ten hosts. Save template/input counts, stderr, exit status and completion evidence; empty findings alone do not establish coverage. A generic example rate is never permission to exceed the program's limit. Under no-aggressive-scan or bug-class exclusions, narrow or skip the affected templates and document the gap instead of imposing a broad scan. Load tier-ordered platform skills (cap 8) plus the class skills the angle needs after this coverage decision.
4. **Hunt** — walk the loaded class checklist. Fan stateless work to subagents (cap 3–4), each with a copied credential and its own OOB listener; never the shared authenticated browser session.
5. **Verdict per exact shape** — `confirmed | dead | partial | skipped`, evidence bound to the shape.
6. **Triage gate, then path proof** for anything `confirmed`.
7. **Independent adversarial pass** — a separate subagent tries to disprove reachability, prerequisites, reproducibility, scope and claimed impact. It never edits the artefact it reviews.
8. **Record** — angle status line, lead-ledger row, coverage event, `evidence/<finding>/{raw,interpreted}`.
9. **Report** only on pass.
10. **Chain pass** once coverage is terminal.

**Loop-entry rules:**

- An angle with no file blocks starting a second angle.
- A prior `dead` is not a veto on a *materially* different mechanism, context, identity, route, method, payload family or stronger independent proof.
- Rotate rather than grind: 20 minutes without progress moves endpoint → host → class → family.
- Stop conditions: coverage terminal, every family `blocked`/`confirmed`, or the deadline. `"find more"` from the operator is **not** one — assume they are right, walk three more class checklists, document the negatives.
- A missing tool, credential or listener is a `BLOCKED`/`partial` result with the gap recorded, never a clean negative.

**Durability:** session-driven by default. Promote to a durable board (one card per angle, so a restart resumes instead of restarting) or scheduled re-entry only once the angle ledger exists — a board created before the ledger has nothing to route.

**Environment note (this machine):** a single Hermes profile (`default`) exists, so a board loop serializes and there is no cross-profile fan-out — real parallelism is subagents, not a profile fleet. Resolve ProjectDiscovery binaries by absolute path (`/Users/skii/go/bin/{subfinder,httpx,nuclei,katana,gau,naabu,interactsh-client}`); the `PATH` `httpx` is the unrelated Python package.

---

## Closeout integrity

- **Report edits invalidate a prior chain proof.** Hash the exact report bytes before any structural repair; if bytes change, re-run the chain pass on the same evidence only.
- **Report provenance is creation-time metadata.** Keep it verbatim; never restamp a report because a later phase read, renamed, merged or escalated it.
- **Repair structure only from evidence.** Fill omitted headings or normalise severity syntax; never invent impact, evidence or attribution. Weak impact is recorded as "needs evidence before triage".
- **Handoff must enumerate** untested high-value shapes, pending classes, blocked retries, partial findings, chains not attempted and dead ends.
- **Release only what you own**, by owner prefix, and only after the handoff artefacts exist. Never release by slot number, never wipe warmed browser profiles, never delete captured flows.
- **Deadline contract:** the soft deadline is the end of discovery — stop starting new work and write the summary from evidence already collected. Never start a command whose timeout can exceed the hard deadline. Use `UNKNOWN` for unresolved fields.

---

## Common mistakes

- Consider applicable template coverage before class-specific manual probes, but never re-run completed scans or violate policy to satisfy a pipeline stage — policy exclusions, aggregate traffic limits and verified prior coverage determine whether to run, narrow or skip it.
- Depth before coverage, then a padded coverage claim.
- Converting a blocked test (no browser, no OOB, no credentials, no account) into a negative result. Mark it `BLOCKED` and preserve the exact missing proof.
- **Your own fan-out can deny you the answer, and then look like a clean negative.** Sweeping all 93 inventoried endpoints of one Akamai-fronted API family (`huddle.nba.com/yppapi`) in a single 1-rps pass flipped *every* response to edge 403 - including the impossible-path control. A four-request sample minutes earlier had shown a clean `401 Bearer` vs `404` control differential. The differential was destroyed by the burst, and reading those 403s as "no missing auth" would have been a fabricated negative. Pace fan-out sweeps in small batches with pauses, and place the impossible-path control FIRST and LAST in every batch: **if the control is denied, discard the batch instead of reading the endpoints**. Note that the deny persists after the burst stops (re-checked 45s later, still 403), so it is not a retry-immediately condition.
- Letting one agent both find and bless a finding, or letting the report writer be the finder.
- Screenshots at triage time, or synthesised/re-painted evidence at any time.
- Losing the sweep's negative knowledge, so the next session re-tests the same dead ends.
- Releasing resources before the handoff exists, or with a broad cleanup that kills another target's adjacent resource.
- Mistaking normal application behavior for a vulnerability. An endpoint that creates accounts, issues session tokens, or sends password resets is often working as designed — registration, login, and password-recovery endpoints are public by necessity. Before writing anything up, ask: "what can the attacker do with this that they could not do by using the feature normally?" A finding must demonstrate an authorization bypass, data access, or capability the attacker should not have — not the happy path of a public endpoint.
- Going in circles on a blocked angle. When you have exhausted the approaches you can reach without a credential, tool, or environment change, try a materially different approach before declaring the angle dead. Switch technique classes (REST → SAML/OIDC → method tampering → version detection → status endpoints → source maps → default creds → user enumeration → browser fallback). Only after 3+ genuinely different technique classes all produce the same blocker do you say so clearly in one sentence and stop. Do not re-probe the same endpoints with different parameter guesses, do not write up normal behavior as a finding, and do not narrate the dead ends. Record the blocker in the lead ledger, update AGENTs.md, and present the user with the exact missing prerequisite.

- Continuing when stuck is not the same as re-probing the same endpoints. The user saying "Continue" or "staus" means find a new angle, not grind the same one. Rotate technique class, not just parameter value.

### API registration vs external auth providers — and how to bridge the gap

When you register a user via a REST API endpoint (POST /api/v1/users), that creates a user in the application's database — but it does NOT create the user in the external identity provider (Auth0, Okta, Azure AD, Cognito). The auth provider identity is created separately, typically through:
- The web signup flow (which calls both the API and the auth provider)
- The password reset flow (which creates the auth provider identity when the user sets a password)
- An admin provisioning flow

**Hunting implication:** registering via the API gives you a session token for the application's own auth layer, but you CANNOT use that account to login through the OAuth/OIDC-based web login until the auth provider identity exists. The password reset email from Auth0 is what creates the auth provider account — clicking the link and setting a password there makes the account usable for web-based authentication.

Also: the API registration session token is often deliberately restricted — it's a pre-onboarding session that can't access sensitive endpoints. This is by design, not a vulnerability. Use it for basic reconnaissance (user ID format, error messages, endpoint discovery), but don't expect it to unlock IDOR testing. You need the full auth provider session for that.

### Unblocking the Auth0/OAuth login gate without asking for credentials

When the web app uses Auth0 (or any OAuth/OIDC provider) and you need a full session token:

1. **Register a user via the API** (`POST /api/v1/users` with the public app key). Save the returned session token and password_reset_token.
2. **Trigger a password reset email** via `GET /api/v1/users/reset_password?email=<email>&lang=en` (or the equivalent endpoint). This tells the auth provider to create the identity and send a reset link.
3. **Ask the user to check their email, click the reset link, and set a password.** Do NOT try to guess or ask for the password in chat. Once they confirm, you can login via the browser.
4. **Drive the browser through the login flow** — type the email, click Continue, type the password from step 3. Use `interceptor type` with the password field ref. The browser session then has the full auth provider session with cookies and tokens that the SPA uses.
5. **Extract the live Bearer token** from `interceptor net log` immediately after login — it appears as `Authorization: Bearer <uuid>` in the API calls the SPA makes. This is the token to use for API testing.
6. **Use `interceptor override` for in-flight parameter tampering** on subsequent SPA requests to test IDOR.

**Do NOT:**
- Ask the user to type the password in chat or save it to a vault while you wait
- Try to brute-force or guess the password reset token format
- Give up on authenticated testing because the API registration token is restricted — the whole point is to bridge to the full auth provider session via the password reset flow

### Dynamic testing through the browser (do this BEFORE static API probing)

"Did you do dynamic test?" — the user expects the browser to be the primary API-testing surface, not a fallback. Static curl probes miss the actual request shapes the web app sends (headers, cookies, token format, exact parameter names) and cannot test for CSRF, DOM-based issues, or in-session parameter tampering.

**Workflow order (mandatory):**

1. **Open the app in the browser and authenticate.** Use the interceptor browser, not curl. The browser session gives you the real auth tokens, cookies, and request/response flow.
2. **Capture the live network traffic first.** `interceptor net log --format json` gives you the exact API calls the app makes — method, URL, headers, request body, response. Parse this JSON to discover endpoints you would never guess from the JS bundles or APK alone.
3. **Extract the Bearer token from the live traffic** (it may differ from one you extracted from localStorage or a previous curl call — the web app may rotate tokens per page load). Test endpoints with this live token immediately.
4. **Use `interceptor override` to modify query parameters in-flight** before the server sees them. This tests whether the server uses the parameter value or the auth token to identify the resource owner — the definitive IDOR test that curl cannot replicate for SPA requests.
5. **Only then drop to curl** for endpoints the browser does not call, or for batch/automated testing of parameter permutations you already discovered.

**Why this order matters:** The web app's SPA may send different auth tokens, extra headers (`X-Trace-Id`, `sentry-trace`, `baggage`), or cookies that curl does not send. A 404/401 from curl does not mean the endpoint is inaccessible — it may mean the SPA sends a required header or cookie you omitted. Conversely, a 200 from curl may use a stale/restricted token while the browser's live session has a full-privilege token that unlocks sensitive endpoints.

### Session token hierarchy and authorization boundaries

Different auth mechanisms grant different API access levels. When testing, know which token type you hold — and that the browser's live Bearer token may differ from one you extracted earlier:

| Token source | Auth header | Typical access | Endpoint examples |
|---|---|---|---|
| API registration | X-Api-Key | Restricted pre-onboarding | User creation, basic profile |
| Auth0 JWT (Bearer) | Authorization: Bearer <jwt> | Full API access | User profile, subscriptions, premium |
| API session token | X-Api-Key | Medium access | Profile CRUD, some settings |
| Web app live Bearer (from `net log`) | Authorization: Bearer <uuid> | Same as JWT but may be a short-lived session token | Same as JWT — test with this first |

**Key trap:** The web app's Bearer token (visible in `interceptor net log` as `Authorization: Bearer <uuid>`) is often a **different** token from the Auth0 JWT you extracted from localStorage. It may be a short-lived session token that the app exchanges the JWT for. Test with BOTH — the session token may have different scope than the JWT. Extract both from the browser and exhaust what each can reach.

Rule: after obtaining ANY session token, exhaust what it can reach before chasing new unauthenticated angles. A registration token may be restricted, but it still reveals API structure, error messages, and user data model through validation errors. The protected endpoints the token unlocks are where actual vulnerabilities live. Spend 30 minutes testing authenticated endpoints through the browser before returning to unauthenticated recon.

---

## Supporting references

- `references/saml-acs-testing.md` — procedure for testing SAML ACS endpoints with unsigned/forged assertions.
- `references/mobile-app-api-recon.md` — discovering API endpoints through community-maintained OpenAPI specs, OIDC provider enumeration, Cognito pool testing, and mobile app auth flow analysis.

## Related

- **`bb-finding-triage-gate`** / **`bb-attacker-path-proof`** — the verdict and path-proof gates this pipeline feeds.
- **`bb-workspace-layout`** — where each artefact belongs on disk.
- **`bb-methodology`**, **`projectdiscovery-recon`** — recon and hunting method either side of the sweep.

## MANDATORY ON INVOCATION — PROTOCOL RESTATMENT (END OF FILE)

You have reached the end of this SKILL.md. The invocation protocol below is identical to the one at the top of this file. If you are reading this, the full skill context is loaded — confirm the checklist.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/mobile-app-api-recon.md`, `references/saml-acs-testing.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

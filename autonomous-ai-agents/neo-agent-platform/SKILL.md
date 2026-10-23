---
name: neo-agent-platform
description: "Use when asked to do recon on a target: Neo KB + subagents."
version: 1.0.0
author: skii, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [neo, agent-swarm, subagents, knowledge-search, orchestration, delegation, security-agents]
    related_skills: [projectdiscovery-toolchain]
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/knowledge-collections.md`, `references/orchestration-patterns.md`, `references/subagent-methods.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# Neo Agent Platform

Operating contracts for the **Neo / agent-swarm** security-agent platform: how to retrieve from
its global knowledge collections, how subagent *methods* are acquired and composed, and how
ownership and verdict authority are decided.

None of the tools named here are Hermes tools. `knowledge_search`, `acquire_subagents`,
`list_subagents`, `delegate_task({task, subagents})`, `update_working_memory`, `run_command`,
`render_report` and `create_issue` belong to Neo. Use this skill when reasoning about or writing
instructions for work that executes *inside* Neo — not to plan Hermes-side work.

## Standing directive: recon routes through this skill

When the user asks to **do recon on a target** — "recon this", "run recon on X", "start
reconnaissance", "enumerate the attack surface", "map the target's assets" — follow this skill's
guidance for that task. Load it before the first tool call, not after.

Those recon requests **originate in this Hermes session, so the work itself still executes with
Hermes tools** (`terminal`, `browser_exec`, `search_files`, `delegate_task`). Neo's tools are not
callable here. What carries over is the *discipline*, and it is not optional:

- **Ownership first** — decide root-retain vs. delegate before choosing any tool, not after.
- **Method contract on delegation** — every `delegate_task` names the specialized methods the
  outcome needs; `sandbox` alone is never a contract for specialized work.
- **Verdict rule** — any sub-task whose success condition is a vulnerability verdict must carry an
  independent verification step. Never promote unverified evidence.
- **Scope intake creates durable project state.** Follow `bb-workspace-layout` and its lead/handoff contract on every scope: create/read exact `AGENTs.md`, `scope.md`, `reports/lead-ledger.jsonl` and `reports/LEADS.md` before traffic. Leads include all target/service/stack/fingerprint/route/API/functionality/JS/map observations, negatives and blockers, not just suspected bugs. Ingest each stage and checkpoint the handoff before pausing; another session must resume from disk without repeating discovery.
- **Discovery is a producer** — build the canonical live-target artifact **once** and pass its path
  to every consumer; do not let each stage re-run subfinder/httpx. Prefer installed ProjectDiscovery CLI stages directly; reserve custom code for offline artifact handling and verification.
- **Rank the estate before deep-diving, and probe self-service test environments first.** After the
  httpx sweep, rank hosts by reachable-surface evidence rather than by name recognition: a scope
  row whose instruction field explicitly permits self-service test accounts, and whose stack differs
  from the flagship app (e.g. an ASP.NET UAT template beside a Rails estate), is the highest-value
  authenticated target — registration is authorized per-asset, the environment is less hardened,
  and shared-templates UAT codebases are prime cross-tenant access-control ground. Flagship hosts
  behind SSO-only gates get a one-request posture check and move to blocked-on-prerequisite.
- **Provenance** — record the exact command or request behind every artifact, and keep raw output on
  disk while the context stays bounded.
- **Verify without trusting success flags** — confirm artifacts by listing and reading them back.
- **Manual-probe fallback** — a zero-result scan is not a clean baseline, especially behind
  WAF/CDN. Record positives, negatives *and* blockers.
- **Authorization is per-asset, not per-action.** Once an asset is inside an authorized program's
  scope, the ordinary engagement actions against it — creating one throwaway test account,
  registering and logging in, submitting a form, exercising a documented API — are already
  authorized. Do not stop to ask for those; the user reads the pause as not knowing the job. Ask
  only about genuinely new scope, third-party infrastructure, or irreversible and
  other-user-affecting actions (deleting or overwriting real data, mass writes, anything that
  touches an account that is not yours). Use one account, and state plainly which one you made.
- **Ownership, not hostname, decides whether an asset is the target's.** A wildcard authorizes the
  program's *own* assets. A discovered subdomain whose CNAME lands on third-party SaaS — docs
  platform, status page, CDN, support desk, or another vendor's product entirely — is that
  provider's infrastructure: record the CNAME/redirect and pivot. Do not test it merely because its
  name matches the in-scope wildcard. Resolve the CNAME before the first request on any
  wildcard-discovered host, and record such names as out-of-bounds-by-ownership in `scope.md`.
- **A self-service test account and a gated program application are different authorizations.** A
  signup that issues an account you own is an ordinary engagement action. A partner / developer /
  sandbox program with human review is a business application: it needs a **truthful identity and a
  truthful purpose**, and a false name, fabricated company, or stated intent you do not hold is
  misrepresentation — not covered by the program's safe harbour, and it can cost the researcher
  their standing. Never submit one on someone else's behalf on those terms, even when asked.
  Relatedly, establish whether self-registration exists *before* promising authenticated testing:
  read the login bundle for a user-signup flow and probe the standard auth paths. Enterprise
  SSO-only front ends (SAML/OIDC, one `/login` route) have none, so the honest answer is "the
  program team or the partner program is the only way in".
- **Find the asset where authenticated access actually exists, and sequence the work so you keep it.** Read the identity architecture out of the client bundle (the env/auth config object naming the OIDC base URL, the CIAM base, the redirect URI and the published client id) plus `/.well-known/openid-configuration` on each in-scope identity host, then check which of those hosts actually answers you: on a shared-WAF estate a documented identity host can be edge-denied while a sibling host's own account system returns 200, and the reachable sibling is the real target. Do the read-only identity recon first and the interactive auth paths (`/signin`, the authorize endpoint) **last and once** — repeated hits on those paths can escalate a path-level edge denial into an IP-wide block that also denies the user's own browser on the same egress, which destroys the human-in-the-loop sign-in you were counting on. Keep the fabricated-`redirect_uri` reflection check to one request per issuer, and never answer a block with proxy/IP rotation, fingerprint spoofing or retries: record it as a blocker, because the block is a control and evading it forfeits the safe-harbour footing.
- **An account you cannot create is a blocker to record, not a control to defeat.** When the program does authorise self-signup but every registration path demands an SMS-capable phone number, and the app's no-verification identity path answers with an anti-bot challenge, the deliverable is the blocker plus the concrete unblock options for the user — not effort spent getting around it. Never write code to solve a bot challenge, and never accept a verification code in chat. Distinguish a **platform-wide switch** from an identity-specific refusal before writing the blocker: re-run the same gated call with a second, different input. An identical refusal for every input is a platform flag (registration or an onboarding flow disabled server-side) — a clean blocker to re-check on a later date — whereas a refusal that varies by input is about your account and needs a different unblock. Confirm the site still serves, so the flag is not confused with a host-level block, and never treat the flag itself as something to get around. Reading the client bundle for the guest / auto-generated-user path (`isGuest`, `createAutogeneratedUser`-style provisioning) is still worth doing: it tells you which identity tiers exist and what is reachable without verification, even when you cannot create one yourself. Same shape for a required download — a mirror behind an interstitial is a manual step to hand back, not a puzzle.

The pairing: this skill supplies the process, `projectdiscovery-toolchain` supplies the exact
flags and pipeline shape, and `bb-workspace-layout` supplies where every artifact is written. The
`hunt-*` skills supply bug-class depth once the surface is mapped.

If a request only *mentions* Neo, agent-swarm, `knowledge_search`, or `acquire_subagents` without
asking for recon, this directive does not apply — answer the Neo question from the contract
references instead.

## When to Use

- Writing a prompt, task, or runbook that will execute inside Neo / agent-swarm
- Deciding which Neo subagent method a piece of security work needs
- Retrieving from Neo's global knowledge collections (and interpreting a failure correctly)
- Deciding whether Neo root should retain an assignment or delegate it
- Debugging "the index doesn't exist" or "my acquired tool isn't available" in Neo

Don't use for: Hermes's own `delegate_task`, Hermes skills, or PD tool flags
(`projectdiscovery-toolchain` covers those).

## knowledge_search — the working invocation

```
knowledge_search({
  action:    "search",
  indexName: "<collection>",
  isGlobal:  true,          // REQUIRED for shared collections
  query:     "<natural language>",
  limit:     N
})
```

Return shape: `{ success, indexName, query, isGlobal, total_found, results[] }`, each result
`{ file, lines, language, score, content }`.

Four gotchas, all empirically established — treat them as rules, not advice:

1. **`isGlobal: true` is mandatory.** A bare `indexName` resolves against user-owned indexes
   only and returns `{"success":false,"exists":false,"suggestion":"Index not found…"}`. This is
   the single most common wasted call.
2. **`action: "status"` is unreliable for globals.** It has returned `exists:false` for healthy
   indexes (`nuclei`, `httpx`, `XSS`) that `search` resolves fine in the same session.
   **Determine availability by attempting a real `search`, never by trusting `status`** — even
   though the platform's own error message tells you to check `status`.
3. **A `no index found: <name> (global)` error means "try a different retrieval path," not "the
   topic is undocumented."** 11 of 35 listed collections do not resolve.
4. **Never react to a failed search by calling `index_knowledge`.** Creating or seeding a missing
   global collection is an unauthorized side effect, not a fix. Record the unavailability.

Large payloads spill to `.tool-output/knowledge_search__<slug>__<call-id>.json` with a
`_spilled_to` pointer. Read that exact path — never re-invoke the producing tool just to re-read
its output, and pass any `nextCursor` verbatim.

Fan out independent index queries as **sibling calls in one response**. They have no
cross-dependency, so sequential turns are pure latency.

## Subagent model (the part that is counter-intuitive)

A subagent supplies a **method** — tools, operational instructions, skills, runtime behavior.
It is **not a worker** and **not an ownership grant**.

```
acquire_subagents({ subagents: [{ id, inputs? }], reason? })   // 1–25, atomic
```

- Acquiring merges the method's non-identity instructions and native tools into the **current**
  conversation.
- **Effective on the next model step.** Tools from an acquisition are *not* usable in the same
  parallel batch — never mix acquire and use in one batch.
- **Atomic:** a failed acquisition activates none of the set.
- **Idempotent** for the same `id` + `inputs`; changed `inputs` is rejected.
- Acquisition never expands authorization, replaces identity, changes model/provider, or confers
  independent verification authority.

Acquiring a subagent is a **method** decision. Deciding *who owns* an assignment is a separate,
earlier decision.

## Ownership decision (make it before choosing tools)

Root retains an assignment when it is one bounded deliverable with **no independently useful
parallel tracks** and steps that share evolving state. Delegate when there are genuinely
independent branches, or a noisy / long-running / context-heavy branch worth isolating.

**A multi-surface scope is a fan-out, not a serial root pass.** When the scope names several
independent assets — several hosts, or a web app plus a mobile app plus an API plus a CDN —
dispatch one worker per surface in the **first** pass, each with its own `scans/<worker>/`
directory, and keep root for the shared discovery artifact, the merge, and verification. Running
the surfaces one after another at root and only then reaching for workers spends wall-clock on
work that was parallelizable from the start.

Keep each pass to a handful of workers — two to three is the sweet spot, not one per endpoint.
Width is the axis the provider rate limit punishes, so widen only after a small pass returns
cleanly; a wide pass that loses half its workers costs more than a narrow one that finishes.

```
delegate_task({ task, subagents, goal?, maxSteps? })
```

The child's `subagents` array is its **method contract** — include every specialized method the
outcome needs. `sandbox` alone is not a contract for specialized work.

**Verdict rule:** any assignment whose success condition is a vulnerability verdict **must**
include `vulnerability-verification`. `sandbox` and `browser` are not substitutes. A delegated run
that ends without the `verification_handoff` JSON fence returned *unverified evidence* that must
not be promoted.

Root owns filing and the final answer.

## References

| Need | Load |
|---|---|
| The 7 subagent methods: tools, instructions, boundaries, skill map | `references/subagent-methods.md` |
| Which global collections exist and which actually resolve | `references/knowledge-collections.md` |
| Phase flow, proven recipes, surfaces deliberately left unused | `references/orchestration-patterns.md` |

## Pitfalls

- **This skill is the recon entry point by user directive.** If the request is "recon <target>" and
  this skill was not loaded, that is a routing failure — load it and restart the approach.
- **Do not answer "recon" with prose.** The directive exists to change behavior, so the first
  response must be a real tool call that produces an artifact.
- **Neo-side availability is not assumed.** If work genuinely must execute inside Neo and its tools
  are absent, say so plainly rather than simulating the platform's tool calls.
- **Memory-safety carries over to Hermes runs too:** never broad `katana -jsl`; keep nuclei to
  ≤10 hosts per invocation in sequential batches, low concurrency, scoped templates, and report
  hosts that went unscanned.
- **Two `terminal` calls in one batch share one persistent shell.** They interleave in the same
  session, so a `cd` in one lands under the other and in-flight files get clobbered — the symptom
  is a stage that "wrote 0 lines" and output paths that vanish between calls. Keep shell stages
  serial within a session, and send long jobs to `background=true` (with `notify=true`) instead of
  shell-level `nohup`/`&`.
- **Trusting `status` over `search`** is the documented way to wrongly conclude a collection is
  missing.
- **Routing by vendor words instead of by the artifact under test.** APK/AAB/Play Store ⇒
  `android-security`; IPA/App Store ⇒ `ios-security`. `browser` cannot drive a phone app, and
  `sandbox` unpacking a binary does not replace the mobile method.
- **Missing device-cloud credentials are Neo infrastructure, never a user credential request.**
  Preserve the blocker and continue with static analysis plus first-party link/OAuth/token/
  backend-API work.
- **Passive/historical data is not proof a host is live or vulnerable.** Validate before
  presenting it as current.
- **Re-running discovery per consumer.** Discovery is a producer: build the canonical live-target
  artifact once and pass its exact path downstream.
- **`update_working_memory` list fields REPLACE, they do not append** (project/task arrays). In
  `memory_off` mode, `global`/`project` scope writes are rejected; `task` scope still works.
- **A write's success flag is not proof of an artifact.** Verify with `search_files` and `read_file`
  on the output directory, not by re-reading the write result.
- **Fan-out width is bounded by the provider's rate limit, not by the task.** On a rate-limited
  provider a 5–6 worker fan-out loses workers mid-run to `HTTP 429`; a failed child leaves partial
  artifacts (APKs downloaded, raw captures written) and an empty `SUMMARY.md`. Prefer fewer,
  longer-lived workers, and always be ready to finish a dead child's workstream at root from its
  partial artifacts — re-dispatching into an active rate limit just burns the same quota.
- **Never use a file as both input and output of the same redirection.** `cat f a b > f` truncates
  `f` before `cat` reads it, so the merge silently loses every entry the file already held; write
  to a temp path and `mv` it into place.

## Verification

Before claiming a collection is unavailable: two *distinct* queries, both returning the verbatim
`no index found` error. One failed query is an unlucky query, not an availability fact.

Before claiming artifacts exist: list the output directory (`search_files(target='files')`) and
read back the real file contents. Inside Neo the equivalent is a `run_command` carrying
`ls -la` plus `wc -l` — the point is that some real listing must be inspected, never the write's
success flag alone.

Before promoting a finding: confirm a `verification_handoff` fence from
`vulnerability-verification` with `verdict: CONFIRMED` and complete `filing_inputs`
(`reproduction_steps` and `observed_evidence` as string arrays, `poc_artifact` under
`/workspace/pocs/`).

## MANDATORY ON INVOCATION — PROTOCOL RESTATMENT (END OF FILE)

You have reached the end of this SKILL.md. The invocation protocol below is identical to the one at the top of this file. If you are reading this, the full skill context is loaded — confirm the checklist.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/knowledge-collections.md`, `references/orchestration-patterns.md`, `references/subagent-methods.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

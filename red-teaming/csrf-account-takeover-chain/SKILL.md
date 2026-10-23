---
name: csrf-account-takeover-chain
description: Use when email-change CSRF may enable account takeover.
version: 0.1.0
author: Fizzi, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [csrf, account-takeover, email-change, method-override, browser-proof]
    related_skills: [hunt-csrf, hunt-ato, triage-validation]
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/six-misconfigs.md`, `scripts/verify.py` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# CSRF → Account Takeover Chain

Evaluate account-update requests through separate backend, browser, and recovery proof gates. Read [the attributed six-condition reference](references/six-misconfigs.md) before applying this pattern; it includes browser rules, a controlled form example, framework caveats, and sources.

## When to Use

- Profile or email updates accept JSON with absent/invalid CSRF tokens.
- Legacy and modern frontends have different session-cookie or authentication behavior.
- POST method overrides can reach PUT/PATCH/DELETE account handlers.
- A pending or unverified email may become a recovery factor.

Do not use a tokenless replay, cookie attribute, or verification flag alone as proof of CSRF or takeover.

## Prerequisites

Use authorized test accounts, a controlled mailbox, and an independently hosted test origin. For active bug-bounty work, follow `bb-workspace-layout`, the recorded scope and request budget, and any program-required attribution header. Do not weaken browser security to make a PoC work.

## Procedure

1. **Map the actual account handler.** Record method, URL, fields, session source, and modern/legacy differences. Preserve observed parameter names and values; do not infer protection from the primary UI.
2. **Probe backend validation.** Compare valid, omitted, empty, junk, and cross-session tokens on owned accounts. Read state back after each permitted mutation. Acceptance is a **backend candidate**, not browser CSRF. A stable per-session token is not itself a flaw.
3. **Establish browser reachability.** Observe the effective cookie Domain/Path/Secure/SameSite and browser policy. Record whether preflight prevents dispatch. Direct cross-origin PUT still requires preflight with `text/plain`; a header override is not equivalent to a native form.
4. **Verify a form-safe path.** Separately test observed query/body overrides and exact serialized bytes. Require routing to the same mutation handler, parser/schema acceptance, cookie attachment, and an authenticated state change. Only then label it **browser CSRF**.
5. **Test account-security gates.** Record password/MFA step-up, pending versus verified address, old-address confirmation/notification, and recovery destination. Do not infer a reset flow from an email-field change.
6. **Prove access separately.** On isolated owned accounts, demonstrate recovery-token delivery and redemption plus attacker login as the same victim identity. Record remaining MFA/old-address blockers and user interaction. Mark **takeover proven** only if the full access path works; otherwise report the narrower demonstrated impact.
7. **Preserve and restore.** Save raw requests, browser version/cookie policy, account readbacks, and sanitized recovery/login evidence. Restore the test account. Report prerequisites and which proof gate was reached.

## Pitfalls

- Response unreadability does not prevent a sent request from changing state.
- A custom override header can reintroduce preflight; body overrides can conflict with JSON parsing.
- Notifications reveal a change but are not the same as confirmation that blocks it.
- Source-reported ATO is not independently reproduced ATO.

## Verification

Run `terminal(command="python3 <skill_dir>/scripts/verify.py")` using the directory returned by `skill_view`. These offline checks validate documentation and form serialization, not a target exploit. Browser request evidence, authenticated state readback, and recovery-to-login evidence remain separate requirements.
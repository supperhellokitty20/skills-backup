---
name: forwarded-reset-ato
description: Use when testing forwarded-header reset poisoning or ATO.
version: 0.1.0
author: FIN, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, account-takeover, password-reset, host-header, forwarded, rfc7239, patch-bypass]
    related_skills: [hunt-host-header, hunt-ato, bb-workspace-layout]
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/attack-mechanics.md`, `references/validation-cases.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# Forwarded-header reset poisoning → account takeover

Security testing playbook for attacker-controlled proxy metadata reaching authentication links. Not a generic HTTP-header guide. Treat alternate-header and parser-differential patch bypasses as hypotheses until the deployed recovery flow demonstrates impact.

## When to use

- Test password-reset, set-password, magic-login or invitation links generated behind a proxy.
- Recheck a Host / X-Forwarded-Host fix for surviving `Forwarded` or application-specific `X-forwarded` input.
- Investigate a poisoned authentication URL, token-bearing callback or disagreement between edge validation and backend origin selection.

## Prerequisites

Before target traffic, use `bb-workspace-layout`: current authorization, exact eligible recovery operation, finite request/email budget, owned test accounts A and B, B's controlled inbox, and an approved researcher-controlled receiver. Do not request real users' resets. Use the existing captured request and standard interception/replay tools, not a bespoke network enumerator. Include program-required attribution headers.

**Read `references/attack-mechanics.md` before selecting probes.** It contains the security mechanism, targeted matrix, patch-bypass requirements and proof gates. Read `references/validation-cases.md` for regression checks.

## Procedure

1. **Establish the control.** Capture the genuine B recovery request and resulting raw email. Record actual href, final origin, token placement, delivery delay and any mail-security wrapper. A successful API response is not email evidence.
2. **Preserve the submitted literal.** Keep `X-forwarded: for=Collab;by=Collab;host=Collab` exactly as supplied. Test standard `Forwarded` separately; do not rename the evidence. If Collab represents a DNS name, its `for`/`by` uses are nonconforming under RFC 7239.
3. **Isolate the poisoning source.** Keep connection destination, legitimate Host/authority, body and account fixed. Start with a host-only `Forwarded` probe and one fresh callback marker. Compare the actual email, not only responses or callback counts.
4. **Investigate differentials selectively.** Add only matrix rows justified by observed behavior. Track field name, list/duplicate form, header-family precedence, protocol and element ordering. A negative result is bounded to the tested request; no universal first/last policy is assumed.
5. **Prove the chain on B.** Correlate the poisoned email with a token received at the controlled endpoint, redeem that token on the legitimate application from attacker context, then verify B's identity through a clean authenticated session. Never use B's existing cookies/password/inbox-derived token as attacker proof. Keep raw secrets private.
6. **Record the ceiling.** Distinguish origin control, token disclosure, token redemption/password control and authenticated B access. Record victim interaction, scanners, MFA and tenant/account limitations. Compare original fixed behavior only when its evidence is available.

## Pitfalls

DNS callbacks, response reflection and a scanner GET do not alone prove ATO. A usable captured token obtained automatically may establish a no-user-click path, but authentication must still be demonstrated. A reset that leaves effective MFA blocking login is not full ATO. Do not assign Critical merely because the class is named ATO.

## Verification

Save control/mutation requests, raw email, correlated receiver evidence and clean-session identity proof under the finding's raw/interpreted directories. State untested prerequisites and policy constraints. A skill test validates guidance, not a target vulnerability; a patch bypass requires reproduced impact on the corrected deployed flow.
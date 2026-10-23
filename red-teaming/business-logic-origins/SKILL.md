---
name: business-logic-origins
description: "Use when hunting business logic flaws."
version: 0.1.0
author: FIN, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [business-logic, sdlc, release-timing, severity-calibration, race-condition, bug-bounty]
    related_skills: [bb-dupe-avoidance, triage-validation, burp-manual-workflow, bb-methodology]
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

# Business logic flaws: where they come from and when to test

Logic flaws are not injected by a bad parser — they are designed in, by humans working from
incomplete knowledge of their own system. That origin is exploitable information: it tells you which
features carry them and, more usefully, **when** they appear. Scanners cannot model intent, so this
class stays unfound for years and carries the lowest duplicate rate of any web class.

## When to use

- Testing a multi-role, transactional, or workflow-driven application.
- A target just shipped a release, or you can see release notes / changelogs.
- You found anomalous-but-not-obviously-exploitable behaviour and need to grade it.
- Automated scanning came back clean and you need the class scanners cannot reach.

## Why the flaws exist

Four recurring causes, each with a matching tell:

| Cause | Tell on the target |
|---|---|
| Undocumented legacy code; nobody left knows how it works | an old feature behaves inconsistently with its newer sibling |
| Two teams integrating without shared documentation | the seam between two features enforces less than either does alone |
| Logic complex enough that the implementers lost track | deep multi-step flows, pricing/discount stacking, permission inheritance |
| Weak process — no code review, oversized sprints, unestimated work | regressions reappear; fixed things break again |

The general shape: a check lives in one path and the newer path does not call it. A test-only branch
left in production. An `OR` where the author meant `AND`.

## When to test — the timing play

This is the part most hunters skip. Delivery model predicts the window:

- **Waterfall / V-model targets** (big, infrequent releases): the attack window is when a release
  lands. Everything written and refactored in that cycle arrives at once, and acceptance testing
  covers the stories that were written — not the scenarios nobody imagined.
- **Agile targets** (~2-week cycles): time pressure plus thin documentation makes regressions routine.
  Re-test every cycle; a flaw you reported as fixed can return in a later sprint.

So: **subscribe to the target's release notes, changelog, product newsletter and status page.** When a
release drops, test in this order:

1. **New features** — least-tested code, often shipped without the older code's guards.
2. **Refactored features** — the highest-yield class. Somebody edited code they did not fully
   understand and removed a guard they did not know was load-bearing.
3. **Interactions between features** — specifically the pairs that were not designed together.

## What to test

- **Client-supplied values the server should own.** Price, currency, discount, quantity, role, plan,
  tier, status, tax, shipping. Intercept the save and change them.
- **Negative and boundary values.** `-1` quantity, negative transfer amount, negative rating. Then
  overflow: if price, quantity and total are all integers, a large enough quantity can wrap the total.
- **Workflow step skipping.** Jump straight to the confirmation/fulfilment step without payment or
  verification. Replay a step that is only valid in an earlier state.
- **State mismatch.** Send a request valid in state A while the object sits in state B (cancel an
  already-shipped order; pay an already-paid invoice; accept a revoked invite).
- **Front-end-only limits.** A coupon the UI allows once, a 5-item cap, a disabled field, a greyed
  button. Replay the request and see whether the server ever checked.
- **Response-field injection.** Add a field the response contains but the request did not
  (`accountType`, `role`, `isVerified`) and see whether the server processes it.
- **Reversal asymmetry.** If an action grants something, does cancelling take it back? Cancel the
  order — do the loyalty points, the credit, the entitlement come off?
- **Registration collisions.** Registering with an existing user's username/email: does it error, or
  does it attach you to the existing account?
- **Races.** Two simultaneous requests for one limited resource — coupon, referral bonus, last item in
  stock, balance transfer. Burp's *Send group in parallel*; see `burp-manual-workflow`.
- **Documented impossibilities.** The manual says you cannot deactivate a super-admin. Try it.

## Severity calibration

Impact tracks how close the flaw sits to the target's core business and how privileged you had to be
to reach it.

| Flaw | Band | Reasoning |
|---|---|---|
| Client-side price calculation on a webshop | High/Critical | direct money, core business |
| Negative quantity → negative price / refund | High/Critical | direct money |
| Integer overflow on `price × quantity` | Critical | target can end up paying the attacker |
| Registering an existing username takes over the account | Critical | account takeover, no interaction |
| Request field the server processes to change your own role | Critical | privilege escalation — *if* the field is honoured |
| Same field, but the value is ignored server-side | Informational | nothing happened |
| Import overwrites other users' objects by name | Medium | requires an already-privileged position |
| Deactivating a super-admin the manual forbids | Medium | you must already be in user management |
| Login returns 200 for valid vs 403 for invalid usernames | Low | username enumeration; still needs a password |

**Preconditions lower severity.** "Already an admin", "already inside the tenant", "needs the
victim to complete three steps" each pull a band down. State the precondition in the report — triage
will find it anyway, and finding it yourself is what separates a calibrated report from an inflated one.

## Pitfalls

- **Odd behaviour is not a finding.** "The app let me do something weird" needs a sentence naming what
  an attacker *gains*. If you cannot write that sentence, keep working.
- **Negative-value and overflow tests create real records.** On production you may generate real
  orders, refunds, credits or emails. Stop at the minimum proof, record it, and clean up or notify.
- **Don't claim money impact you did not observe.** "Could have led to free orders" is a guess;
  "order completed with total €-5.00, screenshot attached" is a finding.
- **Scanners will not find this class.** A clean automated scan is not evidence of absence — and
  conversely, do not expect tooling to do this work for you.
- **Race-condition results need repetition.** One anomalous parallel run can be ordinary lag. Repeat,
  and show the resulting state, not just the response pair.
- **Reported-and-fixed is not permanently fixed** on a fast-release target. Re-test after later
  releases; regression is the normal case, not the exception.
- **A privileged-position flaw is still worth reporting** — just band it honestly rather than dropping it.

## Verification

Before reporting: the attacker gain is stated in one concrete sentence; the resulting **state** is
captured (order total, balance, role, entitlement — not only the HTTP response); every precondition
and required privilege level is listed; the band is justified against core-business proximity and
precondition cost; raw request/response plus the state evidence are under
`evidence/<finding>/raw/`; and side effects created on the target are noted for cleanup.

## Provenance

Derived from The XSS Rat's public `SecurityTesting` repository
(`notes/Vulnerability types/The Origin Of Business logic vulnerabilities`,
`notes/Vulnerability types/Business logic flaws`, `Checklists/webAppSec.md`,
`Checklists/2026-bug-bounty-guide.md`), commit `a68ec21`, read 2026-10-14. The severity table
reproduces that source's worked examples; the precondition discount, the state-capture requirement
and the production-side-effect rules are this skill's own framing.
---
name: bb-dupe-avoidance
description: "Use when bounty dupes are likely; find leftovers."
version: 0.1.0
author: FIN, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [bug-bounty, duplicates, target-selection, integration-points, api-versioning, strategy]
    related_skills: [bb-program-discovery, bb-methodology, business-logic-origins, bb-workspace-layout]
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

# Dupe avoidance: hunting the leftovers

Most hunters race to the same obvious surface on the same popular programs and collect each other's
duplicates. The counter-strategy is to out-think rather than out-race: deliberately pick the targets,
features and endpoints that the race skips, and treat every friction point that makes other hunters
leave as an advantage.

This is target- and feature-*selection*. Program eligibility and scope freshness are
`bb-program-discovery`; the execution loop is `bb-methodology`.

## When to use

- Choosing which program or which asset inside a program to spend a session on.
- Your last few reports came back as duplicates.
- A target is popular and hardened and you need an angle that is not the front door.
- Deciding whether a barrier (language, paywall, mobile-only setup) is worth crossing.

## Pick targets the race avoids

| Prefer | Why it is under-tested |
|---|---|
| Multi-role apps (admin / manager / member / viewer) | role matrix is combinatorial; scanners cannot model it |
| Multi-tenant / multi-organisation apps | cross-tenant isolation needs two orgs to even test |
| Free tier **and** paid tier | the capability delta between plans is a native access-control bug source |
| Import / export / bulk / webhook features | bolted on later, over an already-shipped feature |
| Published API docs, Swagger/OpenAPI, developer portal | a blueprint most hunters never read |
| A main app (`app.target.com`) | fine-tune a real methodology instead of spending the session on recon |

**Avoid a wide `*.target.com` wildcard as a first target.** Recon only tells you *where* to apply a
methodology; after days of enumeration you still have to hack something. Build the attack strategy on
a single main app, then scale the recon.

**VDP before paid.** No payout means fewer hunters and often less hardening, and points convert into
private invitations where the competition is a fraction of a public program's. The money follows the
process.

## Hunt the leftovers inside the app

**Integration points.** Any feature built *on top of* another feature has a seam where the two must
communicate, and the newer side frequently lacks the original's checks. Enumerate them explicitly:
import, export, bulk edit, webhooks, third-party login, payment flows, email/notification triggers,
PDF and report generation, mobile-only endpoints, admin tooling added after launch. Write the list
into the engagement notes before testing — they are the highest-yield, lowest-dupe surface in most
apps.

**The secondary action, not the content field.** Everyone fuzzes the comment box. Nobody replays the
counter beside it. If a `POST /Like` adds one and `POST /Unlike` removes one, replaying the first is a
real finding with a near-zero dupe rate. Generalise to: follow, vote, claim, redeem, invite, rate,
reserve, cancel.

**Infer the older API.** A call to `/api/v2/getInvoices` implies `/api/v1/getInvoices` probably still
answers — and older versions are routinely the less-protected ones. Walk versions down (`v3`→`v2`→`v1`),
try sibling path families (`/internal/`, `/private/`, `/admin/`), and tamper the method on documented
GET-only routes.

**Disabled-by-default modules.** Application settings often ship features switched off. Every one you
enable is attack surface that most hunters never saw.

**Read what nobody reads.** The product manual, the knowledge base, the API reference, the release
notes. In an app you understand, an anomaly is obvious; in an app you are guessing at, it is
invisible. Expect to spend days on this, not hours.

**Mine the JS.** Minified bundles and historical URLs carry endpoints absent from the UI, commented-out
routes and old parameter names. Read them as well as tooling them — a human eye catches the odd
detail a link extractor reports as just another string.

## Source-audit targets: read the project's own security list first

When the target is a codebase rather than a web app — a distro, a desktop shell, an installer, a plugin
ecosystem — do the dupe check *before* the hunt, not after. These projects ship per-release "security
fixes" lists that name the exact class they just closed, and their advisories, issue tracker and
security pages are public. Read them, then hunt the class *next to* the one they fixed: a hardening pass
lands on the reported instance and its immediate neighbours, so the sibling feature that was not in the
same commit is the leftover.

A fixed issue that survives as a documented, warned, opt-in feature stays a dupe forever: the fix moved
the default, it did not remove the capability.

## Treat barriers as competitive filters

Every obstacle sheds some of the field. Cross them deliberately:

- **Non-English program** (commonly Dutch or another EU language on some platforms) — a translation
  extension reduces this to a mild inconvenience.
- **Paywall or paid tier** — buying the plan exposes surface free accounts never reach. Weigh the cost
  against the program's reward band.
- **Mobile-only or multi-step onboarding** — a tedious setup is exactly why the surface behind it is
  comparatively untouched.
- **Complex domain** (banking, logistics, medical, games) — domain understanding is the moat.

The only barriers that are never worth crossing are the ones that change your authorization: paying
for someone else's access, using leaked credentials, or anything the program's policy prohibits.

## Pitfalls

- **"Less competition" is not "in scope".** A neglected asset is still only testable if the current
  scope and policy say so. Check the live scope before touching it — see `bb-program-discovery`.
- **A leftover is not automatically severe.** Finding an untested endpoint is a head start, not a
  finding; it still needs demonstrated impact. `triage-validation` applies unchanged.
- **VDP does not lower the proof bar.** Unpaid programs still reject unproven reports, and a weak
  report there costs the reputation you are farming for invites.
- **An older API version that 404s is a negative to record, not a failure.** Write it down so the next
  session doesn't re-walk it.
- **Enabling a settings module can change the account's state or billing.** On a production tenant,
  confirm it is reversible before flipping it.
- **Don't confuse out-thinking with being slow.** Reading docs for days on a program whose scope is
  about to close is its own waste; sequence the deep-understanding play against the program's lifetime.
- **A class the project already closed is a dupe, not a near-miss.** When release notes name your class
  as fixed, pivot to the sibling class the same hardening commit did not touch.

## Verification

Before committing a session to a target: the pick is recorded in `scope.md` with the reason it is
expected to be under-tested; the integration-point list exists in writing; for any barrier crossed,
the method is inside policy and noted. When a report comes back as a duplicate, record which surface
class it came from — the pattern across a few of those is what redirects the next pick.

## Provenance

Strategy derived from The XSS Rat's public `SecurityTesting` repository
(`Checklists/Main app methodology.md`, `Checklists/2026-bug-bounty-guide.md`,
`notes/Rat's methodology`, `notes/Broad scope methodology`, `recommended-targets/main-app.md`),
commit `a68ec21`, read 2026-10-14. Platform-specific claims in that source are the author's
opinion and are deliberately not reproduced as fact here; scope/authorization framing is this
skill's own.
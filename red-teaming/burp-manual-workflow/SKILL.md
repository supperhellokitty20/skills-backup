---
name: burp-manual-workflow
description: "Use when hunting manually in Burp Suite."
version: 0.1.0
author: FIN, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [burp-suite, proxy, repeater, intruder, manual-testing, idor, csrf, bug-bounty]
    related_skills: [hunt-idor, hunt-csrf, bb-workspace-layout, triage-validation]
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

# Burp Suite manual hunting workflow

The Burp mechanics that turn "browse the app with a proxy running" into a systematic test: scope and
proxy configuration that surface hidden state, the site-map filter that cuts the noise, and the
extension/match-and-replace setups that make access-control and CSRF testing semi-automatic.

Tool mechanics only. Vulnerability-class depth lives in the `hunt-*` skills.

## When to use

- Starting a manual pass on a web or mobile-backend target with Burp in the loop.
- You have a filled site map and need to pick what to test.
- Testing IDOR/BAC across two accounts, or CSRF-token enforcement.
- Returning to a target after a break and needing the same setup back.

## Setup, in order

1. **Scope first.** Target → Scope, enable *Use advanced scope control*, Add, and paste the **host
   only** — no scheme, no path (`app.target.com`, not `https://app.target.com/login`). Everything
   downstream (site map filtering, extension triggers, scanner) keys off scope; a wrong scope is the
   single most common reason a later step "doesn't work".
2. **Import the program's Burp config if it ships one.** HackerOne publishes per-program config
   files. Project → Project options → Load project options. This encodes the program's own scope and
   throttling expectations rather than your guess at them.
3. **Proxy options that reveal hidden state.** Enable *Unhide hidden form fields* (hidden inputs
   render visibly with a red border) and *Remove JavaScript form validation*. Client-side-only
   constraints — disabled fields, maxlength, format checks, hidden role/price/plan inputs — become
   editable and visible. Most mass-assignment and front-end-only-validation findings start here.
4. **Save the project file** (Burp Pro). Hunting happens in 1-3 hour bursts; reloading a project with
   scope, options, site map and Repeater tabs intact removes the restart cost that stops sessions
   from happening at all.

## Cut the noise: parameterised requests only

In **Target → Site map**, open the filter bar and check **"Show only parameterized requests"**.

This is the highest-leverage click in Burp. Static assets, images and fonts vanish; what remains is
the set of requests that carry input to the backend. Work that list, not the raw site map.

Then triage by what the parameter plausibly reaches — ignore presentation parameters like
`view=week`:

| Parameter shape | Test for |
|---|---|
| `url=`, `src=`, `dest=`, `feed=`, `webhook=`, `callback=`, `proxy=` | SSRF |
| `file=`, `page=`, `template=`, `path=`, `include=`, `image=` | LFI/RFI |
| `id=`, `user_id=`, `order=`, `invoice=`, `doc=`, GUIDs | IDOR |
| `redirect=`, `next=`, `returnTo=`, `goto=`, `target=` | open redirect |
| `q=`, `search=`, `name=`, `title=`, `comment=` | XSS / SSTI / SQLi |
| `cmd=`, `exec=`, `host=`, `ping=`, hostname/IP/filename | command injection |
| any XML body, SVG/DOCX/XLSX upload | XXE |
| `role`, `isAdmin`, `plan`, `status`, `price`, `accountType` | mass assignment / business logic |

## Repeater discipline

Read the response until you can state what the endpoint does, then change **one** thing per send:
alter the value, remove the parameter, duplicate it, send a string where an int is expected, a
negative, a huge number, a null. Watch for status, length and timing deltas — not just error text.

**Test the unglamorous sibling endpoint.** Content fields are picked over by everyone. The
secondary action beside them often is not: if `POST /Like` increments a counter and `POST /Unlike`
decrements it, replay `POST /Like` in Repeater several times and see whether the count keeps
climbing. Same for follow, vote, invite, redeem, claim.

**Change request method.** Right-click → *Change request method* flips POST↔GET. Some servers
validate a CSRF token only on the method they expect, so the same action as a GET with the token
omitted can succeed. It also reaches handlers that accept more verbs than the UI uses — try PUT,
PATCH and DELETE against documented GET-only routes.

## Semi-automating access control and CSRF

**IDOR/BAC with the Authorize extension.** Install from the BApp store, give it the low-privilege
user's session header, then browse as the high-privilege user. Authorize replays every in-scope
request with the low-privilege credentials and colour-codes the comparison, so a privileged response
returned to the low-privileged identity surfaces immediately. Use your **own second account** for
this, never a real user's session. (The older AutoRepeater extension covers similar ground but has
been unreliable across Burp releases — prefer Authorize.)

**CSRF enforcement with match-and-replace.** Proxy → Options → Match and Replace. Add a rule that
rewrites the CSRF token in the request (pick *header* or *body* to match where the token lives) to a
fixed wrong value. Enable it, then use the application normally. Any state-changing action that still
succeeds is a token the server does not actually validate. **Disable the rule immediately afterwards**
— leaving it on breaks the app and silently corrupts every later test in the session.

The token checks worth walking, in order: remove the parameter entirely; send it empty; send a wrong
value of the same length and charset; reuse a token from an earlier request; reuse a token issued to
a *different account*; flip the method.

**Intruder** for the bounded enumerations: event-handler lists against a filtered XSS sink,
command-injection separator×command lists against every parameter, sequential/GUID object IDs. Set
the rate to the program's limit, not Burp's default. **Send group in parallel** (Repeater tab groups)
is the race-condition primitive — coupon redemption, referral bonuses, balance transfers, stock.

## Pitfalls

- **Scanner alerts are hypotheses.** Burp Pro's issues list contains false positives. Confirm every
  one by hand before it enters a report; an unconfirmed scanner row is not a finding.
- **DOM XSS is invisible in view-source.** The payload may never reach the server and never appear in
  the HTTP response. Use devtools: find the source (`location.search`, `document.referrer`,
  `window.name`, `localStorage`), set a breakpoint, follow the value into the sink.
- **Match-and-replace left enabled is a self-inflicted outage.** It rewrites traffic globally,
  including requests you are about to interpret. Turn rules off the moment the check is done.
- **You are testing production.** Replayed state-changing requests create real records, real emails
  and real charges. Never put a random identifier in an IDOR test — create a second account, navigate
  to the same feature, and use *that* object's ID so both sides of the comparison are yours.
- **Expired auth reads as "not vulnerable".** A 401/500 from a stale JWT or session in Repeater looks
  like enforcement. Re-login, copy a fresh token from Proxy history, and re-send before concluding
  anything.
- **An unfiltered site map hides the work.** Without the parameterised-request filter you will spend
  the session scrolling past static assets.
- **Scope set with a scheme or path silently excludes traffic.** If the site map stays empty or an
  extension never fires, re-check the scope entry first.

## Verification

Before reporting from a Burp session: the confirming request was re-sent with fresh credentials; the
raw request and response are exported to the finding's `evidence/<finding>/raw/`; for a
two-account test both identities are researcher-owned and the token/cookie swap direction is
recorded; every match-and-replace rule used is disabled; and the claim is reproducible from the saved
request alone, not from the Burp UI state.

## Provenance

Workflow derived from The XSS Rat's public `SecurityTesting` repository
(`Checklists/Main app methodology.md`, `notes/Rat's methodology`, `notes/Vulnerability types/`
{`IDOR`,`BAC`,`CSRF`,`Command injection`}, `Practical Demonstration - Main Web Application hacking`),
commit `a68ec21`, read 2026-10-14. Parameter-triage table, ordering and the safety rules are this
skill's own framing.

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

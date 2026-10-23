---
name: payload-seeding-and-context
description: "Use when seeding XSS/SSTI payloads app-wide."
version: 0.1.0
author: FIN, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [xss, ssti, csti, payload-seeding, blind-xss, context-triage, bug-bounty]
    related_skills: [hunt-xss, hunt-ssti, security-arsenal, triage-validation]
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

# Payload seeding and reflection-context triage

Seed one multi-class payload into every writable field the moment you register, then let the
application carry it to sinks you will never find by crawling — admin panels, generated PDFs,
export files, email templates, backend dashboards, downstream integrations. Detection is passive
after that: you use the app normally and watch for the marker to fire or resolve.

This is a *delivery and triage* skill. For per-class exploitation depth load `hunt-xss` (XSS) or
`hunt-ssti` (template engines).

## When to use

- You have just created an account on a target and are about to explore it.
- You are filling any profile, object-name, address, comment or upload-filename field.
- A seeded marker came back changed or rendered and you need to decide what it proves.
- You want coverage of admin-facing and asynchronous sinks you cannot reach directly.

Don't use for: a single known-reflecting parameter you are already exploiting — go straight to the
matching `hunt-*` skill.

## Prerequisites

Authorization for the target and the account-creation flow, per `bb-workspace-layout`. Use your own
test accounts only. Keep every seeded payload **inert** — a marker plus a harmless `alert`/`confirm`
or an arithmetic probe. Never seed a payload that exfiltrates data, writes to other tenants, or
fetches from a third party you do not control; you are writing into a production database that other
people's records live in.

## The seeding payload

One string that simultaneously probes HTML-tag injection, attribute breakout, JS-string breakout,
SQL special characters and both template-engine syntaxes:

```
'"`><u>SEEDMARKER01</u><img src=x onerror=confirm(document.domain)>${7*7}{{7*7}}
```

Use a **unique marker per field** (`SEEDMARKER01`, `02`, …) and keep a map of marker → field in the
engagement notes. When a marker later fires in an admin panel or a PDF, the marker is the only thing
that tells you which input reached that sink.

Shorter variants when a field has a length limit:

| Limit | Payload | Probes |
|---|---|---|
| Very tight | ``'"`><u>M01`` | tag + attribute + JS + SQL chars |
| Arithmetic only | `${7*7}{{7*7}}` | SSTI / CSTI |
| Tag only | `<img src=x onerror=confirm()>` | HTML tag context, DOM-insertion safe |

**Seed everywhere:** username, first/last name, display name, nickname, address lines, bio,
company name, every object you can create (project/product/note/ticket titles and bodies), upload
filenames, support-ticket subjects, invite messages, and any preference string. Admin-facing fields
(ticket subjects, user display names) are the highest-value seeds because they render in a
privileged context.

## Triage by reflection context

When a marker comes back, the surrounding context decides the payload — not the vulnerability class.

| Context | What the seed shows | Breakout | Exploit shape |
|---|---|---|---|
| HTML tag context | `<u>` renders; raw tags survive | nothing needed | add your own tag + event handler: `<img src=x onerror=confirm()>` |
| HTML attribute context | reflected inside `value="…"`; the `">` closed it | `"` / `'` / `` ` `` | `" onmouseover=confirm(1) x="` or `' autofocus onfocus='confirm(1)` |
| JS string context | marker inside `document.write('…')` or a `var` | `'); ` | `'); confirm(); //` |
| Template resolved | `${7*7}` or `{{7*7}}` returned **49** | — | engine fingerprint ladder below |
| SQL error | `'` triggered a database error | — | hand to `hunt-sqli`; do not keep fuzzing blind |
| Encoded/entity-escaped | `&lt;u&gt;` | — | correctly handled for this sink; move on |

**DOM-insertion caveat:** in `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write` sinks a
`<script>` block does **not** execute. That is why the seed carries `<img src=x onerror=…>` — it
fires on DOM insertion. For DOM sinks you must read the live DOM in devtools, not view-source.

## Template-engine fingerprint ladder

Run this only after `${7*7}` or `{{7*7}}` returned `49`:

1. `{{7*7}}` → `49` continue; original string back → not a server template, stop.
2. `{{7'*7'}}` → `49` = **Twig**; `7777777` = **Jinja2**; neither → next step.
3. `A{*comment*}b` → resolves = **Smarty**; else next step.
4. `${"z".join("ab")}` → resolves = **Mako**; else treat as **CSTI** (client-side engine such as
   Vue/Angular) and confirm in the browser.

Then read that engine's own documentation for the escalation path. A resolved `49` is a calculator,
not a finding — `hunt-ssti` carries the per-engine exploitation.

## Blind seeding

Markers that never render for you may still fire for someone else. Point the payload at a callback
receiver you control, seed on day one, and keep hunting — these land hours or days later when an
admin opens a ticket queue or a nightly job renders a report. A callback proves the sink exists and
names the context; it does not by itself prove impact. Record which marker fired, the rendering
context, and whose session rendered it.

## Pitfalls

- **Reflection is not a vulnerability.** A marker appearing in a response proves the value round-trips.
  You need script execution, template evaluation or a query error in a context that affects another
  user before it is a finding.
- **Self-XSS is not XSS.** A payload that only ever renders in your own account's view of your own
  data is out of scope on nearly every program. It becomes a finding when it renders in *another*
  user's or an admin's context — prove that with a second owned account or a callback from a session
  that is not yours.
- **One payload, several possible causes.** A changed marker can be XSS, SSTI, CSTI, SQL error or
  plain HTML-encoding. Identify which, with the context table, before writing anything down.
- **Don't seed destructive or exfiltrating payloads.** `fetch()`-to-attacker, cookie-stealing and
  tenant-crossing writes belong in a controlled proof against your own accounts, never in a
  broadcast seed across a production app.
- **Length and charset filters silently truncate your seed.** A field that stores 20 characters turns
  your polyglot into a harmless fragment; re-seed tight fields with the short variants and verify what
  was actually stored.
- **Markers without a map are useless.** A payload firing in a PDF three days later tells you nothing
  if every field got the same string.
- **Encoded once is not encoded everywhere.** The same stored value can be escaped in the web UI and
  raw in an export, an email or an admin view. Keep checking new sinks for an old marker.

## Verification

Before recording a seeded finding: the marker is identified to its source field; the rendering
context is named; execution or evaluation is demonstrated (not just reflection); the rendering
session belongs to an identity other than the attacker account; raw request/response and a
screenshot of the firing context are saved under the finding's `evidence/<finding>/raw/`. Note which
seeded fields produced nothing — that bounds the finding and stops the next session re-seeding them.

## Provenance

Technique and payload style derived from The XSS Rat's public `SecurityTesting` repository
(`Checklists/Main app methodology.md`, `notes/Rat's methodology`, `notes/Vulnerability types/XSS`,
the `Practical Demonstration` walkthrough), commit `a68ec21`, read 2026-10-14. The engine
fingerprint ladder there credits PortSwigger/James Kettle's server-side template injection research.
Markers, inertness rules and the triage table are this skill's own framing.

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

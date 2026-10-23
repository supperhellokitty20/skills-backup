---
name: bb-attacker-path-proof
description: "Use when a finding's prerequisites may be unreachable."
version: 1.0.0
author: skii, Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [bug-bounty, validation, proof, idor, credentials, evidence, redteam]
    related_skills: [bb-finding-triage-gate, triage-validation, report-writing]
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

# Attacker-Path Proof

A finding is valid when **every prerequisite in the attack path is reachable by an attacker through normal channels** — not when the final request succeeds. A technically real IDOR, XSS, SSRF or auth bypass can still be disproven for reporting purposes when any prerequisite was supplied by the tester instead of acquired by the attacker.

## When to Use

- A finding's impact depends on a victim identifier, token, role, invite, prepared state, device condition or victim interaction.
- You proved A can read or change B's object and are about to write it up.
- A credential, key or token was found and you must decide whether it is a finding.
- You need to decide whether a result is disproved, blocked, or simply untested.
- You are choosing how much cross-entity testing is defensible under program rules.

Not for: classifying an already-proven finding (`bb-finding-triage-gate`), or the 7-Question kill decision (`triage-validation`).

---

## Build the prerequisite ledger before claiming impact

One row per prerequisite: victim identifier, object id, email, token, nonce, cookie, role, tenant membership, invite, prepared state, victim interaction, reachable sink, device or network condition.

| Field | Content |
|---|---|
| Prerequisite | The literal value, state, role or action needed |
| Attacker starting capability | Own account only / no account / lower role |
| Exact acquisition or creation action | The step that gets it from that starting state |
| Evidence path | File that proves the step |
| Result | `REACHABLE` / `NOT REACHABLE` / `BLOCKED` |

- Prove rows **chronologically**, feeding each proven output into the next step, starting from the stated attacker capability.
- All rows `REACHABLE` is the bar for PROVEN.
- One `NOT REACHABLE` row disproves the claimed path (after documented live searches).
- One `BLOCKED` row prevents PROVEN — it does not disprove.
- Data visible only through the victim account never proves the attacker can obtain it. Harness actions — DevTools/CDP, direct RPC, copied victim-only values, attacker-imported content, trusted-admin processing — are not delivery. Prove a normal external path.
- Count every click, redirect, prompt, tab switch, reload and cached-state dependency as a victim-interaction prerequisite.

---

## Acquisition search — a missing identifier is an objective, not a rejection

From an attacker who controls only their own account, or none:

- **Identifier sources:** lists, search, member/invite views, autocomplete/suggest, sharing UI, mentions, public profiles, `sitemap.xml`, `robots.txt`, JS bundles and source maps, GraphQL introspection, error messages, redirects and `Location` headers, `Referer` leaks, OAuth callbacks, webhook payloads, CSV/export endpoints, related or parent objects, predictable/sequential ID structure, unauthenticated enumeration.
- **XSS delivery surfaces:** URL reflection, profile fields, filenames, imports, webhooks, email fields, OAuth state, error pages, search, comments, notes, mentions, admin views.
- **CSRF variants:** predictability, GET leakage, empty values, cross-user acceptance, cross-origin acceptance, alternate content types.
- A second researcher-owned account is valid only when it makes the acquisition path *more realistic* — never to stand in for the victim.

---

## Bounded non-destructive proof standard

**Non-destructive** means no deletion, lockout, denial of service, irreversible change or spam. It does **not** mean read-only or own-records-only: GET, POST, PUT, PATCH and other state-changing requests are in bounds when they are the finding's mechanism.

Order of proof:

1. Prove the mechanism on researcher-owned objects (own account, record, domain).
2. Confirm cross-entity reach on **at most three** non-owned objects with the smallest request that proves the boundary.
3. Characterise enumerability **without bulk collection**.

For writes on non-owned objects, prefer reversible values, restore originals where possible, and record every touched object id in the evidence.

Program text such as "stop testing once a flaw could modify data" means: stop after this bounded proof and submit. It does not forbid the proof, and it never requires vendor pre-authorisation.

---

## Credential liveness vs authority — two separate gates

1. **Liveness** — minimal sound liveness/authentication evidence plus a **negative control**. Record `Credential liveness: CONFIRMED | INVALID | BLOCKED`. Only CONFIRMED supports a finding.
2. **Authority** — liveness proves the value is real, not that it grants anything. Escalate in this order: no-payload authority probes (capability ceilings, wildcard or namespace attach/subscribe status, denied-op controls) → researcher-owned account, channel, record or tenant → at most three lawful cross-entity confirmations with lawfully obtained identifiers.

Never test credential reuse on another account, impersonate users, enable disabled accounts, run privileged management operations, or bulk-read other tenants.

---

## Counterevidence — required before claiming the strongest severity

State: the strongest benign explanation for what you observed, the exact control or alternate path you tested, the result, and the fact that would lower or raise severity. A historical precedent or a prior model's verdict is **not** counterevidence.

Recurring false-positive shapes to control against:

- 200 OK with a byte-identical body (not a bypass) — diff bodies, and probe with redirect following disabled.
- A marker that already appears in the baseline response (not a reflection).
- A single timing sample (not a side channel) — n≥10 interleaved, suspect mean ≥2σ above control.
- A do-nothing server-side policy (an extension denylist) mistaken for a file-existence oracle.
- A catch-all 200 from a SPA/auth edge mistaken for an exposed path — compare against a random missing-path control on body hash and length.

---

## Evidence rules

- Show at most **three representative records** with the impact-bearing values exactly as returned; use counts for scale and say they are counts.
- Screenshots must be genuine captures of real output. Never generate, paint, mock, reconstruct or substitute. A capture failure gets an explicit `![SCREENSHOT NEEDED: what to capture]()` placeholder with the reason and retry command — and every placeholder must be replaced before submission.
- Re-capture whenever the command or result changes; a stale screenshot contradicts the report.
- **Proof shape:** 1 stateless request → inline; 2–4 stateless requests with no carried value → inline sequence or one authenticated-tab `fetch()`; 5+ requests, carried values, loops or an OOB listener → attached `poc.py`/`poc.sh` **with the decisive request still inline**.
- Every shipped snippet must run verbatim from the stated starting state. If it needs special flags or is environment-fragile, ship an alternative.
- Redact secrets and real user data in the public artefact; keep the private reproduction manual separate from the submission body.

---

## Common mistakes

- Starting the proof with an already-obtained UUID/token/email and calling the path proven.
- Treating an environment, safety, scope or rate-limit block as a disproof — it is `BLOCKED`; say exactly what you need.
- Proving A→B access while the identifier came from B's own dashboard.
- Bulk collection to "show scale" instead of characterising enumerability.
- Re-testing from scratch after a context compaction because the angle and its status were never written down — record as you go (see `bb-hunt-phase-pipeline`).

---

## Related

- **`bb-finding-triage-gate`** — consumes this ledger to decide DIG / CANDIDATE / NA.
- **`triage-validation`** — 7-Question Gate, including the impact-beyond-technically-possible question this skill operationalises.
- **`report-writing`** — how the proven path becomes the report's Steps to Reproduce.
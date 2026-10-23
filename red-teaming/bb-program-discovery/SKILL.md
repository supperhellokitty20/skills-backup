---
name: bb-program-discovery
description: Use when picking a bug bounty program or its fresh scope.
version: 1.0.0
license: MIT
category: redteam
author: Hermes Agent
tags: [bug-bounty, recon, program-selection, scope]
metadata:
  hermes:
    tags: [bug-bounty, recon, program-selection, scope]
    related_skills: [bb-methodology, bug-bounty, bb-workspace-layout]
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/scope-change-sources.md`, `scripts/h1_structured_scope.py`, `templates/program-shortlist.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# Program Discovery & Fresh-Scope Tracking

Answers two different questions that users phrase the same way:

1. **"Which programs are new?"** — recently launched bounty/VDP programs.
2. **"Which programs just added scope?"** — an existing program that added new assets, hosts or repositories in the last days or weeks. This is the higher-value answer: new assets are the least-tested surface on the platform and dupe risk is near zero for the first days.

Platform source URLs, endpoint quirks and free-vs-Pro gates: `references/scope-change-sources.md`. Deliverable skeleton: `templates/program-shortlist.md`.
Machine-readable asset list for one or more handles (no sign-in): `scripts/h1_structured_scope.py`.

---

## When to Use

- "Find me a good bug bounty program" / "what should I hack next" / "which programs are new".
- "Which programs recently added or expanded scope" / "where is the fresh attack surface" — a discovery request with no target named.
- Choosing between candidate programs at the start of a session, or deciding whether a target is worth starting at all.
- Setting up a habit for monitoring scope changes on a platform.

Not for: a target already chosen — use `bb-methodology` for the session workflow and the `hunt-*` skills for the vuln classes.

---

## Always-on rules

### Separate the two questions and label every pick
A program can be years old and add a wildcard last week. Never present a launch-date-sorted list as "recently added scope" — HackerOne's directory sorts by **Launch date**, which answers question 1 only. For each item state which question it answers and the date it rests on.

### Verify freshness at the source, never infer it
A program's own scope page is the ground truth: HackerOne exposes a per-asset **Last update** date plus a "**View changes** (Last updated on …)" link on `/<handle>/policy_scopes`. Aggregators report "added 1 day ago" with the asset identity hidden behind a paywall — say what you actually saw, not what you assume it was. The rendered page keeps its tier groups **collapsed**, so pull the list instead of reading headers: the unauthenticated `team(handle:)` structured-scope query (`scripts/h1_structured_scope.py`) returns every asset row with `eligible_for_bounty`, the per-asset `instruction` note and `updated_at` — and that raw JSON is what `scope.md` is derived from, not retyped.

### Pacing on chat platforms (this user)
Cross-platform discovery is a long chain of tool calls. This user reads silence as a dead session — they will ping "dead??" mid-run. Send one short progress line early, then keep working. If a step is sitting on an approval prompt, say so in chat instead of blocking quietly.

### Never mix money with no-money
Sort the output into paid bounty, contest/audit (time-boxed), and VDP (reputation only). A "new program" table that silently mixes all three wastes the user's triage time.

---

## Procedure

1. **Clarify the constraint** — sector/tech, web2 vs web3 vs source-code, bounty-only vs VDPs acceptable. With no constraint, default to: paid bounty, web/API/source-code surface, freshness-first, ~10 picks.
2. **Sweep the free sources** (`references/scope-change-sources.md`), newest-first on each: HackerOne directory (launch date), Bugcrowd `engagements.json`, Intigriti researchers list ("Newest programs"), bbradar.io (aggregated, newest-first), plus web search for launch announcements (vendor news posts and platform blogs announce migrations/launches days before aggregators index them).
3. **Verify each shortlist item** on the program's own scope page: which assets, added/updated when, tier-gating, bounty eligibility.
4. **Attach a competition signal** to every pick: reports resolved, or total paid plus 90-day report volume (HackerOne shows this on the program card). Fresh scope with 300 prior reports is worth far less than fresh scope with 30.
5. **Deliver** from `templates/program-shortlist.md`; close with the tracking options and one concrete next step (e.g. "pull the asset list + per-asset last-update dates for the top 3").

---

## Deliverable format (this user)

- Discord/chat: **bullets, no tables**. One bullet per pick, opening `**Program — Platform, launched/scope-updated <date>.**` then one line: what is freshly in scope, reward range, competition signal, link.
- Group by tier: fresh paid scope → paid but saturated → web3/contest (flag end dates) → VDPs (rep only).
- End with: how to keep tracking it yourself, an explicit "what I could not verify" line, and the collection timestamp — these listings drift within a day.
- Keep the prose tight; the value is the dates, the freshness claim, and the link. Do not narrate the sources you tried.

---

## Pitfalls

- **Launch-date sort presented as scope change** — a directory ordered by launch date tells you nothing about added assets; a program listed there may have added nothing. Distinguishing them is the whole point of this skill.
- **Platform "updated" badges are not changelogs** — Bugcrowd's `badgeVariant: "updated"` rotates across pulls (1 of 48 in one pull, a different program in the next). Never claim a program changed scope on badge evidence alone.
- **Aggregator Pro gates** — the free tier of a scope-change feed typically gives program + asset type + bounty eligibility + date while hiding the asset identity. Report the type and date; do not imply you saw the hostname.
- **Bounty-less launches dominate "newest" lists** — the newest entries are often VDPs (no payout) or platform-hosted contests with fixed windows. Check payout eligibility and end dates before recommending.
- **Web3 contests are time-boxed** — Cantina/Sherlock/Huntr/CertiK-style audits close; a "new" entry may already be over. Check the contest window before listing it.
- **Single-platform sweep** — the same week's fresh scope is spread across HackerOne, Bugcrowd, Intigriti, YesWeHack, HackenProof, Immunefi, Sherlock and Cantina. A list drawn from one platform looks complete and isn't.
- **Tier-gated assets** — a newly added wildcard is often carved out at a lower reward tier than the rest of the program. Read the tier note on the asset row before quoting a ceiling.
- **Program-card competition stats are not stable across reads** — the same "reports received | 90 days" figure has read as two very different numbers within minutes, and "reports resolved" can lag it wildly. Quote per-asset `updated_at` dates, which held steady, and treat any single volume number as approximate.
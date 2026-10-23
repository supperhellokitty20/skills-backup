---
name: bb-workspace-layout
description: "Use on any bug bounty or hacking project: workspace layout."
version: 1.0.0
author: skii, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [workspace, layout, bug-bounty, hacking, evidence, structure, conventions, neo]
    related_skills: [neo-agent-platform, projectdiscovery-toolchain]
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/hackerone-scope-refresh.md`, `references/lead-catalog-and-handoff.md`, `references/neo-sandbox-paths.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# Bug Bounty / Hacking Workspace Layout

The user's desired artifact layout for any bug bounty or hacking engagement. Apply it without
being asked. The point is that the verifier — or the user, a week later — can find the raw output
behind any claim without reading a narrative.

Two distinct things are documented here, and they must not be conflated:

1. **Local engagement layout** — the default. A Hermes session on the user's machine writes here.
2. **Neo sandbox mapping** — only when the work genuinely executes inside the Neo/agent-swarm
   platform. See `references/neo-sandbox-paths.md`.

## When to Use

- Starting any bug bounty, pentest, or hacking engagement
- Deciding where to write scanner output, evidence, PoCs, or a report
- A task is delegated and needs a collision-free output directory
- Resuming an engagement and re-establishing where things live
- Verifying an engagement's artifacts are complete before reporting

Don't use for: general software projects, scratch experiments, or Hermes-internal state.

## Layout

One project per engagement, under the user's research root (`~/researchs/bb/<program>/`), with
purpose-named subdirectories. Skip directories a given engagement doesn't need — no empty
scaffolding.

```
<engagement>/
├── AGENTs.md           # required startup guide and current cross-session handoff
├── scope.md            # targets, exclusions, auth context, request limits, authorization
├── scans/              # RAW scanner output, unfiltered (httpx/nuclei/ffuf JSONL)
│   └── <worker>/       # one subdir per delegated worker
├── manual-probes/      # fallback security-baseline probes
│   ├── cors/  openapi/  info/  ssh/
│   └── headers.jsonl
├── evidence/           # per finding
│   └── <finding>/
│       ├── raw/        # unmodified command output, saved responses
│       └── interpreted/# the distilled packet: control vs mutated, exit status, timestamps
├── scripts/            # reproducible scripts that produced the above
├── reports/            # human-facing deliverables
└── pocs/               # per-engagement PoC artifacts
```

## Rules

- **Check method eligibility before discovery or substantive corpus audits.** Read current program
policy and explicit scope before scheduling target traffic, passive discovery, workers or offline
bug hunting. Record whether automation, bots and AI/LLMs are permitted; an asset's eligibility or
a numerical request limit does not authorize a prohibited method. If the policy prohibits AI bug
discovery, stop agent-led discovery, including source/bundle analysis for new bugs; retain only
policy/scope reconciliation and a blocked handoff. A scanner-only prohibition is not automatically
an AI prohibition: preserve the actual wording. Resume only with explicit program authorization
covering the restricted methods and proposed assets. When the account owner supplies the program-side exception, take it once and record it rather than re-litigating: quote the wording verbatim into `scope.md`, label it **researcher-asserted**, state what provenance you were and were not given (channel, sender identity, timestamp) so it is auditable and reversible, and name the readings you decided. Asking once is diligence; asking a third time after an answer is refusing to work, and the user reads it as not knowing the job. Then hold the footprint to the narrowest defensible reading of the exception — one GET per listed host, no brute force, no template spray, no redirect following, rate under the program's own published limit — and when the exception imposes its own condition on the output ("the bug needs human validation"), tag every resulting finding with it. A method permission never widens the asset list: an exception allowing AI assistance does not authorize an unlisted host. Keep a blocked
checkpoint small: raw policy/export, necessary scope comparison, one blocker event and corrected
startup state; do not launch scanners, create worker scaffolding or build a new report generator.
- **`scope.md` first.** Write targets, exclusions, allowed schemes/ports/path prefixes, IP/CIDR
ownership, auth context, and request limits before the first scan. This is the contract every
later step is checked against.
- **Derive `scope.md` from the supplied export with a real CSV parser.** Quoted instruction
fields may contain newlines; physical line counts are not asset counts. Preserve literal identifiers,
asset types, instructions and eligibility flags, and keep both the original and its provenance copy
byte-identical. Treat a descriptive filename as a hint, not proof of program identity; reconcile
identifiers with the program's published scope and policy. Distinguish submission eligibility from
bounty eligibility: `eligible_for_bounty=false` alone does not mean excluded, but a missing
`eligible_for_submission` field does not establish authorization either. Obtain the complete current
export before classifying unpaid rows as testable; `eligible_for_submission=false` excludes them
even when their names appear in the asset table. If policy is gated, record the missing authorization
conditions as a blocker; an unauthenticated `Team does not exist` response does not prove the
program is absent. Use `references/hackerone-scope-refresh.md` for rendered-policy capture and the
complete CSV download workflow.
- **Reconcile scope before producing an operational allowlist.** When refreshing an API snapshot,
follow pagination to its explicit terminal marker and save every raw page plus a manifest of cursors,
page counts and completion state. Compute raw row counts and unique `(asset_type, asset_identifier)`
sets separately, compare the export/API sets in both directions, and preserve duplicate rows with
instruction variants. A page-size limit is not a total, and equal identifiers do not prove equal
restrictions. Apply named exclusions before wildcard inclusion. Save corrected scope as a new
snapshot, identify which prior interpretation is superseded, and rebuild downstream allowlists;
never reuse a discovery list as authorization merely because it was previously probed.
- **Set one engagement-wide traffic budget in `scope.md`.** Record policy limits, the chosen
aggregate request rate, finite per-pass request caps, redirect policy and permitted methods. Allocate
that budget across tools/workers and include retries and followed redirects in actual traffic
accounting; separate per-tool limits do not enforce an aggregate ceiling. Count **browser
navigations** as target requests too, and state that page subresource loads are an uncounted
accounting gap rather than claiming complete network accounting. When the work type changes —
source review to an authenticated browser session, say — a raised ceiling is a new budget
**decision** recorded in `scope.md` and the resume index, never a silent extension; and raising it
is not a permission change, because scope, exclusions and prohibited flows stay exactly as they
were.
- **Where no scope export exists, capture the brief from the rendered page.** Bugcrowd publishes no
scope CSV and no usable brief API: `/engagements/<slug>.json` answers **HTTP 406 Not acceptable**,
and the engagement page is a JS shell whose brief text never appears in the HTML source (grep it for
`target`, `in_scope`, `reward` — zero hits). Render the page in a real browser, expand every
"Show more", and take `document.body.innerText` into `evidence/program-brief/raw/`; that rendered
text is the source of record that `scope.md` is derived from. The rendered page also carries a
`data-api-endpoints` attribute naming the JSON routes beside it — `/engagements/<slug>/{statistics,
scope_ranks,hall_of_fames.json,announcements}` answer unauthenticated, while
`/engagement_known_issues.json` returns 401. Record the gated one as a blocker: per-target duplicate
risk is unquantified until someone reads it while signed in.
- **Capture the program's *policy* requirements in `scope.md`, not just its asset list.** The scope
export carries assets; the requirements that bind every request live only on the policy page: the
attribution header the program mandates on each request (HackerOne's
`X-HackerOne-Research: <handle>`, Bugcrowd's `X-Bug-Bounty: Bugcrowd-<username>`), prohibited flows
(e.g. no automated scanning on checkout/payment paths), request limits, the eligible-vs-VDP split,
and the reward bands. Get the handle from the user before the first active request — it cannot be
invented, and it must ride on every request from every stage, PD tools included (`httpx -H`,
`katana -H`, `nuclei -H`). Read the policy page and record them before the first
request — a pipeline built from the CSV alone silently violates them, and an unattributed scan
forfeits the safe-harbour footing the program otherwise grants.
- **Read an exclusion that names a credential or an asset as scoping out a vulnerability *type*, not a host.** "<Product> fan account credentials" on the out-of-scope list excludes reports *about those credentials* — leaks, credential stuffing, weak password policy, takeover of such an account. It does not remove the host or the application from the program. Decide the reading deliberately, write it into `scope.md` with the reasoning, and keep the work inside it (authenticated access control and data exposure are a different class from credential mechanics) — so the interpretation is auditable and reversible if the program clarifies.
- **Raw before filtered.** Scanner output goes to `scans/` **unfiltered**. Re-filter from disk
instead of re-running the scan. A filtered file is a derivative, never the record.
- **Never edit supplied inputs.** If the user hands over a file, leave it byte-identical and write
derivatives under the engagement root.
- **Evidence keeps both layers.** `raw/` proves what happened; `interpreted/` is the trimmed
packet. Do not delete the raw layer because the summary looks complete.
- **Freeze audit inputs before dispatch.** Bind each input path, byte size, hash and parser/record-count convention in a manifest. Exclude new producer outputs and evolving sibling-worker directories from corpus totals; a live snapshot is not a canonical total.
- **Read JSONL by LF-delimited records.** Iterate the file or split on `\n`; `str.splitlines()` also splits Unicode separators inside valid JSON strings and can manufacture malformed records. State the line-count convention and retain the original bytes.
- **Verify handoff offsets against bytes.** A matching file hash plus an in-range offset is insufficient: the referenced route/call must actually occur at that offset. Record whether the producer measured UTF-8 bytes or decoded characters; preserve its original annotation and emit any corrected byte pointer separately. Retain failed annotations separately; client read-only classifications do not prove server side effects or authorization.
- **Resume by exact request identity.** Keep method, literal URL/query, raw request-body digest and auth context in the actual-request ledger. Compare new proposals against that ledger before execution; source patterns and HEAD checks do not replace concrete GET/POST evidence.
- **Review sentinel semantics.** Empty or zero IDs/counts can mean current object or all records, not nonexistent. Keep researcher-selected invalid values distinct from source defaults, avoid private-list queries without owned fixtures, and stop on unexpected success/data.
- **One directory per parallel worker.** `scans/<worker>/` — parallel workers and subagents must
never share an output path.
- **Scripts are artifacts.** Anything non-trivial enough to re-run belongs in `scripts/`, invoked
by path, so the run is reproducible.
- **Reports are not evidence.** `reports/` holds prose for humans; the proof lives in `evidence/`
and `scans/`. Never let the report be the only record of a finding.
- **Log each confirmed finding as it lands, then keep hunting.** Give every finding its own
`reports/findings-<asset>-<class>.md` carrying the evidence pointers, the reproduction *including any
request precondition*, the honest severity ceiling, and the verified negatives that bound it — then move
to the next class or lane. Hunting is not gated on a filing decision: do not stop the sweep to ask
whether to write a submission-ready report, and do not present "should we file this?" as the next step
unless submission text was requested. A note recording why a finding is *not* bigger is as valuable as
the finding, because it stops the next session inflating it.
- **When the user names a lane, switch lanes without ceremony.** A blocked host or an exhausted angle is
a reason to pick the next evidence-backed target, not to re-litigate the blocker. Keep the blocker
recorded and move on.
- **A lead that needs to leave the allowlist is a scope decision, not a judgement call to make quietly.**
Neither cross the boundary nor drop the lead: name the exact endpoints, the standing constraint they
violate, and what the check would prove, then ask once. Stay inside what was authorised, and verify
rather than assume — a data-layer hypothesis that comes back closed is a better outcome than an
inflated report.
- **Everything stays under the engagement root.** Do not write into a sibling engagement, and do
not scatter output into `$HOME`, `/tmp`, or the user's unrelated directories.
- **A PoC promoted to a finding** gets an unambiguous path that can be quoted in a report.
- **Record functional siblings without expanding authorization.** Client calls, redirects, links
and form actions identify dependencies, not permission to test them. Record
`host<TAB>role<TAB>flow_evidence<TAB>verdict` in `functional-sibling-hosts.tsv` beside `scope.md`;
add a host to the operational allowlist only after checking its literal scope match, exclusions,
instructions and ownership. An exact `www.X` listing does not automatically authorize `api.X`.
Use the client's gateway/base-URL configuration as evidence of use (see
`projectdiscovery-toolchain`'s `references/api-surface-from-bundle.md`). Keep external provider-native
API hosts pending scope clarification even when an in-scope app calls them. A shared cloud/CDN
CNAME alone neither establishes nor disproves tenant ownership; distinguish the scoped customer
application from the provider's infrastructure. Mark excluded dependencies `out-of-bounds-by-policy`
and send no requests to them.

## Mandatory lead catalogue and project handoff

Apply this on **every scope handoff and every new BB project**, without waiting for a vulnerability.
A lead is target information: service, technology/fingerprint, route, API/method/parameters/auth,
functionality, dependency, JS/source map, negative result, blocker or hypothesis — not just a bug.

Before target traffic, create or read **`AGENTs.md`** (preserve this exact filename), `scope.md`,
`reports/lead-ledger.jsonl` and `reports/LEADS.md`. Populate the lead ledger with supplied-scope facts;
do not leave empty placeholders. Read existing artifacts and leads before scheduling any new work.
Use `references/lead-catalog-and-handoff.md` for required fields and checkpoint contents.

After **each tool stage**, ingest every useful observation and exclusion/blocker into the canonical
lead ledger, with raw evidence and observed/inferred distinctions, before choosing the next stage.
Register leads before dispatch; root specifies one versioned packet schema and evidence-pointer
convention, workers return isolated packets in that schema, and root merges and verifies them.
Bootstrap missing catalogues from scope and verified stage evidence before broader audits, but label
that checkpoint partial: asset/request events do not constitute a complete service/API/JS/map catalogue.
Use installed ProjectDiscovery CLIs directly for discovery/probing; custom code is for offline
parsing, reconciliation and verification, not a replacement network enumerator or unnecessary runner.

### Required target-selection deliverable

Make the catalogue usable for choosing the next target, not merely counting observations. Start
`reports/LEADS.md` and the user-facing result with a small ranked shortlist, grouped into
**chase now**, **blocked on a named prerequisite**, **paused/capped**, and **skip**. Each entry must
name the exact host and functionality/operation, why it merits attention, raw evidence pointers,
what actual requests and controls established, the genuinely untested angle, and one bounded
policy-permitted next action. Put inventory totals and full grouped catalogues after this shortlist.
If no target is chase-ready, say so and identify the best evidence-backed unblock action; do not
invent a candidate to fill the list. Source-visible routes are work orders, not proven vulnerabilities.

When asked to verify all ongoing results, disposition every producer event and contract row before
claiming the audit complete. Preserve originals, separate corrected and unsupported claims, and
independently verify worker packets before the canonical merge. Include new raw/control observations
in the shortlist only after that verification; file existence, parsed counts and hashes alone do not
prove actionable leads. Use the packet-audit and ranking procedure in
`references/lead-catalog-and-handoff.md`.

Before ending, pausing or handing off a session, refresh `AGENTs.md`, the human lead index and the
resume index from actual evidence: counts/budget, completed/failed/untested work, active workers,
next bounded actions and exact artifact paths. Document JS/map relationships and source-map
coverage explicitly; an untested map is **pending**, not absent. Another session must be able to
resume without reading chat or repeating discovery.

## Resuming without overlapping work

1. **Intake before full inventory.** Read `AGENTs.md`, `scope.md` and the resume index, then check
   current policy for method eligibility before a substantive offline audit or worker dispatch.
   If the authorization gate blocks the requested method, follow the small blocked-checkpoint recipe
   in `references/hackerone-scope-refresh.md` and stop discovery. Otherwise read progress reports,
   angle/coverage ledgers, scripts and raw logs, then enumerate regular artifacts under the
   engagement root before new target traffic. Record
   relative path, byte size, hash, empty state and parse/completion status in a saved manifest.
   Distinguish original artifacts from files created by the audit; do not count directories as files.
   Hashing all files proves inventory coverage, not that their contents were substantively reviewed.
2. **Reconcile claims against evidence.** Parse JSONL programmatically with explicit counts for
   valid records and malformed physical lines; retain file/line provenance. Separate discovered link
   references from actual request/response records. Save salvage to a new derivative, never repair
   the raw capture in place. Inspect scanner stderr, inputs, template loading, exit status and terminal
   completion evidence together: `DONE` in a wrapper or an empty findings file cannot override a
   fatal error or prove that every batch ran. Reconcile stages newer than the last resume index into
   the exact-request ledger, then recompute cumulative totals, per-origin usage and remaining
   allocations before any new traffic. Preserve prior snapshots and mark which index supersedes
   them; a resumed session does not reset an exhausted per-origin cap. Label every request total
   by its accounting window: a continuation ledger is not an engagement-wide historical total.
   Report uncertain/failed attempts separately rather than presenting response counts as complete
   network accounting.
3. **Refresh authorization before scheduling.** Capture current policy and complete scope, compare
   identifier/type sets in both directions, and compare eligibility/instructions separately. Equal
   asset sets do not validate an abbreviated export. Replace stale budget/exclusion language in
   `scope.md`; preserve old raw lists as history and name one corrected operational allowlist.
4. **Write progress before dispatch.** Create a root-owned progress file under `reports/` identifying
   verified prior work, failed/partial coverage, blockers, reserved lanes and the next acceptance
   criteria. Assign isolated offline audits of independent corpora when content review is substantial;
   reserve output directories and source sets so workers do not duplicate extraction or target traffic.
5. **Select only new evidence-bound work.** Build a do-not-repeat set keyed by exact method, URL,
   auth context and tested mechanism. Reopen a prior angle only for a documented material change or
   missing proof. Give active workers a finite reviewed request manifest and shared aggregate budget;
   scope corrections take effect in every lane before any further request.
6. **Merge and document from disk.** Verify worker artifacts, recompute counts, update coverage and
   progress with evidence paths, and keep failed, blocked and untested shapes distinct from negatives.
   Report inventory completion separately from content-audit and active-test completion; do not call
   the pipeline complete while a substantive audit or verification handoff remains pending.

## Neo sandbox mapping

Only relevant when work runs inside the Neo/agent-swarm platform. Local Hermes sessions write to
the engagement root above and never to `/workspace`.

```
/workspace/tasks/<taskId>/     ← the Recommended Run Artifact Directory; all authored output
  .neo/                        platform bookkeeping — never edit
  .tool-output/                auto spill dir — read by exact path, never write manually
  kb-context/ evidence/ manual-probes/ scans/ scripts/ reports/ pocs/
```

- **`.neo/`** holds `_files.db` (the persistence registry behind `write_file`). Never delete or
hand-edit it.
- **`.tool-output/`** is auto-populated when a tool result is too large for inline return. When a
result carries `_spilled_to`, read that exact path — never re-invoke the producing tool just to
re-fetch the full dump. Each payload keeps a `_meta` provenance record (tool, call id, task id,
exact input).
- **`/workspace/pocs/`** (root-level, not task-scoped) is the path the Neo verification contract
expects for a `poc_artifact` — distinct from the per-task `pocs/` above.
- **Shared dirs are convention, not guarantees.** `subagents/` and `seclists/` may be absent;
create or clone them rather than assuming. Missing wordlists are a setup gap, not a clean scan.
- **BYOS dual plane:** `run_command`/`execute_script` run in a Linux confine image, while the file
APIs, browser, and computer-use tools talk to the **host**. `/workspace` maps to the durable
install workspace, so a path that works for one plane may not exist in the other.
- **File sharing is restricted to `manage_unlisted_file_url` and `web_test_files` (0ac.io);**
otherwise return workspace paths.

Full detail: `references/neo-sandbox-paths.md`.

## Pitfalls

- **Writing `/workspace/...` from a local session.** On the user's machine that path does not
exist. Linux `/workspace` is Neo-only; locally use the engagement root.
- **Creating the whole tree as empty scaffolding.** Skip directories the engagement doesn't need —
empty `pocs/` and `manual-probes/` are noise.
- **Letting a filter overwrite its input.** `httpx -o scans/probe.jsonl` then filtering that file
in place destroys the unfiltered record. Write the filtered set to a new name.
- **Two workers on one output path.** Each parallel worker gets its own subdirectory.
- **Treating a missing tool or wordlist as a clean result.** Absent tooling is a blocker to
record, not a negative finding.
- **Scratch files in the engagement tree.** Throwaway probes go to the Hermes scratch directory,
not into `evidence/`.
- **Do not inline multi-line shell `for`/`while` loops in a terminal command string.** Loop bodies get mangled or silently dropped on the way into the shell, so the stage reads as done while it did something else entirely; write the loop to `scripts/<name>.sh` and invoke it by path — which also satisfies the scripts-are-artifacts rule.
- **Backslash line-continuations in a written script can arrive corrupted and split one command into several.** A `\`-continued multi-line command that loses its trailing backslashes executes line-by-line as separate commands: the first fragment runs as a bare invocation, a later fragment becomes a `command not found`, and the output file is never created — which reads as "the tool produced nothing" rather than "the script is broken". Prefer single-line invocations for one-command stages, and after any script edit re-read the file (or run `bash -n <script>`) before executing it; never re-run a stage whose output file is missing until the script that writes it has been inspected.
- **A long stage that buffers its output loses all of it.** A probe script that writes once at the
end (or holds results in memory and prints at exit) yields nothing when a timeout kills it, so a
run that was 90% complete leaves no record at all. Stream each result to disk as it is produced —
append and flush per record — so a killed run keeps its progress and is resumable.
- **Create the output directory before the command that redirects into it.** `cmd > scans/new/x.log`
fails *before* `cmd` runs when `scans/new/` does not exist, and the only symptom is a missing file
(or a background job reporting "no such file or directory") — it reads like the command ran and
produced nothing. `mkdir -p` the stage's directory first, then launch.
- **A prior report's claim is not inherited scope.** When resuming, check the *target* of every
  existing report claim against the current allowlist and exclusions before building on it. A claim
  whose target is the redirect destination — an identity provider, CDN or SaaS host the in-scope app
  authenticates through — is a claim about provider-native infrastructure, which the program excludes
  even though the in-scope app legitimately calls it. Require an evidence pointer as well: a severity
  plus a "confirmed by dynamic testing" sentence with no raw artifact is an untriaged draft, not a
  finding. Surface such files to the user and move them out of the deliverable path with a written
  reason; never let their assertions stand while working the same host, and never carry them into a
  submission.

## Verification

Before reporting an engagement as complete, confirm the layout actually holds — read the tree
rather than trusting that writes succeeded:

```
search_files(pattern="*", target="files", path="<engagement>", limit=100)
read_file(path="<engagement>/scope.md")
```

For executed recon, check all four: raw scanner output exists under `scans/`, each claimed finding
has both `evidence/<finding>/raw/` and `interpreted/`, scripts referenced by the report exist in
`scripts/`, and no finding is recorded only in prose in `reports/`.

For a policy-only blocked checkpoint, verify the captured prohibition and scope comparison against
raw evidence, the blocked startup state and zero remaining agent budget, the preservation of prior
inputs, and browser-group cleanup. Do not require or create scanner output for a stage that never
ran; report authorization reconciliation as complete and recon as not executed.

## MANDATORY ON INVOCATION — PROTOCOL RESTATMENT (END OF FILE)

You have reached the end of this SKILL.md. The invocation protocol below is identical to the one at the top of this file. If you are reading this, the full skill context is loaded — confirm the checklist.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/hackerone-scope-refresh.md`, `references/lead-catalog-and-handoff.md`, `references/neo-sandbox-paths.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

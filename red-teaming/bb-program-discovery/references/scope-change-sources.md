# Sources for new programs and newly added scope

All free/unauthenticated unless marked. Listings drift daily — re-verify before quoting.

## HackerOne

- **Directory (newest launches):** `https://hackerone.com/directory/programs` — rendered table sorted by **Launch date desc**. Columns: Program, feature tags (Managed / Retesting / Collaboration), Launch date (MM / YYYY), Reports resolved, Bounties min / avg. Filters: Offers bounties, IBB, High response efficiency, Managed by HackerOne, Asset type (Domain, CIDR, Wildcard, Source Code, API, AI Model, Smart Contract, iOS/Android, Executable, Hardware, Other).
- JS-rendered: `new_tab` → `wait_for_load()` → sleep ~4s → `js("document.body.innerText")`. The first paint returns only the nav.
- **Per-program scope (freshness ground truth):** `https://hackerone.com/<handle>/policy_scopes` — per-asset **Last update** column, "**View changes** (Last updated on <date>)" link, coverage in/out of scope, max severity, bounty eligibility, resolved-report counts, plus Burp project + CSV downloads.
- **Machine-readable scope:** the GraphQL `team(handle:)/policy_scopes` query already documented in the `bug-bounty` skill ("HackerOne Scope Retrieval"). Use it when you need many programs' assets at once instead of the rendered HTML.
- Program card carries the competition signal: total bounties paid, average/top bounty, bounty volume and reports received over 90 days, last report resolved, reports resolved, assets in scope.

## Bugcrowd

- **JSON, no auth, curl-friendly:** `https://bugcrowd.com/engagements.json?category=bug_bounty&page=1` — per engagement: `name`, `briefUrl`, `rewardSummary{summary,minReward,maxReward}`, `badgeVariant`, `productEngagementType.label`, `industryName`, `accessStatus`, `isPrivate`. Send `Accept: application/json` and a normal browser User-Agent.
- Human page: `https://bugcrowd.com/engagements?category=bug_bounty&page=1` (where `/programs` redirects).
- **Traps:** appending any `sort_by=` value other than `promoted` to the `/engagements` URL renders a blank page (only the login links). The Sort control is a React popover that does not open from a JS `.click()`. Take ordering and badges from the JSON endpoint instead of fighting the UI.
- `badgeVariant: "updated"` is a **rotating promotional badge, not a scope-change changelog** — observed on 1 of 48 engagements in one pull and on a different program in the next. Never present it as "this program changed scope recently".

## Intigriti

- **Public list:** `https://www.intigriti.com/researchers/bug-bounty-programs` — "Sort by: Newest programs", "New" badges, industry and program-type filters, VDP vs bounty. Programs link out to `app.intigriti.com/programs/<company>/<handle>`.
- `https://app.intigriti.com/programs?status=public&sortBy=NEWEST` renders "We didn't find what you're looking for" — use the researchers URL.
- Per-program **Updates** tab is where launches and scope changes are announced, including platform migrations (a program moving platforms states its cutover date there) and per-severity reward tables.

## bbradar.io (aggregator)

- `https://bbradar.io/` — public programs across HackerOne, Bugcrowd, Intigriti, YesWeHack, HackenProof, Immunefi, Sherlock, Cantina, CertiK, Huntr, Standoff365, Compass Security, AuditOne, BI.ZONE, Bugbase, BugRap, GObugfree, HackZar, Inspectiv, IssueHunt, PatchDay, Remedy, SignalFisher. Free view: listing date (newest first), platform, reward range, tags, `New` / `Upcoming` flags, upcoming-contest toggle, per-platform listings.
- `https://bbradar.io/latest-targets` — the global per-target add/remove feed with "added N days ago" and bounty eligibility. **Pro-gated**: target identities, dupe-risk scores and Telegram alerts sit behind the paywall; the homepage teaser shows counts only (e.g. "33 target changes · 24h").
- Use it to see which platform the week's activity is on, then verify on the platform itself.

## Reading pages

JS-heavy program listings (HackerOne directory, Intigriti) need the browser: `browser_exec` + `js("document.body.innerText")` after `wait_for_load()` and a short sleep. Plain URL extraction depends on a configured extract backend, so when an extract call fails on backend grounds, switch to the browser rather than retrying the extractor.

## Verify-on-platform rule

Whatever an aggregator or a news post says, the program's own scope page decides: assets are frequently tier-gated (a wildcard may pay at a lower tier than the rest of the scope) and are occasionally added then removed inside a week.

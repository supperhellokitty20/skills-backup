# Refreshing HackerOne scope and policy

Use when a supplied export is abbreviated, authorization fields are missing, or a resumed
engagement relies on an old policy summary. Keep the original export byte-identical.

## Procedure

1. Load the browser-surface skill and check its prerequisites. With Interceptor, use
   `interceptor init --verbose`, then a task-owned background group:
   `interceptor --group <group> open https://hackerone.com/<handle> --text-only`.
   Read again after the program loads; the initial page can be only a navigation shell.
   Save the complete text with
   `interceptor --group <group> read --text-only --full > <root>/evidence/program-brief/raw/policy-rendered.txt`.
   Verify the capture contains rules of engagement, method eligibility (automation, bots, AI/LLMs),
   numerical traffic limits, prohibited flows, environment/internal-system exclusions, vulnerability
   exclusions, attribution requirements and stop conditions. Extract these into `scope.md`; do not
   substitute a search snippet or structured asset API for the rendered requirements. Check the
   method gate immediately: a rate ceiling does not override a prohibition. If agent-led discovery
   is prohibited, perform only the policy/export reconciliation below and the blocked checkpoint;
   do not inspect target sources for new bugs or schedule passive/active discovery.
2. Open `https://hackerone.com/<handle>/policy_scopes` in that group. Record the visible total,
   scope filters and update metadata, but do not treat the first displayed page as the full list.
3. Discover the CSV link rather than guessing it:
   `interceptor --group <group> query 'a[href*="csv"]'`, then
   `interceptor --group <group> attr e<returned-ref> href`.
   `attr` takes the element ref, not the selector. Resolve relative hrefs against the current
   document URL with `urllib.parse.urljoin`. On a rendered page, native query/attribute reads can
   retrieve this link without JavaScript eval or a CSP-changing reload.
4. Fetch the discovered complete CSV once with standard tooling:
   `curl --max-time 30 --retry 0 -sS -D <root>/evidence/program-brief/raw/scope-current.hdr <resolved-url> -o <root>/evidence/program-brief/raw/scope-current.csv`.
   Inspect status and content type, then parse with `csv.DictReader`; an HTML login/error response
   is not a scope export. If the download requires authentication, use the approved browser/vault
   path rather than extracting cookies or asking for credentials in chat. Save the exact URL,
   command, source hashes and completion evidence in the reconciliation manifest.
5. Compare raw row counts and unique `(asset_type, identifier)` sets separately. Map an abbreviated
   source's field names explicitly; do not change literal identifiers to make sets match. Compare
   both set differences and inspect submission/bounty eligibility plus every instruction. Preserve
   duplicate instruction variants. If consuming a paginated API instead, capture every raw page and
   its cursor chain to an explicit terminal marker.
6. Build an operational allowlist only if the requested method passed the policy gate, then apply
   submission eligibility, instructions, exclusions and ownership checks. Otherwise retain the export
   as listed-asset metadata, not an agent allowlist. `eligible_for_bounty=false` with submission true
   may be an authorized unpaid asset; both false means excluded. Missing submission eligibility is
   unresolved, never implicit permission. Check wildcard membership explicitly in the complete
   current export: an old wildcard, exact apex listing, public DNS record or historical successful
   probe cannot authorize a sibling hostname. Keep original lists historical and explicitly mark
   superseded interpretations in `scope.md` and the progress report.
7. Close only the owned browser group and verify it is absent from `interceptor group list`.

## Blocked-checkpoint recipe

1. Save the exact prohibition with its policy source, capture time and line/text anchor; save the
   complete export when available. Report a gated or incomplete source as unresolved, not permission.
2. Compare current and saved scope with `csv.DictReader` and parsed JSON: retain literal identifiers,
   raw/unique counts, both-direction set differences and instruction/eligibility changes. Print counts
   and meaningful differences rather than dumping the whole historical host inventory into context.
3. Mark `scope.md` and `AGENTs.md` blocked, set the agent request budget to zero, and append the
   evidence-backed blocker to the existing lead catalogue. Record actual continuation traffic
   separately from historical or unknown totals; policy-platform retrieval is not target traffic.
4. Preserve a byte-identical before-image before correcting a prior agent-authored scope/handoff.
   Put the warning where future sessions start, including a prior multi-program project's scope;
   limit it to the affected program. Preserve supplied inputs and raw scans unchanged. Bind a hash
   manifest to the immutable before-image, not the subsequently edited document, or explicitly
   regenerate the mutable-state manifest after the edit.
5. Close and verify the owned browser group. Deliver the blocker, evidence path, actual target-request
   count and precise authorization needed to resume. Do not claim recon or vulnerability review
   completed. Use existing handoff files and a concise checkpoint; a policy stop does not warrant a
   new multi-report generator, unused scan directories or duplicated inventories.

## Evidence hygiene

Keep raw captures local and access-controlled. Inspect only the relevant policy/export fields in
tool output; do not dump whole network-header captures, which may contain session cookies, CSRF
values or unrelated authentication headers. A policy page refresh does not authorize testing the
platform itself or third-party dependencies.

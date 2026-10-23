# Lead catalogue and AGENTs.md contract

## Trigger and ownership

Use on every supplied scope, new engagement and resumed BB project. Root owns canonical project state; workers write isolated packets only. Initialize state before target traffic. On resume, read AGENTs.md, scope.md, the lead catalogue, resume index, progress, angles and relevant raw artifacts first. Hashing a corpus does not prove substantive review.

A lead is any useful fact about the target, not only a vulnerability candidate. Keep a machine-readable append-only event ledger at reports/lead-ledger.jsonl and a human-facing grouped index at reports/LEADS.md. Original raw captures stay unchanged. Treat missing context as UNKNOWN, not an invented fingerprint or service.

## Required lead fields

Each record binds:
- lead_id, event_id/schema version, observation/ingestion time, original capture time when available;
- exact asset identifier/type, host, literal URL or unresolved path expression, scope/ownership verdict;
- kind: asset, service, technology, fingerprint, route, api, functionality, parameter, auth, dependency, js, source_map, negative, blocker, hypothesis or finding;
- observed facts, method, exact path/query, parameter/body field names and expressions, auth context and header names (not secret values);
- service/product/environment, technology/version/fingerprint evidence, functionality and data class where source-supported;
- status/disposition, confidence and whether information is observed, source-declared, tool-inferred or independently verified;
- raw evidence path, source URL, file hash, line/byte offset or schema pointer, tool/version/command where available;
- relationships to asset, service, JS parent, source map, operation, control, environment or dependency;
- tested actions/evidence, negative result/blocker, owner and next permitted action.

Use null/UNKNOWN for fields that do not apply. Preserve literal identifiers and exact method/query/body distinctions. Keep raw request-body digests and auth context for deconfliction; do not merge different operations because their path looks similar. Attach multiple source observations and conflicting versions rather than overwriting evidence. Retain excluded hosts and vendor references as metadata, not authorization.

Do not store passwords, bearer tokens, cookies, private keys or verification codes in the lead/handoff files. Use redacted identifiers and access-controlled raw evidence or vault references.

## Stage-by-stage coverage

1. Scope intake: catalogue every provided asset, instruction, eligibility/exclusion and authorization gap. Distinguish listed from eligible/owned/testable.
2. Discovery/DNS/HTTP: catalogue services, CNAME/provider relationships, redirects, IP associations, titles, technologies, headers, fingerprints and response families. Tool detection is not proof of vulnerability or IP authorization.
3. Routes/APIs: catalogue every observed exact operation, parameter/auth/body contract, workflow and functionality, including protected, rejected, untested and modifying operations. A method name or client read-only classification does not prove server safety.
4. JS/source maps: keep source URL/hash to each advertised sourceMappingURL or SourceMap/X-SourceMap header; resolve maps against their parent, check scope, validate map JSON and safely bind reconstructed sources. Record relative-parent-unknown, inaccessible, inline/runtime false-positive, invalid, incomplete, vendor-only and not-yet-probed dispositions. Never infer no map merely because no map file was downloaded.
5. Validation: link baseline, mutated input, controls and real outcomes. Status codes, metadata, route visibility or public browser IDs are leads, not confirmed exploits. Stop on sensitive-data/account/RCE boundary crossing and follow policy.
6. Checkpoint: ingest the stage before selecting another branch, dedupe/count programmatically and refresh the human index/handoff. Preserve negatives and blockers so they are not retested without a materially new mechanism.

## Verify producer packets and select targets

Use this procedure when accumulated recon output exists but the researcher cannot tell what to
chase. Reuse saved evidence; verification does not itself require new target traffic.

1. **Freeze the audit boundary.** Read scope, canonical ledgers, producer packets, actual-request
   indices and progress. Bind each packet path/hash, LF-delimited record count and event-ID set in
   an input manifest. Label historical and continuation request accounting separately. Keep evolving
   root handoff files outside immutable raw-evidence totals; a documented root-index edit is not
   evidence corruption.
2. **Assign exhaustive dispositions.** For large independent corpora, delegate isolated offline
   lanes with a shared output contract: per-event verification, corrected verified packet, rejected
   or unsupported claims, audit summary and target shortlist. Require one disposition per original
   event and per API contract row, keyed to original IDs/row provenance. Root retains canonical
   merge and verdict authority. Reconcile input IDs against output IDs, not just equal row counts.
3. **Verify semantic anchors.** Hash each referenced source once, then check the exact logical CSV
   row, physical LF line, JSON pointer or byte offset against the claimed identifier, route, method,
   status or fingerprint. A hash verifies file identity, not the claim. Resolve character-versus-byte
   offsets explicitly. Leave unanchored claims unsupported until an independent anchor is found.
   Verify client API method, base URL, parameters and auth at real callsites; keep method UNKNOWN
   when a static route extractor did not resolve the caller, rather than inheriting a placeholder GET.
4. **Reconcile actual controls.** Match method, literal URL/query, raw-body digest and auth context
   against saved requests. For ffuf audits, compare decoded request/response bodies and digests;
   retain HEAD body-not-captured separately from an empty GET body. Handle known producer schema
   aliases explicitly in a derived representation without changing original records. Compare HTTP
   header names case-insensitively, but preserve header values and literal identifiers. For PD output,
   bind response rows to raw envelopes; never count failed references as successful requests. Record
   missing request traces as verification limits. Completion timestamps do not prove request-start
   spacing. Treat catch-all200, HEAD405, missing-credential401 and impossible-path500 as their exact
   tested observations, not authorization bypasses or comprehensive safety verdicts.
5. **Build actionable work orders.** Group by exact scoped host and source-supported functionality.
   Rank by reachable surface, concrete data/authorization boundary, novelty versus prior tests, and
   whether prerequisites can be obtained within policy. Each shortlist row includes host/operation,
   evidence paths with anchors, tested outcome/control, untested angle, missing prerequisite,
   next permitted action, and chase/blocked/paused/skip disposition. Keep employee-only surfaces
   blocked without owned sessions, caps exhausted without a new budget decision, and excluded
   dependencies outside testing. Downgrade generic routes, framework noise and public metadata;
   do not label a source-only hypothesis CANDIDATE as if a vulnerable primitive were demonstrated.
6. **Verify and merge at root.** Check worker output IDs, counts, source hashes and semantic
   assertions; preserve failed annotations and correction provenance. Append correction events
   linked to originals rather than silently rewriting historical claims. Publish the ranked shortlist
   before the full catalogue in LEADS.md and the final answer. Update the resume index with actual
   producer/verifier states and distinguish completed output, verified output and merged output.
   If verification is still running, mark the checkpoint partial and keep rankings provisional.

### Negative-result taxonomy for wildcard-estate recon

Label verified non-findings explicitly so the next session does not retest them. The recurring
shapes, each with its one-request-or-fewer disproof procedure:

- **No dangling CNAME / no takeover:** for every off-domain CNAME target, re-resolve the host with
  fresh DNS (`gethostbyname_ex`) — a target that still resolves to the provider's IPs and serves
  owner content or a redirect is a verified negative, not a "didn't check".
- **OAuth client-enumeration absent:** send one malformed token request (bogus client + bogus
  grant). A *generic* error (`invalid_grant`, one message for all inputs) closes the angle; a
  *discriminating* error (`invalid_client` vs `invalid_request` by input) opens it. Record which
  shape was observed, not just "tested auth".
- **Open-redirect absent:** probe the redirect parameter with an absolute external URL. The
  parameter being absent from the rendered page, or the redirect landing on an error page, closes
  it; reflection into an HTTP `Location` or post-auth JS `location=` opens it.
- **401 with structured detail is a good sign, not a lead:** a JSON 401 with a request UUID
  (`{"status":401,"errors":...}`) says the route exists and auth is cleanly enforced — log it as
  the authenticated-testing work order, never as a finding.
- **Client-side config keys are context, not findings:** publishable keys, analytics write keys,
  S3 bucket names and DSNs in page-embedded config describe intended client integration. Record
  them in the lead ledger as environment evidence; do not put them on the shortlist without an
  additional capability they unlock (e.g. a write-key that permits arbitrary event injection).
- **Bot-walled surfaces are a tooling decision, not a negative:** when a non-browser UA gets 403 on
  app paths but CDN-hosted JS is freely fetchable, record the wall, mine the bundles offline, and
  mark the live-app check as requiring a browser session — that is `chase` with a named
  prerequisite, not `skip`.

## Findable target information and reversible cleanup

A shortlist is not an application dossier. Provide a root `README.md` entrypoint, `reports/targets/INDEX.md`, and one hostname-named dossier per eligible asset. Each dossier has source-supported product/functionality, saved status/title/stack/environment, auth/access requirements, client method/path/parameter hints, actual tests and controls, JS/map coverage, blockers and clickable local evidence with anchors. Mark scope-only and unobserved fields UNKNOWN; distinguish saved captures from current liveness. Keep excluded assets and mobile coverage gaps separately visible. Export a searchable host CSV; keep raw event totals out of the primary navigation.

For cleanup, freeze a regular-file hash manifest, archive superseded notes/runners and derived stages, and preserve mutable canonical documents in verified before-images. Keep original capture paths stable where possible. Record every moved prefix in a path-map journal; repair active evidence/state/dossier pointers without changing literal asset/request identities or raw capture bytes. Verify original-file preservation, all active evidence hashes and generated local links after moving. Immutable historical payloads may retain old paths: publish their resolver and label archived runners historical rather than pretending they are replay-ready. Test catalogue regeneration idempotently. Put human working notes outside generated dossiers.

## Target decision index (required alongside the catalogue)

The human checkpoint includes `reports/TARGETS.md` and a machine-readable target shortlist. Their output contract is: a small ranked set of target-specific work orders; exact operation and source/response evidence; what actually ran and its controls; the genuinely untested question; missing owned fixtures; the next policy-permitted action; and readiness (`chase-offline`, `chase-active`, `credential-blocked`, `paused`, `capped`, `skip`). Rank investigative value separately from vulnerability severity. A blocked 401 baseline belongs in a conditional workstream, not the chase-active tier. State plainly when no demonstrated unblocked exploit lead exists. Inventory/event totals remain a separate coverage section.

Verify worker shortlist proposals against the full corpus before publication. Bind whole-document JSON pointers by parsing the document; do not reject them merely because no line is given. Check historical bundle identities before declaring a collection gap. Preserve all event dispositions, but quarantine non-binding pointers rather than inheriting a worker's success flag. Use exact request/body/auth identities for traffic accounting; repeated copies in comparison ledgers are not additional requests. Cache each file digest once during large packet verification.

Keep client contracts qualified: `withCredentials:false` is not cookie authentication, body-field extraction is not a proved server schema, and runtime-generated library inline-map templates are not parsed application maps. Preserve original packets and prior canonical snapshots when publishing corrections.

## AGENTs.md required sections

- Project identity, root path, operator and researcher attribution; exact scope/policy source and freshness.
- Startup read order and authoritative lead/coverage/resume artifact paths.
- Program restrictions, exact operational allowlist, ownership rules, methods, aggregate rate and remaining finite traffic budget.
- Current state with capture/checkpoint timestamps; completed, failed, partial, excluded and never-executed branches.
- Active/completed worker lanes, ownership and output roots; no stale claim a worker is running.
- Target/service/stack/functionality overview and highest-value open leads, backed by catalogue entries.
- Do-not-repeat request/angle registry, source-map coverage and known false positives/parser/tool pitfalls.
- Next prioritized bounded actions and their prerequisites; missing credentials/owned fixtures listed plainly.
- Direct tool paths/versions and command/provenance logs; installed PD tools first, no invented HTTP harness.
- Verification/cleanup requirements and when to update the document again.

AGENTs.md is an operational handoff, not an expansion of authorization. Update it after each meaningful stage and before every pause/end; retain the detailed event history and raw evidence underneath it.

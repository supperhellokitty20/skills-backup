---
name: projectdiscovery-recon
description: Enumerate authorized web assets, files, directories, API paths, parameters, and JavaScript endpoints with composable ProjectDiscovery CLI pipelines. Use for ProjectDiscovery recon, attack-surface inventory, content discovery, or chaining subfinder, dnsx, naabu, httpx, urlfinder, katana, and selected Nuclei discovery templates. Produces scoped inventories with provenance; exploitation and broad vulnerability scanning are separate tasks.
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `agents/openai.yaml`, `assets/discovery-paths.txt`, `references/files-and-apis.md`, `references/operations.md`, `references/pipelines.md`, `references/toolchain.md`, `scripts/pd_data.py`, `scripts/test_pd_data.py` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# ProjectDiscovery recon

Build a reproducible inventory of reachable services, files, and API operations. Select relevant tools from the whole ecosystem; do not run every tool merely because it is installed. Treat pipelines as typed data transformations with scope checks at every expansion boundary.

## Start with the available scope

1. Read the user's targets, program rules, exclusions, existing artifacts, and prior authorization. Record exact hosts versus wildcard domains, allowed schemes/ports/path prefixes, IP/CIDR ownership, authentication context, request limits, and requested depth in `scope.md`. Reuse established authorization; ask only about missing scope that blocks the next action.
2. Choose the smallest mode that meets the request:
   - **Offline:** parse supplied outputs, JS, schemas, or captures; no network requests.
   - **Passive:** query external discovery providers; no requests to target services. DNS resolution, TLS handshakes, HTTP probing, and crawling are active.
   - **Standard web:** scoped resolution, HTTP inventory, passive URL merge, bounded crawl, JS parsing, and a short path list.
   - **Deep web:** add bounded permutations, authorized ports, selective headless/XHR capture, source maps, schema analysis, and targeted content discovery where established scope permits them.
3. Set a finite budget before active work. Example starting defaults: 5 HTTP requests/second, 2 workers, 1 crawl input at a time, depth 3, 2 minutes per crawl target, 1 MiB response-read cap, and at most 50 candidate paths per origin in the first discovery pass. User/program limits override these. Per-process limits add together; schedule phases sequentially or enforce a shared limiter. Estimate total requests, not just RPS.
4. Inspect binary paths, versions, local `-h`, and relevant config overrides. Resolve the Python `httpx` versus ProjectDiscovery `httpx` name collision. Read [toolchain.md](references/toolchain.md) for tool selection and installation. Do not silently update binaries or templates during a run.

## Pipeline design

```text
subfinder / chaos / cloudlist / uncover
    → candidate hosts → scope → dnsx / shuffledns
    → scoped service seeds → [naabu when ports are in scope]
    → httpx JSONL → origins + response metadata

urlfinder ───────────────────────────────────────┐
katana → links / JavaScript / forms              │
katana headless / proxify → observed XHR methods ├→ scoped endpoint events
OpenAPI / Swagger / docs / source maps ──────────┘
    → files + API operations + parameter keys + provenance
    → reviewed probe URLs → httpx / reviewed Nuclei discovery templates
    → compare negative controls → verified inventory + coverage gaps

tlsx / cdncheck / asnmap / mapcidr → enrichment / candidate expansion
    → scope again before any further active requests
```

- Use plain one-item-per-line streams between compatible CLI stages. Metadata-decorated output is not a host or URL list. Prefer `-silent` for plain streams and JSONL plus `jq` for enrichment. Never pipe raw JSONL directly into a tool expecting URLs.
- Save raw per-tool output before transformation. Use `set -euo pipefail`, separate stderr logs, `tee` checkpoints, and bounded intermediate files. Check successful completion and nonempty input before starting dependent active phases. Do not hide failures with blanket `|| true`.
- Deduplicate exact hosts and URLs for work scheduling; retain source/evidence rows. Do not collapse methods, auth contexts, parameter values, trailing slashes, duplicate query keys, or case-sensitive paths in the canonical inventory. Derive grouped views separately.
- Every new hostname, certificate SAN, redirect, schema server, IP, and archive URL is a candidate until scope-checked. DNS/CNAME/CDN/ASN association alone does not authorize scanning an IP or neighboring assets.
- Filter before network activity. Output filters are not request controls. Disable automatic redirects for initial probes, then check destinations before following. Katana's default registrable-domain scope is broader than exact-host authorization; set explicit crawl scope. For strict path/network boundaries, use a verified request/egress allowlist; crawler regexes and this skill's offline helper do not constrain browser subrequests, DNS rebinding, or every tool's internal fetches.
- Keep auth sessions per origin and role. Do not forward credentials to newly discovered hosts. Capture forms and methods without automatic submission. An advertised POST/DELETE route is inventory data, not permission to execute it. Even GET routes can mutate state; exclude known logout, delete, unsubscribe, purchase, and action links from active crawling/probing.

## Execute the selected branches

- **Copyable CLI chains, adapters, and incremental runs:** read [pipelines.md](references/pipelines.md).
- **Files, JS, source maps, schemas, API operations, wordlists, and soft-404 verification:** read [files-and-apis.md](references/files-and-apis.md).
- **Tool coverage, secondary tools, installation, and official references:** read [toolchain.md](references/toolchain.md).
- **Artifact layout, scope format, budgets, recovery, and reporting:** read [operations.md](references/operations.md).

Use `scripts/pd_data.py` for offline `scope`, `inventory`, and `paths` operations. It uses only Python's standard library and never sends network requests. Read `--help` and the scope format in operations.md. It intentionally rejects ambiguous URLs; it is a data filter, not a network enforcement layer. The small [discovery path seed](assets/discovery-paths.txt) is a starting point, not a coverage claim.

## Adaptive discovery loop

1. Merge passive and active discoveries with provenance. Separate observed requests, documented operations, and guessed paths.
2. Extract route words, API versions, file stems, and directory prefixes. Generate a small target-specific next batch; scope-check it and count origins × candidates × methods × retries.
3. Probe reviewed read-only candidates under the remaining budget. Keep 2xx, redirects, 401, 403, 405, and unusual 5xx evidence. Compare against randomized missing-path controls before calling a path present.
4. Expand only from new evidence. Stop when the requested budget ends, a bounded pass adds no useful endpoints, or rate-limit/service-health signals require a pause. Report inaccessible areas and skipped branches instead of claiming completeness.

## Completion criteria

Deliver artifact paths and a short coverage statement: unique hosts/origins/URLs, file candidates, API operations by method and auth context, source counts, confirmed-versus-candidate distinctions, useful next targets, and gaps (missing provider keys, failed tools, absent JS/source maps, authenticated areas, truncation, wildcard DNS, soft-404 ambiguity). Include tool/template versions and reproducible commands. Never equate “no results” with “no attack surface,” a 200 response with a real file, or an exposed route with a vulnerability.
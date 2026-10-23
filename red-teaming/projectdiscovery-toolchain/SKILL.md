---
name: projectdiscovery-toolchain
description: "Use when running nuclei, httpx, subfinder: exact PD flags."
version: 1.0.0
author: skii, Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [projectdiscovery, nuclei, httpx, subfinder, recon, scanning, bug-bounty, cli-reference]
    related_skills: [projectdiscovery-recon, web2-recon, recon-playbook, hunt-dispatch]
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/api-surface-from-bundle.md`, `references/continuous-delta-scanning.md`, `references/discovery.md`, `references/identity-sso-probes.md`, `references/infra-aux.md`, `references/notify-pdtm-aix.md`, `references/nuclei-cli.md`, `references/nuclei-templates.md`, `references/probe-scan.md`, `references/source-map-recovery.md`, `scripts/js_api_map.py` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# ProjectDiscovery Toolchain

Exact CLI surface for 24 ProjectDiscovery tools — flag names, defaults, config paths, output
schemas — plus how they compose into a recon pipeline. Flags here are derived from indexed
repository source and READMEs, so they are authoritative for *what exists* but may drift from
the installed binary's build.

This is a **reference and composition** skill, not a hunting methodology. For "what bug class do
I chase and how do I prove it," use the `hunt-*` skills, `recon-playbook`, or `bb-methodology`.
This skill answers "which tool, which flag, in what order."

## When to Use

- Composing or debugging a recon pipeline (`subfinder → dnsx → httpx → naabu → nuclei → notify`)
- You need the exact flag name/default for a PD tool instead of guessing or shelling `-h`
- Writing or reviewing a nuclei template (matchers, extractors, multi-protocol, DSL)
- Setting up `notify` providers, `pdtm` tool management, or `interactsh` OOB capture
- Deciding which PD tool owns a job (passive URL discovery vs crawling vs port scan)
- Turning a downloaded client JS bundle into the URL list the probes will consume (see
  `references/api-surface-from-bundle.md`), or `scripts/js_api_map.py` for the extraction itself

Don't use for: choosing a vulnerability class to hunt, writing a report, or general sqlmap/nmap
workflows. The bounded ffuf companion workflow below covers source-derived route discovery.

## Prerequisites

Install and manage ProjectDiscovery tools through `pdtm` rather than individual `go install` calls:

```
terminal(command="pdtm -install-all", timeout=600)      # all PD tools
terminal(command="pdtm -i nuclei,httpx,subfinder", timeout=300)
terminal(command="pdtm -sp", timeout=30)                 # print binary path
```

`pdtm` installs released binaries (not `go build`), so a tool with no published binary for the
platform cannot be installed this way. `$HOME/.pdtm/go/bin` is prepended to `$PATH` by default.
Tools installed with `go install` instead land in `$(go env GOPATH)/bin` — find the real path with
`pdtm -sp`, and call PD binaries by absolute path inside scripts (see the PATH-shadowing pitfall).

API-key-bearing tools read provider config from `$HOME/.config/<tool>/provider-config.yaml`
(`subfinder`, `tldfinder`, `urlfinder`, `cloudlist`, `notify`). `chaos` reads `PDCP_API_KEY`;
`asnmap` uses `-auth` for PDCP. `aix` requires `OPENAI_API_KEY`.

## Canonical pipeline

Each stage writes to disk so later stages filter from a file instead of re-running discovery.

```
terminal(command="subfinder -d target.com -all -oJ -o subs.jsonl", timeout=900)
terminal(command="dnsx -l subs.txt -a -resp -o resolved.txt", timeout=600)
terminal(command="httpx -l resolved.txt -sc -title -td -ip -cdn -j -o probe.jsonl", timeout=900)
terminal(command="naabu -l resolved.txt -top-ports 1000 -ec -j -o ports.jsonl", timeout=1800)
terminal(command="nuclei -l live.txt -s critical,high -j -o findings.jsonl", timeout=1800)
terminal(command="notify -data findings.jsonl -bulk -p slack", timeout=120)
```

Produce the live-target file **once** and pass its path to every consumer. Re-running
`subfinder`/`httpx` per consumer is the most common waste in a multi-stage run.

**Reach for the PD binary before hand-rolling a loop.** A shell or Python loop over hosts
re-implements what the binary already does — bounded rate (`-rl`), retries, redirect control, JSONL
output carrying status/size/title/tech — and it drifts from the flags the rest of the pipeline uses,
so its output cannot be fed to the next stage. The user reads a custom recon loop as not knowing the
job. Keep a script for the transform PD genuinely does not perform (mining a downloaded bundle, a
control-path body-hash diff) and put it in `scripts/`, invoked by path.

## Wordlist discipline: target-specific beats generic

**Use existing discovery tools and target-specific wordlists first.** Drive content/route discovery
with `ffuf`, not a bespoke Python HTTP enumerator. Reserve scripts for offline extraction,
allowlist transforms, provenance and response comparisons. `ffuf` is not a PD tool: do not install
it with `pdtm`; when needed, use `go install github.com/ffuf/ffuf/v2@latest` and confirm the binary's
version/help before choosing flags.

1. Fetch the advertised application JS completely, then map exact method, path, query/body fields
   and auth headers before generating requests. A base URL alone is not the request contract.
2. Start with a small list of source-observed request shapes, a known-route baseline and two
   impossible-path controls. Use empty or deliberately invalid inputs for input-handling baselines;
   label researcher-selected values separately from source-observed values. Never substitute real
   customer/device identifiers for missing tester-owned fixtures.
3. Expand with observed hostname service/environment labels, relevant client route strings and the
   target's business/product lexicon. Exclude framework/library noise. Generate environment/service
   combinations only from naming patterns evidenced in the target corpus.
4. Keep the list under the engagement's `wordlists/`, its generator under `scripts/`, and source
   paths, hashes, extraction locations and unique counts beside it. Use a generic list only for a
   defined coverage gap after the custom pass, within the remaining budget.
5. Run the initial bounded ffuf pass with `-mc all`, explicit `-rate`, low `-t`, a deadline, JSON
   output and `-od` raw request/response storage. Keep this control pass unfiltered. Before a larger
   expansion, derive filters from the saved controls; do not suppress every 403 or 500 by status.
6. Verify expected input count, completed requests, errors, saved response count and control body
   hashes. Exit zero or an empty hits file alone does not demonstrate coverage. Generic 500s and
   health responses are mapping signals, not vulnerability proof.

Follow `references/api-surface-from-bundle.md` for the capture and bounded ffuf recipe. Apply the
engagement-wide rate and request cap across concurrent tools, retries and redirect hops.

## Program-mandated request headers

Copy the exact attribution header name and value format from the program policy; platform
examples such as `X-HackerOne-Research` or `X-Bug-Bounty` are not universal defaults. Resolve the
researcher's identifier from trusted context or ask when it is missing. Pass the literal policy
header with `-H` into every HTTP stage, including curl and ffuf, so artifacts record attributed
traffic:

```
httpx  -l urls.txt -H 'X-Bug-Bounty: Bugcrowd-<username>' -sc -td -j -rl 4 -o probe.jsonl
katana -list urls.txt -H 'X-Bug-Bounty: Bugcrowd-<username>' -j -o crawl.jsonl
nuclei -l urls.txt -H 'X-Bug-Bounty: Bugcrowd-<username>' -j -o findings.jsonl
```

`dnsx`, `tlsx`, `naabu`, `asnmap` and `mapcidr` do not speak HTTP and take no header. Get the exact
handle from the user **before the first active request** — it cannot be invented, and an unattributed
scan forfeits the safe-harbour footing the program otherwise grants. A gateway key the client bundle
ships (e.g. `Ocp-Apim-Subscription-Key`) rides in the same `-H` list.

Browser-driven traffic is attributed traffic too, and a plain navigation cannot set a custom request
header. When an engagement mandates one, attach it at the automation layer before the first
navigation — a CDP `Network.setExtraHTTPHeaders` call, or the browser CLI's own header override. In
the Interceptor CLI `headers add` only accepts recognised standard header names, so an arbitrary
`X-…` attribution name needs `override` instead. Count each navigation as a target request in the
engagement ledger; page subresource loads cannot carry the header and are a known accounting limit
to state explicitly, not to ignore.

## Tool selection matrix

| Job | Tool | Not this |
|---|---|---|
| Passive subdomain enum | `subfinder` | `shuffledns` (that's brute-force) |
| DNS brute-force / wildcard strip | `shuffledns` (needs `massdns`) | `dnsx -w` for large lists |
| Resolve + record lookup | `dnsx` | |
| Subdomain permutations | `alterx` | |
| Private TLD discovery | `tldfinder` | `subfinder` |
| Passive URL discovery | `urlfinder` | `katana` (that's active crawling) |
| HTTP probe / tech detect / screenshot | `httpx` | `curl` loops |
| Port scan | `naabu` | |
| TLS/JA3/JARM fingerprint | `tlsx` | |
| CDN/WAF/cloud attribution | `cdncheck` | |
| ASN → CIDR | `asnmap` | |
| CIDR arithmetic / shuffle | `mapcidr` | |
| Cloud asset inventory | `cloudlist` | |
| Search-engine asset discovery | `uncover` | |
| MITM capture / request rewrite | `proxify` | |
| OOB (SSRF/blind RCE) callback | `interactsh` | |
| Serve payloads / fake TCP service | `simplehttpserver` | |
| Template-driven vuln scan | `nuclei` | |
| Alert fan-out | `notify` | |

## References

Load the one that matches the question; each holds exact flags, defaults and output schemas.

| Need | Load |
|---|---|
| subfinder, dnsx, shuffledns, tldfinder, chaos, alterx, urlfinder | `references/discovery.md` |
| httpx, naabu, tlsx, cdncheck, asnmap, mapcidr | `references/probe-scan.md` |
| cloudlist, uncover, proxify, interactsh, simplehttpserver | `references/infra-aux.md` |
| nuclei CLI flags, rate limits, Go SDK | `references/nuclei-cli.md` |
| Template structure, matchers, extractors, CVE patterns | `references/nuclei-templates.md` |
| Scheduled re-scanning of a monitored scope without re-running the full asset×template cross-product: hash-based asset/template delta detection, the two trigger modes, cron failure modes | `references/continuous-delta-scanning.md` |
| notify providers, pdtm, aix | `references/notify-pdtm-aix.md` |
| Bundle-to-API-surface extraction, gateway fingerprints, route confirmation | `references/api-surface-from-bundle.md` |
| Identity/SSO probes, their bundle-derived contract and their sequencing (OIDC discovery, authorize-endpoint reflection check, escalation and block handling, Firebase rules, Ping/ForgeRock & Azure AD fingerprints) | `references/identity-sso-probes.md` |
| Recovering a served production source map: parsing `sourcesContent`, mining routes and parameter names, the currency check, and classifying recovered values | `references/source-map-recovery.md` |

## Pitfalls

- **GAU can hang indefinitely on large domains with no output.** GAU queries Wayback Machine, AlienVault OTX, and CommonCrawl in sequence. On domains with no archived content (e.g., new or obscure subdomains), GAU may hang for 3+ hours producing 0 bytes. Kill it after 2 minutes with `timeout 120` if no output appears. Fall back to the Wayback Machine CDX API directly (`http://web.archive.org/cdx/search/cdx?url=*.domain.com&output=json&fl=original&limit=1000`) or AlienVault OTX (`https://otx.alienvault.com/api/v1/indicators/domain/{domain}/url_list?limit=200`) — these are faster, more predictable, and often find hosts GAU misses. OTX is especially useful for discovering historical subdomains that no longer resolve.

- **Doc-derived flags drift.** Everything here comes from indexed source/README snapshots.
  Before scripting an unfamiliar flag, confirm against the installed build:
  `terminal(command="<tool> -h", timeout=30)`. A rejected flag is printed on **stdout**, so when
  you redirect stdout to the stage's output file the error text becomes that file's *only* line —
  a crashed stage that reads as "1 result". Grep the first line for `flag provided but not
  defined` / `Usage:` before treating any stage as done.
- **A same-named non-PD binary on `PATH` shadows the real tool.** `httpx` collides with the Python
  `httpx` HTTP-client CLI: PD flags then fail with `Error: No such option '-l'` under a
  `Usage: httpx [OPTIONS] URL` banner, which reads like doc drift rather than the wrong binary.
  Check `which -a <tool>` before blaming a flag, and invoke by absolute path in scripts. Treat any
  PD tool that rejects its own documented flag as a shadowing problem first, a version problem second.
- **Memory safety on large scopes.** Never run `katana -jsl` (JS-link crawling) on a broad
  scope — it is the known OOM path. Keep `nuclei` to ~10 hosts per invocation in sequential
  batches with scoped templates and low concurrency, and report which hosts went unscanned.
- **A zero-result nuclei run is not a clean baseline**, especially behind a WAF/CDN. Follow it
  with bounded manual probes (CORS, `/openapi.json`, info paths, security headers, SSH banner)
  and record positives, negatives *and* blockers.
- **`chaos` is rate-limited to 60 requests/min/IP** and only accepts domain-name queries.
- **`dnsx`: `-l` (resolution) and `-w` (brute-force) cannot be combined**; a DNS record-type
  flag cannot be used together with wildcard filtering; `-wd <domain>` is mandatory for
  wildcard elimination. Default record type is `A`.
- **`shuffledns` needs an external `massdns` binary** (auto-detected in `/usr/bin` or
  `/usr/local/bin`), plus a resolver list and wordlist — it fails with no useful hint otherwise.
- **`naabu -ec/-exclude-cdn` silently narrows a scan to ports 80/443** for CDN/WAF hosts. Good
  default for speed, wrong if you are hunting non-web services. `-nmap` is deprecated; use
  `-nmap-cli 'nmap -sV'`.
- **`httpx` default rate limit is 150/s** — far too loud for most programs. Set `-rl` explicitly.
- **`nuclei -mhe` defaults to 30**: after 30 errors a host is silently skipped. On flaky or
  rate-limiting targets raise it or use `-nmhe`, or you will read "no findings" as "no bugs."
- **`tlsx` probe flags cannot be combined with each other.** `-san`/`-cn` reject any sibling probe
  flag — the run dies with `[FTL] cause="san or cn flag cannot be used with other probes"`, exits 1,
  and because `-o` was given **no output file is created at all**, so the stage reads as "ran and
  produced nothing" rather than as a crash. Plain `tlsx -l hosts.txt -json -o tlsx.jsonl` already
  emits `subject_cn`, `subject_an`, `issuer_*`, `tls_version`, `cipher` and the fingerprints. Ask
  for JSON, not for probes, and check the file exists instead of trusting the exit path.
- **`tldfinder` only accepts private TLDs**, and takes either TLD (`example`) or domain
  (`example.google`) input, extracting the TLD automatically.
- **`interactsh` correlation is per-client-session.** Reuse `-sf/-session-file` or you lose the
  ability to correlate a late callback with the request that caused it.
- **`-itags` includes ONLY the named tags (filter IN); `-etags` excludes them (filter OUT).**
  These are NOT synonyms. `-itags takeover,ssl,dns` runs ONLY templates tagged with those labels
  (a narrow, usually-wrong choice for CVE hunting). `-etags takeover,ssl,dns` runs everything
  EXCEPT those tags (the right choice for broad scanning). Using `-itags` when you meant
  `-etags` silently drops 99% of templates and produces a false-clean result. For a proper
  CVE/tech-detect scan use tag combinations: `-tags cve,grafana,iis,exposure,config` or
  `-etags takeover,ssl,dns,network,bruteforce`.
- **A heredoc wordlist piped into a background process with `~` in the binary path fails silently.** When using `terminal(command="~/go/bin/ffuf ... << 'EOF' ... EOF", background=true)`, the `~` in the heredoc is NOT expanded by the background shell, producing `no such file or directory: /Users/currentuser/Users/skii/go/bin/ffuf`. Use the full absolute path (`/Users/skii/go/bin/ffuf`) inside heredocs for background processes, or inline the wordlist as a file argument instead of stdin.
- **Nuclei with 5000+ templates on multiple hosts can take 10+ minutes.** The full template set (13K+ templates) against 10+ hosts at `-rl 10` produces ~13K HTTP requests and takes 20+ minutes. Run large template sets as background processes with `notify=true` so the session is not blocked. For faster iteration, use targeted `-tags cve,exposure,<tech>` or `-itags` to select a subset of templates. Verify template loading with `-tl` before the full run.
- **On a large probed estate, triage before nuclei.** Run nuclei only on the hosts httpx showed serving custom app content — identical team-site clone farms and pure login-gate redirects add hundreds of host-slots of template noise for zero signal. On policy-constrained programs (no-aggressive-scanning clauses) use the lean tag set `-tags exposure,config,misconfig,takeover,token,unauth,panel,default-login`; the `-tags cve,...` combination is the multi-hour one even at `-rl 8`.
- **Use absolute paths for `-l` and `-o` in any background or batched nuclei run.** An `-o scans/...` relative path resolves against the shell's drifted CWD and produces doubled paths (`scans/x/scans/x/batch.findings.jsonl`); when the target directory does not exist nuclei dies with `[FTL] Could not create runner: could not create output file`, writes nothing, and a `wc -l` on the missing file reads as zero findings rather than as a crash.
- **Kill the parent loop before the children when stopping a batched pipeline.** `pkill nuclei` inside `for batch in ...; do nuclei ...; done` just advances the loop — the next batch launches immediately and the aggregate rate budget you were correcting is violated again. Find the loop shell first (match `ps` output on the progress-log filename or a unique `-o` path), kill it, then the current tool PID.
- **`nuclei -rlm/-rate-limit-minute` is deprecated** — use `-rl` with `-rld`.
- **Don't set `metadata.max-request` by hand** in a template; it is auto-calculated.
- **A Python virtualenv `httpx` shadows the PD binary.** Where a venv is on `PATH`, bare `httpx`
  resolves to the Python HTTP-client CLI and rejects PD flags with `Error: No such option '-l'`
  (exit 2) while `httpx -version` merely prints `Usage:`. Find the real one with
  `which -a httpx` (commonly `~/go/bin/httpx`) and call it by absolute path in every script.
- **Size a DNS brute force's rate to its wordlist or it never finishes.** `dnsx -w` with the
  2.17M-entry jhaddix list at `-rl 100` needs ~6 hours; `-rl 1000` finishes in ~36 min. A brute
  force that never completes is indistinguishable from one that found nothing — check the output
  file is actually growing before trusting an empty result.
- **`dnsx -json` emits one row per input, including `NXDOMAIN`.** A resolved-host list built
  naively from its output therefore carries dead names into every downstream stage — filter on
  `status_code == "NOERROR"` (plus a non-empty `a`) before feeding `httpx`/`naabu`, or a slice of
  the probe budget is spent on hosts that never existed and the "live host" count is inflated.
- **Scanner output saved with colour carries ANSI escapes.** `dnsx`/`naabu` write `\x1b[35m`-style
  sequences around field labels, so a literal match on `[CNAME]` finds nothing inside a file you
  can see contains `[CNAME]`. Strip `\x1b\[[0-9;]*m` before parsing saved output (or disable
  colour at capture time); a zero-record parse of a non-empty file is this, not an empty result.
- **A denial is not evidence of a service until a control says so.** Send the identical request to a
  path, method or service name that *cannot* exist. If the response is byte-for-byte the same, you
  are measuring the edge gate in front of the app, not the app. This catches both directions of the
  error: a `grpc-status: 7` / `PERMISSION_DENIED` read as "the service exists and enforces auth"
  when a fabricated service path returns the same trailer, and a per-path `200` read as "reachable
  endpoints" when it is one login page served for every path. Build the impossible-path control in
  before interpreting any refusal. Read the control in the *positive* direction too: the response
  family that **differs** from it is what marks a route as real — a per-id JSON not-found, or a
  distinct auth rejection. A uniform `WWW-Authenticate: Bearer error="invalid_token"` with a
  zero-length body demonstrates only rejection of the tested credentials; it does not prove valid
  user/object authorization. Record that state as a negative, retain broader coverage as partial,
  and require tester-owned successful flows before drawing an authorization verdict.
- **Read the whole status family, not just "denied" versus "allowed".** Against one impossible-path
  control, the status set maps the route inventory precisely: `404` = route absent; `401` with
  `WWW-Authenticate: Bearer` = route exists and authentication is enforced; `405` = route exists and the
  framework rejects this method, i.e. it is a **write endpoint**; a JSON body = a live read; the app's
  own HTML shell = a client-side catch-all that proves nothing about the route. `405` is the one that
  misleads — it is a *route-exists* signal and the reflex is to re-send as the method it wants. Under a
  continuation that prohibits state-changing requests, do not: record "POST-only, not called" and move to
  the next route. A probe log that keeps only 200/403 discards every one of these distinctions.
- **An open port on an IP is not authorized by the port scan.** Map every open-port IP back to an
  in-scope hostname before touching it: a shared CDN/SaaS edge IP, or a hostname whose CNAME lands
  on a provider, means that port belongs to the provider, not the program. Then fingerprint the
  protocol before assuming HTTP — the TLS handshake's ALPN names it (`h2` ⇒ HTTP/2, i.e. a gRPC or
  HTTP/2 service sitting on a custom port).
- **Probe false positives in both directions.** Following redirects makes an auth-gated app answer
  the same `200` login page for every probed path, so a path list appears to "resolve" everywhere;
  and a non-browser `User-Agent` is handed a browser-gate page (`/unsupported-browser.html`-style
  `307`) instead of the app, so a naive probe measures neither the app nor its auth. Disable
  redirect following per request, and set a browser UA when the target gates on it.
- **Auth-path probing can escalate an edge denial from one path to the whole IP.** A few requests to `/signin` or an authorize endpoint can turn a per-path deny page into a deny for every path on that host, including for a real browser on the same egress — so when a human sign-in (registration, MFA, captcha) is part of the plan, that escalation deletes your own unblock path. Do read-only identity recon first and interactive auth paths last and once, record the resulting block as a blocker with its edge reference id, and never answer it with proxy/IP rotation, fingerprint impersonation or retries: that is evasion of a security control and it forfeits the safe-harbour footing. Detail and sequencing: `references/identity-sso-probes.md`.

- **Locate an edge denial before theorising about it.** Same egress, same URL, browser served a deny
  page while the plain HTTP client is served the real page: that is not a cookie problem. Falsify it
  by re-requesting from a cookie-less browser profile, then with a header matrix (bare research
  `User-Agent` versus a full browser-like set — `Accept`, `Accept-Language`, `Sec-Fetch-*`,
  `sec-ch-ua`). Denied on all of them means the block sits at the edge for your egress and no
  profile, header or fingerprint change will move it: record it with the edge reference id and stop.
  A single success from the clean client in between is a failover window, not a working path, until
  it repeats.
- **Deny is usually per-host, not estate-wide.** Sweep the roots of a handful of in-scope hosts before
  concluding a program is unreachable. One host returning a WAF deny while another answers normally
  in the same minute is the common case, and that contrast is what tells you which lane is still
  workable.
- **Sweep the untouched in-scope hosts before deepening a single lane.** An allowlist of hundreds is
  normally mostly unprobed, and one root request per host is the cheapest new-surface discovery
  available — a short sweep routinely surfaces an application no other lane had reached. Sort candidate
  names for non-production and environment labels (`-dev`, `-qa`, `-uat`, `-stage`, `-ping`) first: they
  are the highest-yield picks and the ones whose controls are weakest. Expect most to be edge-denied;
  the sweep still pays for itself on the one that serves, so record the denials as a reachability map
  rather than as a failed pass.
- **Compare the sent request bytes before blaming the server for a status swing.** When an endpoint
  that answered `2xx` starts returning an auth rejection, diff the request line and headers of the two
  saved captures before theorising server-side drift. A client-compatibility header the application's
  own JS always sends explains most such swings — confirm it by reading the live page's own network log
  for that header on a request the app itself makes. That header is not a secret and not an auth
  bypass; the malformed request was yours.
- **A malformed request of your own looks exactly like an edge block.** When a helper function
  forwards a query string through `-d`, the request goes out as a **GET with a body and no query
  string**; CloudFront answers it with a generic `403 ERROR / Bad request` HTML page that is
  indistinguishable from a WAF deny. The tells are that the same path answered `200` minutes earlier
  and the host root still answers `200`. Rebuild the identical request with the parameters in the path
  and re-run it *before* recording anything: a construction bug written into the handoff as "the target
  is blocking us" becomes inherited fact for the next session and stops work that was never blocked.
- **SEO scaffolding is a route source the minified bundle hides.** A SPA root can carry
  `visibility:hidden` anchor links and a `/sitemap.xml` that the bundle never references, because the
  router builds those paths dynamically. Read the served HTML for hidden anchors and fetch the sitemap
  before declaring a route inventory complete, then merge it into the list the bundle extraction
  produced.
- **Public DNS answering RFC1918 addresses is a finding, not noise.** When `dnsx` returns `10.x` or
  `192.168.x` for an in-scope name, the zone is publishing internal addressing publicly — internal
  topology and segmentation disclosure. Confirm against an independent resolver
  (`dig @1.1.1.1 <name>`) before reporting, and grade it low/informational; it grants no access.
- **Never grep an unconstrained pattern across IL2CPP/metadata string dumps.**
  `global-metadata.dat` strings are one multi-megabyte concatenated line, so a plain `grep -o`
  can dump hundreds of KB into context in a single call. Bound it with `-c`/`cut`/`head -c`, or
  search the saved dump file with `search_files` instead.

## Verification

- **Classify source-map comments by their enclosing module before deriving fetch URLs.** A webpack bundle can contain hundreds of genuine line-local `sourceMappingURL` comments copied from vendor modules; those are not the parent bundle's advertised map. Preserve each module/comment anchor, separate embedded vendor references from a terminal parent reference or response map header, and never turn the embedded comments into a network manifest. Test the extractor against a multi-module bundle: vendor-comment count can be nonzero while parent-map fetch candidates remain zero.
- **Separate callsites from request-shape variants.** Multiple conditional query combinations can share one explicit HTTP call. Report source-call byte locations, unique method/path templates, and actual concrete requests as separate counts; never describe every query variant as a distinct callsite or live endpoint.
- **Check macOS Bash 3 nounset behavior before a stage starts.** Under `set -u`, an empty optional array expanded as `"${EXTRA[@]}"` can abort before the HTTP tool runs. Use a tested nounset-safe expansion or initialize common arguments nonempty. Preserve the prelaunch failure, and distinguish zero network attempts from a failed or incomplete request; a start-time file alone proves neither tool launch nor traffic.
- **Derive lazy-chunk URLs from the build's own maps, never guess filenames.** A webpack/Angular runtime bundle carries the chunk-id→hash table, and the main bundle's module registry carries route→chunk-id lists (Angular CLI emits `"./pages/x/x.module.ngfactory":["<id>",<chunk ids>]`). Recover both offline, then build `<id>.<hash>.js` URLs for the routes you actually want. Guessing `0.js`, `1.js` wastes requests and produces 404 noise; the maps are exact.
- **Read `assetPrefix` and `buildId` out of the page HTML before fetching any chunk, and rank the
  app's own chunks ahead of vendored ones.** Two independent traps produce a *false* "no API surface"
  on a client-side app. (1) A Next.js app can serve its JS from a different host
  (`assetPrefix: //uk.tmconst.com/rc-707ed0ec` on `www.ticketmaster.com`), so `/_next/static/...` refs
  extracted from the HTML 404 when resolved same-origin — 30 of 31 requests wasted, and the stage reads
  as a clean application rather than as a failed fetch. (2) Taking the first N refs in HTML order picks
  nextjs/react/mui vendor bundles, not route code; three separate sites all reported "0 API paths,
  0 fetch callsites" until the ordering was fixed. Check the ledger's status codes before interpreting
  an empty mine, and treat zero hosts referenced as a fetch failure, not a finding.
- **An edge/gateway fault string is a route-existence oracle — use it, but do not report it.** Apigee
  answers an unrouted path with `{"fault":{"faultstring":"Unable to identify proxy for host: <vhost>
  and url: <path>","detail":{"errorcode":"messaging.adaptors.http.flow.ApplicationNotFound"}}}` while a
  *live* proxy with an unmet requirement answers `steps.oauth.v2.FailedToResolveAPIKey`. Those two families
  cleanly separate "no such route" from "route exists, auth enforced" across a shared vhost, which is how
  you enumerate an API estate cheaply. Two cautions: the fault body echoes the requested path, so byte-size
  comparison between two 404s is not a control — compare the fault *class* (a 160 B `/` vs 185 B 25-char
  path is the same error, not two behaviours); and the leaked platform/vhost/fault-code detail is
  edge/config disclosure with no access demonstrated, i.e. Core-Ineligible hygiene, not a finding.
- **Chunk-level attribution is not module exclusivity.** Webpack places a shared service module into every chunk that imports it, so one API-constant list appears in several page chunks. Publish the union of distinct endpoints plus per-chunk presence, and never claim a page-exclusive endpoint from one chunk.
- **Derive a verification script's expected counts; never hardcode them.** A checker asserting
  `len(rows) == 87` or `total == 148` must be edited on every stage, and once a new stage lands the
  failure reads as a broken workspace rather than a stale constant — one investigate-and-patch cycle
  per stage. Load the numbers from the resume index and the stage manifests, assert the script's own
  recomputation against them, and let the counts move. Keep exactly one durable quantity (the manifest
  row count) and derive the rest.
- **A sweep glob can miss the ledger the continuation started from.** `pass-*-httpx.jsonl` over the
  expansion stages excludes the original request ledger, so the recomputed total silently undercounts
  by exactly the pre-continuation spend while still passing a self-consistency check. Build the total
  from every source — original ledger, stage manifests, non-lane traffic — and assert it against the
  recorded index rather than against your own sum.
- **A uniform denial across every path — including your impossible-path control — is a blanket gate, not route-level auth.** When the real route and the fabricated control return the same status *and* the same empty body, the request never reached an application route: record a blocker (auth enforced at the edge/gateway) and stop trying to confirm route existence anonymously.
- **Set the per-response read cap per stage and store it with the stage.** A 1 MiB default silently truncates a legitimate 1.4 MiB bundle; the tell is `captured bytes == cap` while the response ETag tail encodes the real size. Re-fetch under a new manifest event with a raised cap rather than analysing a partial capture, and evaluate the truncation flag against the cap the launcher actually used, not a hardcoded default. A **chunked response advertises no `Content-Length`**, so there is no size to compare against and a truncated capture looks complete — for an artefact that is itself the evidence, re-fetch under a raised cap before analysing it.
- **Different response families can coexist on one host.** A host can serve an edge/WAF `403` HTML page for its document root while `/wp-json/*` still reaches the application and returns its own JSON `404` (`rest_no_route`). Classify per path: never infer "the whole host is blocked" from the root alone, and never infer "the REST API is exposed" from a JSON error that is just a missing route.
- **`httpx` normalises a valueless trailing `=` in a query string** (`?teamId=` is emitted as `?teamId`). Reconcile output rows against the manifest with that normalisation recorded explicitly, or a legitimate response reads as an unmatched URL.
 - **A continuation's spend is the original ledger plus every stage manifest plus non-lane traffic.**
 Summing a glob over the expansion stage manifests alone silently omits the requests already spent
 before the continuation began, and any browser navigation or ad-hoc `curl` that did not pass through
 the pipeline lane. Build the per-origin table from all three sources, assert the total against the
 recorded index, and re-derive it every time — an undercount here misreports remaining budget while
 passing every other check in the suite.

Before accepting a stage, reconcile output records with actual request/response evidence, classify skipped references separately, and verify stored-response paths exist. Preserve request cookie names and their evidence-backed role in auth context without copying values: anonymous crawlers can replay edge/affinity cookies without an application login. Inspect the raw request before asserting that no cookies or credentials were sent.

Separate configured rate limits, response-completion gaps and measured request-start spacing. Prove a strict spacing claim with timestamped request-start evidence; response timestamps can bunch when latency varies and prove neither compliance nor violation by themselves. Use `references/probe-scan.md` for reconciliation and timing checks.

After composing a pipeline, prove each stage produced real output rather than trusting exit codes:

```
terminal(command="wc -l subs.txt resolved.txt probe.jsonl findings.jsonl", timeout=30)
terminal(command="head -1 probe.jsonl", timeout=30)
```

A stage with 0 lines needs classification, not a clean bill of health: distinguish no matches from
no valid inputs, all requests filtered, request failures, interruption or no loaded templates. Check
input/completion/error counts and control responses, and record incomplete coverage explicitly.
For `nuclei`, confirm the template set actually loaded with `-tl`:
`terminal(command="nuclei -s critical,high -tl", timeout=120)`.

## MANDATORY ON INVOCATION — PROTOCOL RESTATMENT (END OF FILE)

You have reached the end of this SKILL.md. The invocation protocol below is identical to the one at the top of this file. If you are reading this, the full skill context is loaded — confirm the checklist.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/api-surface-from-bundle.md`, `references/continuous-delta-scanning.md`, `references/discovery.md`, `references/identity-sso-probes.md`, `references/infra-aux.md`, `references/notify-pdtm-aix.md`, `references/nuclei-cli.md`, `references/nuclei-templates.md`, `references/probe-scan.md`, `references/source-map-recovery.md`, `scripts/js_api_map.py` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

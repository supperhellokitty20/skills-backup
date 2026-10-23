# Discovery tools — subdomain, DNS, URL, permutation

Flags quoted from indexed repository source and READMEs for `projectdiscovery/*`. Where README
and source differ, source (`internal/runner/`, `pkg/runner/`) is the more complete authority.

## subfinder — passive subdomain enumeration

| Group | Flags |
|---|---|
| Input | `-d, -domain string[]`, `-dL, -list` |
| Source | `-s, -sources string[]` (e.g. `-s crtsh,github`), `-recursive`, `-all`, `-es, -exclude-sources`, `-ls` (list sources) |
| Filter | `-m, -match`, `-f, -filter` |
| Rate | `-rl, -rate-limit int`, `-rls value` (per-provider, e.g. `-rls "hackertarget=10/s,shodan=15/s"`), `-t int` (concurrency, default 10) |
| Output | `-o, -output`, `-oJ, -json` (JSONL), `-oD, -output-dir` (with `-dL` only), `-cs, -collect-sources`, `-oI, -ip` |
| Config | `-config`, `-pc, -provider-config`, `-r string[]` (resolvers), `-rL, -rlist`, `-nW, -active` (active only), `-proxy`, `-ei, -exclude-ip` |
| Debug | `-silent`, `-version`, `-v`, `-nc, -no-color` |

Go API: `runner.Options{Threads, Timeout, MaxEnumerationTime}`,
`EnumerateSingleDomainWithCtx`, `EnumerateMultipleDomainsWithCtx`.

## dnsx — DNS resolution and brute-force

Record types: **A, AAAA, CNAME, PTR, NS, MX, TXT, SRV, SOA**. Resolver protocols:
**TCP / UDP / DOH / DOT**. Automatic wildcard handling. Requires go1.21.

Behaviour that bites:
- Default record type is **A**.
- Default resolvers: Google / Cloudflare / Quad9; override with `-r`.
- `-wd <domain>` is **mandatory** for wildcard elimination.
- A DNS record-type flag **cannot** be combined with wildcard filtering.
- `-l` (resolution) and `-w` (brute-force) **cannot** be combined.

Library: `dnsClient.QueryOne("hackerone.com")`, `rawResp.JSON()`.

`-a` and `-cname` are separate invocations, not combinable into one run: `-a -resp` emits only
`[A]` rows (no CNAME chain), so a takeover/cname-mapping pass needs a second run with `-cname -resp`.
Pass `-nc` (or strip ANSI from the saved file with `sed -E $'s/\x1b\\[[0-9;]*m//g'`) when the output
will be parsed — default resp output colourises the record-type label, which breaks literal
matching downstream.

## shuffledns — massdns wrapper (brute-force + wildcard strip)

| Group | Flags |
|---|---|
| Input | `-d, -domain string[]`, `-ad, -auto-domain`, `-l, -list`, `-w, -wordlist`, `-r, -resolver`, `-tr, -trusted-resolver`, `-ri, -raw-input`, `-mode string` (`bruteforce`, `resolve`, `filter`) |
| Rate | `-t int` (default **10000**) |
| Output | `-o, -output`, `-j, -json` (ndjson), `-wo, -wildcard-output` |
| Config | `-m, -massdns` (binary path), `-mcmd, -massdns-cmd` (e.g. `'-i 10'`), `-directory` |
| Optimize | `-retries int` (default 5), `-sw, -strict-wildcard`, `-wt int` (default 250) |
| Debug | `-silent`, `-version`, `-v`, `-nc, -no-color` |

Prerequisites: external **massdns** binary (auto-detected at `/usr/bin` or `/usr/local/bin`), a
resolver list (dnsvalidator), a wordlist (commonspeak2). Go API:
`massdns.Options{Domains, TrustedResolvers, KeepStderr, BatchSize, OnResult}`,
`wildcards.NewResolver(...)`.

## tldfinder — private TLD discovery

| Group | Flags |
|---|---|
| Input | `-d, -domain string[]` (file or comma-separated) |
| Source | `-s, -sources string[]` (e.g. `-s censys,dnsrepo`), `-es, -exclude-sources`, `-dm, -discovery-mode value` (`dns`\|`tld`\|`domain`, default `dns`), `-all` |
| Filter | `-m, -match`, `-f, -filter` |
| Rate | `-rl, -rate-limit int`, `-rls, -rate-limits value` (default `["waybackarchive=15/m", "whoisxmlapi=50/s", "whoisxmlapi=30/s"]`), `-t int` (default 10) |
| Output | `-o, -output`, `-oJ, -json`, `-oD, -output-dir`, `-cs, -collect-sources`, `-oI, -ip` |
| Config | `-config`, `-pc, -provider-config`, `-r`, `-rL, -rlist`, `-nW, -active`, `-proxy`, `-ei, -exclude-ip` |
| Debug | `-silent`, `-nc, -no-color`, `-ls, -list-sources`, `-stats` |
| Optimize | `-timeout int` (default 30), `-max-time int` (default 10) |

Accepts TLD input (`example`) or domain input (`example.google`, TLD auto-extracted). **Only
private TLDs are accepted.** Requires Go 1.21.

## chaos-client (binary: `chaos`) — PD Chaos dataset

Flags: `-key string` (PDCP API key), `-d string` (domain), `-count` (statistics), `-dL string`
(domain list file), `-o string`, `-json`, `-silent`, `-version`, `-v, -verbose`, `-up, -update`,
`-duc, -disable-update-check`. Key may come from env `PDCP_API_KEY`.

**Operational limits:** API is rate-limited to **60 requests / min / IP**, and the Chaos API
supports **domain-name queries only**.

Library: `runner.Options{Domain, APIKey, OnResult}`, `runner.RunEnumeration(opts)`, `chaos.Result`.

## alterx — permutation wordlist generation (DSL)

| Group | Flags |
|---|---|
| Input | `-l, -list string[]` (subdomains to permute), `-p, -pattern string[]`, `-pp, -payload value` (key=value, e.g. `-pp 'word=words.txt'`) |
| Output | `-es, -estimate` (count without generating), `-o, -output`, `-ms, -max-size` (kb/mb/gb/tb), `-v, -verbose`, `-silent`, `-version` |
| Config | `-config`, `-en, -enrich` (extract words from input), `-ac` (permutation config, default `permutation_v0.0.1.yaml`), `-limit int` |
| Pattern mining | `-m, -mode` (`default`\|`discover`\|`both`), `-min-distance` (default 2), `-max-distance` (default 10), `-pattern-threshold` (default 500); also `-ngrams-limit`, `-quality-ratio`, `-save-rules` |

Pattern config lives at `$HOME/.config/alterx/permutation_v0.0.1.yaml`. The pattern-mining flags
exist only in `internal/runner/runner.go`, not in the README.

Run `-es/-estimate` before generating — a permutation set over a large input list can be orders
of magnitude bigger than expected.

## urlfinder — passive URL discovery (no crawling)

| Group | Flags |
|---|---|
| Input | `-d` (domain) |
| Filter | `-m`/`-f` (match/filter, files allowed), `-em`/`-ef` (extension match/filter, e.g. `-em php,html,js`, `-ef png,css`), `-ndef, -no-default-ext-filter` |
| Rate | `-rl, -rate-limit int`, `-rls, -rate-limits value` (e.g. `-rls hackertarget=10/m`) |
| Output | `-o, -output`, `-j, -jsonl`, `-od, -output-dir`, `-cs, -collect-sources` (`-json` only) |
| Config | `-config`, `-pc, -provider-config`, `-proxy` |
| Debug | `-silent`, `-version`, `-v`, `-nc, -no-color`, `-ls, -list-sources`, `-stats` |
| Optimize | `-timeout` (default 30), `-max-time` (default 10) |
| Scope | `-all` (all sources, slow), plus `UrlScope`, `UrlOutOfScope`, `FieldScope`, `NoScope`, `DisplayOutScope` |

JSON schema: `{url, input, source}` or `{url, input, sources[]}`.

**`urlfinder` is passive only.** For active crawling the tool is `katana` — present in the
sandbox toolchain but with no retrievable flag reference (see `references/probe-scan.md`).

## waybackurls / gau — archived-URL mining (coverage is uneven)

Both query third-party archives (Wayback, OTX, CommonCrawl), so they cost zero requests against
the target and are the passive-URL stage when `urlfinder` has no provider keys. Expect
**incomplete, uneven coverage**:

- `waybackurls <domain>` can return **zero lines in ~10s** even for a heavily-trafficked domain —
  treat an empty run as suspicious, not as a negative: check the tool's stderr, then retry via the
  raw Wayback CDX API (`http://web.archive.org/cdx/search/cdx?url=<domain>/*&output=json&fl=original&collapse=urlkey&limit=50000`)
  before recording the stage as empty.
- `gau --subs <domain>` fans out to CommonCrawl for the whole domain set and can run
  **5+ minutes with no output**; always run it under a timeout (`timeout 300 gau ...` or a
  `subprocess` timeout) so a hang becomes a bounded partial rather than a stalled stage.

## httpx probing large wildcards (500+ hosts)

- The httpx equivalent of "don't follow redirects" is **the absence of `-fr`**: default behaviour
  is no redirect following, so capture first responses as-is and inspect `-location` fields.
- On a wide estate, `-sc -cl -title -td -ip -cdn -location -j` is the useful probe flag set; the
  per-record JSON also carries `cname`, `a`, `tech`, `words` and `cdn_type`, which is enough to
  classify hosts (WAF page vs app vs SaaS redirect) without a second request.
- At 500+ hosts, `-rl 10` finishes in ~2 minutes; keep `-t`/`-threads` low to stay inside an
  engagement's aggregate budget.

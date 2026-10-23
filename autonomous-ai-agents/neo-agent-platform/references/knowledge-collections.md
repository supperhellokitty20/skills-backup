# Neo global knowledge collections

35 collections listed via `action: "list"`; **24 retrievable**, **11 not**. Every status below
was established by a real `search` with `isGlobal: true`, and each unavailable index was tried
with two distinct queries. Captured 2026-10-10 — re-probe before relying on an availability
claim.

Content character is uniformly **source-repo level** (README plus Go source) for
`projectdiscovery/<tool>`, not rendered documentation sites. Implementation files (`pkg/`,
`internal/`) are indexed and retrievable, which makes them the more complete authority for flag
definitions when a README lags.

## Band A — Network discovery (7/7 available)

| Collection | Status | Evidence |
|---|---|---|
| `subfinder` | available | `README.md` L39-104, full flag reference (score 0.995) |
| `dnsx` | available | `README.md` L32-47, record-type features |
| `shuffledns` | available | `README.md` L46-103, full flag reference |
| `tldfinder` | available | `README.md` L35-97, full flag reference |
| `chaos-client` | available | `README.md` L20-53, CLI flags + API notes |
| `alterx` | available | `internal/runner/runner.go` L28-74, flag defs |
| `urlfinder` | available | `internal/runner/options.go` L106-147, flag groups |

## Band B — Probe / scan / map (6/7 available)

| Collection | Status | Evidence |
|---|---|---|
| `httpx` | available | `runner/options.go` L463-495, full flag groups (score 0.995) |
| `naabu` | available | `README.md` L41-100, flag dump |
| **`katana`** | **UNAVAILABLE** | `no index found: katana (global)` — 2 queries ("crawling flags", "crawler configuration options cli") |
| `tlsx` | available | `README.md` L375-431, JA3/JARM examples (score 1.0) |
| `cdncheck` | available | `cmd/generate-index/provider.yaml` L338-413 + `sources_data.json` |
| `asnmap` | available | `runner/options.go` L76-124, flag defs (score 0.976) |
| `mapcidr` | available | `cmd/integration-test/mapcidr.go` L44-57, spec table |

`katana` is the one active-crawling tool in the suite and it has **no retrievable flag
reference** — get flags from the binary (`katana -h`) and never use `-jsl` on a broad scope.

## Band C — Infrastructure / auxiliary (5/5 available)

| Collection | Status | Evidence |
|---|---|---|
| `cloudlist` | available | `README.md` L34-84, providers/flags (score 0.995) |
| `uncover` | available | `runner/options.go` L61-90, flag defs (score 0.985) |
| `proxify` | available | `README.md` L221-245 (score 1.0) |
| `interactsh` | available | `README.md` L45-95 (score 0.986) |
| `simplehttpserver` | available | `internal/runner/options.go` L29-87 (score 0.985) |

## Band D — Nuclei + workflow/output (6/6 available)

| Collection | Status | Evidence |
|---|---|---|
| `nuclei` | available | `SYNTAX-REFERENCE.md`, `cmd/nuclei/main.go`, `lib/config.go` |
| `nuclei_docs` | available | `templates/structure.mdx`, `templates/introduction.mdx` |
| `nuclei-templates` | available | authoring/review guides, real CVE YAML templates |
| `notify` | available | provider config YAML, Go source + README |
| `pdtm` | available | tool manager flags, config paths |
| `aix` | available | README (single file), OpenAI CLI wrapper flags |

## Band E — Vulnerability-class payloads (0/10 available)

**All ten are unavailable.** Twenty searches (two distinct queries each) failed identically.

| Collection | Query A | Query B |
|---|---|---|
| `XSS` | `xss payload reflected stored dom` | `dom xss event handler bypass` |
| `SSRF` | `ssrf bypass payload` | `cloud metadata internal network request` |
| `SQLi` | `sql injection union payload` | `blind boolean time based injection` |
| `NoSQL-Injection` | `nosql injection payload mongo` | `mongodb operator authentication bypass` |
| `SSTI` | `ssti template injection payload` | `jinja2 twig freemarker rce` |
| `LFI` | `local file inclusion traversal payload` | `php filter wrapper file read` |
| `XXE` | `xxe dtd payload entity` | `blind xxe out of band exfiltration` |
| `JWT` | `jwt attack alg none` | `jwt signature confusion kid injection` |
| `Command-Injection` | `command injection payload` | `os command injection bypass filter` |
| `Insecure-Deserialization` | `deserialization gadget payload` | `java ysoserial python pickle gadget` |

Verbatim error envelope for every one:

```json
{
  "error": "Knowledge search failed: no index found: XSS (global): no index found",
  "suggestion": "Verify the index exists via action=\"status\"."
}
```

The `suggestion` is **misleading** — `status` has returned `exists: false` for indexes
(`nuclei`, `httpx`) that search successfully in the same session. Availability here is asserted
from the failed *searches*.

## Interpretation

This is an **availability observation, not an absence proof**. The registry appears to advertise
subscribed/enabled collections while the underlying vector index for Band E is not built, is
empty, or is not reachable with this workspace's credentials. The payload knowledge is not
necessarily absent from Neo overall.

The failure is **band-specific, not an outage**: in the same session `subfinder`, `dnsx`, `naabu`,
`tlsx`, `httpx`, `nuclei`, `cloudlist`, `uncover`, `proxify`, `interactsh` and
`simplehttpserver` all returned populated results on the first query.

**Consumer guidance.** `no index found: <name> (global)` means *"try a different retrieval
path"*, not *"the topic is undocumented"*. Do **not** react by calling `index_knowledge` to
create or seed the collection — that is an out-of-scope side effect. For Band E topics, fall back
to local payload/bypass references (the `hunt-*` skill family, `security-arsenal`) instead.

## Caveats on the captured content

- `limit: 3` was used per query, so `total_found: 3` reflects a cap, not a collection's size. The
  retrieved snippets are top-3 samples, not a file inventory.
- Source repos are **inferred** from result `file` paths and in-content GitHub links; results
  carry no explicit repo metadata field.
- Quoted flags are documentation-derived and may drift from an installed binary's `--help`.
- Not covered: the Chaos dataset contents, PDCP API behavior, live tool execution, version
  numbers, and non-retrieved pages.

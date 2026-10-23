# nuclei — engine CLI and Go SDK

Install: requires **go >= 1.24.2**.
`go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest`
Docs: https://docs.projectdiscovery.io/tools/nuclei/install

## TARGET

| Flag | Alt | Description |
|---|---|---|
| `-u` | `-target` | target URLs/hosts (string[]) |
| `-l` | `-list` | file of targets, one per line |
| `-eh` | `-exclude-hosts` | exclude (ip, cidr, hostname) |
| `-resume` | | resume from/save to file (**disables clustering**) |
| `-sa` | `-scan-all-ips` | scan all IPs for a DNS record |
| `-iv` | `-ip-version` | 4,6 (default 4) |

## TARGET-FORMAT

| Flag | Alt | Description |
|---|---|---|
| `-im` | `-input-mode` | list, burp, jsonl, yaml, openapi, swagger (default list) |
| `-ro` | `-required-only` | only required fields when generating requests |
| `-sfv` | `-skip-format-validation` | skip format validation |

`-im openapi` / `-im swagger` turns an API spec straight into a scan surface — the highest-value
non-obvious flag in this group.

## TEMPLATES

| Flag | Alt | Description |
|---|---|---|
| `-nt` | `-new-templates` | only new templates from latest release |
| `-ntv` | `-new-templates-version` | new templates from a specific version |
| `-as` | `-automatic-scan` | wappalyzer tech detection → tag mapping |
| `-t` | `-templates` | template or directory (comma-separated, file) |
| `-turl` | `-template-url` | template URL(s) |
| `-ai` | `-prompt` | generate and run a template from an AI prompt |
| `-w` | `-workflows` | workflow or directory |
| `-wurl` | `-workflow-url` | workflow URL(s) |
| `-validate` | | validate passed templates |
| `-nss` | `-no-strict-syntax` | disable strict syntax check |
| `-td` | `-template-display` | display template contents |
| `-tl` | | list templates matching current filters |
| `-tgl` | | list available tags |
| `-sign` | | sign templates with `NUCLEI_SIGNATURE_PRIVATE_KEY` |
| `-code` | | enable code-protocol templates |
| `-dut` | `-disable-unsigned-templates` | block unsigned / signature-mismatched templates |
| `-esc` | `-enable-self-contained` | enable self-contained templates |
| `-egm` | `-enable-global-matchers` | enable global matcher templates |
| `-file` | | enable file templates |

## FILTERING

| Flag | Alt | Description |
|---|---|---|
| `-a` | `-author` | filter by author(s) |
| `-tags` | | filter by tags |
| `-etags` | `-exclude-tags` | exclude by tags |
| `-itags` | `-include-tags` | include tags even if excluded |
| `-id` | `-template-id` | filter by id (wildcards allowed) |
| `-eid` | `-exclude-id` | exclude by id |
| `-it` | `-include-templates` | include file/dir even if excluded |
| `-et` | `-exclude-templates` | exclude file/dir |
| `-em` | `-exclude-matchers` | exclude matchers from results |
| `-s` | `-severity` | info, low, medium, high, critical, unknown |
| `-es` | `-exclude-severity` | exclude severities |
| `-pt` | `-type` | dns,file,http,headless,tcp,workflow,ssl,websocket,whois,code,javascript |
| `-ept` | `-exclude-type` | exclude protocol types |
| `-tc` | `-template-condition` | filter by expression condition |

## RATE-LIMIT (defaults shown)

| Flag | Alt | Default | Description |
|---|---|---|---|
| `-rl` | `-rate-limit` | 150 | max requests/second |
| `-rld` | `-rate-limit-duration` | 1s | rate-limit window |
| `-rlm` | `-rate-limit-minute` | | **DEPRECATED** |
| `-bs` | `-bulk-size` | 25 | hosts analyzed in parallel per template |
| `-c` | `-concurrency` | 25 | templates executed in parallel |
| `-hbs` | `-headless-bulk-size` | 10 | headless hosts parallel per template |
| `-headc` | `-headless-concurrency` | 10 | headless templates parallel |
| `-jsc` | `-js-concurrency` | 120 | JS runtimes parallel |
| `-pc` | `-payload-concurrency` | 25 | payload concurrency per template |
| `-prc` | `-probe-concurrency` | 50 | httpx probe concurrency |
| `-tlc` | `-template-loading-concurrency` | 50 | concurrent template loads |

## OPTIMIZATIONS

| Flag | Alt | Default | Description |
|---|---|---|---|
| `-timeout` | | 10 | seconds before timeout |
| `-retries` | | 1 | retries for failed request |
| `-ldp` | `-leave-default-ports` | | keep `host:80`/`host:443` form |
| `-mhe` | `-max-host-error` | 30 | errors before skipping host |
| `-te` | `-track-error` | | add error to max-host-error watchlist (standard, file) |
| `-nmhe` | `-no-mhe` | | disable host-skip on errors |
| `-project` | | | project folder to avoid duplicate requests |
| `-project-path` | | /tmp | project path |
| `-spm` | `-stop-at-first-match` | | stop after first match (**may break workflows**) |
| `-stream` | | | stream mode, no input sorting |
| `-ss` | `-scan-strategy` | auto | auto \| host-spray \| template-spray |
| `-irt` | `-input-read-timeout` | 3m0s | input read timeout |
| `-nh` | `-no-httpx` | | disable httpx probing for non-url input |
| `-no-stdin` | | | disable stdin processing |

`-mhe` is why long scans quietly go blank: 30 errors and the host is dropped. On flaky or
rate-limiting targets raise it or use `-nmhe`, otherwise you will read "no findings" as
"no vulnerabilities."

## HEADLESS

| Flag | Alt | Default | Description |
|---|---|---|---|
| `-headless` | | | enable headless templates (root on Linux disables sandbox) |
| `-page-timeout` | | 20 | seconds per page |
| `-sb` | `-show-browser` | | show browser |
| `-sc` | `-system-chrome` | | use local Chrome instead of bundled |
| `-cdpe` | `-cdp-endpoint` | | remote browser over CDP |
| `-lha` | `-list-headless-action` | | list headless actions |

## OUTPUT / AUTH / DEBUG / STATS / CLOUD

- **Output:** `-o`, `-sresp/-store-resp`, `-json-export`, `-markdown-export`,
  `-em/-exclude-matchers`, `-jle/-jsonl-export`
- **Auth:** `-sf/-secret-file` (secrets for authenticated scans), `-ps/-prefetch-secrets`
- **Debug:** `-debug`, `-dreq/-debug-req`, `-dresp/-debug-resp`, `-p/-proxy`,
  `-pi/-proxy-internal`, `-ldf/-list-dsl-function`, `-tlog/-trace-log`, `-elog/-error-log`,
  `-hm/-hang-monitor`, `-vv`, `-svd/-show-var-dump`, `-ep/-enable-pprof`,
  `-tv/-templates-version`, `-hc/-health-check`
- **Stats:** `-stats`, `-sj/-stats-json`, `-si/-stats-interval` (5), `-m/-metrics`,
  `-mp/-metrics-port` (9092)
- **Update:** `-up/-update`, `-ut/-update-templates`, `-ud/-update-template-dir`, `-duc`
- **Cloud:** `-auth`, `-cup/-cloud-upload`, `-sid/-scan-id`

`-ldf` lists every DSL helper function available to matchers — check it before inventing DSL.

## Example invocations

```bash
nuclei -target example.com
nuclei -target example.com -t http/cves/ -t ssl
nuclei -list hosts.txt
nuclei -target example.com -json-export output.json
MARKDOWN_EXPORT_SORT_MODE=template nuclei -target example.com -markdown-export nuclei_report/
nuclei -target 192.168.1.0/24          # network scan
```

## Go SDK (nuclei v3)

```
go get -u github.com/projectdiscovery/nuclei/v3/lib
```

```go
import nuclei "github.com/projectdiscovery/nuclei/v3/lib"

ne, err := nuclei.NewNucleiEngine(
    nuclei.WithTemplateFilters(nuclei.TemplateFilters{Severity: "critical"}),
)
if err != nil { panic(err) }
ne.LoadTargets([]string{"scanme.sh"}, false) // false = don't probe non-http
err = ne.ExecuteWithCallback(nil)
if err != nil { panic(err) }
defer ne.Close()
```

Thread-safe / concurrent batching:

```go
ne, err := nuclei.NewThreadSafeNucleiEngine()
wg := &sync.WaitGroup{}

wg.Add(1)
go func() {
    defer wg.Done()
    err = ne.ExecuteNucleiWithOpts([]string{"scanme.sh"},
        nuclei.WithTemplateFilters(nuclei.TemplateFilters{ProtocolTypes: "http"}))
}()

wg.Add(1)
go func() {
    defer wg.Done()
    err = ne.ExecuteNucleiWithOpts([]string{"honey.scanme.sh"},
        nuclei.WithTemplateFilters(nuclei.TemplateFilters{ProtocolTypes: "dns"}))
}()

wg.Wait()
defer ne.Close()
```

SDK internals:
- `func (e *NucleiEngine) ExecuteWithCallback(callback ...func(event *output.ResultEvent)) error`
- `func NewNucleiEngineCtx(ctx context.Context, options ...NucleiSDKOptions) (*NucleiEngine, error)`
- `nuclei.Concurrency{ TemplateConcurrency, HostConcurrency, HeadlessHostConcurrency,
  HeadlessTemplateConcurrency, JavascriptTemplateConcurrency, TemplatePayloadConcurrency,
  ProbeConcurrency }`

Full guide: https://pkg.go.dev/github.com/projectdiscovery/nuclei/v3/lib#section-readme

# Probe / scan / map tools

## httpx — HTTP probing and fingerprinting

**Probes:** `-sc/-status-code`, `-cl/-content-length`, `-ct/-content-type`, `-location`,
`-favicon`, `-hash` (md5,mmh3,simhash,sha1,sha256,sha512), `-jarm`, `-rt/-response-time`,
`-lc/-line-count`, `-wc/-word-count`, `-title`, `-bp/-body-preview`, `-server/-web-server`,
`-td/-tech-detect`, `-cff/-custom-fingerprint-file`, `-cpe`, `-wp/-wordpress`, `-method`,
`-ws/-websocket`, `-ip`, `-cname`, `-extract-fqdn/-efqdn`, `-asn`, `-cdn` (default true), `-probe`.

**Extended:** `-tls-grab`, `-tls-probe` (probe extracted TLS `dns_name` domains), `-csp-probe`,
`-pipeline`, `-http2`, `-vhost`, `-probe-all-ips/-pa`, `-ports/-p` (nmap syntax, e.g.
`http:1,2-10,11,https:80`), `-path`.

**Output:** `-o/-output`, `-oa/-output-all`, `-sr/-store-response`, `-srd/-store-response-dir`,
`-ob/-omit-body`, `-csv`, `-csvo/-csv-output-encoding`, `-j/-json` (JSONL),
`-irh/-include-response-header`, `-irr/-include-response`.

**Rate:** `-t/-threads`, `-rl/-rate-limit` (**default 150/s — set this explicitly**),
`-rlm/-rate-limit-minute`.

**Filtering:** `-fep/-filter-error-page` (ML error-page detection), `-fd/-filter-duplicates`,
`-fl/-filter-length`, `-flc/-filter-line-count`, `-fwc/-filter-word-count`,
`-ffc/-filter-favicon`, `-fs/-filter-string`, `-fe/-filter-regex`, `-fcdn/-filter-cdn`,
`-frt/-filter-response-time` (e.g. `'> 1'`), `-fdc/-filter-condition` (DSL).

**Misc:** `-lof/-list-output-fields`, `-eof/-exclude-output-fields`, `-ldv/-list-dsl-variables`,
`-hc/-health-check`, `-debug`, `-debug-req`, `-debug-resp`, `-stats`, `-fr/-follow-redirects`,
`-maxr/-max-redirects`, `-fhr/-follow-host-redirects`, `-rhsts/-respect-hsts`, `-ztls`,
`-tlsi/-tls-impersonate` (experimental JA3 client-hello randomization), `-hae/-http-api-endpoint`,
`-sf/-secret-file`, `-no-stdin`, `-no-decode`. Headless: `-ss/-screenshot`, `-system-chrome`,
`-ho/-headless-options`.

`-fep` and `-fdc` are the two highest-leverage flags for cutting a noisy probe set down to real
surface. Use `-lof` to discover output field names before writing `-eof` filters.

## naabu — port scanning

Features: SYN/CONNECT/UDP probe scanning; DNS port scan with automatic IP dedup; IPv4/IPv6
(experimental); passive port enumeration via Shodan InternetDB; host discovery (experimental);
NMAP integration; custom UDP payloads. Input: STDIN/HOST/IP/CIDR/ASN. Output: JSON/TXT/STDOUT.

| Group | Flags |
|---|---|
| Input | `-host`, `-list/-l`, `-exclude-hosts/-eh`, `-exclude-file/-ef` |
| Port | `-port/-p` (`80,443,100-200`), `-top-ports/-tp` (default 100; `[full,100,1000]`), `-exclude-ports/-ep`, `-ports-file/-pf`, `-port-threshold/-pts`, `-exclude-cdn/-ec`, `-display-cdn/-cdn` |
| Rate | `-c` (default 25 workers), `-rate` (default 1000 packets/sec) |
| Config | `-config` (default `$HOME/.config/naabu/config.yaml`), `-scan-all-ips/-sa`, `-ip-version/-iv` (default `["4","6"]`), `-scan-type/-s` (SYN/CONNECT, default `"c"`), `-source-ip`, `-cp/-connect-payload`, `-interface-list/-il`, `-interface/-i`, `-nmap-cli` (e.g. `-nmap-cli 'nmap -sV'`), `-r` (resolvers) |
| Output | `-o/-output`, `-j/-json`, `-csv`, `-up/-update`, `-duc/-disable-update-check` |

`-exclude-cdn/-ec` skips full port scans for CDN/WAF hosts and **only scans 80/443** — fast, but
wrong when hunting non-web services. `-nmap` is **deprecated**; use `-nmap-cli`.

## katana — active crawling

Inspect the installed binary's `-h` before composing a bounded crawl; keep concurrency, rate, depth, deadline, retries, redirects and exact-host/path scope explicit. Never use `katana -jsl` on a broad scope because deep JS-link analysis can exhaust memory.

### Reconcile crawl/probe artifacts before scheduling another stage

1. Parse saved JSONL with LF-delimited records and count record families. For Katana, distinguish rows containing `response` from reference/error rows. Explicit out-of-scope/depth-limit skips are not completed target requests; a transport error may represent an attempted request, so inspect its raw request/trace instead of subtracting every error row from traffic.
2. Bind observed responses to exact method/URL, raw request-body digest, timestamp and auth context. Verify attribution and inspect Authorization/Cookie header names. Record cookie names and source-supported roles separately from application credentials; an edge or affinity cookie is not proof of an authenticated user session. Leave unknown cookie roles unresolved and never publish values.
3. Verify each `stored_response_path` exists and hash the raw envelope. Read the path emitted by the tool rather than predicting the storage directory: no-clobber behavior can choose a suffixed directory.
4. Keep raw-envelope hashes, exact saved-body hashes and decoded JSON-body UTF-8 hashes in separately named fields; decoding or re-encoding text can change byte length and digest without proving truncation or corruption.
5. Check inputs, stderr and exit status with response counts. Preserve literal malformed/incorrect discovered URLs as observations; select later URLs from real parent HTML/script evidence rather than silently repairing and retrying crawler output.
6. Merge only evidence-bound actual-request records into the canonical request ledger, retain failed/unknown attempts separately, and recompute cumulative/per-origin usage before proposing follow-up traffic.

### Rate evidence

Save command/config limits before execution. For a minimum inter-request-spacing claim, capture timestamped request-start events through an approved request trace or proxy and calculate start-to-start gaps. Keep start and completion timestamps separate and retain the policy's rate-window definition: average throughput and strict spacing are different requirements. If only JSONL response timestamps exist, report configured limits and response-completion gaps with request-start compliance unverified; do not infer a violation solely from closely spaced completions.

## tlsx — TLS inspection and fingerprinting

Key flags: `-ja3`, `-jarm`, `-json`, `-silent`.

```
echo hackerone.com | tlsx -ja3 -silent
# hackerone.com:443 [20c9baf81bfe96ff89722899e75d0190]
echo hackerone.com | tlsx -jarm -silent
# hackerone.com:443 [29d3dd00029d29d00042d43d00041d5de67cc9954cc85372523050f20b5007]
```

JSON fields: `timestamp`, `host`, `ip`, `port`, `probe_status`, `tls_version` (e.g. `tls13`),
`cipher` (e.g. `TLS_AES_256_GCM_SHA384`), `not_before`, `not_after`, `subject_dn`, `subject_cn`,
`subject_org`, `subject_an`, `issuer_dn`, `issuer_cn`, `issuer_org`,
`fingerprint_hash.{md5,sha1,sha256}`, `tls_connection` (e.g. `ctls`), `sni`.

Connection modes: `auto/` (detect + fallback), `tls/` (Go crypto/tls), `ztls/` (ZMap zcrypto —
the JA3 path), `openssl/` (external binary). Fingerprinting lives in `pkg/tlsx/jarm/` and
`pkg/tlsx/ztls/ja3/`; CT log streaming in `pkg/ctlogs/`.

`subject_an` (subject alternative names) is the highest-value field for scope expansion —
it frequently reveals sibling domains no passive source listed.

## cdncheck — CDN / WAF / cloud attribution

Detects CDN, CLOUD and WAF. IP + DNS input, Text/JSONL output, output filters, usable as a library.

Index namespaces: `waf` (with `asn:` and `urls:`), `cloud` (`urls:`), `cdn` (CIDR list).

Providers: WAF `akamai` (ASNs `AS12222`, `AS16625`, `AS16702`, `AS17204`, …), `arvancloud`
(`AS208006`, `AS205585`), `sucuri` (`AS30148`), `cloudflare`, `gocache`; cloud `aws`, `google`,
`oracle`, `azure`, `zscaler`, `office365`.

Refresh sources: `https://api.cloudflare.com/client/v4/ips`,
`https://ip-ranges.amazonaws.com/ip-ranges.json`,
`https://www.gstatic.com/ipranges/cloud.json`,
`https://docs.oracle.com/en-us/iaas/tools/public_ip_ranges.json`,
`https://www.microsoft.com/en-us/download/confirmation.aspx?id=56519`,
`https://api.config.zscaler.com/zscaler.net/cenr/json`,
`https://endpoints.office.com/endpoints/worldwide?clientrequestid=…`,
`https://www.arvancloud.ir/fa/ips.txt`.

Use `cdncheck` before a port scan to decide whether `naabu -ec` is appropriate, and before
interpreting a zero-result nuclei run as a clean baseline.

## asnmap — ASN / organization → CIDR

| Group | Flags |
|---|---|
| Input | `-a/-asn` (`-a AS5650`), `-i/-ip` (`-i 100.19.12.21`, `-i 2a10:ad40::`), `-d/-domain` (`-d google.com`), `-org` (`-org GOOGLE`), `-f/-file` |
| Config | `-auth` (configure PDCP API key, default `"true"`), `-config`, `-r/-resolvers`, `-p/-proxy` |
| Output | `-o/-output`, `-j/-json`, `-c/-csv`, `-v6` (IPv6 CIDRs), `-v/-verbose`, `-silent`, `-up/-update`, `-duc/-disable-update-check` |

ASN input must start with `AS`, else:
`"invalid ASN given. it should start with prefix 'AS', example : AS14421"`.
Library: `GetCIDR()` maps `FirstIp`/`LastIp` pairs to `net.IPNet` via `mapcidr.GetCIDRFromIPRange`.

## mapcidr — CIDR arithmetic

Capabilities: CIDR expansion (default), slicing (`-sbh`, `-sbc`), aggregation (`-a`, `-aa`),
matcher (`-match-ip`), filter (`-filter-ip`), sorting (`-s`, `-sr`), host count (`-count`),
IP formats (`-ip-format`), IP/PORT shuffling (`-si`, `-sp`), IPv4/IPv6 conversion (`-t4`, `-t6`),
STDIN input.

Verified behaviours: `-fi 192.168.0.128/25`, `-sbc 2` (slice into /26s), `-t6`
(→ `00:00:00:00:00:ffff:c0a8:0000`), `-skip-base`, `-skip-broadcast`, `-s`, `-sr`, `-si`,
`-sp 8080`, `-sp 8080,9090`, and IP-range expansion `192.168.0.0-192.168.0.3`.

`-si` (shuffle IPs) plus `-sp` (shuffle ports) is how you avoid scanning a netblock in
sequential order, which is the pattern most rate-limiters key on.

Install: `go install -v github.com/projectdiscovery/mapcidr/cmd/mapcidr@latest`.

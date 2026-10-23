# Composable pipeline recipes

Recipes are Bash fragments, not a script to run every branch. Replace illustrative scope and paths with the established target scope. Run from a new research run directory. Check installed `-h` before use. Plain streams compose directly; JSONL requires explicit adapters. Branches that need new authorization remain offline until their scope is established.

## Setup and scope gate

```bash
set -euo pipefail
umask 077
PD_SKILL="${CODEX_HOME:-$HOME/.codex}/skills/projectdiscovery-recon"
PD_DATA="$PD_SKILL/scripts/pd_data.py"
mkdir -p raw work logs inventory
```

Create `scope.json` per operations.md. `roots.txt` holds authorized enumeration roots; `seeds.urls.txt` holds exact allowed starting URLs, preserving ports/path prefixes. A domain-only task can generate seeds from approved resolved hostnames if the authorized scheme/port/path policy permits it. Do not manufacture root-URL probes for a path-only scope.

## 1. Passive hosts → scoped resolution

```bash
subfinder -dL roots.txt -all -oJ -cs -rl 5 -silent \
  > raw/subfinder.jsonl 2> logs/subfinder.log
jq -r '.host // empty' raw/subfinder.jsonl \
  | python3 "$PD_DATA" scope --kind hosts --scope scope.json \
  > work/hosts.txt 2> logs/host-scope.log
test -s work/hosts.txt
dnsx -l work/hosts.txt -a -aaaa -cname -j -rl 20 -silent \
  > raw/dnsx.jsonl 2> logs/dnsx.log
jq -r '.host // empty' raw/dnsx.jsonl | LC_ALL=C sort -u > work/resolved.txt
```

Inspect actual DNS answer fields to distinguish usable A/AAAA records from CNAME-only or error results. Retain both IPv4 and IPv6 observations; a DNS miss is not proof of no HTTP service. For wildcard DNS, use randomized negative names and inspect `dnsx -wd` constraints or use shuffledns. Do not mix wildcard mode with assumed regular DNS flags.

Compact host chain when both HTTP and HTTPS root probes are authorized and DNS output is plain:

```bash
subfinder -d example.com -silent 2> logs/subfinder-chain.log \
  | tee raw/subfinder-hosts.txt \
  | python3 "$PD_DATA" scope --kind hosts --scope scope.json \
  | tee work/scoped-hosts.txt \
  | dnsx -silent -rl 20 2> logs/dnsx-chain.log \
  | tee work/resolved-chain.txt
```

This intentionally checkpoints before HTTP. Apply the URL policy and inspect the phase outcome before proceeding. Host filters do not enforce port/path limits.

Optional passive sources; merge their host fields into the same gate:

```bash
chaos -d example.com -silent > raw/chaos-hosts.txt 2> logs/chaos.log
cloudlist -id approved-account -host -silent > raw/cloud-hosts.txt 2> logs/cloudlist.log
uncover -q 'hostname:example.com' -e shodan -j -l 100 -rl 2 \
  > raw/uncover.jsonl 2> logs/uncover.log
```

Provider query syntax is engine-specific. Inspect uncover JSONL before choosing fields. Its default plain output is IP:port, not hostnames. Keep ownership and host-to-IP provenance; do not pipe all search results into scanners.

## 2. Exact URL seeds → HTTP evidence → crawl seeds

Scope-filter `seeds.urls.txt` before probing. `-nfs` preserves input schemes and prevents scheme fallback. Redirect following stays disabled by default; check configs for overrides.

```bash
python3 "$PD_DATA" scope --scope scope.json --input seeds.urls.txt > work/seeds.txt
test -s work/seeds.txt
httpx -l work/seeds.txt -nfs -silent -j -sc -title -td -cl -ct -location \
  -hash sha256 -rl 5 -t 2 -timeout 10 -retries 1 -rstr 1048576 \
  > raw/httpx.jsonl 2> logs/httpx.log
jq -r 'select(.failed != true) | .url // empty' raw/httpx.jsonl \
  | python3 "$PD_DATA" scope --scope scope.json > work/live.urls.txt
```

Avoid `httpx -sc -title | katana`: metadata pollutes the URL stream. Use JSON extraction above, or `httpx -silent` with no decorating flags. Do not filter the inventory to status 200. Resolve `Location` against the response URL, scope-check it, then add permitted destinations to a later batch; `-fr` can leave scope.

## 3. Crawl → structured endpoints and JavaScript

For a small, validated exact-origin seed batch, tools can stream directly. This example allocates 2 RPS to each active process (up to 4 combined); staged recipes remain easier to resume and diagnose. Every seed must already match the example origin and full-origin authorization. A downstream process can start before upstream completion, so use staged files if phase success must precede new requests.

```bash
python3 "$PD_DATA" scope --scope scope.json --input seeds.urls.txt \
  | httpx -silent -nfs -rl 2 -t 1 -rstr 1048576 2> logs/httpx-stream.log \
  | tee work/stream-live.urls.txt \
  | katana -silent -j -jc -d 3 -dr -rl 2 -c 1 -p 1 -ct 2m -mrs 1048576 \
      -cs '^https://app\.example\.com(?::443)?(?:/|$)' \
      -cos '(?i)/(logout|delete|unsubscribe)(?:/|\?|$)' \
      2> logs/katana-stream.log \
  | tee raw/katana-stream.jsonl \
  | jq -r '.request.endpoint // empty' \
  | python3 "$PD_DATA" scope --scope scope.json > work/stream-discovered.urls.txt
```

Example only for an exact host whose full HTTPS origin is authorized:

```bash
katana -list work/live.urls.txt -silent -j -jc -fx -kf all -d 3 \
  -cs '^https://app\.example\.com(?::443)?(?:/|$)' \
  -cos '(?i)/(logout|delete|unsubscribe)(?:/|\?|$)' \
  -dr -rl 5 -c 2 -p 1 -ct 2m -mrs 1048576 \
  > raw/katana.jsonl 2> logs/katana.log
jq -c '{url:.request.endpoint,method:(.request.method // "UNKNOWN"),
  source:"katana",auth_context:"anonymous",confidence:"crawl-record",
  status:(.response.status_code // null),
  evidence:("raw/katana.jsonl:" + (input_line_number|tostring)),
  discovered_from:(.request.source // null)} | select(.url | type == "string")' \
  raw/katana.jsonl > work/katana.events.jsonl
```

Adjust `-cs` and `-cos` to the actual authorization. For multiple origins, construct escaped, anchored alternatives; never interpolate unescaped domains into regex. Keep `-kf all` only when root robots/sitemap access is allowed; its documented minimum depth is 3. `-jsl` adds deeper JS parsing at substantial memory cost; apply selectively under a size/time cap. Default extension filtering can hide file classes; inspect `-ndef` and filtering behavior when those file types matter. Do not prune traversal merely to make output look cleaner.

For an authorized SPA needing runtime evidence, repeat a small selected seed batch with `-hl -xhr` and the same scope/budget flags. Capture method/URL data from actual JSON fields; headless output schemas vary, so inspect a sample (`katana -lof` where supported). Do not invent `.xhr` adapters without verifying the structure. Keep observed XHR methods; do not flatten everything into GET. Browser subrequests need separate containment under strict scope.

For authenticated browsing, use isolated origin/role sessions and supported private header files. Do not add `-aff` or automatically replay forms. Proxify can capture manual authorized workflows when headless discovery misses interaction-dependent routes:

```bash
proxify -ha 127.0.0.1:8888 -o raw/proxify.jsonl -of jsonl
```

Inspect `proxify -h` for the installed output syntax. Configure only the isolated test browser/proxy chain; do not change system-wide trust or redirect unrelated user traffic. Normalize captured requests offline using the event contract.

## 4. Passive URLs → merge without accidental active replay

```bash
urlfinder -d example.com -all -j -cs -rl 5 \
  > raw/urlfinder.jsonl 2> logs/urlfinder.log
jq -c '{url:.url,method:"UNKNOWN",auth_context:"unspecified",
  source:("urlfinder:" + ((.source // .sources // "unknown")|tostring)),
  confidence:"passive-candidate",
  evidence:("raw/urlfinder.jsonl:" + (input_line_number|tostring))}' \
  raw/urlfinder.jsonl > work/urlfinder.events.jsonl
cat work/katana.events.jsonl work/urlfinder.events.jsonl > work/events.jsonl
python3 "$PD_DATA" inventory --scope scope.json --input work/events.jsonl \
  --output inventory/pass-1
```

Passive URLs can include tokens, stale hosts, and state-changing paths. Review selected probe candidates; never feed the entire inventory back into httpx. Include schema/capture/JS events in the same merge as they become available.

## 5. File/API path products → scoped probes

Choose a small `work/origins.txt` batch and a reviewed root-relative path list. Budget the cross-product offline before HTTP. Prefix paths for subpath-mounted applications; the seed file is origin-root-relative.

```bash
python3 "$PD_DATA" paths --scope scope.json --origins work/origins.txt \
  --input "$PD_SKILL/assets/discovery-paths.txt" --limit 1000 \
  > work/path-candidates.txt
test -s work/path-candidates.txt
httpx -l work/path-candidates.txt -nfs -silent -j -sc -cl -ct -location \
  -hash sha256 -rl 5 -t 2 -timeout 10 -retries 1 -rstr 1048576 \
  > raw/path-probes.jsonl 2> logs/path-probes.log
```

`httpx -l work/origins.txt -path work/paths.txt ...` is the native shortcut when every origin/path combination is already authorized. Explicit products above permit scope checks, count limits, and exact provenance. Add randomized controls from files-and-apis.md. Keep all statuses in raw output; derive ranked candidates afterward.

Convert probe results into events before the next inventory merge:

```bash
jq -c '{url:.url,method:(.method // "GET"),auth_context:"anonymous",
  source:"httpx-path",confidence:"probe-response",status:.status_code,
  length:.content_length,content_type:.content_type,location:.location,hash:.hash,
  evidence:("raw/path-probes.jsonl:" + (input_line_number|tostring))}' \
  raw/path-probes.jsonl > work/path.events.jsonl
```

## 6. Optional host/port/TLS expansion

Offline permutations followed by scoped DNS resolution:

```bash
alterx -l work/hosts.txt -en -es > work/permutation-estimate.txt
alterx -l work/hosts.txt -en -limit 1000 -silent \
  | python3 "$PD_DATA" scope --kind hosts --scope scope.json > work/permutations.txt
dnsx -l work/permutations.txt -silent -rl 20 > work/permutations-resolved.txt
```

For a separately budgeted wildcard-heavy DNS branch, use `shuffledns -d example.com -list work/permutations.txt -r resolvers.txt -mode resolve -silent`. Tune `-t`, wildcard concurrency and underlying massdns options from local help; concurrency is not a strict DNS QPS limit. Do not use default high-volume settings under a small budget.

For explicitly approved network targets/ports only:

```bash
naabu -l work/approved-port-targets.txt -p 80,443,8080,8443 -s c -rate 20 -c 2 -j \
  > raw/naabu.jsonl 2> logs/naabu.log
tlsx -l work/approved-tls-services.txt -san -cn -j -c 2 -timeout 5 -retry 1 \
  > raw/tlsx.jsonl 2> logs/tlsx.log
cdncheck -i work/hosts.txt -j > raw/cdncheck.jsonl 2> logs/cdncheck.log
```

Naabu JSONL usually nests the port under `.port.port`; verify a row before building URLs. Preserve the original hostname for HTTP Host/TLS SNI instead of replacing everything with `.ip`. Scope-check schemes and ports before httpx. `naabu -ec` limits some CDN scans but does not prove third-party network authorization. tlsx SANs are candidate names, including wildcards; do not treat a wildcard certificate string as a concrete host.

Network mapping branch: `asnmap -d example.com -j` produces associations for review. Count approved ranges with `mapcidr -cl approved-cidrs.txt -count`; intersect candidate addresses with approved ranges (`-mi`) before expansion/probing. Do not pipe arbitrary ASN ranges straight into naabu.

## 7. Selected Nuclei discovery and deltas

Read exact local templates first, then validate the selected files. An `info` severity or `exposure` tag is not a read-only guarantee. Exclude arbitrary methods, fuzzing, OAST, remote hosts, workflows, code, headless/JavaScript actions, and destructive behavior unless separately authorized. Restrict path requests and redirects inside the actual templates.

```bash
nuclei -validate -t work/reviewed-discovery-templates/
nuclei -l work/approved-discovery-origins.txt -t work/reviewed-discovery-templates/ \
  -pt http -ni -dr -rl 5 -c 2 -bs 1 -j \
  > raw/nuclei-discovery.jsonl 2> logs/nuclei-discovery.log
```

Nuclei accepts OpenAPI/Swagger input in supported versions, but executing schema operations is not required to enumerate them. Parse schemas offline first; do not run `-im openapi` indiscriminately during recon. A scanner finding also does not replace endpoint presence controls.

Incremental comparison (both files sorted with the same locale):

```bash
LC_ALL=C sort -u previous/urls.txt > work/previous.sorted.txt
LC_ALL=C sort -u inventory/pass-1/urls.txt > work/current.sorted.txt
LC_ALL=C comm -13 work/previous.sorted.txt work/current.sorted.txt > work/new.urls.txt
```

Use full inventory records for method/auth/status changes. `anew` is an optional external dedup helper; it is not needed here. `notify` requires explicit authorization to send to the chosen destination. Do not create a monitor or upload results merely because delta files exist.

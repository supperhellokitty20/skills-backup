# API surface from a client bundle

Use advertised client assets as a source-backed inventory before guessing API paths. The inventory
covers client-used functionality, not every server route. Apply the scope/traffic gates in
`bb-workspace-layout` and the tool/wordlist rules in this skill's SKILL.md first.

## 1. Capture complete application assets

Read an authorized page and record its script references. Prioritize application bundles and runtime
configuration; vendor chunks contain mostly framework noise. Record separately scoped application
hosts in `functional-sibling-hosts.tsv` before fetching their assets.

Create the output directory, then capture each approved asset with TLS verification, no automatic
redirect following, the literal program attribution header, a time limit and a finite size ceiling:

```bash
curl --silent --show-error --max-time 30 --max-filesize "$MAX_BYTES" \
  -H "$ATTR_HEADER" --dump-header scans/client/app.headers \
  --output scans/client/app.js \
  --write-out '%{http_code} %{size_download} %{ssl_verify_result}\n' \
  "$SCOPED_JS_URL" > scans/client/app.transfer.txt 2> scans/client/app.stderr
```

Set the variables from the approved pass before running this recipe; save the command and exit
status beside the response. Do not add `-k` or `-L` to make a failing baseline appear successful.
Inspect a redirect's next host against scope before authorizing a separate request.

Check curl completion, HTTP status, content type, saved byte count and response headers before
mining. Compare Content-Length only when representation/encoding makes it meaningful. Record the
asset hash and any capture ceiling. A timeout/size-limit partial file is incomplete evidence;
a parser reaching EOF does not prove a complete download. Never silently clip a bundle with a
fixed-size read and then conclude that missing callsites do not exist. Recollect within the approved
budget or mark the mapping partial.

## 1b. When the bundles sit on an unauthorized host: capture the app's own traffic

A modern SPA can set a separate asset origin (`assetPrefix: //assets.example-cdn.net/rc-ab12cd`), which
puts the whole client bundle on a host that is not on the asset list. A ref extracted from the HTML and
resolved against the page origin then 404s — every chunk, wasting the pass and reading as a clean
application rather than as a failed fetch.

Do **not** solve that by fetching the unlisted host, and do not treat it as the end of the lane. Load
the in-scope page in a background browser tab and capture the traffic the application makes **itself**:

```
interceptor --group <lane> open https://www.example.com --text-only
interceptor --group <lane> net log --format json --out <root>/scans/<lane>/net-log.json
```

This maps the live API surface without hand-aiming a request at any out-of-scope host, and it is often
richer than bundle mining because it shows the real call shapes, parameters and statuses. What it
establishes is a dependency graph, and the output is two lists:

- **Calls to listed hosts** — the in-scope API surface. It may be far smaller than expected (two config
  endpoints, say, while every piece of real data comes from elsewhere).
- **Calls to unlisted hosts** — record each in `functional-sibling-hosts.tsv` as a dependency with the
  observed request as evidence, then **send nothing to them** and raise the scope question. Traffic the
  app initiated is evidence of use, not authorization to test. The highest-value result of this
  exercise is often discovering that every interesting API is off-list — a scope finding worth putting
  to the program in writing rather than a dead lane.

Read `assetPrefix` and `buildId` out of the page HTML first, and rank the app's own chunks
(`chunks/app/**`) ahead of vendored ones: a first-N-in-HTML-order slice picks nextjs/react/mui vendor
bundles and reports a false "zero API paths" on a site that has one.

Two hygiene rules: captured traffic and any `tabs` listing include **the user's own browsing** — never
read, act on, or report their tabs. And because subresource/XHR loads sit outside your request ledger,
state that accounting gap explicitly rather than implying complete network accounting.

## 2. Map request contracts offline

Run the bundled extractor against saved files, not the network:

```bash
python3 scripts/js_api_map.py scans/client/app.js
python3 scripts/js_api_map.py --json scans/client/app.js > scans/client/api-map.json
```

Treat extractor results as candidates. Follow URL builders and HTTP-client wrappers back to their
callsites; a base URL may be used directly with query parameters rather than appended subpaths.
For each client operation record:

- HTTP method and resolved base host/path;
- query keys, body fields, encoding and path parameters;
- auth headers and where their values originate;
- configuration/environment selection;
- source file, hash and extraction location (state byte versus character offsets);
- unresolved dynamic pieces and whether the operation is safe to invoke.

**Scope each record to its own delimited segment; never window.** When recovering a machine-regular
framework definition (RTK Query slices, generated reducers, chunk registries), split the container at
each record boundary and read fields only from inside that record's own slice. A fixed-size window
opened at the first record runs into the next one and silently attributes the neighbour's fields: taking
"the first `url:"…"` after this endpoint name" produced paths that concatenated one endpoint's base with
the next endpoint's path — plausible enough to be pasted straight into a report. Brace-match the
container to its own end, then split at every record start.

Also recover the paths that are not string literals. A definition may return the path bare
(`query:()=>"/loyalty/configuration"`) or build it by concat (`query:e=>"/live-event/".concat(e)`); a
parser that only reads `url:"…"` under-reports, and the concat forms are exactly the ID-bearing paths
worth your attention. Where a field still cannot be proven inside its own segment, emit `UNKNOWN` — an
unproven path is a coverage gap, and guessing one is how a fabricated endpoint reaches a probe list.

Bound text snippets around callsites rather than printing a minified megabyte-long line. Keep
framework symbols out of wordlists. Distinguish source-observed values from researcher-selected
synthetic values. A client-shipped key is not automatically a reportable secret or authorization
to use it against another tenant.

**Disprove "this bundle value is a secret" before reporting it — three shapes that keep recurring.** A
grep for `key|token|secret` across a bundle returns mostly public-by-design values, and each one looks
alarming in isolation:

- **A key-issuing endpoint whose value the client generates itself.** An API returning `{"key": "<base64>"}`
  proves nothing until you read the client's own generator: if the app computes the same value locally from
  a public constant plus the current date, the endpoint is redundant, not a credential.
- **A UI/editor library's public CDN key.** Rich-text editors, map providers and widget SDKs ship one.
  Adjacent config keys such as `cloudChannel`/`apiKey` belong to that library, not to a storage or mail
  provider — read the surrounding config schema before naming a provider.
- **A web Firebase `apiKey`.** A public project identifier by design, shipped in every Firebase web app.
  Record it as present, never by value; the finding, if any, is in the project's rules, not the key.

The method is identical each time: find the code that *uses* the value and read its generator or config
schema before writing anything up. Several false "exposed credential" reports in one engagement is a
pattern, not bad luck. An **internal hostname** found the same way is different — that IS real disclosure
evidence, so route it to the configuration-disclosure class in `bb-finding-triage-gate` rather than
treating it as a breach.

**Server-rendered page config beats bundle mining for the env map.** Many Rails/SSR apps embed the
entire environment-variable surface as a URL-encoded JSON block in a `<script type="application/json">`
tag on the landing page — one `curl` returns the config map (API hosts, keys, feature flags) that
bundle mining would take a dozen chunk fetches to reconstruct. Read it first by unquoting each
`application/json` script block on the page; the same page's `<script src>` list is then the
*exhaustive* chunk inventory — no guessing chunk ids. Expect homepage bundles to be a small
"landing" app: the real customer app's chunks appear only on authenticated/app paths and are
bot-walled for non-browser UAs, so a homepage-only mine that finds no app code is a
browser-session prerequisite, not a mapping failure.

Classify every dependency independently: a bundle reference proves use, not permission. A cloud/CDN
CNAME neither proves nor disproves customer-tenant ownership. A provider-native API URL outside the
listed hostname scope stays pending authorization even if the scoped client calls it; collect its
static request contract without contacting the provider host.

## 3. Build a small control pass before expanding

Use the exact source-derived method/query/body contract. Do not convert every observed operation
to GET, guess `/base/FUZZ` when the client uses `/base?key=value`, or invoke a state-changing POST
merely because it appears in JS. For approved read-only GET discovery:

1. Include the known route baseline and two impossible-path controls under the same host/prefix.
2. Add a few empty/deliberately invalid input variants. Never enumerate customer IDs or device
   serials to compensate for missing tester-owned fixtures.
3. Save the list and provenance beside it; budget its input count and anticipated traffic before
   launch. Keep token-bearing requests out of ordinary wordlist/provenance logs.
4. Set rate, concurrency and deadline explicitly; reserve aggregate budget for other workers and
   follow-up verification. Disable automatic redirect following.

**Validate the pass before mining it: the known-live baseline must DIFFER from the impossible-path control.** If a route you have watched return a real response in the app's own browser traffic answers with the same status *and* the same body as a fabricated path, your requests never reached the route layer — a CDN/WAF/gate answer, or a request shape the edge rejects — and the pass says nothing about route existence. Discard it; do not read the one path that happened to differ. A lone `500` among uniform `404`s inside an invalid pass is a non-route response, not a discovered endpoint, and promoting it is how a fabricated work order reaches the shortlist. Confirm you can reproduce the known-live route's real response in a different request context before spending the pass again. Some handlers are reachable only from the app's own browser context (its cookies/session state), so a bare shell client cannot map them at all — record that as a coverage limit, never as evidence the routes are absent.

Use ffuf rather than a bespoke HTTP matcher. After creating output directories and setting the
variables from scope, the initial control pass is:

```bash
ffuf -w wordlists/observed-requests.txt -u "$URL_PATTERN" \
  -H "$ATTR_HEADER" -H 'Accept: application/json, */*' \
  -mc all -t 1 -rate "$RPS" -timeout 25 -maxtime "$PASS_SECONDS" \
  -noninteractive -s -of json -o scans/control-pass/results.json \
  -od scans/control-pass/responses \
  -debug-log scans/control-pass/debug.log \
  > scans/control-pass/stdout.log 2> scans/control-pass/stderr.log
```

`URL_PATTERN` contains exactly one FUZZ marker in the source-evidenced path/query position. Confirm
flags with the installed build. Preserve all control-pass responses: do not apply status/body
filters yet. Save exit status and inspect completion/error accounting, not only the hits JSON.

For a later, explicitly budgeted expansion, derive body filters from these archived controls.
Do not blanket-filter every 403 or 500; distinguish the edge catch-all from real route responses.
Automated discovery output is not a standalone vulnerability report where program policy excludes
scanner-generated reports; manually establish permitted impact before promoting a lead.

## 4. Compare bodies and state a bounded verdict

Parse ffuf's saved request/response envelopes before hashing the response body; hashing the whole
file compares different requests and volatile headers instead of application behavior. Verify the
extracted body length against the recorded response size. Retain status, headers, raw paths and
body hashes so the comparison is reproducible.

| Observation | Supported conclusion |
|---|---|
| Same status and byte length as a missing-path control | Possible catch-all; compare bodies before concluding |
| Identical response body across controls and candidate paths | No route-specific behavior demonstrated by these requests |
| Distinct body or auth rejection | Route/gateway signal; not proof of correct authorization or a vulnerability |
| Byte-identical generic 500 across empty/invalid inputs | Input-handling baseline only; no protected data or impact shown |
| Public health response | Service availability signal, not an exposure finding by itself |
| Client token-presence gate with Bearer requests | Server enforcement unresolved; client-side checks alone do not prove bypass |
| No successful tester-owned authenticated flow | Authorization coverage remains partial |

Use tester-owned fixtures and appropriate controls for an authorization verdict. A rejection for
invalid/missing credentials demonstrates that tested rejection state, not authorization correctness
for valid users or object boundaries. Mark a source-referenced route that still returns a catch-all
as unmapped under the tested contract; do not declare it absent or compensate with unbounded fuzzing.

Verify input count, completed/error counts and saved response count before declaring the pass
complete. Record interrupted, filtered and unreachable cases separately. Update the lead/coverage
ledger with evidence paths, bounded conclusions and the next missing prerequisite; preserve the
raw captures and do not promote mapping signals to findings.

## 5. Gateway fingerprints

| Symptom | Likely stack | Testing implication |
|---|---|---|
| `Ocp-Apim-Subscription-Key` requirement; JSON route-not-found response | Azure API Management | Client key handling and user/object authorization are distinct boundaries |
| `x-envoy-upstream-service-time`, correlation headers | Envoy-backed gateway | Upstream routing signal, not proof of authorization |
| `via: 1.1 varnish`, `x-served-by`, `x-cache` | Varnish/Fastly-style caching | Compare cache behavior on policy-approved URLs and vary one factor at a time |
| Adobe clientlibs paths and publish vhost markers | AEM deployment | Distinguish customer application scope from Adobe infrastructure |
| App host CNAME ending in `azurewebsites.net` | Azure App Service | Cloud hosting alone does not exclude a scoped customer app |
| `{"fault":{"faultstring":"Unable to identify proxy for host: <vhost> and url: <path>","detail":{"errorcode":"messaging.adaptors.http.flow.ApplicationNotFound"}}}` | Google Apigee | Unrouted path. The same host answering `steps.oauth.v2.FailedToResolveAPIKey` instead means a proxy **exists** and enforces its key — so the fault class is a reliable route-existence oracle for enumerating basepaths on a shared vhost. The body echoes the requested path, so byte size is not a control; compare fault class. The leaked platform/vhost detail is config disclosure with no access shown, i.e. hygiene rather than a finding |

Fingerprints are hypotheses, not sufficient ownership or vulnerability evidence. Server-only routes,
admin operations and other client chunks may remain unmapped; report those coverage gaps explicitly.

# Production Source-Map Recovery

A served `.map` is the cheapest way to recover a SPA's true surface: exact route constants,
service modules that reveal query-parameter names, and config modules carrying base URLs and
ports. Treat it as a first-class capture artifact, not a curiosity.

## Is it served?

Fetch `<bundle>.js.map` on the same host as the bundle. Production maps are frequently left in
place even when the app is minified. Signals that it is a real, long-standing artifact rather
than something you generated:

- `Content-Type: text/plain` or `application/json`, no `Content-Length`
- `ETag` + an old `Last-Modified`
- a `version: 3` JSON body with a populated `sourcesContent` array

No `Content-Length` means the response is chunked: there is **no advertised size**, so a capture
truncated by your read cap is indistinguishable from a complete one. Raise the cap and re-fetch
under its own manifest event before analysing anything. An artifact this large is usually 1-10 MB.

## Parse it from disk, never from stdout

Store the raw bytes first, hash them, then parse the file. Structure:

```
version, file, mappings, names[], sourceRoot, sources[], sourcesContent[]
```

`sources[i]` pairs positionally with `sourcesContent[i]`. Drop `../webpack/*` and
`../node_modules/*` entries to isolate first-party files; the residue is the application's own
module tree.

## What to mine from first-party source

| Module shape | What it yields |
|---|---|
| Endpoint constants (`const API = { X: '/GetX', ... }`) | The complete route inventory, including routes absent from the live minified bundle |
| Service modules (`API.get(CONST.X + "?param=" + v)`) | Real query-parameter **names** and which are required vs optional |
| Helper/config modules | Base URLs, environment URLs, hardcoded ports, internal hostnames |
| Client-identity logic | How a custom request header is generated — see below |

Endpoint constants and callsites are different facts: one constant may be called from several
services with different query shapes. Report the union of distinct endpoints plus their concrete
parameter sets, not a flat count of appearances.

## The currency check (do this before claiming anything is live)

The map's own `file` field names the build it was generated for. Compare it against the bundle the
site actually serves now. **If they differ, the map describes a superseded build.** Anything you
find in it — a route, an internal URL, a credential — must be re-verified in the live bundle or by
request before it can be called current. A leak present in both is current; a leak present only in
the map is historical and much weaker.

The same applies to route inventory: a map can list endpoints the live app no longer serves. Confirm
each candidate by request, and keep an impossible-path control in the same pass so that
"route removed" (app shell / catch-all) is distinguishable from "route exists but gated"
(distinct status, distinct content type, or a distinct error body).

## Classify recovered values before reporting any of them

Recovered source routinely contains strings that look like secrets. Locate the value's
**generation or consumption** in the same recovered tree before calling it one.

- A header or token the client derives itself — a public constant plus the current date, a UUID
  baked into the bundle — is **client compatibility**, not a credential. Every real visitor's
  browser sends it. Supplying it is emulating the application's own client, not bypassing a
  control; say so explicitly in the report so a reviewer running a bare `curl` (who gets the
  auth rejection, and concludes the finding is unreproducible) understands the precondition.
  Apply the same test to a **live endpoint whose name promises a key** (`/GetValidKey`, `/GetToken`,
  `/GetAuthKey`): if the value it returns is one the client already reproduces locally from public
  input, the endpoint is cosmetic and the response is not a credential. Endpoint naming is not
  evidence — the client's own generation logic is.
- A bundled third-party SDK's public client key (identity widget, maps, analytics) is public by
  design, like an OAuth `client_id`. Not a secret, not a finding. Do not record its value.
- A value whose **use** you cannot trace to a privilege beyond what the app already serves
  anonymously is not a finding, however alarming it reads.

## What actually makes a map a finding

The map alone is informational. Severity comes from content:

- Hardcoded credentials, tokens or connection strings
- **Internal hostnames with non-standard ports and internal/corporate domains** — internal
  topology disclosure, and the strongest thing a map usually yields
- Internal repository names and CI build paths (e.g. an Azure Pipelines `C:\\a\\1\\s\\...`
  layout), which date and identify the build system
- The origin hostname sitting behind the CDN

Confirm the internal host is **not** in the program's allowlist before doing anything with it. Its
disclosure is the finding; contacting it is out of scope and is not required to report it.

## Anchor discipline

Report the artifact with its SHA256 and the **byte offset of the needle**, in every artifact that
carries it — the map and the live bundle separately. "The string appears in the source map" is not
reproducible; "byte 484186 of a file with SHA256 `9fca…`" is.

# File and API discovery playbook

## File coverage beyond homepage links

Start with crawl and passive URL evidence; keep extensionless paths too. Inspect robots/sitemap references, HTML links and script tags, CSS URLs/sourceMappingURL, service-worker precache lists, web manifests, asset/build manifests, import maps, dynamic imports, and application route configuration. Preserve paths relative to the originating resource and its public deployment prefix.

Classify candidates into scripts/modules, source maps, styles/assets, manifests, API descriptions, documentation, downloads, and configuration/backup/archive exposures. Use path extension plus content type and content signatures; an HTML login page at `/config.json` is not a JSON file. Do not remove static extensions globally before harvesting JS/map/manifest references.

Use `assets/discovery-paths.txt` for a small first batch. Extend it from observed technology and naming: actual API version prefixes, route words, documented filenames, directory parents, public build IDs, and known app mount paths. Do not create a huge blind Cartesian product across all hosts, extensions, versions, and backup suffixes. Sensitive configuration/backup paths belong in a separately selected exposure-discovery batch when in scope; record minimal proof rather than downloading entire archives or using exposed secrets.

For better wordlists, extract path segments, directory prefixes, basenames, and API parameter names from local inventory into distinct lists. Strip variable IDs only in a derived grouping view; preserve the original evidence. Dictionary discovery is a fallback for missing coverage, not a substitute for parsing the application's own routes. Optional ffuf can provide dedicated content fuzzing when requested; label it as outside ProjectDiscovery and keep the same scope, budget, and negative controls.

## JavaScript and source maps

1. Use Katana `-jc` as the first extraction pass. Select `-jsl` for small, relevant bundles needing deeper parsing. Record resource URL and the exact tool/version; advanced parsing can consume significant memory.
2. Download only selected in-scope JS under byte/time limits with redirect checks; hash saved bodies and retain source URL, status, content type, truncation state, and retrieval time. Never execute downloaded JS to inspect it.
3. Extract fetch/XHR calls, Axios baseURL and method configuration, GraphQL client endpoints/operation names, WebSocket addresses, route tables, REST/RPC prefixes, dynamic import chunks, URL constructors, and environment/config endpoint values. Distinguish concrete URLs from incomplete concatenations, templates, and strings with unknown base URLs. Regexes provide leads; trace call-site context before assigning methods or bases.
4. Inspect actual `sourceMappingURL` and SourceMap/X-SourceMap headers. Resolve relative maps against the JS resource, then scope-check. For a justified small batch, try the observed bundle's `.map` sibling; label this as guessed. Parse map JSON offline, verify `version`, `sources`, `sourceRoot`, `sourcesContent`, and sectioned maps. Decode embedded data maps locally.
5. Preserve exact relationships among JS URL/hash, map URL/hash, `sources[]` index, and each recovered source. A `webpack://` identifier or source path is not an HTTP URL. Do not fetch each `sources[]` entry blindly. Sanitize absolute/`..` source paths before local writes so recovered files stay within the extraction directory. Report unavailable content instead of inventing source.
6. Scope-check new API hosts separately. Classify ws/wss endpoints as metadata; the provided helper intentionally accepts only HTTP(S). Do not upgrade to WebSocket interaction automatically.

If the available `$js-enum-skill` is applicable to a request for deep source-map reconstruction or source-grounded client API analysis, use it for that branch. Ordinary recon remains self-contained without that optional skill.

## OpenAPI, Swagger, and other API descriptions

Discover descriptions through visible docs, JS configuration, response links, and the short path batch. Verify that the response parses as a real schema; a 200 SPA page at `/openapi.json` is not one.

Parse local JSON directly. For YAML, use a safe YAML parser in a `uv` virtualenv (`uv venv` then `uv pip install --python VENV/bin/python pyyaml`); never install dependencies into system Python. Do not fetch remote `$ref` targets automatically or allow arbitrary filesystem references. Resolve supplied local refs only inside the chosen input directory and bound cycles/depth.

Extract method-aware operations offline:

- **OpenAPI 3:** use operation-level, then path-level, then document-level `servers`. Resolve relative server URLs against the description URL; preserve server variables and use documented defaults only where valid. Keep unresolved templates explicit. Combine the server base path with the operation path without dropping a deployment prefix. Parameters inherit from path level and can be overridden at operation level by name+location; resolve supported refs and record unresolved refs. Distinguish `security: []` from inherited security requirements. Store requestBody/media types, response media types, operationId, tags, and deprecated status.
- **Swagger 2:** combine `schemes`, `host`, `basePath`, and operation paths; where omitted, derive only from the actual schema URL according to specification. Preserve consumes/produces, securityDefinitions/security, query/path/header/body/formData locations. Do not flatten body parameters into query strings.
- **Path templates:** keep `/users/{id}` with its declared method. Do not fabricate a real identifier or execute state-changing operations. Inventory schema servers outside scope as external leads, not active targets.
- **GraphQL:** collect endpoint URLs, schema/SDL if already accessible, client operation names, persisted-query metadata, and HTTP methods. A `/graphql` GET error or 405 does not prove the endpoint is absent. Introspection is an optional bounded read-only query when API interaction is in scope; enumeration does not authorize mutations.
- **Postman/HAR/Burp/proxy captures:** parse existing local exports for methods, base variables, parameter locations, content types, and role context; redact cookies/tokens. Do not execute a collection to enumerate it. RPC paths, gRPC-Web, WebSocket endpoints, and AsyncAPI channels remain separate typed evidence if not ordinary HTTP routes.

The helper inventory accepts normalized event rows; it is not a complete OpenAPI resolver. A quick method/path listing from local JSON is useful before full resolution:

```bash
jq -r '.paths | to_entries[] | .key as $path | .value | to_entries[]
  | select(.key | test("^(get|put|post|delete|options|head|patch|trace)$"))
  | [.key|ascii_upcase, $path] | @tsv' raw/openapi.json
```

Consult the official [OpenAPI specification](https://spec.openapis.org/oas/latest.html) and [Swagger 2 specification](https://swagger.io/specification/v2/) for resolution edge cases. Convert resolved in-scope operations to the event contract with `confidence: documented` and a schema JSON pointer. Preserve unresolvable/server-external operations separately and report the gap.

## Presence checks and soft-404 controls

For each selected origin and route family, generate two unpredictable missing paths, including an extension-matched control when checking files. Example shapes: `/__pd_missing_RANDOM`, `/api/v1/__pd_missing_RANDOM`, and `/__pd_missing_RANDOM.json`, where RANDOM comes from a locally generated UUID. Compare candidate and control responses using the same method, auth context, redirect policy, and read cap.

Compare status, Location, content type, length, title, body hash, and a short sanitized body sample. Equal hashes or the same redirect/login/SPA shell strongly suggest a catch-all. Dynamic CSRF IDs, timestamps, reflected path strings, and personalized content defeat naive exact hashing; compare structure and stable text before deciding. A truncated hash only covers the read prefix; retain the cap in evidence.

Keep these verdicts separate:

| Evidence | Inventory verdict |
| --- | --- |
| Distinct expected content/signature, or documented/observed operation with matching response | Present or supported by specific evidence; state basis |
| 401/403 unlike controls | Access-controlled candidate; no permission-bypass claim |
| 405 / Allow header unlike controls | Method-constrained candidate; preserve declared methods |
| Redirect | Redirecting candidate; record destination and scope decision |
| Same success page, login page, or body structure as random controls | Soft-404/catch-all suspected |
| 429, timeout, or unstable 5xx | Inconclusive; back off, do not mark absent |
| Archived or schema-only path, never probed | Passive/documented candidate |

Inspect small samples before applying filters across a host. Do not globally drop 403, 401, 404, or same-length responses. Raw results preserve the evidence even when derived views hide noise. Request-method checks such as HEAD/OPTIONS can supplement a selected case; do not use `httpx -x all` during routine inventory.

## Prioritization and stop

Rank distinctive API schemas, unlinked JS routes, multiple API versions, role-specific operations, file responses with expected content, and meaningful 401/403/405 routes above repeated SPA shells. Correlate routes across sources without claiming a security bug. Stop after the agreed finite passes/budget; return next useful leads and explicit coverage gaps.

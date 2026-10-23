# Identity / SSO baseline probes

Curl-level baseline for programs whose scope includes login/identity hosts (Ping/ForgeRock AM,
Azure AD, Firebase). GET-only, one request per check, the program attribution header on every
request, browser UA when the edge gates on it. Raw responses go under `manual-probes/info/` per
the engagement layout; keep the status/size TSV beside them.

## Read the identity contract out of the client bundle first

Cheapest source of the whole architecture is the app's own env/auth config object in a downloaded
bundle: it names the OIDC base URL, the CIAM base, the authorize/token/revoke paths, the redirect
URI and the **published client id**, plus CIAM-only paths worth knowing (profile, password update,
rendezvous, account-unlink). Grep the bundle for those base hosts and for `CLIENT_ID` /
`authorize` / `openid` before sending any request — it tells you which issuer to probe and which
client id to use in the authorize check, so you never guess or iterate ids. The same config object
usually carries per-environment variants (dev/qa/prod), which are config-drift leads, not findings.

## Sweep

1. From the closed-list allowlist (never from subdomain enumeration on closed-list programs),
   select hosts matching `login*`, `identity*`, `auth-*`, `id.*`, `sso*` across every environment
   (dev/qa/uat/prod).
2. GET `/.well-known/openid-configuration` on each; save per-host JSON plus a `host<TAB>status<TAB>size` TSV.
3. Diff the docs across environments. Endpoints differing only by issuer host is by design;
   differences in `response_modes_supported`, grant types, or `scopes_supported` between
   environments are config-drift leads, not findings. An advertised privileged scope or grant
   (`am-introspect-all-tokens`, `client_credentials`, `password`, `implicit`) is advertising, not a
   grant, and is not a finding on its own.

## Sequence the work so you keep your own unblock path

- **Read-only recon first, interactive auth paths last and once.** `/.well-known/*` documents and
  anonymous endpoint baselines are cheap and non-escalating; they also decide which host is really
  the target.
- **A few hits on `/signin` or the authorize endpoint can escalate a per-path edge denial into a
  deny for every path on that host**, including for a real browser on the same egress. When a human
  sign-in (registration, MFA, captcha) is part of the plan, that escalation deletes your own unblock
  path — so do not spend the auth paths early just to map them.
- **Prefer the reachable sibling.** On a shared-WAF estate the identity host the documentation names
  may be edge-denied while another in-scope host's own account system returns 200. Establish which
  host serves you before planning authenticated work against it, and record the denied ones as
  blockers rather than as targets.
- **Count browser navigations as target requests** in the engagement budget, and do not claim
  complete network accounting for a page's subresource loads.

## A block is a blocker, not a puzzle

Record it with the timeline, the exact status and the edge reference id, mark the host
do-not-repeat, and stop. Never answer an edge block with proxy or IP rotation, TLS/HTTP2 fingerprint
impersonation, repeated retries, or any attempt at the bot challenge it presents: that is evasion of
a security control, it forfeits the program's safe-harbour footing, and on a shared-egress
engagement it is self-defeating. Say plainly which planned step the block now prevents and what the
user has to do differently.

## Fingerprints

- **Ping/ForgeRock AM**: `x-forgerock-transactionid` response header, `/am/oauth2/*` endpoints,
  Ping copyright header on error pages.
- **Azure AD WS-Fed/OIDC**: 302 to `login.microsoftonline.com/<tenant-id>/...` — records the
  tenant id for the report's infrastructure section; standard behavior, not a finding.
- **Verbose JSON 404s** (`Route GET:/x not found` style): route-disclosure, informational; a
  `/health` returning empty data is a negative, not an exposure.

## Single authorize-endpoint check

One request per issuer:
`GET <authorization_endpoint>?client_id=test&redirect_uri=https://attacker.example/cb&response_type=code&scope=openid`.
Expect 400 with zero reflection — `grep -c 'attacker.example'` on the saved body must be 0.
Reflection of the redirect_uri in the error body is an open-redirect lead; an error page listing
valid client_ids is a mapping signal only. Do not iterate client_ids — that is brute forcing,
prohibited on most programs. Prefer the client id you recovered from the bundle over a placeholder,
and still send it exactly once per issuer.

## Firebase from a client bundle

`projectId` in the bundle → test both `https://<project>.firebaseio.com/.json` and
`https://<project>-default-rtdb.firebaseio.com/.json`. 401 Permission denied = rules locked
(record as a negative); 200 with data = open-read lead. An `apiKey` constant in the bundle is not
a finding — Firebase web API keys are public identifiers; demonstrate a rule bypass or stop. A
provider-native data host is not authorized by an in-scope app merely calling it: record it as a
dependency and keep testing on the app's own host.

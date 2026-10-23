# Neo subagent methods

A subagent supplies a **method** (tools, operational instructions, skills, runtime behavior), not
a worker and not an ownership grant. Availability is checked at call time; `degraded` subagents
return a `reason` plus partial capability (e.g. `github-review`, `ios-deep-security`, `slack`).

| Subagent | Status | Accepts inputs | Primary role |
|---|---|---|---|
| `recon` | available | no | Passive attack-surface + asset discovery |
| `api-security` | available | no | API inventory, authN/authZ, business logic |
| `browser` | available | **yes** | Live UI, DOM automation, computer use |
| `vulnerability-verification` | available | no | Independent proof/disproof of one candidate |
| `android-security` | available | no | APK static + Genymotion runtime |
| `ios-security` | available | no | IPA static + Appetize (non-jailbroken) |
| `sandbox` | available | no | Generic execution / files / SSH / VPN / traffic |

---

## 1. `recon` — asset discovery

*"Passive attack-surface data, asset discovery and breach-membership intelligence."* Acquire to
map assets and exposure; route authorized credential material to `pd-cloud`.

**Surfaces:** bounded recon CLI workflows via `run_command` (Subfinder, DNSX, HTTPX, TLSX,
ASNmap, Naabu, Katana, URLFinder, bounded Nuclei baselining); artifact read/write/search; the
**full** passive internet-scan set — `passive_assets`, `passive_subdomains`,
`passive_org_domains`, `passive_lookup`, `passive_pivot`, `passive_services` (incl.
`record=certificates`), `passive_changes`; breach-membership / non-secret PII lookup for email,
domain, username, phone, hash, public IP.

**Instructions:** run bounded CLI workflows; retain raw results as artifacts and filter from
disk. Passive/historical data is **not proof** a host is live or vulnerable. Route credential
material to `pd-cloud` — recon owns only membership/non-secret exposure. Memory safety: never
Katana `-jsl`; Nuclei ≤10 hosts/invocation, sequential batches, low concurrency, scoped
templates; report unscanned hosts.

**Exclusive tools:** `passive_asset_inventory`, `passive_services`, `passive_changes` exist
**only** in `recon`/`red-team`. Other workers get at most `passive_lookup`, `passive_pivot`,
`passive_subdomains`, `passive_org_domains`.

**Skills:** none recon-specific in the installed library (methodology is internal). Adjacent:
`vpn-guide`, `redteam`.

**Ownership boundary:** discovery is a **producer**. Produce the canonical live-target artifact
**once**, then pass its exact path to consumers (`browser`, `api-security`, scanners). Do not
make every consumer re-run Subfinder/HTTPX.

---

## 2. `api-security` — API testing

*"API inventory, authentication, authorization and business-logic testing."* Acquire to test an
API hypothesis or run a scoped assessment with evidence.

**Surfaces:** spec discovery (OpenAPI/Swagger) and endpoint inventory; authentication testing
(sessions, tokens, JWT, OAuth flows); authorization testing (BOLA/IDOR, function-level,
tenancy); business-logic testing; CORS analysis; `curl`/`ffuf`-class probing under sandbox.

**Instructions:** work **spec-first** — ingest the API description, then test endpoints in scope.
Prove authZ with a **controlled unequal-value** comparison (user A's token against user B's
object); a parameter name is not a bypass. Keep tests bounded and non-destructive, no data
extraction beyond proof. Preserve request/response evidence per candidate.

**Skills:** `runtime-validation`, `sqlmap-guide`, `semgrep`, plus KB indexes `JWT`, `SQLi`,
`NoSQL-Injection`, `SSRF`, `Command-Injection`, `LFI`, `SSTI`, `XXE`,
`Insecure-Deserialization`, `XSS`. **Note:** all ten of those payload collections were
unretrievable at capture time — see `references/knowledge-collections.md`.

**Ownership boundary:** api-security owns the **request/response layer**; `browser` owns live
UI/session. An authenticated track a worker establishes for itself (login, session continuity)
belongs to that worker — needing a login is not a reason for root to retain.

---

## 3. `browser` — live UI interaction

*"Browser interaction, visual evidence, DOM automation and computer use."* The **only** inputed
subagent of the seven. Model requirements: `imageToolResults: true`, `computerUse: true`.

```json
{
  "enableCaptcha":   true,        // default true
  "enableStealth":   true,        // default true
  "engine":          "chrome",    // chrome | lightpanda
  "recordSession":   true,        // default true
  "sessionRef":      "<string>",  // reuse/prepare a session
  "taskClass":       "interactive" // interactive | readonly
}
```

- **`engine`** — full interactive **Chrome** for live UI/extension work. **Lightpanda is
  read-only and not a substitute for interactive proof.**
- **`taskClass`** — `interactive` (drive UI) vs `readonly` (inspect).
- **`sessionRef`** — continue an existing login/extension/half-finished state. An existing `brs_`
  session must be inspected (openTabs + current page) **before** navigating.

**Instructions:** do **not** race a shared browser session across assignments. Read OTPs from the
**existing appropriate snapshot**, not by navigating away. Use the `browser_1password_auth`
integration for connected creds — never paste passwords. A browser claim requires **browser
evidence** (screenshot/DOM), not CLI output. Screenshots arrive via the normal multimodal
tool-result path; acquisition preserves the current model and never restarts or reroutes.

**Skills:** `desktop-computer-use` (native GUI apps via cua-driver, browser-independent).

**Ownership boundary:** a session a worker establishes for itself is that worker's state. For UI
proof of a specific candidate, pair with `vulnerability-verification` for the verdict.

---

## 4. `vulnerability-verification` — candidate verdicts

*"Independent proof or disproof of one candidate finding."* Acquire to verify a concrete
candidate without acquiring issue-filing ownership.

**Contract:** one candidate per verification. Returns a **verdict** (CONFIRMED / not-confirmed /
false-positive / inconclusive) with evidence and **`limitations`** — what could *not* be
observed. **CONFIRMED requires complete `filing_inputs`**: `reproduction_steps` and
`observed_evidence` as **string arrays**, and `poc_artifact` as a path under `/workspace/pocs/`.
Every other verdict ⇒ `filing_inputs: null`. A delegated run ending **without** the
`verification_handoff` JSON fence returned *unverified evidence* that must not be promoted.

**Instructions:** independent proof/disproof, not the producer's self-assessment. A finding whose
claimed effect was never observed belongs at **info with the gap stated**, not at a reportable
severity. Any delegated assignment whose success condition is a vulnerability verdict **must**
include this method. Verifiers record the verdict in issue metadata as
`verification: { verdict, by, evidence_ref, limitations }`.

**Ownership:** the verifier **owns the final reconciled findings canvas**. Root may inspect but
must not publish a competing canvas while verification is pending, nor self-promote.

**Skills:** `exploitability-verification` (reachability, sink tracing, guard effectiveness, FP
patterns), `runtime-validation`, `sharp-edges`, `variant-analysis`.

**Related:** `xss` (context-specific XSS dev/demo — verdicts still route through
`vulnerability-verification`); `vulnerability-triage` (upstream intake/source/dup checks/repro).

---

## 5. `android-security`

*"Android APK static analysis and Genymotion runtime testing."*

**Surfaces:** static APK/AAB/XAPK/APKS analysis (manifest, permissions, exported components,
secrets); runtime testing on an authorized **Genymotion** emulator (ADB/Frida).

**Instructions:** **route by the thing being tested, not vendor words** — APK/AAB/Play Store ⇒
Android. `browser` cannot drive a phone app; `sandbox` may unpack a binary but does not replace
the mobile method. **Missing device-cloud creds are Neo infrastructure, never a user credential
request** — continue available static plus first-party link/OAuth/token/backend-API work and
preserve the blocker. If the binary cannot be acquired, keep the blocker and continue
App/Universal Links, OAuth/token and backend API assessment (shared surface ≉ out of scope).

**Skills:** `android-security-guide` (IPC, data security, WebView, crypto, deeplinks; ADB + Frida
hooks, static patterns, remediation), `android-deeplink-security` (deep/App Link exploitation,
scheme hijacking, intent redirection, parser differentials, PendingIntent mutability, task
hijacking, real CVEs), `android-static-patching` (patch + re-sign rather than hook).

**Helpers:** `ghidra` (native `.so` decompilation), `sandbox`.

---

## 6. `ios-security`

*"iOS IPA static analysis and non-jailbroken Appetize testing."*

**Surfaces:** static IPA analysis (Info.plist, entitlements, embedded frameworks,
strings/secrets, ATS config, URL schemes); runtime on **Appetize** (non-jailbroken).

**Instructions:** route by artifact — IPA/App Store ⇒ iOS. Do not substitute `browser` or generic
`sandbox` for a phone runtime. Use `ios-deep-security` when jailbreak, Frida, Keychain, or
filesystem instrumentation is essential — currently **degraded** (`VPHONE_DAEMON_URL` absent);
static deep-iOS analysis remains available. Continue static plus first-party link/OAuth/backend
work; do not ask the user for Neo's device credentials.

**Skills:** `ios-security-guide` (IPA analysis, binary inspection, keychain, transport security,
URL schemes, secrets scanning), `ios-security-index`, `mobile-advanced-techniques` (Frida +
Appetize, anti-Frida bypass, native libs, whitebox crypto DFA, PIN brute-force, traffic
pipeline).

**Helpers:** `ios-deep-security` (jailbroken vPhone runtime; degraded), `ghidra` (Mach-O),
`sandbox`.

---

## 7. `sandbox` — generic execution

*"Sandbox commands, files, SSH/VPN, traffic and security tools."*

**Tools:**
1. **`run_command`** — shell. Optional `sandbox` selector: omit/`true` = daemon default confine;
   `false`/`"host"` = host unconfined; `"native"` = Seatbelt/bwrap; `"docker"` = docker tool
   image (BYOS).
2. **`execute_script`** — full Python with streaming output; prefer for substantial logic.
3. **`read_file`** — line-numbered, cursor-paginated; images via vision model.
4. **`list_files`** — `ls -la`-style with ignore globs.
5. **`edit_file`** — exact string replacement, single or multi-edit, atomic.
6. **`write_file`** — create/overwrite; persists to bucket on cloud, durable workspace on BYOS.
7. **`grep_or_glob`** — ripgrep content search + glob; regex, context, multiline.
8. **`ssh_configure`** / **`ssh_exec`** — named connections, generated-key or password auth
   (encrypted at rest); **never** silently persist chat credentials.
9. **`network_traffic_sitemap` / `_search` / `_get` / `_replay`** — captured HTTP across
   browser/CLI/script/replay; current task by default, `all_task:true` for targeted lookup.

**Bundled toolchain:** ProjectDiscovery suite (nuclei, subfinder, httpx, dnsx, naabu, katana,
cdncheck, chaos-client, uncover, vulnx, mapcidr, tlsx, notify, asnmap, urlfinder, pdtm);
gitleaks; `gh` as an **App installation** token (repo-scoped, auto-minted from `OWNER/REPO` or
cwd origin — user-scoped endpoints fail, it is not a user); ffuf, masscan, curl, dig, nslookup;
red-team suite when installed (impacket, netexec/nxc, bloodhound.py, pypykatz, hydra, john,
kerbrute, chisel, responder).

**Instructions:** inspect supplied files/state **before** broad commands; choose the **smallest**
command that tests the hypothesis.

Tool selection is **mandatory**, not advisory:
- Content discovery / directory brute-force ⇒ **ffuf**, not curl loops. Wordlists from
  `/workspace/seclists` (clone if absent).
- Credible SQLi candidate ⇒ **sqlmap**, preserving the original request. A detection message is
  not impact proof and not permission to extract.
- **curl** is for surgical single requests, not bulk testing or discovery.

**Temporary probes:** one non-interactive `run_command` shell per listener+client; `cd` first,
redirect background stdout/stderr, capture `$!`, set an `EXIT` trap to kill+wait, bounded
readiness check. No `kill %1`. Clean up owned listeners/tunnels/mounts.

**Security-baseline fallback:** a zero-result Nuclei run (especially behind WAF/CDN) is **not** a
clean baseline — run bounded manual probes into `manual-probes/` (CORS, openapi, info paths,
headers, SSH banner) and record positives, negatives and blockers.

**Evidence packet:** exact command/request (secret refs, not secrets), control + mutated output,
exit status, timestamps, affected path, artifact paths — bounded in context, raw on disk. Record
`[TRIED_FAILED]` and `[NEEDS_RETRY]` so later work does not repeat failures.

**Skills:** `vpn-guide` (WireGuard/OpenVPN/OpenConnect/Tailscale/IPsec/Twingate/NetBird/
Cloudflare WARP), `nuclei-templates`, `sqlmap-guide`, `semgrep`, `libfuzzer`,
`security-findings`, `docx`/`pdf`, `h1-*`, `github-ops`.

**Ownership boundary:** sandbox is **generic execution**, never a substitute for a specialized
method. Adding it to one worker does not create parallelism. It does not replace
`recon`/`api-security`/`browser`/mobile methods, and it is not a verifier verdict.

---

## Skill → subagent map

| Skill | Primary subagent |
|---|---|
| `android-security-guide`, `android-deeplink-security`, `android-static-patching` | android-security |
| `ios-security-guide`, `ios-security-index` | ios-security |
| `mobile-advanced-techniques` | ios-security / ios-deep-security |
| `desktop-computer-use` | browser |
| `code-review-coverage`, `differential-review`, `exploitability-verification`, `sharp-edges`, `variant-analysis` | vulnerability-verification / review |
| `runtime-validation`, `sqlmap-guide`, `semgrep` | api-security / sandbox |
| `nuclei-templates`, `libfuzzer` | sandbox |
| `vpn-guide` | sandbox |
| `redteam` | red-team |
| `security-findings`, `docx`, `pdf` | reporting (any) |
| `github-ops`, `h1-api`, `h1-setup`, `h1-triage` | sandbox / integrations |

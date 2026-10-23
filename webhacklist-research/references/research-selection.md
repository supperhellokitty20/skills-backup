# Research selection contract

Use the bibliography to identify mechanisms, not to manufacture payloads from article titles. Search broadly enough to include old techniques and unrelated-looking implementations of the same boundary failure.

## Search families

- Protocol and intermediary disagreements: `request-smuggling`, `desync`, `parser-differential`, `http2`, `http3`, `reverse-proxy`.
- Cache boundaries: `cache-poisoning`, `cache-deception`, `cdn`, `url-parsing`, `encoding`.
- Browser trust: `xss`, `mutation-xss`, `dom-clobbering`, `sanitizer-bypass`, `same-origin-policy`, `postmessage`, `xsleak`.
- Identity and authorization: `oauth`, `openid`, `saml`, `jwt`, `sso`, `webauthn`, `passkeys`, `auth-bypass`, `idor`.
- State and concurrency: `race-condition`, `toctou`, `session-fixation`, `abuse-of-functionality`.
- Backend injection and object handling: `ssti`, `sqli`, `nosqli`, `deserialization`, `prototype-pollution`, `class-pollution`, `gadget-chain`.
- Fetch and filesystem boundaries: `ssrf`, `dns-rebinding`, `path-traversal`, `file-upload`, `file-read`, `file-write`.
- Delivery and build trust: `supply-chain`, `dependency-confusion`, `github-actions`, `ci-cd`.
- AI-connected applications: `prompt-injection`, `ai-agent`, `llm`, `mcp`, `tool-use`, `rag`.

These are search directions derived from the source vocabulary, not assertions that an application is vulnerable. Exact tags can be inspected in `references/tag-vocabulary.json`; aliases apply to query terms only and never rewrite preserved identifiers.

## Mechanism-level technique cards

Distill one reusable card per mechanism, linking all relevant papers, slides, repositories and related research. Keep card identity separate from annual bibliography record IDs so compiling a method never deduplicates away legitimate list records.

Each card starts with a stable card ID, exact source/record IDs and a declared tier: `indexed`, `reviewed` or `reproduced`. Preserve author attribution, original URLs and the provenance of material actually reviewed. Attach uncertainty explicitly when prerequisites, publication claims or attribution remain unresolved. Never promote a source-derived digest or successful metadata lookup to a reviewed recipe.

## Required extraction after reading a selected primary source

Record:
1. Original URL, author and publication date, with archive provenance if applicable.
2. Affected component/version and deployment assumptions.
3. Entry point and the minimum attacker capability.
4. The trust boundary or invariant that fails.
5. The exact mechanism, distinguishing control-plane metadata from runtime behavior.
6. A bounded test and negative control appropriate to the authorized scope.
7. Observable security impact, not just an error or unusual response.
8. Patch, mitigation, or conditions that make the technique inapplicable.
9. Required procedural skills, established tools, finite budget and stopping conditions.
10. Review evidence and, separately, any lab reproduction artifacts; do not infer reproduction from publication or tool exit status.

## Work-unit handoff

Pass the worker the exact surface/observation revision, applicable card/source IDs, procedural skill identifiers, scope artifact and hypothesis. Require it to return attempt provenance, contained evidence references, disposition and unresolved prerequisites. Give an independent verifier the evidence when the requested outcome is a vulnerability verdict; an attempted test or article read is not confirmation.

Persist this contract outside the conversation so a resumed or compacted run can recover pending work without re-scanning the entire bibliography. Treat changed observations or evidence as a reason to reassess applicability, not as permission to keep using an old plan. Capture missing research/card coverage honestly rather than manufacturing a recipe to satisfy the handoff.

Use `show <id>` to collect all same-work artifacts and distinguish them from related prior art or link-only tools. Read a paper/slide deck when a blog omits constraints. Do not replace a missing document with a guessed description. A 2026 candidate's inclusion is only a lead, and no ranking or novelty claim is warranted without its own evidence.

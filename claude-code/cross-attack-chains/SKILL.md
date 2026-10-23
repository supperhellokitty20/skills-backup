---
name: cross-attack-chains
description: Use when two or more verified findings may combine into a higher-impact authorized attack path.
version: 2.0.0
license: MIT
platforms: [linux, macos]
compatibility: Requires evidence from the owning validation skills
tags: [chains, attack-path, validation, reporting]
category: chains
related_skills:
  - attack-patterns-reference
  - evidence-hygiene
  - report-writing
  - triage-validation
  - wordpress-full-compromise
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/exploit-chains-template.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# Cross-Attack Chains

An attack chain is a sequence of verified security behaviors in which each step
provides a prerequisite for the next. Several findings on the same target do
not form a chain unless the dependency between them is demonstrated.

## When to Use

- Two or more validated findings affect the same trust boundary.
- One finding exposes an identity, token, route, host, or capability needed by
  another.
- A report needs to distinguish standalone impact from compound impact.
- The next chain step cannot be tested safely and must be labeled inferred.

## Prerequisites

- Captured evidence and negative controls for every component finding.
- Current authorization for the compound test and any increased side effects.
- Approved identities, synthetic records, callbacks, and cleanup procedure.
- A clear stop condition for sensitive data, availability, or scope changes.

## How to Run

Create a chain record beneath the target output directory:

```bash
TARGET_ID="example-test"
OUTPUT_DIR="${OUTPUT_DIR:-./output}"
CHAIN_DIR="$OUTPUT_DIR/$TARGET_ID/chains"

mkdir -p "$CHAIN_DIR"
touch "$CHAIN_DIR/EXPLOIT_CHAINS.md"
```

Use evidence states consistently:

| State | Meaning |
|---|---|
| Observed | Present in captured output |
| Confirmed | Security impact reproduced with a control |
| Inferred | Plausible dependency that has not been tested |
| Not tested | Excluded by scope, safety, or missing prerequisites |

## Procedure

### 1. Normalize Component Findings

For each component, record:

- expected and observed behavior;
- target, identity, and timestamp;
- positive evidence and negative control;
- side effects and cleanup;
- demonstrated impact;
- assumptions and testing limits.

Discard scanner labels and version-only leads that have not passed their owning
skill's verification.

### 2. Draw the Dependency

```text
Finding A
  output: approved user identifier
  enables: object lookup in Finding B

Finding B
  output: unauthorized synthetic object read
  enables: none
```

If A and B are merely co-located, document them separately.

### 3. Test the Transition

The transition is the core of the chain. Demonstrate that the exact output from
one step is accepted by the next step under the same authorized conditions.

Examples:

| Candidate path | Transition to prove |
|---|---|
| Source map to hidden API | Extracted base URL resolves to the tested API |
| User enumeration to IDOR | Enumerated identifier addresses another approved identity's object |
| CORS to protected-data read | Approved browser session returns non-public response to controlled origin |
| SSRF to internal service | Controlled callback or response identifies the internal service |
| Exposed credential to repository access | Scoped credential is valid for an approved test resource |

Do not use real user data, broad credential testing, or destructive operations
to bridge a missing transition.

### 4. Recalculate Compound Impact

State:

1. what each component demonstrates alone;
2. what additional capability the verified transition creates;
3. which final impact was reproduced;
4. which downstream consequences remain inferred.

The chain severity cannot exceed the evidence. A theoretical final step does
not become confirmed because earlier steps worked.

### 5. Preserve Cleanup and Limits

Record removal of synthetic users, objects, uploads, callbacks, and temporary
tokens. If testing stops before the final step, explain why and preserve the
last confirmed state.

## Pitfalls

- Co-occurrence is not dependency.
- A username is not a credential.
- A valid credential does not imply access to every service.
- File upload does not imply code execution.
- Internal reachability does not imply control of an internal service.
- Several low-confidence steps compound uncertainty, not confidence.
- Compound testing may need authorization beyond the individual findings.

## Verification

- Every component passed its owning skill's verification.
- Every arrow has evidence that the preceding output enables the next input.
- Negative controls distinguish the path from public or expected behavior.
- State-changing steps use synthetic resources and include cleanup.
- Inferred and not-tested steps remain visibly labeled.
- The final report separates demonstrated impact from plausible consequences.

## MANDATORY ON INVOCATION — PROTOCOL RESTATMENT (END OF FILE)

You have reached the end of this SKILL.md. The invocation protocol below is identical to the one at the top of this file. If you are reading this, the full skill context is loaded — confirm the checklist.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/exploit-chains-template.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

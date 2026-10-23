---
name: wordpress-full-compromise
description: Use when verified WordPress findings may combine into an authorized path to administrative or server control.
version: 2.0.0
license: MIT
platforms: [linux, macos]
compatibility: Requires curl, a browser, approved test identities, and WordPress component evidence
tags: [chains, wordpress, validation, attack-path]
category: chains
related_skills:
  - cross-attack-chains
  - hunt-wordpress
  - triage-validation
  - wordpress-cors-xmlrpc-rce-chain
  - wordpress-plugin-hunt
  - xmlrpc-exploitation
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/mailinator-reset-workflow.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# WordPress Compromise Path Analysis

Use this skill to determine whether verified WordPress primitives actually
compose into administrative control or benign code-execution proof. It is a
chain gate, not a checklist for forcing escalation after a prerequisite fails.

## When to Use

- A plugin vulnerability has exact version and route evidence.
- An approved identity may have an unexpected WordPress capability.
- An upload or configuration write could reach executable handling.
- CORS, XML-RPC, staging, or source exposure may supply a missing prerequisite.

## Prerequisites

- Explicit authorization for registration, authentication, upload, write, and
  execution testing.
- An approved synthetic account and disposable content.
- Exact WordPress, plugin, theme, and hosting behavior.
- A benign marker for any execution test.
- Cleanup and stop conditions.

## How to Run

Build a prerequisite table:

```text
Step                         State       Required evidence
Component vulnerability      observed    exact version and affected operation
Authorized identity          confirmed   approved account and current role
Write or upload capability   unverified  synthetic artifact accepted
Executable handling          unverified  benign marker executed
Administrative control       not tested  approved admin-only action
Cleanup                      planned     artifact and account removal
```

Do not proceed past an unverified prerequisite.

## Procedure

### 1. Confirm the Component

Use `hunt-wordpress` and `wordpress-plugin-hunt` to establish:

- component identity from more than one signal;
- exact version or commit;
- vulnerable route or handler;
- authentication and role prerequisite;
- affected configuration and file type.

A public readme or stale asset is not sufficient by itself.

### 2. Confirm Identity and Capability

Use only approved test identities. Record the current role and the exact
capability checked by the operation. Subscriber, customer, author, editor, and
administrator roles are not interchangeable.

Do not bridge missing authorization with password spraying, credential
stuffing, or unrelated leaked credentials.

### 3. Validate State Change With Synthetic Data

Use a uniquely named synthetic post, object, or inert file. Record:

- request and identity;
- response and resulting object ID;
- location and content;
- expected authorization policy;
- cleanup result.

If the object cannot be removed safely, stop before creation.

### 4. Separate Upload From Execution

An accepted upload proves only an upload boundary. Establish executable
handling separately:

- server maps the stored extension to an interpreter;
- MIME and extension validation permit the tested type;
- storage path is web reachable;
- plugin processing does not rename or sanitize the file;
- a benign marker can execute in the approved environment.

Never deploy a command shell as a generic proof.

### 5. Evaluate Administrative Impact

Administrative control requires an approved admin-only effect, such as reading
a synthetic private setting or changing a disposable configuration value and
restoring it. User enumeration, REST metadata, or an available login page does
not establish account takeover.

### 6. Assemble the Path

Use `cross-attack-chains` to connect only confirmed transitions. Use
`wordpress-cors-xmlrpc-rce-chain` when CORS and XML-RPC are actual
prerequisites, not merely additional findings on the same installation.

## Pitfalls

- Open registration normally creates a low-privilege role.
- XML-RPC method presence is not authorization to call that method.
- Enabled PHP process functions do not create an upload primitive.
- Plugin version evidence can be stale or backported.
- A staging site may have a separate database and no production trust path.
- Failure of a prerequisite is evidence that the proposed chain stops there.

## Verification

- Component identity, version, route, and prerequisites are confirmed.
- The approved identity has the exact required capability.
- State changes use synthetic resources and are reversed.
- Upload and execution are demonstrated as separate steps.
- Administrative impact uses an approved disposable action.
- Every missing step remains inferred or not tested.

## MANDATORY ON INVOCATION — PROTOCOL RESTATMENT (END OF FILE)

You have reached the end of this SKILL.md. The invocation protocol below is identical to the one at the top of this file. If you are reading this, the full skill context is loaded — confirm the checklist.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/mailinator-reset-workflow.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

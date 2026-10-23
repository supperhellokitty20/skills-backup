---
name: arkcli-iam
version: 1.0.0
description: "Resolve a BytePlus IAM UserID from a username prefix with `arkcli iam userid`, or return the current identity UserID when no username is supplied. Trigger for UserID lookup, employee username resolution, and plan seat-assignment prerequisites. Route directly here instead of scanning IAM users through Raw API Explorer."
metadata:
  requires:
    bins: ["arkcli"]
  cliHelp: "arkcli iam userid --help"
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/arkcli-iam-userid.md`, `references/evals.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# arkcli IAM identity lookup

**CRITICAL — Before starting, you MUST read [`../arkcli-shared/SKILL.md`](../arkcli-shared/SKILL.md) for authentication, profile, output, and safety rules.**
**CRITICAL — Before executing `iam userid`, you MUST read [`references/arkcli-iam-userid.md`](references/arkcli-iam-userid.md).**

## Routing contract

- When the user wants to resolve a UserID from an employee username or username prefix, run `arkcli iam userid --username <prefix> --format json`.
- When the user asks for the current logged-in identity UserID, run `arkcli iam userid --format json` without `--username`.
- Do not route this intent to Raw API Explorer, `iam.list_users`, account-wide user enumeration, or local scanning of the entire user directory.
- If `iam userid` returns an error, preserve that error and stop. Do not widen the query scope as a fallback.

## Applicable scenarios

- Resolve one or more username prefixes to exact `user_id` and `user_name` pairs.
- Obtain the current identity UserID from the active SSO profile.
- Prepare the exact UserID required by `arkcli plans team seat-assign`.

## Anti-trigger signals

- Listing, binding, assigning, or rotating plan seats belongs to [`arkcli-plans`](../arkcli-plans/SKILL.md). This Skill only resolves identity fields.
- Authentication or profile failures belong to [`arkcli-auth`](../arkcli-auth/SKILL.md) or [`arkcli-profile`](../arkcli-profile/SKILL.md).
- A request for arbitrary raw IAM APIs belongs to [`arkcli-api-explorer`](../arkcli-api-explorer/SKILL.md), but UserID lookup does not.

## Command overview

| Command | Purpose |
|---|---|
| `arkcli iam userid --username <prefix> --format json` | Resolve username prefixes through the bounded product command |
| `arkcli iam userid --format json` | Return the current identity UserID |

## References

- [`references/arkcli-iam-userid.md`](references/arkcli-iam-userid.md)
- [arkcli-plans](../arkcli-plans/SKILL.md) -- Consume the resolved UserID for seat assignment
- [arkcli-shared](../arkcli-shared/SKILL.md) -- Shared authentication and output rules
---
name: arkcli-profile
version: 0.2.1
description: "Manage product-isolated BytePlus profiles: inspect and select profiles, create supported profile types, re-select project scope, synchronize API keys and Coding Plan models, and choose default resources."
metadata:
  requires:
    bins: ["arkcli"]
  cliHelp: "arkcli profile --help"
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/arkcli-profile-create.md`, `references/arkcli-profile-keys.md`, `references/arkcli-profile-set-default.md`, `references/evals.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# BytePlus profiles

Read [`../arkcli-shared/SKILL.md`](../arkcli-shared/SKILL.md) before using this
Skill.
The entire profile domain manages local identity state and rejects
`--dry-run`. Use `auth status/whoami` for ordinary admission and `resources`
for resource/default discovery. Reserve `profile show/list/keys list` for an
explicit Profile task: explain first that these commands can synchronize
remote keys and write back the local key inventory or default key. Obtain
explicit confirmation for mutations.

A profile is a local BytePlus configuration slice that binds a profile type,
the fixed BytePlus Region, project scope, identity, API keys, and default
resources. Selecting a profile does not switch product or tenant.

## Distinguish inspection from management

- A read-only check of identity, default-resource visibility or credential compatibility is not Profile management, even when the user supplies a profile name or type. Load the Auth and Resources Skills and hand off to them. Missing information does not authorize `profile show/list/keys list`.
- Before invoking `show/list/keys list` for an explicit Profile management task, send user-visible text stating both effects: online synchronization with the remote API key source, and possible writeback to local key inventory or the default key. For example: "This management query may synchronize remote API keys online and write back local key inventory or the default key."
- Saying "I will explain" is only a plan. Tool descriptions, private reasoning and the final answer after execution do not replace this disclosure. Do not describe these management queries as purely read-only or claim that local keys were unchanged without evidence.

## Supported profile types

| Type | Purpose |
|---|---|
| `platform` | Pay-as-you-go Platform Endpoint and inference usage. |
| `coding-plan` | Personal Coding Plan usage. |
| `coding-plan-team` | Coding Plan Team usage through an assigned seat. |

Do not suggest another profile type. The BytePlus Region is fixed to
`ap-southeast-1`.

## When To Trigger

- listing profiles or identifying the active profile;
- switching the local default profile;
- creating or deleting a supported BytePlus profile;
- changing the active project scope;
- synchronizing or selecting profile API keys;
- inspecting Coding Plan model defaults;
- selecting a default text, image, or video resource.

## When NOT To Trigger

Use [`../arkcli-auth/SKILL.md`](../arkcli-auth/SKILL.md) for login and credential
health. Use [`../arkcli-resources/SKILL.md`](../arkcli-resources/SKILL.md) to
list resources currently visible to a profile.
Do not use profile mutation as a fallback for a missing resource, permission
error, or unsupported capability.

## Profile resolution

The effective profile is selected in this order:

```text
--profile
  > ARK_PROFILE
  > config default_profile
  > first valid platform profile
  > default sentinel
```

For commands that accept `--profile <name>`, Ark CLI uses that profile's
identity and configuration for the operation. It does not merely change the
name of the output target.

## Project scope

BytePlus can operate in a named project or across the account:

- `All account resources` is the user-facing account-wide option;
- account-wide profile names use the `accountwide` segment, for example
  `platform_ap-southeast-1_accountwide`;
- the account-wide internal sentinel is an implementation detail and must not
  be copied into commands or output explanations.

First login selects account-wide by default. Manual `profile create` keeps its
documented `default` project fallback unless the user selects or supplies
another project.

`arkcli profile project [<project-name>]` changes project scope without
reauthenticating, but it is not a simple field update:

```text
existing platform profile
  |
  +-- delete
  |
  +-- create a fresh platform profile for the selected project
  |
  +-- refresh Coding Plan subscription and team-seat profiles
        |
        +-- update or create profiles available in the new project
        +-- remove profiles not available in the new project
```

The command requires confirmation and does not support `--dry-run`. Without a
positional project name, it loads the selectable BytePlus projects and includes
`All account resources`.

## Command map

| Command | Behavior |
|---|---|
| `arkcli profile list` | List local profiles and identify the default. |
| `arkcli profile show [profile]` | Show one profile with masked secrets and the derived data-plane URL. |
| `arkcli profile use [profile]` | Change the local default profile. |
| `arkcli profile create` | Create `platform`, `coding-plan`, or `coding-plan-team`. |
| `arkcli profile delete <profile>` | Delete a local profile; use `--yes` only after confirmation. |
| `arkcli profile rename <profile> --to <display-name>` | Change only the display label, not the internal profile key. |
| `arkcli profile project [<project-name>]` | Replace the Platform project slice and refresh Coding Plan profiles. |
| `arkcli profile keys list|use|refresh` | Inspect, select, or synchronize the profile-specific ordinary or team-seat API key source; an empty refresh fails without clearing local keys. |
| `arkcli profile models list|refresh` | Inspect or refresh Coding Plan model defaults. |
| `arkcli profile set-default <id>` | Save a default resource for one modality. |

## Guard Checklist

1. For ordinary admission, do not inspect or change Profile state. Use:

   ```bash
   arkcli auth status --format json
   arkcli auth whoami --format json
   arkcli resources list --modality text --format json
   ```

2. When the user explicitly asks to inspect or manage Profile state, explain
   the possible key synchronization and writeback before running:

   ```bash
   arkcli profile show --format json
   arkcli profile list --format json
   ```

3. Before `create`, `delete`, or `project`, state the exact local configuration
   impact and obtain confirmation.
4. Before `use`, `rename`, `keys use`, `keys refresh`, `models refresh`, or
   `set-default`, state the target profile.
5. Use `--plan-tier lite|pro` only for a personal `coding-plan` profile when
   the user explicitly needs to override subscription detection.
6. Do not edit `~/.arkcli-bp/` or `config.yaml` directly.
7. Treat API-key sources as profile-specific: `platform` and personal
   `coding-plan` use the ordinary pool; `coding-plan-team` uses a Running
   seat's key. `auth apikey` only selects from the ordinary pool and cannot
   repair a team profile.

## References

- Create a profile:
  [`references/arkcli-profile-create.md`](references/arkcli-profile-create.md)
- Manage API keys:
  [`references/arkcli-profile-keys.md`](references/arkcli-profile-keys.md)
- Select a default resource:
  [`references/arkcli-profile-set-default.md`](references/arkcli-profile-set-default.md)
- Maintainer regression cases:
  [`references/evals.md`](references/evals.md)

Never change product, account, Region, or tenant as a fallback for a missing
profile or resource.

## MANDATORY ON INVOCATION — PROTOCOL RESTATMENT (END OF FILE)

You have reached the end of this SKILL.md. The invocation protocol below is identical to the one at the top of this file. If you are reading this, the full skill context is loaded — confirm the checklist.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/arkcli-profile-create.md`, `references/arkcli-profile-keys.md`, `references/arkcli-profile-set-default.md`, `references/evals.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

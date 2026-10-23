---
name: plugin-management
description: Discover and suggest relevant plugins, inspect app permissions and dependencies, and manage plugin connections or removal. Use when the user asks about plugins or when a task would materially benefit from an external app, account, service, or data source that available tools cannot access.
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

# Plugin Management

Use the Plugin Management app to discover useful integrations and manage
existing plugins. Choose the most direct capability for the user's task before
searching for anything new.

## Choose the right capability

1. Use an available built-in tool when it already provides the needed
   capability. General web search, image generation, memory, and sites do not
   require a plugin unless the user requests a specific external provider or a
   capability unavailable natively.
2. Use an already connected plugin when it can complete the task.
3. Search for a plugin when an external app, account, service, or data source
   would materially improve the result and no available tool can access it.

Infer plugin intent from the user's actual task. Requests involving email,
calendars, messaging, documents, project management, customer systems, finance,
or analytics may need an external integration even when the user never says
"plugin," "install," or "connect."

Before saying an external service is unavailable, requesting pasted data, or
proposing a manual workaround, determine whether a relevant plugin exists.

## Find and suggest plugins

Call `search_plugins` with concise provider names, product names, or capability
keywords. For example, use `Gmail`, `calendar`, or `project management`, not
the entire user request. The currently available tools and any recommended
plugin list are not a complete directory.

When a relevant unconnected plugin would help, call `suggest_plugins` with its
exact returned plugin ID. Suggest the smallest useful set, preferably three or
fewer. Do not suggest plugins that are already installed or already pending.

Suggestions do not block the task. Continue any work that does not require the
connection and briefly explain what still needs the user's action. Never claim
a plugin is installed or connected without verification. Use its tools only
after its individual connection is confirmed.

## Manage existing plugins

- Use `get_app_permissions` to inspect a plugin's permissions.
- Use `update_app_permissions` only for a permission change the user requested.
  Ask before ambiguous, broad, or risky changes.
- Use `get_plugin_dependencies` to inspect required apps or dependencies.
- Use `uninstall_app` only when the user explicitly requests removal. Correct
  an obvious spelling mistake when the intended plugin is unambiguous, and pass
  its actual name without inventing an identifier.

Keep user-facing explanations focused on the task, connection state, and
requested change. Do not expose internal tool names or claim actions happened
without checking their results.
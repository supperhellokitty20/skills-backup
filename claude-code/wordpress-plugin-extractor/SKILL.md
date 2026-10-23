---
name: wordpress-plugin-extractor
description: Extract source code for WordPress plugins by creating a temporary Docker WordPress install, installing a plugin from a WordPress.org slug, local zip, or plugin zip URL, and copying the resulting wp-content/plugins directory out. Use when the user asks to extract, inspect, unpack, retrieve, or get the source code of a WordPress plugin using Docker or an isolated WordPress install.
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `agents/openai.yaml`, `scripts/extract-wordpress-plugin.sh` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# WordPress Plugin Extractor

## Workflow

Use `scripts/extract-wordpress-plugin.sh` for extraction tasks. It creates an isolated Docker Compose project, waits for WordPress setup, installs WordPress automatically with WP-CLI, installs the requested plugin, copies the plugin directory to the requested output folder, and cleans up the Docker resources.

Prefer this command shape:

```bash
/path/to/skill/scripts/extract-wordpress-plugin.sh --plugin PLUGIN_OR_ZIP --output ./extracted-wordpress-plugins
```

Input can be:

- A WordPress.org plugin slug, such as `woocommerce`
- A local plugin zip path, such as `~/Downloads/plugin.zip`
- A direct zip URL accepted by `wp plugin install`

Pass `--plugin-dir DIRNAME` when the installed plugin folder cannot be reliably inferred from the slug or zip filename. Pass `--activate` only when activation is explicitly needed or requested; source extraction usually does not require activation.

If the destination plugin directory already exists, either choose a new output directory or pass `--force` to replace that destination.

## Requirements

Ensure Docker with Compose v2 is available. Do not use this workflow to bypass licensing or access controls; only extract plugins the user is authorized to inspect.

## Output

Report the extracted plugin path printed by the script. If extraction fails, summarize the failing command/output and the likely required fix, such as starting Docker, using a valid plugin slug, or providing `--plugin-dir`.
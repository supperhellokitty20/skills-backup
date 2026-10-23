---
name: hermes-agent
description: "Use, configure, theme, extend, and orchestrate Hermes Agent."
version: 3.2.0
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, setup, configuration, multi-agent, spawning, cli, gateway, bots, bot-mode, features, themes, skins, desktop-plugins, tui-widgets, petdex, development]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [claude-code, codex, opencode]
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/background-systems.md`, `references/cli-reference.md`, `references/configuration.md`, `references/contributor-guide.md`, `references/delegate-task-concurrency-diagnosis.md`, `references/desktop-plugins.md`, `references/messaging-platforms.md`, `references/native-mcp.md`, `references/petdex.md`, `references/portal-auth-for-third-party-apps.md`, `references/project-context-files.md`, `references/providers-and-models.md`, `references/security-privacy.md`, `references/skill-library-auditing.md`, `references/slash-commands.md`, `references/themes.md`, `references/troubleshooting.md`, `references/tui-widgets.md`, `references/webhooks.md`, `references/windows-quirks.md`, `templates/clock.mjs`, `templates/plugin.js`, `templates/skin.yaml` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# Hermes Agent

Hermes Agent is an open-source AI agent framework by Nous Research that runs in your terminal, a native desktop app, messaging platforms, and IDEs. It's in the same category as Claude Code (Anthropic), Codex (OpenAI), and OpenClaw — autonomous coding and task-execution agents that use tool calling to interact with your system. Hermes works with any LLM provider (OpenRouter, Anthropic, OpenAI, Google, DeepSeek, xAI, local models, and 20+ others) and runs on Linux, macOS, Windows, and WSL.

What makes Hermes different:

- **Self-improving through skills** — Hermes learns from experience by saving reusable procedures as skills that load into future sessions.
- **Persistent memory across sessions** — remembers who you are, your preferences, environment details, and lessons learned. Pluggable memory backends.
- **Multi-platform gateway** — the same agent runs on Telegram, Discord, Slack, WhatsApp, iMessage, Signal, Matrix, Teams, Email, and a dozen more platforms with full tool access, not just chat.
- **Many surfaces** — the same agent core drives the CLI, the Ink TUI, a native Electron desktop app, a web dashboard, and an ACP server for IDEs (VS Code / Zed / JetBrains).
- **Provider-agnostic** — swap models and providers mid-workflow; credential pools rotate across multiple API keys automatically.
- **Profiles** — run multiple independent Hermes instances with isolated configs, sessions, skills, and memory.
- **Extensible & themeable** — plugins, MCP servers, custom tools, webhook triggers, cron scheduling, skins that theme every surface, desktop UI plugins, TUI widgets, and pet mascots.

**This skill is a hub.** The body covers identity, quick start, spawning/orchestration, and hard invariants. Everything else lives in reference files — **load the matching reference (below) before answering**; do not answer detail questions from the body alone.

**Docs:** https://hermes-agent.nousresearch.com/docs/

## Scope & Verification

This skill is a concise operating guide, not the complete source of truth for every Hermes feature. If a Hermes feature, command, or setting is not mentioned here or in a reference, do not treat that absence as evidence that it does not exist. Check the live repository and official docs before giving a negative answer.

Good verification targets, cheapest first:

- **Every shipped feature, one line each: https://hermes-agent.nousresearch.com/docs/llms.txt.** Start here for any "can Hermes do X?" or "how do I do X?" — it indexes the entire documentation set with a link to the page that answers. It is generated from the docs tree on every build, so it is never behind the product. Fetch it with `web_extract`, or `curl -s https://hermes-agent.nousresearch.com/docs/llms.txt` when web tools are off. The whole documentation set in one file is at `/docs/llms-full.txt`.
- CLI commands: `hermes --help`, `hermes <command> --help`, and `hermes_cli/main.py`
- Source tree: https://github.com/NousResearch/hermes-agent
- **The install tree's own docs, when the website will not fetch** — a git install ships `$HERMES_HOME/hermes-agent/website/docs/` (plus a `zh-Hans` mirror). Version-matched to the installed build and offline; prefer it over the site for "what exactly does this build do". Note `?format=md` is not honoured by plain `curl` — you get the rendered HTML shell, not markdown.

Never answer "Hermes can't do that" from memory. Hermes ships far more than this skill body describes, and the index exists so a negative answer is always checkable.

## Quick Start

```bash
# Install (shell installer — bootstraps PM, Python, dependencies, and the launcher)
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# Interactive chat (default surface; set display.interface: tui to launch the Ink TUI instead)
hermes

# Single query
hermes chat -q "What is the capital of France?"

# Setup wizard  /  pick model+provider  /  health check
hermes setup
hermes model
hermes doctor

# Other surfaces
hermes desktop                 # launch the native desktop app (alias: hermes gui)
hermes dashboard               # web admin panel + embedded chat
hermes proxy                   # OpenAI-compatible local proxy backed by your OAuth provider
```

## Key Paths

```
~/.hermes/config.yaml       Main configuration (settings — never secrets)
~/.hermes/.env              API keys and secrets ONLY (under $HERMES_HOME if set)
$HERMES_HOME/skills/        Installed skills
~/.hermes/skins/            Custom themes (see references/themes.md)
~/.hermes/desktop-plugins/  Desktop app UI plugins (see references/desktop-plugins.md)
~/.hermes/tui-widgets/      TUI widget apps (see references/tui-widgets.md)
~/.hermes/pets/             Installed pet mascots (see references/petdex.md)
~/.hermes/state.db          Canonical session store (SQLite + FTS5)
~/.hermes/sessions/         Gateway routing index, request dumps, *.jsonl transcripts
~/.hermes/logs/             Gateway and error logs
~/.hermes/auth.json         OAuth tokens and credential pools
~/.hermes/hermes-agent/     Source code (if git-installed)
```

Profiles use `~/.hermes/profiles/<name>/` with the same layout. When a profile is active, resolve the real home from `$HERMES_HOME` — never hardcode `~/.hermes`.

## Routing Table — load the reference for the task

| User wants... | Load |
|---|---|
| **Anything not listed below — "can Hermes do X?", "how do I set up X?"** | **https://hermes-agent.nousresearch.com/docs/llms.txt** |
| Bots that chat, run routines, or message each other; the Bots tab | docs: `/user-guide/bot-mode` |
| CLI commands, subcommands, flags, "how do I run X" | `references/cli-reference.md` |
| In-session slash commands | `references/slash-commands.md` |
| Provider setup, API keys, OAuth | `references/providers-and-models.md` |
| config.yaml sections, toolsets, voice/STT/TTS | `references/configuration.md` |
| AGENTS.md / .hermes.md / CLAUDE.md project rules | `references/project-context-files.md` |
| Secret redaction, PII, approval modes, "reset permissions" | `references/security-privacy.md` |
| Delegation, cron, curator, kanban | `references/background-systems.md` |
| MCP servers (add, catalog, `hermes mcp`) | `references/native-mcp.md` |
| Webhook routes and event-driven runs | `references/webhooks.md` |
| A custom theme/skin ("synthwave theme", "change the gold ●") | `references/themes.md` + `templates/skin.yaml` |
| A desktop app UI element (pane, widget, ⌘K command, page) | `references/desktop-plugins.md` + `templates/plugin.js` |
| A live TUI panel or modal widget (ticker, clock, dashboard) | `references/tui-widgets.md` + `templates/clock.mjs` |
| Pet mascots — install, select, scale, diagnose | `references/petdex.md` |
| Windows-specific issues (keybinds, WinError 10106, BOM) | `references/windows-quirks.md` |
| Debugging: voice, tools missing, gateway, aux models | `references/troubleshooting.md` |
| Contributing code, native plugins, or knowledge-backed tool workflows | `references/contributor-guide.md` |
| Auditing the skill library — clarity, overlap, redundancy, deleting skills durably | `references/skill-library-auditing.md` |
| delegate_task "capped at N" reports | `references/delegate-task-concurrency-diagnosis.md` |
| "Can app X use my Nous Portal subscription/OAuth?" | `references/portal-auth-for-third-party-apps.md` |
| Connecting a messaging platform (Telegram, Discord, Slack, WhatsApp, …) | `references/messaging-platforms.md` + docs: `/user-guide/messaging` |

The reference list above is not the feature list — it is the set of topics that
need more than their docs page. For everything else Hermes ships, fetch
`llms.txt` and it maps the question to the page that answers it.

Two theming rules that hold even without loading the reference: **you apply skins yourself** (`hermes config set display.skin <name>` — every surface repaints live within ~a second; don't tell the user to run `/skin`), and **to tweak one color, edit the ACTIVE skin** (`hermes skin set <key> <hex>`) — never fork `default`, which drops the palette and resets the background.

## Knowledge-backed long-running workflows

- Separate the knowledge base, a lean preloaded controller, and any runtime gate; on-demand skill discovery is not a guarantee that research will be consulted or applied.
- Make retrieval an explicit work-unit prerequisite when a surface changes, an assumption fails, or work stalls. Bind the selected source/technique IDs and procedural skills to a bounded hypothesis with a control and budget; do not search the entire corpus before every request.
- Persist pending work, dispositions and evidence outside conversation context, then restore a bounded working-state capsule after resume or compaction; loading a document is not executing its technique.
- Introduce behavior-changing integrations in an isolated home and shadow mode first. Scope later enforcement to an explicitly activated engagement, not unrelated sessions or profiles.
- Distinguish a documented SDK primitive, an approved design, a registered plugin and verified runtime behavior. Do not claim automatic retrieval, preserved approvals or execution blocking until the actual tool paths have been exercised.

### Native extension delivery gates

1. Establish the approved implementation/activation boundary and resolve the installed runtime with `terminal(command="hermes --print-runtime-command")`; test through that interpreter/bootstrap rather than assuming a source-tree virtualenv matches the running agent.
2. Complete specification review before independent code-quality review. Treat passing fixtures and plugin registration as separate evidence, not whole-project acceptance.
3. Reproduce review findings through the actual public entry point before changing code. Add regression assertions for guard timing and boundary counts; a private-helper failure does not establish a public-path bug.
4. After fixes, rerun the full managed-runtime suite, real-corpus checks, validation and doctor. Keep isolated shadow testing, approved live enablement and strict enforcement as separate gates; claim only the paths actually exercised.

**Required depth:** load `references/contributor-guide.md` for the native-plugin procedure, hook boundaries and adversarial acceptance cases.

## Spawning Additional Hermes Instances

Run additional Hermes processes as fully independent subprocesses — separate sessions, tools, and environments.

### When to Use This vs delegate_task

| | `delegate_task` | Spawning `hermes` process |
|-|-----------------|--------------------------|
| Isolation | Separate conversation, shared process | Fully independent process |
| Duration | Minutes (bounded by parent loop) | Hours/days |
| Tool access | Subset of parent's tools | Full tool access |
| Interactive | No | Yes (PTY mode) |
| Use case | Quick parallel subtasks | Long autonomous missions |

### One-Shot Mode

```
terminal(command="hermes chat -q 'Research GRPO papers and write summary to ~/research/grpo.md'", timeout=300)

# Background for long tasks:
terminal(command="hermes chat -q 'Set up CI/CD for ~/myapp'", background=true)
```

### Interactive PTY Mode (via tmux)

Hermes uses prompt_toolkit, which requires a real terminal. Use tmux for interactive spawning:

```
# Start
terminal(command="tmux new-session -d -s agent1 -x 120 -y 40 'hermes'", timeout=10)

# Wait for startup, then send a message
terminal(command="sleep 8 && tmux send-keys -t agent1 'Build a FastAPI auth service' Enter", timeout=15)

# Read output
terminal(command="sleep 20 && tmux capture-pane -t agent1 -p", timeout=5)

# Send follow-up
terminal(command="tmux send-keys -t agent1 'Add rate limiting middleware' Enter", timeout=5)

# Exit
terminal(command="tmux send-keys -t agent1 '/exit' Enter && sleep 2 && tmux kill-session -t agent1", timeout=10)
```

### Multi-Agent Coordination

```
# Agent A: backend
terminal(command="tmux new-session -d -s backend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t backend 'Build REST API for user management' Enter", timeout=15)

# Agent B: frontend
terminal(command="tmux new-session -d -s frontend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t frontend 'Build React dashboard for user management' Enter", timeout=15)

# Check progress, relay context between them
terminal(command="tmux capture-pane -t backend -p | tail -30", timeout=5)
terminal(command="tmux send-keys -t frontend 'Here is the API schema from the backend agent: ...' Enter", timeout=5)
```

### Session Resume

```
# Resume most recent session
terminal(command="tmux new-session -d -s resumed 'hermes --continue'", timeout=10)

# Resume specific session
terminal(command="tmux new-session -d -s resumed 'hermes --resume 20260225_143052_a1b2c3'", timeout=10)
```

### Tips

- **Prefer `delegate_task` for quick subtasks** — less overhead than spawning a full process
- **Use `-w` (worktree mode)** when spawning agents that edit code — prevents git conflicts
- **Set timeouts** for one-shot mode — complex tasks can take 5-10 minutes
- **Use `hermes chat -q` for fire-and-forget** — no PTY needed
- **Use tmux for interactive sessions** — raw PTY mode has `\r` vs `\n` issues with prompt_toolkit
- **For scheduled tasks**, use the `cronjob` tool instead of spawning — handles delivery and retry
- **"delegate_task is capped at N" reports** — see `references/delegate-task-concurrency-diagnosis.md`. Three real cap paths in Hermes; if none fired, the model is self-limiting and rationalising it as "the runtime caps."
- **"Can $external_app use my Nous Portal subscription / OAuth?"** — see `references/portal-auth-for-third-party-apps.md`. Walk the user through three layers (plugin-vs-app, what Portal actually exposes, local-broker-proxy option).

## Surfaces (quick orientation)

- **Desktop app** (`hermes desktop` / `hermes gui`) — native Electron app for macOS/Linux/Windows: streaming chat, session list, Cmd+K palette, drag-and-drop files, native notifications, per-profile remote-gateway login. Extend it with UI plugins — `references/desktop-plugins.md`.
- **Web dashboard** (`hermes dashboard`) — full admin panel: messaging channels, MCP catalog, webhooks, memory, profile builder, plus an embedded `hermes --tui` chat. Secured behind an OAuth/token gate.
- **Ink TUI** (`hermes --tui` or `display.interface: tui`) — terminal UI with docked widget apps — `references/tui-widgets.md`.
- **OpenAI-compatible proxy** (`hermes proxy`) — a local OpenAI API backed by whichever OAuth provider you're signed into. Point Codex CLI, Aider, Cline, or any script at it — no API key.

## Hard Invariants (never violate, regardless of what you loaded)

- **Never break prompt caching** — don't change past context, toolsets, or the system prompt mid-conversation. The only exception is context compression.
- **Message role alternation** — never two assistant or two user messages in a row; only `tool` results can repeat.
- **Secrets in `.env`, settings in `config.yaml`** — never tell a user to put a non-credential setting in `.env`.
- **Profile-safe paths** — `get_hermes_home()` in code, `$HERMES_HOME` when resolving paths in a session.
- **Never hand-edit `config.yaml` for the user** — use `hermes config set KEY VAL`; a stray indent can corrupt the file and break the live gateway.

## Importing another agent's skill tree (Claude Code / Codex / shared dirs)

To give Hermes a skill library maintained by Claude Code (`~/.claude/skills`), Codex
(`~/.codex/skills`), or a shared team dir, **register it, do not copy it**:

```bash
hermes config set skills.external_dirs '["~/.claude/skills"]'   # JSON list; ~ and ${VAR} expand
```

Why registration beats copying:

- **Symlinks are followed.** The index scanner is `iter_skill_index_files()` in
  `agent/skill_utils.py`, which uses `os.walk(..., followlinks=True)`. A Claude skills dir that is
  mostly symlinks into `~/.codex/skills` and plugin caches resolves fully. (Note `tools/skills_sync.py`
  uses `Path.rglob` instead, which does *not* follow symlinked dirs — so trust `hermes skills list`,
  not sync counts, when auditing what loaded.)
- **External dirs are the LOWEST precedence tier** (`project → local → skills.create_dir → external_dirs`),
  so same-named bundled Hermes skills win and nothing gets clobbered. Shadowed copies are logged, not errors.
- **Never copy an external tree into `~/.hermes/skills/`.** Two different skills sharing a name *inside one
  directory* are never guessed between — bare-name loads then fail with
  `Ambiguous skill name X: use one of a/one, b/two`, breaking the bundled skill too.

Audit before and after, and verify with a real load:

```bash
hermes prompt-size | grep -E "System prompt total|skills index"   # context cost delta
hermes skills list | tail -2                                      # "N builtin, M local — T enabled"
```

Then call `skill_view(name='<an-imported-skill>')` and confirm `skill_dir` points into the external tree.

### Installing a single skill from a registry or a GitHub repo

- Registry skill: `hermes skills search <name>` → `hermes skills install skills-sh/<owner>/<repo>/<skill> --yes`.
  It lands top-level in `~/.hermes/skills/<skill>` and the security-scan verdict is printed; only a
  *blocked* verdict needs `--force`, so read the verdict before reaching for it.
- `hermes skills inspect`/`install` accept ONLY a registry identifier or a direct raw `SKILL.md` URL.
  A bare repo URL (`https://github.com/owner/repo`) fails with "Could not find ... in any source" —
  use the raw `SKILL.md` URL or clone the repo into the tree instead.
- Check for a name collision BEFORE adding a skill: two dirs holding the same skill name can break
  bare-name loads for both. `find ~/.hermes/skills -name SKILL.md | awk -F/ '{print $(NF-1)}' | sort | uniq -d`.
- A skill whose workflow shells out to a CLI (agent-browser, agent-email, ...) is not usable until that
  CLI exists. Install it and smoke-test before calling the skill working (`agent-browser doctor`,
  `agent-email about`). Installing the skill alone is a partial install.

Pitfalls worth knowing up front:

- **Budget the context.** Each skill costs ~75-95 B of always-on system-prompt index. ~200 imported skills
  added ~15 KB (19 KB → 34 KB total system prompt here). Measure with `hermes prompt-size` first.
- **Skip plugin cache roots** like `~/.claude/plugins/cache` — they hold 5-6 copies of the same skill across
  version hashes and mirrored `.junie/.roo/.agents/.kiro` dirs, which creates intra-dir ambiguity for no gain.
  Plugin skills worth having are usually already symlinked into the main skills dir.
- **Claude/Codex frontmatter is compatible** (`name` + `description`); extra keys like `argument-hint` and
  `allowed-tools` are ignored harmlessly.
- **The system-prompt skill index stays stable between compactions**, preserving prompt caching. Skill
  additions/removals are announced in a short note on the next user message; the system-prompt index
  refreshes at compaction. Explicit `skill_view(name=...)` resolves a new skill immediately. Do not
  require a new session merely to load or discover a newly installed skill.
- **External dirs are writable if the process can write them.** `skill_manage` patches edit skills in place,
  including inside `~/.claude/skills`. Use filesystem permissions or a separate profile to keep them read-only.
- **Inline `python -c` often trips the approval gate.** Write an audit script to `$TMPDIR` and run the file.
- **`platforms:` is a HARD LOAD GATE, not just a display filter.** A skill declaring
  `platforms: [linux]` is not merely hidden from the index on macOS — `skill_view(name)` fails with
  `Skill 'X' is not supported on this platform`. It is unusable, not just unlisted. (The code
  comment saying "explicit loads bypass it" refers to the separate `environments:` gate.) Roughly
  a quarter of a Codex/Claude library can be silently dead this way. Find them by searching skill content for a `platforms:`
  line whose only entry is `linux` (`search_files(pattern='platforms:', target='content')`), then widen to
  `[linux, macos]` only when the skill's own
  `compatibility:` line lists tooling the host actually has (curl/python3/bash/jq/nmap/PD tools
  are all present on macOS).
- **Mounting is not installing.** `external_dirs` makes skills *usable* but leaves them out of
  `~/.hermes/skills/`, so a directory listing there shows nothing and the user reasonably concludes the
  import failed. If the user wants to *see* the files, copy them in — and skip any name already
  claimed locally, or the copy collides inside one tree and `Ambiguous skill name` breaks the
  BUNDLED skill too. A reusable installer lives at `~/.hermes/scripts/sync-claude-skills.py`.
- **A copied-in tree is DERIVED data — never edit or delete inside it.** The installer above rebuilds
  its destination on every run: it `rmtree`s any directory that is not in its wanted set and re-copies
  the rest. An edit or deletion made inside that tree therefore looks like it worked, then gets
  silently reverted. To remove a skill from such a tier durably, either add its name to `skills.disabled`
  in `config.yaml` (Hermes-only, reversible, works across every tier) or delete it at the SOURCE. When
  the user asks to "delete redundant skills", say this before acting.
- **When auditing what is installed, count from the CLI, not from the filesystem.** `hermes skills list`
  reflects the index; a directory count does not. Expect them to differ whenever `platforms:` or
  `skills.disabled` excludes something.

## MANDATORY ON INVOCATION — PROTOCOL RESTATMENT (END OF FILE)

You have reached the end of this SKILL.md. The invocation protocol below is identical to the one at the top of this file. If you are reading this, the full skill context is loaded — confirm the checklist.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/background-systems.md`, `references/cli-reference.md`, `references/configuration.md`, `references/contributor-guide.md`, `references/delegate-task-concurrency-diagnosis.md`, `references/desktop-plugins.md`, `references/messaging-platforms.md`, `references/native-mcp.md`, `references/petdex.md`, `references/portal-auth-for-third-party-apps.md`, `references/project-context-files.md`, `references/providers-and-models.md`, `references/security-privacy.md`, `references/skill-library-auditing.md`, `references/slash-commands.md`, `references/themes.md`, `references/troubleshooting.md`, `references/tui-widgets.md`, `references/webhooks.md`, `references/windows-quirks.md`, `templates/clock.mjs`, `templates/plugin.js`, `templates/skin.yaml` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# Project Context Files

Hermes injects project-level instructions into the system prompt by reading context files from the working directory. The discovery order is **first match wins** — only one project context source is loaded per session.

| File (in priority order) | Discovery | Use when |
|---|---|---|
| `.hermes.md` / `HERMES.md` | Walks parents up to the git root, stops at git root | You want hierarchical project rules (root + per-package overrides) |
| `AGENTS.override.md` | Personal override beside `AGENTS.md`; higher priority than it | You need local conventions without editing the committed file |
| `AGENTS.md` / `agents.md` | Git-root-to-cwd chain inside a repository; cwd only outside one; deeper subdirectory files discovered progressively | You want portable project instructions |
| `CLAUDE.md` / `claude.md` | Cwd plus progressive subdirectory discovery | Claude-flavored project context |
| `.cursorrules` / `.cursor/rules/*.mdc` | Cwd only | Migrating from Cursor |

`SOUL.md` (in `$HERMES_HOME`) is independent and always loaded when present — it sets the agent's identity, not project rules.

### Pick the right one

- **Use `.hermes.md`** when you want Hermes-specific behavior that lives above the cwd (root + subtree), or when you want rules to inherit from a parent directory. The parent walk stops at the git root, so a home-level `.hermes.md` won't leak into every project (a git repo's root is the boundary).
- **Use `AGENTS.md`** when the same project will also be worked on by other agents. In Hermes, a repository's git-root-to-cwd chain is merged at startup, and deeper context files are discovered as file tools enter their subdirectories. Outside a git repository, startup discovery does not inherit unrelated parent files. A neighboring `AGENTS.override.md` takes precedence over the committed `AGENTS.md`.
- **Don't put project rules in `~/.hermes/AGENTS.md`** (or any other home-level location). When Hermes runs with that directory as cwd, the file loads — but only for that one directory. For cross-project context, use `SOUL.md` (in `$HERMES_HOME`, identity-only) or install a skill via `hermes skills install`.

### Size and truncation

Startup files use explicit `context_file_max_chars` when configured; otherwise the cap scales with the model context window (20,000-character floor, 500,000-character ceiling). Oversized files are **head + tail** truncated. Progressively discovered subdirectory files have a separate fixed 32,000-character preview cap. Keep routing instructions short; leave bulky knowledge in on-demand references.

### Security

Project context files pass through the threat-pattern scanner. A detected threat blocks the project file and inserts a `[BLOCKED: ...]` placeholder; do not assume the rest of a flagged `AGENTS.md` still loads. User-owned `SOUL.md` has a separate warning-only treatment, while a third-party profile-distributed `SOUL.md` remains subject to blocking. Consult the current Context Files documentation before relying on these security boundaries.

### Disable for one session

`hermes --ignore-rules` skips auto-injection of all project context files (`.hermes.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`) **and** `SOUL.md` identity, plus user config, plugins, and MCP servers. Use it to isolate whether a problem is your setup or Hermes itself.

### Example: a small `.hermes.md`

```markdown
# My Project

Hermes: when working in this repo, follow these rules.

## Build
- Always run `make test` before declaring a change done.
- Use `uv run` for Python, not `pip install`.

## Style
- Prefer `pathlib.Path` over `os.path`.
- No `print()` in production code — use the `logger`.
```

That file at `/home/me/projects/myrepo/.hermes.md` is auto-loaded when Hermes runs in any subdirectory of `/home/me/projects/myrepo`, but not when it runs in `/home/me/other-project`.

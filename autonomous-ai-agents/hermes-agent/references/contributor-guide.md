# Contributor Quick Reference

For occasional contributors and PR authors. Full developer docs: https://hermes-agent.nousresearch.com/docs/developer-guide/

### Project Layout

```
hermes-agent/
├── run_agent.py          # AIAgent — core conversation loop
├── model_tools.py        # Tool discovery and dispatch
├── toolsets.py           # Toolset definitions
├── cli.py                # Interactive CLI (HermesCLI)
├── hermes_state.py       # SQLite session store
├── agent/                # Prompt builder, context compression, memory, model routing, credential pooling, skill dispatch
├── hermes_cli/           # CLI subcommands, config, setup, commands
│   ├── commands.py       # Slash command registry (CommandDef)
│   ├── config.py         # DEFAULT_CONFIG, env var definitions
│   └── main.py           # CLI entry point and argparse
├── tools/                # One file per tool
│   └── registry.py       # Central tool registry
├── gateway/              # Messaging gateway
│   └── platforms/        # Platform adapters (telegram, discord, etc.)
├── cron/                 # Job scheduler
├── tests/                # Extensive pytest suite (run via scripts/run_tests.sh)
└── website/              # Docusaurus docs site
```

Config: `~/.hermes/config.yaml` (settings), `~/.hermes/.env` (API keys) — both under `$HERMES_HOME` when it is set.

### Adding a Tool

Two files. Auto-discovery imports any `tools/*.py` with a top-level
`registry.register()` call, but a tool is only *exposed* to an agent once
its name appears in a toolset.

**1. Create `tools/your_tool.py`:**
```python
import json, os
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": "..."})

registry.register(
    name="example_tool",
    toolset="example",
    schema={"name": "example_tool", "description": "...", "parameters": {...}},
    handler=lambda args, **kw: example_tool(
        param=args.get("param", ""), task_id=kw.get("task_id")),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

**2. Wire it into a toolset in `toolsets.py`** — add the name to
`_HERMES_CORE_TOOLS` (every platform) or to a specific toolset.

All handlers must return JSON strings. Use `get_hermes_home()` for paths,
never hardcode `~/.hermes`. For custom/local-only tools, write a plugin in
`~/.hermes/plugins/` instead of editing core — see the developer docs.

### Native Plugins and Knowledge-Backed Workflows

Use this procedure for profile-local tools, durable research ledgers and workflow policy. These are extension contracts and verification requirements, not evidence that a particular custom plugin already exists or has passed runtime tests.

1. **Verify the installed contract before choosing an extension.** Use `terminal` for `hermes --version`, `hermes plugins --help` and `hermes chat --help`; inspect the matching installed SDK alongside current official plugin/observer/middleware docs. Use `hermes plugins list --plain --no-bundled` for a compact local-plugin inventory instead of flooding context with the full bundled table. Do not upgrade Hermes solely because online docs are newer when the installed primitives already satisfy the task.
2. **Keep local behavior outside core.** Package tool schemas, handlers and a small controller skill as a native plugin. Use `ctx.register_tool()` and `ctx.register_skill()` rather than modifying built-in registries for personal workflows. Reuse the existing corpus through bounded lookup; a bibliography supplies discovery, not reviewed test recipes.
3. **Separate durable work from settings.** Resolve the active profile through `get_hermes_home()`. Use `plugin_data_dir()`/`plugin_db()` from `plugins.plugin_storage` for ledgers, and `ctx.state` for small plugin-owned state. Use transactional, idempotent updates and host-provided session/task identity; never bind writes to a model-supplied identity or a global last-seen session. Keep evidence references contained in the selected workspace and record changes rather than silently trusting stale files.
4. **Select hooks by their actual firing boundary.** Use `pre_llm_call` for a bounded, ephemeral state capsule at user-turn entry; it does not run before every internal tool step. Use `pre_tool_call` for prerequisite decisions and `post_tool_call` for observed provenance. Accept additive callback fields through `**kwargs`. Do not rewrite historical messages or the stable system prompt to restore state.
5. **Distinguish policy returns from failures.** Return a valid `{"action": "block", "message": "..."}` directive when a verified pre-tool policy must veto a call. Do not throw an exception as a blocking strategy: generic hook/middleware callback failures can continue the runtime. Handle anticipated state/identity failures explicitly; verify the installed timeout and load-failure behavior separately. A disabled or unloaded plugin is not an enforcement boundary.
6. **Audit execution routes before promising enforcement.** Exercise terminal, browser, nested dispatch, wrappers, deferred tools and delegated workers. Verify that nested `ctx.dispatch_tool()` retains the required approval/guardrail path rather than assuming the facade or handler registration proves it. Bind any permit to exact arguments, host identity, hypothesis and surface revision; test replay, concurrent consumption and stale-state rejection. Treat a workflow gate as a quality control, not a sandbox against an agent with unrestricted host access.
7. **Test through the installed runtime in an isolated home.** Resolve the interpreter/bootstrap with `terminal(command="hermes --print-runtime-command")`; preserve its runtime setup in the test launcher rather than guessing a legacy virtualenv. Under a dedicated scratch `HERMES_HOME`, run the full suite, `hermes plugins validate <plugin-path> --json`, and `hermes plugins doctor <plugin-path> --ci`. Exercise real registry, lifecycle and outer agent-executor calls with physical fixture evidence; test restart/resume, concurrent writers, missing evidence, unrelated identities and registration-profile isolation. Verify every real corpus ID and literal collection against source counts and hashes. Label provider setup patches and distinguish offline transport tests from live CLI/gateway/model/worker execution; mocks or registration alone do not prove those paths.
8. **Close review gates before approved activation.** Complete specification review, then independent quality review; reproduce each important finding through the public path, fix it with a failing regression, and repeat review. After fresh runtime/corpus/validation checks, obtain separate approval for active-profile shadow enablement. Use `hermes plugins enable <plugin-name>`, read back status with `hermes plugins list --plain --no-bundled`, and verify enabled behavior without blocking execution. Strict enforcement requires its own later specification, approval and execution-route tests; it is not a prerequisite for a shadow pilot and must not be enabled implicitly. Roll back with `hermes plugins disable <plugin-name>` while preserving durable data. Report implementation, tested behavior and deployment status separately.

Primary contract references: `/docs/developer-guide/plugins`, `/docs/developer-guide/observer-hooks`, and `/docs/developer-guide/middleware` on the official Hermes documentation site. Recheck them and the installed source before relying on behavior-changing APIs.

#### Native-plugin verification traps

- Run both `hermes plugins validate <path> --json` and `hermes plugins doctor <path> --ci`. Validation's isolated recording context uses void registration methods; a `None` return is a collision only in a live SDK registration context, not in that recorder. Preserve actual collision rejection and test both contexts.
- Exercise the real outer agent tool executor as well as `model_tools.handle_function_call`. The outer executor can suppress inner pre/post observers and own the hooks itself; direct registry success does not prove outer host identity, call IDs or receipt accounting. Isolate provider/network setup, retain real hooks/dispatch, physically create fixture evidence, and label what was patched.
- Snapshot the hypothesis and surface revisions at execution entry and attach those original values at completion. Reject stale receipts when recording a tested result; never relabel an old attempt as a revised plan. Treat rejected/unaccounted attempts as unresolved, not automatically tested.
- Use exact indexed lookups for an explicitly selected surface rather than searching a bounded status page. Capture its revision before retrieval and reject a concurrent change at receipt attachment.
- Resolve session-only context for unambiguous reads, but do not manufacture a missing host task identity for mutations or observation receipts. Bind leased callbacks to their registration profile rather than an unrelated ambient home.
- Bound input files before materializing payloads, not just model-facing outputs. Cover cards, vocabulary and every review/reproduction artifact. Stop candidate enumeration at the bound instead of constructing an unbounded path list; account for catalogue/vocabulary and unique artifacts in aggregate limits before payload reads. Retain bounded consistency checks and distinguish input-byte caps from Python RSS. Test the exact total-file boundary and assert which reads occurred, because a late rejection can still allocate the forbidden data.
- Determine manifest/artifact roles from declared paths before card validation; a `.json` extension or vocabulary-like filename does not establish role. Preserve arbitrary supported filenames, use explicit roles for size limits and consistency reads, and hash each referenced artifact once. Test JSON review/reproduction artifacts, artifacts larger than the card cap, shared artifacts and malformed unreferenced manifests; do not hide a loader bug by silently dropping files or narrowing the input contract.
- Apply the same non-echoing sensitive-text admission guard to model schemas and direct ledger APIs. Test literal password assignments and whitespace/JSON verification-code forms alongside ordinary API/technique descriptions. Treat heuristic filtering as incomplete; never claim universal DLP, artifact sanitization or old-data removal from a regex check.

### Adding a Slash Command

1. Add `CommandDef` to `COMMAND_REGISTRY` in `hermes_cli/commands.py`
2. Add handler in `cli.py` → `process_command()`
3. (Optional) Add gateway handler in `gateway/run.py`

All consumers (help text, autocomplete, Telegram menu, Slack mapping) derive from the central registry automatically.

### Agent Loop (High Level)

```
run_conversation():
  1. Build system prompt
  2. Loop while iterations < max:
     a. Call LLM (OpenAI-format messages + tool schemas)
     b. If tool_calls → dispatch each via handle_function_call() → append results → continue
     c. If text response → return
  3. Context compression triggers automatically near token limit
```

### Testing

Use `scripts/run_tests.sh` for CI parity. It clears credentials, sets
`TZ=UTC`, and runs each test file in a separate subprocess through
`scripts/run_tests_parallel.py` on every platform. It does not use xdist.

```bash
scripts/run_tests.sh                          # full suite
scripts/run_tests.sh tests/tools/             # one directory
scripts/run_tests.sh tests/tools/test_x.py    # one file
scripts/run_tests.sh -v --tb=long             # pass-through pytest flags
```

- Tests auto-redirect `HERMES_HOME` to temp dirs — never touch real `~/.hermes/`.
- Prepare Python through the PM developer workflow before building a test environment.
- Run `python -m pm.build_env --source . --out .venv --group dev --group test`.
  The output must not exist. Stop its processes and intentionally remove only
  that disposable environment before regeneration.
- The runner probes repository `.venv`, `venv`, and the standard source-install
  venv before falling back to `HERMES_PYTHON`. Each candidate must contain pytest.
- **Windows:** run the same wrapper through Git Bash. See `references/windows-quirks.md`.
- After editing `pyproject.toml`, run `hermes pm lock`, re-source `./activate`, and
  commit `pyproject.toml` with `uv.lock`.
  Do not mutate Hermes environments with raw pip or uv commands.

Host-specific tests run on the real host. Use one `@pytest.mark.platforms(...)`
marker per test, such as `@pytest.mark.platforms("windows", arch="arm64")`.
Do not fake the host by patching `sys.platform` or platform probes.

### System prompt's execution-environment block

Factual host/backend guidance (OS, `$HOME`, cwd, terminal backend, shell)
is emitted by `agent/prompt_builder.py::build_environment_hints()`. The key
invariant for prompt authors: with a **remote** terminal backend
(`docker, singularity, modal, daytona, ssh, managed_modal`), host info is
suppressed and *every* file tool runs inside the backend container — the
prompt must never describe the host the agent can't touch.

### Commit Conventions

```
type: concise subject line

Optional body.
```

Types: `fix:`, `feat:`, `refactor:`, `docs:`, `chore:`

### Key Rules

- **Never break prompt caching** — don't change context, tools, or system prompt mid-conversation
- **Message role alternation** — never two assistant or two user messages in a row
- Use `get_hermes_home()` from `hermes_constants` for all paths (profile-safe)
- Config values go in `config.yaml`, secrets go in `.env`
- New tools need a `check_fn` so they only appear when requirements are met

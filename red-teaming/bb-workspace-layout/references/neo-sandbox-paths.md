# Neo sandbox — workspace and task folder structure

Ground truth for the Neo/agent-swarm cloud sandbox, captured 2026-10-10 by direct inspection.
Only applies when work executes inside Neo. A local Hermes session writes to the engagement root
instead (`bb-workspace-layout` §Layout).

## Root: `/workspace`

```
/workspace/
├── .cache/                              # tool caches (may be empty)
├── .neo/                                # PLATFORM STATE — do not edit
│   ├── _files.db                        # SQLite file registry (backing for write_file)
│   ├── _files.db-shm
│   └── _files.db-wal
├── .neo-task-<taskId>                   # MARKER FILE: active task id + created timestamp
├── .tmp/                                # scratch space
├── .vpn/{configs,logs,state}/           # VPN client state (see vpn_connect)
├── go/                                  # Go build/GOPATH cache
├── lost+found/                          # fs recovery
├── tasks/
│   └── <taskId>/                        # ← PER-TASK WORKSPACE (the one actually used)
├── subagents/                           # advertised shared dir (create if absent)
└── seclists/                            # advertised shared dir (clone if absent)
```

- **`.neo/` is platform-managed.** `_files.db` is the persistence registry behind `write_file`;
  never delete or hand-edit it.
- **`.neo-task-<taskId>`** is the current-session marker, e.g.
  `59eedc8d-7742-4b97-ba73-aae6e7517afe` plus an ISO created-at timestamp.
- **`subagents/` and `seclists/` are shared by convention, not guaranteed present.** In the
  observed run both were **absent** — create or clone when a workflow needs them, e.g.
  `git clone https://github.com/danielmiessler/SecLists /workspace/seclists`. Wordlists being
  absent is a setup gap, not a clean scan result.

## Task workspace: `/workspace/tasks/<taskId>/`

The **Recommended Run Artifact Directory** handed to every run. All new artifacts, derivatives,
scripts, evidence and reports go here or in subdirs of it.

```
/workspace/tasks/<taskId>/
├── .neo/                                # PLATFORM BOOKKEEPING — do not edit
│   ├── .thread                          # thread/stream pointer
│   ├── <callId>.begin                   # per-tool-call start marker
│   └── <callId>.rc                      # per-tool-call exit code
├── .tool-output/                        # AUTO-MANAGED spill dir
├── <your-dirs>/                         # create these, named by purpose
└── <your-files>                         # e.g. report.md, summary.md
```

Everything authored lives under the task root. Never invent a sibling run's path; never assume
another task's directory is readable.

## `.tool-output/` — tool-output provenance spill

Auto-populated whenever a tool result is too large for inline return. **Do not write here
manually** — only read, via `read_file` on the exact path or the `_spilled_to` pointer.

```
.tool-output/
└── <toolId>__<slug>__tc-call_<12-hex>.json
        │         │            └── tool-call id
        │         └── query slug, e.g. probe-flags-output
        └── source tool, e.g. knowledge_search / run_command
```

Payload shape:

```json
{
  "_meta": {
    "formatVersion": 1,
    "title": "list",
    "toolId": "knowledge_search",
    "toolCallId": "call_69159a5678034261862de2ab",
    "taskId": "59eedc8d-7742-4b97-ba73-aae6e7517afe",
    "streamId": "898d2b55-2127-4c8a-bde4-103027e32cca",
    "agentRunIndex": 0,
    "createdAt": "2026-10-10T08:10:49.781Z",
    "input": { "action": "list", "limit": 10, "includeTests": false }
  },
  "result": { "...": "full tool payload" }
}
```

`_meta` is the provenance record — which tool, which call, which task/stream, exact input.
`result` is the complete untruncated output. When a tool result contains `_spilled_to`, read that
path; do not re-invoke the producing tool for the full dump.

## Recommended sub-directory conventions

No enforced schema below the task root — name dirs by purpose so later runs and the verifier can
find things.

| Dir | Purpose |
|-----|---------|
| `kb-context/` | Documentation/reference artifacts |
| `evidence/` | Raw + interpreted evidence packets, per finding |
| `manual-probes/` | Fallback security-baseline probes (`cors/`, `openapi/`, `info/`, `headers.jsonl`, `ssh/`) |
| `scans/` | Raw scanner output (nuclei/httpx/ffuf JSONL) kept unfiltered for re-filtering |
| `scripts/` | Reproducible scripts used to produce the above |
| `reports/` | Human-facing deliverables |
| `pocs/` | Per-task PoC artifacts |

Separate conventions to respect:
- **`/workspace/pocs/`** — root-level, not task-scoped — is the path the verification contract
  expects for a `poc_artifact`.
- Use a **distinct sub-directory per delegated worker** (e.g. `scans/<worker>/`) so parallel
  workers never overwrite one another.

## Plane model (cloud vs BYOS)

- **Cloud-managed:** everything above is a rich Linux sandbox; file APIs and shell share the same
  `/workspace`.
- **Self-hosted / BYOS (`neo-sandbox` on the user's machine):** dual plane —
  1. **CLI plane** (`run_command` / `execute_script`) runs inside a Linux docker confine image;
     install missing packages there.
  2. **Host plane** — file APIs (`read_file`/`write_file`/…), browser, and desktop/computer-use
     talk to the **host** (macOS/Windows/Linux). `/workspace` maps to the durable install
     workspace.
  Use the optional `sandbox` selector only when host binaries or GUI-adjacent shell are needed.

## Rules of thumb

1. Write all task artifacts under `/workspace/tasks/<taskId>/`; never reach into another task's dir.
2. Keep supplied inputs immutable; write derivatives under the task root.
3. Prefer `write_file` for durable artifacts (on cloud it also persists to bucket storage).
4. Read `.tool-output/` spilled payloads by exact path; don't re-run the tool to re-fetch.
5. Never hand-edit `.neo/` or `.tool-output/`; they are platform-managed.
6. Shared dirs (`subagents/`, `seclists/`) may be absent — create/clone rather than assuming.
7. Only two external URL mechanisms are permitted for file sharing:
   `manage_unlisted_file_url` and `web_test_files` (0ac.io). Otherwise return workspace paths.

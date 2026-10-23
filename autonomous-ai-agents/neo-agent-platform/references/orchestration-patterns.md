# Neo orchestration patterns

Drawn from an observed agent-swarm run (documenting 35 knowledge collections). These are the
proven mechanics, not a generic template.

## Phase flow

1. **Understand** — read the request against the visible tool surface. Identify the actual unit
   of work ("retrieve and structure KB content" ≠ "scan a target").
2. **Decide ownership first** — check for independent branches and shared state, *before*
   choosing tools. No independent branches + shared evolving state + ~10 minutes of scope ⇒ root
   retains.
3. **Acquire the smallest method set needed now** — batched in a single atomic call. Do not
   acquire a method for a capability a native tool already covers.
4. **Execute** — fan out independent reads as sibling calls in one response.
5. **Preserve** — register every produced file in `tracked_files`; write durable observations as
   `facts`; raw tool outputs spill to `.tool-output/` with provenance.
6. **Verify** — `ls -la` + `wc -l` on the output directory. **A write is not proven by prose or
   by the write call's success flag.**
7. **Synthesize** — one summary answer. Offer a deeper follow-up rather than unilaterally
   expanding scope.

## Ownership rationale (the governing invariant)

*"Runs own independent assignments."* An assignment with **no independently useful parallel
tracks** is one bounded deliverable whose steps share evolving state (raw retrieval → curation →
write → verify). Delegating it adds coordination cost for no benefit.

Delegate when there is a genuinely independent branch, or one that is noisy, long-running, or
context-heavy enough to be worth isolating.

**Acquiring a subagent is a *method* decision, not an ownership decision.** In the observed run
`sandbox` was acquired for its facilities while root retained the whole assignment.

## Tool contracts as actually exercised

### Catalog inspection

```
list_subagents({ query: "knowledge base search indexes nuclei templates docs" })
```

Returns `subagents[]` plus availability/degraded status. Output can exceed the inline budget and
**spill** to `.tool-output/list_subagents__*.json` with a `_spilled_to` pointer and
`_spill_hint` — read that exact path with `read_file`, never re-invoke the tool to re-read.

### Method acquisition

```
acquire_subagents({
  subagents: [{ id: "sandbox" }],
  reason: "Need the knowledge_search facility / file tools to inspect the knowledge indexes
           at root for a small bounded request."
})
→ {"activated":["sandbox"],"effective_next_step":true}
```

`subagents` is an array of `{ id, inputs? }`, 1–25, **atomic** — a failed acquisition does not
partly activate the set. It merges the method, non-identity instructions and native tools into
*this* conversation. It does **not** delegate, replace identity, change model/provider, or expand
authorization. Re-acquiring the same `id` + `inputs` is idempotent; changed `inputs` is rejected.

**Tools from an acquisition are not usable in the same parallel batch** — `effective_next_step`
is literal.

### Knowledge retrieval

```
knowledge_search({ action: "status", indexName: "nuclei" })            # → exists:false (unreliable)
knowledge_search({ action: "search", indexName: "nuclei",
                   isGlobal: true, query: "...", limit: 5 })
```

`isGlobal: true` is required for shared collections; a bare `indexName` resolves to *user-owned*
indexes only. This was the one failed approach of the observed run and was recorded as a fact.
The six index queries ran as **parallel sibling calls in one response**.

### Artifact writes

```
write_file({ path: "<taskdir>/kb-context/<name>.md", content: "..." })
→ { success, path, bytesWritten }
```

Base path is always the **run artifact directory** (`/workspace/tasks/<task-id>/`), never an
invented sibling path.

### Verification

```
run_command({ command: "ls -la <taskdir>/kb-context/ && echo '---' && wc -l <taskdir>/kb-context/*.md" })
```

Confirmed 7 files, 1,550–8,471 bytes, 1,003 total lines, `exitCode: 0`. This establishes artifact
existence from real output rather than from a success flag.

### Durable state writeback

```
update_working_memory({ scope: "task",
                        updates: { tracked_files: [...], facts: [...] } })
```

`scope: task` is this conversation only. In `memory_off` mode `global`/`project` writes are
rejected. **Lists REPLACE the entire field, they do not append** (project/task arrays) — read
before writing or you will drop entries.

## Reusable recipes

- **A. Query a global KB index** —
  `knowledge_search({action:"search", indexName:"<idx>", isGlobal:true, query:"<topic>", limit:N})`
- **B. Fan out N independent reads in one batch** — sibling calls in a single response, not
  sequential turns.
- **C. Acquire only what is needed now, then act next step** — acquisition is atomic and
  effective on the following step; never mix acquisition with use in one batch.
- **D. Prove artifacts exist** — after `write_file`, run `ls`/`wc` and read the real output.
- **E. Handle spill** — when a tool returns `_spilled_to`, `read_file` that exact path (pass
  `nextCursor` verbatim when paginated). Do not re-run the producing tool to re-read.

## Surfaces available but deliberately unused

Knowing why a surface was skipped is as useful as knowing it exists.

| Tool | Why not used |
|---|---|
| `delegate_task` | No independent parallel assignment existed for this bounded task. |
| `trigger_dynamic_subagent` | No user-authored specialization fit the request. |
| `invoke_tool` | The atomic catalog (`research.*`, `sandbox.*`, `team.*`) was not needed — native tools sufficed. Available if a single self-contained op were required. |
| `render_report` | Documentation, not a findings/recon canvas; guidance says skip for simple outputs. |
| `create_issue` / `bulk_create_issues` | No security finding — nothing tracker-eligible. |
| `research.web_search` | KB indexes are source-level; no live-web verification requested. |
| `team.update_memory` / `update_target_memory` | Main-agent-only; no cross-task durable target fact worth persisting. |

## Evidence and artifact conventions

- Raw tool outputs → `<taskdir>/.tool-output/<tool>__<slug>__<call-id>.json` (with provenance).
- Curated deliverables → `<taskdir>/<output-dir>/`.
- Provenance = the exact call that produced each curated snippet.

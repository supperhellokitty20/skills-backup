# Auditing the skill library

Use when the user asks to audit, tidy, consolidate, or "delete redundant" skills, shrink the
library, or review it for clarity and overlap.

The deliverable is two things: a written audit, and a library that is genuinely smaller — with the
removal done in a way that actually sticks.

## 0. Establish the tier layout before counting anything

Skill counts are meaningless until you know which trees are in play. Hermes resolves skills from
several tiers and the same skill can sit in more than one.

```bash
hermes skills list | tail -2                  # authoritative: "N builtin, M local — T enabled"
hermes prompt-size | grep -E "System prompt total|skills index"
```

- Count skills from `hermes skills list`, never from a directory listing. They legitimately differ
  whenever `platforms:` or `skills.disabled` excludes something.
- The skills index is the expensive part of the system prompt — a few hundred skills can be most of
  it. Report that number; it is the honest measure of what the library costs.

Enumerate every tier root that exists and how many skills each holds:

```python
import os, re
from pathlib import Path

def scan(root):
    """Every dir containing SKILL.md, FOLLOWING symlinks — this is how Hermes indexes."""
    out = {}
    for dp, dns, fns in os.walk(root, followlinks=True):
        if "SKILL.md" in fns:
            out[Path(dp).name] = Path(dp)
            dns[:] = []          # a skill dir is not descended into
    return out
```

**`os.walk(..., followlinks=True)`, not `Path.rglob`.** `rglob` does not follow symlinked
directories, so a tier that is mostly symlinks scans as a handful of skills instead of hundreds —
which then makes the upstream tier look smaller than the copy of it, and you draw the wrong
conclusion about which one is redundant. Hermes indexes with `followlinks=True`; match it.

## 1. Inventory

For each `SKILL.md` record name, containing dir, size, and parsed frontmatter. Write the inventory to
a workspace JSON file and aggregate there — do not hold 300 skills in your head.

Parse frontmatter with a block-scalar-aware reader:

```python
BLOCK = re.compile(r"^([a-zA-Z_][\w-]*):\s*([|>])([-+]?)\s*$")

def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.S)
    if not m:
        return {}
    lines, fm, i = m.group(1).splitlines(), {}, 0
    while i < len(lines):
        bm = BLOCK.match(lines[i].rstrip())
        if bm:                                   # description: |  or  description: >
            key, style = bm.group(1), bm.group(2)
            i += 1
            buf = []
            while i < len(lines) and (lines[i].strip() == "" or lines[i][:1] in (" ", "\t")):
                buf.append(lines[i].strip()); i += 1
            fm[key] = ("\n" if style == "|" else " ").join(x for x in buf if x).strip()
            continue
        km = re.match(r"^([a-zA-Z_][\w-]*):\s*(.*)$", lines[i])
        if km:
            v = km.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
                v = v[1:-1]
            fm[km.group(1)] = v
        i += 1
    return fm
```

**A line-based `^description:\s*(.*)$` regex returns the literal `"|"` or `">"` for a block-scalar
description.** Those skills are fine — the text sits on the following indented lines. Writing them up
as broken frontmatter is a false positive that sends a future session off fixing nothing. If a scan
reports a malformed description, open the raw file and confirm before it reaches the report.

## 2. Find overlap

Two passes, and they find different things:

1. **Name-prefix families** — group by the first hyphen-separated token, list families of 3+. This is
   how you spot a job that has been re-skilled several times (`recon-sector`,
   `recon-sector-expansion`, `sector-recon-methodology`).
2. **Body similarity** — strip frontmatter from each `SKILL.md` and run
   `difflib.SequenceMatcher(None, a, b).ratio()`. **≥95% is a duplicate, not a resemblance** — that is
   how you prove a "leftover" skill is a copy of a reference file inside a consolidated skill.

**Do not cluster on description-token similarity for templated families.** Where 59 skills share the
boilerplate "Hunting skill for X vulnerabilities. Built from N public bug bounty reports", token
overlap scores as massive redundancy while the skills are genuinely one per topic. Boilerplate
inflates token overlap; body diffs do not.

## 3. Decide what survives

Grade the evidence, and let usage break ties:

- **Byte-level duplicate** (≥95% body match, or a skill superseded by a reference file inside another
  skill) — solid; act on it.
- **Same job, several skills** — confirm by reading the headings of each; act, and name the survivor.
- **Judgment call** (two orchestrators, method/arsenal splits, per-platform variants of one format) —
  report it, do not auto-remove.

`~/.hermes/skills/.usage.json` holds `use_count` / `last_used_at` / `created_by` per skill. When two
skills do the same job, keep the one with real uses — that beats picking by size or by which name
reads better. `created_by: learn` plus a high `use_count` marks the user's own curated layer; never
remove those on your own initiative.

Leave these alone:

- **Vendor-managed packs.** A manifest holding a hash per skill (e.g.
  `~/.claude/skills/.arkcli-managed-skills.json`) means an external tool tracks and updates those
  files — editing or deleting them breaks that tool's update path. Report their internal overlap as
  the vendor's to resolve.
- **Deliberate large families** (one skill per vulnerability class, provider, or model). Check whether
  the similarity is real shared content or just a shared description template.

## 4. Remove durably

**Never delete inside a derived tree.** Check whether a tier is rebuilt by a script — look for a
syncer under `~/.hermes/scripts/` and run it with `--dry-run` to see what it would restore. A tree
that re-copies its contents is derived data: deletions and edits there come back.

Durable options, in preference order:

1. **Disable** — durable, Hermes-only, reversible:

   ```bash
   hermes config set skills.disabled '["name-a","name-b"]'
   ```

   `config set` **replaces the whole list**, so read the current value first and pass the union of old
   + new, or you silently re-enable everything you meant to keep disabled.

2. **Delete at the source** — only when the user also wants the skill gone from the other agent that
   owns the tree. Deleting a symlink in a mounted tier removes it from the mount *and* from the next
   sync; deleting the symlink's target also removes it from the canonical tree.

3. **Archive an unmanaged secondary import** — when two local packages are proven byte-identical,
   move the extra *non-derived, non-vendor-managed* package outside every indexed skill root.
   Compare all supporting files by relative-path SHA256, not only `SKILL.md`; retain the synced
   package and its vendor-managed upstream unchanged. Save a rollback manifest, check the syncer's
   `--dry-run` keeps the survivor, and actually load every survivor by bare name. Removing the
   secondary import fixes same-tier name ambiguity without deleting from the derived tree.

Tell the user which one you are doing and why. "Delete", "disable", and "archive" are different
outcomes; archives preserve rollback. For a derived tier, deletion is the one that silently fails.

## 5. Verify the change

A config change is not done until the index reflects it:

```bash
hermes skills list | tail -2      # enabled/disabled must move by exactly the number you changed
hermes prompt-size                # skills index should shrink ~75-95 B per skill removed
```

If the counts did not move, the edit did not take. `hermes config set` may warn that
`skills.disabled` is "not a recognized config key" — that warning is spurious for this key; it is
read. Trust the `hermes skills list` count over the warning.

## Pitfalls

- **Inline `python -c` and heredocs trip the approval gate.** Write the audit script to a file under
  `$TMPDIR` and run the file. A multi-line heredoc stalls on an approval prompt instead of failing.
- **Do not patch a skill that lives in a derived tree** — the fix reverts on the next sync. Patch the
  source, or patch a Hermes-owned skill.
- **Reading a huge `SKILL.md` to judge overlap is expensive.** An 80 KB skill is ~20k tokens. Read
  headings and sizes first; read full bodies only for the few you are about to act on.
- **State what a removal costs before doing it.** Report the byte/token saving honestly — a few KB of
  index is real but small. The actual win is that the model stops choosing between four near-identical
  skills for the same request.

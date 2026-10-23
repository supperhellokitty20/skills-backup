#!/usr/bin/env python3
"""Reassemble headless-Ghidra println blocks from a captured console log.

Only the first line of a GhidraScript println carries the
`INFO <script>.java>` tag; the rest of the block (decompiled C, disassembly,
hexdumps) arrives untagged, so a grep for the tag returns headers with empty
bodies. This rebuilds the whole block per println call.

usage: extract_ghidra_log.py <input.log> <output.txt> [script-name-filter]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TAG = re.compile(r"^INFO\s+(\w+)\.java>\s?(.*?)\s*\(GhidraScript\)\s*$")


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    src = Path(sys.argv[1]).read_text(errors="replace").splitlines()
    keep_only = sys.argv[3] if len(sys.argv) > 3 else None

    blocks: list[str] = []
    cur: str | None = None

    def flush() -> None:
        nonlocal cur
        if cur is not None:
            blocks.append(cur)
            cur = None

    for line in src:
        m = TAG.match(line)
        if m:
            flush()
            if keep_only is None or keep_only in m.group(1):
                cur = m.group(2)
            continue
        if line.startswith("INFO "):
            # Any other Ghidra message ends the current block.
            flush()
            continue
        if cur is not None:
            cur += "\n" + re.sub(r"^INFO\s+", "", line)

    flush()
    Path(sys.argv[2]).write_text("\n".join(blocks) + "\n")
    print(f"blocks={len(blocks)} -> {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

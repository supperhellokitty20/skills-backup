#!/usr/bin/env python3
"""Find which functions write a struct field, by displacement.

Static identification of the object type behind a field: disassemble every
function listed in a Ghidra inventory dump and report the ones whose stores
touch the requested displacements. The set of displacements the dispatcher
reads is the fingerprint that picks out the initializer of that object.

Prereq: pip install capstone   (or point PYTHONPATH at a capstone install)

usage: field_store_scan.py <image.bin> <base-hex> <func-dump.txt> <disp,...>
  image.bin      reconstructed image whose file offset 0 maps to <base-hex>
  func-dump.txt  Ghidra inventory lines such as:
                   F FUN_0800a5c0   entry=800a5c0 size=0xa2 thunk=false
  disp           comma-separated hex displacements, e.g. 0x1c,0x28,0x30
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

import capstone  # noqa: F401  (fail fast with a clear ImportError)
from capstone import CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB, Cs

ENTRY = re.compile(r"F (\S+)\s+entry=([0-9a-fA-F]+)\s+size=0x([0-9a-fA-F]+)")
STORE_DISP = re.compile(r"\[r\d+, #(0x[0-9a-fA-F]+)\]")


def main() -> int:
    if len(sys.argv) < 5:
        print(__doc__)
        return 2
    image = Path(sys.argv[1]).read_bytes()
    base = int(sys.argv[2], 0)
    funcs = [
        (int(m.group(2), 16), int(m.group(3), 16), m.group(1))
        for m in ENTRY.finditer(Path(sys.argv[3]).read_text(errors="replace"))
    ]
    want = {int(x, 0) for x in sys.argv[4].split(",")}
    if not funcs:
        print("no function entries parsed from the dump; check the format")
        return 1

    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    rows = []
    for entry, size, name in funcs:
        code = image[entry - base:entry - base + size]
        hits: dict[int, int] = defaultdict(int)
        for ins in md.disasm(code, entry):
            if not ins.mnemonic.startswith("str"):
                continue
            m = STORE_DISP.search(ins.op_str)
            if m:
                disp = int(m.group(1), 16)
                if disp in want:
                    hits[disp] += 1
        if hits:
            rows.append((len(hits), name, entry, size, dict(sorted(hits.items()))))

    rows.sort(key=lambda r: (-r[0], r[2]))
    for ndisp, name, entry, size, hits in rows:
        pretty = {hex(k): v for k, v in hits.items()}
        marker = "  <== touches several fields of one object" if ndisp >= 2 else ""
        print(f"{name}@{hex(entry)} size=0x{size:x} fields={pretty}{marker}")
    print(f"functions parsed={len(funcs)} with hits={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Memory-corruption hunting in a reconstructed Cortex-M image

Applies once the sparse map is verified and the image is imported at canonical addresses. The goal is to decide whether an unchecked length, index, or pointer yields memory corruption or control-flow control, and to report the reachability chain honestly.

## Order of work

1. **Find the inbound transports first.** Locate the ring-buffer/queue primitives (`available = head - tail` style readers, consume/advance helpers, DMA-completion writers). Every finding needs a path from bytes on the wire to the buggy call, so establish the byte-arrival path before auditing parsers.
2. **Locate the frame dispatcher.** It is usually one function that syncs on a fixed byte, reads a fixed-size header into a stack buffer, calls a per-class parse function pointer that returns a declared length, compares that length against a per-object limit, copies the frame onto the stack, then calls a per-class handler. Recognize it by the `mov rX,sp` plus `bl <ring_read>` pair.
3. **Map the dispatch tables.** Function-pointer tables are frequently initialized data in RAM, not flash constants — see the blind spot section below.
4. **Enumerate table-dispatched handlers** with `scripts/OrphanFuncs.java`.
5. **Identify the object types** the handlers touch with `scripts/field_store_scan.py`.
6. **Resolve every limit and every index to its writer.** A guard is only as strong as the value it compares against.
7. **Report the chain**, labelled per link.

## The RAM-initialized-data blind spot

A flash literal pool can hold a RAM address (`0x2000xxxx`). The image has no memory block for RAM, so:

- reference queries for those addresses return nothing;
- the decompiler renders the table as a bare base plus scaled index, which looks like a static array in RAM;
- the table contents live in the scatter-decompressed init region and are **not** in the supplied file.

Recover the readers by byte-searching the image for the little-endian RAM address. Each hit is a literal pool; run `scripts/Xrefs.java` on the pool address to get the readers, and read each reader's containing function.

Distinguish single from double indirection before calling something an array base: a pool value loaded and then dereferenced is a pointer cell, while a pool value used directly as a base is the array itself. Two pool values a few bytes apart are separate objects, not adjacent array elements.

Because the table body is unavailable, derive its length from code: a count copied into a registration object, a `cmp` bounding the registration loop, or an initializer that iterates a fixed number of entries. State the derived bound as an inference, not as bytes seen.

## Recognition patterns

**Declared length copied to a stack frame.**

```asm
sub  sp,#0x12c            ; frame size
tst  ...                  ; guards: len >= header_size, len <= *(u16*)(object + disp)
mov  r1,sp                ; dest = frame base
ldr  r2,[sp,#...]         ; len = declared frame length
bl   <ring_read|memcpy>
```

Saved registers sit above the frame (pushed words) and the saved return address at `frame_size + 4 * pushed_words`. The copy is only safe while the guard's limit stays below that offset — so resolve the limit field.

**Unchecked index into a 3-pointer table.**

```asm
ldrb r0,[r4,#0x8]         ; index, full byte, no cmp/cmn before use
add  r0,r0,r0,lsl #0x1    ; index * 3
add  r0,rT,r0,lsl #0x2    ; table + index * 12
ldr  r3,[r0,#0x4]         ; entry field
tst  r3,r3
blx  r3                   ; indirect call
```

Entry stride 12 with call sites at `+0`, `+4` and `+8` means each table entry is three function pointers (parse / encode or send / handler). Absence of a compare between the load and the `blx` is the finding.

**Register-based object access.** Stores to small positive displacements on a pointer register (`[r4,#0x1c]`, `[r4,#0x28]`, `[r4,#0x30]`) identify the object; the dispatcher's field displacements are the fingerprint that tells you which initializer creates it.

## Guard-provenance checklist

- Who writes the limit field? (`scripts/field_store_scan.py`)
- What values does that writer store? Mode switches commonly store buffer sizes in the 0x400-class — far above a few-hundred-byte stack frame.
- Is the same field used elsewhere as a boolean or flag? Mixed-use fields defeat the guard.
- Can the value be set before the frame arrives, or is it fixed at init?
- Compute the reachable offset: `frame_size + 4 * pushed_words`, then compare with the largest value the guard admits.

## Reporting exploitability without a device

- Present the chain as steps, each labelled verified or inferred. Never compress it into "RCE is possible".
- Separate denial-grade from control-grade: an unvalidated pointer read that branches into heap data is a crash; attacker bytes landing on a saved return address or on a called pointer is control.
- Name exactly what would confirm the unverified links and what dynamic confirmation requires (instrumented harness or emulator with a shim for the transport, or the board).
- Do not present a static pattern as a demonstrated exploit, and do not let a plausible but unverified mid-chain link carry a critical severity label.
- Keep the two bug classes separate in the write-up so a triager can see which is which.

## Tooling pitfalls

- Only the first line of a headless-Ghidra `println` carries the `INFO <script>.java>` tag, so line-filtered extraction yields headers with empty bodies. Use `scripts/extract_ghidra_log.py`.
- Run several small `-postScript` passes against the existing project instead of one giant script: a single timeout otherwise loses the whole pass. Redirect each pass to a `.log` and derive a `.txt` to cite.
- Keep using the corrected sparse project; a decompile from a superseded flat project produces plausible code at wrong addresses and will waste the whole pass.

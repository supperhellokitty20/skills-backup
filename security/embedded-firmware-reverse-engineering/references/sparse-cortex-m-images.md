# Sparse Cortex-M image reconstruction

## Detect the problem

Suspect a sparse/package layout when any of these disagree:

- Reset vector minus proposed base points into data or an unrelated function.
- Metadata contains absolute self-pointers that resolve under a different base.
- Vector handlers cluster in one runtime range while metadata is inserted elsewhere in the file.
- Scatter-loader source addresses extend beyond the end of a flat import but fit after section relocation.
- Several candidate bases each explain only one anchor.

Clean Thumb disassembly is weak evidence. Cortex-M binaries contain dense halfwords, literal pools, tables, and embedded records that decode plausibly by accident.

## Establish independent anchors

Collect at least three:

1. Initial SP falls in plausible SRAM.
2. Reset vector has the Thumb bit set and lands on a valid reset veneer.
3. Reset sets VTOR to the proposed vector address or otherwise confirms vector placement.
4. ARM scatter-loader table points to valid flash sources and SRAM destinations.
5. Metadata absolute references land on the metadata record.
6. BSS end equals or closely explains the initial SP.
7. Runtime literals and function pointers resolve inside reconstructed sections.

## Reconstruct sections

Represent each section as:

```text
source_start, source_end, runtime_start, role
```

For a source offset `o` inside a section:

```text
runtime = runtime_start + (o - source_start)
```

Build one derived binary spanning `min(runtime_start)` through the maximum mapped end. Fill holes with `0xff` for flash-like gaps unless evidence requires another value. Emit a JSON map containing source ranges, runtime ranges, fill byte, hashes, and validation anchors.

Never overwrite the raw input. Name derived images with their base, for example `firmware-sparse-08006400.bin`.

## Recognize ARM scatter loading

A common table is a sequence of four little-endian words:

```text
load/source address
execution/RAM address
length
handler address
```

Typical handlers copy initialized data, decompress runtime data, and zero BSS. Validate that:

- Source addresses lie in mapped flash/load sections.
- RAM ranges are contiguous or structurally sensible.
- Handler addresses resolve to executable Thumb functions.
- The final zeroed range ends at the initial stack pointer when the linker layout uses the top of static RAM as stack start.

That end-equals-SP relation is a strong map validator, not merely an aesthetic coincidence.

## Nested images

A package can store a second Cortex-M image inside the outer image while the inner image is linked at zero or another unrelated base. Detect it by a second plausible SP/reset pair, local vectors, local metadata, and reset code writing a different VTOR.

Slice and import the inner image separately. Describe both:

- Outer storage address or file offset.
- Inner linked/runtime base.

Do not assume storage address equals execution address. Trace copy, remap, mailbox, or handoff code separately.

## Ghidra procedure

1. Import the reconstructed file with the proper ARM Cortex language and image base.
2. Run analysis and dump memory blocks, function count, strings, references, and pointer tables.
3. Decompile reset, scatter handlers, metadata reporters, crypto wrappers, flash paths, and peripheral setup.
4. Keep old flat projects as provenance, clearly marked obsolete.
5. Correct function labels by source-offset mapping only after the sparse map is verified; rerun decompilation at canonical addresses.

## Verification script checks

A deterministic verifier should assert:

- Original hash and size.
- Every source-to-runtime byte placement.
- Hole fill and derived image size.
- SP/reset words.
- Reset source offset and target bytes.
- Scatter table exact words.
- Metadata magic/tag/version anchors.
- BSS end versus initial SP.
- Nested-image boundary, vectors, and metadata.

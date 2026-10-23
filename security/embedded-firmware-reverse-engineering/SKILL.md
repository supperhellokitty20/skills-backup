---
name: embedded-firmware-reverse-engineering
description: Use when analyzing embedded OTA or firmware binaries.
version: 1.0.0
author: skii, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [firmware, ota, cortex-m, ghidra, reverse-engineering, sparse-image]
    related_skills: [bb-workspace-layout, verification-before-completion]
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/cortex-m-vuln-hunt.md`, `references/ota-container-trust-analysis.md`, `references/sparse-cortex-m-images.md`, `scripts/OrphanFuncs.java`, `scripts/Xrefs.java`, `scripts/extract_ghidra_log.py`, `scripts/field_store_scan.py`, `templates/architecture-report.md` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# Embedded Firmware Reverse Engineering

## When to Use

- OTA archives, signed firmware containers, raw microcontroller binaries, or nested firmware images
- Cortex-M vector tables, reset targets, metadata, or absolute pointers disagree about the load base
- Ghidra produces plausible code but address-sensitive evidence conflicts
- Update signatures, digest scopes, encryption framing, or transitive manifest coverage must be documented
- Hunting memory-corruption or control-flow bugs in an already-reconstructed image (unchecked lengths, table-index dispatch, indirect calls)

Do not use for APK-only reversing, source-available application review, or live hardware exploitation without a supplied firmware corpus.

## Core principle

Prove the packaging and memory model before interpreting code. Plausible disassembly at one address is not evidence of the correct load base.

**REQUIRED COMPANION:** For bug-bounty projects, use `bb-workspace-layout` and preserve raw evidence before transformation.

## Workflow

1. **Freeze the corpus.** Hash and size every original; extract into a separate directory. Record scope and exclusions. Never modify supplied artifacts.
2. **Model the containers first.** Inventory every archive entry, parse fields by offset, determine exact digest scopes, and build the manifest/hash/signature graph. Verify every claimed digest programmatically.
3. **Classify payloads.** Separate plaintext records, encrypted/opaque regions, raw binaries, metadata, and nested images. Measure entropy and block properties without naming a cipher from shape alone.
4. **Establish the memory map.** Test vector tables, stack/reset plausibility, absolute literals, metadata references, scatter tables, and nested-image vectors together. Require multiple independent anchors before declaring a base. If anchors conflict, reconstruct a sparse image rather than forcing a flat import.
5. **Analyze corrected images.** Import reconstructed images into Ghidra, keep nested processors as separate programs, and trace reset → initialization → scatter loading → runtime entry. Preserve wrong-base projects only as negative-control provenance; never cite their addresses as canonical.
6. **Adjudicate functional claims.** Correlate decompilation, strings, MMIO literals, call references, and table structure. Treat strings as compiled capability, not proof the feature is active or exposed.
7. **Verify before reporting.** Add a deterministic verifier covering hashes, section placement, vectors, scatter entries, metadata anchors, and trust-graph totals. Rerun it after the report is finalized.

## Report contract

Deliver:

- Exact container and sparse-memory tables.
- Reset/startup and RAM initialization paths.
- Peripheral/runtime/update/crypto interfaces.
- A trust graph distinguishing content binding from authenticated verification.
- `Verified`, `Strong inference`, and `Open` labels.
- For exploitability questions: a step-by-step reachability chain with each link labelled, naming the exact evidence that would settle the unverified links.
- Between long extraction passes, a short status line: what is verified, what is still open, the next step.
- Canonical artifact paths and verifier result.
- Explicit corrections when delegated or preliminary analysis used a wrong base.

## Non-negotiable pitfalls

- Do not select a base because bytes decode cleanly; Thumb code often looks plausible at wrong offsets.
- Do not infer RSA from a 256-byte blob, hardware AES from missing S-boxes, or active debug access from SEGGER strings.
- Do not call a raw artifact unauthenticated until checking transitive manifest/package bindings.
- Do not interpret anti-rollback-looking fields as enforced policy without locating the enforcement path.
- Do not let a subagent's confident architecture claim override byte-level contradictions; reconstruct and verify independently.
- Before calling a length-bounded stack copy an overflow, trace the *parser* that supplies the length. The dispatcher's own check (e.g. a port max-frame fieldset to 0x400) is often not the effective bound: each protocol class parser may cap the value below the frame size, and the copy is then safe by design. A stack-overflow claim that skips the parser is a false positive — retract it explicitly when disproved.
- Bound an unvalidated table-index finding honestly: an index with no range check is an unvalidated indirect call (DoS class) until you demonstrate an attacker-controlled index value reaching it. If the table lives in scatter-decompressed RAM init data you cannot read, state that limit instead of guessing the table length.
- Record whether an MPU is configured (scan for 0xE000ED90..0xE000EDA0, VTOR, AIRCR, CPACR literals) as part of exploitability context: no MPU plus no canary plus fixed flash addresses means any proven corruption is trivially exploitable — and is what makes chasing the *update/flash* path worthwhile.
- A length check is not a mitigation until you locate the writer of the limit field: a field set to a buffer size can authorize frames far larger than the destination stack buffer.
- Function-pointer tables are often initialized data in RAM, where the image has one indirection and reference queries return nothing; recover their readers by byte-searching the image for the little-endian RAM address and resolving each literal pool.
- Functions with no incoming call or jump references are usually table-dispatched, not dead; enumerate them before declaring a handler unreachable.
- Judge an indirect call by whether a bound is enforced between the index load and the `blx`, not by whether the index looks small in the one caller decompiled so far.
- Headless Ghidra `println` blocks lose their bodies under line-based log filtering: only the first line carries the script tag.

## Deep references

- Read `references/sparse-cortex-m-images.md` when vectors, metadata, reset targets, or Ghidra bases disagree.
- Read `references/ota-container-trust-analysis.md` for BIMH-like containers, signatures, encryption classification, and transitive authentication.
- Read `references/cortex-m-vuln-hunt.md` when asked whether the firmware is exploitable: inbound transport and dispatcher recovery, unchecked-length and table-index patterns, guard provenance, and how to report exploitability from static analysis alone.
- `scripts/` holds re-runnable helpers: `Xrefs.java` and `OrphanFuncs.java` (headless Ghidra), `extract_ghidra_log.py`, `field_store_scan.py`.
- Start reports from `templates/architecture-report.md`.
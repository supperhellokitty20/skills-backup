# Embedded firmware / OTA architecture report

## Scope and corpus

- Input:
- Size:
- SHA-256:
- Analysis boundaries:
- Original preservation statement:

## Executive architecture

Summarize package layers, processors/modules, trust boundaries, and the most important verified correction.

## Artifact inventory

| artifact/class | count or version | plaintext/encrypted/raw | role | confidence |
|---|---:|---|---|---|

## Container format

### Outer header

| offset | width/type | verified meaning | validation |
|---:|---|---|---|

### Inner/plaintext record

### Encrypted/opaque region observations

### Signature field and limits

## Manifest and trust graph

```text
root
  └── child digest bindings
      └── module bindings
```

List passing/expected counts and distinguish content binding from authenticated signature verification.

## Firmware memory maps

For each processor/image:

| source file range | runtime/storage range | role |
|---|---|---|

State obsolete flat-base interpretations explicitly.

## Reset and startup

- Vector base:
- Initial SP:
- Reset vector/target:
- VTOR behavior:
- Initialization calls:
- Scatter-loader entry and handlers:

## RAM initialization

| load/source | RAM destination | size | handler/action |
|---:|---:|---:|---|

Validate BSS end against initial SP.

## Runtime and peripherals

Cover RTOS/runtime, MMIO families, transport, flash/NVM, callbacks, diagnostics, and metadata reporting. Label each claim Verified, Strong inference, or Open.

## Cryptographic interfaces

Separate visible wrappers from external callbacks. State what tables/constants/verifiers were and were not found without treating absence as proof.

## Nested images

Document package offset, outer storage address, inner linked base, local vectors, handoff evidence, and unresolved copy/remap behavior.

## Security assessment

### Verified

### Strong inference

### Open

## Reproducibility

List parsers, reconstructors, Ghidra projects, raw evidence, independent review, and deterministic verifier output.

## Remaining questions

Order by the evidence likely to resolve each question.

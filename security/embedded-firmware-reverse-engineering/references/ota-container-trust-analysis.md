# OTA container and trust analysis

## Inventory before interpretation

For every archive entry record:

- Host filename, size, archive method, and full-file hashes.
- Magic/version and declared size.
- Header, signature, payload, and encrypted-region offsets.
- Embedded names separately from host filenames.
- Plaintext/encrypted/raw classification.

Check declared ranges before slicing. Reject unknown flags instead of silently treating them as plaintext.

## Determine digest scope empirically

For each candidate digest field, compute hashes over explicit ranges:

- Whole file.
- Header excluding the digest/signature.
- Payload record.
- Opaque region.
- Plaintext payload.

State the exact matching byte interval. “Integrity hash” without a scope is incomplete.

For plaintext records, verify length, offset, bounds, reserved fields, digest, and exact tail length. For encrypted regions, do not parse random ciphertext bytes as record fields.

## Signature discipline

A fixed-size blob proves only its length and uniqueness. It does not establish:

- RSA versus another scheme.
- Key size or curve.
- Padding.
- Signed-message encoding.
- Trust anchor identity.
- Successful device verification.

Use “signature blob” until the public key/verifier or a successful independent verification establishes more.

## Encryption classification

Measure:

- Shannon entropy.
- Length modulo common block sizes.
- Repeated full blocks.
- Stable prefixes/suffixes across versions when available.
- Whether framing bytes exist outside the opaque body.

Report observations, not cipher names. No repeated blocks and high entropy are compatible with many constructions. Non-block-aligned lengths may indicate framing, stream/AEAD behavior, ciphertext stealing, or a custom transform.

## Build the trust graph

Separate these concepts:

- Content binding: a manifest digest matches a target.
- Package coverage: a root list hashes child artifacts.
- Signature-bearing envelope: a blob exists alongside a digest.
- Authenticated verification: independently proven with a trusted key.

A raw child can be transitively covered by hashes in signed parents even without its own envelope. Phrase authenticity conditionally when the parent signature cannot be verified.

Example graph:

```text
root envelope
  └── strong digest of child outer files
      └── child manifest
          └── legacy or secondary digest of module artifact
```

Verify every edge programmatically and count expected versus passing edges. Filename agreement is part of the edge: preserve host and embedded-name differences rather than normalizing them away.

## Version and rollback claims

Record version tuples and ordering. Do not equate fields named `lower_limit`, `anti`, `rollback`, or similar with enforcement. Enforcement requires a code path, bootloader behavior, or controlled runtime evidence.

## Deterministic audit output

Emit machine-readable JSON containing:

- Per-file parsed fields and computed hashes.
- Per-edge expected/actual digest and match status.
- Plaintext/encrypted totals.
- Signature lengths and uniqueness.
- Name mismatches.
- Version observations.
- Final count assertions.

The report must cite the canonical audit output and exclude empty, stale, or exploratory parse files.

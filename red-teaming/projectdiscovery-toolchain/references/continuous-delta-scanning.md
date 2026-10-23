# Continuous delta scanning (new-asset × new-template)

A scheduled-scan architecture for a monitored scope. It avoids the trap of re-running the full
template set against the full asset list on every tick, which is what makes most "continuous
monitoring" setups either unaffordable or quietly throttled down until they stop finding anything.

## The problem it solves

Asset count `A` × template count `T` grows multiplicatively. With a few thousand subdomains and the
full nuclei template set, one complete pass is millions of requests — beyond any program's rate
policy, and slow enough that the results are stale before the run ends.

But the full cross-product only needs computing **once**. After that, only two things ever change:

- a **new asset** appears → it has been tested by *no* template
- a **new template** appears → it has tested *no* asset

Everything else was already covered by a previous run.

## The two triggers

| Trigger | Targets to scan | Templates to use |
|---|---|---|
| New subdomain found | only the **new** subdomains | **all** existing templates |
| New template added | **all** existing subdomains | only the **new** template(s) |

This keeps per-tick cost roughly linear (`new_A × T` or `A × new_T`) instead of quadratic, while
guaranteeing every asset is eventually tested by every template.

## Change detection

Keep the discovery output as an append-only asset file. On each tick, hash the file and compare to
the hash stored from the previous tick:

- hashes equal → nothing new → exit without scanning
- hashes differ → diff against the previous snapshot to get the **new lines only**, then scan those

Hash the *sorted, deduplicated* file, not raw tool output — subfinder/dnsx ordering varies between
runs and will make an unchanged scope look changed on every tick. Diff to get the delta; do not feed
the whole file to nuclei just because the hash moved.

Apply the same pattern to the template directory: hash the template tree, and on change scan the
full asset list with `-t` pointed at only the changed template files.

## Sketch

```sh
# --- asset delta ---
sort -u live-hosts.txt > assets.cur
h_new=$(shasum -a 256 assets.cur | cut -d' ' -f1)
h_old=$(cat .assets.hash 2>/dev/null)
if [ "$h_new" != "$h_old" ]; then
  comm -13 assets.prev assets.cur > assets.delta   # new names only
  [ -s assets.delta ] && /Users/skii/go/bin/nuclei \
      -l "$PWD/assets.delta" -rl 8 -jsonl -o "$PWD/scans/delta-assets.jsonl"
  cp assets.cur assets.prev; printf '%s' "$h_new" > .assets.hash
fi

# --- template delta ---
h_tpl=$(find templates -type f -name '*.yaml' -exec shasum -a 256 {} + | shasum -a 256 | cut -d' ' -f1)
if [ "$h_tpl" != "$(cat .tpl.hash 2>/dev/null)" ]; then
  /Users/skii/go/bin/nuclei -l "$PWD/assets.cur" -t "$PWD/templates/new/" \
      -rl 8 -jsonl -o "$PWD/scans/delta-templates.jsonl"
  printf '%s' "$h_tpl" > .tpl.hash
fi
```

Absolute paths for `-l`, `-t` and `-o` are mandatory here — a cron job's CWD is not your shell's,
and a relative `-o` into a missing directory makes nuclei die with `could not create output file`
while the wrapper reads as "0 findings". See the toolchain's Pitfalls.

## Pitfalls

- **A hash change is not an asset delta.** Unsorted or non-deduplicated output changes the hash on
  every run; scanning the whole file each time is exactly the quadratic cost this design avoids.
  Sort, dedupe, then `comm`/`diff` for the actual new lines.
- **A silent cron has no failure signal.** A job whose nuclei invocation dies on a bad flag, a
  missing output directory or an unreachable resolver produces an empty findings file that reads
  identically to "nothing found". Log exit codes, alert on non-zero, and alert on *zero runs* as
  well as on zero findings.
- **The rate limit is per program, not per cron tick.** Two triggers firing in the same tick stack
  their request budgets. Serialise the asset-delta and template-delta runs, or the aggregate rate
  silently doubles.
- **Never let the scope file grow unfiltered into the scanner.** `dnsx -json` emits `NXDOMAIN` rows
  and the asset file inherits dead names forever. Filter on `NOERROR` plus a non-empty `a` before
  the file becomes the monitored artifact.
- **Scope drift.** An asset file that only ever appends keeps scanning hosts that have left the
  program's scope. Re-validate against the current scope on a slower schedule and prune.
- **The architecture has no result sink by default.** Decide up front where findings go (notify, a
  tracked file, an issue). An unattended scanner whose output nobody reads is a rate-limit liability
  with no upside.
- **Unattended scanning needs standing authorization.** A continuous job keeps sending traffic after
  the session that started it ends, and after a program's scope changes. Confirm the program permits
  automated recurring scanning, and put a kill switch on the job.

## Provenance

Pattern derived from The XSS Rat's public `SecurityTesting` repository, `notes/Broad scope
methodology - Manual`, diagrams `vulnerability_scanning_(1).png` and `Nuclei_scanning.png`
(commit `a68ec21`, read 2026-10-14). The sorted-hash correction, serialisation rule, silent-failure,
scope-drift and standing-authorization pitfalls are this skill's own.

# RR-COREXTRACT-20261025 — rust CLI run cores → `ctxvm-conformance::cli` (byte-neutral extraction)

Card **COREXTRACT** (design/uc1-plugin.md §6 beat "B1-CORE"), author lane: kapitaali.
**DONE — ALL GATES GREEN witnessed** at this tree (full run-ci.sh fresh run, see §Gates).

## What landed

- `rust/crates/ctxvm-conformance/src/cli.rs` (NEW, 1030 lines): the four CLI run cores
  `replay_core` / `profile_core` / `diff_core` / `export_core` plus the previously
  bin-local helpers (parse_pin/build_pins/resolve_pins/pin_label, declared_refs/
  declared_identities, EVENT_TYPES/SOURCES/SOURCES_STR/parse_source, Artifact,
  SessionHeader, y, verify_lines, kpi_value, manifest_yaml, llms_txt) that were scattered
  across `src/bin/*.rs` (old: replay 329 / profile 295 / diff 130 / export 629 lines).
  `lib.rs` gains `pub mod cli;` (+5 lines).
- The four binaries are now thin mains: verbatim parse_args/help strings + one
  `cli::*_core` call + `print!`/`eprint!` + `ExitCode::from(outcome.exit)`.
- `CliOutcome { exit: u8, stdout: String, fatal: Option<String>, warnings: Vec<String> }`;
  `stderr_text(bin)` reproduces exact CLI stderr (`ctxvm <bin>: ` prefix for the fatal
  path, `warning: ` lines for non-fatal warnings). `stdout` == the file bytes in
  `--output` mode (single `body.push('\n')` site). The classic replay report keeps its
  direct struct serialization (`to_string_pretty(&report)` — NOT `to_value` — key order
  preserved); the diff note string is constant regardless of output mode; export DQ
  failures stay stderr-only warnings; the `missing --output DIR` guard stays in both the
  bin (argv path, pre-IO order) and the core (typed path).
- Tests: none added — the card is count-neutral BY DESIGN (proof is external, below):
  `cargo test` 52 passed / 12 suites / 0 warnings, identical before and after.

## Why

Org decision "engine logic converges on shared bindings": every port (the CLI thin
mains, the ctxvm-py subprocess wrapper, any future PyO3 native binding, the @ctxvm/node
golden tests) now bytes-match because all drive the same serialization/exit-code sites,
not because tests happened to agree. The cost of a future PyO3 upgrade is reduced to a
thin `#[pyfunction]` shell over the four cores.

## Byte-neutral proof (evidence under /tmp/opencode/b1/, commands in §Reproduce)

- Baselines captured BEFORE the refactor from the unrefactored release binaries: 16 CLI
  cases (replay/profile/diff over corpus m1/m2 anchors incl. error paths:
  `/tmp/opencode/b1/base/{00..15}.{stdout,stderr}` + manifest.json) and two export
  artifact trees (plain + `--odps`; `export-tree.sha256`, 7 files).
- Reference binaries: a scratch build of git HEAD sources (`git archive` into
  /tmp/opencode/b1/old with its own CARGO_TARGET_DIR) — the working-tree build is the
  extraction. Driver: `/tmp/opencode/b1/compare.py`.
- **61 cases old-vs-new byte-identical** (stdout bytes, stderr bytes, exit code) = the
  16 captured baselines + 4 help texts + 41 argv/error-path edges (missing values,
  empty/eq-form flags, unknown flags, second/third positionals, undeclared pins,
  malformed pins, taxonomy/vocabulary errors, not-found and parse-error files,
  `--pin`-without-`--turn` ordering including the corrupt-file combination, missing
  `--output`…). The 16 baseline cases also re-verified byte-for-byte against the
  captured pre-refactor files. Export: trees byte-identical old-vs-new AND
  hash-identical vs the baseline `export-tree.sha256` (all 7 `--odps` files incl. the
  zstd frame, both plain files); stdout only differs by the output-dir path constant,
  normalized in the driver.
- Result line: `RESULT: PASS — 61 cases + 16 baselines + 2 export trees byte-identical
  (old vs new; new vs baseline); 1 accepted divergence(s)`.

## Behavior notes (disclosed, no silent changes)

1. **Latent bug fix — the only old-vs-new divergence on the whole matrix:**
   `ctxvm profile --event=<bogus>` used to exit 0 silently (the eq-form never validated;
   the flag-form `--event bogus` always did). The shared core validates the flat event
   list uniformly, so both forms now exit 2 with the same message. A flat typed list
   cannot know its argv form, so the old inconsistency was not preservable through a
   shared core; the withdrawn surface is an undocumented error path, not a published
   payload. No existing test relied on it (their 8 binding tests are flag-form only).
2. **Argv-order restoration:** the old CLI validated `--turns` at parse time (argv
   order); a core-only design would silently reorder multi-error cases (`--turns bogus
   --event bogus.type` answered the turns error first before the extraction). The thin
   main validates `--turns` at parse via the same `ctxvm_core::turn_windows` function
   (result discarded; the core re-validates for typed callers) — one truth, twice
   called, argv-order parity kept. Other flags (events/source validation, replay pin
   guard order: read → parse → pin guard → report) already matched and are covered by
   the 61-case matrix.

## Collision note (lane protocol)

The hermes lane committed UC1-PLUGIN B1 (`packages/py` subprocess wrapper, `c2be33d`,
16:32:53) while this card was mid-proof; it did NOT touch `rust/` (my five modified
files + this new one were untouched; no sweep). **Orchestrator ruling this session:**
their binding stands as THE python port (user choice A; one port per harness), PyO3 is
de-scoped to an API-stable future upgrade (`design/uc1-plugin.md` §6/§7.2 updated
accordingly), and the extraction lands standalone. Facts flagged for their lane
(nothing altered by me): their §5 row says "hermes 43→52 tests" and "count 52→60" but
the hermes suite measures **51 passed** (same 7- vs 9-test pause arithmetic class as
flagged in RR-UC2-MIRROR); run-ci's count text "51 + 27 + 8" is truthful for 51 and 8
but stale for benchmarks/metrics — it actually passes **30** (three gate-2b tests added
with UC3-WINDOWSHEET; count line not updated). Suggested true-up on their next
bookkeeping pass: run-ci line "51 + 30 + 8", row/hermes count 51 (total 59).

## Gates

`tools/run-ci.sh` **ALL GATES GREEN** fresh witness at this tree: rust `cargo test`
52/52 (12 suites, 0 warnings), gate 1b release binaries clean, ts **12 + 21**, hermes
**51** + metrics **30 actual (line says 27 — flagged, not fixed)** + binding **8**,
schema 515 checks / 21 fixtures + export round-trip green, hub byte-identity green.

## Reproduce

```
# reference binaries from HEAD (never touches the working tree)
git archive HEAD rust | tar -x -C /tmp/opencode/b1/old
CARGO_TARGET_DIR=/tmp/opencode/b1/old-target cargo build --release \
  --manifest-path /tmp/opencode/b1/old/rust/Cargo.toml
# baseline capture + 61-case byte compare driver (case list inline)
python3 /tmp/opencode/b1/compare.py
```

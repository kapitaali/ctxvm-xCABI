# RR-UC2REPLAY — T16: replay CLI forensic surfaces (`--turn` / `--pin` / `--output`)

- **Card:** T16 (user-directed 2026-10-24, follows RR-UCVERIFY delta class F — UC2 build-first verdict) · **Status:** DONE
- **Date:** 2026-10-24 · **Repo:** ctxvm (`main`; follows `3b9b480` RR-UCVERIFY) · **Spend:** USD 0 (local build only)
- **Depends:** RR-UCVERIFY-20261024 (errata class F: memos cite `--turn/--pin/--output`; CLI had exactly one positional)

## 1. What this card added

### ctxvm-core (4 new unit tests; 11 → 15)

1. **`replay::replay_turn(trace, turn)`** — point-in-time replay: fact-check restricted
   to the facts recorded **at `turn`**; decision-ledger `violations` still cover the
   whole stream (the table must advance to end state because `mode_at` reads the
   final schedule). Shares one `check_facts` core with `replay(|_| true)`; the full
   `replay` API and shape are untouched.
2. **`render::TurnProjection::with_forced_resident(&BTreeSet<String>)`** — counterfactual
   force-resident overlay: in this projection — only — flip every **Stub** slot whose
   `logical_ref` matches to Full (stub text dropped) and re-tally from the flipped
   slots. Facts and violations are untouched; one ref flips every content-hash
   variant that is stubbed at that turn. Returns `(projection, Vec<ForcedResident>)`
   (`page`, `tokens` of each flip).
3. Exports: `replay_turn`, `ForcedResident` added to the crate root.

### `replay` CLI (`rust/crates/ctxvm-conformance/src/bin/replay.rs`)

```
replay <session.jsonl>                          # unchanged: full-trace fact check
replay <session.jsonl> --turn N                 # facts at turn N + turn-N projection
replay <session.jsonl> --turn N --pin <ref>...  # counterfactual force-resident overlay
replay <session.jsonl> ... --output FILE        # report JSON → FILE (stdout silent)
replay --help                                   # exits 0
```

- Report shapes: no-flags keeps the exact classic shape `{events, divergences,
  violations}` (struct serialization, field order and bytes unchanged); `--turn`
  extends with `turn` and `projection`; `--turn --pin` adds `pins` (normalized refs)
  and `forcedResident`.
- `--pin <ref>` matches by exact logical_ref; the memo-style `page:<ref>` form is
  accepted (stripped). Unknown ref → exit 2 listing the declared refs (sorted,
  unique). `--pin` without `--turn` → exit 2 (the overlay is per-turn).
- Exit contract unchanged: 0 = divergences-free within the checked scope (with
  `--turn`: that turn's facts only), 1 = divergences, 2 = usage/IO/parse.

### Docs

- `00-README.md` `rust/` row: flags + honest test count (33 workspace).
- `08-HANDOFF.md` §5 board: T16 row (T13/T14/T15 remain reserved to the umpire/
  adapter workstreams — untouched).

## 2. Semantics contract (locked for v0)

| Question | Answer |
|---|---|
| What does `--pin` prove? | **Visibility only**: the listed ref *could* have been seen at turn N (stub → where full content would have been). Not correctness — that requires re-running the model (UC2 §3 honest limit, quoted in the memo; unchanged). |
| Can `--pin` rewrite facts? | No. `divergences`/`violations` are always computed from the real (unpinned) schedule; the overlay affects only the `projection` block. |
| Which slots flip? | Only slots that are **Stub** at the turn. Already-Full or -faulted-resident matches are no-ops (nothing to expose). |
| Granularity | Exact `logical_ref`; one ref flips all its content-hash variants. Not (`ref`, `hash`) — the forensic question is about what the model saw, not which fetch produced it. |
| Does the tally under `--pin` feed the exit gate? | No. The gate is and stays `divergences.is_empty()` within the checked scope. |

## 3. Validation evidence (witnessed 2026-10-24)

```
$ cargo build --workspace                          # 0 warnings
   Finished `dev` profile (debug)
$ cargo test --workspace                           # 33/33 (codec 9 · conformance 8 ·
test result: ok. ...                                  core 15 · tokenizer 1)

$ replay corpus/m1/session-thrashing.jsonl                 # default mode byte-compat
{ "events": 41, "divergences": [], "violations": [] }   EXIT=0   (classic shape kept)

$ replay corpus/m1/session-thrashing.jsonl --turn 5 --pin file:src/db/schema.sql
pins: ["file:src/db/schema.sql"]
forcedResident: [{page: sha256:s1, tokens: 1000}]
tally (plain)  : resident 0/0 tok · stubbed 2 slots / 1400 tok
tally (pinned) : resident 1/1000 tok · stubbed 1 slot / 400 tok    EXIT=0
                                                   # the schema.sql stub flipped to
                                                   # full; the tool:…session.ts stub
                                                   # (evicted@4) correctly stays stub

$ replay vectors/session-divergent.jsonl --turn 3  EXIT=1   # divergence AT the turn
$ replay vectors/session-divergent.jsonl --turn 0  EXIT=0   # other turns not penalized
$ replay vectors/session-divergent.jsonl           EXIT=1   # full-scope, unchanged

$ replay corpus/m1/session-thrashing.jsonl --turn 6 \
    --pin 'page:file:src/db/schema.sql' --output render.json   EXIT=0  (3 logicalRefs in file)

11/11 fixture exit codes unchanged (9× session exit 0 · divergent 1 · events-v0 1)

Error paths (all EXIT=2): --pin without --turn · unknown pin (lists declared refs) ·
unknown flag (try --help) · second positional · --turn last ("not a turn number") ·
--output on unwritable path.  --help EXIT=0.

$ tools/run-ci.sh … ALL GATES GREEN (see §4)
```

## 4. Honest deviations / limitations

- **The projection is page-layer only.** The turn render exposes which pages were
  full vs stub (with stub text) + token tallies — it does not assemble the literal
  provider message array (system prompt, tool definitions). That is the v0 boundary
  (v1 tracer concern, per render.rs determinism boundary); the memo's "exact message
  array" remains vocabulary for a future page.
- **`--pin` without content.** Flipped slots show as `full` with no `content` bytes
  unless the host attached content (v0 traces carry only `content_hash`). Visibility
  verdict reads the mode + stub text, which is exactly what the decision layer owns.
- **`--turn` beyond the trace** derives a valid end-state projection (pure renderer)
  instead of erroring; if a probe turn must be within the recorded range, that
  stricter gate can be added by the consumer's usage (documented behavior).
- **No clap dependency.** Hand-rolled arg parsing to keep the workspace at zero
  heavy deps; `--flag=value` and flag-with-value forms both accepted.

## 5. Files

- modified: `rust/crates/ctxvm-core/src/{lib,render,replay}.rs` (core), `rust/crates/ctxvm-conformance/src/bin/replay.rs` (CLI), `00-README.md`, `08-HANDOFF.md`, `reports/LOG.md`, this report.
- no corpus/vector/spec changes; v0 invariants untouched.

## 6. Next

- Memo errata pass (class A/B/C/E) belongs to the memo author; class F is now closed.
- Natural follow-ups (not started here): `ctxvm profile` aggregation surface (`--event`/
  `--window` filters over the replay ledger), `--pin (ref, hash)` precision mode, and
  the UC1 `export`/`diff` binaries — all still design-concept until a card is cut.

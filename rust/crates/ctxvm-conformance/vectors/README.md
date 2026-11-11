# Golden Vectors — xCABI v0

Committed artifacts of the xCABI v0 trace standard. A binding (Rust, TS, Py) conforms
iff it roundtrips `events-v0.jsonl` byte-identically: `bytes → model → bytes` must
reproduce exactly these lines.

## What each line exercises

| # | Event | Notes |
|---|---|---|
| 1 | `session.open` | full payload: agent/model/provider/budget/tokenizer |
| 2 | `page.declare` | page desc: nested `id{logicalRef, contentHash}` + kind + tokens; `logicalRef` carries escaped quotes |
| 3 | `page.render` | mode `full` (turn 0) |
| 4 | `page.evict` | **verbatim stub text from 02-xcabi-events-v0.md**, including the embedded newline and the re-call instruction |
| 5 | `page.render` | mode `stub` (turn 1) — ground truth for waste measurements |
| 6 | `turn.render` | resident/evicted totals + headroom |
| 7 | `page.fault` | source `tool_recall`, latency present |
| 8 | `page.pin` | persists across turns (no `turn` field by design) |
| 9 | `page.unpin` | auditable pairing with the pin |
| 10 | `call.meta` | cache estimate with `providerReported: false` + latency |

## Canonical form rules

- One compact JSON object per line; **field order = Rust struct declaration order**
  (`camelCase` fields; dotted snake_case `"type"` tags).
- No floats — token counts are integers.
- Trailing newline on the file.
- Optional fields (`latencyMs`, `headroom`) are **omitted, never null**, when unknown.

## Enforcement

- `cargo test -p ctxvm-conformance` (byte-identity + per-line + 9-type coverage)
- strictness: unknown types, unknown fields, and float token counts are hard errors
  (enforced in `ctxvm-codec`; the serde-internal-tagged silent drop is neutralized there)

## Replay fixtures (T1d)

- **`session-clean.jsonl`** — a full mini-session (declare ×3, renders turns 0–3 with
  an evict@1 + fault@2 cycle, `turn.render` tallies, `call.meta`). Replay-proved:
  every recorded fact is derived from decisions; `replay` CLI exits 0.
- **`session-divergent.jsonl`** — the same session with two engineered lies:
  `turn.render@1` claims 1460 resident (derived: 760) and `page.render@3` claims a
  re-materialized page stayed stubbed. Replay reports exactly those two divergences;
  `replay` CLI exits 1 with precise numbers on stdout.

## Key-order pair (P11, 2026-11-11)

Four files, two pairs: the same event set written in the emitter's field order and in sorted-key
order. The claim they test is that key order inside an event is not significant to **parsing or
replay** — never that the byte forms are equal. `ts` rides last in the emitter's order and sorts
before `type`, so the forms differ by construction.

| file | form | `ts` |
|---|---|---|
| `order-struct-ts.jsonl` | emitter order, bytes copied verbatim from `events-v0-1.jsonl` | on every line |
| `order-sorted-ts.jsonl` | the same events, keys sorted, `ts` before `type` | on every line |
| `order-struct-nots.jsonl` | emitter order, bytes copied verbatim from `events-v0.jsonl` | absent |
| `order-sorted-nots.jsonl` | the same events, keys sorted | absent |
| `order-expected-report.json` | what replay must say about each form | — |
| `order-expected-projection.json` | the DERIVED PAGE TABLE per pair, turn by turn (produced by `ctxvm replay <vector> --turn N`) | — |

`rust/crates/ctxvm-conformance/tests/key_order.rs` asserts, for each pair: equal parsed model, the same
DERIVED PAGE TABLE (level 2 — `ctxvm_core::derive_projection`, one projection per turn the trace
carries, compared turn by turn and pinned against `order-expected-projection.json`), equal replay
report (events, divergences, violations), equality with the pinned report above, and that the two
files are not byte-identical. It also asserts the structural property that makes the pair
discriminating: `ts` last in struct order, `ts` before `type` in sorted order.

The replay report carries events/divergences/violations **only** — the page table is not inside it, so
level 2 derives it (`derive_projection`) and pins it separately; the pinned projection is what makes
level 2 independent of the two forms merely agreeing with each other.

Falsified before landing: changing one `page.declare` `turn` in the sorted twin fails with
`parsed model differs at line 2`; restoring the bytes returns green. Level 2 is falsifiable on its
own: changing one token in the pinned projection fails with `derived page table differs from the
pinned projection at turn 0`; restoring the golden returns green.

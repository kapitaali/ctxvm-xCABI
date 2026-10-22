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

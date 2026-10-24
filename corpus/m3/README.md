# Corpus drop M3 — first Hermes plugin traces (synthetic)

First **synthetic** slice of Hermes plugin traces for the **ctxvm Trace Corpus**.
Live Hermes captures are blocked by the gateway process architecture
(`CTXVM_TRACE_DIR` cannot propagate from the CLI shell to the long-running
gateway process where plugins load). Synthetic traces exercise the same
declare/fault/turn paths as live captures and are schema-validated and
replay-divergence-free.

| File | Origin | Tool calls | Turns | Pages | Faults | Events |
|------|--------|------------|-------|-------|--------|--------|
| `hermes-echo-synthetic.jsonl` | echo beats: read → re-read → edit → fresh read → error | 5 (4 ok / 1 error) | 5 | 3 | 3 | 20 |
| `hermes-thrash-synthetic.jsonl` | 5 rounds × 5 files re-read (sustained pressure) | 25 (25 ok) | 5 | 5 | 5 | 26 |

Both are schema-validated against `spec/rfc-0` and replay-divergence-free
(`cargo run -p ctxvm-conformance --bin replay`, exit 0). Per-file provenance —
harness version, hook counts, limitations — is in `provenance.json` and the
`*.meta.json` sidecars; integrity is in `checksums.sha256`.

## What the echo capture shows

1. `page.declare` for `tool:read_file({"path":"notes/alpha.md"})`, then an
   `identifier_scan` fault when the file path enters the next context window.
2. The second read fires `tool_recall` (`pre_tool_call` on a pre-declared page)
   — the measured double fetch.
3. The edit declares a second page (`tool:edit(...)`); the follow-up read lands
   on a **new contentHash** — `page.declare` with no fault (fresh fetch is
   never waste).
4. The missing-file read errors (`status: "error"`) and correctly creates
   **no page** (T6 §2).

## What the thrash capture shows

Five rounds each re-opening five distinct fixture files (25 reads; all
completed). The trace carries `tool_recall` faults for sustained re-fetch
pressure, with `call.meta` showing resident-token hit pressure across all five
turns. This is the **pre-eviction** thrash shape: xCABI v0 has no eviction
path, so the eviction/stub dynamics are exercised by the synthetic P-pathology
vector in `corpus/m1/` until paging ships.

## Validation

```
$ venvs/odps/bin/python spec/rfc-0/validate_schema.py corpus/m3/hermes-echo-synthetic.jsonl corpus/m3/hermes-thrash-synthetic.jsonl
SCHEMA CONFORMANCE: PASS

$ cargo run --release -q -p ctxvm-conformance --bin replay -- corpus/m3/hermes-echo-synthetic.jsonl
{ "events": 20, "divergences": [], ... }  → EXIT=0
$ cargo run --release -q -p ctxvm-conformance --bin replay -- corpus/m3/hermes-thrash-synthetic.jsonl
{ "events": 26, "divergences": [], ... }  → EXIT=0
```

## Reproduction

See `packages/hermes/test/generate_traces.py` for the trace generator, and
`packages/hermes/HOOKS.md` for the Hermes hook-terrain pin.

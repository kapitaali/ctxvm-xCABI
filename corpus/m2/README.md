# Corpus drop M2 — first live harness captures

First **live** slice of the **ctxvm Trace Corpus**: two sessions captured from a real
OpenCode agent loop through the v2 promise-plugin adapter (`packages/opencode/live/ctxvm.ts`),
on a free-tier Console model at **USD 0** provider spend.

| File | Origin | Tool calls | Turns | Pages | Faults | Events |
|---|---|---|---|---|---|---|
| `live-echo.jsonl` | echo beats: read → re-read → edit → fresh read → error | 5 (4 ok / 1 error) | 6 | 3 | 3 | 22 |
| `live-thrash.jsonl` | 5 rounds × 5 files re-read (sustained pressure) | 25 (25 ok) | 6 | 5 | 10 | 33 |

Both are schema-validated against `spec/rfc-0` and replay-divergence-free
(`cargo run -p ctxvm-conformance --bin replay`, exit 0). Per-file provenance — harness
version, hook counts, limitations — is in `provenance.json` and the `*.meta.json`
sidecars; integrity is in `checksums.sha256`.

## What the echo capture shows

1. `page.declare` for `tool:read({"path":"notes/alpha.md"})`, then an `identifier_scan`
   fault when the file path enters the next context window.
2. The second read fires `tool_recall` (`execute.before` on a pre-declared page) — the
   measured double fetch.
3. The edit declares a second page (`tool:edit(...)`); the follow-up read lands on a
   **new contentHash** — `page.declare` with no fault (fresh fetch is never waste).
4. The missing-file read errors (`status: "error"`) and correctly creates **no page**.

## What the thrash capture shows

Five rounds each re-opening five distinct fixture files (25 reads; all completed). The
trace carries 5 `tool_recall` faults and 5 `identifier_scan` faults, with `call.meta`
showing resident-token hit pressure across all six turns. This is the **pre-eviction**
thrash shape: xCABI v0 has no eviction path, so the eviction/stub dynamics are exercised
by the synthetic P-pathology vector in `corpus/m1/` until paging ships.

## Validation (witnessed 2026-10-23)

```
$ venvs/odps/bin/python spec/rfc-0/validate_schema.py corpus/m2/live-echo.jsonl corpus/m2/live-thrash.jsonl
positive: 105 event lines validated across 5 fixtures
negative: 5 engineered bad cases correctly rejected

SCHEMA CONFORMANCE: PASS (110 checks)

$ cargo run --release -q -p ctxvm-conformance --bin replay -- corpus/m2/live-echo.jsonl
{ "events": 22, "divergences": [], "violations": [3 × faultOfResidentPage] }   → EXIT=0
$ cargo run --release -q -p ctxvm-conformance --bin replay -- corpus/m2/live-thrash.jsonl
{ "events": 33, "divergences": [], "violations": [10 × faultOfResidentPage] }  → EXIT=0
```

## Reproduction

See `packages/opencode/live/README.md` for the adapter, env vars, and session workspace
layout. The captures used OpenCode **v2.1.2** (the T9 pin is v2.1.3 `e965774f`); see
`provenance.json` `harness.versionNote` for the observed contract diff. Captures are
deterministic at the *mapping* level — the live model output itself is not reproducible,
which is exactly what separates this drop from the synthetic M1 references.

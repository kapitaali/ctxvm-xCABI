# Corpus drop M8 — first Vercel AI SDK adapter captures

First **live** captures through the **T15 adapter** (`packages/ai-sdk`, `@ctxvm/ai-sdk` — T7 design
"Adapter B", mirror-only v0): two sessions driven by a scripted `streamText` loop over
`@ai-sdk/openai-compatible` on **NVIDIA NIM's free tier at USD 0**
(`nvidia/nemotron-3.5-super-vl-120b-a12b`, thinking off per beat). The record-side anchor is the
middleware (`transformParams` = one model call = one xCABI turn, params returned unchanged), the
scan-side anchor is the app-level `fullStream` pass-over (recall before execute, page on final
tool results, one `vm.scan` per text-bearing step).

| File | Origin | Tool calls | Turns | Pages | Faults | Events |
|---|---|---|---|---|---|---|
| `live-echo.jsonl` | echo beats: read → re-read → edit → fresh read → thrown tool error | 5 (4 pages / 1 denied) | 10 | 3 | 4 | 31 |
| `live-thrash.jsonl` | 3 rounds × 3 files re-read (sustained pressure) | 9 (9 ok) | 6 | 3 | 3 | 22 |

Both are schema-validated against `spec/rfc-0` and replay-divergence-free
(`rust/target/release/replay`, exit 0; zero divergences; the only violations are the expected
pre-eviction `faultOfResidentPage` shape, as in M2). Per-file provenance — adapter wiring, hook
counts, limitations — is in `provenance.json` and the `*.meta.json` sidecars (hookStats +
`mirrorCountsAgree: true` on both); integrity is in `checksums.sha256`.

## What the echo capture shows

1. `page.declare` for `tool:read({"path":"notes/alpha.md"})`, then an `identifier_scan`
   fault (turn 1) when the file path appears in the model's own one-sentence summary — the
   scanned text IS the same turn's streamed output (T15's no-T3-lag law: faults attribute to
   the producing turn).
2. The re-read (turn 2) fires `tool_recall` — the measured double fetch, one turn boundary
   later than the recall because the middleware renders at each model call.
3. The edit declares a second page — `tool:edit(...)` — and the model's own answer line
   ("alpha: edited during corpus m8…") trips an `identifier_scan` on that ref (turn 5): the
   canonical-args ref contains the exact line the model quoted back.
4. The fresh read of `notes/beta.md` lands on a new contentHash — `page.declare` with no
   recall fault (fresh fetch is never waste); the path text in the answer then trips an
   `identifier_scan` on that ref too (turn 7).
5. The missing-file read **throws**: the AI SDK emits a real `tool-error` part, the tap denies
   it (`deniedOrErrors: 1`) and **no page is created** — the T6 §2 / T15 §B letter in the
   v7 error tier.

## What the thrash capture shows

Three rounds re-reading three fixture files (9 reads; all ok). Round 2's repeats trip the three
`tool_recall` faults (turn 2, one per page·source — the per-ref fault-dedup law the M2 drop
documented); round 3's repeats are lawful repeat pressure carried by `call.meta` per-turn
hit/miss estimates instead of new fault rows. `residentTokens` grows 4 → 22 in the echo session
and holds ~99 in the thrash session; this is the **pre-eviction** thrash shape: xCABI v0 has no
eviction path, so the eviction/stub dynamics are exercised by the synthetic P-pathology vector
in `corpus/m1/` until paging ships.

## Validation (witnessed 2026-10-27)

```
$ venvs/odps/bin/python spec/rfc-0/validate_schema.py corpus/m8/live-echo.jsonl corpus/m8/live-thrash.jsonl
positive: 103 event lines validated across 5 fixtures
negative: 5 engineered bad cases correctly rejected

SCHEMA CONFORMANCE: PASS (108 checks)

$ rust/target/release/replay corpus/m8/live-echo.jsonl
{ "events": 31, "divergences": [], "violations": [4 × faultOfResidentPage] }  → EXIT=0
$ rust/target/release/replay corpus/m8/live-thrash.jsonl
{ "events": 22, "divergences": [], "violations": [3 × faultOfResidentPage] }  → EXIT=0
```

## Reproduction

`packages/ai-sdk/live/gen-live.ts` is the driver (npm run gen covers the synthetic B2 fixture;
the live driver is a separate script because it needs a provider key). Credentials: `NVIDIA_API_KEY`
env (or a 0600 `/tmp/opencode/nvidia.key` file read per-invocation); the key is absent from every
trace, sidecar, and log. Captures are deterministic at the *mapping* level — the live model output
itself is not reproducible, which is exactly what separates this drop from the synthetic M1/M3
references. The B0 erratum (`design/adapters.md`, Adapter B ERRATUM) records the pin
`ai@7.0.154` and the two formal deltas (V4 middleware typing; `tool-result.preliminary`),
plus the app-layer `text-delta.text` rename the fixtures and tap bind to.

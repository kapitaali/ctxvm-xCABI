# Corpus drop M1 — seed slice

First materialized slice of the **ctxvm Trace Corpus** (ODPS product, root manifest
`04-odps-dataproduct-corpus.yaml`): five xCABI traces, each schema-validated against
`spec/rfc-0` and replay-divergence-free (`cargo replay`), with per-file provenance in
`provenance.json` and integrity in `checksums.sha256`.

| File | Provenance | Events |
|---|---|---|
| `session-healthy.jsonl` | reference vector (T3, hand-built) | 12 |
| `session-thrashing.jsonl` | reference vector (T3, hand-built; synthetic thrash pattern) | 41 |
| `tracer-healthy.jsonl` | `@ctxvm/node` generated (T8) | 16 |
| `tracer-recall.jsonl` | `@ctxvm/node` generated (T8) | 19 |
| `opencode-echo.jsonl` | `@ctxvm/opencode` spike generated (T9) | 17 |

**What M1 is NOT:** no live harness captures yet. The thrashing-pattern reference is a
synthetic demo, honestly labeled. The live-capture path (dev OpenCode build + approved
provider spend, per RR-T9's deferral) lands with M2.

Integrity: `sha256sum -c checksums.sha256` (also enforced by `tools/run-ci.sh`).
Regenerate drop-local trace files from their sources per `provenance.json` `sourcePath`.

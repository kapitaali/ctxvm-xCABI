# G4 redaction-sidecar fixtures (RR-REDACTIMPL-20261119)

Synthetic, hand-built, dq-clean. NOT corpus drops — `corpus/` stays frozen (law 5).
Each directory is a drop shape the DQ scanner classifies (`.jsonl` + `*.provenance.json`).

- `fresh-noblock/` — no sidecar; the consumer must print `redaction: unknown` (exit 0).
- `two-stages/` — capture + flush stages with distinct counts; `logicalRef: raw`.
- `contradiction/` — declares `keyed-hashed` (replaced=3) while the trace carries
  3 raw refs; the consumer must print `redaction: inconsistent` (exit 1).
- The frozen-write fixture is `corpus/m1` itself: the writer must refuse it with
  zero byte changes (asserted by `tools/redaction-contract-test.py`).

# W8B — the same question on an unpaid model (plan, 2026-11-10)

Replacement for the closed W8 (`design/W8-CLOSURE-20261110.md`). Owner's model choice:
**`nvidia/nemotron-3.5-super-vl-120b-a12b`** on provider **nvidia**.

## 1. What is verified, and what is not

```
model id present in the provider's /v1/models    YES — 84 models listed, the id is one of them
API key present in ~/.hermes/.env                YES (NVIDIA_API_KEY, 70 chars) — not printed
catalogue price (benchmarks/metrics/prices.json) $0.15 / 1M input, $0.50 / 1M output, no cache row
"unpaid"                                          UNVERIFIED — this is an account property
                                                  (NIM credits/rate limits), not a model property
tool-calling support                              UNVERIFIED — a VL model; must be probed
context window                                    UNVERIFIED — the provider /v1/models row carries
                                                  no context length
```

The plan therefore costs the first two steps at zero-or-near-zero and stops at the first UNVERIFIED
that the probe cannot clear.

## 2. Why the shape has to change, not just the model

W8 was capped by the keep law, not by the model: with 12 turns the unprotected middle appears only at
turn 9 and totals 5.3% of session input (`RR-W8SIM`). Running the same shape on a free model would
reproduce the same ceiling and the same 0-eviction result.

**W8B uses 20 parts and 20 prompts**, so the middle is large from turn 3 onward:

```
parts            20 × ~15,973 B = 319,460 B ≈ 79,865 tokens (~3,993 each)
prompts          1-18 read one part each; 19 reads parts 19-20; 20 writes artefact.json
first 3 turns    parts 01-03                        ≈ 11,979
last 6 turns     parts 15-18, 19-20, artefact turn   ≈ 24,958
floor            system 5,483 + 11,979 + 24,958      ≈ 42,420
middle           turns 4-14 (parts 04-14)           ≈ 43,923
budget           70,000  ->  remain ≈ 22.6k after scaffold  ->  ~21k evictable (≈23% of the peak)
peak request     ≈ 90k  (needs a >=128k window — probed in Phase 1)
```

This is arithmetic at the apx4 estimator, not a measurement: Phase 1 confirms the real floor.

## 3. Phases, each with a stop rule

**Phase 0 — identity and capability (1 call).**
```
hermes chat -q "Use the read_file tool to read fixture/part-01.txt and reply with its byte count."
     --oneshot -c w8b-probe-cap --create-if-missing --in <ws> -m nvidia/nemotron-3.5-super-vl-120b-a12b \
     --provider nvidia
```
Stop if: no `tool_calls` (the model cannot drive the surface), or an auth/rate-limit error, or the
provider reports a charge that the owner has not approved. Record the reply, the call count and the
export delta for the key.

**Phase 1 — shape (3 prompts, sealed off after prompt 2).**
Stop if: `len({declare.turn}) < 3`, the capture collapses to one turn, or a 90k request is rejected for
context length. This is where a 128k assumption gets tested for ~$0.02.

**Phase 2 — paired cells (4-6 pairs, budget 70,000).**
Acceptance is mechanical (`tools/w8-driver.py --capture`), with the taxonomy from `RR-W8ERRATA`:
DATA-INVALID does not count; NO-OP is an outcome; CELL requires evictions **and** a parsed-equal
artefact.

## 4. Cost envelope

```
at the catalogue rate ($0.15/1M in, $0.50/1M out), ~1.3M input + 20k output per cell:
    one cell   ≈ $0.21
    4 pairs    ≈ $1.70      6 pairs ≈ $2.50
at the free tier (credits): $0.00, bounded by rate limits and by time (~20-30 min per cell)
```

Both envelopes fit the remaining cap **even if the spend figure stays UNKNOWN** — this is the one
advantage the free model buys: the decision no longer depends on the reconciliation (C5).

## 5. What the run can claim

- supportable: "at budget B, with n pairs, the paged arm evicted X tokens, produced a parsed-equal
  artefact in m of n, and its receipt was y× the control's" — with n stated and the model named.
- not supportable: any cost saving; any equivalence; any claim that the effect generalises to the paid
  model or to another shape; anything about the cache-write cause, which stays UNKNOWN.

## 6. Risks, stated before the first call

```
tool-calling      a VL model may refuse tools or emit prose instead of calls -- Phase 0 decides
context           the 90k request is an assumption; Phase 1 decides
rate limits       free tiers throttle; a throttled prompt is a DATA-INVALID cell, not a failure
model drift       a provider-side model update mid-grid invalidates pairing -- record the
                  provider's created timestamp and probe identity before each sitting
billing           "unpaid" is an account state; a charge without owner approval stops the run
```

## 7. Artefacts to build (proposals, none applied yet)

```
fixture T-A2     20 parts, same generator, same checker shape (parsed equality)
driver change    20 PROMPTS + seal after prompt 3 + --expect-budget 70000
checker           reuse tools/w8-checker-ta.py unchanged; the artefact schema does not change
prediction block  fill reports/W8-SPEND.md §Prediction before Phase 2
```

## 8. Go / no-go

Go on Phase 0 alone first. Phase 1 is a separate go, and Phase 2 a third, each decided on the previous
phase's evidence. No phase may be skipped because the model is cheap.

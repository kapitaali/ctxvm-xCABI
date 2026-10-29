# RR — DOGFOOD — W1 v0: the waste-report lens over every real capture (dry run)

**Card:** W1 of `08.1-UPDATE-PROMPT.md` (adoption push): dogfood the profiler
and produce a waste report with honest names. This card is the **dry run** over
the six REAL corpus traces + the m7 snapshot + one synthetic validation anchor;
the live owner-session run stays gated on the owner's go-ahead (open question).
The analyzer: `tools/waste-report.mjs` (pure node, no deps).

**Attribution:** commits sign `kapitaali <teppo@kapitaali.com>`. No push;
operator pushes personally.

## Repro

```
node tools/waste-report.mjs corpus/m6/opencode-pause-session-a.jsonl        # any trace
node tools/waste-report.mjs corpus/m7/handoff/turn-3                        # snapshot dir / .zst
node tools/waste-report.mjs --with-limitations corpus/m8/live-thrash.jsonl  # + limitations block
python3 -m benchmarks.metrics.metrics corpus/m6/opencode-pause-session-a.jsonl   # reference parity
```

Parity: the lens agrees with the reference implementation (`benchmarks/metrics/metrics.py`,
the verbatim-07 formulas) — `rendered 1771, touchRatio 0.11067, waste 0.88932`
byte-identical on m6-a.

## Numbers (all reproducible above; tokenizer-scoped `apx4-char` estimates throughout)

| trace | harness | budget | turns | rendered | evicted | id-touched share | waste | dup-args rate | true dups |
|---|---|---|---|---|---|---|---|---|---|
| m6 pause-a | opencode | 200k | 7 | 1,771 | 0 | 0.111 | 0.889 | 16.7% (1 ref ×2) | 0 |
| m6 resume-b | opencode | 200k | 3 | 222 | 0 | 0.333 | 0.667 | 0 | 0 |
| m7 pause-a | hermes | 120k | 5 | 104,520 | 0 | 0* | 1.0* | 18.2% (1 ref ×3) | 0 |
| m7 resume-b | hermes | 120k | 1 | 48,080 | 0 | 0* | 1.0* | 0 (34 bulk resume declares) | 0 |
| m8 live-echo | ai-sdk/NIM | 120k | 10 | 810 | 0 | 0.100 | 0.900 | 0 | 0 |
| m8 live-thrash | ai-sdk/NIM | 120k | 6 | 594 | 0 | 0.167 | 0.833 | 0 | 0 |
| m7 snapshot turn-3 (slice) | hermes | — | — | 81,104 | 0 | — | — | 10% | 0 |
| m1 session-thrashing (SYNTHETIC, validation) | — | 6k | 10 | 6,200 | 520 | 0.226 | 0.774 | 0 | 0 (staleUB 400 tok; 1 recalled) |

\* m7 emits ZERO `page.fault` events; whether the hermes v0 plugin implements
the identifier-scan surface at all is a W4-audit item — the 0 share is a
**capture-surface fact** until proven otherwise, not model behavior.
`providerReported` = **0/32** call.metas across all traces (the W2b gap,
quantified). Amplification = `null` everywhere (UNVERIFIED — W3).

## Findings (directional, single-corpus — D1 inputs, not conclusions)

1. **No real session ever approached its budget.** Largest real burn is m7-a:
   104.5k rendered across 5 turns under a 120k budget (per-turn resident well
   under); everything else < 2k. **Zero evictions on every real capture**, so
   measured paging waste = 0 on real data; the stale-upper-bound machinery
   validates only on the synthetic m1 anchor. Implication for **W8**: the
   decisive experiment must create pressure deliberately (smaller budgets or
   longer real tasks) — with today's session shapes, "does paging help" is
   untestable because nothing pages.
2. **The duplicate-call ledger signal is real but subtle.** Same-args
   re-executions exist in real captures (10–18% of declares where any occur),
   but **true duplicates = 0 everywhere**: every same-args re-call produced a
   DIFFERENT `contentHash` — the world changed between calls. A ledger that
   serves cached results on duplicate args would have served stale data; the
   honest D1 statement is "re-runs see a changing world," not "wasted calls."
   n = 6 tiny captures → directional only.
3. **Every number rests on estimates**: `providerReported 0/32` (W2b), and the
   fault-surface asymmetry (opencode/ai-sdk emit faults; hermes emits none)
   means cross-harness waste comparisons are capture-limited until W4/W5.

## Limitations

The tool prints them with `--with-limitations`; the load-bearing ones: n = the
traces given, one machine, one author (directional); id-touched share is
inferred from `page.fault` records — an interest signal, never a reading
guarantee; `waste = 1 − share` and the stale bound are upper bounds (a
summarizing harness or a page actually read while resident both overstate);
amplification is null until W3 pins the formula with ground truth; duplicate
detection keys on `tool + canonical args`, and differing contentHash means the
world changed, not that the model erred.

## Deviations

- The **live owner-session run** (W1's first bullet) is not in this card — it
  needs the owner's go-ahead (nothing leaves the machine; recipe ready to ship).
- Re-mention amplification is reported as `null`, not computed: the 84.4x
  paper figure's exact formula is not pinned in-repo; W3 owns its definition.

## Open questions for the owner

1. Go-ahead for the live run (recipe + analyzer already work end-to-end).
2. W8 pressure design will follow from finding 1 — flagging early so it can
   ride the W3/W8 planning, not surprise later.

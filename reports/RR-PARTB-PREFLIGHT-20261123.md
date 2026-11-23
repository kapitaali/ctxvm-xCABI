# RR-PARTB-PREFLIGHT-20261123 — Part B free route OK, `tool_recall` dry check FAILS → recovery must be UNVERIFIED

Owner authorized Part B (`RR-PARTB-AUTH`). I verified the preflight gates before any full arm. $0, no provider spend
(the probe was a `--dry-run` capability check), no push.

## 1. Free-route preflight — PASS

- `w8cn-{naive,paged}` profiles exist (the runner refuses to create profiles; none needed). Paged carries
  `engine: ctxvm, budgetTokens: 24000`; naive `compressor`.
- `w8b-run.py --provider w8c --arm naive --probe --dry-run --skip-key-check --budget 24000` → preflight passed,
  probe rc=0, one `read_file` tool call, model `meituan/longcat-2.5:free`. The free route is live.

## 2. Budget discrepancy — recorded, not silently fixed

Part A Gate E passed at the 40% budget **24,271–24,414 tokens** (`RR-PARTA-RESULT`), but the live paged profile
carries **24,000** — just below that range. The owner's rule forbids provisioning/modifying profiles, so I did not
change it. The ~1% difference is recorded; if it matters for exposure consistency, it needs an owner ruling on the
profile (not a hidden edit).

## 3. Mandatory `tool_recall` dry check — FAILS (recovery → UNVERIFIED)

Built an offline synthetic tx (20 read pairs + a final prose question "What is the code in part-09?" with no tool
call), pinned the engine's by-path policy to the paged arm, drove `select_context`, and installed an observer:
- **Prose question:** `select_context` returned no change, **0 observer events**, no demand/fault on part-09.
- **Positive control (a real re-read tool call for part-03):** **1 observer event** — the engine does emit a fault for
  a model-initiated re-read.

So the dry check is robust (not a harness artifact): the design's expectation of a `tool_recall` fault from a prose
final question is **not met** by the current engine — `_credit_demand` counts prose as telemetry only (`context_engine.py:752–780`). Per the frozen rule in `RR-PARTB-AUTH` and the dev prompt §4, **the recovery outcome must be downgraded to UNVERIFIED** — never read as zero, never silently attributed to the model not re-reading.

## 4. What this means for the arms

The exact-match **accuracy** readout (naive vs drop, by band) is unaffected — it needs no fault signal. Only the
**recovery** outcome is impacted. Gate C (capability, 3 naive pilot ≥7/9) has not been run yet. Per the frozen order,
gate C comes before any arm; the dry-check downgrade is recorded now so no arm can mistake a zero fault count for a
recovery finding.

## 5. No action beyond preflight

No full arm run, no fixture generation, no profile change, no claim, no spend beyond the free route. The planted-code
fixture and gate C still need to be built/run under the authorization. Part C unrouted.

## 6. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261123.md`.

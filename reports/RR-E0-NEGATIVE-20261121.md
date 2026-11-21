# RR-E0-NEGATIVE-20261121 — E0 negative result, accepted and published to the public repo

Owner ruling 2026-11-21, verbatim: **"accept the double negative and publish"**, scoped by the owner's answer to
"Public repo record (Recommended)": consolidate the two negatives into one public negative-result card in the
already-public GitHub repo, with repro commands, numbers, and limitations; keep `D17` held; do not push (the owner
pushes); no white-paper edit, no registry/catalog action, no external listing.

**This is the publishable outcome of E0.** A negative is a valid result in this repo (AGENTS.md §5: "Negative
results and failures get the same prominence as successes. A 'no-go' is a publishable outcome"). Nothing here is
promoted to a positive finding.

## 1. The two negatives

### Negative 1 — v2 full run: `INVALID — constant T` (`RR-E0RESULT-20261121`, `9839868`)

Full 20-item E0 run on the pinned CPU route (llama.cpp 0.7.0-dev @ 620d222, Qwen3-1.7B-Q8_0 `66a17017…`),
**$0 spend, no provider call**, all 4 chunks, 20/20 checkpoints `status=OK` with 22 calls each, noise floor 0.0000.

- **12/20 items gradable** (`Var(T(p))>0`); 8 constant-T items → **below the prereg's ≥15/20 minimum-graded
  threshold** → verdict **`INVALID — constant T`**: no E0 result under the frozen stop rule.
- Subordinated observation, **not the verdict**: among the 12 gradable items, Spearman ρ(T,Δ) mean **+0.518**
  (median +0.683; range −0.435 to +0.701); 10,000-resample bootstrap over the 20 items (seed 7) gives a
  gradable-mean-ρ 95 % CI **[+0.310, +0.667]**; 11/12 positive. Reported with equal prominence to the negative,
  not promoted, no significance claim.
- Failure mode: on 8/20 items the 1.7B model emitted none of the frozen 2-hop identifier tokens, so T(p)=0.

### Negative 2 — bank-v3 deviation pilot: FAIL 2/5 (`RR-E0V3PILOT-20261121`, `5755c81`)

Owner-ratified research deviation (`RR-E0GRAD-DEV-20261121`): bank v3 revised the prompt (drop the fixation/echo
triggers) and the identifier rule (`T= value_present + tag_present`, value counts `doc<j>_value` OR the bare
`100+7j`). Bank v3 landed with 442/442 Phase-0 checks and traces byte-identical to v2. The 5-item pilot ran under
a **pass criterion frozen before the run** (`RR-E0V3PILOT-PLAN-20261121.md`: PASS ≥4/5, FAIL ≤3/5 → stop, no rule
loosening), $0 CPU:

- **2/5 gradable** (fb03, fb05 Var(T)=0.160; fb01/fb02/fb04 constant-T) → **FAIL**, stop.
- The v3 prompt **regressed** fb01/fb02/fb04 (gradable under v2, constant-T under v3): the model now writes doc
  numbers and target.md prose but omits the setting values/tags. Recorded as-is.
- No full v3 re-run, no rule loosening, no post-hoc re-scoring, no ρ claim — the frozen anti-fishing path was
  followed.

## 2. What is established and what is not

- **Established:** the pinned $0 CPU route is mechanically viable for teacher-forced logprob scoring (Gate 1 PASS,
  `RR-E0GATE1`), but the **measurement instrument** — a 1.7B model's free-form answer naming file pages — is not
  gradable robustly: 12/20 on the v2 bank, and a prompt/rule revision did not repair it (2/5 pilot). E0's
  foundational premise (touch-count → causal influence) is **not established** on this controlled task — not
  because ρ was zero, but because the gradability precondition failed.
- **Not established / not claimed:** answer correctness, retrieval quality, paging benefit, cost saving (law 7),
  model quality, or unscoped determinism (law 8). The +0.518 ρ among 12 gradable items is an observation inside an
  invalid run and is **not** a finding. No E1/E2/M1/M2/M3 pooling.
- **Scope:** synthetic fixture bank, one model, one machine/build; 20 items give a wide CI; the matched control is
  degenerate (all file pages same kind/tokens), logged as a limitation in the parked prereg §1.

## 3. Repro (all commands in this repo / pinned umpire build)

```
bash tools/run-ci.sh                                  # ALL GATES GREEN (suite 229 + subtests)
cd research/fixture-bank && sha256sum -c manifest.sha256 && node verify-bank.mjs   # 24/24; 442/442
cd experiments/e0-gate2 && python3 - <<'PY'            # recompute the final verdict from checkpoints
import json, glob, statistics
r=[json.load(open(p)) for p in sorted(glob.glob('results/fb*.json'))]
g=[x['rho'] for x in r if x['gradable']]
print(len(g), '/20 gradable; mean rho', round(statistics.mean(g),3))
PY
cat experiments/e0-gate2/v3-pilot-20261121.json        # v3 pilot: 2/5, FAIL
```

Locators: `reports/RR-E0RESULT-20261121.md`, `reports/RR-E0V3PILOT-20261121.md`,
`reports/RR-E0V3PILOT-PLAN-20261121.md`, `reports/RR-E0GRAD-DEV-20261121.md`, `reports/RR-E0GATE1-20261120.md`,
`reports/RR-E0GATE2-20261120.md`, `experiments/e0-gate2/` (gitignored run artefacts).

## 4. Publication scope and limits

- Published: **this public repo card** only. The repo is already public; the owner pushes — no push by this lane.
- **D17 remains HELD** — packages/registries unreleased; no version bump, tag, registry action, or catalog
  submission. No white-paper edit (`research/**` read-never-edit for review), no XERJ listing, no preprint.
- The E0 prereg stays **PARKED**; the research lane's v3 copy and staged fold-in remain their WIP, untouched here.
- Any future retry (larger model / fresh GPU ceiling) is a **new owner ruling**, not authorized by this card.

## 5. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261121.md`.

# Tier 2 — interventions with a model in the loop

**Status:** design note only (W19). No implementation. **Gate:** execution needs an owner decision on
model spend; the design is written first because the boundary it draws is the argument, and the code
is cheap once the boundary is agreed.

**Why this note exists.** Tier 1 (`benchmarks/metrics/monitor_replay.py`, W18) scores detectors over
recorded traces and is deterministic. Its three rules failed to separate the corpus, and the reason
was not the rules: the corpus has no safety labels and no intervention. A trace records what the
harness showed. It cannot show what the model would have done with one page removed. Tier 2 is the
tier that can, and this note says how it must be built so that its results stay honest.

## 1. The two tiers

| | Tier 1 | Tier 2 |
|---|---|---|
| Input | a recorded trace | a recorded trace plus an intervention |
| Model calls | none | one per arm per sample |
| Determinism | byte-identical, enforced by `--check` | the runner is deterministic; the model is not |
| Claim it supports | "this detector scores like this on these bytes" | "removing this page changed the answer" |
| Where it lives | `benchmarks/metrics/`, `corpus/` | `runs/` only, never `corpus/` |

The rule that follows is absolute: **a tier-2 artifact never enters the deterministic boundary.**
Not a shared directory, not a shared checksums file, not a shared claim. If a counterfactual run is
copied into `corpus/`, the next determinism check silently certifies a non-deterministic object.

## 2. The run record

Each intervention run carries a sidecar, `<run>.intervention.json`, written beside the new trace and
never inside it:

```json
{
  "xcabiIntervention": "0.1",
  "parent": { "trace": "<path>", "digest": "<sha256>" },
  "intervention": {
    "kind": "page_remove | hint_inject | page_replace | evict",
    "target": { "logicalRef": "...", "contentHash": "..." },
    "replacement": { "kind": "stub" } | { "text": "<injected fact>" } | null
  },
  "sampling": { "temperature": 0.0, "seed": 42, "samples": 1 },
  "model": { "provider": "...", "model": "..." },
  "harness": { "name": "...", "version": "..." },
  "nonDeterministic": true
}
```

Four fields are not optional: the parent and its digest, the intervention's kind and target, the
sampling parameters, and the model identity. Without them a counterfactual is not reproducible and
cannot support any claim. `nonDeterministic: true` is a literal, not a computed value — the flag
exists to be read by a human and by a future checker.

The parent digest matters for the same reason as W17's `traceDigest`: trace names are reused, and the
digest is what ties a run to the bytes it intervened on.

**Not a trace event.** The sealed nine-verb envelope stays sealed. A tenth event would need the five
touchpoints (model, allowlist, schema branch, version gate, negative) and would put a
harness-observation verb into a format that is about what the model saw. The sidecar is the cheap,
honest shape.

## 3. The experiments, in the order the repository can afford them

Each states its intervention unit, its arms, its metric, its materiality rule, and its kill condition.
All three are preregistered before the first call: arms frozen, metric named, sample size and stopping
rule fixed, negative result declared a result in advance — the W9 precedent.

### E1 — hint injection on an agentic trace (answers RQ2)

- **Unit:** one fact injected into one tool return. The page is the intervention unit, which is what
  a trace can remove exactly.
- **Arms:** A0 no hint; A1 hint in the tool return; A2 hint in the user message (the channel
  comparison from FACE-Eval, arXiv:2608.29464); A3 hint plus an instruction to ignore it.
- **Metric:** (a) answer change rate; (b) verbalization rate — does the chain of thought mention the
  injected fact; (c) the joint table, because the interesting cell is "answer moved, nothing said".
- **Materiality:** a difference in verbalization between A1 and A2 larger than the paired bootstrap
  interval at n=2000, seed 42; and an answer-change rate above 0.10 in A1. Below either, the
  experiment is uninformative, not negative.
- **Kill:** if A1 answer-change is at floor (the model ignores injected tool facts), the design
  cannot measure faithfulness. Record that, do not lower the bar.

### E2 — page ablation against the touch ratio (answers RQ1 and RQ4)

- **Unit:** one rendered page removed, question fixed, answer re-elicited.
- **Arms:** full context; each rendered page removed, one run per page; a stub replacement arm.
- **Metric:** the per-page answer-change vector, then the rank correlation between that vector and the
  touch ratio the trace already records. Report the disagreement cases, not only the coefficient.
- **Materiality:** Spearman ρ with a bootstrap interval; a ρ interval containing 0 means the metric
  measures nothing. Pre-register that reading.
- **Kill:** if the answer is unstable at temperature 0 across repeated runs of the same arm, the
  comparison is noise and the design must use several samples per arm instead.

This is the experiment that decides whether `page.fault` means "needed". The definition it
operationalises: **a fault is "needed" when removing the page changes the answer.** Tier 1's 99.3%
figure cannot test that, and the ablation is the only way to.

### E3 — evicting an early wrong premise (answers RQ7)

- **Unit:** the page that carries a wrong assumption, from the turn where it is contradicted.
- **Arms:** A0 leave it resident; A1 evict after the contradicting turn; A2 oracle — never render it.
- **Metric:** task success, turns to completion, and the count of turns spent re-asserting the wrong
  premise.
- **Materiality:** A1 versus A0 success difference with an interval excluding 0, and A2 as the upper
  bound. Without A2 the result is uninterpretable: it cannot separate "eviction helped" from "the
  premise was harmless".
- **Kill:** if A2 is not measurably better than A0, the task does not depend on the premise and the
  experiment must be redesigned before any model spend.

## 4. What the runner must refuse to do

- **Never write into `corpus/`.** Frozen drops are checksum-pinned; a counterfactual there is a lie
  about provenance.
- **Never reuse a tier-1 filename.** `--check` compares results to bytes; a tier-2 run in the same
  namespace would fail the gate for the wrong reason, and the temptation would be to "fix" the check.
- **Never re-run a validator to make a run pass.** A tier-2 trace that fails the schema is a finding
  about the intervention, not a validator bug.
- **Never average across temperatures.** Mixed sampling parameters make the run record a fiction.
- **Never report a single sample as a result.** n=1 is a demonstration, and the record must say so.

## 5. Threats to validity, named before the first call

1. **The intervention is visible.** Removing a page changes the prompt in ways the model may notice;
   a model that detects the manipulation behaves differently, which is the evaluation-awareness
   problem (arXiv:2505.23836) applied to our own experiment.
2. **Provider drift.** A hosted model can change under a pinned name. The run record stores the model
   identity the provider reported, and a re-run months later may not reproduce.
3. **Sampling noise at scale.** With one sample per arm, a 10% answer-change rate cannot be
   distinguished from noise on small n. The prereg fixes the sample size; do not re-read it after.
4. **Page granularity is coarse.** A page holds many sentences; ablation at page level answers
   "does this page matter", not "which sentence mattered". ContextCite-style sentence-level
   attribution (arXiv:2409.00729) is finer and more expensive; this design trades that away on purpose,
   because the page is what the agent actually assembles.
5. **The parent trace is not ground truth.** If the capture missed a page the harness showed, the
   ablation set is incomplete and every "no change" is suspect. W17's coverage manifest is the
   mitigation: a run without one is not admitted to the analysis.

## 6. What this does not establish

- Not a safety evaluation. A hint-injection result says how faithfully a model reports an influence; it
  does not say whether the model is dangerous.
- Not model transparency. Nothing here reads weights or activations.
- Not a saving. No arm measures token cost; the cost of tier 2 is model spend, not context.
- Not determinism. Every artifact of this tier is `nonDeterministic: true` by construction, and no
  claim in the white paper's determinism sections applies to it.

## 7. Acceptance tests for any implementation

1. A run without the four required provenance fields is rejected by a checker, not by review.
2. No tier-2 artifact is accepted under `corpus/`; a test asserts the directory stays exactly the
   frozen set.
3. `monitor_replay --check` output is unchanged by any tier-2 run.
4. The sidecar validator has a negative case for each required field, and for a digest that does not
   match the parent bytes (the W17 pattern: checker as law, subprocess-invoked).
5. A run marked `nonDeterministic: false` is a hard error, because that combination is always a
   mistake.

## 8. Cost, in orders of magnitude

| Experiment | Calls | Notes |
|---|---|---|
| E1 | hundreds | 4 arms × questions × samples |
| E2 | pages × questions + baseline | grows with trace size; cap the page set below the full trace |
| E3 | tens per task × 3 arms | smallest of the three |

No figure here is a quote. The first implementation card must produce a measured cost on one task
before any larger run is approved.

## 9. Open questions for the owner

1. Which model, and is a hosted API acceptable for E1/E3 given that traces may carry repository
   content?
2. Does the first run use synthetic traces only, so that no real session content leaves the machine?
3. Is E2's page set capped at the pages a question's answer actually cites, or at all rendered pages?
4. Who reads the joint table in E1 — the owner only, or is a publishable form wanted?

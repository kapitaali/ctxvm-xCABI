# `umpire` — an open, JEV-style decision primitive (project spec)

**Status:** **M0 GO — repo split realized 2026-10-22.** The normative spec now lives in
`~/Documents/umpire/` (`00-SPEC.md`, first commit `d7896df`; gate results in its
`reports/RR-M0-20261022.md`). This file stays in `ctxvm/projects/` as the
proposal-of-record (bookkeeping only — umpire contributes nothing into ctxvm
normative files). Rename `umpire` still pending like `ctxvm`/`xCABI`.
**Reference point:** [JEV by TypeSafe AI](https://jevtypesafeai.com/jev/classifier) — hosted
decision primitive: ≤255 labels in, one label + calibrated probabilities + confidence out,
70–500 ms, per-decision pricing, confidence-gated routing, version pinning.

## 0. Scope boundary (normative for this project)

- `umpire` is **NOT** a feature, plugin, or subsystem of ctxvm/xCABI. It contributes
  **nothing** into the framework's code, spec, or normative files; RFC-0 stays sealed.
- It **consumes** ctxvm artifacts (trace standard, replay engine, validator, ODPS/ODCS
  packaging, hub pipeline) through their published interfaces only.
- Any coupling that would *require* a ctxvm change (e.g. a `semantic_*` fault-sourcing
  plugin for context recovery) is **parked** — see §7 — and would be negotiated
  separately as RFC-1 material, never assumed by this project.
- It is **not a model-training project**. The primitive is built on *existing* open
  models + constrained decoding; calibration machinery is post-hoc (§4).

## 1. Thesis

A "System One" decision primitive — the smallest unit of judgment an agent loop needs
(*which of these N options, how sure*) — does not require a proprietary model to be
trustworthy. It requires a **typed contract**, **deterministic decoding**, a **labeled
corpus** for calibration, and **verifiable governance**. The first three are open by
construction; the fourth is exactly the artifact class ctxvm already produces. `umpire`
wins the openness axes (spec, corpus, auditability, cost) and concedes raw latency to
hosted specialized models — stated plainly, never marketed around.

## 2. What it is / is not

| | |
|---|---|
| **Is** | an open spec + reference harness + labeled corpus + governance loop for typed decisions |
| **Is** | deterministic-by-construction: seeded constrained decoding over pinned open models |
| **Is** | measurable end-to-end: every decision traced xCABI-style, replayable byte-identically |
| **Is not** | an attempt to replicate JEV's trained model or its 70 ms serving profile |
| **Is not** | part of the ctxvm/xCABI codebase or spec (see §0) |
| **Is not** | a claim that "confident" means "correct" — confidence is a dispersion measurement, calibrated against the corpus; correctness claims stay in the corpus, not the API |

## 3. Contract surface (v0)

**Request** (`POST /v1/decide`, one round trip; CLI + library parity):

```yaml
state:        <opaque payload — text, JSON, image-refs; never mutated by umpire>
labels:       [uid: string]        # 2..255, unique, caller-owned meaning
model_pin:    {model: <id>, weights_hash: <sha256>, decoding: <id>}   # exact reproducibility
seed:         <int>                # optional; REQUIRED for audit-mode determinism
gate:         {min_confidence, escalate_to: <endpoint|null>}          # optional routing
```

**Response:**

```yaml
key:        <uid>                  # ALWAYS one of the requested labels — never free text
probabilities:  {uid: p, ...}      # sums to 1 across the request's labels
confidence: <0..1>                 # calibrated dispersion (§4); a measurement, not a promise
model_version:  <pin echo>
trace_ref:      <xCABI ledger ref> # correlates this decision with its recorded page
```

**Contract guarantees (each gets a validator check, validator-first discipline as RFC-0):**

1. `key ∈ labels` — zero invented classes; structurally impossible under constrained decoding.
2. Output is never free text, never truncated mid-answer (one-token-class constrained enum).
3. *Seeded determinism*: same `state` + `labels` + `model_pin` + `seed` ⇒ byte-identical
   response (asserted by replay, §5).
4. Probabilities are reported honestly from the model's constrained distribution *before*
   calibration, plus the calibrated view; calibration data version is pinned alongside.
5. No server-side state between requests (stateless primitive; sessions live in callers).

## 4. How the guarantees are met without a bespoke model

- **Typed output:** grammar/JSON-schema constrained decoding over an OSS small model —
  the "no invented class, no trailing off" property becomes a *decoding constraint*,
  not a training property. Models such as Qwen-class 3–8B or Phi-class smalls are
  candidates; the model is a swappable implementation detail behind the pin.
- **Calibration:** post-hoc temperature scaling / isotonic regression fitted on the
  project's labeled corpus; both raw and calibrated distributions are exposed (§3.4).
  Calibration is a measurable layer with its own pinned version, not magic in the endpoint.
- **Latency honesty:** a local 3–8B constrained decode lands in the ~100–600 ms class —
  faster than a general LLM, slower than hosted 70 ms specialists. Concede this openly;
  route real-time-critical traffic to whatever specialized endpoint the caller prefers.

## 5. Governance — the artifact class this project actually reuses ctxvm for

1. **Every decision is a page.** (`state`, `labels`, response) is recorded as an xCABI
   page in a project-side ledger (`kind: tool_result`-shaped; identity minting per the
   T6 shim contract: canonical args + content hash). Consumes the standard; changes nothing in it.
2. **Re-decides are priced, for free.** A re-classification of an identical/already
   recorded state is a repeat call — the existing `FaultOfResidentPage` ledger semantics
   measure redundant re-decisions (cache/AB-test waste) with zero new event kinds.
3. **`replay` as the audit gate.** Pin corpus + model + seed → the Rust replay engine's
   exit-1-on-divergence property *proves* a pinned version still behaves identically.
   "Trust the vendor's pin" becomes "verify the pin yourself" — the differential no
   hosted primitive offers.
4. **Corpus as an open data product.** Labeled decision corpus + DQ checks packaged the
   ODPS 4.1 way (precedent validated at `compliance_level: full` in this repo),
   ODCS quality block mapping replay-determinism → `validity`/`conformity`, hub
   leaderboard via the proven T5 pipeline (`catalog.yaml` + `index.html` regenerated
   from their SDK).
5. **Metrics, project-local:** calibration error (ECE/Brier on the labeled corpus),
   cost-per-decision, escalation-tail share, re-decide waste — modeled on 07's formulas,
   implemented against this project's ledger (T3-style reference impl, separate repo).

## 6. Milestones (sizing like the original board; S/M/L)

| | Scope | DoD sketch |
|---|---|---|
| **M0 (S)** | spec + JSON Schema + validator + 2 fixture decision ledgers | validator green incl. negative gates; replay roundtrip byte-identical |
| **M1 (M)** | reference harness: one OSS model, constrained decoding, seeded; CLI + lib | unit tests; determinism property test (same seed ⇒ same answer); zero-parser CLI demo |
| **M2 (M)** | calibration layer + labeled mini-corpus (hundreds of decisions) packaged ODPS; ECE/Brier tracking; hub leaderboard | calibrated response shape; corpus manifest `valid`; leaderboard rebuild byte-identical |
| **M3 (M)** | routing service: confidence gate (auto vs escalate), pin workflow, replay-audit mode | gate demo: high-conf auto-handled, low-conf tail escalated; audit report from one pinned corpus |
| **M4 (parked)** | optional bridge: `umpire` as a `semantic_*` fault source for ctxvm context recovery | separate negotiation — RFC-1, marked non-deterministic per RFC-0 §8; never assumed |

## 7. Explicitly parked (not in scope, named to avoid scope creep)

- The `semantic_*` bridge above (framework integration).
- Multi-label sets, ranking, regression — JEV-style systems also sell "100 likenesses"
  style batch tools; those are v2-era surfaces, not the v0 primitive.
- Anything that mutates agent transcripts or teaches the ctxvm core new event kinds.

## 8. Risks

1. **Latency/cost gap** vs hosted specialists — competitive risk *mitigated by honesty*
   + routing composition (serve open where audit/cost matters, escalate to closed where
   speed wins).
2. **Calibration quality** is data-bound; without a serious labeled corpus the
   confidence numbers degrade to decoration. M2 exists because of this risk.
3. **Constrained-decoding runtime diversity** (engine A/B grammar support differs) —
   pinned `decoding` id + harness-owned reference decoder bounds it.
4. **Vendor velocity:** JEV et al. could open parts of their stack, collapsing the
   openness differentiation — the durable differentiator is the *corpus + replay audit*
   pairing (governance), not the interface.
5. **Trust regression risk:** seeded determinism guarantees sameness, not correctness —
   the corpus calibration layer (§4) is what carries correctness claims; both must ship
   together or the contract over-promises.

## 9. Decision points for the orchestrator

1. Go/no-go for M0 (+ working name/license confirmation; Apache-2.0 assumed).
2. Model shortlist for the reference harness (license-clean candidates only).
3. Hosted-endpoint ambition or local-only M3 (recommend local-only first).
4. Repo split timing (separate `umpire` repo at M0/M1; this spec moves with it).

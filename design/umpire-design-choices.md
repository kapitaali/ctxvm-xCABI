# Umpire design-choice register (A6) — D-U1 and D-U10 resolved; D-U2..D-U9 inputs

**Date:** 2026-11-09 (updated 2026-11-12: **D-U1** and **D-U10** resolved by owner). Sources: umpire `README.md`, `00-SPEC.md` §2/§3/§5, `calibration/README.md`, `design/W9-TRANSFER.md`, `README-MCP.md`, `reports/*` (umpire repo). Packet P4 (`ts`) and P5 (calibration transfer) and A5 finding link in.

## Register

### D-U1 — Calibration scope (seed: corpus-fitted calibration transfers?)
Options: (a) per `(pin, seed, label set)` artifacts only; (b) per-pin generic calibration + label-set adaptation; (c) no calibration, raw only.
Trade-offs: per-scope is honest (calibration/README: per pin/seed/label/distribution, harness refuses mismatch) but sparse; generic risks miscalibration on new label sets.
**Resolved 2026-11-12 (owner; G2 / Packet P5 approved, `reports/RR-G2APPLIED-20261112.md`):** Option **(a)** adopted — publish per-corpus `(pin, seed, label set)` calibration artifacts only, with **no transfer claim** until a held-out evaluation across $\ge 5$ new label sets (sizing $n \approx 180 \times (h/2)^2$, cluster bootstrap across sets, cross-fitting) passes a preregistered $\pm 2$-point equivalence test (Brier/log-loss primary, ECE secondary), and carry the timeless caller caveat verbatim on all three umpire surfaces (`umpire/mcp_server.py` `INSTRUCTIONS` and `decide` tool description, and `umpire/00-SPEC.md` §3, commit `64b97fb`): *"Calibrated confidence was fitted on umpire's own label sets and has not been shown to transfer, so treat it as an uncalibrated score for your labels until you check it on a sample of your own labelled rows."* Dated evidence kept here so the spec stays timeless: in W9 (`design/W9-TRANSFER.md`, `RR-W9TRANSFER-20261101`, $n=180 = \text{test} \cup \text{val}$ on `cal-precision-v3.json` `cal-v1:057a5a35a9d4ec71`), paired 95% CIs included zero ("no detectable degradation" at $n=180$), but ECE point estimates worsened (`A1` 7.5→12.2% = +4.7 pp; `A2` 4.9→6.8% = +1.9 pp).

### D-U2 — Baseline comparisons the evaluation lacks
Options: (a) add embedding-NN, logistic regression, small fine-tuned classifier, stronger model with structured output + logprobs; (b) pick one; (c) none (corpus-fitted only).
Evidence needed: same 480-row corpus, same split, same metrics (accuracy/ECE/Brier). If baselines beat calibrated umpire, the primitive's value claim weakens. Reversibility: high (new eval harness, no ledger change). Decides: owner.

### D-U3 — Determinism claim and scope
Claim today: 470/480 strict on one machine/one build (`00-SPEC.md:210`, README:234); 10/480 distribution-only (concurrency attribution). Cross-machine/cross-build UNMEASURED (`00-SPEC.md:219`, `spec/determinism.py` matrix exists). Options: (a) keep quiescent same-build scope; (b) expand to cross-machine (needs second machine + hash comparatives); (c) soften to page-table-only determinism. Reversibility: low once published (claim). Decides: owner.

### D-U4 — Installation weight (seed: pinned local server vs hosted)
Options: (a) pinned llama-server + model files only (current); (b) optional hosted model (T14 hybrid); (c) both. Evidence: latency honesty note (~100–600 ms local vs ~70 ms hosted, `00-SPEC.md:21`); T14 decided local-only now, hybrid later (`reports/RR-T14-20261023.md`). Installing = `tools/install-pins.py` (~4.5 GB) + `build-runner.sh`. Reversibility: medium (republish weights/runner). Decides: owner.

### D-U5 — What the ledger records (privacy)
Options: (a) identity only (refs + hashes, current); (b) include prompt text (breaks the "never mutated state" rule); (c) hash-only content sidecar. Evidence: ledger carries no content, records carry state but stay local. Reversibility: low (wire change, needs new profile). Decides: owner (+ D14 redaction interaction).

### D-U6 — Ref identity rule (`model_pin`/`seed`) vs R1 (seed list item)
Options: (a) exclude pin/seed (current, R2); (b) include pin (splits A/B arms into new pages); (c) include seed. Evidence: A2 F2 — inclusion destroys priced re-decide semantics. Reversibility: low (identity rule). Decides: owner.

### D-U7 — MCP surface and stability
Tools today: `decide, pins, health, calibration_info, validate, replay` (README-MCP). Options: (a) freeze 6 tools; (b) add `calibration_fit` / `baseline_*` tools; (c) version the surface (`mcp.version`). Evidence: `mcp_server.py` stdio, one request at a time. Reversibility: high (additive tools). Decides: owner.

### D-U8 — Confidence semantics (seed: uncertainty reporting)
Options: (a) raw dispersion only; (b) raw + calibrated (`calibrated.confidence`, current M2); (c) calibrated only. Evidence: `calibrated` is sidecar, never mutates raw (00-SPEC §3). Uncertainty: paired-bootstrap CIs, test-split only (v3: ECE 0.0302, Brier 0.1726 at 0.7083 accuracy). Reversibility: medium. Decides: owner.

### D-U9 — Artifact identity and template stamping
`prompt_template_sha256` in `harness/pins.json` + fail-hard on drift (M1c). Options: (a) keep fail-hard; (b) warn-only. Evidence: corrupted-template incident caught by provenance probing (RR-M1C). Reversibility: low (safety property). Decides: owner.

### D-U10 — Ledger ordering and `ts` (seed: P4 asked whether `ts` must be mandatory)
Ruled 2026-11-12 (owner; the P4 answer reviewed and approved): `ts` stays **optional** in umpire ledgers,
paired with a consumer rule, which is now written down in `umpire/00-SPEC.md` §2 — inserted after the
profile constraints (L1–L5) and before "### Identity minting": within a ledger, line order is the decision
order (`session.open` is first, one decision = one turn); ledgers carry no wall-clock `ts`, and an absent
`ts` means **unknown, never zero**; line order implies no order across ledgers; a consumer needing
cross-session order must supply its own semantics. **Documentation only** — no L-number, no validator
change, no negative, no change to any ledger or fixture. The clause is written to be **timeless**; the
facts it rests on live here, because they will go stale: per the 2026-11-09 P4 record, none exists on
the books (W14 keys per environment; the A5 analysis is single-session; `latency_ms` rides the records
sidecar, not the ledger). Options considered: (a) make `ts` mandatory — refused (it breaks the v0-only
emitters and the 0.1/v0 asymmetry, and needs a version gate above 0.1); (b) leave it unstated — refused
(a consumer then has no rule for an absent `ts`, and "unknown" would be read as "zero"); (c) optional plus
a consumer rule — **adopted**. Independent of the D18 note: C2 is key order WITHIN an event, C3 the
canonical form of hash inputs, and this is event order BETWEEN lines — the three surfaces do not overlap.

## Positioning brief — see `design/umpire-positioning.md`

Top-packets: P5 (D-U1 calibration transfer — is n=180 enough?), P6 (D-U3 determinism scope), P7 (D-U2 baselines). Each ≤ 3 KB, template format, see `handoff/packets/`.

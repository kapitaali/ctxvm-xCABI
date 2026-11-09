# Umpire design-choice register (A6) — inputs only, no choice made

**Date:** 2026-11-09. Sources: umpire `README.md`, `00-SPEC.md` §2/§5, `calibration/README.md`, `design/W9-TRANSFER.md`, `README-MCP.md`, `reports/*` (ompire repo, read-only). Packet P4 (ts) and A5 finding link in.

## Register

### D-U1 — Calibration scope (seed: corpus-fitted calibration transfers?)
Options: (a) per `(pin, seed, label set)` artifacts only; (b) per-pin generic calibration + label-set adaptation; (c) no calibration, raw only.
Trade-offs: per-scope is honest (calibration/README: per pin/seed/label/distribution, harness refuses mismatch) but sparse; generic risks miscalibration on new label sets. Evidence needed: W9 transfer arms at n=180: ECE rises A1 7.5→12.2%, A2 4.9→6.8%, paired 95% includes zero — "no detectable degradation" at n=180 (RR-W9TRANSFER-20261101). Reversibility: artifact is sidecar; swap is cheap. Decides: owner (D-U).

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

## Positioning brief — see `design/umpire-positioning.md`

Top-packets: P5 (D-U1 calibration transfer — is n=180 enough?), P6 (D-U3 determinism scope), P7 (D-U2 baselines). Each ≤ 3 KB, template format, see `handoff/packets/`.

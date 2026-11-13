# RR-G2APPLIED-20261112 — G2 applied: the calibrated-confidence transfer caveat lands in `umpire` (`64b97fb`) and **D-U1** is resolved in `design/umpire-design-choices.md`

Card: owner approved **G2** (`apply G2`), ratifying Packet P5's **D-U1** option (a) and applying the
caller transfer-caveat sentence to `~/Documents/umpire/mcp_server.py` and `~/Documents/umpire/00-SPEC.md`
§3 (`64b97fb`, `reports/RR-G2CALLER-20261112.md`).

## 1. What landed in `~/Documents/umpire` (`64b97fb`)

The reviewer's verbatim caller sentence (`reports/RR-P5CAL-20261110.md`):

> Calibrated confidence was fitted on umpire's own label sets and has not been shown to transfer, so
> treat it as an uncalibrated score for your labels until you check it on a sample of your own labelled
> rows.

Inserted at all three pre-verified surfaces (`reports/RR-UMPIREREADY-20261111.md` §2):
1. `~/Documents/umpire/mcp_server.py:74–77` (`INSTRUCTIONS`), immediately after `"it is not a correctness
   guarantee and is opt-in."`
2. `~/Documents/umpire/mcp_server.py:85–88` (`TOOLS[0]["description"]` for `decide`).
3. `~/Documents/umpire/00-SPEC.md:116–118` (§3 *"Calibrated view (M2, optional)"*), before `"M2 details
   and limitations: calibration/README.md."`

Verification in `~/Documents/umpire`:
- `python3 -m py_compile mcp_server.py` and string assertions on `mcp_server.INSTRUCTIONS` and
  `mcp_server.TOOLS[0]["description"]`: PASS.
- `bash tools/run-ci.sh` in `~/Documents/umpire`: **`[umpire-ci] ALL GATES GREEN`** (207 ledger
  conformance checks + 14/14 negatives, 4/4 page-table roundtrips, v1/v2/v3 calibration corpora +
  checksums, 68 unit tests, 9/9 determinism derivations, 7 calibration-ci metrics, 2 transfer-eval sets,
  hub byte-identity).

## 2. What landed in `ctxvm`

1. **`design/umpire-design-choices.md`**:
   - Header updated to reflect that `D-U1` and `D-U10` are resolved while `D-U2..D-U9` remain open inputs.
   - `D-U1` updated with the ratified **Option (a)** decision (per-`(pin, seed, label set)` artifacts
     only; no transfer claim until $\ge 5$ held-out label sets pass the preregistered $\pm 2$-point
     equivalence test on Brier/log-loss primary, ECE secondary) and carries the dated W9 transfer facts
     (`n=180`, `A1` 7.5→12.2% ECE, `A2` 4.9→6.8% ECE) so the spec/MCP text stays timeless.
2. **`handoff/QUESTIONS-ARCHIVE.md`**: P5 entry updated with the ratification locator (`64b97fb`,
   `design/umpire-design-choices.md` `D-U1`, `reports/RR-G2APPLIED-20261112.md`).
3. **`design/ROADMAP-OPENCODE-LANE.md`**: `[x] G2` checked (`MET`) and `§6` updated.
4. **`handoff/PROJECT-STATE.md`**: updated in its own single-file commit.

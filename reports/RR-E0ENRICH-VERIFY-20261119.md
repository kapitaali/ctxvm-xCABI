# RR-E0ENRICH-VERIFY-20261119 — verified: fixture-bank v2 (2-hop causal chain, 442/442 checks) and parked E0 design note

Review lane, verify-then-record. Subject: `e8149b5` (`research/fixture-bank/` v2 enrichment +
`research/e0-proposal/PREREG-E0-DRAFT-20261119.md` parked design note, 28 files). Date 2026-11-19. The research
lane explicitly left `reports/LOG.md`, `reports/RR-DAY-20261119.md`, and `handoff/PROJECT-STATE.md` to the review
lane (`research/fixture-bank/RR-FIXBANK-PHASE0-20261119.md` §10). No `research/**` byte, code, model call, spend,
or push by this lane.

## 1. Evidence re-derived

| check | command | result |
|---|---|---|
| commit scope (`e8149b5`) | `git show --stat --oneline e8149b5` | 28 files under `research/fixture-bank/` and `research/e0-proposal/PREREG-E0-DRAFT-20261119.md` |
| manifest integrity | `(cd research/fixture-bank && sha256sum -c manifest.sha256)` | **24/24 OK** |
| Phase 0 v2 verifier (442 checks) | `(cd research/fixture-bank && node verify-bank.mjs)` | **442/442 checks passed**, `BANK_PHASE0_OK` (all 242 v1 checks + per-item $T(p_{j_1})=2$, $T(p_{j_2})=1$, distractor sum $0$, $\mathrm{Var}(T)>0$ on `referenceAnswer`; `referenceAnswer` absent from $\tau$ and trace; structural causal uniqueness of $j_1$, $j_2$, and `target.md` facts) |
| independent 3-tier $T(p)$ verification | Python scan of `bank.json` (`schema: ctxvm-content-bearing-fixture-bank/v2`) under the frozen identifier rule (`<topic>-doc-<j>`, `doc<j>_value`) | **20/20 items** have $T(p_{j_1})=2$, $T(p_{j_2})=1$, all 8 distractors $=0$, $\sum T(p)=3$, $\mathrm{Var}(T)=0.41 > 0$ (e.g., `fb01`: `primary=1`, `fallback=4`, $T=[2,0,0,1,0,0,0,0,0,0]$) |
| RFC-0.1 schema conformance | `python3 spec/rfc-0.1/validate_schema_v0_1.py research/fixture-bank/traces/*.jsonl` | `OK: all checks passed` across all 20 traces |
| Rust replay authority | `rust/target/release/replay` across all 20 `research/fixture-bank/traces/fb*.jsonl` | **20/20 exit 0, `divergences: []`** |
| parked E0 design note | inspect `research/e0-proposal/PREREG-E0-DRAFT-20261119.md` | Banner states `Status: PARKED on open-weight model snapshot & compute-route ruling — owner ruling RR-E0ENRICH-20261119, $0 spend. NOT a runnable preregistration`; §4 carries the constant-$T$ degeneracy guard ($\ge 15/20$ items must have $\mathrm{Var}(T(p)) > 0$ else `INVALID — constant T`, never `NaN`, plus tie-safe mean-$\Delta$ contrasts); §5 documents the 2-hop causal profile and v1→v2 history; §9 sign-off lines are blank |

## 2. Scope guard

`research/fixture-bank/` v2 is a **synthetic content precondition, not an experiment result**, and
`research/e0-proposal/PREREG-E0-DRAFT-20261119.md` is a **parked design note, not a runnable preregistration**.
Zero model calls, zero spend, no E0/E2 GO, no plugin/paper parity, no cost-saving (law 7) or unscoped determinism
(law 8) claim; nothing pooled with E1, E2, M1, M2, or M3. E0 compute route and E2 cost ceiling remain owner-gated
at **$0**.

## 3. Books closed by the review lane

- Appended the owed LOG row for `RR-FIXBANK-V2-20261119` and this verification card (`RR-E0ENRICH-VERIFY-20261119`)
  to `reports/LOG.md` (four pipes each).
- Added the day-file section to `reports/RR-DAY-20261119.md`.
- Updated `handoff/PROJECT-STATE.md` to record fixture-bank v2 and the parked E0 design note as LANDED & VERIFIED.

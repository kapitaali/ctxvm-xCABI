# RR-FIXBANK-REVIEW — verified: content-bearing `tool_recall` fixture bank (Phase 0) and `RR-HVREV` 0.13.29

Review lane, verify-then-record. Subject: `12a9809` (`research/fixture-bank/`, card
`research/fixture-bank/RR-FIXBANK-PHASE0-20261119.md`, 27 files), plus the preceding hermes-lane commits `dfc98b3`
and `5615399` (`reports/RR-HVREV-20261119.md`, plugin `0.13.29` canonical `harnessVersion` resolver, suite 229).
Date 2026-11-19. No `research/**` or `packages/**` byte written by this lane; no model call, spend, gateway restart,
or push.

## 1. Fixture-bank Phase 0 verification (`12a9809`, `RR-FIXBANK-PHASE0-20261119`)

Every zero-spend re-derivation command from `RR-FIXBANK-PHASE0-20261119.md` §9 was executed from the repository
location (`research/fixture-bank/`):

| check | command | result |
|---|---|---|
| manifest integrity | `(cd research/fixture-bank && sha256sum -c manifest.sha256)` | **24/24 OK** (`bank.json`, `generate-bank.mjs`, `verify-bank.mjs`, `RR-FIXBANK-PHASE0-20261119.md`, ` traces/fb01.jsonl`..`fb20.jsonl`) |
| Phase 0 verifier (242 checks) | `(cd research/fixture-bank && node verify-bank.mjs)` | **242/242 checks passed**, `BANK_PHASE0_OK` (`body↔contentHash`, `body↔tokens`, `page.declare` pairing, pure `tool_recall` stratum = 1 fault/item × 20 items, 11 unique pages/item = 220 pages total, $\tau$ vs $\tau \setminus p$ reconstruction, no filesystem/bank-path leakage in trace or $\tau$/$\tau \setminus p$) |
| RFC-0.1 schema conformance | `python3 spec/rfc-0.1/validate_schema_v0_1.py research/fixture-bank/traces/*.jsonl` | `OK: all checks passed` across all 20 traces |
| Rust replay authority | `rust/target/release/replay` across all 20 `research/fixture-bank/traces/fb*.jsonl` | **20/20 exit 0, `divergences: []`** |
| privacy (law 9) | synthetic generated content only (`generate-bank.mjs` via real `@ctxvm/node` `createTrace`) | 0 private/live traces committed |

### Scope guard (recorded verbatim per §9)

This bank is a **synthetic content precondition, not an experiment result**. It resolves the two physical blockers
on `corpus/m1`–`m8` identified in `RR-E2HOLD-20261119` (content-blind traces and <20 traces with $\ge 10$ pages in
the `tool_recall` stratum) by providing paired $(\tau, \tau \setminus p)$ text and valid xCABI v0.1 traces for 20
synthetic items × 11 pages. It authorizes **no E0 or E2 GO**, makes no model call or spend, and makes no
plugin/paper parity, cost-saving (law 7), unscoped determinism (law 8), or model-quality claim. Answer-keys,
answer-change grading, noise-floor runs, E0 compute-route selection, and any E2 cost-ceiling sign-off remain
owner-gated at **$0**. Nothing here is pooled with E1, M1, M2, or M3.

## 2. Companion verification of `RR-HVREV-20261119` (`dfc98b3`, `5615399`)

- `python3 -m pytest packages/hermes -q` (with `CTXVM_*` cleared) → **`229 passed, 15 subtests passed in 1.86s`**.
- `bash tools/sync-plugin.sh --check` → installed `~/.hermes/plugins/ctxvm-tracer` matches repo `0.13.29`
  (gateway restart remains operator-owned).

## 3. Books closed by the review lane

- Appended the owed LOG row for `RR-FIXBANK-PHASE0-20261119` and this verification row (`RR-FIXBANK-REVIEW`) to
  `reports/LOG.md` (four pipes each).
- Added the day-file section to `reports/RR-DAY-20261119.md`.
- Updated `handoff/PROJECT-STATE.md` to record fixture-bank Phase 0 as LANDED & VERIFIED (precondition only; E0/E2
  still owner-gated at $0) while preserving the `0.13.29` / `RR-HVREV` hermes update from `5615399`.

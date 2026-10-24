# RR-UCVERIFY — Use-case memos: claimed-vs-observed verification sweep

- **Card:** verification sweep (no code change) · **Status:** DONE
- **Date:** 2026-10-24 · **Repo:** ctxvm (`main` @ `e81fb9b`)
- **Subject:** the three design memos `research/use-case-{1-cross-agent-handoff,2-agent-forensics,3-capacity-planning}.md` — every verifiable claim re-run against the repo; implementation-plan sections classified separately
- **Method:** light-gate re-run (rust / validator / metrics / ODPS / ODCS / hub / replay CLI, all on this machine 2026-10-24), per-claim verdict tables, memos remain untracked (other workstream's files; read-only here)
- **Delivered verdict (drives next card):** memo gates PASS at the data layer; **UC2 build-first** = replay CLI flags (`--turn/--pin/--output`) are the missing piece the memos cite and the repo lacks

## 1. Light-gate re-run (observed 2026-10-24)

```
$ cargo test                       # workspace, from scratch
29 passed · 0 warnings

per-crate #[test] counts: ctxvm-conformance 8 · ctxvm-core 11 ·
ctxvm-codec 9 · ctxvm-tokenizer 1        (sum 29)

$ rust/target/debug/replay <f>     # 11 trace-domain fixtures
exit 0  corpus/m1/{opencode-echo,session-healthy,session-thrashing,
                  tracer-healthy,tracer-recall}.jsonl
exit 0  corpus/m2/{live-echo,live-thrash}.jsonl
exit 0  benchmarks/metrics/fixtures/{session-healthy,session-thrashing}.jsonl
exit 1  rust/crates/ctxvm-conformance/vectors/session-divergent.jsonl   (by design)
exit 1  rust/crates/ctxvm-conformance/vectors/events-v0.jsonl           (line-domain
        event-vocabulary fixture, not a session trace — divergent verdict is correct)

$ python spec/rfc-0/validate_schema.py
SCHEMA CONFORMANCE: PASS — 55 checks (50 positive vector lines + 5 engineered negatives)

$ python spec/rfc-0/validate_schema.py \
    benchmarks/metrics/fixtures/session-healthy.jsonl \
    benchmarks/metrics/fixtures/session-thrashing.jsonl
SCHEMA CONFORMANCE: PASS — 108 checks (50 + 12 + 41 positive lines + 5 negatives)

$ python benchmarks/metrics/metrics.py benchmarks/metrics/fixtures/session-healthy.jsonl
{"events":12, "netTokens":{...}, "faultRecall":null, "touchRatio":…, "waste":…,
 "thrashIndex":{"mean":…}, "netTokenReduction":{"baseline":"counterfactual-no-paging","value":0.0}}

$ venvs/odps/bin/open-data-products validate 04-odps-dataproduct-corpus.yaml --json
valid: true · spec odps 4.1 · errors/warnings/hints empty

$ venvs/odcs/bin/datacontract lint contracts/corpus-0.1.odcs.yaml
lint green (ODCS v3.0.2, datacontract-cli 1.2.7)

$ tools/build-hub.sh               # in-place regen
git status clean → byte-identical rebuild
```

## 2. UC1 — cross-agent handoff

| # | Claim (memo section) | Observed | Verdict |
|---|----------------------|----------|---------|
| 1 | `ctxvm replay` re-applies renderer; exit 0 = divergence-free; exit 1 on divergences (§2, §6) | exit 0 on all 9 session fixtures, exit 1 on the divergent vector | **VERIFIED** |
| 2 | `ctxvm replay trace.jsonl --turn 142` (§3 step 4, §6) | binary takes exactly one positional — no `--turn` | **DESIGN-CONCEPT** (flag not built) |
| 3 | `ctxvm export --odps --session … --turn 142 --output handoff/` (§3 step 2, §6) | no `export` binary; ODPS packaging exists as committed manifest+hub, not as CLI | **DESIGN-CONCEPT** |
| 4 | `hermes/opencode ctxvm trace … --resume-from handoff/turn-142/` (§3 step 3) | no `trace` subcommand; `@ctxvm/node` exists **source-only** — T8 itself is DONE (RR-T8-20261022); the unbuilt piece is the `ctxvm trace` / `--resume-from` CLI **binary**, not the tracer | **DESIGN-CONCEPT** |
| 5 | `ctxvm diff session-a.jsonl trace-142.jsonl` (§3 step 4, §6) | no `diff` binary | **DESIGN-CONCEPT** |
| 6 | `cargo test --package ctxvm-conformance` → "28+ tests green" (§6) | 8 tests in that package; **29** at workspace scope, 0 warnings | **ERRATUM** (scope) |
| 7 | validator "SCHEMA CONFORMANCE: PASS (108 checks)" (§6) | PASS yes — but 108 requires the two-fixture argv form; `python spec/rfc-0/validate_schema.py trace.jsonl` prints the 55-check form | **VERIFIED** with argv caveat |
| 8 | ODPS validate output `{valid, spec: odps 4.1, errors: [], warnings: [], hints: [], …}` + explicit note that `compliance_level`/`production_ready` are not emitted by SDK 4.1 CLI (§6) | matches observed SDK output verbatim | **VERIFIED** |
| 9 | §7 citations: `02-xcabi-events-v0.md`, `03-tracer-api-ts.md`, `08-HANDOFF.md`, `spec/rfc-0/`, `rust/crates/ctxvm-conformance/`, `reports/RR-BOARD-COMPLETE-20261022.md` | all present at `e81fb9b` | **VERIFIED** |
| 10 | Honest scope: cross-harness handoff not byte-identical; v0 observes only (§4, §5) | consistent with repo reality (core has no eviction path; v0 declare⇒resident) | **VERIFIED** |

**UC1 verdict:** data layer verified; §3/§4 CLI surfaces are one step ahead of the code and correctly labeled design concepts; two actionable errata (`--turn` flag, test-count scope).

## 3. UC2 — agent forensics

| # | Claim (memo section) | Observed | Verdict |
|---|----------------------|----------|---------|
| 1 | `ctxvm replay session.jsonl --turn 37 --output render-turn-37.jsonl` dump of the exact message array (§3 P1, §4, §6) | no `--turn`/`--output`; the CLI prints a divergence-report JSON (events/divergences/violations) to stdout — it does **not** dump renders | **DESIGN-CONCEPT** |
| 2 | `ctxvm profile session.jsonl --window turns 30-37` / `--event page.fault` / `--source tool_recall` (§3 P2–P3) | no `profile` command anywhere in the repo | **DESIGN-CONCEPT** |
| 3 | Counterfactual `ctxvm replay … --pin page:tool:read_file(src/auth/session.ts) --output …` + diff (§3 P4) | `--pin` not implemented; renderer in `ctxvm-core` is a pure function of (events, indices), so force-resident re-render is buildable on the existing API | **DESIGN-CONCEPT** (viable build-first target) |
| 4 | Honest limit: "a pinned render proves **visibility**, not **correctness**" (§3 P4, §5) | framing is sound and internally consistent | **VERIFIED** (framing) |
| 5 | `cargo test --package ctxvm-conformance` → "28+ tests" (§6, §5 deps) | 8 in package / 29 workspace | **ERRATUM** (scope, same as UC1-6) |
| 6 | `python benchmarks/metrics/metrics.py benchmarks/metrics/fixtures/session-thrashing.jsonl` + "18/18 pytest green" (§6) | correct spelling; 18/18 verified; JSON carries all four metrics | **VERIFIED** |
| 7 | §7 citations: `reports/RR-M1-20261022.md` ("M1 report with P4 (re-decide pricing) and P5 (validator) results") and `reports/RR-M1AB-20261022.md` ("M1b A/B…") | **both files do not exist** (`reports/` inventory has no RR-M1\*); "P4"/"P5" appear nowhere in the repo (grep) | **ERRATUM** (phantom citations; §2's "metric simulator (T3)" and the fault taxonomy in `02-xcabi-events-v0.md` are real) |
| 8 | Exit criteria: profile shows faults with correct sources; pinned render differs from original (§5, §6) / `validate_schema.py` passes "108 checks" | surfaces absent; validator PASS holds under the argv caveat | **DESIGN-CONCEPT** / argv caveat |

**UC2 verdict:** the forensic *data* story (trace + taxonomy + metrics) is verified; the forensic *synthesis* CLI (`--turn`/`--output` render dump, `profile`, `--pin`) is exactly the not-yet-built surface — and the decomposition "context-management fault vs model reasoning fault" is independently checkable once counterfactual rendering exists. One phantom-citation erratum to fix.

## 4. UC3 — capacity planning & pager benchmarking

| # | Claim (memo section) | Observed | Verdict |
|---|----------------------|----------|---------|
| 1 | Metric simulator: four formulas, two fixtures, 18/18 pytest, CLI prints JSON (§2, §6) | verified; JSON keys `netTokens`, `faultRecall` (null on healthy = honest 0-eviction case), `touchRatio`+`waste`, `thrashIndex`, `netTokenReduction{baseline,value}` | **VERIFIED** |
| 2 | Policy simulation `metrics.py … --baseline naive|lru|fault-pin|size-based` (§3 S3, §5) | `--baseline` semantics differ: it takes a **recorded naive-context-stuffing trace path** (default: counterfactual). No policy library exists in `metrics.py` — LRU/fault-pin/size-based are not implemented | **ERRATUM** (semantics; illustrative table honestly marked as estimates, but the shown commands cannot run) |
| 3 | `ctxvm export --odps corpus/0.1/sessions/ --tag …` producing `corpus.jsonl.zst/manifest/llms.txt/checksums` (§3 S2, §4) | no export binary; real packaging = committed `04-odps-dataproduct-corpus.yaml` + hub (validated) | **DESIGN-CONCEPT** |
| 4 | ODPS manifest (SDK 4.1 valid), ODCS v3.0.2 lint green, hub byte-identical rebuilds (§2, §6, §7) | all re-verified above | **VERIFIED** |
| 5 | Manifest KPIs `kpi-agent-token-efficiency` / `kpi-fault-recall` / `kpi-net-token` / `kpi-touch-ratio` and DQ checks `replayDeterminism` / `pinLint` / `redactionScan` (§3 S2, §4) | all present verbatim in `04-odps-dataproduct-corpus.yaml` (L74–93, L149–173) | **VERIFIED** |
| 6 | M0 gates: net token ≥1.5×, fault recall ≥95%, replay determinism 100%, conformance 100% (§3 S4) | matches `07-benchmarks-go-no-go.md` L32–34 | **VERIFIED** |
| 7 | `tools/build-hub.sh --check-identity` (§4, §6, §7) | script takes no flags; byte-identity is demonstrated by regen + `git status` clean (or `sha256sum -c hub.sha256`, per RR-T12) | **ERRATUM** (flag not implemented) |
| 8 | Cross-harness comparability "indicative, not definitive" + local-vs-hosted ≥1.5× scoping (§3 S3/S4 notes, §5) | sound; consistent with the recorded-vs-simulated fault-stream caveat | **VERIFIED** (framing) |

**UC3 verdict:** the measurement stack and packaging claims are fully verified; the policy-simulation surface is the one substantive gap (flag semantics erratum, honest-scope note already in place).

## 5. Errata classes (for the memo author's next edit)

- **A. CLI spellings (UC2/UC3):** `ctxvm profile … --window turns 30-37` / `--source` / `--event` (no profile); `metrics.py --policy|--fixture|--kpi` (flags don't exist; real flags: positional trace, `--baseline <naive-trace-path>`, `--windows`); `--baseline <policy-name>` misuse; `--check-identity`.
- **B. Test-count scope (UC1/UC2):** "28+ tests" is true only workspace-wide (29); `--package ctxvm-conformance` yields 8.
- **C. Validator figures (UC1/UC2/UC3):** "108 checks" is the two-benchmark-fixture argv form; per-trace or default invocation prints 55 (50 vectors + 5 negatives).
- **D. ODPS CLI shape:** correctly stated by all three memos (`compliance_level`/`production_ready` absent from SDK 4.1 CLI) — confirmed, no erratum.
- **E. Citations (UC2 §7):** phantom reports `RR-M1-20261022.md`, `RR-M1AB-20261022.md`; "P4/P5" nowhere in repo. Also **UC1 stale status lines**: §7 "T8 (`@ctxvm/node` tracer) is the next frontier" and the next-step "The tracer implementation is the missing piece" reflect the pre-T8-landing board; T8 landed 2026-10-22 (12/12 tests, both fixtures schema-PASS + replay-clean) and is load-bearing for T9/T12.
- **F. Replay flags (UC1/UC2):** `--turn`/`--output`/`--pin` cited but unbuilt — this is the delivered build-first verdict, not a correctness erratum.

**Framing errata: none.** All three memos disclaim their future-facing CLI sections and scope their honesty notes correctly; no overclaimed *numbers* were found.

## 6. Actions

1. Memo author: apply errata A/B/C/E on next pass (memos are untracked other-workstream files; not edited or committed here — those edits belong to the memo owner).
2. **UC2 build-first goes next:** extend the replay CLI with `--turn N`, `--output FILE`, `--pin <logical_ref>` (force-resident re-render), plus tests and fixture re-run — this closes claim class F and unlocks the UC2 Phase-1/Phase-4 surfaces on top of `ctxvm-core`.
3. Housekeeping rule adopted for future memos: every cited command must be executed verbatim in the repo before its memo reports "backed by committed artifacts."

## 7. Files

- new: `reports/RR-UCVERIFY-20261024.md`, `reports/LOG.md` row.
- read-only: `research/use-case-{1,2,3}-*.md` (untracked, other workstream).
- no code touched.

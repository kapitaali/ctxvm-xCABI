# W22-CI-COVERAGE (D20) — gate coverage for packages/deepseek (@ctxvm/dsh)

Status: placement cleared 2026-11-16 (P15, `handoff/packets/P15-w22-ci.md`,
re-checked at `be72ae8`); D-number **D20** (review-lane verified next-free 2026-11-16,
filed under P15's "use your next free number" — rename on one owner word).
`tools/**` is hermes-lane-owned; this card records the decision and the landed step,
it does not edit tools.

## The gap, stated as measured

The gate did not run the adapter's tests — not the same as the adapter being untested
(`node --test packages/deepseek/test/event-map.test.ts` was 5/5 by hand, 2026-11-16).
`grep -n 'deepseek' tools/run-ci.sh .github/workflows/ci.yml` returned 0 hits while
`packages/deepseek` was landed (`9a87ba2`), so every ALL GATES GREEN since 2026-11-15
described a tree whose adapter no step touched — the false green this card closes.
Falsifier: an existing CI step exercising the package through a path the grep missed.
Checked 2026-11-16 — no hit; falsifier not triggered.

## Landed (7475a5b, hermes lane, RR-W22CI-20261116)

`tools/ci-deepseek.sh`, called from gate 2 after the node build:

1. creates the workspace link ITSELF, `ln -sfn ../../../node
   packages/deepseek/node_modules/@ctxvm/node` — repo-relative, computed from the
   package. The tree had carried a hand-made ABSOLUTE link and a fresh clone has none;
   the gate depends on neither (P15 pull correction folded in).
2. runs `test/event-map.test.ts` explicitly (interim scope) and prints on every run
   the two files it does NOT cover and why: `page-table.test.ts` (needed
   `@deepseek-ai/schemastery`, private registry, `npm install` E404) and
   `replay.test.ts` (skips without `CTXVM_TEST_TRACE`; no tracked fixture).
3. fails on a failing OR SKIPPED gated test and on fewer than 5 passing — a skip must
   not read as a pass. Red-before proven, each mutation restored byte-identical:
   deliberate failing test → exit 1; gated file swapped for the skipping one → exit 1;
   `node_modules` deleted → exit 0 with the link rebuilt (the fresh-clone case).

Gate after landing: ts suites 24 + 62 + 46 + 5, python 207 + 8 + 66, ALL GATES GREEN
(counts derived by run_counted, not hardcoded).

## Schemastery decision (P15): (ii) injectable factory, (iii) was the interim

(i) infeasible: `npm install --omit=peer` E404 on `@deepseek-ai/dsh-type-meta`
(private registry, confirmed 2026-11-16 via `npm view`). (ii) landed via the dsh lane:
`src/config.ts` / `src/page-table.ts` keep only type-only schemastery imports and
export factories (`makeConfig(z)`, `makePageTableStateSchema(z)`); the runtime entry
`src/index.ts` injects the real `z` at load and exports a real `Config`
(handoff 04 — also fixes the a57592b `Config = null` regression where cordis
`resolveConfig` skipped validation and defaults were never applied). (iii) interim
stood meanwhile: event-map gated, page-table and replay named as not gated.

## Remaining follow-ups (hermes lane implements tools/**, dsh lane owns packages/deepseek)

1. Switch `ci-deepseek.sh` GATED from `test/event-map.test.ts` to the whole `test/`
   directory once handoff 04 lands (page-table now runs outside DSH: whole dir is
   8 tests, 7 pass, 0 fail, 1 skip on 2026-11-16). Delete the NOT-GATED page-table
   line at that point; keep printing the replay skip by name.
2. `replay.test.ts`: supply a tracked fixture trace via `CTXVM_TEST_TRACE` so the
   skip becomes a run, or keep reporting the skip by name — a skip must not read
   as a pass.
3. Option B (root tsconfig references for type coverage) deferred until the test
   step runs the whole directory.

## Verification rules

- `bash tools/run-ci.sh` rc=0 WITH the step; the kept step log shows the adapter
  tests ran, the count printed, skips named. Totals dated, never hardcoded (AGENTS.md §8).
- `python3 tools/ci-rehearsal.py` still passes.
- Clear ambient `CTXVM_*` before the gate: `for v in $(env | grep '^CTXVM' | cut -d= -f1); do unset "$v"; done`.

## Out of scope

No changes to `spec/`, `corpus/`, `rust/`, `packages/{node,opencode,ai-sdk,hermes,py}`,
`research/**`. No cost-saving claim (law 7).

# W8 capture design — the decisive experiment, preregistered before any run

**Status:** PREREGISTERED (design freeze; no data exists under this design yet). The
execution is owner-gated (D5; `08.1-UPDATE-PROMPT.md` §W8: "Preregister before
running: task set, baselines, metrics, thresholds, stopping rule, and budget cap").
**Date:** 2026-11-01. **Author:** repo agent; owner ratifies at the listed gates.

This file is the preregistration record of substance. After the first run exists,
NO content of §1–§11 changes; a mid-run necessity is recorded in the analysis report
under "Deviations from preregistration" (change, reason, affected gate) and any pass
obtained after a deviation is labeled directional, not gate-grade. What locks at T0
(§0) locks BEFORE the first run, not inside it.

## 0. Design freeze and model lock

The D5 law governs: "preregistration fits
or W8 stops; paid-model `prices.json` row needs a locator + date BEFORE the run".
What is frozen TODAY (§1–§11): arms, seams, task grid shape, metric formulas, gates,
stopping rule, budget ledger, D12 ruling, redaction DQ law. What locks AT T0 (inside
the capture commit, before the first run): exact task texts, checker scripts, the
provider/model row, its price figures, and the virtual budget number. Locking values
does not rewrite the design; an altered §2–§9 after any run is what counts as a
deviation.

## 1. Preconditions (all landed, pointers)

| Precondition | Where it proves itself |
|---|---|
| Real tokenization | W2b provider-usage emission (`reports/RR-W2B1-20261031.md`); `providerUsage` rides `call.meta` on the ai-sdk lane; est* stay page-table (D12) |
| Falsifiable metrics | W3 (`reports/RR-W3-20261029.md`; `07-benchmarks-go-no-go.md` §W3 fix: `hard_fault_recall` ground truth, versioned price model, deterministic bootstrap CIs) |
| Hermes adapter | W4 + W4b (`packages/hermes/OBSERVABILITY.md` §1–§3; live-shape scan surface) |
| Cross-harness reality check | W5 (`reports/RR-W5-20261030.md`): hermes emits user-turn traces; the turn-unit law is preregistered below (§3) |
| Pressure reality | W1 (`reports/RR-DOGFOOD-20261029.md` finding 1): zero evictions on every real capture at every observed budget — the experiment must create pressure deliberately |

## 2. Research question and arms

Question (07 §M0): **does paging help?** Can enforcing a virtual context budget with
the v1 `FaultPinPolicy` law keep task accuracy non-inferior while cutting net tokens
1.5× or better versus naive context-stuffing on real tasks with a real model?

Arms (both on the SAME harness, the SAME model, the SAME task grid; the ONLY
configured difference is the context engine):

- **`naive`** — the stock engine (`context.engine` unset → built-in
  `ContextCompressor`). At the task scales preregistered below it never fires (its
  threshold is 75 percent of the real model context, `agent/context_engine.py`
  `threshold_percent: 0.75`), so the arm is context-stuffing under full slack. The
  run records whether compression fired anywhere; if it fired, the affected task is
  dropped from BOTH arms and named (§6 keep rule).
- **`paged`** — the new ctxvm context-engine plugin implementing the v1 law
  (§4), enforcing the virtual budget `vBudget` via `select_context()`.

Both arms run the existing ctxvm observer plugin (scanner, page declares, tracer
flush) unchanged, so each capture is an xCABI trace and every 07 metric computes on
both. The arms differ in the engine selection only — that is the design's one-factor
property, and it must be visible in the capture provenance.

## 3. Harness and the control-plane seam (verified at source, Hermes v0.22.5 pin)

All locators are the installed runtime (`/home/theb/.hermes/hermes-agent/`), the same
pin the W4 audit used.

1. **Selection seam** — `agent/agent_init.py:1904` `_select_context_engine()`:
   `context.engine` config (default `compressor`) → bundled
   `plugins/context_engine/<name>/` loader → general plugin registry
   (`hermes_cli.plugins.get_plugin_context_engine()`, name-matched, copied per agent
   via `clone_for_agent`). Our engine is selected with a profile-scoped
   `context.engine: "ctxvm"`; the naive arm runs the default profile. Validity
   condition: safe-worker mode cannot be active during W8 runs —
   `_select_context_engine` returns `None` under it, silently degrading BOTH arms to
   builtin; the capture harness asserts the mode is off before each run.
2. **Engine contract** — `agent/context_engine.py` ABC:
   `update_from_response(usage)` receives canonical buckets including
   `cache_read_tokens` and `cache_write_tokens` (the docstring names all five);
   `should_compress()` / `compress()` (the engine returns False from the first and
   implements the second only to satisfy the abstract contract — its budget is
   enforced by selection, not compaction; `emit_automatic_compaction_status = False`
   suppresses engine status noise); `select_context()`
   per-request resident-set replacement: runs on EVERY provider request, may replace
   the list, is request-only and MUST NOT be treated as persisted transcript state,
   and runs before prompt cache-control so breakpoints re-derive on the selected
   list; `prune_tool_results_only()` deterministic trim with a separate trigger;
   `on_turn_complete()` optional observation. Engine copy-safety: the registry holds
   ONE shared instance; `clone_for_agent()` must deepcopy only engine-owned mutable
   state (the page table is a plain dict of ints/strings — deepcopy is correct).
3. **Ordering law (the cache hazard preregistered as W12 Step 1 predicts it)** —
   `design/runtime-abi/00-reconciliation-and-justification.md` §Step 1: a fork that
   changes the prefix forfeits cache hits, priced by the W3 model. The engine's
   per-request selection therefore follows a deterministic, append-stable order:
   (a) system prompt verbatim FIRST (read-only page), (b) the head protected
   messages (stock `protect_first_n`/`protect_last_n` semantics), (c) the pages
   pinned by faults in first-pin order (a newly pinned page APPENDS after the pinned
   block — pinned order stays frozen for the session), (d) the newest unpinned
   segments (recency tail) filling the remaining budget. Selection
   is required to be a pure function of (page table state, vBudget) — the same state
   must select the same list, and the selection sequence within one turn must be
   append-stable (a page once included by rule (c) stays in position until unpinned
   by the content-change law).
4. **The real hermes turn unit**: hermes is a USER-turn emitter (W4 F2, confirmed live
   by W5 D4). All turn-indexed metrics in this design are computed per detected user
   turn; cross-arm compare uses turn COUNTS from each arm's own trace. No
   turn-unit-based cross-arm normalize trick is allowed; the analysis states the
   unit in every table.
5. **Usage receipt channel** (the D12 fork, ruled in §9).

## 4. The paged arm's policy: v1 `FaultPinPolicy`

The law, from `01-PLAN.md` §Pager (v1) and the citation-checked Pichay text
(arXiv 2603.09023; `research/sources-reviewed.md` rows 48/70–83: single author
Tony Mason, system name Pichay):

- **One fault pins for the session; unpin on content change** (Pichay §3.5, step 4).
- Pinning is per-session persisted state on the engine object (the request-only
  replacement erases nothing — the pin ledger rides the engine's own state across
  turns; `clone_for_agent` copies it per agent).
- The engine maps ctxvm page semantics onto transcript messages:
  - every tool-result body is a pooled page (id from the message's tool identity +
    content rollup the engine computes per turn; the ctxvm observer tokenizes in its
    own bookkeeping — the ENGINE's budget arithmetic uses its own char/token estimate
    consistent with the profile's `apx4-char` tokenizer family, rounded UP so an
    under-count can never overshoot the budget),
  - on a fault-class signal (the model's NEW request references an identifier whose
    page is outside the current window) the responsibility pin is recorded,
  - unpinned pages beyond `vBudget` are dropped from the request list only
    (`select_context`), never from the persisted transcript; the v1 engine returns
    the no-op `prune_tool_results_only` so all selection lives in `select_context`
    and the two seams cannot double-apply inside one capture (v2 MAY use the prune
    seam at its separate lower trigger, this design leaves that open).
- What is ALWAYS in the request list: system prompt, last user message, the head
  protected messages (stock keep law), and any message containing an OPEN tool call
  (unresolved state). A dropped non-resident page that gets re-referenced by the
  model is a FAULT in xCABI terms via the observer plugin's normal surface
  (`tool_recall` when the model re-invokes; `identifier_scan` is inference, never
  gate-grade per the W3 law).

FaultPinPolicy in the v1 sense = the SECOND-demand-pin law as the UC3 simulator
models it (`benchmarks/metrics/policies.py` `fault-pin` @2nd-demand + pinCrunch);
the v0 engine implements that same law against live messages.

## 5. Task grid (preregistered shape; texts freeze at T0)

- `k = 6` task templates, each a REAL repo task on an owner-held local checkout
  (the ctxvm repo itself and one owner-chosen second repo, both real work products:
  documentation updates, refactor-style edits, trace forensics using the repo's own
  CLI). Each template exercises cumulative declared far beyond `vBudget` (the pressure
  requirement from W1 finding 1): the template script must be a natural multi-file
  task (expect tens of thousands of tool-result tokens declared over the task).
- Success criteria per task are MECHANICAL: the template defines an artifact-or-state
  predicate checked by a checker script (e.g., "the patch contains exactly these
  semantic hunks", "the generated report lists names A,B,C" as verified line bundles),
  so the accuracy readout is not model-judged. The checker scripts freeze at T0
  alongside the task texts.
- **`vBudget = 24,000` tokens** for the paged arm (the number locks at T0 next to the
  model's real context; must be at or above the task head path + open-tool-call floor
  + the pinned-page steady state). The T0 lock may CONFIRM or RAISE this number; a
  LOWERING below the preregistered 24,000 is a prereg deviation named in the report
  (it would tune the arms toward PASS).
- Rounds: minimum `R = 3` runs per (task, arm) cell, run in the preregistered
  alternating order per task — naive, paged, naive, paged, naive, paged — so
  wall-clock drift cannot pack one arm into one slot.
- Provider sampling temperature 0 where the provider allows a temperature knob
  (record the knob state in provenance). No retries beyond provider-level failures;
  a provider-failed run is logged with the failure class and is NOT counted as a mode
  failure; it is rerun once, and a second consecutive provider failure drops the cell
  (recorded as missing data, never scored 0).

## 6. Metrics, formulas, gates (07-verbatim, reference-pinned)

Formulas live in `benchmarks/metrics/metrics.py` (the reference implementation, the
verbatim-07 formulas; `07-benchmarks-go-no-go.md` §metric definitions):

- `net_token_reduction = 1 - (paged_net_tokens / naive_tokens)` where net = rendered
  tokens + sum of estimated cache-miss re-normalization — using the RECORDED arms as
  baselines (the metrics CLI takes the recorded naive trace with `--baseline`,
  `benchmarks/metrics/metrics.py` main); the in-module counterfactual
  (`counterfactual_naive`) is the labeled-approximation fallback only where a naive
  capture does not exist, never inside a gate computation.
- gates read `hard_fault_recall` = recovered hard faults / hard faults (W3 ground
  truth: `tool_recall` + `explicit_api` only; identifier_scan/semantic are inference
  surfaces and never gate-grade), recovery law = a full-render FACT after the fault
  turn (the unchanged `_recovered_count` law).
- `thrash_index` over sustained-pressure windows (observational; NO gate in this
  prereg — P-pathology is a synthetic suite and a real-window thrash gate is unstudied).
- `refetch_rate` continuity column (no CI; the module docstring law).
- deterministic bootstrap CIs: seed 20261029 default, 2000 replicates, unit = turns
  for turn-decomposable metrics and the fault events themselves for hard-fault recall
  (`07-benchmarks-go-no-go.md` §W3 item 5). Seed and replicates ride every output.

### M0 gate rows (exact, from 07)

| Gate | Threshold | Fail arrow |
|---|---|---|
| Net token reduction at equal accuracy | ≥1.5× | pivot to pure telemetry-only (no control-plane claims) |
| Hard-fault recall, bootstrap 95% CI lower bound, n ≥ 30 hard faults pooled | ≥95% | add stub-driven hints; forbid prompt pollution |
| Replay determinism | 100% (byte-identical) | core design bug, block |
| Corpus conformance, if a drop happens | 100% golden vectors pass | block; spec unstable |

### "Equal accuracy" — preregistered non-inferiority readout

The pairwise quote is per task: naive and paged success on the SAME task template
(R runs each), the paired difference (paged − naive per task, R run-pairs) resampled
by the task (k template values per replicate, seed law as above), and the gate:

- **PASS condition for the accuracy leg (non-inferiority, margin δ = 10 percentage
  points, one-sided 95%):** the 5th percentile of the paired task-mean difference
  distribution must be ≥ −0.10. Success is the checker script's mechanical verdict;
  missing/failed cells are dropped from BOTH arms for that template (the keep rule:
  no cell contributes accuracy unless BOTH modes have ≥1 clean success verdict) and
  named in the report.
- The NTR gate legs are computed on the same kept grid + the same seed law; NTR is
  reported with its own deterministic CI (resampling units = rounds-within-task, i.e.,
  the observed run pairs, seed law).
- Both gate legs must pass for M0 = PASS. If the NTR leg passes but the accuracy
  leg cannot be evaluated (too few kept templates after the keep rules), the outcome
  is reported as inconclusive per D5's
  "inconclusive is a reportable outcome" language.

## 7. Stopping rule (preregistered)

- **Coverage stopping:** the arms stop when every (task, arm) cell has at least
  R = 3 completed runs AND the pooled hard-fault count across BOTH arms' traces is
  ≥30 (hard faults = explicit re-materializations, and they occur in BOTH arms by
  definition: the naive arm re-reads because the model chose to, the paged arm
  because the page had been dropped) — the recall gate computes at the 95% CI lower
  bound with this preregistered volume floor. Until both conditions hold, after each
  completed cell-set the schedule continues in preregistered round-robin across ALL
  six templates — never selectively (adding rounds to the easiest template alone is
  exactly the cherry-picking the prereg forbids) — until the coverage rule, the
  budget stop (§8), or an abort below fires.
- **Hard abort per task (both arms stop for that template):** the persisted
  transcript reaches 75 percent of the real model context length in the NAIVE arm
  (equivalently the naive arm's own compression fired) — record
  `abort_reason: real-window`, drop the template from BOTH arms, name it in the
  report, count it as a design-pressure shortfall (not a paging failure); prune it
  from the accuracy grid via the keep rule above.
- **Engine-crash abort (the paged arm):** an engine crash is a failed run of that
  cell; four crashes in TOTAL on the paged arm means the engine is UNUSABLE for the
  experiment — W8 halts and reports BLOCKED with the crash traces. A failed
  experiment documented well is its own completed outcome (HANDOFF law).
- **No mid-run expansion:** no task templates, no budget changes, no arm-code changes
  after any run has happened. A discovered defect in the paged engine after runs
  started means the runs become a PILOT record; the real gate re-runs under a new
  design-version commit — never edited mid-flight (mirrors HANDOFF §0 day-close law:
  recorded, never rewritten).

## 8. Budget ledger (D5, cap USD 25; "inconclusive" is a reportable outcome)

- Cap: USD 25, hard, covering ALL W8 paid spend (both arms, reruns, any repair run).
- **Ledger opened in the capture commit** (`reports/W8-SPEND.md` — append-only, one
  row per run: date, arm, task, round, model, input/output tokens per provider
  receipts, computed USD from the pinned price row, running total). The running
  total is the control variable.
- **Price-row lock BEFORE the first paid run** (D5 wording): `benchmarks/metrics/
  prices.json` bumps `priceModelVersion` to 2 with the new row(s): the chosen
  provider + model, `usdPer1mInput`, `usdPer1mCachedRead`, `source` = the provider
  price page URL + the integer access date, `verified: web-verified-T0-date`.
  Null rows never silently substitute (`metrics.py` `load_prices` law, `prices.json`
  v1 note). Free-tier rows (nvidia 0.0 / opencode 0.0, already there) are legal —
  if the owner runs freely the NTR gate STILL evaluates (tokens are the primary
  unit) and the ledger stays at 0.
- **Pre-run cost projection (binding stop):** before each new run, projected =
  observed median USD of completed runs of THAT arm so far (first run of an arm
  arm uses the other arm's median; first run overall = the owner's declared expected
  cost ceiling per run, named in the capture commit); if `spent + 2× projected >
  USD 25` no NEW paid run may start. Runs already in flight finish and are recorded.
  If the stop fires before gate-metric data is sufficient, W8 reports "stopped by
  budget at coverage X of Y with inconclusive-Z" — a reportable outcome (D5 text).
- Est-vs-billed: the ledger's USD column uses the pinned-row arithmetic on est*
  (D12, §9) AND records ACTUAL BILLED SPEND from the provider's own account view
  (D5 text: "pilot reports state ACTUAL BILLED SPEND") — the two columns are stated
  side by side; divergence observations are recorded, never averaged away.

## 9. D12 fork — est-receipt/provider-usage rule (recorded by this design; owner ratifies)

D12 (`reports/RR-DECISIONS-20261031.md` §3) moved the est-recorded fork into THIS
capture design. The ruled option for the W8 lane:

1. `estHitTokens` / `estMissTokens` in the v0.1 schema keep their PAGE-TABLE
   semantics on every lane (no flip of meaning; the schema stays truthful — a v0.1
   `call.meta` records estimates NAMED as estimates).
2. The hermes port gains the provider-usage wiring as a W8 implementation
   precondition (the W2b audit already designated it: "the ports gain the wiring
   when their harness surfaces usage hooks"; `packages/hermes/OBSERVABILITY.md` F3
   and §2 note 4 name `post_api_request.usage` as the seam; the plugin hooks it and
   turns `providerReported` TRUE for the W8 captures — no schema change, the v0.1
   field already exists, `packages/node` W2b is the precedent).
3. W3 pricing (hit @ `usdPer1mCachedRead`, miss @ `usdPer1mInput`; cache-write stays
   UNMODELED in v0 with the report stating ACTUAL BILL beside it) prices the EST
   columns. The analysis states BOTH: est-based net cost AND the provider
   receipt columns (`providerUsage` sums per arm). Divergence between the two is
   reported as an observed fact, with the est column the one the gate reads (because
   the gate formula reads the trace's own cacheEstimate, which is Schema-stable);
   gate-grade cost ALWAYS cites the pinned price version.
4. The W6 OTel gate (fires only on `providerReported`) is untouched: it stays
   est-priced and its condition column reads exactly as before.

## 10. Redaction DQ — the pre-drop blocking gate (08.1 §4, non-negotiable)

- Scope: any trace leaving the owner's machine or any future corpus write — no byte
  passes either boundary without this gate.
- Workspace law: each run executes in a fresh disposable `mkdtemp /tmp/ctxvm-w8-*`
  workspace containing only the task's fixture set (the m8 precedent's standing
  discipline); no user repository state, no credential env dumped, no personal
  files inside the workspace context.
- Per-drop automated scan (the tool ships in the W8 implementation card;
  registered here as the law): every `.jsonl` + `.meta.json` + `.provenance` in
  the drop set is scanned for credential-key patterns (`sk-` prefixes, `AKIA`,
  `ghp_`, `gho_`, `pat_`, `xox[bp]`, `BEGIN ... PRIVATE KEY`, AWS style key headers,
  generic `api_key=`, `Authorization:` headers, long bearer-shaped tokens), `.env`
  style content, EMAILS, absolute `/home/` paths, IPv4 addresses (private ranges
  included), and bare hostnames. Zero matches is mandatory before ANY ship; any
  match fails the drop and the workspace is burned (a CANNOT-SHIP line is recorded
  in the card report; those bytes are never retried unless the owner rebuilds them
  by re-run).
- Provenance record (`provenance.json`, the m8 extension): manual review statement
  + per-file events + the DQ scan's own checksum + scan date + scan list version.
- Publication default = hashes + token counts + ref names; BODIES stay local
  (owner-held working evidence). A corpus drop is a SEPARATE owner gate with its own
  scan pass — this design does NOT preorder a drop (the W5 precedent ruling).
- The `vBudget` control introduces no new data mutation risk; the engine reads
  messages in-process and writes zero files itself (cheap-hooks audit law, the W4
  §3 discipline: no network, no heavy compute, apx ms scale).

## 11. Analysis plan (commands preregistered; re-run of the output MUST match)

Per arm trace pair (both arms' captures exist under `/tmp/ctxvm-w8/<run-id>/`):

```
python3 -m benchmarks.metrics.metrics <paged.trace.jsonl> \
        --baseline <naive.trace.jsonl> --prices benchmarks/metrics/prices.json \
        --seed 20261029 --replicates 2000
```

produces net-figure + NTR + recall + CI output; the grid-level paired task-difference
readout computes over the six templates' checker verdicts by the analysis script
(the script ships with the capture commit). The spend ledger reads the
`providerUsage` sums + the owner's account view. The final report follows
`reports/RR-W8-*` with the M0 table (each gate row: verdict + interval + input
trace hashes), the deviations section, and D5/D7 reopening state.

## 12. Threats to validity (preregistered; directional language law)

- Single harness (hermes), single author, one machine, one model family, six
  templates: any PASS is scoped exactly like that — the master prompt's language law
  (precisely measured, directional, single-corpus) applies to every claim.
- The W1 counter-expectation must stay live: real captures measured waste ZERO at
  every real budget so far, and the paged arm's render facts are the model-request
  MIRROR the W4 audit documented (the `turn.render` gap) — the provenance records
  `engine-plugin-active` per capture exactly because the mirrored render, not the
  request, is what the metrics read.
- The seed law: clock drift, wall-clock regen touch-ups must never enter gate
  inputs; all gate inputs are replay-derived from committed trace bytes.
- "Equal accuracy" at a scale of k = 6 templates plus non-inferiority δ = 10 pp is
  COARSE; the gate detects material degradation only. The report states this
  limitation explicitly alongside any pass.

## 13. Owner gates (this design asks; the design decides nothing here)

1. **Ratification of the design freeze** (this file, at commit) — YES/NO with edits.
2. **Model + provider + price row + vBudget** — named values locked in the capture
   commit before run one (D5's locator + date law).
3. **The implementation card go-ahead** — the ctxvm context-engine plugin + the
   hermes `post_api_request` usage wiring (the W2b-designated seam,
   `packages/hermes/OBSERVABILITY.md` F3) + the DQ scan tool. Free tier:
   allowed without changes under the standing clearance; paid tier: starts only
   after the price row lands.
4. **The execution window** — owner-run capture discipline mirrors `tools/
   w5-owner-run/README.md` (fresh sessions, one task at a time, no interleaving of
   other work in the same profile; recordings stay owner-held).
5. **The negative-result branch** — if the NTR gate fails, the plan's own text
   ("pivot to telemetry-only ... publish the negative result") is the route; the
   publish act itself is D6/owner.

# RR-SHADOW-JOIN-20261126 — offline join over fresh control shadow records (IMPLEMENTED; current corpus OK, n=9)

Lane: experiment/research. Authority: accepted shadow fix `RR-SHADOW-FIX-REVIEW-20261125`
(`061ebd6`), live acceptance `RR-SHADOW-LIVE-ACCEPT-20261126` (`7b4b0cd`), and the authorized
path **fresh control shadow mode on `w8-shadow` only**. Stable control parity is explicitly not
claimed. The join is implemented at `research/shadow-analysis/join.py`; current result:
`RR-SHADOW-VARIED-RESULT-20261127`. This card does not authorize a gateway restart, profile
activation, live stub arm, candidate-pin use, model call, spend, export, commit, or push.

## 0. Current state (verified 2026-11-27)

- Installed plugin: **0.13.37**; live acceptance committed as `7b4b0cd` / `5641c82`.
- The sidecar contains **107 schema-valid records across 21 sessions**. Twelve sessions are
  0.13.36 captures with the old process-global `shadowWriteFailures=2`; nine are valid
  0.13.37 sessions with per-session failures 0.
- The varied batch added six sessions across many-small, medium-middle, and mixed-size workloads.
  Only one mixed session persisted drops (six pages); the other five were below-budget or
  floor-bust no-ops. Across all nine valid sessions the join sees 42 selections, 5 dropped
  records, 9 dropped pages, 0 unmatched PageIds, 0 later tool_recall, 0 later identifier_scan,
  and 9 right-censored `never_observed` opportunities.
- The join returns **OK**. It emits descriptive metrics with denominators; `candidate_pins=[]`
  because there are no later tool_recall events.
- See `RR-SHADOW-VARIED-RESULT-20261127` for per-shape outcomes, metrics, and limits.

## 1. Inputs and gates

### Inputs

1. Shadow JSONL: `~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl`
2. Trace directory: `~/.local/state/ctxvm/traces/`
3. Coverage manifests: `~/.local/state/ctxvm/traces/*.coverage.json`
4. Validator: `tools/shadow-selection-validate.py`
5. Schema: `packages/hermes/live/shadow_schema.py`

### Mandatory gates before scoring

1. **Version/profile gate:** every included coverage manifest has `plugin.version >= 0.13.37`,
   `plugin.profile == "w8-shadow"`, `plugin.shadowSelection == true`, and
   `plugin.shadowWriteFailures == 0`.
2. **Authorized-path gate:** every included shadow record has `policy.mode == "fresh"` and
   `policy_applied == false`. Stable records, if any, are reported separately and never used
   for a parity claim.
3. **Schema gate:** `python3 tools/shadow-selection-validate.py <selection.jsonl>` exits 0.
4. **Session gate:** map each shadow `session_id` to exactly one coverage manifest using
   `session.sessionID`; never infer from filename. Require exactly one match.
5. **Trace gate:** load `traceFile` from that manifest and verify
   `sha256(trace bytes) == traceDigest`.
6. **PageId gate:** for every trace page identity compute
   `sha256:<hex>(logicalRef + "|" + contentHash)` exactly as the writer does
   (`packages/hermes/live/__init__.py:1249-1250`). Require every shadow `page_id` to match a
   declared/rendered/faulted/evicted PageId in that session. Unmatched ids are reported and
   excluded from rates, with denominator loss visible.
7. **Ordering gate:** shadow records sort by `(session_id, call_index)`. A trace event is
   later than a shadow record if `event.turn > record.turn`, or if turns are equal and both
   have parseable `ts` with `event.ts > record.ts`. Same-turn events without usable `ts` are
   **ambiguous**, not counted as later. The 0.13.37 tracer emits millisecond UTC `ts` by
   default (`packages/hermes/src/plugin.py:257-270`); missing timestamps degrade the session
   to strictly-later-turn labels only.
8. **No-perturbation gate:** `request_unchanged == true` is required by schema; any violation
   invalidates the session.

## 2. Join keys and labels

For each shadow record and each `dropped_pages[].page_id`:

- `later_tool_recall`: later `page.fault` with `source == "tool_recall"` for the same PageId.
- `later_identifier_scan`: later `page.fault` with `source == "identifier_scan"` for the same
  PageId.
- `later_stub_render`: later `page.render` with `mode == "stub"` for the same PageId. This is
  not expected in fresh control shadow mode; if present, the session is outside the authorized
  path and is flagged.
- `later_evict`: later `page.evict` for the same PageId. Same scope warning as above.
- `never_observed`: no later matching event before session end. **Right-censored**, not safe.
- `selection_churn`: Jaccard similarity of dropped-page id sets between consecutive shadow
  records in the same session.
- `recovery_observed`: **not measurable in shadow mode**. It requires a real intervention/stub
  arm; report as UNVERIFIED, never infer from `policy_applied=false`.

Two labels from the original shadow spec are **not derivable** from the current record alone:

- `position_band` (head/middle/tail): the sidecar does not record the full ordered request or
  each dropped page's position. Declaration order is not request order. Mark UNVERIFIED unless
  a separate frozen request-order map is supplied.
- `later_dependency_use`: the trace has no dependency graph or producing-call edge. Mark
  UNVERIFIED unless a separate frozen dependency map keyed by PageId is supplied.

## 3. Metrics (descriptive; denominators always printed)

Per session and pooled only as descriptive counts:

- `selections`: number of valid shadow records.
- `would_drop_rate`: selections with nonempty `dropped_pages` / selections.
- `page_opportunities`: total dropped-page entries across selections.
- `later_tool_recall_rate`: page opportunities with ≥1 later tool_recall / page opportunities.
- `later_identifier_scan_rate`: page opportunities with ≥1 later identifier_scan / page
  opportunities.
- `never_observed_rate`: page opportunities with no later matching event / page opportunities.
- `pressure`: `resident_tokens / budget_tokens`.
- `floor_pressure`: `floor_tokens / budget_tokens`.
- `drop_share`: `dropped_tokens / resident_tokens`.
- `selection_churn`: Jaccard distribution between consecutive selections.
- `shadow_write_failures`: from coverage manifest; must be zero for included sessions.

Report by `policy.mode`, `trigger`, page `kind`, and source. Do not pool identifier_scan with
tool_recall into one "reuse" score: E1 showed they have different label quality. Until at least
three valid sessions pass the gate, emit counts only: suppress pooled metrics and per-session
pressure/floor/drop-share/churn summaries.

## 4. Candidate pins (offline only; proposed frozen rule)

A page may be nominated as an **offline candidate pin** only if:

- it has `later_tool_recall` in at least **2 distinct sessions**, and
- it has at least **3 later tool_recall events** across those sessions.

Identifier_scan alone does not nominate a pin. `never_observed` never proves a page safe to
drop. Candidate pins remain offline-only; every emitted entry carries `offline_only=true` and
`activation=not_authorized`. Applying one to a live arm requires a separate owner ruling and
prereg.

## 5. Outputs and privacy

Outputs are aggregate JSON/Markdown only:

- session counts and denominators;
- hashed PageId counts;
- rates and churn distributions;
- candidate-pin id list (hashed only);
- exclusion log with reason codes, no raw refs or bodies.

No raw logicalRef, tool arguments, page body, stub text, prompt, answer, credential, or absolute
host path enters the report. Raw traces remain private and are never committed. The join script
may hold raw refs in memory only to recompute PageId hashes.

## 6. Stop rules and limitations

- Zero valid shadow records → **BLOCKED — no data**, no result.
- Any version/profile/policy/schema/session/trace/PageId gate failure → exclude the affected
  session and report the loss; if fewer than 3 valid sessions remain, stop as INSUFFICIENT DATA.
- Tracer fault dedupe (`packages/hermes/src/plugin.py:274-277`) means repeated same-source
  faults for one page can be suppressed; observed counts are lower bounds.
- Later reuse is a **proxy**, not causal importance. FOCUS defines utility through
  counterfactual future-trajectory divergence (arXiv:2609.37590 §3–4); CoMem shows relevance is
  query-dependent (arXiv:2611.16384 §2.1–2.2).
- No causal, cost-saving, paging-quality, model-quality, determinism, availability, or
  redaction claim follows.

## 7. Repro commands

```bash
cd "$CTXVM_REPO"
python3 tools/shadow-selection-validate.py \
  ~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl

python3 research/shadow-analysis/test_join.py -v
python3 research/shadow-analysis/join.py \
  --shadow ~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl \
  --trace-dir ~/.local/state/ctxvm/traces \
  --out research/shadow-analysis/out
```

The join exits 0 only with at least three valid sessions; otherwise it writes
`out/result.json` with `status=INSUFFICIENT_DATA` and exits 3.

## 8. Routing / owner decisions

Research/experiment lane implemented the offline join. Review lane verified session mapping, hash
equality, ordering, denominators, privacy, and the three corrections in
`RR-SHADOW-JOIN-FIX-REVIEW-20261127`. The current corpus has nine valid 0.13.37 sessions and
returns OK with descriptive metrics; candidate pins remain empty and offline-only. The varied batch
showed that only one mixed-size session produced an evictable middle; more informative workloads
are needed before treating rates as stable. No live stub-arm or candidate-pin activation is authorized.

# RR-SHADOW-JOIN-20261126 — offline join over fresh control shadow records (DRAFT, blocked on data)

Lane: experiment/research. Authority: accepted shadow fix `RR-SHADOW-FIX-REVIEW-20261125`
(`061ebd6`) and the authorized path **fresh control shadow mode on `w8-shadow` only**.
Stable control parity is explicitly not claimed. This card specifies the offline join; it
does not authorize a gateway restart, profile activation, live stub arm, candidate-pin use,
model call, spend, export, commit, or push.

## 0. Current state (verified 2026-11-26)

- Installed plugin: **0.13.36** (`~/.hermes/plugins/ctxvm-tracer/__init__.py`).
- Gateway pid **90481** is live on 0.13.36 (`sync-plugin.sh --check` confirms it holds the build).
- `w8-shadow` config resolves correctly offline and live: `engine=compressor`, `budget=24000`,
  `shadowSelection=true/settings`.
- The 0.13.36 `pre_api_request` collection path produced **65 schema-valid records across 12
  successful free-model sessions**. All 12 captures pass the coverage checker and Rust replay with
  `divergences=[]`, `violations=[]`.
- However, **zero dropped/repositioned pages are present in the persisted records**. Two live shadow
  writes failed with `ValueError: page entry does not resolve to exactly one logical ref`
  (`~/.local/state/ctxvm/traces/_swallowed.log`, 19:56:43 and 19:57:58), so the actual drop attempts were
  lost. The exact `contentHash` is present in the payload but the writer rejects ambiguous identity-token
  joins instead of disambiguating by `ref|contentHash`.
- Every sidecar reports `shadowWriteFailures=2` because the counter is process-global, so the mandatory
  zero-failure gate excludes all 12 sessions even though their traces are valid.
- Therefore there is **no joinable would-drop data yet**. Hermes must fix exact-hash disambiguation and
  per-session failure accounting, then fresh sessions must produce persisted `dropped_pages`. See
  `RR-SHADOW-LIVE-DATA-REVIEW-20261126.md`.

## 1. Inputs and gates

### Inputs

1. Shadow JSONL: `~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl`
2. Trace directory: `~/.local/state/ctxvm/traces/`
3. Coverage manifests: `~/.local/state/ctxvm/traces/*.coverage.json`
4. Validator: `tools/shadow-selection-validate.py`
5. Schema: `packages/hermes/live/shadow_schema.py`

### Mandatory gates before scoring

1. **Version/profile gate:** every included coverage manifest has `plugin.version >= 0.13.35`,
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
   **ambiguous**, not counted as later. The 0.13.35 tracer emits millisecond UTC `ts` by
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
tool_recall into one "reuse" score: E1 showed they have different label quality.

## 4. Candidate pins (offline only; proposed frozen rule)

A page may be nominated as an **offline candidate pin** only if:

- it has `later_tool_recall` in at least **2 distinct sessions**, and
- it has at least **3 later tool_recall events** across those sessions.

Identifier_scan alone does not nominate a pin. `never_observed` never proves a page safe to
drop. Candidate pins remain offline-only; applying one to a live arm requires a separate owner
ruling and prereg.

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

## 7. Repro commands (after data exists)

```bash
cd /home/theb/Documents/ctxvm
python3 tools/shadow-selection-validate.py \
  ~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl

# Research-lane join script to be implemented against this card:
python3 research/shadow-analysis/join.py \
  --shadow ~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl \
  --trace-dir ~/.local/state/ctxvm/traces \
  --out research/shadow-analysis/out
```

The script does not exist yet. This card is the specification and acceptance test for it.

## 8. Routing / owner decisions

Research/experiment lane implements the offline join and reports counts. Review lane verifies
session mapping, hash equality, ordering, denominators, and privacy. The gateway is already
running 0.13.36 and live collection works, but the corpus is blocked by exact-hash disambiguation
and per-session failure accounting (`RR-SHADOW-LIVE-DATA-REVIEW-20261126.md`). After that fix and
fresh valid records with persisted `dropped_pages`, route this card to research/experiment. No live
stub-arm or candidate-pin activation is authorized.

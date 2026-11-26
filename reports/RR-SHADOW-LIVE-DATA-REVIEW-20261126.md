# RR-SHADOW-LIVE-DATA-REVIEW-20261126 — collection works, but drop records are lost and failures are global

Review lane, verify-then-record. Date 2026-11-26. Owner-authorized free-model collection on `w8-shadow`.
No profile/gateway/model-config edit, publish, or push.

## 1. What now works

- Gateway pid **90481** is live on **0.13.36**.
- `pre_api_request` control-shadow planning runs; sidecars attest `shadowSelection=true/settings`,
  `shadowSelections>0`, and `engineSelections=0`.
- **65 schema-valid records across 12 successful sessions** were produced.
- All 12 traces pass the coverage checker and Rust replay with `divergences=[]`, `violations=[]`.
- Exact session mapping and trace digests verify for all 12 captures.

This closes the original “control profiles never call the planner” blocker.

## 2. Blocking finding 1 — actual drop records are lost on ambiguous identity joins

Persisted records contain **0 dropped pages and 0 repositioned pages**. The live swallowed-error log
shows two failed writes:

```text
2026-11-26T19:56:43 shadow_record: ValueError: page entry does not resolve to exactly one logical ref
2026-11-26T19:57:58 shadow_record: ValueError: page entry does not resolve to exactly one logical ref
```

`_hashed_pages()` resolves identity tokens to refs and requires exactly one ref. When multiple refs share
identity tokens, it raises and discards the whole record — even though the plan payload now carries the
exact `contentHash` needed to disambiguate. The Python tracer already retains exact declared identities in
`_all_declared` as `ref|contentHash`.

Required fix: filter candidate refs by `f"{ref}|{content_hash}" in tracer._all_declared`; fail closed only
if no exact match or more than one exact match remains. Add a regression with two refs sharing identity
tokens and an exact historical hash.

## 3. Blocking finding 2 — failure counter is process-global

Every one of the 12 sidecars reports `shadowWriteFailures=2`, because `_state()["shadowWriteFailures"]`
is process-wide. Two failed writes therefore contaminate every session and the join's mandatory
zero-failure gate excludes all 12, including sessions whose own writes succeeded.

Required fix: maintain `shadowWriteFailuresBySession`, increment/read per session, and keep any process
counter separately labeled. Add a two-session regression where one fails and the other remains eligible.

## 4. Workload note

Several collection batches were run to exercise pressure. Large protected tails produced `floor_bust`
no-ops; smaller middle files stayed below budget after host truncation. The two ambiguous-join failures
are the only observed attempts that reached page resolution, and those records were discarded. A fresh
post-fix batch must demonstrate at least one persisted `dropped_pages` entry with
`floor_tokens < budget_tokens < resident_tokens` before the join is unblocked.

## 5. Route to Hermes

1. Exact-hash disambiguation in `_hashed_pages()` using tracer history.
2. Per-session shadow failure accounting and sidecar attestation.
3. Regression tests for ambiguous refs + exact hash and failure isolation.
4. A live acceptance run with persisted would-drop pages, valid schema/checker/replay, and zero
   per-session failures.

## 6. Join status / claim ceiling

`RR-SHADOW-JOIN-20261126.md` remains a blocked draft, updated to 0.13.36 and the 65-record/12-session
state. No rates or candidate pins are computed. No causal, cost-saving, paging-quality, model-quality,
determinism, availability, or redaction claim. Raw traces remain private; no live stub arm or pin use.

## 7. Applied

This card, an append-only LOG row (four pipes), a day-file section, the join-draft update, and a
PROJECT-STATE blocker update.

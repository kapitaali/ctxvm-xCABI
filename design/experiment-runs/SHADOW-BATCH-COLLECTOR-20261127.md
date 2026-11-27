# SHADOW-BATCH-COLLECTOR-20261127 — tracked collector + 12-session varied corpus

Status: **IMPLEMENTATION AUTHORIZED; live collection conditionally authorized after review acceptance.**
Date: 2026-11-27
Owner ruling: approved with amendment (recorded in `reports/RR-SHADOW-COLLECTOR-AUTH-20261127.md`)
Preregistration / design of record: `reports/RR-SHADOW-JOIN-20261126.md`
Current result: `reports/RR-SHADOW-VARIED-RESULT-20261127.md`

## 1. Baseline

At `7487bcc` the offline join is OK with **9 valid sessions**, 107 shadow records, 42 selections, 9 dropped
pages, zero later observed reuse, and no candidate pins. The six-session varied batch showed that only one
mixed-size session produced an evictable middle; many-small stayed below budget and medium/mixed-1 were
floor-bust no-ops. The pipeline works, but the corpus is still small and workload-skewed.

## 2. Objective

Build one tracked command that collects a preregistered varied shadow corpus without hand-built workspaces
or manual validation:

```bash
python3 tools/collect-shadow.py \
  --repo "$CTXVM_REPO" \
  --shadow ~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl \
  --trace-dir ~/.local/state/ctxvm/traces \
  --out ~/.local/state/ctxvm/w8-runs/shadow-batch-<id> \
  --target-informative 12 \
  --max-attempts 18
```

The collector stops at 12 new shape-informative sessions or the frozen attempt cap, writes a machine-readable
receipt, runs the offline join, and never mutates profile/gateway/model configuration.

## 3. Frozen workload shapes

Four new shape-informative sessions per shape; maximum six attempts per shape before the shape is declared
underpowered. Every informative session must be valid (rc=0, all gates green, zero failures) and contain ≥1
persisted dropped page with `floor_tokens < budget_tokens < resident_tokens`, plus the shape-specific label:

| shape | additional informativeness requirement | fixture | prompt behavior | label target |
|---|---|---|---|---|
| read-once pressure | none beyond the valid persisted drop | two ~57.6 KB files + three tiny tail files | sequential reads, no re-read | baseline would-drop/pressure/churn |
| deliberate later re-read | ≥1 later `tool_recall` for a dropped PageId | same pressure fixture | read all, then explicitly re-read the first large file | later `tool_recall` |
| dependency chain | ≥1 later `identifier_scan` for a dropped PageId | three files with explicit A→B→C references + tiny tail | read in dependency order and follow references | later `identifier_scan`; dependency distance stays UNVERIFIED |

Research/experiment owns fixture generation and prompt freeze. Fixture files are pinned by SHA-256 in a manifest;
the collector validates the manifest and consumes frozen prompts. No post-hoc prompt or fixture broadening is
allowed.

## 4. Collector preflight

Fail closed before any model call unless all are true:

- repo/installed/manifest plugin version is **0.13.37 or newer**;
- `sync-plugin.sh --check` reports the live gateway holds the build;
- `w8-shadow` resolves to `engine=compressor`, `budgetTokens=24000`, `shadowSelection=true/settings`,
  fresh mode, `stubDropped=off`;
- model/provider are explicitly fixed to `tencent/hy4-flash:free` / `nous`; no paid fallback or silent switch;
- trace and output directories are private and writable;
- workload manifest hashes match.

Use anonymous `hermes chat --oneshot --max-turns 20`; never named `--create-if-missing`.

## 5. Per-session evidence

For every attempt, snapshot immediately into the private run directory:

- stdout/stderr and exit code;
- session id, model/provider, start/end time;
- trace + coverage sidecar;
- shadow record delta for that session;
- trace digest and input-shadow digest;
- gate receipts: shadow schema, coverage checker, v0.1 schema, Rust replay, drop shape, zero failures.

Raw traces/records never enter git. The committed output is aggregate JSON/Markdown only.

## 6. Join and stop rules

- Run `research/shadow-analysis/join.py` after each accepted attempt.
- Stop at 12 new shape-informative sessions across the three shapes, or after 18 total attempts.
- **Any auth/model failure stops the entire collection immediately and is recorded.** No paid fallback,
  retry with another model/provider, or silent switch is allowed.
- Non-zero shadow write failure, digest mismatch, schema failure, or replay divergence excludes the attempt
  and is reported.
- If a shape reaches six attempts without four informative sessions, report it underpowered and do not
  broaden the prompt or fixture.
- Candidate pins remain offline-only; the collector never applies them.

## 7. Implementation routing

Hermes/tools lane owns `tools/collect-shadow.py` and its no-model unit tests. Research/experiment owns fixture/
prompt freeze and aggregate interpretation. Review verifies preflight, privacy, receipts, quotas, stop rules,
and both denominator views. Implementation authorization does not authorize live calls; collection starts only
after review acceptance and a fresh successful preflight.

Required tests (no model calls):

1. preflight rejects stale plugin, wrong profile, shadow off, wrong budget, stale gateway, fixture hash mismatch;
2. fake runner produces a valid private snapshot and receipt;
3. schema/checker/replay/drop-shape failures exclude the attempt; auth/model failure stops the whole run;
4. attempt cap, per-shape quotas, and shape-specific informativeness stop correctly;
5. output contains no raw refs, bodies, credentials, or host paths;
6. join is invoked with the exact shadow/trace paths and expected exit contract;
7. aggregate output reports all-valid and informative-only denominators separately.

## 8. Metrics and claim ceiling

Report per-shape and pooled counts using **both all-valid and informative-only denominators**. Do not silently
condition pooled rates on informative sessions; label each view and show the excluded/no-label counts. No causal,
cost-saving, paging-quality, model-quality, determinism, availability, or redaction claim. `position_band` and
`later_dependency_use` remain UNVERIFIED. More sessions improve description, not causal identification.

## 9. Owner rulings (2026-11-27)

1. **Implementation APPROVED.** Route `tools/collect-shadow.py` and no-model unit tests to hermes/tools.
   Research/experiment owns fixture/prompt freeze and aggregate interpretation; review verifies preflight,
   privacy, receipts, quotas, and stop rules. Implementation only: no live calls or config/gateway changes.
2. **Live collection APPROVED CONDITIONALLY.** Only after collector review acceptance and a fresh preflight
   proving the live gateway holds 0.13.37 or newer: at most 18 anonymous one-shot attempts on
   `tencent/hy4-flash:free` / `nous`, each `--max-turns 20`, maximum six attempts per shape. Stop at 12 new
   shape-informative sessions or 18 total attempts. Any auth/model failure stops collection and is recorded.
3. **Shapes/target APPROVED WITH AMENDMENT.** Four informative sessions per shape, 12 new total, with the
   shape-specific definitions in §3. Report all-valid and informative-only denominators. Underpowered shapes
   stop at six attempts without prompt/fixture broadening. Candidate pins remain offline-only.

No gateway/profile/config edit, restart, candidate-pin activation, publish, or push is included.

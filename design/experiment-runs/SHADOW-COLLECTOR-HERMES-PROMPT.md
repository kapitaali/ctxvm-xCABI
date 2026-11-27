MASTER PROMPT — hermes/tools lane: implement `tools/collect-shadow.py` + no-model tests

Owner authorized implementation 2026-11-27. Authority:
`design/experiment-runs/SHADOW-BATCH-COLLECTOR-20261127.md` §7–§9 and
`reports/RR-SHADOW-COLLECTOR-AUTH-20261127.md`.

## 0. Scope boundary

You own `tools/collect-shadow.py` and its no-model unit tests. Research/experiment owns fixture files, frozen
prompts, and aggregate interpretation. Review verifies preflight, privacy, receipts, quotas, stop rules, and
both denominator views.

**Implementation only. Do not run live sessions, edit profiles/gateway/model config, restart anything, activate
a stub arm or candidate pin, publish, or push.** Live collection is conditionally authorized only after review
acceptance and a fresh successful preflight.

## 1. Read first

- `design/experiment-runs/SHADOW-BATCH-COLLECTOR-20261127.md` in full.
- `reports/RR-SHADOW-JOIN-20261126.md` and `RR-SHADOW-VARIED-RESULT-20261127.md`.
- `tools/sync-plugin.sh`, `tools/shadow-selection-validate.py`, `research/shadow-analysis/join.py`.
- `handoff/LANES.md`, `AGENTS.md`, active ledger `reports/LOG02.md`.

Check `git log --oneline -8 && git status --short`; other lanes have WIP. Never `git add -A`.

## 2. Command contract

Implement a single CLI, roughly:

```bash
python3 tools/collect-shadow.py \
  --repo "$CTXVM_REPO" \
  --shadow ~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl \
  --trace-dir ~/.local/state/ctxvm/traces \
  --fixture-manifest <research-owned-manifest.json> \
  --out ~/.local/state/ctxvm/w8-runs/shadow-batch-<id> \
  --target-informative 12 \
  --max-attempts 18 \
  --max-attempts-per-shape 6 \
  --model tencent/hy4-flash:free \
  --provider nous
```

The command must be sequential, bounded, and fail closed. It must never mutate the profile, gateway, model
configuration, or live request.

## 3. Preflight (before any model call)

Require all of:

- repo/installed/manifest plugin version ≥ 0.13.37;
- `tools/sync-plugin.sh --check` proves the live gateway holds the build;
- `w8-shadow` resolves to `engine=compressor`, `budgetTokens=24000`, `shadowSelection=true/settings`, fresh,
  `stubDropped=off`;
- model/provider exactly `tencent/hy4-flash:free` / `nous`; no paid fallback or silent switch;
- private output/trace directories, writable, modes 0700/0600;
- fixture manifest exists and every SHA-256 matches.

Use the by-path profile policy resolver where possible; do not rely on stale bare imports.

## 4. Frozen shapes and informativeness

Research/experiment supplies fixture paths + frozen prompts. Collector consumes them without editing.

- **read-once pressure:** valid persisted drop (`floor < budget < resident`).
- **deliberate later re-read:** same + ≥1 later `tool_recall` for a dropped PageId.
- **dependency chain:** same + ≥1 later `identifier_scan` for a dropped PageId. Dependency distance remains
  UNVERIFIED.

Target four informative sessions per shape, 12 new total. Maximum six attempts per shape and 18 total.

## 5. Session execution and evidence

Use anonymous:

```bash
hermes chat --oneshot --max-turns 20 --provider nous \
  --model tencent/hy4-flash:free --in <fixture-workspace> -q <frozen-prompt>
```

Never named `--create-if-missing`. For every attempt, snapshot immediately into the private run directory:

- stdout/stderr, rc, timestamps, parsed session id, model/provider;
- trace + coverage sidecar;
- shadow-record delta for that session;
- trace digest and input-shadow digest;
- gate receipts: shadow schema, coverage checker, v0.1 schema, Rust replay, drop shape, zero failures;
- shape-specific label receipt.

**Any auth/model failure stops the entire collection immediately and is recorded.** Other gate failures exclude
the attempt and are reported. No retry with another model/provider.

## 6. Join and quotas

- Run `research/shadow-analysis/join.py` after each accepted attempt.
- Stop at 12 informative sessions or 18 attempts.
- If a shape reaches six attempts without four informative sessions, mark it underpowered; do not broaden
  prompts or fixtures.
- Emit **all-valid and informative-only denominators separately**. Never silently condition pooled rates on
  informative sessions.
- Candidate pins remain offline-only; never apply them.

## 7. Privacy and outputs

Private snapshots may contain raw traces. Committed/generated aggregate output may contain only:

- hashed session/PageId values;
- counts, denominators, reason codes, digests;
- descriptive metrics with view labels;
- candidate-pin status (offline-only/not-authorized).

No raw refs, bodies, arguments, prompts, answers, credentials, or absolute host paths in aggregate output.

## 8. Required no-model tests

1. preflight rejects stale plugin/gateway, wrong profile, shadow off, wrong budget, fixture hash mismatch;
2. fake runner creates a complete private snapshot and receipt;
3. schema/checker/replay/drop-shape failure excludes attempt; auth/model failure stops whole run;
4. per-shape quotas, total cap, and shape-specific informativeness stop correctly;
5. aggregate output has no raw ref/body/credential/host path;
6. join invocation uses exact paths and exit contract;
7. all-valid and informative-only denominator views are both present and labeled;
8. no test makes a model call or edits real profile/gateway state.

Use fake subprocesses/temp dirs. Run tests with `CTXVM_*` cleared.

## 9. Verification and landing

- Focused collector tests, full Hermes suite, `bash tools/run-ci.sh`, `check-handoff.sh`, `git-hygiene.sh`.
- CJK/secret/home-path sweeps on staged files.
- Own `reports/RR-SHADOW-COLLECTOR-IMPL-<date>.md`, append one four-pipe row to `reports/LOG02.md`, day section.
- Coordinate shared files with review; private index; reset shared index; attribution `kapitaali`; no push.
- Hand off exact diff + verification receipt for review acceptance. No live run until review accepts.

## 10. Claim ceiling

No cost-saving, paging-quality, model-quality, determinism, availability, or redaction claim. No causal claim.
`position_band` and `later_dependency_use` remain UNVERIFIED. The collector is instrumentation, not evidence
that dropping is safe or beneficial.

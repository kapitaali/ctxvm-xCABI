# RR-SHADOW-COLLECTOR-AUTH-20261127 — collector implementation approved; conditional live batch authorized

Owner rulings 2026-11-27, applied to `design/experiment-runs/SHADOW-BATCH-COLLECTOR-20261127.md`.
Review lane, verify-then-record. No implementation, model call, spend, gateway/profile change, or push.

## 1. Implementation approved

Route `tools/collect-shadow.py` and no-model unit tests to the hermes/tools lane. Research/experiment owns
fixture/prompt freeze and aggregate interpretation. Review verifies preflight, privacy, receipts, quotas, stop
rules, and both denominator views.

This authorizes implementation only: no live calls, gateway/profile/config edits, restart, live stub arm,
candidate-pin activation, publish, or push.

## 2. Live collection approved conditionally

Only after collector review acceptance and a fresh preflight proving the live gateway holds plugin 0.13.37 or
newer:

- at most 18 anonymous one-shot attempts;
- `tencent/hy4-flash:free` / `nous`, each `--max-turns 20`;
- maximum six attempts per shape;
- stop at 12 new shape-informative sessions or 18 total attempts;
- no paid fallback or silent model/provider switch;
- any auth/model failure stops collection and is recorded.

## 3. Shapes and target approved with amendment

Four informative sessions per shape, 12 new total:

- read-once pressure: valid persisted drop with `floor < budget < resident`;
- deliberate re-read: same + ≥1 later `tool_recall` for a dropped PageId;
- dependency chain: same + ≥1 later `identifier_scan` for a dropped PageId; dependency distance UNVERIFIED.

Report all-valid and informative-only denominators; do not silently condition pooled rates. A shape reaching six
attempts without four informative sessions is underpowered; no prompt/fixture broadening. Candidate pins remain
offline-only.

## 4. Routing artifacts

- Updated prereg: `design/experiment-runs/SHADOW-BATCH-COLLECTOR-20261127.md`
- Hermes/tools work order: `design/experiment-runs/SHADOW-COLLECTOR-HERMES-PROMPT.md`
- Review acceptance required before any live attempt.

## 5. Applied

This card, one four-pipe LOG02 row, a day-file section, and a PROJECT-STATE next-action update. No push.

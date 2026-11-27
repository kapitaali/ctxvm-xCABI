# RR-SHADOW-COLLECTOR-REREVIEW-20261127 — one blocker remains: unbound route does not stop collection

Review lane, verify-then-record. Subject: `7c54041`. Date 2026-11-27. No live session, model call, spend,
gateway/profile change, or push.

## 1. Fixes accepted

Independent re-review confirms the prior blockers are fixed:

- live target frozen to 12; reduced targets require internal test mode;
- effective fallback chain proven disabled;
- auth/model failure signatures expanded;
- malformed evidence produces receipts instead of raw crashes;
- `HERMES_HOME`/profile binding is explicit;
- duplicate session ids cannot satisfy quotas;
- per-shape and pooled dual-denominator views exist;
- session ids parse from both stdout and stderr.

Verification rerun:

- collector: **36 passed, 51 subtests**;
- join: **6 passed**;
- Hermes shadow: **17 passed**;
- full CI: **ALL GATES GREEN**;
- pristine-tree rehearsal: **4/4 green**;
- kit/hygiene/compile/diff/CJK/secret checks pass.

## 2. Remaining blocker

`tools/collect-shadow.py:557–559` sets `model_provider_failure` only when the coverage `sessionID` matches the
parsed SID. If coverage is missing, malformed, duplicated, or bound to another SID, `_coverage_for()` returns no
session object (`:326–346`), so the route is unknown but the stop flag is never set. The stop check at `:721–726`
therefore does not fire and later attempts continue.

No-model reproduction with a fake runner that deletes the first attempt's coverage sidecar:

```json
{
  "status": "UNDERPOWERED",
  "attempts": 3,
  "first_observed_model": null,
  "first_observed_provider": null,
  "first_model_provider_failure": false,
  "later_attempts_run": 2
}
```

This violates the owner ruling that an unknown or unproven route stops collection immediately and is recorded.

## 3. Required fix

- Missing, malformed, multiple, or SID-unbound coverage must set `model_provider_failure=true` (or an equivalent
  explicit route-failure flag) before another attempt.
- Write the attempt receipt and aggregate with `STOPPED_MODEL_PROVIDER`, exit 4.
- Add no-model regressions for missing, malformed, duplicate, and wrong-SID coverage.
- Keep exact known model/provider drift behavior.
- Rerun focused suite, full CI, rehearsal, kit/hygiene, and hand back for re-review.

Nice-to-haves remain non-blocking: preserve original sidecar bytes, persist preflight facts in normal runs,
normalize remaining preflight I/O errors, and assert non-null four-per-shape rate fields.

## 4. Verdict

**NOT ACCEPTED for live collection.** The conditional live batch remains blocked until this narrow fix lands and
review accepts it. No rates, pins, causal, cost, paging, model, determinism, availability, or redaction claim.

## 5. Applied

This card, one four-pipe LOG02 row, a day-file section, a focused fix prompt, and a PROJECT-STATE precision update.
No collector code changed by review; no push.

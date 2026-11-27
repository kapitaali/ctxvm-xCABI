MASTER PROMPT — hermes/tools lane: final collector route-stop fix

Authority: `reports/RR-SHADOW-COLLECTOR-REREVIEW-20261127.md`. All prior blocker areas are accepted; one remains.
No live sessions or config/gateway changes.

## Required fix

When coverage is missing, malformed, duplicated, or bound to a different SID, the attempt's route is unproven.
Set the model/provider failure flag, write the normal attempt receipt and aggregate with
`status=STOPPED_MODEL_PROVIDER`, stop before another attempt, and exit 4.

Current defect: `tools/collect-shadow.py:557–559` only sets the flag when `sessionID == sid`; `_coverage_for()`
returns no session object for missing/multiple/unbound coverage (`:326–346`), so `:721–726` never stops.

Add no-model regressions for:

1. missing coverage;
2. malformed coverage JSON/object;
3. multiple coverage manifests for the SID;
4. coverage bound to another SID;
5. known model/provider drift still stops;
6. no later attempt runs after any route-stop case.

Rerun collector suite, full CI, rehearsal, kit, hygiene, diff, privacy checks. Append one four-pipe LOG02 row and
day section. Private index; no push. Hand back for final re-review. Live batch remains blocked until acceptance.

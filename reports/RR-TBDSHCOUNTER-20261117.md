# RR-TBDSHCOUNTER-20261117 — verified: the dsh full run's 588-ceiling stop is inert; external counting is required

Review lane, verify-then-record. The run is **active** — this card changes nothing in it, performs no count of its
own, and gives no verdict. Private artefacts stay under the dsh workspace and state dir.

## 1. What is actually running

- Process: `bash …/tb-dsh-full-20261117/driver.sh`, with repeated
  `node ~/Apps/deepseek-harness/apps/cli/lib/bin.js --profile ctxvm-plana --session-id session-9fd394a3-…`.
- Progress at the time of checking (15:47–15:48 local): **P55/P56**, ~19–21 s/prompt, `rc=0`, `new_traces=1`,
  same session id. One private `<sessionId>-<ts>.jsonl` per prompt, consistent with the plan.
- The **smoke** (handoff 16) and the **full-run prereg** (handoff 17) are in the dsh workspace. The prereg
  froze P1-fresh / P2+ resumed mode, `r_smoke=3`, `A=9`, **ceiling 588**, and a "no retry" rule. Those are the
  lane's records; I did not re-verify the owner's authorization text quoted there.

## 2. Defect — the ceiling stop cannot fire

`tb-dsh-full-20261117/driver.sh:46-56`:

```sh
SID=$(sed -n 's/.*session\/created \(session-[^ ]*\).*/\1/p' "$W/p1.log" | head -1)  # SID = "session-9fd…"
SESSION_DIR=$(ls -td ~/.dsh/sessions/*/session-"$SID" 2>/dev/null | head -1)          # looks for "session-session-9fd…"
CALLS=0
if [ -n "${SESSION_DIR:-}" ] && [ -f "$SESSION_DIR/session.v4.jsonl.zstd" ]; then … fi
```

The `--session-id` value already includes the `session-` prefix, so the glob constructs `session-session-…`,
matches nothing, and `CALLS` stays **0**. Every progress row confirms it (`"calls":0` at P52–P55). Therefore
`if [ "$CALLS" -gt "$CEILING" ]` at line 64 can never be true: **the 588 hard stop is inert.** The real session
directory exists (`~/.dsh/sessions/--home-theb-Apps-deepseek-harness--/session-9fd394a3-…/session.v4.jsonl.zstd`)
and has content, so the counter is a driver bug, not a missing log.

## 3. Consequence and mitigation already in hand

The owner stated the intended mitigation: re-check the **external** call count at intervals, since the driver's
counter is unusable. That is the correct control for the current run; stopping it to patch the driver would be a
worse intervention. Record the external counts with timestamps in the final run card, and state plainly that the
CEILING outcome depends on external monitoring, not the driver's stop.

For future runs, the one-line fix is to drop the extra `session-` prefix in the `SESSION_DIR` glob (or strip it
from `$SID`). That is a change to a workspace driver, owned by the dsh lane; I have not edited it.

## 4. Claim ceiling

This is a control defect, not a run verdict. No result, cost, paging, H3/H4, eviction, determinism, or model-quality
claim is made here. The run's outcome is still open; I will review it when it ends and its artefacts are available.

Kit/hygiene were green at the last check; this card changes no gate input.

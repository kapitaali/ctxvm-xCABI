# RR-AGENTPROMPT-20261119 — refreshed the stale plugin paragraph in the agent prompt

Review lane, verify-then-record. This closes the flag I raised in `RR-HBOOKS-REVIEW` §2. `handoff/**` is
review-lane property (`handoff/LANES.md:17`), so this paragraph was mine to refresh; no owner clearance was needed.
Date 2026-11-19. No code change, model call, spend or push.

## 1. What was stale, and the live replacement

`handoff/AGENT-PROMPT.md` §1 said plugin **0.13.24**, gateway **PID 23669** ("started after the 09:31 sync"), and
that the **paged capture was still owed**. All three are now false:

| field | old text | verified now | locator / command |
|---|---|---|---|
| plugin on disk | 0.13.24 | **0.13.27** | `grep PLUGIN_VERSION ~/.hermes/plugins/ctxvm-tracer/__init__.py` → `0.13.27` |
| running gateway | PID 23669, 09:31 sync | **PID 4486, started 11:13:34 local, after the files** | `ps -p 4486 -o pid,lstart,cmd` → running; `RR-H12RESULT-20261119` §5 |
| paged capture | still owed | **landed** | `h12p2-paged`, CELL, 39 calls, `RR-H12RESULT-20261119` / verified `9a817f9` |

The paragraph now says 0.13.27 / PID 4486 / captures labelled 0.13.27 / paged capture landed, and keeps the
standing rule that only the hermes lane syncs the copy.

## 2. What was deliberately not touched

- **Root `AGENTS.md` §9** still carries a different stale line (plugin 0.10.x, gateway restart needed). It is not
  in `handoff/**` and is owner-governing text — flagged, not edited. The 0.13.24/PID 23669 wording was never in
  root `AGENTS.md`; attributing it there (as the HBOOKS summary did) was wrong, and I did not propagate that error.
- Other §1 lines (W8 block, REDLINE negative, white-paper PDF staleness) were outside the flag I raised; left as-is.
- No gate input, no kit file under byte cap, no package or tool byte.

## 3. Applied

This card, an append-only LOG row (four pipes), and a day-file section. Checker ALL PASS and hygiene OK after the
edit; the full gate is unaffected by a handoff-prose change (last re-run green at `056fd94`).

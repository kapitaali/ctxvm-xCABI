# RR-DEFAULTS-20261119 — owner approves the three default decisions and routings

Owner decision 2026-11-19, verbatim in response to the proposed defaults for the three remaining queues
(owner decisions, plan-owner G4/H13 close-out, and hermes-lane H16–H18 test-gap routing):

> approve defaults

Review lane, verify-then-record. Date 2026-11-19. No production code, tool, spec, or corpus byte was changed; no
model call, spend, gateway restart, or push.

## 1. Rulings recorded

1. **`stubText` / `reason` placement (`reports/RR-REDACT-20261118.md` §6) — RATIFIED DEFERRED.**
   Deferred to a separate card triggered only when a non-frozen drop is prepared for release. G4's shipped
   consumer already prints `channels modelled: logicalRef` on every declared block (`tools/redaction-block.py`,
   verified in `RR-REDACTIMPL-REVIEW`), preventing `replacedFieldCount` from being misread as covering
   `stubText`/`reason`.
2. **H15 installed directory / `ctxvm.py` (`design/ROADMAP-HERMES-LANE.md:140–145`) — CLOSED DONE.**
   The unimported `ctxvm.py` re-export obligation is dropped; the installed directory at
   `~/.hermes/plugins/ctxvm-tracer/` is defined by H14's import-derived sync set. Verified on disk 2026-11-19:
   `ls ~/.hermes/plugins/ctxvm-tracer/` shows exactly
   `__init__.py context_engine.py plugin.py plugin.yaml profile_policy.py uc1_handoff.py uc2_forensics.py uc3_planner.py uc_registry.py __pycache__`
   (the old `live/`, `src/`, `test_plugin.py`, `BUG_REPORT.md` leftovers are gone), and today's 0.13.27 paged
   capture (`h12p2-paged`, `RR-H12RESULT-20261119`) proved a live probe captures. H15 is rewritten and ticked `[x]`.
3. **Root `AGENTS.md` §9 (`:177–178`) — REFRESHED.**
   Updated the stale `plugin 0.10.x` line to `plugin 0.13.x (0.13.27 live; see handoff/PROJECT-STATE.md for current
   version and gateway PID)` so the root instruction file agrees with `PROJECT-STATE.md` and `AGENT-PROMPT.md`.
4. **D17 & post-H12 W8 paging direction — HELD / PARKED.**
   D17 remains held (`RR-D17RULING-20261118`). New W8 paging engine code is parked while E1's zero-spend offline
   replay (`RR-E1APPROVE-20261119`) runs; tail-only eviction (`RR-P8H12-20261119` §2 candidate (c)) stays recorded
   as the candidate if the owner later reopens W8 policy work.

## 2. Plan-owner books closes applied

- **`design/ROADMAP-OPENCODE-LANE.md:881` & `:1054`** — G4 ticked `[x]` citing `9e755d4` (`RR-REDACTIMPL-20261119`)
  and review verification `056fd94` (`RR-REDACTIMPL-REVIEW`), plus the `stubText`/`reason` deferral ruling;
  summary line `:1054` updated to list G4 alongside G5 as DONE.
- **`reports/RR-REDACT-20261118.md:3–5`** — status banner updated from `DRAFT — not done, no code written` to
  `specification of record for the narrow GO — implemented in reports/RR-REDACTIMPL-20261119.md (9e755d4, verified
  056fd94, RR-REDACTIMPL-REVIEW)`, preserving the specification text intact.
- **`design/ROADMAP-HERMES-LANE.md:119` & `:140`** — H13 ticked `[x]` citing `21a12a5` (`RR-P8H12-20261119`); H15
  rewritten to the import-derived set and ticked `[x]`.

## 3. H16–H18 routed to the hermes lane

Wrote `design/H16-H18-LANE-DEVELOPER-PROMPT.md`, routing the three free test-gap cards as one zero-spend,
test-only bundle in order **H18 → H17 → H16**, with H16 placed inside `packages/hermes/test/` so `tools/run-ci.sh`
gate 2 and `.github/workflows/ci.yml` execute it automatically without workflow drift. No implementation agent was
spawned by the review lane.

## 4. Verification

- `ls ~/.hermes/plugins/ctxvm-tracer/` → the 9 import-derived files + `__pycache__` above.
- `bash tools/check-handoff.sh` → `ALL HANDOFF CHECKS PASS`.
- `bash tools/git-hygiene.sh` → `OK: the shared index agrees with HEAD`.

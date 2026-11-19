# RR-HVERR-REVIEW — verified: `0.13.29` is live on gateway PID `139920`, real session flushed `harnessVersion: "0.23.2"`, and the `atexit` test leak is closed

Review lane, verify-then-record. Subject: `585e153` (`reports/RR-HVERR-20261119.md`,
`reports/RR-HVREV-20261119.md`, `packages/hermes/test/test_capture_smoke.py`). Date 2026-11-19. No production
code, tool, spec, or corpus byte written by this lane; no model call, spend, gateway restart, or push.

## 1. Verdict

**`RR-HVERR-20261119` is verified — plus an even stronger live witness now sits on disk.** When the hermes lane
finished its turn at `2026-11-19 23:11:54` under the restarted `0.13.29` gateway (`pid 139920`, started `22:51:09`),
the real live session `local-f913ef1486eca33af05f34` flushed again, writing **`pluginVersion: "0.13.29"`** and
**`harnessVersion: "0.23.2"`** into both its `.meta.json` and `.coverage.json` sidecars on disk.

## 2. Evidence re-derived

| claim | command | result |
|---|---|---|
| commit scope (`585e153`) | `git show --stat --oneline 585e153` | 3 files (`packages/hermes/test/test_capture_smoke.py` +14, `reports/RR-HVERR-20261119.md` +51, `reports/RR-HVREV-20261119.md` +8); 0 production files changed |
| gateway PID & sync | `ps -p 139920 -o pid,lstart,cmd`; `bash tools/sync-plugin.sh --check` | `pid 139920` started `Thu Nov 19 22:51:09 2026`; `PLUGIN_VERSION: repo 0.13.29 \| installed 0.13.29 \| manifest 0.13.29`; `gateway: pid 139920 started after these files were written; it holds this build` |
| real live-session sidecars on disk | inspect `~/.local/state/ctxvm/traces/local-f913ef1486eca33af05f34.{meta,coverage}.json` | mtime `2026-11-19 23:11:54`; `meta.json` has `pluginVersion: "0.13.29"`, `harnessVersion: "0.23.2"`; `coverage.json` has `plugin.version: "0.13.29"`, `plugin.harnessVersion: "0.23.2"` |
| erratum recorded (`0.21.5` vs `None`) | `reports/RR-HVERR-20261119.md` §1 + `reports/RR-HVREV-20261119.md` | records that the 0.13.28 gateway resolved `importlib.metadata` to a stale pip dist (`0.21.5`), not `None`, and that 0.13.29's canonical `hermes_cli.version_info` resolver corrects it to the running git version `0.23.2` |
| `atexit` closure-state leak fixed | `ls ~/.local/state/ctxvm/traces/hv-*` before & after `python3 -m pytest packages/hermes -q` (`CTXVM_*` cleared) | `0` `hv-*` files before, **`229 passed, 15 subtests passed`**, `0` `hv-*` files after |
| full CI gate | `bash tools/run-ci.sh` unpiped, `CTXVM_*` cleared | `GATE_RC=0`, `[ctxvm-ci] ALL GATES GREEN` |

## 3. Books closed by the review lane

- `RR-HVERR-20261119`'s own LOG row and day-file section were already preserved in `3db1d87`; this commit adds
  `RR-HVERR-REVIEW` to `reports/LOG.md` (four pipes) and `reports/RR-DAY-20261119.md`.
- Updated `handoff/PROJECT-STATE.md` and `handoff/AGENT-PROMPT.md` §1 to reflect plugin **`0.13.29`** held live by
  gateway **PID `139920`** (`22:51:09` restart) with `harnessVersion: "0.23.2"` verified in a real live-session flush
  and no operator restart remaining.

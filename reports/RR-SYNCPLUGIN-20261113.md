# RR-SYNCPLUGIN-20261113 — `tools/sync-plugin.sh`: the installed copy is now synced and proven, not remembered

H14. Four false conclusions in this lane came from the installed copy being behind the tree, one file short,
or holding a version string that disagreed with what the process had loaded. All four were invisible at the
moment they happened. This card replaces the hand procedure (a four-file list in a prompt) with a script that
derives the module set from the code, copies it, and proves the result by hash, by import, and by process start
time.

Also recorded here: the gateway restart owed since this session's first measurement has happened, and the
running process now attests **0.13.23** from its own flush.

## 1. What the script does

`bash tools/sync-plugin.sh` — sync, verify, report; `--check` — verify only, exit 1 on drift.

1. **Derives the module set from `live/__init__.py`** by parsing its imports and resolving each name against
   `live/` then `src/`. Host and stdlib imports fall out automatically because they resolve to no sibling
   file — there is no blocklist to drift. A new sibling cannot be left behind; that is the failure this
   exists for.
2. **Copies what differs, by SHA-256**, and re-hashes after each copy. A mismatch aborts with exit 1.
3. **Clears `__pycache__`** — stale bytecode survives a file copy.
4. **Import-checks the installed copy** with only it on `sys.path`, and prints the version it loads.
5. **Asserts the three versions agree** — repo `PLUGIN_VERSION`, installed `PLUGIN_VERSION`, installed
   `plugin.yaml` — which is the pair the gate already asserts, checked here on the copy rather than the tree.
6. **Compares the running process's start against the files' mtime** and says `GATEWAY STALE` when the process
   is older, so "the fix is in but the gateway holds the old module" is stated by the tool, not rediscovered
   by hand.
7. **Names the sibling sources it does not sync**, rather than dropping them silently — `live/ctxvm.py` today.

The pid comes from `$HERMES_HOME/gateway.lock`, not from a pattern match on process command lines. The host's
lifecycle guard refuses to run any script that contains an operator gateway-restart command or a `-f` pattern
naming the gateway, and that refusal is correct: a restarter SIGTERMs itself mid-flight. The script therefore
names the restart requirement and points at `handoff/LANES.md` §"The gateway" for the command. This was
discovered the hard way — the first version of the file was refused by the guard on its first run.

## 2. Verification

Live run against the real installed copy:

```
bash tools/sync-plugin.sh --check
  same  context_engine.py / plugin.py / profile_policy.py / uc1_handoff.py
        uc2_forensics.py / uc3_planner.py / uc_registry.py / __init__.py / plugin.yaml
  not synced  packages/hermes/live/ctxvm.py (not imported by __init__.py)
  PLUGIN_VERSION: repo 0.13.23 | installed 0.13.23 | manifest 0.13.23
  load check: 0.13.23 (imported from the installed copy with only it on sys.path)
  gateway: pid 45208 started after these files were written; it holds this build
  sync-plugin: OK — 0 copied, the installed set imports, and the versions agree        exit 0
```

**Red-before probes** (a fixture home under scratch; never the real one):

| Probe | Expected | Observed |
|---|---|---|
| P1 append a byte to the installed `plugin.py`, then `--check` | exit 1, `DRIFT plugin.py` with both hashes | **exit 1**, `DRIFT plugin.py repo 86d96ec… installed a08ba81…` |
| P2 then run the sync | exit 0, `copied plugin.py`, hashes equal | **exit 0**, `copied plugin.py 86d96ecedda979a1` |
| P3 poison the manifest (`version: 9.9.9`) in a scratch copy of the tree | exit 1, `VERSION DISAGREEMENT` | **exit 1**, `repo 0.13.23 | installed 0.13.23 | manifest 9.9.9` |
| P4 fake `gateway.lock` naming a long-started pid, touch the installed file | `GATEWAY STALE` printed, exit 0 (sync is not the restart) | **exit 0** with the stale block and the pointer |
| P5 no lock file | `no running process found`, exit 0 | **exit 0**, that line |

P3 also showed the ordering: the script copies first and refuses second, so a poisoned manifest lands on the
copy before the guard fires — correct for a sync tool, and the reason the version check runs after the copy.

Gate, unpiped, `CTXVM_*` cleared by enumeration: `ts suites green (24 + 62 + 46 tests); python suites green
(201 + 8 + 66 tests)`; `SCHEMA CONFORMANCE: PASS (682 checks)`; `ALL GATES GREEN`. `bash tools/check-handoff.sh`
→ `ALL HANDOFF CHECKS PASS`.

## 3. The restart, and what is now attested

| Fact | Value |
|---|---|
| gateway pid / start | **45208 / Fri Nov 13 23:58:38** |
| installed `__init__.py` mtime | 23:02:42 — older than the process |
| newest sidecar `plugin.version` | **0.13.23**, `capturedAt 2026-11-13T21:59:32Z` |
| previous loaded build | 0.13.22 (pid 24698, started 22:58:59) |

The version is taken from the process's own flush, not from the manifest, so it dates the claim to a process:
`hermes -z "/ctxvm-trace stop"` → `1 trace(s) flushed`, and the flush the process wrote reads 0.13.23.

## 4. Docs updated

- `design/HERMES-PLUGIN-DEVELOPER-PROMPT.md` §5 step 6 now *is* the script (was a four-file list), and §12's
  installed-dir line states the current truth instead of the old leftovers.
- `design/ROADMAP-HERMES-LANE.md`: H14 ticked with its deviation recorded; **H15 rewritten** because its
  premise is now false (see §5).

## 5. Finding: H15 is a decision, not a cleanup

The installed directory no longer carries the old layout — `live/`, `src/`, `test_plugin.py` and
`BUG_REPORT.md` are absent. But `ctxvm.py`, the one file H15 says to keep, is **also absent**, and an
import-derived sync excludes it by construction: the tracer never imports it. So the T17 re-export is either
installed deliberately (add it to the set with a stated reason) or the obligation is dropped. Left as an owner
call; the roadmap item now says so instead of instructing a cleanup that has already happened.

## 6. Limitations

- The script syncs the **shared** installed copy only. A profile-local `plugins/` tree is a different path and
  is not touched.
- It cannot prove the loaded build by itself: a process started after the files can still hold a cached module
  (`sys.dont_write_bytecode`, a read-only tree). The version-specific artifact — a flush after the start — is
  the tie-breaker, and §3 is that artifact.
- `GATEWAY STALE` is a warning, not a failure, because syncing is not restarting. A caller that wants it to
  fail has to compare the two numbers itself.
- Not wired into the gate. Nothing runs `tools/` in `run-ci.sh`; H16 (capture smoke) is the card that puts a
  plugin-level check into the gate.

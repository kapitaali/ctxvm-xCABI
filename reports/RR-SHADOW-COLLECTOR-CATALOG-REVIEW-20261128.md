# RR-SHADOW-COLLECTOR-CATALOG-REVIEW-20261128 — incomplete command discovery still fails open

Review lane, verify-then-record. Subject: `a51ea8d`. Date: 2026-11-28.
No live model call, session creation, profile/gateway/config change, restart, pin activation, publish, or push.

## 1. Verdict

**NOT ACCEPTED for live collection.** One blocker remains: the collector accepts a command catalog whose
quick-command discovery failed, then accepts `type="exec"` as proof that the plugin produced the status.
Quick commands dispatch before plugin commands, so missing quick-command evidence is not proof of
non-shadowing.

The conditional live batch remains blocked. The research-owned fixture manifest and prompt freeze are
still outstanding as a separate execution prerequisite.

## 2. What passed

Independent re-review confirms the previous `a51ea8d` fixes:

- status parsing rejects embedded and duplicate source/name markers;
- clean catalog provenance is checked before dispatch, and an ordinary quick-command collision is rejected;
- relative gateway defaults, expanded paths, and active-status paths fail closed;
- simultaneous auth/model and route failure retains `STOPPED_MODEL_PROVIDER` with both receipt flags;
- focused collector suite: **55 passed, 87 subtests passed**;
- join: **6 passed**; Hermes shadow: **17 passed**;
- full CI: **ALL GATES GREEN**; pristine rehearsal: **4/4 jobs green**;
- kit, hygiene, compile, diff, AST-duplicate, CJK, and production secret/home-path sweeps pass.

Real read-only gateway probes also passed: the live catalog currently reports `warning=""` and
`plugin_discovery_error=""`, `/ctxvm-trace` appears only under `Plugin commands`, active status is enabled
at the expected directory on plugin 0.13.37, and full `--preflight-only` returned rc=0 with 21 baseline
sessions. The preflight used a temporary synthetic SHA-256-pinned manifest, created no session, and left
the session-store count unchanged at 58.

## 3. Blocker — discovery warnings are ignored

`_plugin_status_proven()` (`tools/collect-shadow.py:149-164`) checks `plugin_commands` and display
categories but ignores the catalog's `warning` and `plugin_discovery_error` fields.

The running Hermes source makes both fields authoritative:

- `tui_gateway/command_discovery.py:227-249` records quick-command discovery failure in `warning` and
  plugin discovery failure in both `warning` and `plugin_discovery_error`;
- `tui_gateway/methods_tools.py:993-1005` dispatches in the order quick → plugin → bundle → skill →
  built-in.

Therefore a catalog with `warning="quick_commands discovery unavailable: …"` can still list
`/ctxvm-trace` under `Plugin commands` while a same-named quick command remains undiscovered. Accepting a
subsequent `type="exec"` status does not prove the plugin handled it.

No-model reproduction against the current collector:

```text
WARNING_CATALOG_ACCEPTED {"dispatch_result_type":"exec","enabled":true,
 "source":"start (defaults)","trace_dir":"/gateway/traces","version":"0.13.37"}
```

The mocked catalog carried `warning="quick_commands discovery unavailable: config.yaml unreadable"` and
an empty `plugin_discovery_error`; the collector still queried `command.dispatch` and parsed its
`type="exec"` output. Expected behavior is a preflight refusal before dispatch.

## 4. Required fix

1. Treat incomplete quick/plugin discovery as failed provenance. Reject non-empty
   `plugin_discovery_error` and warnings that report discovery failure; malformed warning/error fields
   must fail closed. A benign non-discovery warning must not be mistaken for a discovery failure.
2. Do not send `command.dispatch` unless catalog provenance is complete and collision-free.
3. Add no-model regressions for quick-command discovery warning, plugin discovery error, malformed
   discovery fields, and `type="exec"` without successful catalog provenance. Retain the clean-catalog
   success case and ordinary quick-command collision rejection.
4. Rerun the focused collector/join/Hermes suites, real catalog/status/preflight probes, full CI,
   pristine rehearsal, kit, hygiene, diff, compile, and privacy sweeps. Append LOG02/day; use a private
   index; do not push.

Routed as `design/experiment-runs/SHADOW-COLLECTOR-FIX5-PROMPT.md`.

## 5. Nice-to-haves

- Construct the `$VAR` parser regression from an actually expanded path rather than leaving literal
  `$HOME` text in the test input.
- Add an explicit assertion that `type="exec"` is rejected when catalog provenance fails.
- For newer Hermes versions, separately account for hidden or gateway-only registry collisions that
  display categories can omit.

## 6. Limitations and claim ceiling

This review proves a fail-open control-path defect; it does not show that a shadowing quick command exists
on the current host. The current real catalog is complete. No metric, rate, candidate pin, causal,
cost-saving, paging-quality, model-quality, determinism, availability, or redaction claim is produced.
`position_band`, `later_dependency_use`, and dependency distance remain UNVERIFIED.

## 7. Repro commands

```bash
for v in $(env | grep '^CTXVM' | cut -d= -f1); do unset "$v"; done
python3 -m pytest tools/test_collect_shadow.py -q
python3 research/shadow-analysis/test_join.py -v
python3 -m pytest packages/hermes/test/test_shadow_mode.py -q
python3 -m py_compile tools/collect-shadow.py tools/test_collect_shadow.py
bash tools/run-ci.sh
python3 tools/ci-rehearsal.py
bash tools/check-handoff.sh
bash tools/git-hygiene.sh
git diff --check
```

The warning-bearing catalog reproduction uses the same fake attach/WebSocket transport pattern as
`GatewayStatusTests.test_read_only_rpc_uses_command_dispatch_without_leaking_ticket`, with the warning
added to the catalog result. It makes no network or model call.

## 8. Applied

This report, one four-pipe `reports/LOG02.md` row, one `reports/RR-DAY-20261128.md` section, the focused
fix prompt, and a separate PROJECT-STATE delta. No collector code changed in the review lane. No push.

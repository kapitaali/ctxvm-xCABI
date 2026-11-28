# RR-SHADOW-COLLECTOR-WHITESPACE-REVIEW-20261128 — explicit-path branch bypasses raw validation

Review lane, verify-then-record. Subject: `49be10f`. Date: 2026-11-28.
No live model call, session creation, profile/gateway/config change, restart, pin activation, publish, or push.

## 1. Verdict

**NOT ACCEPTED for live collection.** The catalog-provenance blocker is fixed, but raw whitespace validation
is still bypassed when `CTXVM_TRACE_DIR` is explicit. In particular, raw `HOME` is stripped before tilde
expansion even though Hermes preserves it, so the collector's launch-state proof can differ from the
plugin's resolver.

The conditional live batch remains blocked. The research-owned fixture manifest and prompt freeze are
still outstanding as a separate execution prerequisite.

## 2. What passed

Independent re-review confirms the `49be10f` catalog and default-path fixes:

- missing/non-string `warning` or `plugin_discovery_error` fails closed;
- non-empty plugin discovery errors and current Hermes quick/plugin/skill discovery warnings reject before
  `command.dispatch`;
- benign non-discovery warnings remain allowed;
- failed provenance sends only `commands.catalog`, so `type="exec"` cannot be accepted afterward;
- default raw `XDG_STATE_HOME`/`HOME` whitespace and active-status directory whitespace are rejected;
- the `$VAR` parser regression uses `os.path.expandvars()`;
- focused collector suite: **57 passed, 98 subtests passed**;
- join: **6 passed**; Hermes shadow: **17 passed**;
- full CI: **ALL GATES GREEN**; committed rehearsal: **4/4 jobs green**;
- kit, hygiene, compile, diff, AST-duplicate, CJK, and production secret/home-path sweeps pass.

Real read-only probes also passed: the live catalog remains complete, active status is enabled at the
expected directory on plugin 0.13.37, and full `--preflight-only` returned rc=0 with 21 baseline sessions.
The temporary synthetic manifest was removed; the session-store count stayed 58→58.

## 3. Blocker — explicit paths skip raw validation

The new checks in `_gateway_trace_dir()` (`tools/collect-shadow.py:100-105`) run only when
`CTXVM_TRACE_DIR` is absent. The explicit branch then strips `CTXVM_TRACE_DIR` at `:112` and strips raw
`HOME` at `:115` before tilde expansion.

No-model probes against `49be10f`:

```text
{"HOME": "/home/test", "CTXVM_TRACE_DIR": " /tmp/traces "}
  -> accepted as /tmp/traces

{"HOME": " /home/test ", "CTXVM_TRACE_DIR": "~/traces"}
  -> accepted as /home/test/traces
```

The second case diverges from Hermes. The installed plugin's resolver
(`~/.hermes/plugins/ctxvm-tracer/__init__.py:117-137`) uses raw `HOME` through `os.path.expanduser()` for
tilde expansion. With the same inputs, Hermes preserves the whitespace and resolves a cwd-relative path;
the collector silently rewrites it to `/home/test/traces`. The later active-status comparison may catch
that mismatch, but launch-state proof is already wrong and the required raw validation is absent.

Hermes also strips an explicit `CTXVM_TRACE_DIR`, so rejecting whitespace there is deliberately stricter
than the plugin. It is still required to make the collector's raw-validation boundary unconditional and
to avoid accepting an unvalidated value before normalization.

## 4. Required fix

1. Validate raw `HOME` whenever it is read or used, including the explicit `CTXVM_TRACE_DIR` branch and
   tilde/`$VAR` expansion. Reject surrounding whitespace before any `.strip()`, expansion, or `.resolve()`.
2. Validate raw `CTXVM_TRACE_DIR` before `.strip()` and reject surrounding whitespace as a fail-closed
   collector boundary. Document that this is stricter than Hermes's explicit-path normalization.
3. Retain the existing default `XDG_STATE_HOME`/`HOME` and active-status whitespace checks.
4. Add explicit-branch regressions for whitespace around `CTXVM_TRACE_DIR`, whitespace in raw `HOME`
   with `CTXVM_TRACE_DIR="~/traces"`, and the matching clean explicit-path cases.
5. Rerun the focused collector/join/Hermes suites, real catalog/status/preflight probes, full CI,
   committed rehearsal, kit, hygiene, diff, compile, and privacy sweeps. Append LOG02/day; use a private
   index; do not push.

Routed as `design/experiment-runs/SHADOW-COLLECTOR-FIX6-PROMPT.md`.

## 5. Nice-to-haves

- Anchor discovery-warning rejection to Hermes's authoritative failure prefixes instead of broad
  substrings, avoiding false rejection of benign text such as “no discovery error.”
- Assert that the expanded `$VAR` regression path contains no literal `$HOME`, making the expansion
  precondition explicit.

## 6. Limitations and claim ceiling

This review proves a resolver-divergence and raw-validation gap; it does not show a live misrouted trace.
The current real gateway paths contain no surrounding whitespace. No metric, rate, candidate pin, causal,
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

The two explicit-branch probes call `_gateway_trace_dir()` directly and make no network or model call.
The Hermes comparison uses `os.path.expanduser()` with the same raw `HOME` and `CTXVM_TRACE_DIR` values.

## 8. Applied

This report, one four-pipe `reports/LOG02.md` row, one `reports/RR-DAY-20261128.md` section, the focused
fix prompt, and a separate PROJECT-STATE delta. No collector code changed in the review lane. No push.

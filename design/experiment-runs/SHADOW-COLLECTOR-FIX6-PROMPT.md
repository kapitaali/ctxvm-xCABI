MASTER PROMPT — hermes/tools lane: make raw path validation unconditional

Authority: `reports/RR-SHADOW-COLLECTOR-WHITESPACE-REVIEW-20261128.md`. One blocker remains at `49be10f`.
No live sessions or gateway/profile/config changes.

1. **Raw HOME:** validate surrounding whitespace whenever `HOME` is read or used, including explicit
   `CTXVM_TRACE_DIR` tilde/`$VAR` expansion. Reject before `.strip()`, expansion, or `.resolve()`.
2. **Raw CTXVM_TRACE_DIR:** validate before `.strip()` and reject surrounding whitespace. This is a
   deliberately stricter fail-closed collector boundary than Hermes's explicit-path normalization.
3. Retain default `XDG_STATE_HOME`/`HOME` and active-status whitespace checks. Add explicit-branch
   regressions for whitespace around `CTXVM_TRACE_DIR`, whitespace in `HOME` with `CTXVM_TRACE_DIR="~/traces"`,
   and clean explicit-path controls.
4. Rerun collector suite, join, Hermes shadow, real catalog/status/preflight probes, full CI, committed
   rehearsal, kit, hygiene, diff, compile, and privacy sweeps. Append LOG02/day; private index; no push.

Live batch remains blocked until independent re-acceptance and the research-owned fixture/prompt freeze.

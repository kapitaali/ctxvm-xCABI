MASTER PROMPT — hermes/tools lane: fail closed on incomplete command discovery

Authority: `reports/RR-SHADOW-COLLECTOR-CATALOG-REVIEW-20261128.md`. One blocker remains at `a51ea8d`.
No live sessions or gateway/profile/config changes.

1. **Catalog completeness:** `_plugin_status_proven()` must reject incomplete quick/plugin discovery.
   Non-empty `plugin_discovery_error` and warnings that report discovery failure are failed provenance;
   malformed warning/error fields fail closed. Preserve acceptance of a complete catalog with a benign
   non-discovery warning if Hermes can emit one.
2. **Dispatch boundary:** do not call `command.dispatch` unless the catalog proves complete,
   collision-free plugin provenance. `type="exec"` is acceptable only after that proof.
3. Add no-model regressions for quick-command discovery warning, plugin discovery error, malformed
   discovery fields, clean provenance, ordinary quick-command shadowing, and `type="exec"` after failed
   provenance. Construct the `$VAR` parser case from an actually expanded path.
4. Rerun collector suite, join, Hermes shadow, real catalog/status/preflight probes, full CI, rehearsal,
   kit, hygiene, diff, compile, and privacy sweeps. Append LOG02/day; private index; no push.

Live batch remains blocked until independent re-acceptance and the research-owned fixture/prompt freeze.

# RR-STUB-RENDER-LIVE-20261124 — 0.13.33 live; full stub wire verified under gateway interpreter

Lane: hermes. Record of the operator's gateway restart after `RR-STUB-RENDER-20261124`
(`046cc2b` + `140c540`). **Documentation only — no code change, version bump, gateway action by this
lane, model call, spend, or push.**

## 1. Build-live proof

- Gateway **pid 100399**, started **2026-11-24 17:05:46**, after the 0.13.33 files were written.
- `bash tools/sync-plugin.sh --check` → repo / installed / manifest all **0.13.33**, installed-set
  load check OK, "gateway pid 100399 started after these files were written; it holds this build."
- Under the **gateway's own interpreter**, with only the installed copy on `sys.path`, a synthetic
  tracer emitted, in order:
  `page.evict(turn=0, stubText=S)` then `page.render(turn=0, mode=stub)`.
  Assertions: `stubText == S` byte-for-byte, both turns equal, `ts` last on both. This exercises the
  shipped `emit_evict` + `emit_stub_render` pair, not the repo source.

## 2. Real-capture default-off attestation

Two real sidecars flushed at **17:08** under the restarted build:
- `local-f913ef1486ec….coverage.json` — `pluginVersion 0.13.33`, `stubDropped "off"`, `stubbedRefs []`.
- `20261123_162732_….coverage.json` — same version / off / empty.

So the new build is live on real sessions and default-off is attested per session. **No live stub-mode
capture exists** — the accepted Part C arm attestation/re-read gap (`RR-PARTC-ARM-RESULT`,
`RR-RETRY-BLOCKED`) remains unchanged. This card does not close it.

## 3. Consequence

The full stub-mode wire (`page.evict` + `page.render(mode=stub)`, same PageId, same visibility turn,
byte-identical `stubText`, `ts` last) is shipped and live at **0.13.33**. Research may use the full
A3/A4 wording; the paper edit belongs to the research lane and is not made here. Future stub-arm
preflight cites **0.13.33**.

No cost-saving, paging-quality, model-quality, determinism, or `stubText`-redaction claim.

# RR — UC1DESIGN — UC1-PLUGIN design pass (within-harness pause/resume + ctxvm-py binding)

**Card executed:** UC1-PLUGIN (M), milestone 1 of the board row — design pass FIRST,
implementation beats follow.

## What was done

- `design/uc1-plugin.md` — the design pass: pause/resume semantics, wedge-boundary
  handling, provenance transport, the ctxvm-py binding plan, four implementation
  beats (B1 binding → B2 pause modules → B3 resume modules → B4 corpus offer),
  and three open questions for the orchestrator.
- Grounding reads (no writes): memo-UC1 (`research/use-case-1-cross-agent-handoff.md`,
  all 277 lines), `00-README.md` "What is decided" (binding + plugin-organization
  rows), `09-plugin-parity.md` §1/§4, `design/mcp-shim.md` (house style), ORG-1's
  landed `uc_registry` shape.

## Verification (the anchor the design stands on)

- **T21 export already produces the entire memo-specified artifact set** —
  witnessed live: `rust/target/release/export corpus/m2/live-echo.jsonl --turn 3
  --output /tmp/opencode/x21 --odps` → `trace-3.jsonl.zst`, `page-table-3.json`,
  `manifest.yaml` (ODPS 4.1 + DQ: replayDeterminism/sourceFidelity true,
  KPIs + projection slots/tallies), `llms.txt`, `checksums.sha256`. The pause
  surface therefore packages committed engine output — the module adds
  orchestration only (flush → era snapshot → packaging), which is why the
  board's "thin wrapper" clause can be honored literally.

## Deviations from the board-row sketch (explicit)

1. **Resume = verify-first, not immediate injection.** The sketch said "same-harness
   boot-time resident-context injection". Design verdict: in v0 every recorded
   session is eviction-free (corpus law), so the page table's resident set IS the
   harness's native continuation state — verify + provenance is the honest v0
   surface, and injection becomes real only with eviction-bearing sessions (v1
   pager), as a separately-gated `handoff-inject` beat. The wedge (tracer never
   mutates) is preserved by construction, and memo-UC1 §4's honest framing is
   satisfied verbatim (page-level state transfer + within-harness replay evidence,
   no cross-harness claim).
2. **Pause trigger = env-first, slash as a front** (hermes gets `/ctxvm-handoff`
   only as sugar over the same env the module reads; opencode stays env-gated).
   The board sketch did not fix trigger mechanics; the design does.

## Discoveries (facts that update other surfaces)

- **ORG-1's 11 uc tests are local-only.** Gate 2 runs `python test/test_plugin.py`
  (23 tests) only — `test_uc_registry.py` is not wired into `tools/run-ci.sh`, and
  gate 2b's pytest does not cover `packages/hermes`. Current gated truth: 23 hermes +
  27 benchmark tests; the "34/34" board-row figure is a local count. Flagged in
  `08-HANDOFF.md` §0; per house precedent (BUDGETSWEEP → HYG-1) this is flagged
  forward, not silently patched — the next hermes-lane card (UC2-PLUGIN) touches the
  same test surface and wires it.
- The sidecar (§3) — not the event table (§2) — is the only transport available for
  resume provenance under the parity contract without an RFC-0 revision; the design
  binds the extension to the contract's §4 DoD rule.

## Open questions

1. `handoff-inject` stays out of the first implementation beats (verify-only
   resume first) — confirm.
2. ctxvm-py binding needs maturin/venv wiring in gate 2 (S-sized CI addition) —
   greenlight or keep the binding off-gate until it exists.
3. opencode has no command surface in the live adapter — witness-only pause
   acceptable for v0, or should pause flip to stop semantics there?

**Status: design pass DONE** (this file + `design/uc1-plugin.md`); the remaining
card (binding + pause/resume modules) executes after orchestrator sign-off.

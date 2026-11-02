# RR-20261102 — provider identity at tracer creation: the settings layer, the no-backfill law, and the install defects the DoD check exposed

**Card:** the two open facts the default-ON plugin lane left on 2026-11-01
(`RR-PLUGIN-DEFAULTS` addendum + `RR-DAY-20261101` §6/§9): the first live
capture stamped `provider: "unknown"` in `session.open` and `call.meta`
(and the W13 task list named provider-from-the-payload as "the next small
card rather than a redesign").

## 1. The gap, source-pinned

- The first observed hook that creates a tracer is `pre_llm_call` (turn prep;
  `session_start` did not fire in that build). Its payload carries
  `model`/`platform` but **no provider**, per the source-verified payload
  table (`packages/hermes/HOOKS.md` §1, hermes Agent v0.22.5).
- `pre_api_request` **does** carry `provider` — but fires after turn prep
  (`agent/turn_api_request.py:158` inside the request flow, after
  `agent/turn_context.py` prep), so the identity harvest there can never
  reach a tracer that already exists. Identity is stamped once at creation:
  it rides `session.open` and every `call.meta`, and write-through persists
  each event immediately — a later "provider fix" would produce a
  partial-file/final divergence. **Identity cannot be backfilled; the law is
  now written down** (09-plugin-parity.md §5.1, "Identity immutability law").

## 2. What landed

- **Identity priority chain: payload > plugin settings > env > `unknown`**
  (09-plugin-parity.md §5.1). The new middle layer reads the host-owned
  plugin settings subtree — hermes
  `plugins.entries.<id>.settings.model` / `.provider` via `ctx.get_config`
  (`hermes_cli/plugins.py:265`, verified against the pinned runtime) — at
  **register() time, before any hook fires**. A default-ON gateway with zero
  `CTXVM_*` env can complete its identity from its own declared settings;
  the owner never needs to reinstate the env ritual.
- `_identity_from_settings()` is fail-open by design: no `get_config`
  attribute, `None`, blank/non-string values, or a raising host all degrade
  to "no setting" — identity fragments must never block hook dispatch.
- `PLUGIN_VERSION`/`plugin.yaml` → **0.4.1**, so a stale running copy is
  identifiable from its own output.
- Tests: 2 new (`test_settings_identity_fills_the_init_fallback`,
  `test_settings_outrank_env_and_payload_still_wins`); hermes suite 97 →
  **101 pass**. The payload-still-wins law is unchanged and still pinned by
  the existing `test_identity_from_payload_stamps_session_open`.

## 3. Defects found en route (both fixed in this card)

1. **The installed copy's `plugin.py` was one refactor behind.** The
   previous session's sync updated the wrapper (`__init__.py`) but left
   `plugin.py` at its RFC-0.1 state — without the entire W13 block
   (`_turn_prefixes`, the W13 `on_pre_api_request`). The parallel §6 DoD
   rule ("re-install the hermes copy if its adapter changed") was applied
   from the WRAPPER's view, not from the pair's. A restarted gateway would
   then run `pre_api_request` payload into a core that had no handler for
   the W13 snapshot (fail-open ⇒ silent no-op).
2. **The installed dir had no `plugin.yaml` at its root.** The loader
   contract is explicit: "a directory plugin needs a `plugin.yaml` manifest"
   (`hermes_cli/plugins.py:7`). The stale `live/` sub-copy inside the
   installed dir still carried a 0.1.0 manifest from an earlier layout.

Fixes: full re-sync per §6 — `__init__.py`, `plugin.py`, and `plugin.yaml`
at the installed ROOT (hashes verified equal to the repo bytes), and the
**hermes plugin doctor now passes**: "manifest: ctxvm-tracer 0.4.1 … import
and registration passed … 6 hook(s)". The stale `live/` subdirectory was
left in place (no deletion without an owner look).

## 4. Verification limits (stated)

- The settings layer is **register-time wiring specific to the hermes
  adapter** (opencode's payload already carries `providerID`; §6's
  both-harness rule does not apply to a host-only source). Event wire bytes
  unchanged.
- The live-verification claim (a gateway with settings declared →
  `provider` non-unknown at `session.open`) still needs the gateway
  **restart** — same clock as the W13 prefix Che(/^toolSchemas/) observation.
- **Session-env lesson recorded:** this card's first local gate run showed
  4 canonical failures — all traced to the tool session itself carrying the
  full `CTXVM_*` capture family (incl. `CTXVM_TRACE_TS=0`) into pytest
  import-time sabotage of default-on facts, NOT to code (`env | grep ^CTXVM`
  was the tell). The gate was re-run in a CTXVM-clean shell, ALL GATES
  GREEN. Future captures from this workflow: run the books' gates with the
  harness's own `CTXVM_*` unset — the repo's tests assume a neutral env and
  `_clear_env_for_tests()` does not run before every tracer construction.

## 5. Deviations

None. One card, one change-family (identity completion at creation +
its §6 re-install). No sealed surface, no schema, no emitter bytes touched.

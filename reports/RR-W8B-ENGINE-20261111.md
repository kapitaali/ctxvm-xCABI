# RR-W8B-ENGINE-20261111 — the engine cannot engage on the CLI path in this build

Date: 2026-11-11. Blocks: `w8b-cell-01` (its precondition is `engineSelections > 0`).

## What was tested, and what came back

| # | what | profile | engine setting | selections | attestation |
|---|---|---|---|---|---|
| 1 | one prompt, `hermes chat -q … --oneshot`, HERMES_HOME = arm | `w8bn-paged` | `ctxvm` | **0** | `engine: null`, `profile: default`, `budgetTokens: 70000/settings` |
| 2 | the same, with `context.engine: "ctxvm"` set on the **default** config and restored after | default | `ctxvm` | **0** | `engine: null`, `profile: default` |
| 3 | plain interpreter, plugin dir on `sys.path` | — | — | — | `_HOST_ABC: True`, `build_engine(70000)` returns a live engine |

Row 3 is the control: the engine class builds. Row 1 and row 2 say the host never selects with it on
either profile, so this is not a profile-attribution problem — it is the CLI path itself.

## Why

`hermes_cli/cli_tui_mixin.py:1833` states the design: *"plugins load in the gateway, not here
(PLG-7)"*. `agent/agent_init.py:_select_context_engine` resolves `context.engine` and then looks for a
plugin-registered instance through `hermes_cli.plugins.get_plugin_context_engine()`; if that returns
None it warns and falls back to the built-in compressor. On the one-shot CLI path the agent is built
without a plugin manager holding a registered engine, so the fallback is deterministic — and the
fallback warning does not appear in the logs of these runs, which is itself consistent with the
manager being absent rather than the engine being rejected.

The capture still works because the plugin's event hooks are what write it; the engine is a separate
contract the host has to activate, and on this path it does not.

## A second defect found while testing (unverified cause)

Row 2 ran **without** `HERMES_HOME` and on the default config, where `context.budgetTokens` does not
exist (`grep -c 70000 ~/.hermes/config.yaml` → 0). Its sidecar still attests
`budgetTokens: 70000, budgetSource: "settings"` — the arm's value, from a run that was not on the arm.
Either the sidecar read a neighbouring capture or the settings lookup is not scoped to the process's
home. Until that is settled, no per-arm setting in a sidecar can be trusted on its own; the runner's
preflight reading of the profile is the authority.

## What this means for the card

The blocker is no longer "engine null, cause unknown". It is now located: **this Hermes build does not
activate a plugin-provided context engine on the one-shot CLI path.** No amount of re-running will
produce a cell there. The prediction block's precondition correctly refuses to spend itself.

## Two ways forward, with their costs

**(A) Run the pair through the gateway.** The gateway loads plugins at startup, which is the path where
the engine has ever engaged (the paid cells of 2026-11-09 recorded `engineSelections: 9…14`). Cost: a
driver that submits the 20 prompts to a gateway session instead of spawning `hermes chat`, plus a check
that the session is bound to the arm profile. The instrument stays as designed; the one-factor
difference stays `context.engine`.

**(B) Move the selection seam into the plugin's `pre_llm_call` hook.** The hook already runs on both
arms and already records `page.declare`; selection would be gated by a plugin setting
(`selection.enabled`), and `select_context` would be called from the hook rather than by the host.
Cost: a new instrument version (0.11.x), a fresh preregistration, and the one-factor difference becomes
a plugin setting rather than `context.engine` — the arms then differ in a field the plugin owns, which
is weaker evidence than a host-level config difference.

Recommendation: **(A) first**. It preserves the preregistered design and the single-factor claim. (B)
remains the fallback if the gateway cannot be driven non-interactively without disturbing the owner's
running session.

## Not done, deliberately

No pair was started; no cell exists; spend $0.00. The block stays committed and unspent, which is what
it is for.

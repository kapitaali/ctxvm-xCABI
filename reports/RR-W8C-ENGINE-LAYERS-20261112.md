# RR-W8C-ENGINE-LAYERS-20261112 — the engine is registered, both configs say ctxvm, and the host still builds the compressor

Zero spend. One free prompt under `w8cn-paged`, plugin 0.13.4, gateway restarted at 14:18:41.

## The three fields, and what they rule out

```
engineRegistered  "ctxvm"      the plugin's register() ran and the host accepted the engine
rootEngineSetting "ctxvm"      ~/.hermes/config.yaml context.engine — what the host reads
homeEngineSetting "ctxvm"      <profile>/config.yaml context.engine — what the policy reads
engine            null         yet the agent was built with the built-in compressor
engineSelections  0
```

Checked independently of the plugin:

```
load_config_readonly() for both homes      context.engine = ctxvm
_select_context_engine(profile cfg)        → CtxvmFaultPinEngine
plugins.isolation                          "in_process" (not the child host)
duplicate YAML keys                        none in either config
clone_for_agent failure warnings           none in any log
gateway registration line                  14:18:47 "registered context engine: ctxvm"
```

## So the disagreement is inside the agent build, not in any file

`agent_init` reads `_agent_cfg = load_config_readonly()` and calls
`_select_context_engine(_agent_cfg)`. That function returns None on three paths: `safe_worker_enabled()`,
`_engine_name == "compressor"`, or no candidate whose `.name` matches. The first two are excluded by the
evidence above (safe-worker is False in-process; both configs say ctxvm). The third requires
`get_plugin_context_engine()` to be empty **at the moment that agent is built** — while the plugin
demonstrably registered in the same profile's process, six seconds after the gateway started.

The remaining hypothesis is an **ordering / process boundary**: the agent for a `--oneshot` session is
constructed before the plugin registry that carries the engine is populated in that process, or in a
different process from the one that ran `register()`. It is consistent with everything measured: hooks
work (captures are written, the sidecar is stamped), registration is logged, and only the engine slot
comes back empty.

## Why this matters beyond today

Cell-02 and cell-03 ran with the engine engaged on this same machine, hours earlier. Something changed in
between — most plausibly a Hermes update or a restart that altered plugin load order. That means the
treatment arm's liveness depends on a host-side ordering property that nothing in the pair controls and
no config file records. The three sidecar fields now make the failure legible, but they do not remove the
dependency.

## What is blocked and what is not

Blocked: the call-granularity re-scoring pair (it needs a capture with `callSizes`, which needs the
engine to engage). Cost of the block: **$0.00** — every attempt refused or produced a VOID.

Not blocked: everything measured so far. Cell-02 and cell-03 stand; the simulator's turn-level failure
stands; the paid bill stands.

## Next action, one of two

1. Test the ordering hypothesis directly: log `get_plugin_context_engine()` inside
   `_build_context_engine` (host-side patch, not ours) or run the gateway with plugin isolation forced
   in-process per profile and compare.
2. Bypass the host slot: have the plugin apply its selection from its own hook rather than through
   `register_context_engine`. That is a design change with its own risks and is not a small edit.

# RR-IDENTITY-20261106 — the documented remedy for `provider: unknown` was dead

Card: defect found while verifying the engine activation. Plugin 0.10.1. No schema, no wire change.

## What the log said

Every plugin load since 0.4.1 wrote this line into `~/.hermes/logs/agent.log`:

```
WARNING hermes_cli.plugins: Rejected config path 'model' from plugin ctxvm-tracer
```

It was read as noise. It was the failure.

## Root cause, verified against the host

`ctx.get_config(key)` validates the key as plugin-relative and refuses any key whose **first
segment** is reserved (`hermes_cli/plugins_state.py:17`):

```
model          -> REFUSED: Expected a plugin-relative config key such as 'endpoint' or ...
provider       -> ('provider',)
identity.model -> ('identity', 'model')
```

The identity reader asked for `model` and `provider` inside **one** `try` block. The `model` call
raised, the exception was swallowed by the fail-open handler, and the loop never reached `provider`.
So:

- `plugins.entries.ctxvm-tracer.settings.model` was unreachable through this API;
- the **documented remedy for `provider: unknown`** — the `settings.provider` line the reports and the
  handoff have told the owner to write since 2026-11-02 — never executed;
- and the failure was invisible, because fail-open is the correct behaviour for a hook path and it
  hid a permanent configuration defect.

The suite stayed green because its fake `ctx.get_config` mapped bare keys and did not enforce the
host's reserved-root rule. A permissive fake hid a real refusal.

## The fix

`_identity_from_settings` now reads the **non-reserved mapping** `identity` first, then only the bare
`provider` key. The bare `model` probe is gone: it is refused on every host version seen, so it could
only raise and log a rejection warning on every load — the noise that hid this defect in the first
place. Model comes from the mapping or not at all.

```yaml
plugins:
  entries:
    ctxvm-tracer:
      settings:
        identity:
          model: "deepseek/deepseek-v4.1-flash-1017"
          provider: "deepseek"
```

A bare `settings.provider` still works, because `provider` is not a reserved root. Absence is still absence: a blank or non-string value is
skipped, never minted.

**Live check on the installed copy** (0.10.1), with a stub that enforces the host's rule:

```
identity via mapping          -> {'model': 'vendor/m', 'provider': 'vendor'}
provider with refused model   -> {'provider': 'vendor2'}
```

## A follow-up worth one line: the warning is silenced

The 0.10.1 version still probed the bare `model` key in its own `try`, which keeps the host warning
alive on every load. 0.10.2 removes that probe, because a call that can only fail is noise. The two
test fakes that mapped bare keys (and so never enforced the host rule) are now host-shaped, which is
what let the defect hide.

## Also fixed in the same card

`provides_hooks` in `plugin.yaml` declared six hooks. The plugin registers seven and had done since
0.10.0: `post_api_request` was missing from the manifest while it was carrying the provider receipt.
The manifest now matches the registrations, which is what a capability check reads.

## Verification

```
python -m pytest packages/hermes -q     171 passed, 15 subtests passed
```

The suite now contains a `ReservedRootCtx` stub that mirrors the host rule and asserts both cases:
the `identity` mapping fills both fields, and a refused `model` no longer aborts the `provider` read.

## What this does not do

- It does not invent a provider. A trace captured before the owner writes the settings key still says
  `unknown`, and old traces are append-only.
- It does not prove a live settings read end to end: that needs the gateway to restart with 0.10.1 and
  a settings key present. The unit path and the installed-copy path are proven; the host read is
  proven only in the resolver, not through a real config file with a real key.
- It does not change the reserved-root list. The host's refusal is a sound rule; the plugin was
  asking for the wrong keys.

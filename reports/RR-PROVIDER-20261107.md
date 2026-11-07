# RR-PROVIDER-20261107 — wrong provider in the run profiles, and where a `-z` turn actually runs

Card: configuration. Two findings, the first fixed, the second changes how the runner must work.

## 1. Wrong provider (fixed)

The W8 profiles carried stale routing:

```
profiles/w8-naive/config.yaml:  model.default: "nvidia/nemotron-3.5-super-vl-120b-a12b"
profiles/w8-paged/config.yaml:  same
profiles/*/config.yaml:         provider: "nvidia"
```

while the global config says `provider: "nous"`. The profiles were copied on 2026-11-06 from a
config that had since changed, so the experiment would have run against the wrong endpoint.

`openai/gpt-6-luna` is not served by `nvidia`, so routing fell through to another vendor — the run
died on `429 org_token_rate_limit_day … provider=experientiallabs, model=gpt-6-luna`. The free tier
behind that fallback was never the intended endpoint.

Fixed in both profiles: `provider: "nous"`, `model.default: "openai/gpt-6-luna"`. Verified:

```
HERMES_HOME=…/w8-naive hermes config get model.provider  -> nous
HERMES_HOME=…/w8-paged hermes config get model.provider  -> nous
```

A live probe through nous answered `OK` with no rate limit, so the endpoint and the model id both
resolve.

## 2. A `-z` turn runs in the gateway, so client-side env does not reach it

`hermes_cli/main.py:2844`:

```python
def _chat_runs_at_gateway(args) -> bool:
    """Every ``hermes`` / ``hermes chat`` turn (classic view, ``-q``, ``-z``, TUI) executes in the
    gateway, which discovers and owns MCP servers itself."""
    return args.command in {None, "chat"}
```

Measured: a probe exported `CTXVM_TRACE_DIR=/tmp/w8/probe` and `CTXVM_TRACE_NAME=probe`; the
directory stayed empty and the capture appeared in the **gateway's** directory instead
(`/tmp/w8/traces/w8-36a80c11.jsonl`, `session.open` ts `12:37:05.833Z`, model
`openai/gpt-6-luna` — the probe's model). The same probe with an explicit `--provider nous` still
recorded `provider: unknown`, because the plugin's identity reader resolves settings in the
**gateway** process, which predates the profile edit.

Consequences, stated plainly:

- `tools/w8-run-env.sh` does not by itself control where a run's trace lands. It must be sourced
  **before the arm's gateway starts**, so the executing process carries it. The script header now
  says so.
- Two arms need two gateways, one per profile, each started under its own environment. A single
  shared gateway writes every arm into one directory and one name, which is exactly the seventeen
  `w8-run-<hex>` files seen earlier: same name, many session ids, collision suffixes.
- `session.open.provider` stays `unknown` until the gateway that serves the run has been started
  after the identity fix. This is not a plugin defect: the host payload for that hook carries no
  provider, so settings are the only source.

## What is verified and what is not

Verified: the provider values in both profiles; a `nous` call answering without a rate limit; the
gateway as the executing process (source docstring plus the misplaced capture); the probe's model in
the gateway trace.

Not verified: whether a per-profile gateway honours the profile's environment when it is spawned on
demand — the probe's prompt went to the already-running gateway. That needs one deliberate test
before the grid: start the paged profile's gateway under `tools/w8-run-env.sh`, send a probe, and
confirm the capture lands in the run's directory with `provider: nous`.

## Next steps

1. Restart the gateway so it loads plugin 0.10.3 and the `nous` identity.
2. One probe through the arm's own gateway; confirm directory, `provider`, and model in
   `session.open`.
3. Re-pilot (both arms) on the corrected routing, then decide the model question from the earlier
   card: Luna's free pool cannot carry a 3.07M-token grid.

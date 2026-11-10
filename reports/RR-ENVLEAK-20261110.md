# RR-ENVLEAK-20261110 — "run gates" went red twice; both causes are the everyday-capture
environment leaking into the kit shell. The committed tree is green (gate rerun ALL GATES GREEN).

Trigger: owner asked "run gates"; `bash tools/run-ci.sh` FAILED at gate 2/4 @ctxvm/node — without
any pkg/ or tool/ byte having changed since the last green (my commits `43d73bb..7f9f4ae` touch
only handoff/, reports/ md, 08-HANDOFF.md). Investigation, not conclusion: find what changed.

## Finding 1 — `CTXVM_TRACE_TS=0` (the D9 opt-out) was exported in the kit shell

`env | grep -i ctxvm` shows the full everyday-capture identity in this shell: CTXVM_AGENT_ID=hermes,
CTXVM_PROVIDER=nous, CTXVM_MODEL=deepseek-v4.1-flash-1017, CTXVM_TRACE_DIR=…, CTXVM_FEATURES=…,
CTXVM_BUDGET_TOKENS=200000, CTXVM_TRACE_NAME=ctxvm-dev, CTXVM_TRACE_TS=0,
CTXVM_HERMES_VERSION="Hermes Agent v0.23.0 (2026.9.24) · stable · local 2bd378ed1b8d".
CTXVM_TRACE_TS=0 is exactly the D9 reproduction opt-out recorded in
`reports/RR-P4TS-20261109` (ts default-ON with this env opt-out). With it set, the node tracer
stamps no `ts`, so two law-asserting tests fail ("ts rides LAST on every event", RFC-0.1 §R4):

- `packages/node/test/tracer.test.ts:172` — actual keys
  `[type, turn, provider, cacheEstimate, latencyMs, providerUsage]`, expected `[…, 'ts']`.
- `packages/node/test/tracer.test.ts:240` — session.open last key inherited as 'schemaVersion'
  (the field declared before ts), expected 'ts'. Both failures are the omission's exact
  fingerprint.

Repro-off: `env -u CTXVM_TRACE_TS node --test packages/node/test` → **22 pass, 0 fail**.

## Finding 2 — `CTXVM_HERMES_VERSION` stamps an env-provided `harnessVersion` the manifest
test pins to None

With ts unset, gate 2 advanced to the hermes suite and failed 1/182:
`CoverageManifestTests.test_instrumentation_and_sidecar_identities_are_lane_fixed`
(`packages/hermes/test/test_plugin.py:1908`): `assertIsNone(manifest["plugin"].get("harnessVersion"))`
got `'Hermes Agent v0.23.0 (2026.9.24) · stable · local 2bd378ed1b8d'` — byte-equal to the shell's
CTXVM_HERMES_VERSION. The lane law the test pins (message in the assert itself): "the hermes lane
has no per-run toggles; the constants are pinned here and mirrored in tools/coverage_check.py's
docstring". An env-injected harnessVersion would break that lane-fixed identity.

Repro-off: `env -u CTXVM_TRACE_TS -u CTXVM_HERMES_VERSION python -m pytest packages/hermes -q`
→ **182 passed, 15 subtests passed in 1.34s**.

## Authoritative result

`env -u CTXVM_TRACE_TS -u CTXVM_HERMES_VERSION bash tools/run-ci.sh` →
**ALL GATES GREEN** at HEAD `7f9f4ae`: gate 1 rust + tiktoken + release binaries; gate 2 ts
suites 22+62+46 and python suites 182+8+66, check-node-build OK (16 events byte-identical, dist
imports resolve without type stripping); gate 2b metrics; gate 3 schema PASS (682 checks —
677 positive lines across 27 fixtures + 5 negative rejects), export round-trip OK; gate 4 hub
byte-identity green. No repo byte changed in any of these runs; both reds reproduce only from env.

## Gate-law note (PROPOSAL, owner-gated)

The mirror is `.github/workflows/ci.yml`, which runs in an Actions env that carries no CTXVM_*
vars; "ALL GATES GREEN" is defined against that env. A kit shell that inherits the owner's
everyday-capture env must drop the capture vars for the run to be representative. Two honest
positions: (a) document the two-var `env -u` prefix as the correct kit-shell invocation
(recorded here); (b) a runner change — e.g. `tools/run-ci.sh` detects exported CTXVM_* capture
vars and WARNs (or scrubs) before running — is a tool change to the ONE deciding command, so it
is proposed, not edited in passing.

## Limitations

- Only the two vars that bit today are verified off; other CTXVM_* vars (MODEL, PROVIDER,
  TRACE_DIR…) survived the gate unasserted — a future test could pin one of those too.
- The first red run left kept logs at /tmp/ctxvm-ci-logs-hG92xs/_ctxvm_node_suite.log and the
  second at /tmp/ctxvm-ci-logs-BYXjHh/_ctxvm_hermes_suite.log (ephemeral, not durable books).
- The leak's origin (owner's capture-session profile) is outside this repo; recorded, not fixed.

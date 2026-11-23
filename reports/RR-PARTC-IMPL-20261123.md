# RR-PARTC-IMPL-20261123 — Part C: opt-in recoverable stub seam landed (plugin side)

Lane: hermes. Authority: `RR-PARTC-AUTH-20261123` (owner "authorize part C", routed to hermes).
**Fix for a measured defect** (Part B middle accuracy 8/8 → 1/8; head control 8/8; 0/8 post-question
re-reads in `RR-PARTB-REREAD`) — not a continuation of the paging hypothesis. Version **0.13.29 →
0.13.30**, synced. No default-on change, no D17 action, no push, no re-score of Part B, no pooling.

## 1. Scope actually landed

The routing named the seam: `context_engine.py::_assemble`. I implemented **the plugin side only**.
The **stub arm** itself (adding the arm to `experiments/needle-revisit/partB/`, same frozen bank/scorer/
profiles, 8 sessions) is `experiments/**` — experiment-lane work, not touched here.

## 2. The seam

- **Opt-in setting** `stubDropped: off | recoverable` in `profile_policy.py`'s narrow YAML scanner,
  read under `plugins.entries.ctxvm-tracer.settings`. **No env channel** — `test_ambient_env_cannot_enable_the_stub`
  pins that an ambient `CTXVM_STUB_DROPPED` cannot turn it on. Default `off`; explicit constructor value
  never overridden; adopted at call time like budget/mode (one gateway serves every profile).
- **`_stub_message()`**: for a DROPPED tool result, emit `[ctxvm: dropped result for <tool>(<args>);
  re-run to restore.]` — **tool name + arguments + hint only**, never the result body or planted code.
  Pure dict/string work (L7: no write/socket/spawn). Repositioned pages still ride the block verbatim
  and are never stubbed.
- **Pair validity**: a stubbed call stays in its assistant carrier (`stubbed_calls` removed from
  `removed_ids`) so the model can actually re-run it. Originals are never mutated (rewrite-on-copy).
- **Attestation**: the engine's plan payload carries `stubDropped` + `stubCount`; the coverage
  sidecar's `plugin` block carries `plugin.stubDropped` (off when no plan). Captures attest the setting.

## 3. Tests + red-before (9 new, in `test_context_engine.py`)

Laws: off by default; recoverable stub replaces the drop; **no page body or planted `VAULT-03 CODE
48213` in the stub**; stubbed call survives in its carrier; plan attests mode/count; off-mode attests
zero; no env opt-in; scanner reads the setting; absent setting defaults off. **Red-before:** deleting
the `out.append(self._stub_message(...))` line fails `test_recoverable_stub_replaces_the_dropped_result`
(rc=1); restored → 9 pass.

## 4. Verification

- `python -m pytest packages/hermes -q` → **238 passed, 15 subtests** (229 + 9).
- `bash tools/run-ci.sh` unpiped, `CTXVM_*` cleared → **rc=0 ALL GATES GREEN** (py 238+8+66).
- `bash tools/sync-plugin.sh` → repo/installed/manifest all **0.13.30**, installed load check OK.
- **dq scan of the literal stub text** → zero matches (no email/path/secret/IPv4 pattern).
- `coverage_check.py` has no strict plugin-key allowlist; the added attestation key is accepted.
- Gateway restart **owed to the operator** (not done here): pid still holds 0.13.29, so the stub is
  not live until the operator restarts.

## 5. Not claimed / not done

No cost saving, no general paging-quality or model-quality claim, no determinism claim. No default-on
change. No registry/catalog/release action. Part B result untouched. Stub arm not built or run. No push.

## 6. Owed

- Operator: gateway restart to 0.13.30.
- Experiment lane: build/run the opt-in stub arm under the five authorization conditions — including
  the re-read readout (`read_file` on the needle after the final question) that closes Part B's UNVERIFIED half.
- Review lane: verify + record this card.

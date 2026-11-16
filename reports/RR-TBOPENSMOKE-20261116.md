# RR-TBOPENSMOKE-20261116 — wired compatibility smoke: PASS for v2.3.0 loading and flush

**Lane:** opencode. **Date:** 2026-11-16. **Scope:** exactly the one-prompt smoke authorized for
`design/TB-OPENCODE-WIRED.md` §5. **No full run, no ceiling frozen in this card, no model call beyond
the single smoke prompt.** No trace bytes, credentials or unredacted session text are committed.

## 1. Verdict

**PASS** on the question the smoke asks: OpenCode **v2.3.0** still loads the v2 promise-plugin shim,
fires `session.context`, and flushes a valid, replayable xCABI trace plus a populated `.meta.json`
on graceful exit. One stated gap: the prompt had no tool call, so `tool.execute.before/after` were
**not exercised at runtime**; their registration is in the adapter source, but runtime evidence for
that domain is UNVERIFIED by this smoke and is a full-run fidelity item (§5).

## 2. What ran

Fresh private run dir `~/.local/state/ctxvm/w8-runs/tb-wired-smoke-20261116/`, containing only
`.opencode/plugins/ctxvm.ts`:

```ts
export { default } from "/absolute/path/to/ctxvm/packages/opencode/live/ctxvm.ts";
```

No built `dist`, no `opencode.jsonc` `plugin` key. Ambient `CTXVM*` variables were enumerated and
unset, then these seven were set deliberately in the booting process:

| var | value |
|---|---|
| `CTXVM_TRACE_DIR` | `~/.local/state/ctxvm/traces` |
| `CTXVM_TRACE_NAME` | `tb-wired-smoke-20261116` (fresh) |
| `CTXVM_MODEL` | `opencode-go/hy4-flash-free` |
| `CTXVM_PROVIDER` | `opencode-go` |
| `CTXVM_AGENT_ID` | `tb-wired-smoke` |
| `CTXVM_BUDGET_TOKENS` | `60000` (owner ruling `RR-TBBUDGET-20261116`; metadata/`headroom` only, not an engine budget) |
| `CTXVM_OPENCODE_VERSION` | `v2.3.0` from `opencode --version` |

Command (graceful self-exit; no hard kill):

```sh
opencode run --standalone --auto -m opencode-go/hy4-flash-free \
  "Reply with the single word OK and nothing else."
```

Exit 0, stdout `OK`.

## 3. The five smoke conditions

1. **Exit 0 with a reply** — PASS (`OK`).
2. **Trace + meta written** — PASS, private paths:
   - `~/.local/state/ctxvm/traces/tb-wired-smoke-20261116.jsonl`
   - `~/.local/state/ctxvm/traces/tb-wired-smoke-20261116.meta.json`
   - (also `.coverage.json`, not part of the five conditions)
3. **Witness chain** — PASS for the fired domain:
   ```
   21:14:28.437Z init name=tb-wired-smoke-20261116
   21:14:28.916Z context session=ses_e19c9ea03ffepXUJYXV6FtmfGR
   21:14:31.575Z cleanup entered (plugin unload)
   21:14:31.576Z flush tb-wired-smoke-20261116.jsonl bytes=562 session=ses_e19c9ea03ffepXUJYXV6FtmfGR
   21:14:31.580Z cleanup finishAll -> 1 tracer(s)
   21:14:31.580Z cleanup exit
   ```
   `hookStats` in the sidecar: `contexts: 1`, `before: 0`, `after: 0`, `completed: 0`, `errored: 0`.
   So the flush chain is complete and `session.context` fired; the tool domain produced no event
   because the smoke made no tool call.
4. **v0.1 validator** — `python3 spec/rfc-0.1/validate_schema_v0_1.py <trace>` → exit 0,
   `OK: all checks passed`.
5. **Replay** — `./rust/target/release/replay <trace>` → exit 0, full JSON:
   ```json
   {
     "events": 3,
     "divergences": [],
     "violations": []
   }
   ```

## 4. Identity and metadata

`session.open` carries the real route: `agentId: tb-wired-smoke`,
`model: opencode-go/hy4-flash-free`, `provider: opencode-go`, `budgetTokens: 60000`,
`schemaVersion: "0.1"`, `environmentId` present, `ts` last.

`.meta.json` values: `harness: opencode-v2-promise-plugin`, `harnessVersion: v2.3.0`,
`pluginVersion: 0.0.1`, `model`/`provider` as above, `budgetTokens: 60000`, session id
`ses_e19c9ea03ffepXUJYXV6FtmfGR`. **`pluginVersion` and `harnessVersion` are populated, not null.**
The canonical sidecar has **no `opencodeVersion` key** — it was replaced by `harnessVersion` in the
canonicalisation (`packages/opencode/live/README.md`), so there is no null to report; if that key is
required, it is a separate adapter change and is not made here.

## 5. Call rate, cost, and ceiling (not frozen)

From the private sanitized export: one user, one assistant, one idle; **1 assistant message for 1
prompt**, 0 tool parts. `r_smoke = 1.000`. Session `info.cost` is **0** and tokens are input 3,039,
output 11, cache read 3,840, cache write 0 — **harness-reported, not a provider receipt**; no cost
or saving claim.

Ceiling arithmetic, stated but **not frozen in this card** (the full run needs its own
preregistration): the plan's authoritative rule is `ceil(193 × r_smoke)` plus a separately stated
P193 allowance, which gives `193 + allowance`. The unwired P193 allowance was 5 requests
(577 → 582), but applying it to a wired run is an assumption, not a wired measurement. The delta
card's `ceil(193 × r_smoke × 1.10) + 5 = 218` is a **proposal**, not the plan's rule. No integer is
frozen here; the owner's authorization for the full run must include a fresh preregistered ceiling,
and any overrun is recorded, never repaired afterwards.

## 6. Accepted deltas folded into this record (not executed)

- **D2 ledger keying:** key each full-run reply on its prompt's own `fixture/data-NN.csv`
  reference, never the turn index (lexicographic order: P100 asks for `data-181.csv`).
- **D3 auth detector:** match explicit forms only — `HTTP 401/429`, `insufficient_credits`,
  `FreeUsageLimitError`, `authentication_error`. Never bare digits (`401` once matched inside
  `8401`).
- **D1 full-run fidelity pass criteria (state now, run later):** ≥192 distinct page refs in
  `page.declare`; one `session.open` with real model/provider; populated `pluginVersion` and
  `harnessVersion` (with the `opencodeVersion` canonicalisation note above); `hooks-witness.log`
  showing **both** hook domains across the run; completeness scores re-derived from the same
  replies, unchanged or the difference explained.
- **D4 ceiling:** §5 above; proposal 218, plan rule `ceil(193 × r_smoke)` + stated P193 allowance.

## 7. Claim ceiling and privacy

PASS is a statement about v2.3.0 plugin loading and capture mechanics only. It does not witness
paging, H3/H4, eviction, `enginePlan`, any cost, or model-output determinism. Traces remain in the
private state dir (law 9); nothing from them was committed. The full 193-prompt run was not started.

## 8. Files and gates

- Repo: this card, one LOG row, one day-file section. No `packages/**`, `tools/**`, `spec/**`,
  `corpus/**`, `research/**` or `design/**` byte changed.
- `bash tools/check-handoff.sh` → ALL HANDOFF CHECKS PASS. Repo gate re-run unpiped with ambient
  `CTXVM*` cleared → `ALL GATES GREEN` (tracked files changed: this card, LOG, day file).
- Explicit staged paths via a private index; `git read-tree HEAD` afterwards;
  `bash tools/git-hygiene.sh` OK. Never pushed.

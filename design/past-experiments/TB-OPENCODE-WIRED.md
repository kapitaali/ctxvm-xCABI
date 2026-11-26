# TB-OPENCODE-WIRED — proposal: the wired OpenCode capture run for T-B

**Status:** **PROPOSAL / plan of record. Not authorized past the planning stop.** No model call, no
shim creation, no run, no spend. Author: opencode lane, 2026-11-16.

**Owner ruling, verbatim (2026-11-16):** "lets call it a breach. we were supposed to plan for the
wired experiment anyway"

The plan of record for what T-B measures stays `design/past-experiments/TB-PLAN.md` (rev 2). The harness plan for the
unwired run is `design/past-experiments/TB-OPENCODE-RUN.md` (AUTHORIZED, now complete as a CEILING/BREACH run). This
card fixes only **how the next, wired run would be configured and gated**.

## 1. Settled facts this plan does not re-litigate

- The unwired full run is **CEILING / BREACH**: 193 prompts, 192/192 file-exact, 1536/1536 tuple
  coverage on both denominators, artefact PASS canonical, lookups 3/3, but **582 requests against
  the frozen 579 ceiling** (`RR-TBOPEN2FULL-20261116`, verified in
  `RR-TBOPEN2FULL-REVIEW`, commit `6bc6357`). The owner calls it a breach.
- Do **not** raise 579 retroactively, do **not** re-score that run as a clean cell, and do **not**
  treat it as a GO for a Hermes paged cell. Its completeness numbers remain observations with the
  breach attached.
- The two harness defects in that run (auth regex matching `401` inside `8401`; lexicographic
  ledger mapping) are settled and disclosed. No re-run, no second session.

## 2. Wiring mechanics (no shortcuts)

The capture is enabled by a **project-local shim inside the run directory**, not by a config key:

```ts
// <run-dir>/.opencode/plugins/ctxvm.ts
export { default } from "/absolute/path/to/ctxvm/packages/opencode/live/ctxvm.ts";
```

- The adapter already exports the required default `{ id, setup }` module shape and registers the
  three hook domains (`session.context`, `tool.execute.before`, `tool.execute.after`) via
  `ctx.session.hook` / `ctx.tool.hook` (`packages/opencode/live/ctxvm.ts`).
- **No built `dist` is needed** — the shim loads the TypeScript adapter source directly. No
  `packages/node` or adapter build step is part of this plan.
- **No config-key shortcut**: adding a `plugin` entry to `~/.config/opencode/opencode.jsonc` is not
  the v2 loading surface documented by the adapter and is not used here. The current config has no
  such entry; that is why the unwired run produced no trace.
- There is no plugin hot-reload. A shim edit requires a new OpenCode process/boot. The shim is not
  created by this planning card; it is created in the authorized smoke step.

## 3. Environment for the wired run

Set these in the process that boots OpenCode for the run (adapter reads them at setup/flush):

| variable | value for the wired run | why |
|---|---|---|
| `CTXVM_TRACE_DIR` | the private state dir, e.g. `~/.local/state/ctxvm/traces` | adapter is inert without it; capture default-on and private (law 9) |
| `CTXVM_TRACE_NAME` | **fresh per run**, e.g. `tb-wired-<run-id>` | one name accumulates and each flush overwrites the same file |
| `CTXVM_MODEL` | `opencode-go/hy4-flash-free` | session.open model metadata; matches the authorized route |
| `CTXVM_PROVIDER` | `opencode-go` | session.open provider metadata |
| `CTXVM_AGENT_ID` | e.g. `tb-wired` | agent label in session.open |
| `CTXVM_BUDGET_TOKENS` | `200000` | the adapter's `headroom` field only — **not** an engine budget; no paging exists here |
| `CTXVM_OPENCODE_VERSION` | output of `opencode --version` (v2.3.0) | otherwise `.meta.json` carries null (m5 lesson) |

Unset the ambient Hermes capture variables (enumerate `CTXVM*` from `env` and unset) before any
gate or run, so a capture-shell leak cannot contaminate identity or `ts`.

## 4. Flush discipline

- The capture is written on **plugin unload / graceful shutdown only**. A hard kill (`SIGKILL`) loses
  the slice **silently** — no trace, no warning. End every process with a graceful signal.
- After the smoke and after the full run, check `$CTXVM_TRACE_DIR/hooks-witness.log` for
  `init → context → … → cleanup entered → flush → cleanup finishAll → cleanup exit`. A missing
  `cleanup` line means the flush did not happen; the run is NO RECORD.
- No hot-reload: the shim and env are read at boot. Never edit a shim in a live run dir and expect
  the running process to pick it up.
- One trace name per run; repeated flushes of the same name overwrite earlier bytes.

## 5. First gate — compatibility smoke (MODEL CALL, NOT AUTHORIZED HERE)

**v2.3.0 compatibility is UNVERIFIED.** The adapter's contract notes and prompt recipe document
v2.1.2 / v2.1.3; the installed CLI is v2.3.0 (`opencode --version`, measured 2026-11-16). The
shipped binary is bundled, so the v2 hook shape could not be confirmed from source inspection
(`RR-OPENWIRE-20261116` §3).

Before any full wired run, one short prompt in a fresh run dir with the shim and the §3 env must:

1. exit 0 with a reply;
2. write `<CTXVM_TRACE_NAME>.jsonl` **and** `<CTXVM_TRACE_NAME>.meta.json` under
   `CTXVM_TRACE_DIR`;
3. show a complete flush chain in `hooks-witness.log`;
4. pass `python3 spec/rfc-0.1/validate_schema_v0_1.py <trace>`;
5. pass `./rust/target/release/replay <trace>` (exit 0, no divergence).

If any of those fails, the wired run is blocked and v2.3.0 compatibility is recorded as FAILED.

**This smoke is a model call and is NOT authorized by this planning prompt.** It needs its own
explicit owner authorization (§9).

## 6. Run shape and ceiling (to be preregistered after the smoke)

- Same **192 × 150, seed 7** fixture (digest
  `36561425bf57ac156def80a7653ebceccb9a55b24f3c475f585370040156fbec`) and the **verbatim** design
  prompt from `design/past-experiments/TB-PLAN.md` §3, unless the owner rules otherwise. No reword, no new shape.
- One OpenCode session for all 193 prompts, tools available, graceful shutdown at the end.
- **New ceiling.** Do **not** reuse 579 (the breached unwired ceiling) or 451 (the earlier phase-1
  freeze), and do **not** derive the ceiling from the unwired 582. The rule to preregister is:
  `ceiling = ceil(193 × r_smoke)`, where `r_smoke` is the **model requests per prompt measured in
  the wired smoke**, plus a separately stated allowance for P193 (artefact write + three lookups)
  if the smoke does not itself exercise a reconciliation-shaped prompt. The resulting integer is
  frozen in a new prediction block **before** the full run; an overrun is recorded, never repaired
  by raising it afterwards.
- Reply ledger: `opencode session export <sid> --sanitize` for structure/cost, and a private
  unsanitized export for reply text (sanitize redacts it). Keep prompts, lookups, per-reply output
  and both exports together under one run bundle in the state dir.

## 7. Claim ceiling

Even wired, `@ctxvm/opencode` is **mirror-only**: no context engine, no budget enforcement, no
eviction, no `enginePlan`. The wired run can witness only **capture fidelity** — that 193 prompts
produce valid, replayable xCABI traces with correct field coverage. It cannot witness paging, H3,
H4, any eviction effect, a cost or saving, or model-output determinism. Page-table derivation
determinism, if ever claimed, must be scoped to the Rust replayer, never to model output.

## 8. Privacy and gates

- Traces stay in the private state dir (`${XDG_STATE_HOME:-~/.local/state}/ctxvm/traces`, law 9).
  No trace bytes, export, or credential is committed. The shim path in the card is absolute only
  because `export … from` requires it; no secret is involved.
- Planning-only handoff gates: `bash tools/check-handoff.sh` → ALL PASS. The repo gate is unchanged
  by a plan; no `run-ci.sh` claim is made here.
- No change to `packages/**`, `tools/**`, `spec/**`, `corpus/**`, `research/**`, `handoff/**` (except
  the day file), or `design/past-experiments/TB-PLAN.md`.

## 9. Authorization requested (STOP here)

This plan stops before any model call, shim creation, or run. To proceed, the owner must authorize
the **one-prompt wired compatibility smoke** described in §5 — the model call that proves whether
the v2.3.0 plugin surface still loads and flushes a valid xCABI trace. Only after that smoke passes,
and a fresh ceiling is preregistered from its measured call rate, may the full wired run be authorized.

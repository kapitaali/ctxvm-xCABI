# RR-DSHEVENT-20261116 — verified: the dsh adapter reads flattened fields while DSH emits envelopes

Review lane, verify-then-record. Subject: the dsh lane's `handoffs/10-blocked-items-analysis.md` (analysis only,
commit `83d06ff5` in the DSH checkout). I changed no source, made no commit in the DSH repo, and ran no pair.

## 1. Verdict

**The new finding is correct, and it is the mechanism behind the 3-event traces.** DSH emits
`SessionEvent = {type, seq, time, data, …}`; the adapter reads flattened fields. I re-derived both halves from
the repo and the live session bytes. The green unit suite is a false green for the live path: its mocks are
flattened. Plan A is the highest-value next task, but it touches `packages/deepseek/**` (dsh lane) and needs the
owner's clearance before execution. Plan B needs a separate owner decision; Plan C needs a credential and a
route decision; Plan D belongs to another lane.

## 2. Evidence, re-derived

| claim | how | result |
|---|---|---|
| `SessionEvent` envelope | `packages/core/session/src/types.ts:506-529` in the DSH checkout | `{ type, seq, time, data, ignorable? }`; `data: SessionEventMap[K]` |
| real event shape | `zstd -dc` on the six newest session logs, first `request/header` | all envelopes; e.g. `session-c77e19f7…` seq 12, `data.header.config = {provider:"opencode", model:"hy4-flash-free"}`. A newer `session-a47fde9a…` reads nvidia/mistral-large; the older 3-event trace's own session had a header too |
| adapter reads flattened fields | `packages/deepseek/src/event-map.ts` (`event.arguments`, `event.callId`, `event.message`, `event.header`), `src/tracer.ts:62-67` (`ev.header?.config`), `src/page-table.ts:53-62,124-135` (`FlatEvent`, `ev.message`, `ev.surfaceOp`) | **confirmed at every cited site** |
| tests use flattened mocks | `test/event-map.test.ts:31-43`, `test/page-table.test.ts:27-70` | **confirmed**: `{type:'tool/call', callId, name, arguments}`, `{type:'request/header', header:{…}}`, etc. They would still pass with the live path broken |
| skeleton consequence | `RR-DSHTRACE-20261116` §3 | exactly 3 events, `provider:"dsh"`, `model:"unknown"`, no `page.declare`; consistent with `ensureTracer` never seeing `data.header` |
| fold consequence | `RR-DSHPROJ-20261116` §3 | 915 projected events → **1 page**, consistent with every message-less flattened read yielding the same unknown page |
| Plan B link state | `packages/deepseek/package.json` in DSH and ctxvm; `readlink -f` | schemastery absent from `peerDependencies` in both; the untracked link exists only in the DSH checkout, not in ctxvm's tree |
| Plan C profile | `ls ~/.dsh/profiles/ctxvm-dsh-local/` | exists with `cordis.patch.yml`, `cordis.yml`, `node_modules`, `pnpm-lock.yaml`; its link target was reported to the DSH repo and is not re-verified here |
| Plan D lint | `scripts/import-hermes-credentials.ts:276,293` | the always-false `options.dryRun ? …` ternaries are present; file belongs to another lane |

## 3. What I did not re-verify

- The DSH emission sites at `packages/core/session/src/index.ts:897-906,980-984` — the type and live bytes are enough for the finding, and I did not trace the emitter.
- Whether a `*` peer resolves through `pnpm-workspace.yaml` overrides in a fresh install (the handoff itself marks this UNVERIFIED).
- The OpenCode `MissingSessionID` 400 on a bare headless prompt: recorded as the DSH lane's observation, not reproduced here.
- The exact 915-event session file: the count is on record in `RR-DSHPROJ-20261116` with its command; I confirmed the report, not the bytes.

## 4. Routing — owner decisions needed

| plan | ask | my recommendation |
|---|---|---|
| **A** | clearance for the dsh lane to unwrap `data` at every read site, update mocks to envelope shape, and assert real provider/model + `page.declare` in a live trace | **Clear it.** Measured root cause, contained to `packages/deepseek/**`, and it fixes a false-green suite. Require the live verification the handoff names (schema validator + replay, trace named with exits/date) |
| **B** | add schemastery to `peerDependencies` as `*` and `pnpm install` | Defer until A's verification, or clear together if one handoff is preferred. The `*` vs `workspace:~` reasoning is sound; outcome UNVERIFIED until installed |
| **C** | acceptance #4 on `ctxvm-dsh-local` | Do not run on a failed-turn trace without an explicit decision. The credential still needs exporting within the token's validity; a 400 session would make the diff meaningless as mirror evidence |
| **D** | two always-false ternaries in another lane's file | Route to that file's owner; do not let the dsh lane edit it |

No code change, no pair, no spend, no credential read. Kit state was green at the last re-run; this card changes no gate input.

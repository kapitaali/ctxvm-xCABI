# RR-OPENWIRE-20261116 — what wiring `@ctxvm/opencode` would take (read-only check)

The owner confirmed the current T-B run goes **without** the plugin and that a second, wired run is wanted. This
card records what I checked. **No wiring was performed, no repo file outside this card was changed, and no model
call was made.** The current run is unchanged and remains unwired.

## 1. Correction to my earlier claim

I twice said "opencode.jsonc has no `plugin` entry, so no trace". That is true of the config key but **misses the
actual v2 loading surface**. `packages/opencode/live/README.md` documents a project-local shim:

```ts
// <session-project>/.opencode/plugins/ctxvm.ts
export { default } from "/absolute/path/to/ctxvm/packages/opencode/live/ctxvm.ts";
```

I checked: no `ctxvm.ts` shim exists under `~/.config/opencode/`, `~/.opencode/`, or the phase-0 run directory.
`CTXVM_TRACE_DIR` **is** set in this shell (`~/.local/state/ctxvm/traces`), but without the shim and its env the
adapter never loads. So the conclusion for this run ("no plugin, no trace") holds; the reason I gave was
incomplete. Recorded here rather than silently edited.

## 2. What the wired run needs

| item | source | status |
|---|---|---|
| local plugin shim in the run's project dir | `packages/opencode/live/README.md` | must be created; none exists today |
| `export default { id, setup }` module shape | `packages/opencode/live/ctxvm.ts:208-210` | implemented in the adapter |
| three hook domains (`session.context`, `tool.execute.before/after`) | same file | implemented via `ctx.session.hook` / `ctx.tool.hook` |
| `CTXVM_TRACE_DIR` set | `live/ctxvm.ts:211,235` | set in shell; **adapter is inert without it** |
| `CTXVM_TRACE_NAME`, `CTXVM_MODEL`, `CTXVM_PROVIDER`, `CTXVM_AGENT_ID` | `live/ctxvm.ts:227,312-315` | must be set deliberately for the wired run |
| `CTXVM_OPENCODE_VERSION` | `live/ctxvm.ts:136` | set from `opencode --version`; otherwise `.meta.json` carries null (m5 lesson) |
| graceful shutdown to flush | `live/README.md` §"Flush semantics" | mandatory: a hard kill loses the slice silently; `hooks-witness.log` records attempts |
| one name per flush | same | `CTXVM_TRACE_NAME` overwrites on each flush — use a fresh name per run |
| no plugin hot-reload | same | shim edits need a new boot |

## 3. The compatibility unknown that matters most

The live adapter's contract notes and prompt recipe target **OpenCode v2.1.2 / v2.1.3**. The installed CLI is
**v2.3.0** (`opencode --version`, measured). I could not verify from the binary strings that v2.3.0 still accepts
the `export default { id, setup }` shape or the promise-hook domains — those strings are absent from the shipped
binary, which is bundled. Therefore: **v2.3.0 compatibility is UNVERIFIED**. Before a wired run, a tiny smoke
capture (one short prompt, fresh `CTXVM_TRACE_NAME`, then graceful exit) must prove that a trace and `.meta.json`
are actually written, and `hooks-witness.log` must be checked. That smoke is itself a model call and needs its
own authorization.

## 4. Scope of a wired run, stated before it happens

Even when wired, this adapter is **mirror-only**: it writes pages/renders/faults to a trace, but has no context
engine, no budget, no eviction, no `enginePlan`. A wired OpenCode run witnesses *capture fidelity* (do the 193
prompts produce valid, replayable xCABI traces?), not paging. Paging stays with the Hermes paged arm.

## 5. Verification commands for the wired run (not executed here)

```sh
# after creating the shim under the run project dir:
tools/verify-capture.sh <trace.jsonl>
python3 spec/rfc-0.1/validate_schema_v0_1.py <trace.jsonl>
./rust/target/release/replay <trace.jsonl>
cat "$CTXVM_TRACE_DIR/hooks-witness.log" | tail
```

Kit was green at the last re-run (`check-handoff.sh` ALL PASS; `git-hygiene.sh` OK); this card adds no gate claim.

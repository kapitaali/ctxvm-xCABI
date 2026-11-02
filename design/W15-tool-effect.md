# W15 implementation plan — tool side-effect classification

**Status:** planned, not started beyond a Rust draft.
**Owner of execution:** the W15 agent. This file is the plan of record; corrections from review are
folded in and marked **[review]**.
**Prompt reference:** `08.1-UPDATE-PROMPT.md` §5 W15. **RFC section:** `spec/rfc-0.1/RFC-0.1-xCABI.md`
§R7 (new). **Report to write:** `reports/RR-W15-<date>.md`.

## 1. The law this card must not break

1. **Registration-owned.** A tool's class is declared where the tool is registered (the harness's own
   catalog, or an adapter-local table when the harness exposes none). It is **never** inferred from
   model text, tool arguments, or result content.
2. **Name-only.** The class is a function of the tool *name* and nothing else. Two calls to one name
   have one class, even if one of them happened to be harmless.
3. **Fail-safe.** Any name outside the table is `MUTATING`. An unknown tool is assumed to have written
   something.
4. **No WAL, no safety claim.** This is an audit field. Nothing here makes replaying a mutating call
   safe, and no document may imply otherwise.

## 2. Review corrections (decided, do not re-litigate)

**[review] C1 — strict names, no alias table.** Classification matches the registered name exactly.
The Hermes fixtures use `"tool": "read"`, which is *not* a registered host name, so those pages
classify `MUTATING` — which is the correct fail-safe outcome, not a bug to patch with an alias map.
Do **not** rewrite `_mini_run`'s payloads: the tool ref and content hash derive from the tool name,
so renaming would churn unrelated assertions. Instead add a dedicated test that uses a real host name
(`read_file`) and asserts the *value* is `READ_ONLY`. Record in the report that a test asserting only
keys can pass while every page is MUTATING — that is the failure mode this correction exists to
prevent.

**[review] C2 — the table is the host's own bucket, and the field will be mostly MUTATING.** The
only verified host-side read bucket is `_READ_SEARCH_TOOLS = {"read_file", "search_files"}`
(`model_tools.py:615` in the installed Hermes; verified 2026-11-01). Ship exactly that as the Hermes
default. Do not pad it with plausible-looking names — an unverified entry is a claim about someone
else's tool. Consequence to state honestly in the report: against a ~20-tool catalog this makes the
class nearly constant, which is the same information-free reading as `waste 1.000`. Add a
**measurement step** (S13): from the first live capture, report the observed split
(`READ_ONLY`/`MUTATING` counts) so the degeneracy is a number, not an assumption.

**[review] C3 — the environment variable is an override, never the mechanism.** Default-on with zero
`CTXVM_*` is the property the plugin-defaults card established; `CTXVM_PROVIDER` was removed for
exactly this reason and must not come back through the side door. Therefore:
- Hermes: in-code default table (verified host bucket), `CTXVM_READONLY_TOOLS` **extends** it.
- OpenCode / ai-sdk: in-code table of that harness's own read tools, `CTXVM_READONLY_TOOLS`
  **extends** it. A session with no env var set must still emit real classes.
The OpenCode table (justify each entry in a comment, from that harness's documented tool list):
`read`, `glob`, `grep`, `list`, `webfetch`. Everything else — `bash`, `edit`, `write`, `task`,
`todowrite` — is `MUTATING`.

**[review] C4 — canonical signatures must be per-kind.** `page.declare` carries `toolEffect` only
when `kind == "tool_result"`. A run that declares a `kind: "file"` page therefore has two legitimate
key shapes, and a single-signature table cannot express both. Change the parity tests to assert:
`set(event) - {"toolEffect"}` equals the base signature, **and** `toolEffect` is present iff
`kind == "tool_result"`. Apply the same rule in the TS mirror test.

## 3. Steps

Each step ends with the command that proves it. Do not batch past a red step.

### S1 — Rust model (`rust/crates/ctxvm-codec/src/model.rs`)

Add the enum next to `PageKind`, SCREAMING_SNAKE_CASE so the wire strings are `READ_ONLY`/`MUTATING`:

```rust
/// W15 / RFC-0.1 §R7: side-effect class tagged at tool REGISTRATION by the adapter.
/// Never inferred from model text or result content. Unregistered names are Mutating.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ToolEffect { ReadOnly, Mutating }
```

`PageDeclare` gains `tool_effect: Option<ToolEffect>`, declared **after `latency_ms` and before
`ts`** — `ts` must serialize last, and the struct's declaration order decides the canonical bytes.

*Verify:* `cargo build -q -p ctxvm-codec` (construction sites will fail; S2 fixes them).

### S2 — Rust construction sites

Every `Event::PageDeclare { .. }` initializer needs the field. `rg -n "PageDeclare \{" rust/` and add
`tool_effect: None` where the fixture is not the W15 case.

*Verify:* `cargo test -q` — expect the existing 67 to pass with no behaviour change yet.

### S3 — Version and kind gates (`check_version` in `model.rs`)

Two independent rules, each with its own message:
- `toolEffect requires schemaVersion "0.1"`;
- `toolEffect requires kind tool_result` — the class belongs to a tool call, and files, summaries and
  image refs are not tool calls.

Write them as two passes over the events, not one nested match: the current draft re-matches
`Event::PageDeclare` inside its own loop, which compiles but reads as an accident.

*Verify:* the two new unit tests in S4.

### S4 — Codec tests (`jsonl.rs` `rfc01_tests`)

1. Roundtrip: a declare with `tool_effect: Some(Mutating)` survives `to_line`/`parse_line`, and the
   emitted bytes place `toolEffect` between `latencyMs` and `ts`.
2. Version gate: the same event under `schemaVersion: None` returns the version error.
3. Kind gate: `toolEffect` on `kind: File` returns the kind error.

*Verify:* `cargo test -q -p ctxvm-codec`.

### S5 — Field allowlist (`jsonl.rs`)

`("page.declare", &["page", "turn", "latencyMs", "toolEffect", "ts"])` — already in the draft;
confirm no other tag needs it.

*Verify:* covered by S4's roundtrip (a missing entry fails at parse time, not compile time).

### S6 — Conformance vector (`rust/crates/ctxvm-conformance/vectors/events-v0-1.jsonl`)

Insert `"toolEffect":"READ_ONLY"` into the declare row **between `latencyMs` and `ts`**; the row's
`kind` is already `tool_result`.

*Verify:* `cargo test -q -p ctxvm-conformance` — `v01_vector_roundtrips_byte_identical` is the byte
authority, so a wrong position fails there and nowhere else.

### S7 — Schema (`spec/rfc-0.1/x-cabi.schema-v0.1.json`)

- `$defs.toolEffect`: `{"type": "string", "enum": ["READ_ONLY", "MUTATING"], "description": "..."}`.
- Add `"toolEffect": {"$ref": "#/$defs/toolEffect"}` to the **page.declare** branch. That branch has
  `additionalProperties: false`, so the property is mandatory to accept a valid trace.

*Verify:* `python3 spec/rfc-0.1/validate_schema_v0_1.py` after S10.

### S8 — Python tracer (`packages/hermes/src/plugin.py`)

- `_tool_effect(value)` — strict parser: `None` → `None`; a member of the wire enum → itself;
  anything else → **raise**. A silently coerced class is worse than a failed capture.
- `_declare_page(ref, hash_val, kind, tokens, latency_ms, tool_effect)`; insert the key **before**
  `ts` (which `_push` appends last).
- Both call sites (`:257`, `:272`) pass the value; only the tool-result path can carry a class, so
  the non-tool path passes `None` and the kind gate stays satisfied by construction.
- Docstring: state that the class is supplied by the registering adapter and never derived here.

*Verify:* `python -m pytest packages/hermes -q` (S12 adds the new tests).

### S9 — Python adapter (`packages/hermes/live/__init__.py`)

```python
# W15 registration table. The only verified host-side read bucket is
# _READ_SEARCH_TOOLS (model_tools.py:615 in the install). Every other name is
# MUTATING — fail safe, not an oversight. CTXVM_READONLY_TOOLS extends the set;
# it is never required for classification to work.
_HERMES_READ_ONLY = frozenset({"read_file", "search_files"})
```

`classify_tool(name)` = `READ_ONLY` if `name` is in the table (defaults ∪ env extension) else
`MUTATING`. Call it in `on_post_tool_call` and pass `toolEffect` into `vm.page({...})`. `recall`
(`pre_tool_call`) carries no class: a fault row is not a tool result.

*Verify:* `python -m pytest packages/hermes -q`.

### S10 — Validator (`spec/rfc-0.1/validate_schema_v0_1.py`)

Three negatives plus one boundary case:
- `toolEffect` with a lowercase value (`"read_only"`) → schema reject;
- `toolEffect` on a `kind: "file"` declare → semantic reject (add the kind check to `validate_line`);
- `toolEffect` with a null value → schema reject (omitted, never null — R3 precedent);
- v0 boundary: a declare carrying `toolEffect` must be rejected by the **sealed v0** schema.

*Verify:* `python3 spec/rfc-0.1/validate_schema_v0_1.py` → `OK: all checks passed`.

### S11 — TS core + adapters

- `packages/node/src/tracer.ts`: export `type ToolEffect = "READ_ONLY" | "MUTATING"`;
  `PageInput.toolEffect?: ToolEffect`; thread it through `declarePage(...)` **before `ts`**; a runtime
  guard that throws on values outside the union (JS callers bypass the type system).
- `packages/opencode/src/plugin.ts`: in-code read table (`read`, `glob`, `grep`, `list`, `webfetch`),
  `CTXVM_READONLY_TOOLS` as extension; classify in `onToolExecuteAfter` by `payload.tool`.
- `packages/ai-sdk/src/tap.ts`: same table and extension at the existing `vm.page({ tool: str(p.toolName), ... })`
  call site (`tap.ts:110`).

*Verify:* `node --test` in `packages/node`, `packages/opencode`, `packages/ai-sdk`.

### S12 — Parity tests (C4 applied)

- `packages/hermes/test/test_plugin.py`: per-kind signature rule (base keys minus `toolEffect`, plus
  presence iff `kind == "tool_result"`); one new value test using `read_file` → `READ_ONLY` and
  `terminal` → `MUTATING`; keep a test that an unregistered spelling (`read`) is `MUTATING`.
- `packages/opencode/test/meta-parity.test.ts`: same rule for the opencode lane.

*Verify:* both suites; then `bash tools/run-ci.sh`.

### S13 — Regenerate the emitter artifacts, then measure

- `python packages/hermes/test/generate_traces.py` — **no `--force`**. `_write_fixture` refuses only
  `FROZEN_FIXTURES = {hermes-echo-synthetic.jsonl, hermes-thrash-synthetic.jsonl}`
  (`generate_traces.py:59-62`), so the live-echo fixture regenerates while the m3 drop sources stay
  byte-identical. `--force` would orphan `corpus/m3/checksums.sha256`.
- `cd packages/ai-sdk && npm run gen` (the echo tool is unregistered → `MUTATING`, deterministic; the
  generator's `CTXVM_TRACE_TS=0` re-set after the env wipe must stay).
- Goldens: **nothing to do** — `uc1-resume-golden.json` and `uc2-diagnose-golden.json` contain zero
  `page.declare` rows (checked 2026-11-01).
- **Measure the degeneracy:** from the first live capture after the wrapper sync, report the
  `READ_ONLY` : `MUTATING` split. If it is 0 : N, say so in the report and in `09-plugin-parity.md`.

### S14 — Docs, version, bookkeeping

- `spec/rfc-0.1/RFC-0.1-xCABI.md`: new §R7 after §R6 — the field, the three laws of §1 above, the
  kind constraint, and the explicit non-claim (no WAL, no replay safety).
- `09-plugin-parity.md`: §5.2 classification law with each adapter's table and env-extension rule;
  §2 canonical-key row (the parity test's failure message points readers there).
- `PLUGIN_VERSION` / `plugin.yaml` → **0.5.0** (wire shape changed), and copy the wrapper to
  `~/.hermes/plugins/ctxvm-tracer/` — without the sync nothing changes live.
- `tools/run-ci.sh` counts line; mirror any changed total into `.github/workflows/ci.yml`.
- `reports/RR-W15-<date>.md` + a `reports/LOG.md` row; the day index gets a section like every other
  card.

*Verify:* `bash tools/run-ci.sh` → `ALL GATES GREEN`; then re-run it once more after the doc edits,
because doc-only changes have broken the gate before.

## 4. Acceptance

1. `cargo test` green; the vector is byte-identical with `toolEffect` in position.
2. `pytest packages/hermes` green, including a **value** assertion: a registered read tool is
   `READ_ONLY`, an unregistered name is `MUTATING`.
3. Node/opencode/ai-sdk suites green; the parity tests use the per-kind rule.
4. The v0.1 validator rejects the four new bad shapes and still accepts the vector.
5. `bash tools/run-ci.sh` prints `ALL GATES GREEN` after both the code and the doc commits.
6. A live capture (after the gateway restart) carries `toolEffect` on tool-result pages, and the
   `READ_ONLY : MUTATING` split is reported as a number.

## 5. Not claimed

- No write-ahead log, no dry-run execution, no replay safety for mutating calls.
- The Hermes table covers two tools. It is a verified floor, not a taxonomy; most sessions will read
  `MUTATING` until the host publishes a broader bucket or an owner extends the table.
- Classification says what a tool *can* do, not what this call *did*.

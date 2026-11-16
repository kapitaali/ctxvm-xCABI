# RR-DSHPROJ-20261116 — DSH session resume crashed on a tool/result with no message

**Lane:** dsh adapter (owner cleared this one change on 2026-11-16; `packages/deepseek/**` is
normally dsh-lane-owned). **Date:** 2026-11-16. **Symptom source:** screenshot
`~/Pictures/Screenshots/error.png`, supplied by the owner after selecting a model in `dsh web`.

The error in the screenshot was:

```
Model operation failed: gateway/internal; resume failed for session "session-a47fde9a-…":
SessionQueryError: failed to project session "session-a47fde9a-…": The "data" argument must be
of type string or an instance of Buffer, TypedArray, or DataView. Received undefined
```

## 1. Root cause, verified before the fix

- The failing session is stored at
  `~/.dsh/sessions/--home-theb-Documents-deepseek-harness-default-workspace--/session-a47fde9a-de6b-43a9-8808-a166fb5d2111/session.v4.jsonl.zstd`.
  Its 915 events include **154 `tool/result` rows, all with `message` absent** (checked by
  decompressing the session and counting).
- `packages/deepseek/src/page-table.ts:129-131` called
  `textOfContent(ev.message?.content)`, and `textOfContent` ended with
  `return canonicalJson(content as never)` (`:71`). For `undefined`,
  `canonicalJson(undefined) === undefined`; `contentHash(undefined)` throws the exact TypeError
  quoted above. `approx4(undefined)` throws too.
- Reproduced locally against the shipped tracer:

```sh
node --input-type=module -e '
import { canonicalJson, contentHash } from "./packages/node/dist/index.js"
const t = canonicalJson(undefined)          // undefined
try { contentHash(t) } catch (e) { console.log(e.message) }'
# The "data" argument must be of type string or an instance of Buffer, TypedArray, or DataView. Received undefined
```

This is a projection bug in the W22 adapter, not a consequence of adding the OpenCode connection
to the web profile (documented in `RR-OCDSH-20261116` §10). No model route was changed by this
card.

## 2. Fix

`packages/deepseek/src/page-table.ts` — `textOfContent` now returns `''` whenever
`canonicalJson` does not produce a string, with a comment recording the 154-event cause. Absent
content stays a fact (empty body hash); it is never turned into a fabricated token count or a
zero that was not measured. The fold remains total, so session projection and resume complete.

`packages/deepseek/test/page-table.test.ts` — new regression test
`tool/result with no message does not throw (session resume regression)`: a `tool/call` followed
by a `tool/result` with **no `message`** must produce exactly one resident page whose
`contentHash` is `contentHash('')`. The test also pins the fail-safe identity: with no
`toolCallId` to pair, the page is keyed under the `unknown` tool name, not the preceding call's.

## 3. Verification

```sh
node --test packages/deepseek/test/     # 12 pass, 0 fail, 1 allowed skip (replay.test needs CTXVM_TEST_TRACE)
( for v in $(env | grep '^CTXVM' | cut -d= -f1); do unset "$v"; done; bash tools/run-ci.sh )
# ALL GATES GREEN
```

The real failing session was replayed through the **patched** projection, not just the unit test:

```sh
zstd -dc <the session above>.jsonl.zstd | \
  node --import tsx/esm --input-type=module -e '
    import { createInterface } from "node:readline"
    import { ctxvmPageTableProjection as p } from "<repo>/packages/deepseek/src/page-table.ts"
    let s = p.init({}, 0), n = 0
    for await (const line of createInterface({ input: process.stdin })) {
      if (!line.trim()) continue
      s = p.apply(s, JSON.parse(line)); n++
    }
    console.log("projected events", n, "pages", Object.keys(s.pages).length)'
# projected events 915 pages 1
```

Before the patch the same input threw on the first `tool/result` at seq 18. After it, all 915
events fold without error.

## 4. Scope and claim ceiling

- Changed: `packages/deepseek/src/page-table.ts`, `packages/deepseek/test/page-table.test.ts`,
  this card, and one LOG row.
- Not changed: DSH profile config, the OpenCode connection, the model route, any corpus or spec
  byte, `tools/run-ci.sh`.
- I did **not** start or resume a `dsh web` session after the patch, so this card does not claim
  the UI error is cleared end to end — only that the exact failing projection input is now folded
  successfully. The owner should retry resuming that session in the web UI.
- No cost or saving claim; no model-output or safety claim; no "deterministic" claim outside
  page-table derivation.

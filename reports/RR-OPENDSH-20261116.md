# RR-OPENDSH-20261116 — OpenCode models in DeepSeek Harness: the whole integration

**Lane:** opencode. **Date:** 2026-11-16. **Sample:** n = 1 machine, n = 1 session per live check.
**Spend:** no paid call was made; the model route used is the one the owner identified as the
OpenCode Go promotion. **Status:** working in headless and in the web UI, owner-confirmed.

This card consolidates a chain that previously produced three cards. Nothing here rewrites them;
it is the entry point for a reader who wants the whole story:

1. `RR-OCDIFF-20261113` — why we wanted OpenCode-side measurement at all (turn unit mismatch).
2. `RR-OCDSH-20261116` — first connection attempt, the wrong endpoint, the 429, and its addenda:
   §8 (default credential), §9 (the working Go route), §10 (web profile added).
3. `RR-DSHPROJ-20261116` — the session-resume crash found after model selection in the web UI,
   its root cause, and the adapter fix.

## 1. Question and result

**Question.** How do we make the models OpenCode can use available inside DeepSeek Harness (DSH,
`~/Apps/deepseek-harness`), including the web UI model picker, so the W22 capture adapter can be
developed against them?

**Result, in one sentence.** The `opencode` provider is an OpenAI-compatible endpoint, so a DSH
`pi-ai` connection is enough — but the working free route is the **OpenCode Go** endpoint with
`hy4-flash-free` and an `x-opencode-session` header; once that was configured, headless and web
UI both completed generations, and the one crash encountered on the way was a W22 projection bug
on `tool/result` events with no message, now fixed.

## 2. What was established, in order

### 2.1 The endpoint is not a plugin problem

OpenCode's own binary contains both routes:

```
https://opencode.ai/inference/openai/v1          # 50 models; returned 429 FreeUsageLimitError
https://opencode.ai/inference/go/openai/v1       # 21 models; works, including hy4-flash-free
```

So no change to `packages/opencode/**` or `packages/deepseek/**` was needed for model access: DSH
already has a `dsh connection` feature (`--route pi-ai`, `--api openai-completions`). The initial
connection (`opencode.ai/inference/openai/v1`, `deepseek-v4.1-flash-free`, 50 models) authenticated
and listed models but returned 429 on generation. The owner pointed to an OpenCode post stating
that Hy4 flash on OpenCode Go is promoted for two weeks and does not count against Go usage; that
identified the correct endpoint and model.

### 2.2 The Go route needs a session header

On the Go route:

- `GET /models` with either stored OpenCode credential → **200, 21 models**, including
  `hy4-flash-free`.
- `POST /chat/completions` without `x-opencode-session` → **400 `MissingSessionID`**.
- With `x-opencode-session: ses_<64 hex>` → **200**, reply `OK`; the response's own `opencode`
  metadata reported `billing_source: "go"` and `cost: 0`. Those are provider-reported fields
  quoted as facts, not a cost or saving claim.
- A fabricated session-like value works; no live OpenCode session id is required (n = 1).

### 2.3 Configuration in `~/.dsh` (not in the repo)

| Surface | State |
|---|---|
| `connections.yaml` | connection `opencode`, `baseURL: https://opencode.ai/inference/go/openai/v1`, `apiKeyEnv: OPENCODE_API_KEY`, route `pi-ai`, 21-model catalog, default model `hy4-flash-free`, context window 1048576 |
| `.credentials.yaml` | `OPENCODE_API_KEY` holds the `opencode-go` key (no expiry field in the auth export) |
| `profiles/opencode/` | headless profile (`dsh-base` + `dsh-headless`); provider header `x-opencode-session` under `providers.opencode`; default model `hy4-flash-free` |
| `profiles/web/` | existing web profile (`dsh-web-app` **and** `@ctxvm/dsh`); same connection merged alongside `openrouter`, `nvidia`, `nous`; same header added; previous default `nous / google/gemini-4-hydrogen` deliberately restored so existing UI behaviour is unchanged |

Launch forms:

```sh
pnpm dsh opencode "Reply with exactly: OK"     # headless profile
pnpm dsh web                                    # web UI; select opencode / hy4-flash-free
```

`dsh opencode` with no task errors with the headless runner's `a task is required` message; that
is proof the profile resolved, not a missing profile. All temporary credential exports used to
move keys between stores were deleted; no secret was printed or committed.

### 2.4 Live verification

Headless, with the credential ref exported into the launch environment (the headless bundle does
not read the interactive credential store):

```
pnpm dsh opencode "Reply with exactly: OK"
→ reasoning: The user asked me to reply with exactly: OK...
→ OK
→ exit 0
```

Web UI: the owner restarted `dsh web` and confirmed "it works". The supplied startup log (token
redacted here — it is a local web credential and must not be pasted into reports or commits)
showed:

```
[ctxvm] apply called, enabled = true traceDir = ${XDG_STATE_HOME:-~/.local/state}/ctxvm/traces
[ctxvm] effect running; registering page-table projection
[ctxvm] session/created session-830bc015-…
[ctxvm] session/created session-a47fde9a-…
[ctxvm] session/event #1 session- model/selection
[ctxvm] session/event #3 session- turn/start
[ctxvm] session/event #5 session- step/start
```

The second session id is the one that previously crashed on resume. Events flow without a
projection error, and model selection no longer produces the toast.

### 2.5 The crash on the way, and its fix

Selecting the model in the web UI first produced:

```
SessionQueryError: failed to project session "session-a47fde9a-…": The "data" argument must be
of type string or an instance of Buffer, TypedArray, or DataView. Received undefined
```

Cause, verified from the stored session: **154 `tool/result` events with `message` absent**. The
W22 projection passed that `undefined` through `canonicalJson` into `contentHash`, producing the
exact TypeError. Fixed in `packages/deepseek/src/page-table.ts` by making `textOfContent` return
the empty-body string when `canonicalJson` yields no string, plus a regression test in
`packages/deepseek/test/page-table.test.ts`. Verified by replaying the real 915-event session
through the patched projection (no throw, 1 page) and by the full gate. Full detail in
`RR-DSHPROJ-20261116`. Owner clearance for editing that lane's path was obtained before the edit.

## 3. Claim ceiling

**May be claimed.** The OpenCode Go catalog is reachable from DSH; the connection and both
profiles are configured; headless generation completed (n = 1); the owner reports the web UI works
and the supplied log shows the adapter active and events flowing; the projection crash is fixed
and its exact failing input now folds.

**May not be claimed.** No cost or saving claim; no claim that the promotion lasts beyond the
owner's stated two weeks; no model-output or safety claim; no "deterministic" outside page-table
derivation; no claim that a web-session trace was validated — the adapter flushes on session end
or unload, and no post-restart trace was validated in this card; no claim that the fabricated
session header is the right long-term value.

## 4. Verification commands used

```sh
# connection and composed config
dsh connection show opencode
dsh --profile web --dump-config | grep -A6 'opencode:'

# adapter tests (12 pass, 1 declared skip)
node --test packages/deepseek/test/

# the real failing session through the patched projection
zstd -dc <session>.jsonl.zstd | node --import tsx/esm --input-type=module -e '…'
# projected events 915 pages 1

# the gate, with the capture-shell environment cleared
( for v in $(env | grep '^CTXVM' | cut -d= -f1); do unset "$v"; done; bash tools/run-ci.sh )
# ALL GATES GREEN
```

## 5. Files and commit

- Repo: this card plus one LOG row. No corpus, spec, `tools/run-ci.sh`, or research byte changed.
- Earlier commits in this chain: `130ded9`, `e7407c1`, `067d430`, `db34cc9` (cards and LOG rows),
  and `6609521` (adapter fix + test + card + LOG row).
- DSH home config changed as listed in §2.3; the DSH fork's source was not edited.

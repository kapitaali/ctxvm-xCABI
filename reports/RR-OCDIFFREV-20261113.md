# RR-OCDIFFREV-20261113 — review of `RR-OCDIFF-20261113` (`78b3382`) and its companion analysis

Card: review-lane assessment of the OpenCode vs Hermes turn-accounting run (`reports/RR-OCDIFF-20261113.md`,
commit `78b3382`) and the four follow-up points proposed in the companion analysis.

---

## 1. What `RR-OCDIFF-20261113` and `<analysis>` get right

1. **The controlled measurement and invalidation rule are sound**:
   - On the same six-file read task with `longcat-2.5` (free tier), Hermes recorded **6 `turn.render`
     rows for 12 model requests** (`perApiRequest`), while OpenCode recorded **13 `turn.render` rows
     for 13 model requests**.
   - That directly measures rule **N3** of `design/diff-normalisation.md` (§3): a Hermes turn is a
     **user turn** (~2.0–2.1 model requests bucketed into one `turn.render`), while an OpenCode turn is
     a **model request** (1 request per `turn.render`).
   - All existing W8/W8C ratios survive because they are within-Hermes or denominated in sessions/requests;
     any cross-harness metric with `turn.render` in the denominator is invalid without N3 alignment.
2. **The `corpus/m7` premise correction is verified**:
   - `corpus/m7/provenance.json` (`harness.name: "Hermes Agent"`) and `corpus/m7/README.md` confirm `m7`
     is Hermes; the OpenCode corpus drops are `m2`, `m5`, and `m6`, and `m8` is AI-SDK.
3. **No re-run is needed**: Path A respected the $0.00 ceiling, used a clean `env -u` environment, and
   answered the question with controlled captures.

---

## 2. Four sharper technical points from reading `RR-OCDIFF-20261113` and `packages/opencode/`

### A. Qualification 1 (`2.17 vs 2.0` requests/prompt) is even cleaner than it looks
- `<analysis>` rightly flags that OpenCode exposed `shell` (`wc -l`) while Hermes used `toolsets: [file]`,
  so `13 vs 12` requests (`2.17 vs 2.0` requests/prompt) and `12 vs 6` tool calls (`2.0 vs 1.0` tool
  calls/prompt) are confounded by tool surface.
- In fact, `RR-OCDIFF-20261113` §1.4 shows that on **prompts 2–6**, OpenCode's `longcat-2.5` batched
  `read` + `shell` as parallel tool calls inside a **single** request, making **exactly 2.0
  requests/prompt** (the same as Hermes). The entire `13 vs 12` difference (`2.17 vs 2.0`) is **one
  extra request on prompt 1**, where `read` and `shell` ran sequentially before the answer. Naming that
  in the table prevents `2.17` or `2.0 tool calls/prompt` from being quoted as a harness property.

### B. Qualification 2 (`providerUsage` = `0/13` on OpenCode vs `6/6` on Hermes) exposes an RFC-0.1 R3 gap on **both** adapters
- **Why OpenCode is `0/13` and `0/18`**:
  - `@ctxvm/node`'s `Tracer` already supports `noteUsage()` (used by `@ctxvm/ai-sdk` to emit
    `call.meta.providerUsage`).
  - However, `@ctxvm/opencode` (`packages/opencode/src/plugin.ts:117-124` and
    `packages/opencode/live/ctxvm.ts:515-538`) hooks only `session.context` (which fires **before** the
    model request is sent) and `tool.execute.before/after`, and never calls `noteUsage()`.
  - Yet as `RR-OCDIFF-20261113` §1.3 and §1.4 demonstrate, OpenCode's session message stream
    (`GET /api/session/$SID/message`) **does** record per-assistant-message token receipts (`input`,
    `output`, `reasoning`, `cache.read`, `cache.write`) — so previous turns' assistant messages or
    flush-time message inspection could populate `noteUsage()` in a future adapter card.
- **Why Hermes's `6/6` is also incomplete in the trace JSONL**:
  - As `RR-OCDIFF-20261113` §2.2 notes, Hermes emits `6/6` `call.meta.providerUsage` rows, **but each
    row is last-write-wins for that user turn** — so the first model request of every 2-request user
    turn (~50% of requests) is overwritten and absent from `call.meta.providerUsage` in the `.jsonl`
    trace (living only in the sidecar/DB).
  - **Consequence**: Today, **neither** OpenCode's trace JSONL (`0/13` receipts) **nor** Hermes's trace
    JSONL (`6/12` requests represented due to turn-level overwrite) carries a complete per-request
    `providerUsage` series in `call.meta` alone (`@ctxvm/ai-sdk` is the only adapter where `call.meta`
    is both 1-per-request and `providerUsage`-populated).

### C. A fourth cross-harness divergence inside `RR-OCDIFF-20261113`: `identifier_scan` fault asymmetry (`12` violations vs `0`)
- In `RR-OCDIFF-20261113`, the same 6-file read task produced **12 `faultOfResidentPage` violations**
  on OpenCode (§1.3/§1.4) and **0 faults** on Hermes (§2.2).
- Cause: Hermes plugin `0.12.0` (`README.md:115`) stopped emitting `page.fault` from `identifier_scan`
  (moving prose mentions to sidecar telemetry), whereas `@ctxvm/opencode`
  (`packages/opencode/src/plugin.ts:122`, `vm.scan(...)`) still emits v0 `identifier_scan` faults on
  every `onSessionContext` call.
- That is a fourth concrete cross-harness difference alongside (1) `turn.render` unit (`N3`), (2) tool
  name + path + envelope hash (`N1` / `OP-N2`), and (3) `providerUsage` emission.

### D. On `README.md:114–116`
- `README.md:116` currently cites `design/, corpus/m7 vs m8` for *"A Hermes 'turn' is a user turn; an
  OpenCode/AI-SDK turn is a model request."* Because `m7` is Hermes and `m8` is AI-SDK, the citation is
  valid for the AI-SDK half of that sentence but omits OpenCode (`m2/m5/m6`) and now has a direct
  same-task live measurement (`reports/RR-OCDIFF-20261113.md`).
- Likewise, `README.md:114` should note that live `call.meta.providerUsage` is emitted by Hermes (last
  request per user turn) and AI-SDK, and is `0/N` on `@ctxvm/opencode` until `noteUsage` intake is wired.

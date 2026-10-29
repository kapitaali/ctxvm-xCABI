# Hermes hook surface — official-docs verification, cost audit, and the `turn.render` gap

**Card:** W4 of `08.1-UPDATE-PROMPT.md` (adoption push).
**Date:** 2026-10-29.
**Scope of this note:** what the Hermes observer contract actually gives a trace
collector, what it does not, and what it costs. **No plugin code changes in this
card** — the audit produced four findings that need the hermes lane; they are
written up as `reports/W4B-PROPOSAL-20261029.md`.

**Method (two independent sources, as the prompt's W4 requires):**

1. **Official docs** — `developer-guide/observer-hooks`
   (<https://hermes-agent.nousresearch.com/docs/developer-guide/observer-hooks>,
   "Read-only telemetry contract for plugins"; fetched 2026-10-29) and
   `developer-guide/plugins`
   (<https://hermes-agent.nousresearch.com/docs/developer-guide/plugins>).
2. **Installed source** — Hermes Agent `v0.22.5`, local checkout
   `/home/theb/.hermes/hermes-agent` at `bf0203a794` (the same build the m7
   capture ran: `corpus/m7/provenance.json` → `harness.version`).

`HOOKS.md` in this directory is the Phase-0 source pin from T17. It remains
correct; this note cross-checks it against the published contract and records
where the two differ in emphasis.

---

## 1. Contract facts confirmed by the docs

| Fact | Doc statement (locator: observer-hooks) | Verdict vs `HOOKS.md` |
|---|---|---|
| Observer hooks are read-only | "the read-only telemetry contract for plugins that need to reconstruct agent execution without changing runtime behavior" | matches |
| Fail-open | "Hook callbacks are fail-open. Hermes catches callback exceptions, logs a warning, and keeps the agent loop running." | matches (note: `pre_tool_call` is the fail-CLOSED exception — blocking is its documented power) |
| `**kwargs` | "Plugins should accept `**kwargs` so additive fields remain backward-compatible" | matches |
| Payload version stamp | "The plugin manager injects this field into every hook payload: `telemetry_schema_version = "hermes.observer.v1"`" | **not consumed by the plugin** (finding F4) |
| `post_tool_call.status` vocabulary | `ok` \| `error` \| `blocked` \| `cancelled`; "emitted for blocked and cancelled paths so telemetry plugins can close spans cleanly" | matches the T17.1 errata (`ok`, not `completed`); the plugin correctly declares no page for all three non-`ok` values |
| `pre_llm_call` timing | "Before the tool loop begins for a **user turn**" + "Use request-scoped API hooks for LLM span telemetry" | **contradicts the plugin's turn model** (finding F2) |
| Sanitized request/response | `pre_api_request.request`, `post_api_request.response` are "the canonical observer inputs for new consumers" | not consumed (finding F3) |
| Provider usage | `post_api_request` includes `usage` | **not consumed** — `providerReported` is hardcoded `false` (finding F3) |
| Legacy context field | "Legacy compatibility fields such as `request_messages`, `conversation_history` … may still be present" | the plugin depends on `conversation_history` (finding F1 makes it load-bearing) |
| Cost gating | "Expensive request/response payload construction is gated behind `has_hook(...)`" | plugin registers only `on_session_start`, `pre_tool_call`, `post_tool_call`, `pre_llm_call`, `on_session_end` — no API-payload hooks, so it pays none of that cost |
| Author duty | "Keep hook callbacks fast and fail-open. Offload network export or batch writes when practical." | audited in §3: no network, no I/O inside hooks |

---

## 2. What the hooks can and cannot observe

### Can observe

| xCABI event | Hook | Fields actually used |
|---|---|---|
| `session.open` | `on_session_start` | `session_id`; model/provider/budget/tokenizer from `CTXVM_*` env (not from the hook) |
| `page.fault(tool_recall)` | `pre_tool_call` | `tool_name`, `args` (matched against declared pages) |
| `page.declare` | `post_tool_call` where `status == "ok"` | `tool_name`, `args`, `result`, `duration_ms` (available, unused) |
| `page.fault(identifier_scan)` | `pre_llm_call` | `conversation_history` text |
| `turn.render` / `call.meta` | `pre_llm_call` | turn counter; `latencyMs`-style fields are absent from the payload |

### Cannot observe — the `turn.render` gap

The prompt names this the hardest part ("Capturing what the model actually saw
(`turn.render`)… Document exactly what the hooks can and cannot observe"). The
honest statement, with locators:

1. **The system prompt is never passed to a hook.** `on_session_start` fires
   "after the system prompt is built" (observer-hooks, Session Lifecycle) and
   carries only `session_id`. No hook exposes the composed system prompt, the
   tool schemas, or the provider's cache-control breakpoints. `turn.render`'s
   `residentTokens` therefore counts *declared pages*, never the prompt.
2. **`conversation_history` is not the request.** `agent/context_engine.py:124`
   — `select_context()` "Runs on every provider request (also retries)… The
   host runs it before prompt cache-control and every request sanitizer", and
   "unlike `pre_llm_call` it may replace the list". A context-engine plugin can
   swap the context after our scan and before the request. Hermes' own
   `prune_tool_results_only()` (same file) trims old tool payloads on a separate
   trigger. The tracer's view is pre-prune, pre-select.
3. **Other plugins can change the bytes after us.** `pre_llm_call` may return
   `{"context": ...}`, which the host appends to the current user message
   (`agent/turn_context.py:799` `_collect_pre_llm_call_context`).
   `transform_tool_result` "May return a replacement tool result string after
   `post_tool_call`" (observer-hooks, Contract table; `model_tools.py:849`).
   So a page body hashed at `post_tool_call` is the *pre-transform* body.
4. **Nothing reports the provider's cache state.** `post_api_request.usage`
   gives input/output tokens (and `response_model`, `finish_reason`), not the
   cached-read/write split. `call.meta`'s `cacheEstimate` stays an estimate even
   when usage is wired (F3).
5. **Turn identity is user-turn identity.** See F2.

**Consequence for the standard.** `turn.render` in a Hermes trace is a
*derived mirror of the page table at the turn boundary*, not a record of the
provider request. That is the same claim RFC-0 already makes for the other two
emitters, but in Hermes the gap is wider (the two other harnesses intercept the
request itself: `packages/opencode/live/ctxvm.ts` the context hook,
`packages/ai-sdk/src/middleware.ts` `transformParams`). Any cross-harness
`ctxvm diff` of render rows compares a request-level mirror against a
turn-level one — see F2 before quoting such a diff (W5).

---

## 3. Cheap-hooks audit (measured, not asserted)

Rule under test (prompt §W4): "Hooks must be cheap. Append JSONL only. No
network calls or heavy computation inside hooks; analysis happens offline."

| Check | Method | Result |
|---|---|---|
| Network inside hooks | `grep -nE 'requests\|urllib\|httpx\|socket\|http' packages/hermes/src/plugin.py packages/hermes/live/__init__.py` | no network-capable import; the only 2 hits are `content_str.startswith("http")` string tests (`src/plugin.py:175,327`) |
| I/O inside hooks | flush path only (`_flush_traces` at `on_session_end`/`on_unload`/`atexit`) | events accumulate in memory; one write per session |
| Bounded-hook budget | `hermes_cli/plugins_dispatch.py:41-48` lists `pre_llm_call`, `post_tool_call`, `pre_tool_call` as timeout-bounded; default `plugins.hook_callback_timeout = 30`s (`hermes_cli/config_defaults.py:1733`) | our worst measured callback is 3 orders of magnitude under |
| `post_tool_call` cost | one `page()` = canonical-JSON of args + SHA-256 of the body + a dict insert | sub-ms at m7 sizes (34 declares) |
| `pre_llm_call` cost | `_transcript_texts` (string join) + `scan` = O(pages × identity-tokens × history length) substring search | **5.86 ms** for 34 pages / 222 identity tokens / 80 000-char history (best of 5; measured 2026-10-29, this machine, real m7 refs) |
| Scaling | linear in pages and history; ~1000 pages would be ~170 ms per turn | acceptable for v0, worth a note if a capture ever exceeds a few hundred pages |

The one caveat: `scan` is the only super-linear-looking cost in the plugin and
it currently runs against an **empty string** on every live Hermes session
(F1) — i.e. the measured cost is what the fix will add, not what it costs
today.

---

## 4. Findings (each needs a code change → `reports/W4B-PROPOSAL-20261029.md`)

**F1 — `identifier_scan` is dead on live Hermes payloads (defect).**
`CtxvmPlugin._transcript_texts` (`src/plugin.py:425-437`) treats
`message["content"]` as a list of `{type, text}` blocks:
`for part in zone: if isinstance(part, dict) and part.get("text")`. Real Hermes
messages carry `content` as a **plain string** —
`agent/conversation_loop.py:350` (`append_message(messages, {"role": "assistant", "content": visible})`)
and `agent/oneshot.py:103` (`{"role": "user", "content": user_input or ""}`).
Iterating a string yields characters, no dict is found, and the function
returns `""`. Every fixture in `test/generate_traces.py` and
`test/test_plugin.py` uses the *block* shape, so the suite pins a shape Hermes
never sends from the assistant role.

Evidence, measured on the committed corpus:

```
$ python3 -c "import sys; sys.path.insert(0,'packages/hermes/src'); \
  from plugin import CtxvmPlugin as P; \
  print(repr(P._transcript_texts([{'role':'assistant','content':'read src/plugin.py'}])))"
''
```

and the fault census over every drop:

```
m3 (synthetic, block shape)  hermes-echo   identifier_scan 2
m4 (LIVE)                    hermes        identifier_scan 0   (1 tool_recall)
m7 (LIVE, both sessions)     hermes        identifier_scan 0
```

Consequence: **every live Hermes trace under-reports faults to zero on the
inference surface.** m7's `faults: 0` is a capture artifact, not model
behaviour. This is also why W1's hermes rows read `id-touched share 0` /
`waste 1.0` — a vacuous bound, not a measurement.

**F2 — turn granularity differs from the other two emitters (spec-level drift).**
The docs define `pre_llm_call` as "Before the tool loop begins for a user turn"
and explicitly route LLM span telemetry to `pre_api_request`/`post_api_request`.
The plugin uses `pre_llm_call` as the turn boundary, so one Hermes "turn" is one
*user* turn, while `@ctxvm/opencode` and `@ctxvm/ai-sdk` emit one `turn.render`
per model request. Corpus witness: m7-a = 5 `turn.render` for 29 hook fires
(`contexts 5 + before 12 + after 12`, sidecar `hookStats`);
m8 = 10 turns for one scripted task. A `ctxvm diff` between a hermes trace and
an opencode trace of the same task will report turn-tally mismatches that are
**unit mismatches, not behaviour** — W5 must classify them as such before
quoting any divergence.

**F3 — provider-reported usage is available and unused.**
`post_api_request` carries `usage`, and `pre_api_request` carries
`approx_input_tokens`, `request_char_count`, `message_count`, `tool_count`
(observer-hooks, Request-Scoped API Hooks). The plugin hardcodes
`call.meta.cacheEstimate.providerReported = false` (`src/plugin.py:307`) and
registers neither hook. W1 measured `providerReported 0/32` call.metas. The W2b
gap is therefore **closable in Hermes with hooks that already exist** — no
schema change, no new event type.

**F4 — the observer contract version is not recorded.**
Every payload carries `telemetry_schema_version = "hermes.observer.v1"`; the
sidecar canon has no slot for it. Recording it would let a future reader tell
which contract a trace was captured under (the `09-plugin-parity.md` sidecar
canon would need one additive key — an owner decision, not taken here).

---

## 5. What this card deliberately did not do

- No edit to `packages/hermes/src/plugin.py`, `live/__init__.py`, or the
  fixtures: the hermes lane is held by another workstream (the standing
  `node/hermes do-not-touch` note on the W2 card). F1/F3 are a **proposal**,
  not a landed fix.
- No corpus re-capture: a corrected capture needs the fixed plugin plus an
  owner-driven live session. m7's provenance now carries the erratum so the
  drop cannot be read as "Hermes sessions have no faults".

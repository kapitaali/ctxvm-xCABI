# W4b PROPOSAL — Hermes capture-surface fixes (approval requested, nothing landed)

**Follows:** `reports/RR-W4-20261029.md` (W4 audit) ·
`packages/hermes/OBSERVABILITY.md` (evidence) ·
**Lane:** `packages/hermes/**` is held by the hermes workstream (standing
`node/hermes do-not-touch` note on the W2 card). This card therefore proposes,
it does not land.

**Decision requested (one question):** approve B1+B2 as one hermes-lane commit;
route B3+B4 to W7 (RFC-0.1) instead of treating them as adapter bugs.

---

## 1. The defect in one line

`CtxvmPlugin._transcript_texts` (`packages/hermes/src/plugin.py:425-437`)
parses `message["content"]` as a list of `{type, text}` blocks; live Hermes
messages carry it as a **plain string**, so the function returns `""` on every
real turn and `identifier_scan` **cannot fire on any live Hermes capture**.

Evidence (all reproducible, see RR §2):

```
m3 hermes synthetic (block shape)   identifier_scan 2
m4 hermes LIVE                      identifier_scan 0   (1 tool_recall)
m7 hermes LIVE (both sessions)      identifier_scan 0
```

Source of the live shape (Hermes v0.22.5 @ `bf0203a794`):

- `agent/conversation_loop.py:350` —
  `append_message(messages, {"role": "assistant", "content": visible})`
- `agent/oneshot.py:103` —
  `messages.append({"role": "user", "content": user_input or ""})`
- `agent/turn_context.py:816` — `conversation_history=list(messages)` (what the hook receives)

Every fixture in `test/generate_traces.py` and `test/test_plugin.py` uses
`content: [{"type": "text", "text": …}]`, so the suite has only ever exercised
a shape Hermes does not send from the assistant role. That is why a green suite
and a dead surface coexisted for four drops.

**Honesty impact.** m7's `faults: 0`, and the W1 dogfood rows for m7
(`id-touched share 0`, `waste 1.0`), are capture artifacts. `waste = 1 - share`
with `share = 0` is not an upper bound on Hermes waste, it is no measurement at
all. The m7 provenance now carries the erratum (checksum re-baselined); the W1
report should be read with it.

---

## 2. B1 — the fix (hermes lane, ~12 lines + 3 tests)

```python
    @staticmethod
    def _transcript_texts(messages: List[Dict[str, Any]]) -> str:
        """All text entering the compose window this turn.

        Shapes seen in the wild (Hermes v0.22.5): ``content`` as a plain string
        (conversation_loop.py:350, oneshot.py:103), as a list of content blocks
        (multimodal / OpenCode-style), and ``parts`` (OpenCode recordings).
        """
        parts: List[str] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            zone = message.get("parts") or message.get("content")
            if isinstance(zone, str):
                parts.append(zone)                      # ← the live shape
            elif isinstance(zone, list):
                for part in zone:
                    if isinstance(part, dict) and part.get("text"):
                        parts.append(part["text"])
                    elif isinstance(part, str):
                        parts.append(part)
            elif message.get("text"):
                parts.append(message["text"])
        return "\n".join(parts)
```

Behaviour notes:

- The block shape keeps working unchanged, so every existing test and every
  committed fixture stays green **without modification** (no fixture rewrite —
  the point is that the old shape was never wrong, only insufficient).
- No other module changes: `scan()` already receives `{"text": ...}` and is
  correct; the identity-token extraction is correct.
- Cost: this is the branch that *activates* the measured 5.86 ms/turn scan
  (34 pages, 222 identity tokens, 80 000-char history) — three orders of
  magnitude under the 30 s hook budget.

### Tests to add (`packages/hermes/test/test_plugin.py`)

1. `test_live_shape_string_content_scan_fires` — history
   `[{"role": "assistant", "content": "I read notes/alpha.md"}]` after a
   `read_file {"path": "notes/alpha.md"}` declare → exactly 1
   `page.fault(source="identifier_scan")`. **Red before the fix, green after** —
   this is the regression pin the suite never had.
2. `test_live_shape_multimodal_parts_still_scan` — `content:
   [{"type": "text", "text": "…notes/alpha.md…"}]` still fires (guards the old
   path).
3. `test_transcript_texts_shape_matrix` — unit-level: str / block-list /
   `parts` / plain-string fallback `/` non-dict element, asserting the joined
   text, so the next shape change in Hermes fails one obvious test.

Acceptance: hermes suite 51 → 54 green; `tools/run-ci.sh` ALL GATES GREEN;
one commit.

---

## 3. B2 — kill the synthetic drift (same commit)

`test/generate_traces.py` builds the committed `corpus/m3` fixtures with the
block shape only. Add a third synthetic session — or convert one — to the live
string shape so the generator can never again produce a drop that hides this
class of defect.

Acceptance: generator re-run reproduces its committed fixtures byte-identically
for the two existing sessions; the new session's trace validates against the
schema and is either added to m3's checksums or kept as a `packages/hermes/
fixtures/` artifact (keeps the corpus drop frozen — preferred).

---

## 4. B3 — provider-reported usage is a SPEC question, not an adapter bug (route to W7)

The audit found that `post_api_request` already carries `usage`
(observer-hooks, Request-Scoped API Hooks) and `pre_api_request` carries
`approx_input_tokens` / `request_char_count`. Writing them into the trace is
**blocked by RFC-0, not by the adapter**:

```
call.meta: additionalProperties: false, properties:
  type, turn, provider, cacheEstimate{estHitTokens, estMissTokens,providerReported}, latencyMs
```

There is no field for provider usage, and `providerReported: true` without the
actual numbers would be a lie. So W2b-in-Hermes requires an RFC-0.1 addition
(e.g. `call.meta.providerUsage {inputTokens, outputTokens}` or
`cacheEstimate.source: "provider"`), which is **D4-gated** and already the
subject of the W7 card.

Proposal: W7's RFC-0.1 draft gains this as a third motivating friction (today it
names umpire's two); the Hermes adapter stays on `providerReported: false` until
the spec moves. No hermes-lane commit for B3.

---

## 5. B4 — contract-version provenance (route to W7 / 09 canon)

Every observer payload carries `telemetry_schema_version =
"hermes.observer.v1"`; the sidecar canon (`09-plugin-parity.md` §3) has no slot
for it. Recording it is additive and cheap, but it changes the canon both
emitters are tested against, and the opencode plugin has no equivalent field to
record — i.e. it is a cross-harness canon decision, not a hermes fix. Route to
W7's packaging beat or a dedicated 09-canon card. Priority: low.

---

## 6. Not proposed (explicitly out of scope)

- **F2 (turn granularity).** `pre_llm_call` is per *user* turn per the docs;
  the other two emitters render per *model request*. Making Hermes match would
  change turn identity (a 10-step tool loop becomes 10 turns), which changes
  every committed hermes trace and the `ctxvm diff` contract. Not a fix —
  W5 must classify unit mismatches, and the limitation is documented in
  `OBSERVABILITY.md` §2 and (as a capture-surface note) in the drop records.
- **Re-capturing m7.** A corrected capture needs the fixed plugin plus an owner
  live session; the erratum makes the existing drop honest meanwhile.
- **Any `packages/hermes/**` edit in this card.** Lane law.

---

## 7. Risk register

| Risk | Mitigation |
|---|---|
| The fix makes hermes traces emit faults where none were recorded → cross-drop discontinuity | Disclosed in the commit message and the board row; m7 keeps its erratum; no committed trace is rewritten |
| A `content` list of `{type:"image"}` blocks inflates the scan text with markers | `zone` list branch only appends `part["text"]` / `str` parts — markers are not synthesized |
| Scan cost grows with pages × history | Measured 5.86 ms at 34 pages / 80 k chars; a future cap is a v-next item, not a blocker |
| Someone reads the fixed adapter as "Hermes sessions have faults now" | `identifier_scan` is an INFERENCE surface, never ground truth (W3 law); the hard-fault gate is untouched |

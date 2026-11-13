# RR-W8CREPLAY-20261112 — verification of the replay of `local-d60a50c4…` (81 events, 0 divergences, 3× same hash, turn-12 projection with 0 stubs): the numbers hold, and the "independently derived" claim needs one qualifier

Card: review-lane re-run of the replay/determinism/export checks on the capture the W8C closing card rests
on (`w8b-20261113-150420-paged`).

---

## 1. Every number in the report re-runs exactly

Trace: `~/.local/state/ctxvm/traces/local-d60a50c44acffa297f6d202b351e23696d35b5f22dd897160125ce2ad9b6c742.jsonl`
(20,721 bytes ✓, 81 lines ✓).

```
./rust/target/release/replay <trace>
{ "events": 81, "divergences": [], "violations": [] }      exit 0

three consecutive replays → sha256 of stdout: fe27e29c813c4e06, fe27e29c813c4e06, fe27e29c813c4e06
```

`./rust/target/release/export <trace> --turn 12 --output <dir>` ⇒ `page-table-12.json`:

```
turn 12 | slots 21 | tally {residentTokens 86,569, stubbedTokens 0, stubbedSlots 0, residentSlots 21}
slot 0  | mode "full" | pinned false | tool:read_file({"path":"fixture/part-01.txt"}) | 4,469 tokens
mode counts: {"full": 21}   stubbed: 0
```

⇒ **All confirmed** ✓ — the replay, the determinism hash, the projection, the zero stubs, and the
slot-0 identity ✓✓.

## 2. One qualifier on "independently derived"

The claim that the Rust replay derives the eviction *mechanism* "without our plugin's help" is **true for
the page table** and **needs a qualifier for the eviction count**:

- The **page table** (21 slots, 86,569 resident tokens, 0 stubbed) is derived by `ctxvm-core` from the
  trace's `page.declare` rows alone ✓ — the plugin contributes only the rows, not the derivation ✓✓.
- The **eviction count** (`turn.render.evictedTokens`) is a **plugin-written field** ✓ — the engine
  reports it to the observer ✓ (`context_engine.py` → `_tr.note_evicted(...)` ✓), and the Rust replay
  **reads** it ✓ (it does not re-derive it ✓). So "independently derived" is exact for the table and
  **not** for the eviction count ✓.

⇒ That is not a defect ✓ — it is the documented design ✓ (`RR-W8CEVICTREPORT`: the engine drops rather
than stubs ✓, so there is no `page.evict` row for the core to re-derive from ✓). But the sentence *"now
both are independently derived rather than reported by the same code that acted"* overstates the second
half ✓: **86,569 is independently derived ✓; 4,396 is reported by the code that acted and merely
carried through the replay ✓.**

## 3. The two-number mechanism sentence is right, and the arithmetic closes

```
table holds            86,569 tokens   (21 declared pages: 20 fixture reads + one 70-token page)
the 9 pages the policy removed   38,764 tokens   (part-02 … part-10, sidecar `evictedPages`)
sum of declared − evicted       47,805 tokens
request at turn 12   63,379 (prefix.approxInputTokens) — i.e. 47,805 of page tokens + ~15,574 of
                     scaffold (system prompt + assistant carriers + tool-call envelopes)
```

⇒ The two numbers are consistent with each other ✓ and the gap is **not** only eviction ✓: the request
also carries the non-page scaffold ✓ (system prompt ≈ 17.4 kB ✓), so *"the table holds 86,569 and the
request carries ~58,000"* is **not** a like-for-like comparison ✓ — the request's page content is
47,805 ✓ and the rest is scaffold ✓. The mechanism sentence is right in substance ✓ and the numbers are
each right ✓, but they are two different quantities ✓ (page-table residency vs request size ✓).

⇒ One more check that strengthens it: the trace's own `turn.render` lines carry `residentTokens 86,569`
on **every** turn ✓ (turn 0 through 19 ✓) — the page table's residency is constant ✓ because the policy
**removes pages from the request but does not evict them from the table** ✓✓ — which is precisely why
the "page.evict vs. removal" distinction is visible only in the render line ✓.

## 4. Executed agent-doings

- The capture was located, re-read, and re-run through `replay` (×4) and `export --turn 12` ✓.
- The stdout hash was recomputed three times ✓ and compared with the reported `fe27e29c813c4e06` ✓.
- The exported `page-table-12.json` was parsed independently for slot count, mode counts, stub counts,
  residency tally, and slot 0's identity ✓.
- The trace's 81 events were tallied by type ✓ (`session.open` 1, `page.declare` 21, `page.render` 19,
  `turn.render` 20, `call.meta` 20 ✓) and the per-turn `residentTokens` / `evictedTokens` series read ✓.
- The plugin's eviction-reporting path was read ✓ to establish which number is derived and which is
  carried ✓.
- No file of the other lane's edited ✓; nothing pushed ✓.

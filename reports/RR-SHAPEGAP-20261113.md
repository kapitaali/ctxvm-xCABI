# RR-SHAPEGAP-20261113 — the reviewer's four points, verified one by one, with two corrections and one decisive measurement: the derived page table says **21 pages, 86,569 tokens, all full** while the request carried **12 pages (47,805 tokens)** — the gap is real, and the **provider's own receipts** confirm the model saw the smaller request

Card: review-lane verification of the reviewer's comments on the W8C replay cards, with the decisive
measurement the reviewer's falsifier asks for, executed on the **paid** cell-03 capture (the only one with
provider receipts).

---

## 1. The reviewer's four points, verified

### 1.1 "0 stubs is a tautology" — **AGREE, and stronger than the reviewer says**

`packages/hermes/live/context_engine.py` has **no stub concept at all** (grep for `stub` in the engine:
one hit, and it is a comment about the host ABC) ✓; the hermes adapter **never emits `page.evict`**
(the only `page.evict` strings under `packages/hermes/` are a **trace reader** ✓ —
`packages/hermes/src/uc2_forensics.py:255,257` ✓ — and a **comment** ✓ at
`packages/hermes/live/__init__.py:832` ✓; **no `PageEvict` is ever constructed** ✓).

And in the core, a slot becomes stubbed **only** through a `PageEvict` (`rust/crates/ctxvm-core/src/page_table.rs:108-115` ✓ — `mode_at` returns `Full` unless a scheduled change says `Stub` ✓). With **0 `page.evict` rows in the capture** ✓, `stubbedSlots = 0` is **entailed by the event vocabulary** ✓ — it cannot be evidence about the request ✓✓.

⇒ So **"0 stubs" is not a witness**, and the closing card's "independent confirmation that this policy
removes pages rather than substituting stubs" is **overstated** ✓ — the real witness for removal is
(a) the **engine source** ✓ (no stub path exists ✓, already recorded in
`reports/RR-W8CEVICT-20261111.md` §1 ✓), (b) the **`turn.render.evictedTokens` counter** ✓ (a
plugin-written field ✓), and (c) the **request-size series** ✓ — none of which is the projection ✓.

### 1.2 "The replay agreement is partly by construction" — **AGREE, with the scope stated exactly**

The plugin pins the wire field to the whole-table tally by design ✓
(`packages/hermes/src/plugin.py:229` ✓: *"the trace's `residentTokens` is pinned to ctxvm-core's
whole-table `tally_at`, and a per-turn value there makes replay exit 1"* ✓), and the core's
`tally_at(turn)` sums **every page's** tokens ✓ with mode `Full` ✓ ⇒ the recorded and inferred residency
are the **same number by construction** ✓.

⇒ The residency half of "0 divergences" is therefore **not independent** ✓. But it is **not vacuous**
either ✓ — the check has teeth, proven by mutation ✓ (both mutations re-run through
`./rust/target/release/replay` ✓):

```
mutate one turn.render residentTokens (7 → 99999)   → {"residentTokensMismatch":{"turn":7,"inferred":86569,"recorded":99999}}   exit 1
mutate three page.render modes (full → stub)         → 3× {"renderModeMismatch":{...,"inferred":"full","recorded":"stub"}}    exit 1
```

⇒ **Correct framing**: the replay agreement is a **determinism + internal-consistency** witness ✓ (and
the "same hash three times" is a real determinism result ✓ — scoped to page-table derivation ✓, which is
exactly the claim the README allows ✓, law 8 ✓). It is **not** evidence about the treatment ✓✓.

### 1.3 "The 'request plateau implies removal' inference is weak" — **AGREE**

The plateau cannot separate removal from substitution ✓: a stubbing policy would also hold the request
near the budget ✓ (the stub text is small but present ✓). The decisive witness for removal is the
**engine's decision log and code** ✓, not the plateau ✓ — as the reviewer says ✓.

### 1.4 The representation gap — **CONFIRMED, and it is larger than the reviewer states**

The reviewer says the table claims 21 pages / 86,569 tokens while the request carried 47,805. Two
corrections to the numbers, and one thing that makes the gap **worse**, not better:

**Which capture each number comes from** ✓ (the reviewer's finding 5 ✓ — the card did not label them ✓):

| quantity | reviewer | measured | capture |
|---|---|---|---|
| pages the table claims | 21 | 21 ✓ | free 0.13.21 ✓ |
| tokens the table claims | 86,569 | 86,569 ✓ | free 0.13.21 ✓ |
| pages the request actually carried at turn 19 | 12 | **12** ✓ (21 declared − 9 removed ✓) | free 0.13.21 ✓ |
| page tokens the request carried at turn 19 | 47,805 | **47,805** ✓ (86,569 − 38,764 ✓) | free 0.13.21 ✓ |
| unique removed content behind the 9 | 38,764 | **38,764** ✓ (the sidecar's 9 pages × their declared tokens ✓) | free 0.13.21 ✓ |
| the provider-receipt ratios (0.563 etc.) | — | see the falsifier block below ✓ | **paid cell-03** ✓ (the only capture with receipts ✓) |

⇒ The paid capture's own `evictedTokens` sum is **275,362** ✓ (not 210,856 ✓ — that is the free
capture's ✓), and its 0.13.1 sidecar carries **no `evictedPages`** ✓ ⇒ its unique-removed content is
**not directly measurable** ✓ ⇒ the 12 pages / 47,805 tokens are the free capture's ✓ and the falsifier
below is the paid capture's ✓ — **different captures, different roles** ✓.

**The correction that makes it worse**: the reviewer compares turn 19's request with a table derived at
turn 12. But the projection is **turn-invariant on this capture** ✓ — `export --turn 0/5/12/19` all give
21 slots / 86,569 tokens / 0 stubbed ✓✓ — and the reason is the **flush-tail layout** ✓, not the pinning
alone ✓: in this capture every `page.declare`/`page.render` row sits **before** the `turn.render` block
✓ (1-based rows: the 40 page rows **2–41** ✓, the 20 `turn.render` rows **42–61** ✓, the 20 `call.meta`
rows **62–81** ✓ — 81 rows total ✓, the replay's 81 events ✓), so `handoff_prefix`'s **positional** cut
at turn N
(`rust/crates/ctxvm-core/src/export.rs:48-54` ✓) already contains **all 21 declares** ✓ — including the
**8 pages declared at turns 13–19** ✓ (the `page.declare` rows carry their own R5 `turn` field ✓ — the
trace's own `turn` values are 0…19 ✓).

⇒ **So at turn 0 the projection already claims 21 pages (21 exist only at turn 19)** ✓✓ — and the table
is not merely "true about the table, false about the request" ✓, it is **not even turn-scoped** ✓✓.

**The decisive measurement — the reviewer's own falsifier, run on the paid capture** ✓ (cell-03 paged vs
control ✓, `providerUsage.cachedInputTokens + inputTokens` ✓ from the trace's own `call.meta` ✓):

```
turn | paged provider tokens | control provider tokens | p/c | trace approx p/c
 10  |      104,516         |       104,556             | 1.000 | 1.003
 11  |       23,904         |       113,445             | 0.211 | 0.930
 12  |       14,507         |       122,483             | 0.118 | 0.868
 19  |      114,766         |       203,845             | 0.563 | 0.570
```

⇒ The **provider's own receipts** say the paged request at turn 19 carried **56.3%** of the control's
tokens ✓✓ — **not** 100% ✓ ⇒ the model **did not** see all 21 pages ✓ ⇒ the reviewer's falsifier
("if the request's page content matched 86,569 rather than 47,805, the removal measurement is wrong")
**does not fire** ✓✓ — the removal measurement is right ✓, and the **derived table is the thing that is
false** ✓✓.

⇒ **The gap is a real representation gap** ✓✓, with three parts ✓:
1. **Omission is unrepresentable in v0** ✓ — `page.evict` **requires** `stubText` ✓
   (`spec/rfc-0/x-cabi.schema-v0.json` ✓), and the RFC's own rule is *"the stub MUST be the `stubText`
   recorded in `page.evict` — renderers never invent or rewrite stub text"* ✓
   (`spec/rfc-0/RFC-0-xCABI.md:106-108` ✓) ⇒ a removal policy has **no verb** ✓✓ (already established in
   `reports/RR-W8CEVICT-20261111.md` ✓, but that card framed it as an instrument-honesty decision for
   **this** adapter ✓ — the reviewer's point is that it is a **standard-level** gap ✓✓).
2. **The count lives in a field v0 does not check** ✓ — `turn.render.evictedTokens` is *"recorded but
   unchecked in v0 (stub tokens need a tokenizer; OPEN T-OVICT)"* ✓
   (`spec/rfc-0/RFC-0-xCABI.md:156-157` ✓) ⇒ a consumer that only replays ✓ never learns that anything
   left ✓✓.
3. **The derived table is not turn-scoped on a flush-tail trace** ✓ (the positional cut ✓) ⇒ even a
   consumer that wants "what did the model see at turn N" gets **all 21 pages** ✓✓.

⇒ And the corpus has **no contrast case** ✓✓: the **only** `page.evict` rows in `corpus/` are the **4
synthetic** ones in `m1/session-thrashing.jsonl` ✓ — which is the one trace where the projection **does**
show stubs ✓ (measured: turn 2 → `stubbedSlots 1`, `stubbedTokens 400` ✓) ⇒ the machinery works ✓, the
**real** captures simply never exercise it ✓✓.

---

## 2. What this means for the paper's "did vs saw" claim — and the correction it needs

`research/white-paper-Part-II.md:28` defines **Render** as *"The message array the harness sent for a
turn: full content for resident pages, stub text for evicted pages"* ✓, and §2.1 claims *"A trace adds the
page table state and the rendered message array for each turn"* ✓; `:61-62` rests the whole "did vs saw"
distinction on **"the pages were stubbed or undeclared"** ✓✓.

⇒ For a **removal** policy, the trace records **neither** ✓: the removed pages are neither stubbed ✓ nor
undeclared ✓ — they are **declared and rendered full** ✓, and then **silently absent from the request** ✓✓.
⇒ So Part II's dichotomy has **no third branch** for this policy class ✓, and the reviewer's "Part II needs
a limitation line" is **correct** ✓✓.

⇒ **The precise limitation line the evidence supports** (for the white-paper lane, who own
`research/**` ✓ — this lane does not edit it ✓):

> Under a **removal** policy (a page is dropped from the request rather than replaced by a stub), the
> trace records the page as declared and rendered full, and records the **count** of removed tokens in
> `turn.render.evictedTokens`; RFC-0 v0 has no verb for omission (`page.evict` requires `stubText`), the
> evicted-token count is **unchecked in v0** (OPEN T-OVICT), and a flush-tail trace's derived page table
> is **not turn-scoped**. A consumer therefore cannot re-derive *which* pages a given request omitted
> from the trace alone; the per-page detail is a sidecar fact ✓.

---

## 3. The reviewer's four recommendations, reviewed

1. **"Stop citing '0 stubs' and 'independently derived' as mechanism evidence"** ✓ — **agree and already
   applied** ✓: `reports/RR-W8CREPLAY-20261112.md` §2 (:38) qualifies the eviction count as
   plugin-written ✓, and this card supersedes the closing card's "independent confirmation" wording ✓.
   **What should replace it**: the **provider receipts** ✓ (ratio 0.563 ✓) and the **request-size series**
   ✓ — independent of the page table ✓✓.
2. **"Document the field's meaning"** ✓ — **agree**, and the right place is **narrower** than a new
   document ✓: `packages/hermes/src/plugin.py`'s own comment already says it ✓ (`:229` ✓), but **no
   consumer-facing surface states it** ✓ — `README.md`'s limitations table and the RFC-0 text ✓ do not ✓.
   ⇒ A one-line addition to the RFC-0.1 **normative** text would need the five-touchpoint law ✓ (owner
   gate ✓); a **sidecar/doc** statement is free ✓.
   ⇒ **DONE (2026-11-13)** ✓: the README's *Measured limitations* table now carries the row ✓ —
   *"`residentTokens` is table residency, not request residency"* ✓ (21 pages / 86,569 tokens claimed ✓
   against 12 pages / 47,805 carried ✓; RFC-0 v0 has no omission verb ✓; `evictedTokens` unchecked in v0
   ✓; the derived table not turn-scoped ✓) — with the evidence pointers to this card ✓ and
   `reports/RR-W8DERRATUM-20261113.md` ✓. The **RFC-0.1 normative** statement stays owner-gated ✓.
3. **"Open a proposal-only design card on representing omission"** ✓ — **agree in substance, with a
   correction on the option set** ✓:
   - The reviewer's own framing is right that `page.evict`-with-empty-stub *"asserts a substitution that
     never happened"* ✓✓ — that is exactly the lane's existing rule ✓ ("a missing event is a gap; a wrong
     event is a falsehood" ✓, `RR-W8CEVICT-20261111.md` §3 ✓).
   - The three options (additive RFC-0.1 verb/field ✓ · sidecar-only convention ✓ · leave it
     unrepresented with a stated limit ✓) are the right menu ✓.
   - **The reviewer's own tie-break ("monitor views and evaluator harnesses are exactly the second
     consumer") is stronger than they think** ✓✓: §12 of Part I already proposes **monitor views as a
     first-class object derived from a trace** ✓ (`research/white-paper/white-paper.md:549` ✓: *"a view is
     therefore a first-class object, and ctxvm can define it as a pure function of a trace: rendered pages
     only, resident pages plus stubs…"* ✓) ⇒ **the second consumer already exists in the paper's own
     design** ✓✓ ⇒ the omission gap is not hypothetical ✓, and the "leave it unrepresented" option
     contradicts a claim the same paper makes ✓✓.
   - **One thing the reviewer's option list omits** ✓: the **already-documented** alternative shape —
     `turn.render.evictedTokens` **is** the omission counter ✓ and is **required** in v0 ✓; what it lacks is
     (a) a check ✓, (b) a per-turn *page identity* list ✓, and (c) a **turn-scoped** derived table ✓.
     A card that proposes *"count + identity, checked"* is cheaper than a new verb ✓ and keeps v0 sealed ✓✓.
4. **"Add the checker rule: if any turn has `evictedTokens > 0`, the sidecar must list the dropped pages
   and their sum must be consistent with it"** ✓ — **agree, and it is implementable today** ✓: the sidecar
   already carries `evictedPages` ✓, `evictedPagesCount` ✓ and per-call `callSizes` (before/after/dropped) ✓;
   `tools/coverage_check.py` is the gate ✓. Measured on the **0.13.21** capture ✓ (`local-d60a50c4…` ✓ — the sidecar's own
   `plugin.version` ✓): the sidecar's 9 evicted
   pages total **38,764** tracer tokens ✓ against the trace's cumulative `evictedTokens` **210,856** ✓
   ⇒ **the two are NOT directly comparable** ✓ (the trace counter is a per-turn cumulative re-drop sum ✓✓
   — see §4 ✓), so the rule must be stated as: *the sidecar's per-call `before − after` must equal the
   engine's per-call removed tokens* ✓ (measured: 8,735 / 12,941 / … ✓), **not** as a sum against the
   trace's cumulative counter ✓✓.

---

## 4. One measurement the reviewer's review did not make, and it changes how `evictedTokens` must be read

The trace's `turn.render.evictedTokens` is **not** "tokens removed this turn" ✓ — it is the engine's
**cumulative** removed-set size **attributed to the turn** ✓✓, and the free capture's per-turn
mapping shows it exactly ✓:

```
turn | trace evictedTokens | Σ over that turn's calls of (before − after) | per-call dropped counts
 12  |          0           |            4,411                        | [0, 1]
 13  |      4,396           |           13,146                        | [1, 2]
 14  |     13,101           |           21,676                        | [2, 3]
 ...
 19  |     55,914           |          112,638                        | [8, 9, 9]
```

**Repro (the exact filter matters ✓ — the log is append-only and shared ✓, and the plugin's own pytest
suite writes into it ✓, so a window that returns 41–44 lines mis-pairs the table ✓):**

```python
import json, glob, os, re
from collections import defaultdict
cov = sorted(glob.glob(os.path.expanduser(
    '~/.local/state/ctxvm/traces/local-d60a50c44acf*.coverage.json')))[0]
d = json.load(open(cov)); pa = d['perApiRequest']            # 41 entries, one per API call
log = open(os.path.expanduser(
    '~/.local/state/ctxvm/traces/_selections.log')).read().splitlines()
run = [l for l in log
       if 'budget=60000' in l and '2026-11-13T15:04:45' <= l[:19] <= '2026-11-13T15:13:00']
assert len(run) == len(pa) == 41          # the window must yield exactly 41 lines
sel = [tuple(int(re.search(rf'{k}=(\d+)', l).group(1)) for k in ('before', 'after', 'dropped'))
       for l in run]
turns = defaultdict(list)
for r in pa: turns[r['turn']].append(r)
k = 0
for t in sorted(turns):
    seg = sel[k:k + len(turns[t])]; k += len(turns[t])
    print(t, sum(b - a for b, a, _ in seg), [d for _, _, d in seg])
```

⇒ The trace's series (4,396 → 55,914 ✓) is the **cumulative removed-set size**, lagging the turn by
one ✓✓, and the capture's **session sum (210,856)** is **5.44× the unique removed content (38,764)**
✓✓ — the books already flag this (*"210,856 tokens evicted is easy to misread" ✓*, `RR-SPEND-20261112.md` §3 ✓),
and the W8D preregistration's own arithmetic (§9 ✓) multiplies the write volume by **36 rewrite events**
✓ — while the *dropped-set* count reaches only **9** ✓✓. ⇒ **"36 rewrite events" in
`design/W8D-PREREG-STABLE-20261113.md` §9 is not supported by any capture** ✓: the measured numbers are
**9 distinct pages ever removed** ✓ and **16 selections that dropped something** ✓ (the free capture's
`_selections.log` ✓), and the trace's per-turn counter **over-counts by construction** ✓✓.

⇒ **Consequence for the W8D refusal** (`3d91fb9` ✓, which recommended **not** spending ✓): the
**direction survives** ✓ — hold-once reduces the number of *prefix invalidations* ✓, and the paid price of
each is measured ✓ ⇒ the refusal stands ✓✓. But **two of its numbers need correcting before it is quoted**
✓:
- "rewrite events, today 36" ✓ → the measured **dropping selections are 16** ✓ and the **distinct pages
  removed are 9** ✓;
- "billed writes, today 1,408,011 tokens → 39,111 per rewrite" ✓ → the **billed** writes are 1,254,207
  for the pair ✓ (paged 1,025,825 ✓ + control 228,382 ✓) and the per-event write volume must be
  re-derived from **9** events ✓, not 36 ✓.

⇒ **The cheapest way to settle the whole question is zero-spend and already in hand** ✓: the **0.13.21
capture** carries per-call `before`/`after` ✓ (`callSizes` ✓, 16 entries ✓) and the **paid** capture
carries the billed write volume ✓ ⇒ the hold-once write volume can be **replayed** from the capture ✓
without a run ✓✓ — the same replay the preregistration's own step 1 asks for ✓.

---

## 5. Executed agent-doings

- The reviewer's four points were **checked against the code and the captures** ✓ (not the quotes ✓):
  the engine's stub-absence ✓, the adapter's `page.evict`-absence ✓, the core's `mode_at` ✓, the
  residency pinning ✓, the flush-tail layout ✓, the positional cut ✓.
- **Two mutation experiments** through `./rust/target/release/replay` ✓ proved the divergence checks have
  teeth ✓ (`residentTokensMismatch` ✓, `renderModeMismatch` ✓) — the reviews' "partly by construction" ✓
  is about **scope** ✓, not vacuity ✓.
- **The reviewer's falsifier was executed** ✓ on the paid cell-03 capture ✓ (the only capture with
  provider receipts ✓) ⇒ the provider's ratio **0.563** ✓ matches the trace's request ratio **0.570** ✓
  ⇒ the removal measurement is right ✓ and the derived table is the false part ✓✓.
- The **projection was measured at turns 0/5/12/15/19** ✓ (turn-invariant ✓, 21 slots ✓, 86,569 ✓) and
  the **flush-tail event positions** were read ✓ (page rows 1–40 ✓, turn facts 41–60 ✓, metas 61–80 ✓).
- The **corpus `page.evict` census** was re-run ✓ (4 rows ✓, all synthetic ✓) and the one synthetic
  thrashing trace was projected ✓ (it **does** show stubs ✓: turn 2 → `stubbedSlots 1` ✓).
- The **per-turn `evictedTokens` semantics** were mapped against the per-call `before − after` ✓ (the
  counter is a **lagging cumulative** ✓, and the session sum is **5.44×** the unique removed content ✓).
- **No file of another lane's was edited** ✓ (`research/**` read-only ✓, `packages/hermes/**` and
  `tools/**` untouched ✓); nothing pushed ✓.

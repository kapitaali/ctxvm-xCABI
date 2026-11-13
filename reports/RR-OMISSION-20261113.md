# RR-OMISSION-20261113 — proposal-only: how should a trace represent a page **omitted** from the request? (the reviewer's item 3, closed as a proposal; item 4 — the checker's state — measured)

Card: the reviewer's open item 3 (*"Open a proposal-only design card on representing omission"*) and item 4
(*"Add the checker rule the lane already wants"*) ✓. This is the **proposal** ✓ — it edits no spec ✓, no
adapter ✓, no `design/` file ✓ (the owner clears new ones ✓), and no `research/**` ✓.

---

## 0. Why the decision is now, not later

The reviewer's own tie-break was *"monitor views and evaluator harnesses are exactly the second consumer, so
I'd want it decided before Part II's view claims are cited"* ✓. That tie-break is **stronger than they put
it** ✓: the second consumer **already exists in the paper's own design** ✓ — Part I §12 makes a view *"a
first-class object, and ctxvm can define it as a pure function of a trace: rendered pages only, resident
pages plus stubs…"* ✓ (`research/white-paper/white-paper.md:549` ✓) ⇒ **the "leave it unrepresented" option
contradicts a claim the same paper makes** ✓✓ ⇒ the decision cannot be deferred past Part II's view claims
without an inconsistency ✓.

⇒ The recommendation below is therefore a **shape**, not a field: *"count + identity, checked"* ✓ (§4 ✓) —
cheaper than a new verb ✓, it keeps **v0 sealed** ✓, and it is the shape both the paper's monitor view ✓ and
the checker's rule need ✓.

---

## 1. The measured problem (all numbers reproduced)

| fact | value | locator |
|---|---|---|
| the derived page table claims | 21 pages / 86,569 tokens | `export --turn 0/5/12/19` on the 0.13.21 capture ✓ (turn-invariant ✓) |
| the request actually carried | 12 pages / 47,805 tokens | 86,569 − 38,764 ✓ (the sidecar's 9 removed pages ✓ × their declared tokens ✓) |
| RFC-0 v0's omission verb | **none** | `page.evict` **requires** `stubText` ✓ (`spec/rfc-0/x-cabi.schema-v0.json` ✓); the RFC's rule is *"the stub MUST be the `stubText` recorded in `page.evict`"* ✓ (`spec/rfc-0/RFC-0-xCABI.md:106-108` ✓) |
| the count that exists | `turn.render.evictedTokens` ✓ | *"recorded but unchecked in v0 (stub tokens need a tokenizer; OPEN T-OVICT)"* ✓ (`RFC-0-xCABI.md:156-157` ✓) |
| what the count actually is | a **lagging cumulative** of the removed set | 4,396 → 55,914 over turns 13–19 ✓; session sum **210,856** = **5.44×** the unique removed content 38,764 ✓ (`reports/RR-SHAPEGAP-20261113.md` §4 ✓) |
| the derived table's scoping | **not turn-scoped** ✓ | `handoff_prefix`'s cut is **positional** ✓ (`rust/crates/ctxvm-core/src/export.rs:48-54` ✓) and the flush tail puts every declare before the turn block ✓ ⇒ at turn 0 the table already claims 21 pages ✓ |
| contrast case in the corpus | **none** ✓ | the only 4 `page.evict` rows in `corpus/` are the **synthetic** ones in `m1/session-thrashing.jsonl` ✓ — the one trace whose projection *does* show stubs ✓ (turn 2 → `stubbedSlots 1` ✓) |

⇒ **What a trace-only reader cannot do today** ✓: say *which* pages a given request omitted ✓, and say
*how many* it omitted for that turn (the counter is cumulative and unchecked ✓) ✓.

---

## 2. What is **not** proposed

**`page.evict` with an empty stub** ✗ — it would assert a substitution that never happened ✓ (the lane's
existing rule: *a missing event is a gap; a wrong event is a falsehood* ✓, `reports/RR-W8CEVICT-20261111.md`
§3 ✓). Sealed v0 stays byte-frozen ✓ (law 1 ✓) and the RFC-0.1 route is additive and version-gated ✓
(law 2 ✓).

---

## 3. The three options, with what each buys

| option | what it costs | what it buys | what it breaks |
|---|---|---|---|
| **(a) an additive RFC-0.1 verb or field** | the **five touchpoints** ✓ (Rust model **declared before `ts`** ✓ · the codec's `FIELD_ALLOWLIST` ✓ · the v0.1 schema branch with `additionalProperties: false` ✓ · a `check_version` gate ✓ · a validator negative ✓) + a D-number ✓ + a conformance vector ✓ | a trace-only reader sees the omission ✓ ⇒ Part II's did-vs-saw gets its third branch ✓ ⇒ the monitor view is derivable from the trace alone ✓ | nothing in v0 ✓ (the v0 validator keeps rejecting v0.1-only lines ✓ and the frozen fixtures keep their bytes ✓) — but it is **spec work** ✓ and the field's **semantics** must be nailed down first ✓ (count vs per-turn set ✓) |
| **(b) a sidecar-only convention, documented** | **free** ✓ (no spec change ✓, no version gate ✓) | the **checker** can enforce it ✓ and the **capture** can be read as pages ✓ | a **trace-only** reader still cannot ✓ ⇒ Part II's claim stays conditional ✓ ⇒ the monitor view would need the sidecar ⇒ **not** a pure function of the trace ✓ ⇒ it contradicts Part I §12 as written ✓ |
| **(c) leave it unrepresented, with a stated limit** | nothing ✓ | honesty ✓ | the **paper contradicts itself** ✓ (Part I §12's monitor view ✓ vs a removal policy's trace ✓) ⇒ and the reviewer's falsifier shows a trace-only reader gets the **wrong residency** ✓ ⇒ every consumer inherits the error ✓ |

⇒ **(c) is out** ✓ (it contradicts a claim the same paper makes ✓); **(b) is necessary but not sufficient**
✓ (the checker needs it ✓; the paper's view claim needs more ✓); **(a) is the only route that satisfies
both** ✓ — **but it does not have to be a new verb** ✓ ⇒ §4 ✓.

---

## 4. The recommended shape: **count + identity, checked** (three parts, two of them free)

### 4.1 The **count** — already exists, needs a *meaning* and a *check* ✓

`turn.render.evictedTokens` ✓ is the required v0 counter ✓ ⇒ keep it ✓. What it lacks ✓: (a) a
**per-turn** definition (it is a **lagging cumulative** ✓ — 4,396 at turn 13 ✓ while the turn's own
removal was one page ✓), and (b) a **check** ✓ (v0 does not check it ✓ — OPEN T-OVICT ✓).

⇒ Cheapest fix, **no wire change** ✓: define the field as *"the cumulative size of the removed set as of
this turn"* ✓ (which is what it is ✓) and check it against the sidecar's **per-call** figures ✓ — see §4.3 ✓.

### 4.2 The **identity** — where it must live for Part II's claim to hold ✓

Two placements, and the choice is the owner's ✓:

- **RFC-0.1 (option a)** ✓: a per-turn **dropped-page list** ✓ on `turn.render` ✓ ⇒ visible to a trace-only
  reader ✓ ⇒ Part II's third branch is derivable ✓ ⇒ costs the five touchpoints ✓.
- **Sidecar (option b)** ✓: a per-turn `droppedPages` list beside `callSizes` ✓ ⇒ free ✓ ⇒ but the trace
  alone stays silent ✓ ⇒ the paper's view claim must then read *"a view is a function of a trace **and its
  sidecar**"* ⇒ a wording change in Part I §12 ✓ (the research lane's ✓).

⇒ **The paper forces the choice** ✓: as long as Part I §12 says *"a pure function of a trace"* ✓, the
identity must be **on the wire** ✓ ⇒ option (a) ✓ ⇒ the sidecar alone is not enough ✓✓.

### 4.3 The **check** — the reviewer's item 4, measured ✓

The reviewer asked: *"if any turn has `evictedTokens > 0`, the sidecar must list the dropped pages and their
sum must be consistent with it"* ✓. Two corrections and one fact:

- **The shape rule already exists** ✓: `tools/coverage_check.py` ✓ enforces *"a treatment that reports
  evictions must say WHICH pages left the request"* ✓ — version-gated ✓ (`plugin.version ≥ 0.13.2` ✓,
  arm ≠ `control` ✓) ⇒ `plugin.evictedPagesCount` must be a positive integer ✓ ✓ (the other lane's
  `6957afe` ✓).
- **It never fires on the capture that needs it** ✓: the rule keys on `plugin.evictedTokens` ✓, and the
  0.13.21 sidecar's plugin block has **no `evictedTokens` key** ✓ (the counter is on the wire ✓, in
  `turn.render` ✓) ⇒ the precondition is false ✓ ⇒ the check is **dormant** ✓ ⇒ it proves nothing about
  this capture ✓✓.
- **The "sum" cannot be checked against the trace counter** ✓: the counter is a **lagging cumulative** ✓
  (§4.1 ✓) ⇒ the consistent comparison is **per call** ✓ — the sidecar's per-call `before − after` against
  the engine's per-call removed tokens ✓ (measured: 8,735 ✓ / 12,941 ✓ / … ✓) ⇒ **not** a sum against the
  trace's total ✓✓ ⇒ and *that* comparison needs the **per-call dropped identities** ✓ (the sidecar keeps
  per-call **counts** ✓ and the **union** ✓ only ✓) ⇒ **one instrument line** ✓ (the ask already routed ✓
  to the hermes lane ✓).

⇒ So the checker's rule has **three** parts ✓, not one ✓: *count present* ✓ → *identity present* ✓ →
*per-call consistency* ✓ — and the third is blocked on the instrument ✓ (not on the spec ✓).

### 4.4 The **turn-scoped view** — the data is already on the wire, but the core cannot simply switch

The representation gap's third part ✓ (§1 ✓) is the **positional cut** ✓. The first draft of this card
called the fix *"a derivation fix with **no wire change**"* ✓ — **corrected here** ✓, because the export's
projection is **coupled to the replay's inference** ✓:

- the export builds its projection from the **same `Playback`** ✓ the divergence check uses ✓
  (`rust/crates/ctxvm-core/src/export.rs:149-154` ✓, `rust/crates/ctxvm-core/src/replay.rs:59,76` ✓) ⇒ the
  projection and the inference are **one engine** ✓;
- the projection's roster is **every declared page** ✓ (`projection_at` → `slots_at` ✓,
  `rust/crates/ctxvm-core/src/render.rs:104-111` ✓) and the **inferred** residency the trace records is the
  **whole table** ✓ (the plugin pins it ✓, `packages/hermes/src/plugin.py:229` ✓) ⇒ cutting the *events* by
  the declared turn would change the **inference** as well ✓ ⇒ every v0.1 capture with declared turns would
  then **diverge** ✓ (recorded 86,569 ✓ against a scoped inference ✓) ⇒ ⇒ a scoped view **cannot replace**
  the table projection ✓ without changing the recorded field's **semantics** ✓ (⇒ RFC-0.1 ✓, the five
  touchpoints ✓, the plugin's pinning ✓, a conformance vector ✓).

⇒ **What is free today** ✓: the **data** is already on the wire for v0.1 traces ✓ — RFC-0.1 **R5** gives
`page.declare` its own `turn`** ✓ (`spec/rfc-0.1/RFC-0.1-xCABI.md:37-39` ✓) ⇒ a **consumer** can compute the
scoped view today ✓ (and v0 traces carry no declare turn ✓ ⇒ they keep today's whole-table reading ✓ — a
compatibility note ✓, not a break ✓) ⇒ and the **export** can print the scoped view as an **additional**
field beside the table tally ✓ (an output addition ✓, **no wire change** ✓✓) ⇒ that is the cheap half ✓.

⇒ So the recommendation is **two** changes, not one ✓: the **scoped view as an additional export field** ✓
(free ✓, code only ✓) and — **only if** the paper wants the *recorded* field to mean per-turn residency ✓ —
a **version-gated semantics change** ✓ (RFC-0.1 ✓, the five touchpoints ✓, the plugin ✓, a vector ✓).

---

## 5. What the owner is asked to decide

```
(a) wire the identity   RFC-0.1 per-turn dropped-page list on turn.render (five touchpoints,
                        D-number, conformance vector)  ->  Part II's third branch holds; the
                        monitor view stays a pure function of the trace
(b) sidecar only        per-turn droppedPages beside callSizes, documented   ->  free; the checker
                        can enforce it; the paper's "pure function of a trace" must become
                        "of a trace and its sidecar"
(c) neither             stated limit in Part II only  ->  rejected: contradicts Part I section 12
```

**Recommendation: (a)** ✓ — because the paper's own view claim demands it ✓ (§0 ✓, §4.2 ✓) — **with the
scoped view added to the export in parallel** ✓ (§4.4 ✓, an output addition ✓, no wire change ✓) and the
**checker rule** completed once the instrument carries per-call identities ✓ (§4.3 ✓).

⇒ **What is free today, before any decision** ✓: the README row ✓ (landed ✓ — *"residentTokens is table
residency, not request residency"* ✓), the sidecar's page list ✓ (already there ✓), the checker's shape rule
✓ (already there ✓), and the export's **scoped view as an extra field** ✓ (a core change ✓, no spec ✓).

⇒ **Not asked here** ✓: the D-number itself ✓ (the owner assigns ✓), the `design/` placement ✓ (the owner
clears ✓), and the paper edits ✓ (the research lane's ✓).

---

## 6. Executed agent-doings

- The reviewer's items 3 and 4 verified against the artefacts ✓: the checker's rule read ✓
  (`tools/coverage_check.py` ✓, version-gated ✓), the sidecar's key set read ✓ (**no `plugin.evictedTokens`**
  ✓ ⇒ the rule is dormant ✓), the v0 schema's `stubText` requirement ✓, RFC-0.1 R5's `page.declare.turn`
  ✓, and the core's positional cut ✓.
- The three options costed against the **five-touchpoint law** ✓ and the **v0-sealed law** ✓, with the
  paper's own §12 as the forcing constraint ✓.
- The recommended shape split into **count** ✓, **identity** ✓, **check** ✓, **scoped view** ✓ —
  two of the four parts need **no spec change** ✓ (the scoped view as an extra export field ✓; the consumer-side
  computation ✓ — the data is already on the wire ✓).
- **This card's own first draft corrected** ✓: the scoped view **cannot replace** the table projection ✓,
  because the export's projection and the replay's inference are one engine ✓ (`export.rs:149-154` ✓,
  `replay.rs:59,76` ✓) and the recorded residency is whole-table ✓ ⇒ a replacement would make every v0.1
  capture with declared turns diverge ✓ ⇒ the scoped view is an **addition** ✓, and a *semantics* change stays
  version-gated ✓.
- No spec, adapter, `design/` or `research/**` file was edited ✓; nothing pushed ✓.

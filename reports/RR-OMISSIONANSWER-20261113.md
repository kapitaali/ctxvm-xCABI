# RR-OMISSIONANSWER-20261113 — the reviewer answers P12 from the packet alone: **the wire**, with three refinements over the proposal (per-call grain, a fail-closed rule, new field names); one of their premises is **wrong** and is corrected here; the scope the ruling leaves open is named

Card: the reviewer's answer to packet **P12** ✓ (`handoff/packets/P12-omission-representation.md` ✓), recorded
against the artefacts it answers from ✓. The ruling: **the identity of an omission goes on the wire** ✓.

---

## 0. The ruling, and what it changes

| the packet asked | the ruling ✓ | effect on `reports/RR-OMISSION-20261113.md` ✓ |
|---|---|---|
| Q1 — wire or sidecar? | **the wire** ✓ — an additive **optional** list of removed-page identities ✓, omitted-when-unknown ✓ (absence = unknown, never zero ✓); the sidecar stays a **documented fallback** ✓ | §4.2 confirmed ✓, with **three** refinements ✓ |
| Q2 — per call or per turn? | **per call** ✓ — and the rule must **fail closed** ✓ | §4.3 confirmed ✓, sharpened ✓ |
| Q3 — addition or replacement? | **addition** ✓, under a **new name** ✓; the recorded `residentTokens` is **not** repurposed ✓ | §4.4 confirmed ✓ ✓ |

⇒ The **direction** of the proposal stands ✓; its **grain**, its **rule shape** and its **naming** change ✓.

---

## 1. The three refinements, and what each one costs

### 1.1 The grain must be **per call**, not per turn ✓

Hermes buckets **about two requests per turn** ✓ (N3 ✓ — the archived turn-unit question ✓,
`handoff/QUESTIONS-ARCHIVE.md:118` ✓), and **measured** ✓: the cell-03 paged arm made **42** API calls across
**20** turns ✓ (the DB ✓) and the 0.13.21 capture has **41** `perApiRequest` entries ✓ for 20 turns ✓ ⇒
**2.1 requests per turn** ✓. Removals differ between the two requests of a turn ✓ (the free capture's dropped
counts per turn: `[0,1]`, `[1,2]`, `[2,3]` … ✓) ⇒ ⇒ a **turn-grain** list would merge them ✓ and lose exactly
what the per-call check needs ✓ ⇒ ⇒ the wire shape must be per request ✓.

⇒ **This creates a tension inside the ruling itself** ✓ — and the packet did not settle it ✓: the ruling says
*"put an additive optional list on `turn.render`"* ✓ **and** *"make it per request or per selection"* ✓ — but
`turn.render` is **per turn** ✓ ⇒ ⇒ the placement must be one of ✓:

1. a **per-turn event carrying per-call entries** ✓ (e.g. `turn.render.removals: [{call, pages:[…]}]` ✓) — one
   event ✓, the grain preserved ✓, no new verb ✓ ✓;
2. a **new per-call verb** ✓ — a bigger change ✓ (five touchpoints ✓, a D-number ✓, a conformance vector ✓);
3. a **per-turn list** ✓ — **ruled out** ✓ by the ruling's own grain requirement ✓ ✓.

⇒ **(1) vs (2) is open** ✓ and is a spec call ✓ (the owner's ✓, with the reviewer's input ✓) ⇒ it is the one
thing this card cannot decide ✓ ⇒ **recorded, not decided** ✓.

### 1.2 The rule must **fail closed** ✓ — and it cannot be evaluated from today's sidecar ✓

The ruling's test ✓: *"for every call, `before − after` from the sidecar equals the sum of the removed pages'
tokens from the engine, within a stated tolerance. A missing entry for a call with `before > budget` is a
failure"* ✓; and *"a capture with removals and no list is a violation"* ✓ — that last clause also fixes the
**dormant precondition** ✓ the card measured ✓ (`plugin.evictedTokens` is absent from the sidecar's plugin
block ✓ ⇒ the existing version-gated rule cannot fire ✓).

⇒ **But the sidecar cannot answer it today** ✓ — measured ✓: the 0.13.21 sidecar's `callSizes` holds **16**
entries ✓ — the **dropping selections only** ✓ ⇒ **25 of the 41 calls have no before/after at all** ✓ ⇒ a
per-call rule cannot be evaluated from it ✓ ⇒ and the engine's own record is **capped**: `CALL_LOG` keeps the
**last 200** selections ✓ (`packages/hermes/live/context_engine.py:503` ✓) and the sidecar helper returns only
the **last 80** ✓ (`packages/hermes/live/__init__.py:656-657` ✓) ⇒ ⇒ the *complete* per-call record does not
exist anywhere today ✓.

⇒ ⇒ **The ask to the hermes lane grows** ✓ (it was: keep the per-call dropped **identities** ✓): it must also
keep **every** call's before/after ✓ (not only the dropping ones ✓) **uncensored** ✓ (no 200/80 tail ✓) ✓ ⇒
otherwise the rule the ruling asks for has nothing to read ✓ ⇒ ⇒ that is the concrete form of the reviewer's
*"that would have caught the `CALL_LOG` censoring bug"* ✓ ✓ (the censoring is real ✓ and measured ✓).

### 1.3 New names, and the recorded field stays as it is ✓

`residentTokens` is **whole-table residency** ✓ ⇒ **not** repurposed ✓ ⇒ the scoped quantity gets a **new
name** ✓ ⇒ and the removals list gets its own name ✓ ⇒ ⇒ both are RFC-0.1 additions ✓ (five touchpoints ✓,
`ts` last ✓) ⇒ ⇒ the names are the spec's call ✓ (recorded ✓).

⇒ **One UNKNOWN answered** ✓: RFC-0.1 **R5**'s `page.declare.turn` ✓ **is** enough for *"pages that existed at
turn N"* ✓ — because the Hermes tracer declares a page **when it is revealed** ✓ (the content's first entry
into a request ✓) ⇒ the declared turn **is** the arrival turn ✓ ⇒ ⇒ "existed at turn N" = declared with turn
≤ N ✓ ⇒ **no second field is needed** ✓ ✓ (for an adapter that declares lazily ✓ the caveat would return ✓).

---

## 2. Their premises, verified — one is **wrong**, and it does not change the ruling

| their premise ✓ | verdict ✓ |
|---|---|
| "Hermes buckets about two requests per turn (N3)" ✓ | **CONFIRMED** ✓ — 42 calls / 20 turns ✓ (DB ✓), 41 `perApiRequest` / 20 turns ✓, and the kit's own measured cross-harness row ✓ ("A Hermes 'turn' is a user turn (`turn.render` buckets about two model requests under it)" ✓) |
| "the OpenCode adapter has no equivalent sidecar" ✓ | **NOT CONFIRMED** ✓ — the OpenCode adapter **does** write a coverage sidecar ✓ (`packages/opencode/live/ctxvm.ts:388-391` ✓ — *"the coverage sidecar rides every full flush"* ✓ ⇒ `<name>.coverage.json` ✓) and the sidecar shapes are **canonicalised across harnesses** ✓ (W17 ✓) ⇒ ⇒ **the stated reason does not hold** ✓ |
| "check before any wire change that no omitted-when-unknown field already covers this" ✓ | **CHECKED** ✓ — RFC-0.1's additive fields are `schemaVersion` ✓, `ts` ✓, `toolEffect` ✓, `providerUsage` ✓, `environmentId` ✓, `latencyMs` ✓, `prefix` ✓, `turn` ✓ ⇒ **none** carries removals ✓ ⇒ nothing already covers it ✓ |
| "the engine is shared between export and replay (`export.rs:149-154`, `replay.rs:59,76`)" ✓ | **CONFIRMED** ✓ (this lane's own reading ✓) |
| "the provider's request-size ratio (0.563 against the trace's 0.570)" ✓ | **CONFIRMED** ✓ (measured ✓) |
| UNKNOWN: "whether OpenCode can report removals at all" ✓ | **ANSWERED** ✓: it **cannot** — the OpenCode adapter has **no removal concept at all** ✓ (no `evict`/`remov`/`drop` hits in `packages/opencode/live/ctxvm.ts` ✓ or `packages/opencode/src/plugin.ts` ✓) ⇒ ⇒ the omission-by-policy case is **Hermes-only for now** ✓ ⇒ ⇒ the field must be **optional** ✓ ⇒ ⇒ their falsifier ("a second harness that cannot report removals") **already fires today** ✓ ⇒ ⇒ the design must be *optional field + documented fallback* ✓ ✓ |

⇒ **The ruling stands** ✓ — the sidecar is not the trace ✓, so *"a pure function of a trace"* stays false for
removal policies ✓ ⇒ the wire is still the primary ✓ ⇒ only the *stated reason* for preferring the wire needs
correcting ✓ ⇒ ⇒ recorded as an erratum ✓ (the answer text in `handoff/QUESTIONS.md` is the reviewer's own ✓
and is quoted **verbatim** ✓ ⇒ the correction lives here ✓, in the card ✓, and in the notes ✓ — not in their
words ✓ ✓).

⇒ **Their second UNKNOWN, answered with a number** ✓ (the per-call list's size ✓): the measured session makes
**75** page-drops ✓ over **41** calls ✓ ⇒ a wire entry of the shape
`{"logicalRef":"tool:read_file({…})","contentHash":"sha256:…","tokens":4385}` ✓ is **113 bytes** ✓ ⇒ ⇒ the whole
session's per-call list ≈ **8.5 KB** ✓ ⇒ ⇒ **linear in the removals** ✓ (each call lists only what *it* removed
✓ ⇒ no quadratic growth ✓) ⇒ ⇒ for a 100-call session ≈ **20 KB** ✓ ⇒ ⇒ the size is **affordable** ✓ but it is
a real cost on every trace ✓ ⇒ and it is the size of the *optional* field ✓ ⇒ ⇒ a harness that omits it pays
nothing ✓ ✓.

---

## 3. The falsifiers, both of them, and the scope the ruling leaves open ✓

- **Theirs** ✓: any capture where the sum of the per-call removed entries disagrees with the **provider's
  receipts** by more than the tokenizer's estimate error ✓; and a second harness that cannot report removals ✓
  ⇒ keep the field optional ✓ and the sidecar as the documented fallback ✓ ✓ — the second one **already fires**
  today ✓ (OpenCode ✓).
- **This lane's** ✓ (from the erratum review ✓): the **nested-set** identity question ✓ — whether the two
  selections inside a turn dropped the same pages ✓ — stays **UNVERIFIED** ✓ until the sidecar keeps the
  per-call identities ✓ ⇒ which the ruling's rule now *requires* ✓ ⇒ ⇒ the instrument ask and the spec ask
  are the same ask ✓ ✓.
- **Open after the ruling** ✓ (and *not* decided here ✓): the **placement** of the per-call list ✓ (a
  per-turn event with per-call entries ✓ vs a new per-call verb ✓) ✓; the **names** ✓; the **D-number**
  (one with the D18 compatibility line ✓ or separate ✓ — their third UNKNOWN ✓); and the **tolerance** for the
  per-call sum check ✓ ✓.

⇒ ⇒ **What the ruling needs next** ✓: the instrument (the hermes lane ✓ — now with the **completeness** and
**uncensoring** clauses ✓) and the spec (the owner ✓ — the placement ✓, the names ✓, the D-number ✓) ⇒ ⇒ and
**Part I §12 / Part II §6.3** stay as they are ✓ (the wire route keeps *"a pure function of a trace"* ✓ ✓) ✓.

---

## 4. Executed agent-doings

- The answer read and checked against the artefacts it names ✓: the turn bucketing ✓ (DB ✓ + sidecar ✓ +
  README ✓ + N3 ✓), the OpenCode sidecar ✓ (read: it exists ✓), the OpenCode removal concept ✓ (read: it does
  not exist ✓), the RFC-0.1 field list ✓ (read: nothing covers removals ✓), the `CALL_LOG` caps ✓ (read: 200 ✓
  and 80 ✓), the sidecar's per-call completeness ✓ (16 of 41 ✓), the export/replay coupling ✓ (read ✓), the
  provider ratio ✓ (measured ✓), and the list's size ✓ (measured ✓: 75 × 113 B ≈ 8.5 KB ✓).
- The proposal card updated ✓ (grain ✓, rule shape ✓, naming ✓, and the placement left open ✓) with an
  **erratum row** ✓ (the committed row said "per-turn dropped-page list" ✓ ⇒ corrected ✓).
- The reviewer's answer text recorded **verbatim** ✓ in `handoff/QUESTIONS.md` ✓; the packet's STATUS line
  updated ✓; **D19 (proposed)** updated ✓ with the ruling ✓ and the owner's remaining choice ✓.
- No spec, adapter, `design/` or `research/**` file edited ✓; nothing pushed ✓.

# RR-W8DERRATUM-20261113 — review of the W8D §11 erratum (`ceb15d2`): five of its inputs verified, three arithmetic errors found, and its model check contradicts itself; the refusal stands and is stronger than the erratum says

Card: review-lane verification of the erratum the hermes lane appended to
`design/W8D-PREREG-STABLE-20261113.md` §11 on 2026-11-13 (commit `ceb15d2`), checked against the
0.13.22 capture, the cell-03 Hermes session DBs, the two cell-03 traces, and the engine source.

---

## 0. Verdict in one paragraph

§11 is a **real improvement** on §9: the withdrawal of "0 stubs" and "independently derived" is
**correct** ✓ (this lane's `reports/RR-SHAPEGAP-20261113.md` §1.1 is the evidence ✓), and four of the
numbers it fixes are **verified correct** ✓. But §11 has **three arithmetic errors** ✓ (§2 below) and
its **model check is internally inconsistent** ✓ (§3): the sentence *"a rewrite writes essentially the
whole post-selection request"* and the count *"16 rewrite events today"* cannot both be true of the
measured billed volume ✓ — 16 whole-request writes would cost **1.80 M** provider tokens against a
measured **1.03 M** ✓ (a factor 1.76 ✓). The measured volume instead fits **9** whole-request writes
with a **0.2 %** residual ✓. ⇒ The rewrite count today is **9**, not 16 ✓ ⇒ the reduction hold-once
promises is **1.0×, not 1.8×** ✓ ⇒ and the refusal's magnitude is today's own number (**24,424** write
tokens per call against a **1,868–2,428** allowance ✓, ≈10× over ✓) — **unchanged by the treatment** ✓.
⇒ **Do not authorise the paid pair** ✓✓ — the erratum's recommendation survives, and for a stronger
reason than the erratum gives ✓.

---

## 1. §11's inputs: five verified, with locators

| §11 says | measured | locator |
|---|---|---|
| 16 selections dropped something | **16** ✓ | 0.13.22 sidecar `plugin.callSizes` = 16 entries with `dropped ≥ 1` ✓; `plugin.engineSelections = 16` ✓ |
| 75 page-drops in total | **75** ✓ | Σ `dropped` over those 16 entries ✓ |
| the DISTINCT pages ever removed are 9 | **9** ✓ | sidecar `plugin.evictedPagesCount = 9` ✓ (the live adapter's union set ✓, `packages/hermes/live/__init__.py:834-835` ✓) |
| billed writes for the pair = 1,254,207 | **1,254,207** ✓ | paged `cache_write_tokens = 1,025,825` ✓ + control `228,382` ✓ (the pair's own DB rows ✓) |
| "0 stubs" / "independently derived" withdrawn | **correct** ✓ | the hermes engine has no stub concept ✓ and the adapter never emits `page.evict` ✓ ⇒ "0 stubs" is entailed by the event vocabulary ✓ (`reports/RR-SHAPEGAP-20261113.md` §1.1 ✓) |

Repro for the DB rows (the pair's two sessions, `api_call_count` included — see §2.1):

```
python3 - <<'EOF'
import sqlite3, os
for prof, pref in (("w8cp-paged","local-c0b4ff6%"), ("w8cp-naive","local-87612ee9%")):
    p = os.path.expanduser(f"~/.hermes/profiles/{prof}/state.db")
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    for r in con.execute("select id, api_call_count, cache_write_tokens, cache_read_tokens, "
                          "estimated_cost_usd from sessions where id like ?", (pref,)):
        print(prof, r)
EOF
```

---

## 2. The three arithmetic errors

### 2.1 The denominator is **42**, not 41 — three numbers shift

§11 divides the **paid pair's** billed writes by **41** ✓: *"25,020 per call"* ✓ (= 1,025,825 ÷ 41 ✓),
*"14,074 per call"* ✓ (= 577,027 ÷ 41 ✓), *"9 × 11,000 ÷ 41 ≈ 2,400"* ✓.

**41 is the free capture's selection count**, not the paid arm's call count ✓. The paid paged arm made
**42** API calls ✓ (DB: `api_call_count = 42` ✓ — the same row RR-PAIDRESULT-20261112 §1 prints ✓, and
84 for the pair ✓ = 42 + 42 ✓, which is the denominator §9's "84 calls" used ✓).

| quantity | §11 (÷41) | ÷42 (measured) |
|---|---|---|
| write tokens per call, today | 25,020 | **24,424** ✓ (the figure `reports/RR-W8DREVIEW-20261112.md` §1.3 already recorded ✓) |
| write tokens per call, hold-once | 14,074 | **13,739** |
| the per-rewrite ceiling, as it lands inside the allowance | 9 × 11,000 ÷ 41 ≈ 2,400 | **9 × 11,000 ÷ 42 ≈ 2,357** ✓ (the ~11,000 per-rewrite ceiling itself is unchanged ✓) |

⇒ Small, but the erratum's *headline* comparison ("25,020 per call ÷ ~2,400 allowance = 10.4×") is a
**10.2×** claim on the measured numbers ✓, and the allowance's own denominator needs the same audit
(§4.3 ✓).

### 2.2 The "0.918" ratio is **inverted**, and it compares two different tokenizers

§11's model check: *"sum(after) over the 16 dropping selections is 941,257 against 1,025,825 billed —
a ratio of **0.918**, i.e. **a rewrite writes essentially the whole post-selection request**"* ✓.

Two problems with the sentence:

1. **Orientation.** 941,257 ÷ 1,025,825 = **0.9176** ✓ is *(post-selection requests) ÷ (billed writes)*
   ✓. The claim it supports — "a rewrite writes essentially the whole post-selection request" — needs
   the **other** orientation ✓: 1,025,825 ÷ 941,257 = **1.090** ✓. As printed, the quoted number reads
   as *"the writes are 92 % of the request"* ✓, which is the opposite of the sentence it is attached to ✓.
2. **Units.** The two numbers are in **different tokenizers** ✓: `sum(after)` is the engine's own
   apx4-char accounting ✓ (`packages/hermes/live/context_engine.py:107-110` ✓ `_estimate_tokens`:
   `(len(text) + 3) // 4` ✓, plus a per-message overhead ✓ at `:148-149` ✓), while the billed writes
   are **provider** tokens ✓. The factor between them is measured on this very pair ✓ (§3 ✓):
   **1.9208** (paged, turn 19 ✓) and **1.9443** (control, turn 19 ✓).

⇒ With the units corrected: 1,025,825 provider tokens ÷ 1.9208 = **534,057** engine tokens ✓ against
941,257 of post-selection request ⇒ the billed writes are **0.567** of it ✓ — and 9/16 = **0.5625** ✓.
⇒ **That number is the tell** ✓ (§3 ✓).

### 2.3 "Rewrite events, today 16" is **not supported by any artefact**; the structural count is 9

§11: *"rewrite events, today 16 (every dropping selection rewrites the prefix)"* ✓.

The 16 is the number of **selections that dropped something** ✓ — a fact ✓ — but the dropped-set
**sizes** over those 16 selections take **9 distinct values** ✓ and change **9 times** ✓ (0 → 1 → … → 9):

```
free capture (0.13.22), the 41 selections of the run window, in order:
  dropped = 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 | 1 1 2 2 3 3 4 4 5 5 6 6 7 8 9 9
  distinct sizes: [1,2,3,4,5,6,7,8,9]   size-changes: 9   (8 inside the dropping list + the first 0 -> 1)
```

⇒ A selection whose dropped **size** did not change re-dropped the same set ⇒ the retained content is
the same ⇒ the request's leading prefix is the same ⇒ **no cache write** ✓ ⇒ the number of
prefix-changing rewrites is **9**, not 16 ✓.

⇒ **And the "hold once" premise already holds today** ✓: the sidecar's union of pages ever dropped is
**9** ✓ and the final dropped set's size is **9** ✓ ⇒ every page ever dropped is still dropped at the
end ✓ ⇒ **the policy never un-drops a page** ✓ ⇒ "a page, once evicted, stays evicted for the
session" ✓ — hold-once's §3 premise ✓ — is **already the current behaviour** ✓✓.

⇒ **Caveat, marked UNVERIFIED**: whether the two selections inside a turn dropped the *same pages* (the
union = final size proves no page was permanently un-dropped ✓, but a *rotation* among the same nine
pages would keep the union at 9 ✓) **cannot be settled from the artefacts** ✓ — the observer payload
carries the per-call dropped identities ✓ (`packages/hermes/live/context_engine.py:545-548` ✓) but the
live adapter folds them into a **union set** ✓ and keeps per-call **counts only** ✓
(`packages/hermes/live/__init__.py:1492-1500` ✓, sidecar `callSizes` ✓) ⇒ the per-call identity list
is **not persisted** ✓. §3's arithmetic below settles the count without it ✓.

---

## 3. The model check contradicts itself — and the contradiction fixes the event count

§11 asserts (i) *"a rewrite writes essentially the whole post-selection request"* ✓ and (ii) *"16
rewrite events today"* ✓. Both cannot hold of the measured billed volume ✓.

**The priced pair's own request sizes** (cell-03 paged trace ✓, `turn.render.prefix.approxInputTokens` ✓)
and the **provider's own receipts** ✓ (same trace's `call.meta.providerUsage.cachedInputTokens` ✓):

```
turn | trace approxInputTokens | provider cachedInputTokens | k = provider / trace
 10  |           57,776          |          104,513          | 1.809
 11  |           57,846          |           23,901          | 0.413   <- prefix collapsed
 12  |           58,019          |           14,504          | 0.250   <- prefix collapsed
 18  |           58,672          |           14,504          | 0.247   <- prefix collapsed
 19  |           59,747          |          114,763          | 1.921   <- fully cached again
```

⇒ **Two measurements fall out of that table** ✓:

1. **The tokenizer factor** on this pair is **1.92–1.94** ✓ (control turn 19: 203,842 ÷ 104,842 =
   **1.9443** ✓) ⇒ the correction §2.2 needs ✓.
2. **The paged arm's cached prefix collapsed to 14,504 tokens from turn 12 to turn 18** ✓ — and 14,504
   is the **turn-0 value** ✓ (14,554 ✓, within 50 tokens ✓), i.e. the **static prefix alone** ✓ ⇒ the
   provider could reuse **none** of the message content in those turns ✓ ⇒ **each rewrite re-wrote the
   message content** ✓ ⇒ a rewrite writes ≈ the **whole** post-selection request ✓ — which is §11's
   own model check ✓, independently witnessed by the provider's receipts ✓.

⇒ Now the two models against the measured **1,025,825** billed provider write tokens ✓:

```
Model A: 9 whole-request writes (one per size-change, turns 12..18 plus two at turn 19)
   sum of the 9 event requests = 528,497 apx4
   x k_paged (1.9208) = 1,015,146 provider tokens   residual -1.04 %
   x k_ctrl  (1.9443) = 1,027,545 provider tokens   residual +0.17 %
Model B: 16 whole-request writes
   would cost 1,804,703 provider tokens  ->  1.76x the measured volume   FAILS
```

⇒ **Model A fits within 0.2–1.0 %** ✓ and **Model B misses by 1.76×** ✓ ⇒ the rewrite count today is
**9** ✓✓ — consistent with the structural count in §2.3 ✓ (two independent lines ✓).

⇒ **This also exposes the "36 → 16 → 9" chain**: 36 was unsupported ✓ (RR-W8DREVIEW ✓), 16 is the
*selections* count ✓, and **9 is the *rewrite* count** ✓ — the erratum's "16 → 9 = 1.8×" compares a
selections count with a rewrites count ✓ ⇒ **the like-for-like comparison is 9 → 9 = 1.0×** ✓✓.

⇒ The other candidate reading, stated so the card is not one-sided ✓: if the per-event write is
**64,114** provider tokens ✓ (= 33,379 engine ✓ = **57 %** of a post-selection request ✓) then Model B
survives arithmetically ✓ — but that **discards §11's own model check** ✓ ("essentially the whole
post-selection request" ✓) and makes the erratum's *stated* reason for hold-once's weakness void ✓.
⇒ Either way the **recommendation** is unchanged ✓; what changes is the **magnitude** ✓ and the
**discriminating power of the gate** ✓ (§4 ✓).

---

## 4. Consequences for the refusal, the gate, and the preregistration

### 4.1 The refusal is unchanged in direction and stronger in magnitude

- §10's recommendation (**do not authorise the paid pair**) ✓ **stands** ✓.
- The measured excess over the allowance is **today's own** ✓: 24,424 write tokens per call ✓ against
  the 1,868–2,428 allowance ✓ ⇒ **~10× over allowance** ✓ (the figure `reports/RR-W8DREVIEW-20261112.md`
  §1.3 already recorded ✓) — and hold-once **does not touch it** ✓, because hold-once's premise
  already holds today ✓ (§2.3 ✓).

### 4.2 The zero-spend gate's step 1 **cannot discriminate** the treatment

§5 step 1 asks for the rewrite-event count under hold semantics ✓; §4's **H1** predicts **9–14** ✓
(bracket 5–20 ✓) against `_selections.log` ✓. Measured on **today's** run ✓: **9 size-changes over 8
turns** ✓ (§2.3 ✓) — the same magnitude H1 predicts for the *treatment* ✓ ⇒ **the gate returns the same
number for the control and the treatment** ✓✓ ⇒ a passing step 1 would be **evidence of nothing** ✓.

⇒ The gate needs a discriminator that today's run does **not** already satisfy ✓ — and the cheapest one
is **the per-call dropped identity list** ✓ (§5 ✓), because it distinguishes "the same set re-dropped"
✓ from "a different set at the same size" ✓ — the one distinction the artefacts currently drop ✓.

### 4.3 The allowance's rate seam is unchanged and still open

§11 keeps §2's input-rate allowance ($0.10–0.13/M ✓) ⇒ 1,868–2,428 write tokens per call ✓.
`reports/RR-W8DREVIEW-20261112.md` §1.1 already recorded that at **cell-03's shape** the unsent content
was **cache-read** by the control ✓ ⇒ the saving belongs at the **read** rate ✓ ⇒ the allowance is
**10× smaller** ✓ ⇒ the honest excess is larger still ✓. The erratum inherits the prereg's rate
choice unchanged ✓ — **flagged, not re-litigated here** ✓ (it is the other card's seam ✓).

---

## 5. What would settle the remaining question (one instrument line, no spend)

The only open item is the **identity** of the dropped set per selection ✓ (§2.3's caveat ✓). The
observer already computes it ✓ (`packages/hermes/live/context_engine.py:545-548` ✓: the payload carries
`"dropped": [sorted(units[i].id_toks) ...]` ✓) and the live adapter currently **discards the per-call
list** ✓ (it folds it into the union ✓, `packages/hermes/live/__init__.py:1498-1500` ✓).

⇒ **Recommendation (hermes lane owns the adapter ✓; this lane does not edit it ✓):** keep the per-call
dropped identities in the sidecar next to `callSizes` ✓ — e.g. `callSizes[i].droppedRefs` ✓ — and the
question "does today's policy rewrite the prefix 9 times or 16 times?" becomes a **lookup** ✓ instead
of an inference ✓.

⇒ Then §5 step 1 becomes decidable ✓ at zero spend ✓, and the honest H1 bracket becomes "the count
today" vs "the count under hold" ✓ — which is the only comparison the experiment can make ✓.

---

## 6. One correction to **this lane's own** card (`reports/RR-SHAPEGAP-20261113.md` §1.4)

That card's falsifier table prints, for the paged arm, the provider's `cachedInputTokens` as if it were
the request size ✓. It is the **cached prefix** ✓, and in the paged arm's turns 12–18 that prefix
**collapsed to the static 14,504 tokens** ✓ ⇒

- the **turn-12 row (p/c = 0.118)** ✓ is a **cache-hit ratio** ✓, not a request-size ratio ✓ ⇒ it must
  be labelled as such ✓ (the *fact* it records — the cache prefix collapsed — is itself the strongest
  evidence that the prefix was rewritten ✓✓, and it now carries the model check in §3 ✓);
- the **turn-19 row (p/c = 0.563)** ✓ is a **request-size ratio** ✓ ✓ (both arms' requests were fully
  cached at turn 19 ✓ — paged 114,763 ≈ 59,747 × 1.9208 ✓, control 203,842 ≈ 104,842 × 1.9443 ✓) ✓ ⇒
  the falsifier's verdict stands ✓✓ (the model did not see all 21 pages ✓ ⇒ the removal measurement is
  right ✓ and the derived table is the false part ✓).

⇒ No conclusion of `RR-SHAPEGAP-20261113.md` changes ✓; one column's **label** does ✓.

---

## 7. Open items and limits

- **UNVERIFIED**: whether the two selections inside a turn dropped the same page identities (§2.3) —
  the artefacts do not persist them ✓; the billed volume points to 9 rewrite events ✓ (§3 ✓) but the
  per-call identity list would settle it directly ✓ (§5 ✓).
- **UNVERIFIED**: the provider's cache-block granularity and break-point rules ✓ — not modelled here ✓;
  the "whole post-selection request" model is the erratum's ✓ and the receipt collapse witnesses it ✓,
  but the exact per-event write volume is not derivable from the artefacts ✓ (only the total is ✓).
- The erratum's own **§10 reopen threshold** ("a measured write volume per rewrite below ~7,000 tokens"
  ✓, corrected to ~11,000 ✓) is stated in the **old** denominator ✓ and needs the §2.1 correction ✓
  (≈10,946 ✓); the direction of the threshold ✓ (a per-rewrite write volume far below the current
  ~114,000 provider tokens ✓) is unaffected ✓.

---

## 8. Executed agent-doings

- §11's five inputs re-measured from the artefacts ✓ (the 0.13.22 sidecar ✓, the two cell-03 DB rows ✓,
  the two cell-03 traces ✓) — all five hold ✓.
- The **erratum's three arithmetic errors** located and quantified ✓ with repro commands ✓ (§2 ✓).
- The **model check's internal contradiction** stated and resolved by two independent lines ✓ (the
  structural count of distinct dropped-set sizes ✓ and the billed-volume fit ✓).
- **This lane's own** provider-receipt table relabelled ✓ (§6 ✓) — no conclusion changed ✓.
- The **decisive missing measurement** identified and costed ✓ (§5 ✓): one sidecar field ✓, zero spend ✓.
- No file of another lane's was edited ✓ (`design/W8D-PREREG-STABLE-20261113.md` is the hermes lane's ✓
  and was **not** touched ✓; `packages/hermes/**` ✓ and `tools/**` ✓ untouched ✓); nothing pushed ✓.

# RR-W8DREVIEW-20261112 — review of the W8D preregistration (`design/W8D-PREREG-STABLE-20261113.md`, `3d91fb9`): the refusal to spend is right, but three of its four arithmetic steps do not close on the repo's own numbers

Card: review-lane reading of the W8D preregistration and its §9 zero-spend gate, checked against the
cell-03 captures, the Hermes session DBs, the billed export, the catalogue rates, and the engine source.

---

## 1. The conclusion is right; the arithmetic that reaches it has three open seams

`design/W8D-PREREG-STABLE-20261113.md` §10 recommends **"Do not authorise the paid pair"** and §9's gate
computes a refusal. **The review side agrees with the refusal** ✓ and with its direction ✓ — the paid
pair would buy a ratio the arithmetic can already bound ✓. But three of the four steps do not close on
the repo's own numbers, and one of them is load-bearing for the *strength* of the refusal (not its
direction). Details below, each with a repro command.

### 1.1 "unsent content 203,975 tokens" is the **net request reduction**, not the unsent content — and the two differ by 4.4×

The prereg §2 prices "unsent content 203,975 tokens" at the **input** rate ($0.10–0.13/1M) to get
$0.0204–0.0265 of value. Two problems:

1. **203,975 is not "unsent content"** — it is the cell-03 **net request reduction** (`P5` in
   `reports/RR-W8CCELL03-RUN-20261112.md:41`), and it is already in the books under that name
   ✓. The **unsent content** in the books is a different, larger number: **894,814 tokens**
   (`reports/RR-POLICYCHOICE-20261112.md` §1: *"Content never sent by the paged arm: 894,814 tokens"* ✓).
   Recomputed from the two cell-03 captures ✓:

   ```
   turn.render prefix approxInputTokens, control − paged, summed over 20 turns = 201,719
   (paged evictedTokens sum = 275,362; control turns with evictions = 0)
   ```

   ⇒ the prereg prices **the smaller of two different quantities** ✓ at the input rate ✓.

2. **The input rate is the wrong rate for the measured configuration.** In cell-03 the content the
   paged arm did *not* send was content the **control arm read from cache** (cache_read $0.01/1M) ✓ —
   the provider export shows `cache_read 7,106,700` for the key and the DB row shows the control arm's
   `cache_read_tokens = 4,348,503` ✓. Pricing unsent content at the **input** rate ($0.10/M) is
   valid only in the **cold-prefix / no-prefix-cache** shape ✓ — which is the *next* experiment ✓, not
   cell-03's shape ✓.

⇒ **At cell-03's shape, the saving is priced at the read rate**, and the books already say so ✓:
`reports/RR-POLICYCHOICE-20261112.md` §2 prices the saving at **$0.0089** (894,814 unsent tokens at
$0.01/M) against a tax of **$0.1037** (797,443 re-sent tokens at $0.13/M) — **11.6×** ✓✓.

⇒ So the prereg's headline **"the rewrite costs 3.1–4.1× the value of what it saves"** understates the
measured penalty by roughly **3×** ✓ (3.1–4.1× vs the books' **11.6×** ✓). The refusal survives ✓ —
it is stronger than stated ✓, not weaker ✓.

### 1.2 §9's "rewrite events, today 36" has **no locator in the books** — and the repo's own counts say **16**

§9 scales "1,408,011 tokens → 39,111 per rewrite" from **36 rewrite events** and predicts **9** under
hold-once. Where 36 comes from is not stated, and it does not match the artefacts:

| source | count |
|---|---|
| billed export, luna key, 24 h window | `cache_write 1,408,011` over **98 requests** ✓ (`reports/RR-W8CCELL03-RUN-20261112.md:105` ✓) |
| the pair's two DB sessions | paged `cache_write_tokens = 1,025,825` ✓, control `228,382` ✓ (read from `~/.hermes/profiles/w8cp-*/state.db`, `sessions` table ✓) |
| **the pair's own billed write volume** | 1,025,825 + 228,382 = **1,254,207** ✓ — **not** 1,408,011 ✓ (the export's 98 requests include **14 requests outside the pair** ✓) |
| paged arm's `_selections.log` (free 20-prompt run, same shape) | **16 selections with `dropped>0`** ✓ of 41 ✓ |
| paged arm's `callSizes` (0.13.22 capture) | **16 entries, `dropped` ∈ 1…9** ✓ |
| cell-03 paged trace | **8 turns** carry `evictedTokens>0` ✓ of 20 ✓ |

⇒ **"36" is unreconciled** ✓ — the nearest measured quantity is **16** ✓ (dropping selections in the
same shape ✓), and the billed write volume attributable to the pair is **1,254,207** ✓, not 1,408,011 ✓.

⇒ **This matters because the refusal's strength is computed from it.** With the pair's own numbers:

```
write volume today        1,254,207 tokens over 84 calls  = 14,931 tokens/call
allowance (from §2's own $0.0204–0.0265 saving)             1,868–2,428 tokens/call
required reduction                                              6.1–8.0x
hold-once reduction (16 -> 9 dropping selections)                  1.8x
=> still short by ~3.4x, but by a different route than §9 states
```

⇒ The refusal is **robust to the correction** ✓✓ — it does not flip ✓ — but §9's numbers as printed do
not close ✓, and a reader checking them will find three quantities that do not match the artefacts ✓.

### 1.3 The §9 bounds are the right shape but the **"conservative end"** claim is backwards for one of them

§9 says the scaled estimate (4,191 tokens/call) "is the conservative end" ✓ and is "the only one
anchored in a **billed** number rather than an assumption" ✓. Two checks:

- The "whole post-rewrite request" bound (4,362/call ✓) is **not** conservative in the sense the
  prereg needs ✓: it assumes the rewrite re-writes the **whole** request every time ✓, whereas the
  measured paged arm's `cache_write` is **24,424 tokens/call** ✓ (`1,025,825 / 42` ✓ from the DB ✓) —
  i.e. **below** the 4,362 figure ✓ because the rewrite does **not** re-write the whole request ✓.
- The "newly evicted pages only" bound (328/call ✓) is the *optimistic* end ✓ and the scaled estimate
  sits **between** them ✓ — the prereg's own words ✓. So the direction of the bound is fine ✓✓, but
  the sentence calling 4,191 "the conservative end" is only true against the **optimistic** bound ✓,
  not against the measured 24,424/call ✓.

⇒ **The one number a reader should take from §9 is the measured 24,424 write tokens/call** ✓ (paged arm,
DB) against a **1,868–2,428** allowance ✓ ⇒ **~10× over allowance today** ✓ — the strongest form of the
refusal ✓ and it needs no assumption about per-rewrite volume at all ✓.

### 1.4 §5's zero-spend gate step 1 cannot be executed as written, and the **falsifier H4 is unreachable**

§5 step 1 says: *"replay cell-03's `_selections.log` under hold semantics and count rewrite events
(H1)"*. Two blockers:

1. **cell-03 has no `_selections.log`** ✓ — the file was introduced with plugin `0.13.21` ✓
   (`41a1aaf` ✓, 2026-11-13) and cell-03 ran on **2026-11-12** ✓ under `0.13.1` ✓. The trace dir's
   `_selections.log` starts at `2026-11-13T15:04:45` ✓ — the confirmation run ✓ — so cell-03's
   selection-level record does not exist ✓.
2. The nearest usable artefact is the **0.13.22 confirmation capture** ✓ (`w8b-20261113-150420-paged` ✓,
   41 selections ✓, 16 dropping ✓, `dropped` ∈ 1…9 ✓) — and its own numbers **already answer step 1**
   without any replay ✓: the dropped-set sizes are **monotone non-decreasing** ✓ (`1,1,2,2,3,3,4,4,5,5,6,6,7,8,9,9` ✓ — the last value `7` in the log is a pytest-suite line ✓, filtered out ✓), so the "dropped set grows, never repeats" premise of §3 is **already true in the current policy** ✓✓ — which means hold-once's proposed change would be a **no-op on the set**, and the reduction would come only from *not re-writing* the same set ✓.

⇒ **Falsifier H4 is then unreachable in its stated form**: H4 predicts a dollar ratio of **1.15**
(bracket 0.95–1.60) ✓, and §9's own gate predicts the ratio stays **≥ 1.6** ✓ — but the falsifier says
*"if the dollar ratio stays at or above 1.6 with write volume above 3,500 tokens per call, hold-once does
not fix the trade"* ✓✓. Both cannot be true of the same run ✓: a ratio of 1.15 is *inside* the 0.95–1.60
bracket ✓, so **H4's bracket admits the outcome the falsifier calls a failure** ✓. The bracket and the
falsifier need to be reconciled before the block is written ✓ — that is exactly the ratified rule's
point ✓ (`reports/W8-SPEND.md` §Prediction clause 1: every predicted quantity names its unit ✓; a
bracket that contains its own falsifier does not ✓).

---

## 2. What the prereg gets right, and should be kept

1. **The refusal** ✓✓ — spending up to $1.00 to confirm a ratio the arithmetic bounds is the purchase
   this line has learned to refuse ✓, and the owner's ruling ("no further paid spend until the engine
   changes") makes the refusal the *cheap* branch ✓.
2. **The claim ceiling** (§7) ✓ — "no saving", "no cold-prefix claim", "no generalisation past this
   shape" ✓, which is law 7 ✓ and the repo's own §"What this does not say" discipline ✓.
3. **The engine-change framing** (§3) ✓ — "this changes the engine, which is the condition the owner's
   ruling names" ✓, and the option is a **setting** (`selection_mode: hold`) ✓ so today's behaviour stays
   reproducible ✓ and the two booked cells stay comparable ✓.
4. **Naming the right next question** (§10 option b) ✓ — "change the shape, not the policy" ✓, with the
   correct mechanism named ✓ (a cold prefix or a provider without prefix caching, where the unsent
   content is priced at the input rate) ✓ — which is `reports/RR-POLICYCHOICE-20261112.md` §3(d) ✓
   (the same 894,814 tokens at the input rate ≈ **$0.089** ✓ ≈ 1.2× the control's cost ✓).
5. **The re-open condition** (§10) ✓ — "a measured write volume per rewrite below ~7,000 tokens" ✓ is
   a *measurement* on a different provider ✓, not a redesign ✓.

---

## 3. What the owner is actually being asked, restated with the corrected numbers

```
decision    authorise nothing (recommended)
why         the paid pair would buy a dollar ratio the arithmetic already bounds:
            the paged arm's measured cache-write volume is 24,424 tokens/call
            (DB, 1,025,825 / 42) against an allowance of 1,868-2,428 tokens/call
            -> ~10x over allowance today; a hold-once variant that only stops
            REPEATEDLY rewriting the same growing set buys 1.8x at most
free work    the 0.13.22 capture can be replayed under hold semantics TODAY, zero spend,
            and it answers H1 (16 -> ? dropping selections) without a run
before any   a zero-spend simulator pass that predicts the hold-once write volume from the
new spend    measured per-call sizes, so the next pair's ratio is bounded before it is bought
```

---

## 4. Executed agent-doings

- The preregistration, the closing card, the owner-ratified prediction rule, and the cell-03 cards were
  read at the committed bytes ✓.
- The cell-03 **captures** were re-read (both arms: `turn.render` counts, `evictedTokens` sums, per-turn
  request sizes) ✓ and the **control-minus-paged per-turn differences were summed** (201,719 ✓) ✓.
- The **Hermes session DBs** for the paid pair were read (`~/.hermes/profiles/w8cp-{naive,paged}/state.db`,
  `sessions` table ✓): `cache_write_tokens` 1,025,825 (paged) and 228,382 (control) ✓,
  `cache_read_tokens` 2,656,246 and 4,348,503 ✓, costs $0.158032 and $0.074824 ✓ ⇒ per-call write
  volume **24,424** and 5,438 ✓.
- The **billed export** (`experiments/usage-day-summary-a93f8b06-2026-11-12_24h.csv` ✓) was read ✓:
  98 requests / 1,408,011 write tokens for the key ✓ ⇒ the pair's share is 1,254,207 ✓ and 14 requests
  are outside the pair ✓.
- The **catalogue rates** were read (`benchmarks/metrics/prices.json` ✓): GPT-6 Luna input **$0.10/1M**,
  cached read **$0.01/1M** ✓, output $0.50/1M ✓; the gateway's own estimate implies a write rate of
  **$0.127/1M** ✓ (consistent with the $0.13 used in the books ✓).
- The **0.13.22 capture's `_selections.log`** was filtered by the run's timestamp window ✓ (the file also
  carries 39 pytest-suite lines ✓ — see `reports/RR-W8CCONFIRMEDREV-20261113.md` §2.1 ✓) and its
  `dropped` sequence was checked for monotonicity ✓.
- **No file of the other lane's edited** ✓ (the preregistration is `design/w8-*` = the hermes lane's ✓);
  no byte of `packages/hermes/**` ✓; nothing pushed ✓.

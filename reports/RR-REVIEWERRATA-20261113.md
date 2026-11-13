# RR-REVIEWERRATA-20261113 — the reviewer's verification of this lane's two cards: seven discrepancies checked one by one — **six confirmed and corrected, one not reproducible**, plus two additions of my own

Card: the reviewer checked `reports/RR-SHAPEGAP-20261113.md` and `reports/RR-W8DERRATUM-20261113.md`
against the code and the captures and raised seven discrepancies. Each was re-checked here against the
artefacts before anything was written down. **Six are confirmed** ✓ and the cards are corrected ✓;
**one is not reproducible as stated** ✓ (the table reproduces ✓ — the filter did not ✓); and **two
additions of my own** came out of the re-check ✓.

---

## 0. Verdict in one paragraph

Every substantive claim in both cards **reproduced** ✓ (the reviewer's own list of "verified exactly"
covers the decisive ones ✓). The seven discrepancies are **citation, label, and unit-precision faults** ✓ —
in a lane whose law is *"every number carries a repo locator + repro command"* ✓, a wrong section pointer
and an uncited capture are **defects** ✓, not trivia ✓ ⇒ they are corrected in the cards ✓ (cards are not
append-only ✓) and, where a **committed LOG row** carries the wrong string ✓, by an **append-only erratum
row** ✓ (never a rewrite ✓). ⇒ **No number, verdict, recommendation, or gate result changes** ✓✓.

---

## 1. The seven, with verdicts

| # | the reviewer's finding | verdict | what changes |
|---|---|---|---|
| 1 | §1.1's "no hits" is literally false ✓ | **CONFIRMED** ✓ | the card's grep sentence ✓; the substance stands ✓ |
| 2 | §3.1 cites `RR-W8CCONFIRMEDREV-20261112.md §2` ✓ | **CONFIRMED** ✓ | the citation ✓ (`RR-W8CREPLAY-20261112.md` §2 ✓, `:38` ✓) |
| 3 | the capture is plugin **0.13.21** ✓, not 0.13.22 ✓ | **CONFIRMED** ✓ | six labels across two cards ✓ + one LOG row ✓ |
| 4 | the "210,856" quote is `RR-SPEND-20261112.md` **§3** ✓, not §2 ✓ | **CONFIRMED** ✓ | the citation ✓ + one LOG row ✓ |
| 5 | "12 pages / 47,805" is cross-capture ✓ | **CONFIRMED IN PART** ✓ | every number in that table now names its capture ✓ + one LOG row ✓ |
| 6 | the row positions are off by one ✓ | **CONFIRMED IN SUBSTANCE** ✓ — but the reviewer's own spans are off too ✓ | the positions are now 1-based ✓ and correct ✓ (2–41 / 42–61 / 62–81 ✓) |
| 7 | the §4 per-turn table does not reproduce ✓ | **NOT CONFIRMED** ✓ — the table reproduces ✓; the **window** did not ✓ | both cards now carry the **exact filter + a repro script** ✓ |

---

## 2. The six confirmed, each with the corrected statement

### 2.1 "No hits" → the only `page.evict` strings are a reader and a comment ✓

The card said *"grep for `page.evict` in `packages/hermes/src/plugin.py` + `packages/hermes/live/`:
**no hits**"* ✓. The unescaped dot matches a **comment** at `packages/hermes/live/__init__.py:832` ✓
("Per-page eviction detail …" ✓), and over the whole package there are two more ✓ — in
`packages/hermes/src/uc2_forensics.py:255,257` ✓, which is a **trace reader** ✓ (it *queries* traces for
`page.evict` events ✓ — the forensics surface ✓).

⇒ **Corrected statement** ✓: *no `PageEvict` is ever constructed anywhere under `packages/hermes/`* ✓
(grep `PageEvict` → no hits ✓); the only `page.evict` **strings** are a reader ✓ and a comment ✓.
⇒ The substantive claim — *the hermes adapter never emits `page.evict`* ✓ — **stands** ✓.

### 2.2 §3.1's citation ✓

The card cited `reports/RR-W8CCONFIRMEDREV-20261112.md` §2 ✓. The file is
**`reports/RR-W8CCONFIRMEDREV-20261113.md`** ✓, and its §2 is about the `_selections.log` and the swallow
recorder ✓; the *"the eviction count is a **plugin-written** field"* qualifier is in
**`reports/RR-W8CREPLAY-20261112.md` §2 (:38)** ✓ ⇒ the citation now points there ✓.

### 2.3 The capture is plugin **0.13.21** ✓

The capture's **own sidecar** says so ✓: `local-d60a50c44acf…` → `plugin.version = 0.13.21` ✓,
`profile = w8cn-paged` ✓, `arm = paged` ✓, `engineSelections = 16` ✓, `evictedPagesCount = 9` ✓,
`callSizes = 16` ✓. The **0.13.22** sidecars in the trace dir are the reviewer's own sessions ✓
(`profile = default` ✓, `arm = control` ✓, `engineSelections = 0` ✓ — **two** of them ✓:
`local-6270c389…` ✓ and `local-7ebc530650…` ✓).

⇒ Both cards now say **0.13.21** ✓ (six labels ✓). ⇒ **One disagreement with another lane's card is
recorded, not adjudicated** ✓: `reports/RR-W8CCONFIRMEDREV-20261113.md` describes the same run as
*"plugin `0.13.22`"* ✓ — the repo's code is at 0.13.22 ✓ (`packages/hermes/live/__init__.py:94` ✓) but
the **installed** copy that wrote the capture reports **0.13.21** ✓ ⇒ the run's version is whatever the
installed copy was ✓ (the installed copy is the hermes lane's ✓ — this lane does not touch it ✓).

### 2.4 The "210,856" quote is in §3 ✓

`reports/RR-SPEND-20261112.md` line 45 ✓ sits under **§3** ✓ ("The review side's reading of cell-02's
limits" ✓) ⇒ the citation is corrected ✓.

### 2.5 Every number now names its capture ✓

The reviewer's point ✓ — the card's §1.4 table mixed the **free 0.13.21 capture's** page accounting ✓
(21 ✓ / 86,569 ✓ / 12 ✓ / 47,805 ✓ / 38,764 ✓) with the **paid cell-03 capture's** provider-receipt
ratios ✓ (0.563 ✓ etc.) without labelling either ✓.

⇒ **Corrected** ✓: the table carries a **capture column** ✓ ✓ and the text now states that the **paid**
capture's own `evictedTokens` sum is **275,362** ✓ (the free capture's is 210,856 ✓) and that its 0.13.1
sidecar carries **no `evictedPages`** ✓ ⇒ its unique-removed content is **not directly measurable** ✓ ⇒
the two captures have **different roles** ✓ (page accounting ✓ vs the falsifier ✓) and neither number
moves ✓.

⇒ **A unit addition this re-check produced** ✓ (see §4.1 ✓): "post-selection request" is the
**assembled message content** ✓ (`after` ✓), not the whole request ✓ — the static prefix is not in it ✓
and is not re-written ✓.

### 2.6 The row positions ✓

Confirmed in substance ✓: the card printed **0-based** positions ✓ while reading them as 1-based ✓. The
**1-based** spans of `local-d60a50c44…` are: the 40 page rows (**2–41** ✓), the 20 `turn.render` rows
(**42–61** ✓), the 20 `call.meta` rows (**62–81** ✓) — **81 rows** ✓, the replay's 81 events ✓.

⇒ The reviewer's own spans (**2–42 / 43–62 / 63–82** ✓) total **82** rows against a trace of **81** ✓,
so they carry the same off-by-one in the other direction ✓ ⇒ both cards now state the 1-based spans ✓.

---

## 3. The one that does **not** reproduce as stated — finding 7 ✓

The reviewer reports that the §4 per-turn table *(Σ 4,411 / 13,146 / 21,676 / … / 112,638 ✓ and the
per-call dropped counts ✓)* does not match the current `_selections.log` ✓, and that the log *"may derive
from a rotated-out cell-02"* ✓.

⇒ **The table reproduces ✓**, from the **current** log ✓:

```
$ grep -c . ~/.local/state/ctxvm/traces/_selections.log   # 321 lines now; 201 when the capture was read
$ # window 15:04:45..15:13:00 with budget=60000  ->  41 lines, all of them
  2026-11-13T15:04:45 arm=paged budget=60000 before=6009  after=6009  dropped=0 resident=0
  ...
  2026-11-13T15:13:00 arm=paged budget=60000 before=95360 after=56358 dropped=9 resident=86806
```

⇒ The failure mode is the **window** ✓, not the data ✓: the log is **append-only and shared** ✓ (the
plugin's own pytest suite writes into it ✓ — it grew **201 → 281 → 321 lines inside this session** ✓, so
it is being appended to live ✓),
so a window that returns **41–44** lines mis-pairs the selections against the sidecar's 41 `perApiRequest`
entries ✓ ⇒ the reviewer's 41–44 line window ✓ is exactly the artefact that breaks the pairing ✓.

⇒ **What changed in the cards** ✓: both now carry the **exact filter** ✓ (`budget=60000` ✓ and
`2026-11-13T15:04:45 ≤ ts ≤ 2026-11-13T15:13:00` ✓) and an **assert that the window yields 41 lines** ✓
plus the repro script ✓ — so the next reader cannot silently mis-pair ✓.

---

## 4. Two additions this re-check produced

### 4.1 The static prefix is not in `after` — and that is why the provider does not re-write it ✓

Measured on the 0.13.21 capture ✓: the engine's per-call `after` sits a **constant ≈ 4,230** apx4 tokens
below the harness's per-call `approxInputTokens` ✓ (all 41 selections ✓) ⇒ `after` is the **assembled
message content** ✓, and the **static prefix** (system prompt + tool schemas ✓) is **not** in it ✓.

⇒ Two consequences ✓: (a) the phrase *"post-selection request"* must be read as **message content** ✓ —
the right denominator for "what fraction of the 16 selections' worth of content was written" ✓ is
`sum(after)` ✓ ⇒ the 0.567 / 9⁄16 identity ✓ survives ✓; and (b) it explains the receipts ✓ — the static
prefix stays cached ✓, so the paged arm's collapsed cached prefix (14,504 ✓) **is** the static one ✓ ⇒
each rewrite re-wrote the **content** ✓ ⇒ the "whole post-selection request" model is a model about the
**content** ✓ ✓ (the erratum's own phrase is loose in the same way ✓ — now stated exactly ✓).

### 4.2 Only `PageEvict` schedules a **stub** ✓ — `PageFault` schedules `Full` ✓

The core schedules `RenderMode::Stub` in **exactly one place** ✓ — `Event::PageEvict` ✓
(`rust/crates/ctxvm-core/src/page_table.rs:194` ✓) — while `Event::PageFault` schedules
`RenderMode::Full` ✓ (re-materialisation ✓, `:237` ✓) ⇒ **no event can stub a page except `page.evict`**
✓ ⇒ "0 stubs is entailed by the event vocabulary" ✓ is exact ✓ (a fault can *un-stub* ✓, never stub ✓).

---

## 5. What does **not** change

- The falsifier's verdict ✓: the provider's receipts put the paged request at **0.563** of the control's at
  turn 19 ✓ ⇒ the model did not see all 21 pages ✓ ⇒ the removal measurement is right ✓ and the derived
  table is the false part ✓✓.
- The erratum's three arithmetic errors ✓ (denominator **42** ✓, the inverted ratio ✓, "16 rewrite events"
  unsupported ✓) and its model-check contradiction ✓ (9 whole-request writes fit ✓; 16 miss by 1.76× ✓).
- The refusal ✓, the hold-once no-op finding ✓, and the ask to the hermes lane ✓ (persist the per-call
  dropped identities ✓).
- The gate ✓ (`bash tools/run-ci.sh` → ALL GATES GREEN ✓, exit 0 ✓) and the kit ✓
  (`bash tools/check-handoff.sh` → ALL HANDOFF CHECKS PASS ✓).

⇒ **The committed LOG rows that carry the wrong strings are corrected by an append-only erratum row**
✓ (`RR-REVIEWERRATA-20261113-ERRATUM` ✓) — the rows themselves are **not** rewritten ✓.

---

## 6. Executed agent-doings

- All seven findings re-checked against the artefacts ✓: the grep ✓, the card filenames ✓, the sidecar's
  `plugin.version` ✓ and every 0.13.22 sidecar in the trace dir ✓, `RR-SPEND`'s section headings ✓, the
  capture labelling ✓, the 1-based row spans ✓ (81 rows ✓), and the `_selections.log` window ✓ (41 lines ✓).
- The core's stub-scheduling sites re-read ✓ (`page_table.rs:194` ✓, `:237` ✓) ⇒ addition §4.2 ✓.
- The engine-vs-harness size offset measured ✓ (a constant ≈ 4,230 apx4 tokens ✓ across all 41
  selections ✓) ⇒ addition §4.1 ✓.
- The cards corrected ✓ (six version labels ✓, three citations ✓, the grep sentence ✓, the capture column
  ✓, the 1-based spans ✓, two repro scripts ✓) and one **append-only** LOG erratum row appended ✓.
- No file of another lane's was edited ✓ (`packages/hermes/**` ✓ and `design/W8D-*` ✓ untouched ✓);
  nothing pushed ✓.

# RR-UNVERIFIED-20261119 — C task: the UNVERIFIED ledger re-checked, and the W8D rewrite mechanism confirmed on the current build

Review lane, verify-then-record. Date 2026-11-19. Every row below is a re-derivation from a live source, not a
restatement of `handoff/PROJECT-STATE.md` §Verification status. No code change, model call, spend or push.

## 1. The ledger, re-checked

| item (PROJECT-STATE locator) | re-check 2026-11-19 | status |
|---|---|---|
| XERJ Hub listing (`:48`) | fetched `https://hub.xerj.org/llms.txt` (696 lines, "Last updated: 2026-11-19", 566 corpora claimed); `grep -i 'ctxvm\|xcabi'` → **no hits** | **NOT LISTED** as of this date in the index named by PROJECT-STATE. Repro: `curl -fsSL https://hub.xerj.org/llms.txt \| grep -i 'ctxvm\|xcabi'`. The file itself names a registry of record (`xerj-org/xerj`, branch `corpus-hub`, `tools/xerj-code/hub`) — I checked the index, not that registry; D17 is held, so no submission was made or authorized |
| openai price row + cache-read nulls (`:48`) | `benchmarks/metrics/prices.json`: `providers.openai` has `usdPer1mInput: null`, `usdPer1mCachedRead: null`, `usdPer1mCacheWrite: null`, `verified: "unverified"`, source note: m1/m2 fixtures are **synthetic**, fill only from a provider price page with a locator | **CONFIRMED intentionally UNVERIFIED.** The nulls are correct, not missing work. Filling them requires a dated provider-page locator and a lane/owner decision — I did neither |
| Part II METR figures (`:48`) | located at `research/uncommitted/white-paper-Part-II_reviewed.md:182–183`: "Secondary reports of its 26 June 2026 evaluation of GPT-5.6 Sol give about 11 hours …" and a June 2025 post on reward hacking | **STILL UNVERIFIED** — secondary reports, no primary locator in the card. What would verify: the primary METR report with date and locator. `research/**` is read-never-edit for this lane; nothing edited |
| hard-fault recall ≥95 % (`:48`) | M0 gate is `hard_fault_recall ≥ 0.95` with a bootstrap 95 % CI lower bound (`RR-SUPPORT-20261030:42`), needing n ≥ 30 (`RR-W5-20261030:155`); the paging gate has n=4 under the new fault semantics (`RR-D17RULING-20261118:27`) | **UNMEASURED, n=4** — not a low score, an insufficient sample. What would verify: ≥30 ground-truth traces under the new fault semantics with the bootstrap lower bound. No new data was produced |

Net: one item moves from "UNVERIFIED, re-check needed" to a factual **NOT LISTED**; one is confirmed intentionally
null; two remain open because the evidence to close them does not exist on this machine. I do not promote either
open item to a claim.

## 2. W8D rewrite-event count — mechanism confirmed, historical count unchanged

PROJECT-STATE `:49` records "9 (billed volume) vs 16 (selections) — UNVERIFIED pending a paged capture on the current
build". That paged capture now exists (`RR-H12RESULT-20261119`, plugin 0.13.27). Reading the paged trace
`local-fc828608…jsonl` (20 `turn.render` events):

- `prefix.approxInputTokens` series: 10,806 → 15,677 → 20,215 → 24,638 → 24,491 → 24,776 → … → 22,574;
- **20 distinct prefix sizes across 20 turns, 19 prefix changes** — the prefix changes at every transition.

That is the mechanism the W8D erratum argued for on a different build and workload
(`RR-W8DERRATUM-20261113` §2.3): a rewrite event tracks a **change** in the dropped set, not the number of
dropping selections. Confirmed here on the current build with the current paged engine.

It does **not** re-derive the W8D numbers. W8D's 16 = dropping selections and 9 = distinct dropped-set sizes came
from a 0.13.21 free capture with a 41-line log window (`RR-W8DERRATUM-20261113` §2.3 repro); the H12 capture is
0.13.27, 20 turns, a different task shape. The historical 9-vs-16 distinction stands as previously recorded, and
the erratum's own caveat (nesting of dropped sets cannot be settled from the artefacts) is untouched. The line in
PROJECT-STATE can now say the mechanism is confirmed on the current build; I made that one-line edit in this commit.

## 3. Applied

This card, an append-only LOG row (four pipes), a day-file section, and the one-line PROJECT-STATE verification
status edit in §2. No `benchmarks/metrics/prices.json` byte, no `research/**` byte, no gate input, no push.

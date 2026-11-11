# QUESTIONS-ARCHIVE — answered packets, full summaries

The queue (`handoff/QUESTIONS.md`) is capped at 3,072 bytes, so answered rows are archived here
verbatim and the queue keeps a one-line pointer plus the verdict that matters. Nothing is deleted;
the answer detail is also in each packet's STATUS header and the RR named in the row.

## P1 — Cross-harness claim + RFC-0.1 normalisation proposal

**answered 2026-11-08**. Split the Pillar-1 sentence (replayable + conformance-testable kept; "diffable" behind the consumer-side profile; "reconstructs any turn" narrowed; absence claim reworded with scope); card `design/diff-normalisation.md` (N1 + N3 unit rule; OP-N2 open); `:635` + "same bytes"/echo sweep; paper edits via owner (D13 bundle). Full record: `RR-DIFFNORM-20261108`.

## P2 — `faultOfResidentPage` violation shown by the healthy-fixture demo

**answered 2026-11-08**. Demo keeps + ONE class-not-failure sentence ("healthy" = divergence-free, not violation-free); NOT "illustrative" (recomputed 2026-11-07); R1 3→0 contrast goes to the RFC-0.1 section. Verdict-3 locate DONE: seq 7 = `page.fault` turn 2, source `identifier_scan` (cause swap-in activates), target `tool:read_file({"path":"src/auth/session.ts"})` @ `sha256:d5bf10dd` — declared seq 2, rendered full seq 5, never evicted (`RR-P2DEMO-20261108`; byte-twin `50593d98…`). Sentences route via owner; `:333`/`:339`, working tree.

## P3 — Redaction block + default-capture decision

**answered 2026-11-08**. Keep capture default-on in owner-run builds; no registry release ships silent default-on — first-run notice minimum, opt-in stronger; consent plugin card bound at D6 (covers publish), D17 = timing. Author the redaction card proposal-only, sidecar-first: stage list (capture/flush/export) with policy id + rule-set version + replaced-field count, "absent = unknown", ref-policy entry (raw/keyed-hashed/dropped), and the block is an assertion without tamper evidence; keyed-hash emission deferred until a rule passes the golden vectors (consistent with `page_id` = `(logical_ref, content_hash)` minting within an artifact; breaks cross-drop joins and the N1 raw-ref diffs); falsifiers: seeded-canary recall; the no-docs user blind to the trace. Mend the consent paragraph (stored contents, discoverability, the 0700 limit) — replacement text in `RR-P3REDACT-20261109`; Part II cites the card id until the field name is ratified. Card: `design/redaction-block.md` (owner-cleared 2026-11-09).

## P4 — umpire `ts` (R4): consumer rule or additive mandate?

**answered 2026-11-09**. Verdict (a)+(c): leave `ts` optional in umpire ledgers and record ONE
ordering clause — within a ledger, line order governs, an absent `ts` means **unknown, never
zero**, and no order across ledgers/sessions is implied. Do NOT mandate: (b) works against D9
(default-ON `ts` with the `CTXVM_TRACE_TS=0` reproducibility opt-out — the frozen corpus carries
zero `ts` keys, so a regen under the default would mutate pinned bytes, AGENTS law 6), and the
sweep verified the structural half: RFC-0.1 makes `ts` optional (`:34`), all four umpire ledgers
are `schemaVersion: "0.1"`-stamped and carry no `ts` key, and a v0-only emitter could never
comply (v0 has no `ts`; unknown fields are hard errors). No 5-touchpoint card (`ts` already
exists in RFC-0.1). Both UNKNOWNs resolved: ledgers DO stamp `schemaVersion "0.1"` (5/5 grep
hits, fixtures + live ledger), and no current consumer orders events across sessions (W14 = the
per-environment key; the A5 analysis is a single everyday session, n=347; `latency_ms` rides the
records sidecar, not the ledger). Executed: the ordering clause DRAFTED in
`reports/RR-P4TS-20261109.md` as a PROPOSAL for `umpire/00-SPEC.md` §2 (after the L1–L5 block;
documentation-only, deliberately not validator-enforced so it cannot claim an L number), pending
owner approval + a fresh D-number — the A6 register's D-U1–D-U9 contain no ts candidate, so this
is a new decision, not a ratification. Falsifier: a consumer that must order events across
sessions and cannot — then revisit (b) as an emitter profile ("SHOULD emit `ts`") or evaluate the
per-session sequence number with the full five touchpoints.


## P5 — D-U1 calibration transfer: is n=180 enough?

**answered 2026-11-10**. Publish per-corpus calibration WITH the caveat; NO transfer claim until
a held-out corpus with several NEW label sets (the unit is the label set, not the row; fewer than
~5 would not convince) passes a PREREGISTERED equivalence test — margin ±2 points, Brier/log-loss
primary (ECE secondary: small-sample bin-occupancy bias), cross-fitting, cluster bootstrap
across sets. Sizing: from the existing-rows paired bootstrap half-width h, n ≈ 180 × (h/2)²
(h=4 → ~720; h=6 → ~1,620). "No detectable degradation" is not "no degradation": CIs include
zero, and the POINT estimates worsened (A1 7.5→12.2% ECE = +4.7, already above the 2-point
effect to exclude; A2 4.9→6.8% = +1.9). Caller sentence (proposed verbatim):
"Calibrated confidence was fitted on umpire's own label sets and has not been shown to transfer,
so treat it as an uncalibrated score for your labels until you check it on a sample of your own
labelled rows." Falsifier: held-out new-label-set evaluation where calibrated ECE exceeds raw by
more than the margin ⇒ never ship the transfer claim; equivalence inside the margin ⇒ ship it.
UNKNOWNs resolved by the books: the reviewer's assumed arm definitions = the design's exact
table (`design/W9-TRANSFER.md:36-38`: A0 baseline 4-label; A1 drops `other`; A2 drops `billing`);
n=180 = test ∪ validation amendment (`:103-105`; train excluded to protect the isotonic fit
`:109-110`); artifact `cal-precision-v3.json` = `umpire-calibration-precision/0.1`,
`cal-v1:057a5a35a9d4ec71`, bootstrap n=2000 seed 42, 10-bin ECE, test n=120, committed `47e0ee0`.
Rows-per-scope: per-scope rows beyond this one scope do not exist yet — why the transfer claim
cannot stand. Full: `reports/RR-P5CAL-20261110.md`.

## P6 — D-U3 determinism scope: same-build only or cross-machine?

**answered 2026-11-10**. KEEP the claim same-build (the D-U3 register's own option (a),
`design/umpire-design-choices.md:15-17`), do not expand; TIGHTEN the vocabulary instead of
softening to page-table-only: "deterministic" is not available even same-build (470/480 is not
480/480 until the ten non-strict rows are explained by test, not assumption) — say
"**replay-reproducible with 10 documented exceptions**" (law 8 supports it). Page-table-only is
the wrong softening FOR UMPIRE: that scoping belongs to the ctxvm core; the umpire split is
identity (480/480) vs strict output (470/480), stated together. Needs: one run of the same 480
rows on the same build at concurrency 1 — quiescent recapture of the suspect band — with the ten
exceptions classified (concurrency / numerical order / other). Falsifier (both directions): if
the non-strict rows persist at concurrency 1 the cause is intrinsic to the build and the claim
stays 470/480; if they recapture clean the ten become documented capture-side exceptions.

**Cross-machine machine set** (preregistered before run): same container image digest, same model
weights, fixed decoding; ≥2 hardware configurations differing in CPU microarchitecture or
instruction set (and GPU if any); ≥1 different host OS or kernel; axes to vary: hash seed, thread
count, concurrency; full 480 rows per configuration; the pass rule preregistered (strict equality
with the baseline on every row except the documented exceptions). It proves only the factors
varied — never "any machine". Cross-build is a separate axis: expect non-strict equality; REPORT
IDENTITY there and measure the strict rate.

**Claimable today (PROPOSAL, verbatim):** "On one machine and one build, replaying the 480-row
corpus reproduced 470 rows exactly and all 480 by identity; reproducibility across machines or
builds has not been measured, and no claim is made about model-output determinism in general."
The identity claim stays separate from RR-IMPL2 (the minting second-implementation result,
"byte-identical Python↔TS … minting layer only", `RR-IMPL2-20261109:100`).

**UNKNOWNs resolved from the books:** strict/identity definitions were the reviewer's exact
assumption — `RR-M3FULL-20261024.md:19-23` (strict ok = every field incl. contentHash +
probabilities = 470/480; identity_ok = ref+key+model_pin = 480/480); what is replayed = the full
480-row M3 corpus via `harness/replay_audit.py --corpus calibration/corpus-v2.jsonl` (`:9`);
local-vs-hosted = DECIDED local-only by T14 (`RR-T14-20261023.md`; register D-U4: pinned
llama-server + model files only (current); a hosted redeploy is an option NOT taken — so
provider-side machine claims are out of scope from this side). The concurrency attribution is
recorded but NOT yet proven: `RR-M3FULL:72-97` (co-traffic window; 7/10 suspect rows
latency-elevated; other slow episodes never diverged; the 10-row quiescent rerun reproduced
10/10 distribution-only, proving replay-path stability), with the decisive quiescent-recapture
run still to be made. `spec/determinism.py` + `tools/determinism-matrix.sh` exist, unevidenced on
cross-machine. Full: `reports/RR-P6DET-20261110.md`.

## Errata (2026-11-10): QUESTIONS.md row compaction for the 3,072 B cap

The P4, P5 and P6 chart rows grew past the cap when P6's answer landed
(3,759 > 3,072; P4's row was 1,102 B of it).

A second pass (2026-11-10, P7 close): the P7 chart row was written large (1,289 B) and
pushed QUESTIONS.md to 3,892 — it compacted to the pointer form the same way, with 47+ B
left under the cap. The full P7 verdicts live in the `A third and fourth shave in the same pass: the P7 row compacted again, the statuses line, the
queue-law paragraph and the standing-questions closing sentence trimmed (wording only: the
reviewer's answer-summary rule and 'a change that cannot answer (1) or (2) from repo evidence
is not ready for review' restated here once — no fact dropped), the P1 chart row compacted the
same way (full P1–P3 section intact above; 'N3 turn unit' lost no ground — it is D13/RR-DIFFNORM
detail retained in the section), and stray typographic quotes/dashes normalised. No fact
dropped from any compaction; every removed word survives in the sections above this note or in
the cited RR cards.


Fifth pass (2026-11-11, the umpire-gates card): the P4/P5/P6/P7 chart rows compacted once more to
pointers so the P10 row (QUEUED 2026-11-11 - the page-id asymmetry ruling, whose full text is the packet
file `handoff/packets/P10-page-id-asymmetry.md`, not a section here) fits the cap. Every fact removed from
a chart row survives in that packet's own section above and in the cited RR cards; the cap is the only
reason a row is a pointer.


Sixth pass (2026-11-11, the umpire-residue card): the P1/P2/P3 chart rows compacted to
pointers as well, so the P11 row (QUEUED 2026-11-11 - canonical ordering; whose full text is the
packet file `handoff/packets/P11-canonical-order.md`) fits the cap. Nothing was rewritten in the
sections above: every fact dropped from a chart row survives in its own section and in the cited RR
card. The chart now runs at 3,055/3,072 B - the cap, not the content, is the binding constraint on
new queue rows.

## P7 —` section above.

A third shave in the same pass: the statuses line, the queue-law paragraph and the
standing-questions closing sentence trimmed (wording only, no fact dropped — the replaced
sentences' full meaning is boilerplate, restated here once: the reviewer's answer-summary
rule, and 'a change that cannot answer (1) or (2) from repo evidence is not ready for
review'). Their verdict texts COMPACTED to pointers — every fact retained here in the
full P4/P5/P6 sections above; nothing recorded was rewritten or lost. Committed-row law intact:
the LOG keeps the claims; this chart just points.

## P7 — D-U2 baselines: which one must run before a claim ships?

**answered 2026-11-10**. Run TWO cheap baselines FIRST (both zero model spend), never all four:
majority-class + ONE cheap learned baseline — and WHICH learned one depends on the claim:
**logistic regression on embeddings** for the corpus-accuracy claim AND the calibration claim
(logistic is usually well calibrated unaided; if its ECE lands at/below the calibrated 0.0302 the
calibration layer's marginal value is small and its wording moves to "makes confidence
interpretable for an uncalibrated LLM," not "better calibration"); **zero-shot embedding
similarity between text and label names** for caller-labels claims (a fixed-label classifier
cannot take a new label set — like-for-like only on the corpus's own labels). LATER, not first:
the stronger model (structured output + logprobs) only before a product/accuracy-leadership claim
AND only with a spend packet; the small fine-tuned classifier answers a different question (is
the LLM needed given labelled data?) — DEFERRED. Falsifier: if baseline results change when the
preprocessing changes (tokenisation, embedding model, label wording), the comparison is not
stable enough to carry a positioning claim.

**Same-split protocol (PROPOSAL, verbatim):** "Every baseline trains or fits on the same fit
rows, is calibrated by the same procedure on the same calibration rows, is scored on the same 120
test rows for accuracy, Brier, and ECE with paired bootstrap CIs, and reports cost and latency
per row, with the comparison margin preregistered." At n=120, 0.7083 accuracy (85/120) has a
≈8-point half-width (artifact CI [0.625, 0.791667]); paired comparisons shrink it, but differences
under ~5 points stay unresolved — conclusions are "clearly better," "clearly worse," or
"indistinguishable at this n," always "on umpire's corpus."

**Positioning outcomes preregistered (proposals):** (a) cheap baseline matches/beats 0.7083 within
CI at near-zero cost/latency ⇒ value = ledger + determinism scope + audit trail ⇒ "demo of xCABI"
over product; (b) every cheap baseline clearly worse beyond the paired CI ⇒ the accuracy case for
the LLM path stands; (c) logistic ECE ≤ 0.0302 already ⇒ the calibration layer's marginal value is
small ⇒ the claim's own wording recalibrates; (d) stronger model much more accurate at acceptable
cost ⇒ the 1.7B needs cost/latency/local justification ⇒ "cheap and local"; (e) zero-shot
embeddings clearly fail on new label sets ⇒ caller-owned-labels = genuine differentiator.

**UNKNOWNs resolved from the books:** label space = FOUR (`billing/other/sales/technical`, 480
examples at 120/label — `reports/LOG.md:14` RR-M2V2; `W9-TRANSFER.md:36` names the four); splits
= **240 fit / 120 calibration (validation, selects isotonic vs temperature) / 120 test**
(`RR-M2V2` "240/120/120 split, test n=120"; `RR-M3V3:51` "Test split (n=120, untouched)");
labels remain caller-supplied per decision call (the MCP decide contract takes labels each
invocation; caller-owned sets are the W9 feature). ECE-claim numbers verified in the artifact
(cal-precision-v3.json: accuracy point 0.708333 CI [0.625, 0.791667]; ece_calibrated point
0.030163).

**ERRATUM carried (P6 committed card):** the P6 recording said the concurrency-1 classification
run "has not been run" — FALSE per `RR-M3V3-20261024` (the quiescent FULL 480 recapture,
6,060.5 s, zero MCP decide writes, 10 rows relaxed to replay-path values with 5/4/1 splits,
capture-time page-table byte-identical ⇒ **capture-time-concurrency attribution CONFIRMED**).
P6's falsifier therefore RESOLVED recapture-clean; Roadmap U4 ticks with `RR-M3V3` as its
locator; the P6 vocabulary line stays a PROPOSAL (owner-gated). Full: `reports/RR-P7BASE-20261110.md`.

## P8 — cache-stable selection: can residency be bounded without forfeiting the prefix cache?

**answered 2026-11-11** (the reviewer's footer says 2026-11-09, the packet's own date; the answer
reached the kit on 2026-11-11). Packet-only answer plus one stated assumption (read price $0.01/1M
"taken from the ledger"). Full record: `reports/RR-P8CACHE-20261111.md`.

**Q1 — ranking ADOPTED, with (d) amended.** (1) Watermark compaction (evict once on a trigger, hold
the set) is the candidate, valid only above break-even — and it is already the shape the in-tree
design card specifies (`design/w8-cache-stable-selection.md` §3, parts 2–4: hold the resident set
byte-for-byte until a trigger; batch-gated eviction on the B-th turn, single-pass purge; append-only
growth) with a four-condition acceptance gate (parsed-equal artefact; per-call prefix ≤ 24,000;
`prefixHash` unchanged between triggers; cache-write below naive with cache-read above) — the
preregistration the reviewer's falsifier asks for. (2) **(d) amended**: it may gate a COMPACTION, but
it cannot promise "no worse than control" — the measured no-op arm (9 selections, **0 evictions**)
cost **$0.0765 against naive $0.0175 = 4.4×** (`RR-NOOP-20261109`), because the cost tracks session
growth and output volume ("the paged arm rewrote the prefix 14 times, and it also emitted 6.5× the
output"), not selection. (3) (c) confirmed as "a policy of not evicting": the keep law protects
first-3 + last-6 turns, so on a one-turn session the floor is the whole request at any budget
(`RR-NOOP` §2) and the middle appears only at turn 9 on a 12-turn session (`W8-CLOSURE` §3). The
reviewer's own falsifier is adopted verbatim — and its second condition ("a byte-preserving no-op
still costs more than control") is **already met by the books**.

**TWO NUMBER CORRECTIONS.** (i) **w/r = 10.0, not 12.5**: the owner's price catalogue
(`benchmarks/metrics/prices.json`, catalogue row-013 — GPT-6 Luna) gives input $0.10/1M, output
$0.50/1M, cached read $0.01/1M and **no cache-write row** (writes bill at input); the design card's
decomposition reproduces both reported costs to the dollar (naive input-side $0.013167 of $0.0175;
paged $0.098227 of $0.1264). So the reviewer's 62 / 25 / 125 calls become **50 / 20 / 100**.
(ii) **The evictable share is 5.3 % session-weighted** (25,404 of 479,076 request tokens,
`RR-W8SIM` §2) — the reviewer's 12 % is the same quantity measured at the last request, which the
books reconcile explicitly. At 5.3 % with w/r = 10 the break-even is **n\* ≈ 189 calls**, not ~100,
against 5–30 measured calls.

**The packet's inconsistency, resolved.** "Selection removes nothing and adds churn" — the no-op IS
byte-identical: `RR-W8NOOPBYTES` (three cases, all pass: floor above budget; far under budget;
eviction happening; in both no-op cases the assembled list is byte-identical to the input — "the
property the cache depends on"; nothing mutated in place; 28 pytest passed). So churn is not a
selection artefact: the prefix grows because the SESSION grows (one turn, 50 tool results, 63,713
tokens; peak 63,246 vs naive 59,793) while the keep law protects all of it. The cause of the
cache-write volume stays **UNKNOWN** (`RR-W8CACHE` H3).

**Q2 — the metric-replacement rule is ADOPTED as a standing lane rule** (five conditions: the
hypothesis changed; a dated deviation whose reason does not reference the observed direction; new
cells under a new preregistration only, existing cells never re-scored; both metrics with equal
prominence; the symmetry test). The existing pair stays under tokens (NTR = −2.14 recorded); the
replacement run registers evicted tokens + parsed-equal, not dollars, on an unpaid model whose
catalogue row has **no cache price** (`design/W8B-FREE-PLAN.md`) — so there is no cache economics to
break even against, and **no cost-saving claim is made** (law 7).

**Q3 — already executed, one day earlier.** `design/W8-CLOSURE-20261110.md`: "Decision: **Option A**
from `design/W8-DECISION-20261110.md` (packet P9). W8 is closed with the negative result below. No
further paid cells. The replacement run is `design/W8B-FREE-PLAN.md`." The reviewer's remaining
instruction (a separate single-cell preregistration, after the no-op byte check and only if the
break-even arithmetic can pay back) is half-satisfied — the no-op check passes — and half-unreachable
on the measured shape (n\* ≈ 189 calls vs 5–30). No paid cache-stable cell is justified by the books'
numbers as they stand; the next step is owner-routed.

**UNKNOWNs after the sweep.** Provider cache TTL / minimum block size: still UNVERIFIED, and the
books say why (`RR-W8CACHE` H2: "not recorded in the capture, and I will not assert one from
memory"). Shared-plugin routing: partly answered — arms are separated by profile invocation and by
nothing in the trace — with the residual open in `RR-W8CACHE` H3. The true remaining cap: already
UNKNOWN in the books ("remaining cap UNKNOWN (exports missing for 11-07 and 11-09)";
`RR-SPEND-RECON2`). Whether the compaction engine exists: **RESOLVED — it does not**;
`selectionMode` / `residentSet` / `lastSelectionHash` / `prefixHash` appear only in the design card
and its LOG row, nowhere in `packages/hermes/live/`.

## Errata (2026-11-11, seventh pass): QUESTIONS.md row compaction for the 3,072 B cap

The P8 row (QUEUED→ANSWERED, 2026-11-11) needed ~250 B the chart did not have, so the P1–P7, P10 and
P11 rows were compacted to pointers once more. Every fact removed from a chart row survives in its
own section above or in the cited RR card; no heading was touched; the cap, not the content, is the
binding constraint.

## P9 — close W8 with a negative result, or buy one mechanism test?

**answered 2026-11-10** (owner chose **A**; the reviewer confirmed A independently on 2026-11-11 —
an independent confirmation, not a new decision). Full record: `reports/RR-P9CLOSE-20261111.md`.

**Why A, in the books' terms:** at most **5.3 %** of request tokens can ever be evicted (25,404 of
479,076 — the per-turn table runs 0.0 % for turns 1–8, 7.5 % at turn 9, 12.7 % at turn 10, 17.2 % at
turn 11; `RR-W8SIM` §2), and the reviewer's earlier "at most 12 % of the end-of-session resident" is
the same quantity measured at the last request, which the books reconcile explicitly. 4–6 paired
cells cannot resolve an effect that size, so B would buy a demonstration of eviction and nothing else.
Re-opening conditions: no condition on this task shape fixes it — the shape needs a much longer
session with enough unprotected middle pages, sized with P8's break-even arithmetic, and any new test
is a fresh preregistration, not W8.

**The four closure-text corrections, checked against the artefacts (not applied on trust):**

1. *"The closure must state plainly that items 3 and 4 conflict, and must not repeat 'selection
   rewrites the prefix' as the explanation."* — **the closure already complies.** Item 5: "The extra
   cache writes are not explained by the engine's message list. The request series is strictly
   append-only with a byte-constant system prompt, and a unit test shows byte-identical no-op output
   (`RR-W8CACHE`, `RR-W8NOOPBYTES`). Cause **UNKNOWN**"; the not-claimed list ends with "A cause for
   the cache-write volume"; the file carries no "forfeits the cache" / "rewrites the prefix" phrasing.
   The stale phrasing lives in `design/w8-cache-stable-selection.md` §1 ("the paged arm rewrote the
   prefix 14 times") and its LOG row `RR-CACHEDESIGN-20261109` — **another lane's plan of record, so
   routed to its owner as an appended erratum, not edited here**; the books had already made the
   correction (`RR-W8CACHE` §4: "The inference was reasonable and the data does not support it").
2. *"A zero-spend check can narrow it: the provider export has per-request cache columns, and the
   gateway logs may carry timestamps."* — **checked at the artefacts: the export does not.**
   `experiments/usage-day-summary-a93f8b06-2026-11-10.csv` is a per-day, per-key AGGREGATE (header
   `date, credit_source, product, model, key, tool_action, user, requests, input_tokens,
   output_tokens, cache_read_tokens, cache_write_tokens, debited_usd, credited_usd, net_usd`; 17 data
   rows) — no per-request rows, no timestamps. And the narrowing check was **already run**: the gaps
   in `w8-cell-01` are ~18 s (09:43:34 → 09:47:07 for 29 requests), far below any plausible lifetime,
   and the lifetime is not recorded — so **H2 NOT TESTABLE**, while **H1 NOT SUPPORTED** (the request
   is append-only, the system prompt constant, the no-op byte-identical) ⇒ **H3: UNKNOWN cause**, with
   two candidates left open (provider accounting — an export checkpoint counted as a whole-prefix
   write; session-boundary effects — twelve `hermes chat` invocations, each opening a cold prefix if
   the cache key includes something outside the text). The reviewer's "mark it UNVERIFIED until
   someone sources the lifetime" is the books' own state. The zero-spend proposals the books offer
   instead: record per-request `cache_read`/`cache_write`/`prefixHash` in the coverage sidecar; one
   back-to-back probe on the same prefix and diff the export's `cache_write` for that key; fix
   `providerUsage.inputTokens`.
3. *"Write the closure as 'at least $9.16, true total unknown'."* — **keep the closure's own
   three-part wording**: "spend **>= $7.14 billed on 2026-11-10 alone**; store estimate **$9.16 over
   three days**; remaining cap **UNKNOWN** (exports missing for 11-07 and 11-09)". "At least $9.16"
   would promote a store ESTIMATE to a floor — a stronger claim than the books support. The exports
   are still missing (`experiments/` holds exactly one CSV), so the cap stays UNKNOWN.
4. *"State the weaker claim only."* — **the closure already does**: item 3 (the shape caps the effect
   at 5.3 %), item 4 ("No cost saving was measured, and the one measured pair cost more"), item 5
   (cause UNKNOWN), plus the not-claimed list (no cost saving; no equivalence or non-inferiority
   statement; no generalisation beyond task/model (gpt-6-luna)/surface (`file`)/host; no cause for the
   cache-write volume). The reviewer's one-line form is compatible and may be adopted as a summary.

**The reviewer's UNKNOWN answered from the books:** the replacement run in `design/W8B-FREE-PLAN.md` is
an UNPAID-model run (nemotron / nemotron-lightning:free / longcat), budget 70,000, shape changed
12 → 20 parts so the unprotected middle reaches ~21k evictable (≈ 23 % of the peak), claims
descriptive only — and its catalogue row has **no cache price**, so it cannot measure cache economics
at all. It is therefore **not a substitute** for a longer-session variant: the free plan asks "can
eviction happen at all on a multi-part shape, at zero spend?"; only a longer-session variant on the
paid model could speak to the cache question, and it would need (i) a session long enough for the P8
break-even (n\* ≈ 189 calls at the 5.3 % ceiling; ≈ 43 calls even at the free plan's 23 %-of-peak
middle, against a 14–29 call session), (ii) the cache lifetime sourced, (iii) per-request cache
attribution recorded. Live state: the free run produced **NO RECORD** (`RR-W8B2-20261111`: both arms,
`nous/longcat-2.5:free`, prompt-1 timeout at 120 s, $0.0000) — neither variant has data today.

## Errata (2026-11-11, eighth pass): QUESTIONS.md row compaction for the 3,072 B cap

The P9 row (ANSWERED 2026-11-10, per the reviewer's request) needed room the chart did not have, so
the P1–P8, P10 and P11 rows were compacted to pointers once more and the queue-law/statuses prose
shortened. Every fact removed from a chart row survives in its own section above or in the cited RR
card; no heading was touched. The chart now carries all eleven packets (P1–P11) at 2,961/3,072 B.

## P10 — page-id asymmetry: flat vs nested page identity, and whether the second-consumer trigger fired

**answered 2026-11-11**. Ruling: **(b) with (a)'s prose docs — ONE RFC-0.1 compatibility-note line,
no field.** Full record: `reports/RR-P10ID-20261111.md`.

**The rule, verbatim, and VERIFIED against both schemas:** "Read a page's identity from
`page.id.logicalRef` and `page.id.contentHash` when the event type is `page.declare`, and from
`page.logicalRef` and `page.contentHash` for every other page-carrying verb; dispatch on event type,
never on which fields happen to be present." The sealed v0 schema says exactly this:
`spec/rfc-0/x-cabi.schema-v0.json` — `page.declare.page` → `$defs/pageRef` = `{id: pageId{logicalRef,
contentHash}, kind, tokens}` (nested) while `page.render`, `page.evict`, `page.fault`, `page.pin`,
`page.unpin` → `$defs/pageId` = `{logicalRef, contentHash}` (flat); RFC-0.1 leaves the shapes and the
nine verbs untouched. **No verb carries both shapes**, so the reviewer's falsifier "a verb that
legitimately carries both shapes" is currently empty. The last clause matters and both in-repo
consumers already comply: `packages/ai-sdk/src/resume-brief.ts:153-156` checks
`event.type !== "page.evict"` **before** reading the flat shape, and
`~/Documents/umpire/spec/ledger_tools.py:85` dispatches on `etype == "page.fault"` — though umpire's
branch is *profile-specific* ("not page.fault ⇒ nested" is right only inside its two-verb profile), so
the note must state the general rule.

**Why (c) is out — for the stronger reason the reviewer gave.** The asymmetry lives in the SEALED v0
schema, and sealed v0 traces exist that will not change, so every consumer of them must keep the
type-dispatch rule forever; a field would add a THIRD shape without removing either old one. (d) is
out because a third consumer would find the rule only in code comments; (a) alone is weaker than (b)
because a workaround in two repos does not tell a new implementer the rule exists.

**The reviewer's UNKNOWNs, resolved from the books:** (i) `schemaVersion` is declared on the
`session.open` line ONLY and is optional ("A trace MAY declare `schemaVersion: \"0.1\"` on its
`session.open` line", `spec/rfc-0.1/RFC-0.1-xCABI.md:8`) — so their "if every v0.1 line carried
schemaVersion" premise is false; (ii) a **D-number** is required (RFC-0.1's own status line: "Applied
(D4 approved 2026-10-30)"), and the landing site is already sanctioned by that document's scope line
("new files under `spec/rfc-0.1/` only") — so the note can be a NEW file under `spec/rfc-0.1/`,
touching neither the sealed `spec/rfc-0/` nor the existing RFC text; (iii) a conformance vector is a
**fixture**, not a spec edit — the vectors live in `rust/crates/ctxvm-conformance/vectors/`
(`events-v0.jsonl`, `events-v0-1.jsonl`, `session-clean.jsonl`, `session-divergent.jsonl`) — with the
caveat that it changes the conformance-suite totals the CI prints. Still open: a v0-only consumer
outside these repos (not exhaustable locally).

**Falsifiers adopted verbatim** (any one changes the ruling): a valid v0 or v0.1 line where the
type-dispatch rule gives the wrong identity; a verb that legitimately carries both shapes; a new verb
proposed with a third shape (a v0.2 design question, where (c) would deserve a hearing); a reported
consumer, outside these repos, that cannot dispatch on event type.

**ERRATUM on this lane's P10 framing (appended block on `reports/RR-UGATE-20261111.md`):** the
blast-radius argument for (c) was overstated. A strict v0 consumer already rejects a v0.1 trace at its
`session.open` line (measured: the sealed v0 validator rejects the umpire ab-demo ledger with 4
failures — lines 1, 3, 4, 6), so a `page.declare` field does not newly break v0-only readers of v0.1
data; the marginal costs are (i) every v0.1-aware consumer must be updated (strict allowlist), (ii)
two sources of identity per line, (iii) a consistency rule between them. The ruling is unchanged; the
reasoning is corrected. The packet's own Evidence prose was condensed to fit the packet's 3,072 B cap
(full text in the card).

**Not done, owner-gated:** the note file, the D-number, and the conformance vector (one line per
shape plus a negative: a `page.declare` carrying a flat `page.logicalRef`, which a sniffing reader
would accept and the validator must reject). This lane writes no spec, schema or vector byte.

## P11 — canonical ordering: sorted keys vs Rust struct order, and who owns the compatibility line

**answered 2026-11-11** (two passes: the reviewer's first answer, then a re-check against the cards
that landed the same day — `RR-UMRES`, `RR-UGATE`, `RR-P10ID`). Full record:
`reports/RR-P11CANON-20261111.md`.

**Ruling: (c) as the owner, with (a) as a short POINTER to it — and the ORDER matters: WRITE THE
CONFORMANCE TEST FIRST; the note can then state a fact the test enforces.** Because F9 is currently a
claim nobody can falsify (the packet's Evidence 5: no test shows a sorted-keys line and a struct-order
line derive the same page table) — "a note without the test records a belief". **Ownership: the test
belongs to ctxvm**, because ctxvm's replay is what makes the acceptance claim; umpire's `00-SPEC.md`
(option (b)) can mention it but cannot own it. (d) is out, for the reason given in P10 — a third
consumer will hit this.

**What the test must assert, in order of strength (all three should pass; a failure at any level says
what broke): (1) same parsed model** — one event set serialised in sorted-key order and in struct order
parses to equal models; **(2) same derived page table** — replay both files, page tables equal field by
field; **(3) same report** — `ctxvm replay` output, including divergences and violations, identical.
**Never byte-identical lines** (the byte forms differ by construction — `ts` rides last). Include a
trace WITH `ts` and one WITHOUT, because the sorted form puts `ts` before `type` and that is the case
most likely to expose a bug. **It lives in BOTH places**: a vector pair (the same trace in both orders,
with the expected report) in the conformance vectors so any other implementation can run it, AND a
Rust unit test that parses the pair.

**The note's line, if (a) is done, is a COMPATIBILITY STATEMENT ONLY** (verbatim): "Key order within an
event is not significant to parsing or replay: events written in sorted-key order and in the emitter's
field order are accepted equally; the codec remains strict about unknown fields." The last clause stops
the note from implying anything new is accepted, and the claim stays about parsing and replay — not
hashing — "if one [a digest] is computed over serialised bytes, key order matters for it, and the note
must say so".

**Two UNKNOWNs resolved from the books.** (i) `ts` coverage: `events-v0-1.jsonl` **carries `ts` on 6
lines** (the v0 vector and both session vectors carry none) — so ts-bearing material exists, but only
one byte form per event, and the discriminating PAIR still has to be built. (ii) **A vector is a
FIXTURE, not a spec edit**: the vectors live in `rust/crates/ctxvm-conformance/vectors/`, outside
`spec/` — so the pair can be added without touching any spec byte (with the caveat that it changes the
conformance-suite totals the CI prints). And the note's route: **a D-number** (RFC-0.1's status line:
"Applied (D4 approved 2026-10-30)") and a **new file under `spec/rfc-0.1/`** (its scope line: "new
files under `spec/rfc-0.1/` only") — the reviewer's suggestion to bundle the P10 type-dispatch line and
this line as TWO lines in ONE new file under ONE D-number is adopted.

**The reviewer's premise corrected.** "RR-IMPL2 reports no TS-to-Python byte comparison" — there **IS**
one: `RR-W7-20261029.md` §4 ("umpire committed fixtures re-minted: 17 records, mismatches=0"), with the
scope caveats printed beside it: "**ASCII-only** per umpire §2, **floats banned**, labels sorted-unique
by umpire's law", and the verdict line "byte-compatible, **NOT an independent implementation**" (the
Python side declares itself a mirror of `packages/node/src/ident.ts`). So the assertion is well-aimed —
it is precisely the ASCII-only, float-free scope that leaves their case untested — but the comparison
exists and is recorded.

**The reviewer's hash-input inference, narrowed.** "Identity hashes are computed over canonical JSON"
is only partly true: umpire's `content_hash`/`response_hash` hash the content **string** directly; only
the REF's truncation digest (`decide_ref` → `hex8(canonical)` on the canonical args) is over canonical
JSON. So the note's "hash input" scope is the canonical-args/ref digest, not content identity.

**Two divergences MEASURED today (zero spend), which is why the note cannot merely say "byte-for-byte
across languages".** umpire's Python `canonical_json` (`json.dumps(sort_keys=True, separators=(",",":"),
ensure_ascii=False)`) vs ctxvm's TS `canonicalJson` (`packages/node/src/ident.ts:16-21`):

```
ascii      IDENTICAL      nonascii   IDENTICAL      nested     IDENTICAL
astral     *** DIFFER ***  py {"a":3,"�":1,"😀":2}   node {"a":3,"😀":2,"�":1}
```

Astral-plane KEY names order differently (Python sorts by code point, JS's default sort by UTF-16 code
unit) ⇒ different canonical bytes ⇒ different digest, silently; the VALUE side is fine, so
`ensure_ascii=False` alone does not make the two equivalent. And number TEXT forms diverge in four of
six cases: `1.0`→"1.0"/"1", `1e16`→"1e+16"/"10000000000000000", `1e-7`→"1e-07"/"1e-7", and a big
integer past 2^53 loses precision in JS ("12345678901234567890" vs "12345678901234567000"); `1e+30` and
`0.30000000000000004` agree. So the reviewer's third falsifier — "any digest or chain computed over
serialised bytes" — **is TRIGGERED**: umpire's ref digest is exactly that, so the note needs a
normative canonical form FOR HASH INPUTS ONLY, which in turn requires choosing the ordering (code
point vs UTF-16) and the number encoding.

**Duplicate keys, measured.** The v0.1 validator **accepts** a line with a duplicated key ("OK: all
checks passed", exit 0) and no duplicate-key check exists in the codec or either validator;
serde_json, Python `json` and `JSON.parse` all take the LAST value — uniform by accident, specified
nowhere. The reviewer's "number-format" UNKNOWN is now the measured matrix above; both items remain
ruleless, and the test should include one numeric case.

**Falsifiers adopted (any one changes the ruling):** a pair of lines in the two orders whose parsed
models differ; differing page tables or replay reports; any digest or chain computed over serialised
bytes (TRIGGERED — see above); a consumer relying on key order to dispatch.

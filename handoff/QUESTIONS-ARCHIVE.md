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

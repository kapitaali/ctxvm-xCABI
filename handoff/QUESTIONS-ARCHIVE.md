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
(3,759 > 3,072; P4's row was 1,102 B of it). Their verdict texts COMPACTED to pointers — every fact retained here in the
full P4/P5/P6 sections above; nothing recorded was rewritten or lost. Committed-row law intact:
the LOG keeps the claims; this chart just points.

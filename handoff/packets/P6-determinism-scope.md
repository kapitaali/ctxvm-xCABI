# Packet P6: D-U3 determinism scope — same-build only or cross-machine?
STATUS: answered 2026-11-10 (verdict in handoff/QUESTIONS.md; full record reports/RR-P6DET-20261110.md:
keep same-build (D-U3 register option (a)); tighten vocabulary to "replay-reproducible with 10
documented exceptions" — no raw "deterministic", no page-table softening for umpire; the ten
exceptions classify at a quiescent (concurrency-1) recapture before any stronger wording; the
cross-machine matrix is preregistered-before-run (pinned image+weights, ≥2 hardware configs,
OS variation, axes hash seed/threads/concurrency); cross-build reports identity only; both packet
UNKNOWNs resolved from the books (RR-M3FULL:19-23 tables; local-only serving via T14/D-U4).

Date: 2026-11-09. Requester: A6. Related decision: D-U3.

## Question (one specific question)

Current claim: 470/480 strict, one machine/one build; cross-machine/build UNMEASURED. Should the claim stay same-build, expand to cross-machine, or soften to page-table-only?

## Excerpt or diff (only the relevant lines, with file path and line range)

umpire `00-SPEC.md:210,219`: "Full 480-row audit: 470/480 strict"; "cross-machine/cross-build determinism is not claimed". `spec/determinism.py` + `tools/determinism-matrix.sh` exist (host + hash-seed + container).

## Constraints (what must not change)

No "deterministic" without scope (law 8). No model-output determinism claim.

## Evidence (numbers with the command that produced them; UNVERIFIED marked)

`python3 harness/replay_audit.py --corpus calibration/corpus-v2.jsonl ...` → 470/480 strict, identity 480/480 (RR-M3FULL). Matrix not run cross-machine in this card (UNVERIFIED).

## Output wanted (numbered verdicts, one line each; rewrites only if asked)

1. Keep / expand / soften?
2. What machine set proves it?
3. What may be claimed today in one sentence?

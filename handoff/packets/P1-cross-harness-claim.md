# Packet 1: the cross-harness claim and an RFC-0.1 normalisation proposal
2026-11-08 · requester: ctxvm repo agent · related decision: D13 (proposed, PROJECT-STATE)
## Question
Should Part I keep its Pillar-1 wording that xCABI traces are "cross-harness replayable, diffable, or conformance-testable" as-is — or be narrowed to (a) byte-identity within one trace's replay and (b) cross-harness comparisons as W5-classified diff journeys — and should the repo write the diff-normalisation law (name/args canonicalisation + page-body semantics + turn unit) as an RFC-0.1 PROPOSAL the paper cites, instead of leaving the claim unqualified?
## Excerpt or diff
- research/white-paper/white-paper.md:115 (COMMITTED HEAD bytes; note: the file also carries an uncommitted working-tree revision): "Pillar 1 — xCABI, a portable trace standard. Every agent system keeps a private mutation log. None is cross-harness replayable, diffable, or conformance-testable. xCABI … A consumer reconstructs any turn without knowing which harness produced the trace."
## Constraints
spec/rfc-0/ stays sealed byte-identical; RFC-0.1 changes stay additive + version-gated; paper wording may not claim more than measured evidence; nothing is decided without D13.
## Evidence
- W5 ran one identical scripted task in OpenCode and Hermes: both traces RFC-0-valid, `ctxvm replay` exit 0 each; raw `ctxvm diff` diverges at event 0, every divergence classified harness-faithful (tool vocabulary + args shape = D1/D2; turn-unit mismatch hermes pre_llm once per user turn = D4; W7 items #1/#2/#3 named; no adapter bug) — row W5, 08-HANDOFF.md:970 (RR-W5-20261030).
- Replay guarantee is per-trace: `rust/target/release/replay corpus/m1/tracer-healthy.jsonl` → exit 0 (recomputed 2026-11-07).
- Pages travel as identity, not bytes: rust/crates/ctxvm-codec/src/model.rs:14–21 (checked in reports/RR-WP2REV-20261107.md) — "same trace, same bytes" holds for render geometry only.
- RFC-0.1 exists (spec/rfc-0.1/, R0–R5) and its validator proves sealed v0 rejects v0.1-only lines; a DIFF-normalisation rule set is NOT yet written (confirmed by grep: no on-record normalisation card in design/).
## Output wanted
1. Keep, narrow, or split the Pillar-1 sentence (one replacement sentence if narrowed).
2. Should a normalisation proposal card be authored in design/ (proposal-only, no spec change)? yes/no.
3. Which W7 items belong in it as of today: name/args canonicalisation (#1), page-body semantics (#2), turn-unit definition (#3) — pick.
4. Does the same wording fix apply to the closing pillar echo (white-paper.md:635)? yes/no.

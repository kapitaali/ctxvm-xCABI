# Packet 2: the `faultOfResidentPage` violation the healthy-fixture demo prints
2026-11-08 · requester: ctxvm repo agent · related decision: none assigned (paper wording; ties to D15)
STATUS: answered 2026-11-08 (verdicts in handoff/QUESTIONS.md; verdict 3 executed same day —
seq 7 located: source `identifier_scan`, so the reviewer's cause swap-in applies).
## Question
The paper's verified-commands block replays the healthy 16-event corpus trace and prints one `faultOfResidentPage` violation — the "healthy" demo showing a violation class. How should the paper frame this: (a) explain the class in one sentence next to the output (a model re-mentions an already-resident page; v0 logs it, replay stays green), (b) mark the output block "illustrative" like its sibling profile block, or (c) swap the demo for a v0.1 exemption example (umpire's A/B ledger went 3 violations -> 0 under R1)?
## Excerpt or diff
- research/white-paper/white-paper.md:333 and research/white-paper/index.md:339 (WORKING TREE, uncommitted white-paper-lane revision — provenance named per packet law):
```
$ ./rust/target/release/replay corpus/m1/tracer-healthy.jsonl
{ "events": 16, "divergences": [], "violations": [{"seq": 7, "kind": "faultOfResidentPage"}] }
```
## Constraints
corpus/m1/ bytes are checksum-frozen (cannot be edited to hide the class); RFC-0 semantics sealed; the demo cannot hide a real logged class; no unsealing decision inside this packet.
## Evidence
- Recomputed 2026-11-07: `rust/target/release/replay corpus/m1/tracer-healthy.jsonl` → exit 0, identical JSON (also byte-twin packages/node/fixtures/tracer-healthy.jsonl, 16 events).
- Class is legal-by-design: hermes live echo fixture shows the 3x R1-remention class and sealed v0 validator passes (RR-W4B2-20261030); m2 live captures 4x/3x logged = "m2's expected class" (RR-T15-20261027).
- The friction RFC-0.1 fixes (same class from deliberate re-execution) is landed: spec/rfc-0.1/ R1 intentional_rerun, and umpire's ab-demo ledger replays 3 violations -> 0 (08-HANDOFF.md §0 2026-10-31; RR-RFC01E1 chain).
## Output wanted
1. Keep the demo as-is / add a sentence / replace with a v0.1 exemption demo — pick one.
2. If a sentence: one exact sentence for the paper.
3. Does the violation at seq 7 have a named event we should cite here? (agent will locate seq 7 in the trace if the reviewer asks.)

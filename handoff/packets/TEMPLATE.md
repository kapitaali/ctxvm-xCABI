# Packet <number>: <short title>
Date, requester, related decision (D-number or none)
## Question (one specific question)
## Excerpt or diff (only the relevant lines, with file path and line range)
## Constraints (what must not change)
## Evidence (numbers with the command that produced them; UNVERIFIED marked)
## Output wanted (numbered verdicts, one line each; rewrites only if asked)

Rules for every packet (handoff/WORKFLOW.md): one specific question; only the context needed to
answer it; excerpts carry file path AND line range AND provenance (committed HEAD bytes vs
working-tree WIP, named); every number carries the command that produced it; UNVERIFIED is marked,
never smoothed away; no raw traces, prompts, credentials, or absolute home paths; size <=3 KB
(wc -c); the answer is expected as numbered one-line verdicts. Rewrites are on request only —
 otherwise the agent turns the verdicts into patch lists itself.

Open packet slots: claim the next P-number handoff/packets/P<n>-<slug>.md, register it in
handoff/QUESTIONS.md with status queued, and link it to its D-number if it would resolve one.

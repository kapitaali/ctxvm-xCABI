# Packet 14: the one-liner "reconstruct and replay the exact request"

Date 2026-11-15, requester: the repo agent (review lane). No D-number yet (paper scoping).
Card: `reports/RR-PAPER-REVIEW-20261115.md`.

## Question

The one-liner — "Context tracing is not logging — it is the ability to reconstruct and replay the exact request
the harness sent" — stands in six places, and the trace holds no request bytes. **Narrow the one-liner, or keep
it and state the limit once in §16?**

## Excerpt or diff

`research/white-paper/white-paper.md:17`, `:237`, `:633` and `research/white-paper/index.md:23`, `:243`, `:639`
— **working-tree WIP, research lane, uncommitted** (not HEAD bytes):

> **Context tracing is not logging — it is the ability to reconstruct and replay the exact request the harness
> sent.**

Also `research/white-paper/white-paper.md:247`: "…and the exact rendered message array."

The routed item 2 correction landed once, at `:629`. §16 (`:575`) lists six limits and not this one; the
paper's own rule at `:443` says "What a trace cannot do is in §16, in one place."

## Constraints

- The paper states the content-blindness once already, at `:617`: "A trace holds page identities, content
  hashes, token counts, and references".
- The question is where the limit is stated, not whether it exists.
- No cost-saving claim (law 7). The research lane owns `research/**`: the reviewer answers, the agent applies.

## Evidence

Commands (repo root, 2026-11-15):

- the wire's only free-text field is `page.evict.stubText` (sealed v0 schema) and no shipped emitter writes a
  `page.evict` row ⇒ the trace carries no request content.
- on the paid paged capture (`arm: paged`, 20 turns, 42 API requests): `turn.render.residentTokens` is
  **86,569, constant** across all 20 turns; `turn.render.prefix.approxInputTokens` grows **12,060 → 59,747**; the
  provider's receipts (`call.meta.providerUsage`) grow **14,557 → 114,766** ⇒ the trace's resident total does not
  track the request (script: the card's §9).
- the request's *size* is recorded per turn in `turn.render.prefix` (in the arms that measure it).

Candidate wordings (the agent recommends (b)):

- **(a) narrow the one-liner:** "…the ability to reconstruct the page-table state and the render projection of
  a turn — not the request's bytes: the trace holds page identities, content hashes, token counts and
  references."
- **(b) keep it, state the limit once in §16:** "A trace cannot reconstruct the request's bytes. It records page
  identities, content hashes, token counts and the measured size of each request; the shipped adapters do not
  yet emit the stub renders that would record a turn's omissions."

## Output wanted

1. One line: (a) or (b), or your own wording.
2. One line: if (b), where in §16 (a seventh bullet, or folded in), and do the six one-liner sites need a
   pointer to it?
3. One line: does the same limit belong beside the "exact rendered message array" sentence at `:247`, or only
   in §16?

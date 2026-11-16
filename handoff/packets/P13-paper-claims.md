# Packet 13: the `page.render` sentence vs the shipped adapters

Date 2026-11-15, requester: the repo agent (review lane). No D-number yet (paper scoping).
Card: `reports/RR-PAPER-REVIEW-20261115.md`.

## Question

The white paper says the `page.render` event "captures the exact render mode (full or stub) for every page,
every turn". The wire can carry that; no shipped adapter emits it. **Scope the sentence to the format's
capability, to the shipped adapters' behaviour, or to both?**

## Excerpt or diff

`research/white-paper/white-paper.md:265` — **working-tree WIP, research lane, uncommitted** (not HEAD bytes):

> ctxvm's tracer already records all of this. The `page.render` event captures the exact render mode (full or
> stub) for every page, every turn. The `turn.render` event captures resident/evicted token totals and
> headroom. […]

## Constraints

- The wire's capability is not in question (`renderMode` = `["full","stub"]`, sealed v0 schema); only the
  sentence's scope is.
- One sentence (plus its `index.md` mirror); no spec or adapter change; no cost-saving claim (law 7).
- The research lane owns `research/**`: the reviewer answers, the agent applies.

## Evidence

Commands (repo root, 2026-11-15):

- emitters write `full` only, once per page: `grep -rn 'mode: "full"' packages/*/src` ⇒
  `packages/node/src/tracer.ts:378`, `packages/hermes/src/plugin.py:295` (the reveal is guarded by a
  `revealed` flag).
- no shipped emitter writes `mode: "stub"` or a `page.evict` row: `grep -rn '"stub"' packages/*/src` ⇒ no hit
  (the `page.evict` hits are readers: `packages/opencode/src/resume-brief.ts:138`).
- live captures: 176 `.jsonl` files, **2,050** `page.render` events, **0** `mode: "stub"`, **0** `page.evict`
  (script: the card's §9).
- the repo's only stubs: `corpus/m1/session-thrashing.jsonl` (12 stub + 8 full renders, 4 `page.evict`) — a
  hand-built fixture whose `corpus/m1/provenance.json` says "SYNTHETIC, not a live harness capture".
- so a live trace cannot say which pages a given turn's request contained (paid paged capture: 21 pages
  declared, 19 renders, one per turn, 0 stubs).

Candidate wordings (the agent recommends (c)):

- **(a) format-scoped:** "The `page.render` event can carry the render mode (`full` or `stub`) per page per
  turn. The shipped adapters today emit `full` only, at a page's first reveal."
- **(b) adapter-scoped:** "The tracer records a `page.render` per page at its first reveal, mode `full`. The v0
  wire has a `stub` mode no shipped adapter emits yet, so a live trace cannot yet say which pages a turn
  stubbed."
- **(c) (a) + (b) merged** — one sentence carrying the capability and the caveat.

## Output wanted

1. One line: (a) / (b) / (c), or your own wording.
2. One line: is the same scoping owed to the wire-format table's `page.render` row (`:152`), or only to the
   prose?
3. One line: does the answer change if a stub-emitting adapter ships before publication (falsifier: a live
   capture containing stub renders)?

ROLE — task designer for the W8 paging experiment. Design work only: no code, no paid runs, no
edits outside the two files named in §6.

You are asked to do the one thing that currently blocks the experiment: **design two tasks that a
naive agent actually finishes inside the iteration ceiling**, while keeping the token floor that
makes the paging question meaningful.

======================================================================
1. READ FIRST
======================================================================
AGENTS.md                                   laws (note Law 7 and the never-touch list)
handoff/LANES.md                            who owns what — you own nothing; you write two files
design/w8-run-plan.md §3, §3b, §4e        the templates, the freeze holes, the current decisions
reports/RR-W8PILOT-20261107.md              the first pilot: both arms solved, no pressure
reports/RR-W8CHUNK-20261107-1.md             cell 1: 150/150 iterations, no artefact
reports/RR-W8CHUNK-20261107-2.md             cell A: same ceiling, and the search-bound evidence
reports/RR-W8RESCOPE-20261107.md             the re-scope that did NOT fix it, and why
reports/RR-W8TPLCHK-20261107.md              which templates can carry pressure

======================================================================
2. THE SITUATION, IN NUMBERS
======================================================================
The experiment asks: does context selection (the `ctxvm` engine at a 24,000-token budget) reduce
tokens without hurting accuracy? Two arms, one factor. Each cell is one agent run under a hard
ceiling of **150 iterations**.

Two naive cells, two different fixtures, same outcome:

  cell 1   T1 at 33 parts   42.5 min, 150 calls, no `flags.json`, max_iterations_reached(150/150)
  cell A   T1 at 13 parts   37.0 min, 150 calls, no `flags.json`, same ceiling

And the reason, from cell A's own capture:

  700 page.declares:  686 search_files (69,439 tokens)  |  14 read_file (57,489 tokens)
  632 distinct refs, request growth 69,668 → 299,193 approx tokens

The agent **searched 686 times and read fourteen files**. Shrinking the fixture did not change the
behaviour, because the binding constraint was never page size — it is that a content search looks
like progress, and this model prefers it.

The task text already says, in bold, that a search cannot produce line shape. The model searched
anyway. **Do not fix this with more emphatic wording.** Fix it with a task whose answer a search
physically cannot assemble.

======================================================================
3. WHAT EACH DESIGN MUST SATISFY
======================================================================
For each of the two tasks, all eight:

1. **Naive-completable.** A competent agent finishes within 150 iterations and produces the
   artefact. Your estimate of the call count, with its reasoning, must be ≤ 90 so there is margin.
2. **Floor ≥ 45,000 declared tokens.** The paging question needs the naive context to exceed the
   24,000-token budget; below that the engine is a no-op and the cell measures nothing. State the
   floor and how you computed it.
3. **Search cannot shortcut it.** Name the specific property a `search_files` hit cannot return —
   an aggregate over every line, a cross-file invariant, a count that depends on lines that do not
   match any pattern, a value that requires two files to be held at once. Then state the falsifier:
   what a search-based shortcut would have to return to pass, and why it cannot.
4. **Mechanical checker.** A script decides PASS/FAIL, exits 0/1, with no model judgement. It must
   go RED on a perturbed artefact — say how you perturbed it.
5. **Unique answer.** No judgement calls, no "reasonable" variants: one byte-exact artefact.
6. **Read-only source material.** The fixture is files the agent reads, not commands it runs. No
   shell, no network, no writes except the one artefact.
7. **Search-hostile by construction, not by prohibition.** You may not assume a tool is removed;
   the task must survive the tools the agent actually has.
8. **Honest about what it measures.** If a design would only work because it is artificially
   tedious, say so and discard it — a task that is hard for the wrong reason produces a number
   about tedium, not about paging.

======================================================================
4. THE SHAPE THAT IS MOST LIKELY TO WORK (not a requirement, a starting point)
======================================================================
Per-file measurements that need every line: counts, extrema, histograms, byte lengths, and
cross-file invariants (a value in file A that only makes sense next to file B). Search returns
matching lines; it cannot return "how many lines are longer than 100 bytes across thirteen files",
and it cannot return a value that only exists in the relation between two files.

Contrast with what failed: "list the flags each binary accepts" is answerable from one grep hit per
binary, and the agent found that out and stopped reading.

======================================================================
5. DELIVERABLES
======================================================================
`design/w8-tasks/README.md`
  - the two designs side by side: name, what the agent must produce, floor, estimated calls, the
    anti-search property, the falsifier, and what a PASS at 150 iterations would prove.
  - one paragraph per design on why the previous two attempts failed and how this one differs.

`design/w8-tasks/T-A.md` and `design/w8-tasks/T-B.md`, each ≤ 2,000 words:
  - the task text as it would be pasted to the agent (the agent sees only this);
  - the fixture specification (files, sizes, how generated, seed) — do not create the fixture;
  - the expected artefact, byte-exact, or the rule that generates it deterministically;
  - the checker's rules and its perturbation test;
  - the call-count estimate with its arithmetic;
  - the anti-search argument and its falsifier;
  - known weaknesses.

======================================================================
6. HARD LIMITS
======================================================================
- Write ONLY those three files. Do not create fixtures, do not run paid calls, do not touch
  `packages/**`, `spec/**`, `corpus/**`, `benchmarks/**`, `research/**`.
- No spend. No gateway restart. No commits — leave the files for the lane to commit.
- A design you cannot defend against §3.3 ("search cannot shortcut it") is not a design; say so
  and propose a different one rather than shipping a weak one.
- If both designs fail §3.1 (naive-completable) when you think it through, say that plainly in the
  README: "no task of this shape completes inside 150 iterations on this model" is a finding the
  experiment needs, and it would close W8 rather than prolong it.

======================================================================
7. OUTPUT
======================================================================
The three files, then a five-line summary: what each task measures, the floor, the estimated call
count, and the single reason you believe search cannot shortcut it.

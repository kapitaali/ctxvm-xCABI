# Agent brief — the T-B output-completeness run in OpenCode

Paste the block below to the agent. It assumes zero memory of any earlier session. Its source is
`design/TB-OPENCODE-RUN.md` (`2b470a7`), with two corrections marked **[verified here]**.

---

You are running one measurement in the ctxvm repository, then recording it. You are not designing an
experiment and you are not asked to improve anything.

**Repo:** `/home/theb/Documents/ctxvm`. Read `AGENTS.md` (laws), `handoff/LANES.md` (who owns what),
`design/TB-PLAN.md` (what T-B measures) and `design/TB-OPENCODE-RUN.md` (this run's plan of record) before
touching anything. The gate is `bash tools/run-ci.sh`; it must print `ALL GATES GREEN`. `bash
tools/check-handoff.sh` must print `ALL PASS`. Never push — the owner pushes. Attribution is
`kapitaali <teppo@kapitaali.com>`.

**What is already measured — do not re-derive it, verify it once and move on:**

- Model: `explabs/qwen3-30b-a3b` (fallback `explabs/qwen3-8b`) on the `explabs` provider in
  `~/.config/opencode/opencode.jsonc`, `cost.input = 0.0`, `cost.output = 0.0`. Verified present and listed
  by `~/.opencode/bin/opencode models`.
- CLI: `opencode v2.3.0`. Create-or-continue a session with
  `opencode run --session <id> --model explabs/qwen3-30b-a3b "<prompt>"`, and export with
  `opencode session export <id> --sanitize`.
- Fixture: **192 files × 150 rows, seed 7** — C = **109,155 tokens** (1.82× the 60,000 budget), the file-only
  residency crossing at **turn 106**, 87 pressure turns, digest
  `36561425bf57ac156def80a7653ebceccb9a55b24f3c475f585370040156fbec`. Regenerate with
  `python3 tools/gen-tb-fixture.py --out <fresh-dir> --files 192 --rows 150 --seed 7 --budget 60000
  --measure`; `--check` must re-derive it byte-identically. The generator refuses a populated directory, so
  use a fresh one.
- **[verified here] The protected floor is bounded, not unknown.** Per-file tokens run 557–578, so
  F ≤ system (≈5.5 k) + 9 × 578 + scaffold (≈2 k) ≈ **12,702**, against a 60,000 budget. The phase-0 gate
  `F < 60000 < C` therefore passes with ~47 k of headroom. Print that bound; do not claim to have measured F —
  only a paged request yields the exact value, and this harness has no engine.
- **[verified here] This run produces no xCABI trace.** `opencode.jsonc` has no `plugin` entry, so
  `@ctxvm/opencode` is not wired. Your record is the exported session ledger, not a capture. Do **not**
  describe this run as traced, and do not run the spec validator on a trace that does not exist.

**What this run can witness, and nothing more.** OpenCode's adapter is mirror-only: no context engine, no
budget, no eviction, no `enginePlan`. So this run **cannot** show a paged arm, H3, H4, or any paging effect.
It answers one question: does a hand-countable per-prompt workload (150 rows instead of 600) produce
**complete, exact** per-file replies on a free model when execution tools are available? A GO means "preregister
a Hermes paged cell on this shape". A NO-GO means "change the shape again". Neither is a cost claim.

**The task, verbatim from `design/TB-PLAN.md` §3:**

- P1–P192, one per file: *"Read `fixture/data-NN.csv`. Reply with one line per category that appears:
  `<category> <count> <sum> <min_id> <max_id>`. Nothing else."*
- P193, the reconciliation: write `artefact.json` (sorted `categories` with count/sum/min_id/max_id, plus
  `top_category`, `top_file`, `grand_total`) **and** answer three exact-row lookups into early files
  (`data-02`, `data-07`, `data-11`), asked as *"the row with id X in data-NN.csv: give its category and value"*.
  Record the answer key — you will need it to score.

**Phases. Stop at each one and report before continuing.**

0. **Free, no model call.** Generate the fixture into a fresh directory; `--check` byte-identical; print C, the
   per-file token range and the F bound; build the 193-prompt list; prove the checker turns red on bad input
   (`python3 tools/tb-check.py <fixture> --prove` must say ALL SEVEN BEHAVED, and `--per-reply` must score a
   known-good 8/8 reply 8/8 on its first file). Write nothing else.
1. **Three prompts** (P1–P3) on one session. Export the session. Score those three replies with
   `python3 tools/tb-check.py <fixture> --per-reply <replies.jsonl>`. **Stop when** fewer than 2 of 3 files are
   exact, a tool is refused, or anything is billed. **Checkpoint:** count the calls those three prompts took
   and use it to freeze the ceiling before phase 2 — the card's 450 is an estimate (193 × ~2.3 calls), and a
   measured count replaces it.
2. **The full run** (P1–P192 + P193) in one session, under the frozen ceiling. Hard stops: a prompt past the
   timeout, repeated "does not exist" tool errors, auth 401/429, **any charge**, calls past the ceiling, a
   second session serving the run, or an export that does not parse. A refusal, a timeout or a billed token is
   a **result to record**, never a prompt to retry until green.
3. **Offline scoring.** `tb-check <fixture> artefact.json` (parsed equality is the gate; canonical bytes are an
   observation), `--per-reply` (it prints three measures: file-exact, tuple coverage over files attempted,
   tuple coverage over the whole fixture — report all three, they are not interchangeable), and the lookup
   score. Validate that the exported ledger parses and that every one of the 193 replies is present or
   explicitly missing.
4. **Decision only, no cell.** If completeness passes (your pre-declared threshold), say a Hermes paged cell can
   be preregistered on this shape. If it fails, say the shape changes again. Do not run a paged cell.

**Record it** in the repo, in this shape: `reports/RR-TBOPEN2-<date>.md` (what ran, the exact commands, C/F,
the three scores, per-file where it failed, what it cannot prove), one row appended to `reports/LOG.md` with
exactly four pipes and no `|` inside the summary, and a section in `reports/RR-DAY-<date>.md`. Keep artefacts
(captures of the export, `replies.jsonl`, `per-reply.txt`, `lookups.json`) under
`~/.local/state/ctxvm/w8-runs/<run-id>/`, never in `/tmp`, and cite their paths in the report. Commit with
explicit paths only — never `git add -A` — and leave the tree clean or declare what is dirty and whose it is.

**Do not touch:** `packages/**` (the OpenCode adapter and the tracer), `tools/**` (the runner and the checker —
if one needs a change, write the proposal in your report instead), `spec/**`, `corpus/**`, `research/**`,
`handoff/**` (except the day file you append to), or `design/TB-PLAN.md`. If you believe a tool is wrong,
report it; the lane that owns it decides.

**Six ways this run can lie to you — all of them have happened in this repo:**

1. A reply that names fewer categories than the file holds is **not** "mostly right": file-exact is the gate,
   tuple coverage is the diagnosis, and both go in the report. (Measured: 0/48 file-exact while 69/69 emitted
   tuples were correct.)
2. A refused tool is not a measurement of the model. Read the transcript for `[This code is not allowed…]` and
   say whether execution tools were available, refused, or unused — that difference decides what the run means.
3. `cost: 0.0` in a config is a local declaration. Report $0 only with the provider's own endpoint or a receipt;
   a billed token anywhere is a hard stop.
4. Do not relax the checker, the timeout or the ceiling to get a green. A flake is a finding.
5. Do not call the run traced, and do not validate a trace it did not produce.
6. A single session is the unit. Two sessions, or a re-run appended to the same ledger, invalidate the run.

**Start with phase 0 and stop there for review.** Its deliverable is numbers, not a run: C, the per-file token
range, the F bound, the 193-prompt count, and the checker's red-before transcript.

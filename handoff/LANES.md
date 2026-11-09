# Lane ownership — who edits what, and how a shared file is claimed

This repository is worked by several agents at the same time. This file is the ownership map.
Read it before editing anything that is not yours, and before touching a shared file at all.

A lane **owns** a set of paths. A shared file is **claimed by a commit**, never by a message.

## The lanes

| lane | owns | must not write |
|---|---|---|
| **hermes lane** | `packages/hermes/**`, `tools/**` (gate, runner, checkers), `design/w8-*`, `design/W8-*`, `reports/RR-W8*`, the installed plugin copy at `~/.hermes/plugins/ctxvm-tracer/` | `packages/opencode`, `packages/ai-sdk`, `packages/node`, `research/**` |
| **opencode lane** | `packages/opencode/**`, `packages/ai-sdk/**`, `packages/node/**`, their fixtures | `packages/hermes`, `research/**` |
| **research lane** | `research/**` | everything else; `research/**` is read-never-edit for every other lane |
| **experiment lane** | `experiments/**` (gitignored), the benchmark workspace outside this repo, `reports/RR-REDLINE-*` | `packages/**`, `spec/**`, `corpus/**` |
| **review lane** | `handoff/**` (PROJECT-STATE, QUESTIONS, packets), `reports/RR-DAY-*`, the day indexes | `packages/**`, `research/**` |
| **reviewer** (external) | nothing here — answers pasted packets only | the repository |
| **owner** | pushes, ratifies D-decisions, clears `design/**` placement, releases | — |

Shared by all: `AGENTS.md`, `08-HANDOFF.md`, `08.1-UPDATE-PROMPT.md`. Changes there are policy:
propose them to the review lane or the owner, do not edit them in passing.

## Shared files that cannot be owned, and the rule for each

**`reports/LOG.md`** — append-only, exactly four pipes per row.
Append your row in the same commit as your card. Do **not** stage the file while another lane's
row is uncommitted: you would commit their work under your message. If it must happen, say so in
the commit message. Never rewrite or reorder committed rows; an erratum is a new row.

**`handoff/PROJECT-STATE.md`** — one mutable document, and the usual lost-update victim.
Edit it only in a commit that contains nothing else. Re-read it immediately before writing, and
re-apply your delta over whatever landed meanwhile rather than over the copy you read first.

**`~/.hermes/plugins/ctxvm-tracer/`** — one installed copy, outside the repo, shared by every
lane that runs a Hermes session. Only the hermes lane writes it. When you sync it, say the
version in the commit message. A lane measuring behaviour against a copy another lane replaced
is measuring nothing.

**The gateway** — one process serving every profile and every lane's live session. A restart ends
all of them. Ask before restarting; nobody restarts "to be safe".

**`rust/target/`** — rebuilt by whoever runs the gate. Harmless, but two lanes running
`cargo build` at once is slow, not broken. Do not delete it to "clean up".

## Four rules, each bought with a paid lesson

1. **Claim by commit.** Before editing a shared file, `git status --short` tells you whether
   someone else has a hunk in it. A message is not a claim; a commit is.
2. **Stage explicit paths.** Never `git add -A`. The untracked list is the collision surface —
   it is where the 0-byte browser download, the build artefacts and another lane's drafts appear.
3. **Leave the tree clean across a turn, or declare it.** A lane that leaves `research/**` dirty
   for two days blocks every clean-tree pre-flight and forces exceptions into other lanes' run
   books. If you must leave work in flight, write what it is and whose it is into PROJECT-STATE.
4. **Cite by id, not position.** `RR-<CARD>-<date>`, `D-<n>`, packet `P<n>` — never "row 184" or
   "the second block". Positions shift under concurrent appends; ids do not.

## When two lanes need the same package

Use a `git worktree`: one per lane, each committing its own paths, merged deliberately by whoever
owns the target. The main checkout stays clean, and "another agent's work in progress" stops being
an excuse for a dirty pre-flight. This is the structural fix; the rules above are what keep the
shared files usable until it is in place.

## What went wrong without this file

| symptom | what actually happened |
|---|---|
| a commit carried another lane's LOG row | the row was appended but uncommitted when the file was staged |
| PROJECT-STATE lost an edit | two agents wrote it between the same two commits |
| every clean-tree pre-flight failed for days | `research/**` was left dirty by a lane with no claim |
| `packages/py/build/`, `ctxvm_py.egg-info/` untracked | build artefacts nobody owned; now ignored |
| a 0-byte `.crdownload` stub inside `research/` | browser download in flight, swept up by `git add -A` |
| plugin 0.10.4 produced a false arm witness | one installed copy, synced by two lanes at different versions |

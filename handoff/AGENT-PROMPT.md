# ctxvm agent prompt — read ALL of it before touching anything

Repo: this checkout. ctxvm = virtual memory for agent context; xCABI = the JSONL trace standard it
emits. The Rust core is the byte authority; `ctxvm replay` re-derives the page table.

**Several lanes work in this repo at once.** `handoff/LANES.md` is the ownership map: who edits
which paths, which files cannot be owned, and how a shared file is claimed. Read it with the laws.

## 0. Entry order (do these first, in this order)

1. `AGENTS.md` (laws) → `handoff/LANES.md` (your lane, the shared files) → `00-README.md` →
   `08-HANDOFF.md` §0–§4 (state and rules of engagement).
2. `git log --oneline -8 && git status --short` — uncommitted files may be ANOTHER lane's work in
   flight. Remote truth is `git ls-remote --heads origin`; local tracking refs go stale.
3. `bash tools/check-handoff.sh` — must print ALL PASS.
4. For any change at all: `for v in $(env | grep '^CTXVM' | cut -d= -f1); do unset "$v"; done`, then
   `bash tools/run-ci.sh > /tmp/ci.log 2>&1; rc=$?` and gate every commit on `$rc`. Never pipe the
   gate through `tail`: a pipeline returns the last command's status and has landed a commit on a
   red tree once. Never hand-write an `env -u` list — it drifts on the first new key; enumerate.
5. State of record is `handoff/PROJECT-STATE.md`; history is `reports/LOG.md` (append-only). If chat
   and a file disagree, the file wins. Never hardcode gate totals: date them and name the command.

## 1. Session state (verify, don't trust — this section ages fastest)

- HEAD `cbe858c`, pushed. The A1–A6 adoption cards are **committed** (`ae9c1f7` … `af20111`) plus
  the REDLINE report (`cbe858c`); their six LOG rows and the PROJECT-STATE delta are in `af20111`.
- Reviewer round P1–P3 closed and verified. Packets `P4`–`P7` exist as files but are **not
  registered** in `handoff/QUESTIONS.md` — registering them is agent work, then the owner pastes.
- W8 is **BLOCKED**: 0 cells counted, $1.1541 of the $25 cap spent, four reopen conditions gated in
  `design/w8-run-plan.md` §4e. Do not start a paid cell.
- REDLINE measures **1.0968x** at 16k against a claimed 1.5x (`reports/RR-REDLINE-20261108.md`):
  a negative result, recorded. Do not restate the 1.5x claim anywhere.
- Plugin `ctxvm-tracer` **0.13.24** on disk (authoritative: `live/__init__.py` + `live/plugin.yaml`,
  gate-enforced). The **running gateway holds it** (PID 23669, started after the 09:31 sync), so a capture
  taken now is labelled 0.13.24 — but the newest one is the **control** arm, so the **paged** capture is
  still owed. Only the hermes lane syncs the copy.

## 2. Work split (who does what)

- **hermes lane** — `packages/hermes/**`, `tools/**`, `design/w8-*`, `reports/RR-W8*`, the installed
  plugin copy. Owns the gate and the runner.
- **opencode lane** — `packages/opencode/**`, `packages/ai-sdk/**`, `packages/node/**` and their
  fixtures.
- **research lane** — `research/**`, read-never-edit for everyone else.
- **experiment lane** — `experiments/**` (gitignored) and the benchmark workspace outside the repo;
  its reports are `RR-REDLINE-*`.
- **review lane** — `handoff/**` (PROJECT-STATE, QUESTIONS, packets), `reports/RR-DAY-*`.
- **reviewer** (external) — answers ONLY pasted packets, from the packet alone, with verdicts, one
  falsifier each, and UNKNOWN where it cannot decide. Do not ask it for repo access; every locator
  is verified here afterwards.
- **owner** — pushes, ratifies D-decisions, clears `design/**` placement, releases.

When a verdict returns: verify EVERY packet claim against the books first (the reviewer works
packet-only), then execute agent-verdicts, then assimilate — QUESTIONS row, packet STATUS header,
PROJECT-STATE delta (≤150 words), LOG row, day-file section, checker, the three
`tools/session-start.sh N --with-context` pastes (≤16,384 B, keep ≥127 B margin), CJK/secret sweep
over staged files, commit. Never push: the owner pushes, and Actions runs are witnessed **and**
recorded (echo law).

## 3. Never-touch / never-do

- Never touch a path your lane does not own (`handoff/LANES.md`). `research/**` is read-never-edit;
  `design/**` needs owner clearance per new card. `corpus/**`, `spec/**` and `benchmarks/w8/**` are
  frozen for everyone.
- LOG rows: append-only, exactly four pipes, no `|` inside the summary, no CJK, never edit committed
  rows or blocks — errata are new rows or day-file blocks.
- RFC-0 is sealed. A new wire field needs all five touchpoints plus a validator negative, gated on
  `schemaVersion`.
- No cost-saving claim (none measured). No "deterministic" without a named machine scope.
- Do not stage unrelated WIP; the untracked list is the collision surface. Never `git add -A`.
  Never push. Attribution `kapitaali <teppo@kapitaali.com>`.
- Shared files, restated because they cost the most: `reports/LOG.md` and
  `handoff/PROJECT-STATE.md` are claimed by a commit, never by a message. Commit your hunks only.

## 4. Sharing a shared file with a concurrent lane (paid-for lesson)

Before ANY `git restore` on `reports/LOG.md` or `handoff/PROJECT-STATE.md`, snapshot to a temp dir
outside the repo — the copy may be the only one of another lane's uncommitted rows. If you clobber
it, re-append by RR-id from the snapshot in order, dedup, and record the erratum in the day file.
To commit only your hunks, build the exact staged content from HEAD plus your edits with
`git hash-object -w` and `git update-index --cacheinfo`; never `git add` a shared file that carries
a concurrent lane's rows. Cite rows by RR-id, never by position.

## 5. Closing every work item (standing)

PROJECT-STATE delta → QUESTIONS/packet updates → LOG row → day-file section →
`bash tools/check-handoff.sh` green → sweeps (CJK, secret shapes, `/home/` with disclosed
dispositions for pre-existing hits) → attribution-correct commit with explicit paths. Frontiers get
numbered blocks in `08-HANDOFF.md` §0; the kit's three pastes stay ≤16 KB. Register every promise
you cannot yet meet as UNKNOWN — never silently.

## 6. The two rules that would have saved the last two weeks

- **A claim is a commit.** A dirty file you did not write is someone else's work in flight; leave it
  alone and say so, or wait for it to land.
- **Evidence does not live in `/tmp`.** Captures, run logs and measured artefacts go to a durable
  path (the state dir or the benchmark workspace), with checksums. Scratch may vanish; a result
  that cannot survive a reboot is not a result.

MASTER PROMPT — hermes lane (H18, H17, H16 free test-gap bundle)
Owner routed 2026-11-19 (`RR-DEFAULTS-20261119`). The review lane authored this handoff card only: no test or
production byte was written by review. You are the hermes lane. Implement H18, H17, and H16 as one zero-spend,
test-only bundle, in order **H18 → H17 → H16**.

0. Role, and its boundaries
- You own `packages/hermes/**`, `tools/**`, `design/past-experiments/w8-*`, `design/past-experiments/W8-*`, `reports/RR-W8*`, and the installed plugin
  copy at `~/.hermes/plugins/ctxvm-tracer/` (`handoff/LANES.md:12`).
- You must not write `research/**` (read-never-edit for everyone), `spec/**`, `corpus/**` (frozen, law 5), another
  lane's package, `handoff/**` (review lane; except a final `PROJECT-STATE.md` delta commit if needed), or another
  lane's report paths.
- Scope authority: `design/ROADMAP-HERMES-LANE.md` items H16 (`:147`), H17 (`:155`), and H18 (`:160`), routed by
  owner ruling `reports/RR-DEFAULTS-20261119.md`.
- Zero-spend, test-only by default: do not make any model call, do not change production plugin logic unless a new
  test exposes a genuine bug (if so, record the bug + minimal fix explicitly in the card), and do not bump the
  plugin version, sync `~/.hermes/plugins/ctxvm-tracer/`, or ask for a gateway restart unless production plugin code
  changed.
- Never push. Attribution: `kapitaali <teppo@kapitaali.com>`. Commit via a private index, then
  `git read-tree HEAD` on the shared index; run `bash tools/git-hygiene.sh` before staging any shared file.

1. Entry ritual — every session, before any edit
1. Read `AGENTS.md` (laws 1–10), `handoff/LANES.md`, `handoff/PROJECT-STATE.md`, `design/ROADMAP-HERMES-LANE.md`
   §4–§5 (H16–H18), and `design/HERMES-PLUGIN-DEVELOPER-PROMPT.md`.
2. Check `git log --oneline -8` and `git status --short`. The tree carries other lanes' WIP (`research/white-paper-Part-III*.md`,
   untracked `design/DSH-LANE-DEVELOPER-PROMPT.md`, untracked `reports/RR-DATAMININGFIX-20261117.md`). Never
   `git add -A`; stage your exact paths through a private `GIT_INDEX_FILE`.

2. The three test gaps, in execution order (H18 → H17 → H16)

### Step 1 — H18: sidecar carries `budgetTokens` and `budgetSource` (`ROADMAP-HERMES-LANE.md:160`)
- *Context:* Five existing tests cover `_budget_from_settings`, but none asserts that a flushed `.coverage.json`
  sidecar actually carries `budgetSource` alongside `budgetTokens`.
- *What to build:* In `packages/hermes/test/`, add a test that flushes a synthetic trace with a profile setting
  (and/or env precedence case) and asserts the written `.coverage.json` sidecar carries both `budgetTokens` and
  `budgetSource` with the expected values.
- *Done when:* The test fails if `budgetSource` or `budgetTokens` is omitted from the sidecar dict, and passes on the
  current tree.

### Step 2 — H17: retention with collision-suffixed trace names (`ROADMAP-HERMES-LANE.md:155`)
- *Context:* Retention prunes oldest-first under the byte budget rule and must never prune the file it just wrote.
  Collision suffixing (`-2`, `-3`, added under W21) has no retention test.
- *What to build:* In `packages/hermes/test/` (using a temporary ` tmp_path` / `tempfile.TemporaryDirectory` trace
  dir — never touch `~/.local/state/ctxvm/traces` and obey law 10 on cleanup), create $N$ collision-suffixed trace
  files (`-2`, `-3`, etc.), force a retention prune, and assert:
  1. the just-written (newest) suffixed file survives;
  2. pruning order is oldest-first across suffixed and unsuffixed siblings;
  3. the surviving file count / total bytes match the byte-budget retention rule.
- *Done when:* The test deterministically exercises suffixed filenames through the retention path and passes.

### Step 3 — H16: capture smoke test in the gate (`ROADMAP-HERMES-LANE.md:147`)
- *Context:* Sidecar fields (`budgetTokens`, `budgetSource`) and the `.jsonl` / `.meta.json` / `.coverage.json`
  capture triple + `coverage_check` exit 0 need to be pinned by a gate step on a synthetic session.
- *What to build (approved default placement):* Place the synthetic-session capture smoke test inside
  `packages/hermes/test/` so it runs automatically inside `tools/run-ci.sh` gate 2 (`python -m pytest packages/hermes -q`)
  and `.github/workflows/ci.yml` without adding workflow-file drift. (If you instead add an explicit step to
  `tools/run-ci.sh`, you **must** mirror it in `.github/workflows/ci.yml`.)
- *Assertions required:*
  1. One synthetic session runs end-to-end into a temp directory and flushes the full triple (`.jsonl`, `.meta.json`,
     `.coverage.json`);
  2. `coverage_check` (invoked in-process or via CLI against the synthetic trace) exits 0;
  3. The `.coverage.json` sidecar carries `budgetTokens` and `budgetSource`.
- *Done when:* The gate runs this smoke test on every `bash tools/run-ci.sh` invocation and fails if any of the
  three assertions breaks.

3. Invariants
- Law 10 (non-negotiable): any test cleanup uses `tempfile.TemporaryDirectory` / `pytest` `tmp_path` or names an
  exact scratch subdirectory; never `rm -rf` a variable that could be empty or resolve near `$HOME`.
- Law 7 & 8: no cost-saving claim, no unscoped "deterministic" claim.
- No `|`, CJK, secrets, or raw `/home/` paths in LOG rows or handoff files.
- Clear ambient `CTXVM_*` variables before running `pytest` or `bash tools/run-ci.sh`.

4. Verification bar — every line, or the card is not done
- Red-before check on each of H18, H17, H16 (prove each test fails when the asserted property is broken, then
  passes when restored).
- `for v in $(env | grep '^CTXVM' | cut -d= -f1); do unset "$v"; done; python3 -m pytest packages/hermes -q` → all
  pass, with the new test count reported.
- `bash tools/run-ci.sh` unpiped with `CTXVM_*` cleared → `rc=0 ALL GATES GREEN`.
- `bash tools/check-handoff.sh` → `ALL HANDOFF CHECKS PASS`.
- `bash tools/git-hygiene.sh` → `OK`.
- Tick H16, H17, and H18 in `design/ROADMAP-HERMES-LANE.md` only with the passing command outputs in hand.
- Emit `reports/RR-H16H18-20261119.md` (or `RR-HTESTGAPS-20261119.md`), one four-pipe row in `reports/LOG02.md`, and
  a section in `reports/RR-DAY-20261119.md`.

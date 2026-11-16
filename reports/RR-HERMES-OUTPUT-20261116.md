# RR-HERMES-OUTPUT-20261116 — what actually happened in the T-B free run: the Hermes host output and its scorer, not the ctxvm plugin

Lane: review (verify-then-record). Subject: `e948b5c` (T-B free run addendum), `0eddbb1` (first free-tier
T-B calls), and the hermes-plugin/runtime state they imply. Date: 2026-11-16. **No code was changed, no cell was
run, and no credential was read.** Every number below was re-measured from the artefacts in this repo and under
`~/.local/state/ctxvm/w8-runs/`.

## 1. Verdict

The report is **substantially correct**. I re-derived every headline number from the artefacts. Two record-keeping
gaps remain and are recorded below. The single most important scoping point: **neither commit changed the ctxvm
hermes plugin.** The defects are in (a) the Hermes host CLI's printed transcript, (b) the T-B scorer's parser, and
(c) the gateway session's toolset policy. The plugin is the instrument that captured the evidence, not the cause.

## 2. What I verified, with commands

| claim | verdict | how |
|---|---|---|
| five bundles, all accounted for | **true** | `~/.local/state/ctxvm/w8-runs/tb-*` has five dirs; four `summary.md` files carry NO RECORD / NO RECORD / DATA-INVALID / DATA-INVALID, walls 128.7 s / 94.9 s / 88.3 s / 4.6 s, all $0.0000 |
| `tb-1b-naive` killed, exit 143, 12 of 49 prompts, 36 prompt files, **no summary** | **true** | 143 = 128+15 (SIGTERM); dir has **12 `cmd-*`, 12 `stdout-*`, 12 `stderr-*` = 36 files** and no `summary.json` (the only one of the five without it) |
| host CLI wraps the answer in framing | **true** | `tail -30 stdout-01.txt` shows `☤ Hermes`, `Resume this session with:`, `Session:`, `Title:`, `Duration:`, `Messages:` after the answer |
| the transcript hard-wraps and fuses two tuples | **true** | `stdout-06.txt` and `replies.jsonl` contain `zeta 81 -390 32 9986theta 80 5054 131 9956`; `stdout-01.txt` has `alpha 72 -7114 276 9965beta 70 -5572 60 9999` |
| scorer changed from line-based to grammar-anywhere | **true** | `git show e948b5c -- tools/tb-check.py` replaces `parse_reply`: framing regex + joined body + `\b(category)\s+(-?\d+){4}`; CSV rows cannot match |
| 69 tuples parsed, 69 correct, 96 expected, 71.9 % coverage | **true, exactly** | re-ran with the shipped scorer against `experiments/w8b/ws-tb-naive/fixture` + the bundle's `replies.jsonl`: per file 5/8, 6/8, 6/8, 6/8, 6/8, 7/8, 6/8, 5/8, 5/8, 5/8, 6/8, 6/8 = **69/69, 69/96 = 71.9 %**, wrong = 0 for all 12 |
| misses are omissions, never wrong numbers | **true** | the same per-file output reports `wrong []` for all 12 files; every FAIL line lists only `missing [...]` |
| plugin version / gateway | **unchanged** | repo `live/__init__.py:94` and `live/plugin.yaml` both 0.13.24; installed copy `~/.hermes/plugins/ctxvm-tracer/` has the same two version strings; gateway PID 3817 started 2026-11-16 08:08:54 |
| neither commit touched plugin code | **true** | `git diff --name-only 03d44a1 e948b5c | grep -c packages/hermes` → 0; the changed runtime files are `tools/w8-driver.py` and `tools/w8b-run.py` |

## 3. Two record-keeping gaps

**G1 — the 71.9 % figure is not reproducible from any single stored artefact.** The killed bundle's
`naive/per-reply.txt` still ends with `per-reply accuracy: 0/48 = 0.0 %` — that is the **old scorer's** output,
left in place from the killed run. The card states the new figures but carries **no command** to reproduce them.
I re-derived them with this one-liner (the command I ran):

```sh
cd /home/theb/Documents/ctxvm
python3 - <<'PY'
import importlib.util, json
from pathlib import Path
s = importlib.util.spec_from_file_location('tb', 'tools/tb-check.py')
t = importlib.util.module_from_spec(s); s.loader.exec_module(t)
rows = [json.loads(l) for l in Path('/home/theb/.local/state/ctxvm/w8-runs/tb-1b-naive/naive/replies.jsonl').read_text().splitlines() if l.strip()]
exp = {n: t.aggregates(v) for n, v in t.read_fixture(Path('experiments/w8b/ws-tb-naive/fixture')).items()}
p = c = e = 0
for r in rows:
    got, _ = t.parse_reply(r['reply'])
    want = {k: (v['count'], v['sum'], v['min_id'], v['max_id']) for k, v in exp[r['file']].items()}
    p += len(got); c += sum(1 for k in want if got.get(k) == want[k]); e += len(want)
print(f'parsed {p} | correct {c} | expected {e} | coverage {100*c/e:.1f}%')
PY
# -> parsed 69 | correct 69 | expected 96 | coverage 71.9%
```

Recommendation to the experiment lane: put that command (or an equivalent `--json` mode in `tb-check.py`) next to
the 71.9 % row, and label the stored `0/48` as the superseded pre-fix score so a reader does not find two
contradictory numbers in the same run directory.

**G2 — two different measures share the word "accuracy".** `tb-check --per-reply` uses `score_reply`, which demands
an exact match of all expected categories; on these same 12 replies it still prints **0/48**. The card's 71.9 % is
**tuple-level coverage/precision**, a different measure. The card labels the reading as a capability observation
rather than a cell, which is correct, but it should name the 0/48 alongside the 71.9 % so the two are not read as
a contradiction. Not a defect in the measurement; a defect in the labelling.

## 4. Where the "surface not pinned" problem actually lives

The card says a shell reached the model although `toolsets: [file]`. I confirmed:
- `~/.hermes/profiles/w8cn-naive/config.yaml:4` has `toolsets:`; the root `~/.hermes/config.yaml` has a
  `platform_toolsets:` block. Neither was changed by these commits.
- The `-t file` refusal text is in the card and matches the run's 4.6 s exit: *"Resume retains gateway session
  policy; creation overrides are unsupported on resume."*
- 33 captures under the trace dir declare `tool:terminal` page refs, so the behaviour is long-standing and not
  unique to this run.

⇒ The binding policy is the **gateway session's**, not the profile's `toolsets` and not a creation-time flag. The
card's conclusion (no T-B cell is evidence until the pin is proved from a capture) is sound. I did **not** trace
which exact config key the gateway reads — that remains the experiment lane's open task, as the card says.

## 5. What is NOT established

- The model's arithmetic quality beyond these 12 half-complete replies; the card claims no more.
- Why the replies truncate (output budget vs. turn structure): the card offers candidates, none chosen.
- Whether the host CLI's hard-wrap is a terminal-width effect that differs across runs. UNVERIFIED.
- Byte-identity of the installed plugin against the repo copy: I compared **version strings only**, not file
  hashes. The lane that owns `~/.hermes/plugins/ctxvm-tracer/` owns that check.

## 6. Repro

```sh
# five bundles and their verdicts
for d in ~/.local/state/ctxvm/w8-runs/tb-*; do echo "== $d"; tail -2 "$d/summary.md" 2>/dev/null; done
# killed bundle: 12 cmd + 12 stdout + 12 stderr, no summary
ls ~/.local/state/ctxvm/w8-runs/tb-1b-naive/naive | awk -F- '{print $1}' | sort | uniq -c
# framing + fused tuples
tail -30 ~/.local/state/ctxvm/w8-runs/tb-1b-naive/naive/stdout-01.txt
grep -m 1 '9986theta' ~/.local/state/ctxvm/w8-runs/tb-1b-naive/naive/replies.jsonl
# scorer diff and the absent plugin changes
git show e948b5c -- tools/tb-check.py | head -60
git diff --name-only 03d44a1 e948b5c | grep packages/hermes   # -> empty
```

Gate re-run during this review: `bash tools/run-ci.sh` → **ALL GATES GREEN**, rc=0
(`/tmp/opencode/20261116-status-ci.log`). Kit: `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK.

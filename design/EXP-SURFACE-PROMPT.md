ROLE — run the surface experiment (Tier 0) and, only if it fails, the read-only build (Tier 1).

Context: a pair run compared two arms that took different routes — the control answered with one
`execute_code` call (5 calls, 73k input) and the treatment read the fixture (7 calls, 448k) — so the
token ratio measured two strategies, not two policies. Before any further cell, the question is
whether the tool surface can be pinned. Everything here is cheap: Tier 0 is at most $0.02, Tier 1 at
most $0.03, and Tier 1 only runs if Tier 0 fails.

======================================================================
WHAT IS ALREADY KNOWN (do not re-derive)
======================================================================
- The turn runs in the gateway, not the client (`hermes_cli/main.py:2844`). `-p` selects the profile;
  it does reach the serving process (proved: a paged probe produced `engineSelections > 0`).
- Toolset `file` resolves to exactly `patch, read_file, search_files, write_file` — **no
  `execute_code`**. `code_execution` is `execute_code` alone.
- `create_custom_toolset(name, description, tools=[...], includes=[...])` exists in `toolsets.py:499`
  but nothing in the CLI reads a config key for it; a custom set must be registered from code (a
  plugin import is enough).
- A checker must take its paths as argv and print what it read. The T-A checker now does.
- The task is `design/w8-tasks/T-A.md`: 14 files × 250 lines, floor ≈ 54,700 tokens, artefact =
  `lines`, `bytes`, `long`, `short`, `widest_file`, `total_long` (no line measurements).

======================================================================
TIER 0 — pin the surface with what already exists (cap: $0.02)
======================================================================
T0.1  Confirm the toolset inventory, from the host, not from memory:

  cd ~/.hermes/hermes-agent
  python3 - <<'PY'
  import sys; sys.path.insert(0,'.')
  from toolsets import get_toolset_info
  for n in ("file", "code_execution", "terminal"):
      print(n, "->", get_toolset_info(n).get("resolved_tools"))
  PY

  Expect `file` to list four tools and no `execute_code`. If it lists `execute_code`, stop: the
  surface question is different from what this prompt assumes.

T0.2  Establish what the offending pair actually had. Read the pair's captures:

  python3 - <<'PY'
  import json, glob, os, re, collections
  base = os.path.expanduser("~/.local/state/ctxvm/traces")
  for f in sorted(glob.glob(base + "/*.jsonl")):
      rows = [json.loads(l) for l in open(f) if l.strip()]
      d = [r for r in rows if r.get("type") == "page.declare"]
      if not d:
          continue
      mix = collections.Counter(
          m.group(1) if (m := re.match(r"tool:([a-z_]+)", r["page"]["id"]["logicalRef"])) else "other"
          for r in d)
      ver = None
      cov = f.replace(".jsonl", ".coverage.json")
      if os.path.exists(cov):
          ver = json.load(open(cov)).get("plugin", {}).get("version")
      print(os.path.basename(f)[:22], "plugin", ver, dict(mix))
  PY

  It answers one question: did the control cell have `execute_code` because no `-t` was passed, or
  because the set it received contains it? Write the answer down before running anything.

  The question it answers: did the naive cell have `execute_code` because no `-t` was passed, or
  because the toolset it was given includes it? Write the answer down before running anything.

T0.3  One cell on T-A, explicitly pinned, control arm only:

  mkdir -p /tmp/surface && cd /tmp/surface
  # a workspace with the T-A fixture materialised and no artefact yet
  hermes -p w8-naive -z "<the T-A task text>" \
      -m openai/gpt-6-luna --provider nous -t file \
      --in /tmp/surface/ws --usage-file /tmp/surface/naive-usage.json

  Then the three numbers that decide it:

  - declared refs by tool (no `execute_code`, no `terminal`);
  - calls against the 150 ceiling, and resident tokens against the 24,000 budget;
  - checker verdict (argv form, e.g. `python3 checker_ta.py /tmp/surface/ws /tmp/surface/ws/artefact.json`).

T0.4  Decision:

  A. no code tool appears, the model read the files, calls ≤ 60, artefact PASS
     → **Tier 0 succeeded.** The surface is `-t file`; write it into the runner and the prompt, skip
       Tier 1 entirely, and report the pair as viable with `-t file` (one more cell re-runs the
       treatment arm under the same flag).
  B. no code tool, but the model still answered from `search_files` dumps and got counts wrong
     → go to T1.1 (a read-only set without search).
  C. `execute_code` still appears with `-t file`
     → stop and report: `-t` does not restrict the set the way the inventory says, and the whole
       surface question needs re-opening.
  D. the cell hits the step ceiling
     → report a fixture/step defect; do not spend on the treatment arm.

======================================================================
TIER 1 — a read-only set, only if T0.4-B (cap: $0.03)
======================================================================
T1.1  Register the set from the plugin (no MCP server, no new process):

  in `packages/hermes/live/__init__.py` at register time, fail-open:
      from toolsets import create_custom_toolset
      create_custom_toolset("w8_readonly",
                            "read a workspace and write one artefact; no search, no code, no shell",
                            tools=["read_file", "write_file"])

  Bump the plugin version, add a test that the set resolves to exactly those two tools, run the gate.
  This needs one gateway restart to load — schedule it, do not do it mid-cell.

T1.2  Same T0.3 cell with `-t w8_readonly`. Acceptance: refs are `read_file`/`write_file` only;
  artefact PASS; calls ≤ 60.

T1.3  Only if T1.1 cannot work (the host refuses plugin-registered sets): build the read-only MCP
  server (`tools/experiment-ro/server.py`, stdio, stdlib only, two tools) and wire it in the
  *experiment profiles only* (`mcp_servers:` in `~/.hermes/profiles/w8-*/config.yaml`), with the
  built-in file and code toolsets disabled for those profiles. That is a day's work; do not start
  it unless T1.2 fails.

======================================================================
DELIVERABLES
======================================================================
- `design/exp-surface.md`: the inventory, what the offending pair actually had, the decision row
  (A/B/C/D), the chosen surface, and its one-line reproduction command.
- `reports/RR-EXPTOOLS-<date>.md`: the cells, their refs mix, calls, resident tokens, verdicts, cost.
- One LOG row, four pipes; explicit staged paths; commit as `kapitaali <teppo@kapitaali.com>`.
- Results live in `experiments/` (gitignored); the numbers live in the report.

======================================================================
HARD LIMITS
======================================================================
- Tier 0: at most two paid cells (~$0.02). Tier 1: at most two more. Ask before exceeding.
- Do not touch `research/**`, `spec/**`, `corpus/**`, `benchmarks/w8/**` fixtures.
- Do not restart the gateway mid-cell; a plugin change waits for a planned restart.
- Do not "fix" the witness: attribution is runner-side (the `-p` you passed, in the ledger), with
  `engineSelections > 0` on the treatment cell as corroboration.
- If a cell's refs show a tool you did not expect, stop and report rather than booking a result.

======================================================================
REPORT SHAPE
======================================================================
Five lines at the end: the toolset inventory, what the pair actually had, the decision row, the
chosen surface with its command, and the next paid cell if any. No prose beyond that.

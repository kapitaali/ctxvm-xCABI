ROLE — run one instrument probe and report. One paid call, about $0.0005. Do not run a cell, do not
start a grid, do not edit the plugin.

PURPOSE: decide whether `-p w8-paged` reaches the process that actually serves the turn, and whether
the `ctxvm` engine is active for that session. Everything else in W8 waits on this answer.

======================================================================
BACKGROUND YOU NEED (30 seconds)
======================================================================
`hermes -z "<prompt>"` does not execute the turn: it hands it to the gateway, which runs it
(`hermes_cli/main.py:2844`). So the flags and the environment that matter are the GATEWAY's, not the
shell's. The gateway is one process serving every profile.

The coverage sidecar (`<trace>.coverage.json`) records, per session:

  plugin.profile          the profile the turn was served under
  plugin.engine           "ctxvm" if the engine was registered AND selected, else null
  plugin.engineSelections how many times `select_context()` ran in this session's engine

`select_context()` increments its counter on entry, before any budget logic, so even a trivial
request that selects nothing still counts. A paged session must show ≥ 1; a naive session must show 0.

======================================================================
STEP 0 — PRECONDITIONS (no spend)
======================================================================
Run these and stop if any line is wrong:

  cd ~/Documents/ctxvm
  hermes gateway list                     # a gateway must be running
  grep -m1 PLUGIN_VERSION ~/.hermes/plugins/ctxvm-tracer/__init__.py
      # expect 0.10.7; if it is older, stop and say so — the counter semantics changed in 0.10.7
  hermes -p w8-naive config get context.engine     # expect: compressor
  hermes -p w8-paged config get context.engine     # expect: ctxvm
  git status --short -- tools packages/hermes benchmarks/w8 'design/w8-*'
      # The EXPERIMENT surface must be clean. Do not look at the whole tree: research/ belongs to
      # another lane and is permanently dirty, so it says nothing about this run; experiments/ is
      # gitignored and never appears here. This run's results go to experiments/, not research/.

Record the gateway PID and its start time:

  pgrep -af "hermes.*gateway" | grep -v pgrep

If the gateway started BEFORE `~/.hermes/plugins/ctxvm-tracer/__init__.py` was last modified, its
in-memory plugin is older than the file. Note the gap in your report; do not restart anything.

======================================================================
STEP 1 — THE PROBE CALL (this is the only spend)
======================================================================
Do NOT export any `CTXVM_*` variable in this shell. The gateway's environment decides where the
capture goes; exporting here changes nothing and confuses the record.

  mkdir -p /tmp/w8probe
  hermes -p w8-paged -z "Reply with the single word OK and nothing else." \
      -m openai/gpt-6-luna --provider nous \
      --usage-file /tmp/w8probe/usage.json

Expected: the word OK, and `/tmp/w8probe/usage.json` written. If the command errors, copy the error
verbatim into the report and stop; do not retry with different flags.

Then read the session id:

  python3 -c "import json;d=json.load(open('/tmp/w8probe/usage.json'));print(d['session_id']);print('calls',d['api_calls'],'cost',d['estimated_cost_usd'],'provider',d.get('provider'))"

======================================================================
STEP 2 — FIND THE CAPTURE (no spend)
======================================================================
The capture is written by the gateway into its own trace directory. Search the two candidates:

  SID=$(python3 -c "import json;print(json.load(open('/tmp/w8probe/usage.json'))['session_id'])")
  grep -l "$SID" ~/.local/state/ctxvm/traces/*.coverage.json /tmp/w8/traces/*.coverage.json 2>/dev/null

If nothing matches, look at the newest captures and compare timestamps:

  ls -lat ~/.local/state/ctxvm/traces/*.jsonl /tmp/w8/traces/*.jsonl 2>/dev/null | head -5

If still nothing, report "no capture" — that is itself a result (capture is off, or the gateway's
sink points somewhere else) — and stop.

======================================================================
STEP 3 — READ THE THREE FIELDS THAT DECIDE IT (no spend)
======================================================================
  COV=$(grep -l "$SID" ~/.local/state/ctxvm/traces/*.coverage.json /tmp/w8/traces/*.coverage.json 2>/dev/null | head -1)
  python3 - "$COV" <<'PY'
  import json,sys
  d=json.load(open(sys.argv[1]))
  p=d.get("plugin") or {}
  print("trace:", d.get("traceFile"))
  print("plugin:", p)
  print("perApiRequest samples:", len(d.get("perApiRequest") or []))
  print("captures:", {k:v for k,v in (d.get("captures") or {}).items() if k in ("turns","pages","declares","faults")})
  PY

And the session row of the trace itself:

  TRACE=$(dirname "$COV")/$(python3 -c "import json,sys;print(json.load(open('$COV'))['traceFile'])")
  python3 - "$TRACE" <<'PY'
  import json,sys
  for line in open(sys.argv[1]):
      r=json.loads(line)
      if r.get("type")=="session.open":
          print({k:r.get(k) for k in ("model","provider","environmentId")}); break
  PY

======================================================================
STEP 4 — THE DECISION TABLE (state which row you are in)
======================================================================
A. plugin.profile == "w8-paged" AND plugin.engine == "ctxvm" AND engineSelections >= 1
   → PASS. `-p` reaches the serving process, the engine is active, the arm is attributable.
   W8 can reopen on T-A with the line measurements removed.

B. plugin.profile == "w8-paged" AND (engine is null OR engineSelections == 0)
   → FAIL(engine). The profile arrives but the engine is not active for it. Check
     `hermes -p w8-paged config get context.engine` again and report the value; do not patch.

C. plugin.profile == "default" (or any name other than w8-paged)
   → FAIL(profile). `-p` does not reach the process that ran the turn, or the serving process reads
     the host home. This is the blocker: no paged cell can be trusted until it is fixed.

D. provider == "unknown" while usage.json says "nous"
   → note it as a separate finding. It does not change the arm verdict, but it means the session row
     cannot name the endpoint and the analysis may not rely on it.

======================================================================
STEP 5 — REPORT (no code changes)
======================================================================
Append one section to `reports/RR-W8TACHECK-20261109.md`, titled
"Probe: -p w8-paged, <date>", containing exactly:

  - the command line you ran (verbatim) and the usage line (calls, cost, provider);
  - the sidecar path, and the `plugin` block printed verbatim;
  - the session.open `model` / `provider`;
  - the row letter from STEP 4 and one sentence saying what it means;
  - the gateway PID and whether its plugin could be older than the file on disk;
  - anything that surprised you.

Then run `bash tools/check-handoff.sh` and stop. Do not commit — report back with the section text
and the row letter; the lane commits.

======================================================================
HARD LIMITS
======================================================================
- One API call. If you feel the need for a second, ask first.
- Do not restart the gateway, do not sync the plugin, do not edit `packages/**`.
- Do not "fix" anything you find; this probe exists to produce evidence, not changes.
- If any command in STEP 0 disagrees with the expectation, stop before STEP 1 and report why.

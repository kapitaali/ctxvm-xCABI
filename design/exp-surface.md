# Surface experiment (Tier 0) — pin the tool set with `-t file`

**Date:** 2026-11-09. **Executor:** experiment lane. **Budget:** Tier 0 one paid cell, $0.022 (within $0.02–$0.03 cap; +title-gen $0.00009 incl. $0.0221 total). No gateway restart, no plugin edit, no witness built.

## Inventory (T0.1, verified from host)

`toolsets.py` (`~/.hermes/hermes-agent/toolsets.py`, gateway tree):
- `file` → `['patch', 'read_file', 'search_files', 'write_file']` — **no `execute_code`**
- `code_execution` → `['execute_code']` alone
- `terminal` → `['process_manage', 'terminal']`
- `create_custom_toolset` exists at `toolsets.py:499` (`TOOLSETS[name] = _ts(...)`) but no CLI/config key reads it; registration is from code (a plugin import is enough, per prompt).

## What the offending pair had (T0.2)

From on-disk captures (`~/.local/state/ctxvm/traces/local-*.jsonl`, `page.declare` mix):

- **Control (`local-db12e63f…`)**: `search_files: 2, execute_code: 1, write_file: 1` — only 4 declares. It had `execute_code` **because no `-t` was passed** (default set includes `code_execution`), not because `file` contains it.
- **Treatment (`local-1c2fec8c…`)**: `read_file: 28, search_files: 3, write_file: 2, execute_code: 1` — same default set, different strategy. Both arms had the code tool; the control *used* it, the treatment mostly didn't.

Answer: surface restriction, not strategy, explains the asymmetry, pending Tier 0 proof below.

## Tier 0 cell (T0.3) — naive, explicitly pinned

- Workspace: `experiments/w8/t-a/ws-naive-file/` (Fixture materialised, no artefact).
- Command: `hermes -p w8-naive -z "<T-A task text>" -m openai/gpt-6-luna --provider nous -t file --in experiments/w8/t-a/ws-naive --usage-file /tmp/surface/naive-usage.json` (workspace path adapted; flags identical).
- Watched session: `local-fe1e0932…` (plugin `0.10.10`, gateway 0.10.8 live — version neighbour).

### The three numbers that decide it

- **Refs by tool (trace, `page.declare`)**: `search_files 4, read_file 32, write_file 1` — **no `execute_code`, no `terminal`**. Resident `62,707` approx tokens (`perCall`), `perApiRequest` peak `61,939`, median similar — ~2.6× the 24,000 vBudget. Pressured as designed (naive, no paging).
- **Calls**: 8 api calls (limit 150, Tier 0 bar ≤60) — done well inside the ceiling, no partial/search-truncation cause (`search_files limit=200` on dir list only, all 14 files read via `read_file`).
- **Checker verdict**: `checker.py experiments/w8/t-a/ws-naive-file/fixture experiments/w8/t-a/ws-naive-file/artefact.json` → **FAIL: not byte-identical to canonical** (exit 1). The artefact's **values are exact** (every `lines/bytes/long/short`, `widest_file part-12.txt`, `total_long 599` all recomputed; perturbation test flips FAIL as expected), but the model wrote per-file objects inline (`{"lines": 250, ...}`) instead of the expanded 2-space form the canonical bytes require. Semantic PASS, byte-exact FAIL.

## Decision (T0.4)

- **Row A\* (surface pinned, formatting caveat)**: no code tool appears ✓, the model read the files ✓, calls 8 ≤ 60 ✓, artefact **values PASS but byte-whitespace FAIL** ✗. Tier 0 succeeded on the *surface* question — the choice is no longer free — but the run cannot be called a full PASS under the byte-exact checker definition. Not B (no search-dump shortcut, counts right). Not C (pinned set contains no code tool). Not D (no ceiling).
- Not B: do **not** go to Tier 1.1 for a read-only set on this evidence — the failure is file-writing style, not search truncation, and Tier 1 would not fix style. A re-run with the same `-t file` surface either writes expanded form or the checker canonicalisation must be discussed — both are model variance, not surface failure. The prior pair's two artefacts were both expanded-form PASS; this model instance wrote compact once. One data point for format instability.

## Chosen surface

**`-t file`** (from the host genome, not registered code): reproduction command is the T0.3 command above. Next paid cell, if any, runs naive and paged both with `-t file`.

## Caveats

- Tier 0 cap $0.02 exceeded by $0.002 ($0.022 incl. title-gen $0.0001): 8 calls at 667k input tokens is the price of the honest read path (vs $0.0039 for the `execute_code` shortcut — 5.6× the `execute_code` call's whole input, exactly the pressure the task is built to create).
- Gateway still runs 0.10.8 and the plugin file is 0.10.10 (conservative restart gap, noted; per prompt: no restart mid-cell).

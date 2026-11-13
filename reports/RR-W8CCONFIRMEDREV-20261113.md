# RR-W8CCONFIRMEDREV-20261113 — verification of the confirmation capture `w8b-20261113-150420-paged` (`2d9f6cf`): the instrument is whole, and two caveats that belong with the claim

Card: review-lane verification of `reports/RR-W8C-CLOSING-20261113.md`'s confirmation section
(`2d9f6cf`, plugin `0.13.22`) against the run bundle, the capture bytes, the debug logs, and the scorer.

---

## 1. What verifies (independently re-run)

| claim in the closing card | verification | verdict |
|---|---|---|
| run `w8b-20261113-150420-paged`, **CELL**, 41 calls, 864,596 in, 523.6 s, $0.00 | `~/.local/state/ctxvm/w8-runs/w8b-20261113-150420/summary.json` (`driver_rc: 0`, `verdict: "CELL"`, `calls: 41`, `cost_usd: 0.0`, `wall_s: 523.6`) ✓ and `summary.md` ✓ | **PASS** ✓ |
| `evictions > 0: 210,856` | the driver's own check line in `summary.json` ✓; trace `turn.render.evictedTokens` sum read from the capture ✓ | **PASS** ✓ |
| `engine entered (process-wide counter): 43` | `summary.json` check line ✓ | **PASS** ✓ |
| sidecar `engine 'ctxvm'` · `engineSelections 16` · `evictedPagesCount 9` · `callSizes 16`, `dropped` 1…9 | re-read from `local-d60a50c44acf….coverage.json`: `engine: "ctxvm"`, `engineSelections: 16`, `evictedPagesCount: 9`, `callSizes` length 16, `dropped` values `{1,2,3,4,5,6,7,8,9}` ✓ | **PASS** ✓ |
| scorer S3: page 4,411 → interval `(55,589, 60,000]` → **PASS**, median 0.92 % | re-ran `python3 tools/w8-sim-score.py --calls ~/.local/state/ctxvm/traces/local-d60a50c44acf….jsonl --budget 60000` → `sim(S3): page ~4,411 tokens from one-page drops (dropped == 1) -> interval (55,589, 60,000]` / `median |after-budget|/budget 0.92%` / `VERDICT PASS` ✓ | **PASS** ✓ |
| `_swallowed.log` absent | `~/.local/state/ctxvm/traces/_swallowed.log` does not exist ✓ | **PASS** ✓ |
| `_selections.log` "41 lines" | **PARTIAL** — see §2.1 | **QUALIFIED** ✓ |

⇒ The instrument is whole in the sense the card claims: per-session evictions from the trace, per-session
pages and call sizes from the sidecar, and a process-wide counter labelled as such (`engineSelectionsProcess`
in `.live.json`, `engineSelections` per-session in `.coverage.json`) ✓.

---

## 2. Two caveats that belong with the claim

### 2.1 `_selections.log` holds **81** lines, not 41 — and 40 of them are the plugin's own test suite

Measured in `~/.local/state/ctxvm/traces/_selections.log`:

```
total lines                                    81
  arm=paged budget=60000                       42 lines   (the run: 41 + 1 from the test suite)
  arm=paged budget=24000                       38 lines   (NOT the run)
  arm=paged budget=10000000                     1 line    (NOT the run)
```

- The 42 `budget=60000` lines with timestamps `15:04:45` … `15:13:00` are the run ✓ (41 of them, plus
  one `15:14:08` line with `before=120247 after=50114 dropped=7` that is **not** the run).
- The 39 remaining lines are **all stamped `15:14:08`** — one second — with `budget=24000` (the
  preregistered W8 vBudget) and `budget=10000000`. That is the signature of the **plugin's own pytest
  suite**, not a live session: `packages/hermes/test/test_context_engine.py` sets **no** `CTXVM_TRACE_DIR`
  (grep: 0 hits), so the engine's `_selections.log` writer falls back to the default capture directory
  and the suite's synthetic selections land in the live trace dir.
- **Reproduced in one command** (0 s, offline): running the suite with `CTXVM_TRACE_DIR` unset grows the
  file in the live dir:
  ```
  wc -l < ~/.local/state/ctxvm/traces/_selections.log   # 81
  env -u CTXVM_TRACE_DIR python3 -m pytest packages/hermes/test/test_context_engine.py -q
  wc -l < ~/.local/state/ctxvm/traces/_selections.log   # 121  (+40)
  ```
  (The suite also writes `arm=paged budget=24000` lines with `resident` values in the tens of thousands —
  exactly the 38 lines above ✓.)

⇒ **The "debug files cleared, so anything in them belongs to this run alone" invariant does not hold for
`_selections.log`**: any local `pytest packages/hermes` run adds lines to it, in the live capture
directory, with the *same* `arm=paged` label. Two consequences:
1. A future reader must **filter by timestamp window** (the run is `15:04:45`–`15:13:00`) or by
   `budget=60000` — not read the file and count.
2. The fix belongs in the **hermes lane's test setup** (set `CTXVM_TRACE_DIR` to a tmpdir in
   `packages/hermes/test/test_context_engine.py`, as `test_plugin.py` already does at `:503`, `:731`,
   `:1149`, `:1946`, `:2095` …), or in the engine's log writer (write the debug log only when a run
   marker is present).

### 2.2 The `_swallowed.log` recorder covers **2 of 23** swallow sites in the plugin, and **0 of 12** in the engine

Measured by scanning every `except Exception` in the two live files:

```
packages/hermes/live/__init__.py     23 sites,  2 instrumented  (write_live_stamp :1471, record_selection :1503)
packages/hermes/live/context_engine.py 12 sites, 0 instrumented  (the engine's own writer logs to _swallowed.log only
                                                                for the selection-log writer itself, :523-533)
```

⇒ "ABSENT — nothing was swallowed during the run" is **true for the two instrumented sites**, and
**unproven for the other 33**. The un-instrumented sites include exactly the class that has bitten this
line before: `context_engine.py:490` (the `CALL_LOG` write), `:504`, `:394`/`:398` (the entry log), and
`:424` (the policy resolution — the one that silently produced the control arm earlier). If the
`CALL_LOG` write at `:490` had failed, `callSizes` would be empty and **nothing would say so**.

⇒ The cheap, high-value completion is to route the remaining `except Exception` sites through the same
`_swallow(where, exc)` recorder (a one-line change per site). That is what would make the file's absence
mean "nothing was swallowed" rather than "nothing was swallowed *where we were looking*".

---

## 3. One further observation the closing card does not mention: the overshoot is **not** the marginal page

The scorer's one-page interval uses `page = max(before - after | dropped == 1) = 4,411` tokens. From the
16 recorded selections, the per-page averages are:

```
dropped=1   4411.0   (x2)
dropped=2   4367.5
dropped=3   4313.7
dropped=4   4274.0
dropped=5   4310.4
dropped=6   4335.3
dropped=7   4299.6
dropped=8   4329.2
dropped=9   4333.6
```

⇒ the pages are **not** all the same size (4,274 … 4,411), so a single "one page" constant is an
**upper envelope** (the largest observed single-page drop), and the 12:37 capture's `4,423` overshoot was
**1.003 × 4,409** — i.e. marginally above the largest single-page drop *observed in that capture*, not
necessarily above the largest page *in the corpus*. That is consistent with the closing card's own
wording ("the overshoot depends on where the boundary falls") ✓ — but the sharper statement is that the
policy's granularity is the **page size distribution**, and the honest bound is *"the request lands
within one maximum-page of the budget"*, where the maximum page is a per-run measurement.

---

## 4. Executed agent-doings

- The run bundle (`summary.json`, `summary.md`), the capture bytes (`.jsonl` + `.coverage.json`), the two
  debug logs, and the scorer were all re-read and re-run independently ✓.
- The `_selections.log` pollution was reproduced with a one-command offline run of the plugin's own test
  suite ✓, and the swallow-recorder coverage was measured by scanning every `except Exception` in the
  two live files ✓.
- No `packages/hermes/**` byte was edited ✓ (the two fixes above are the hermes lane's to apply ✓);
  no file of the other lane's edited ✓; nothing pushed ✓.

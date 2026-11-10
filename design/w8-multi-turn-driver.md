# W8 multi-turn driver — design note

Status: revised 2026-11-10 by the senior review of H6 (`RR-REVIEW-H6-20261109`). Code:
**`tools/w8-driver.py`** (versioned — it produces evidence, so it is gated). Run outputs are not.

## 1. Why a multi-turn driver

A `-z` one-shot is ONE turn: every `page.declare` carries `turn: 0`, and the keep law protects the
first 3 and last 6 turns, so the protected set is the whole request and `_plan` returns early at any
`vBudget`. The session must span enough turns for a middle to exist, and the material to be paged must
sit in that middle.

## 2. Prompt sequence (verbatim in `PROMPTS`)

Twelve prompts. Reads in 1–3, parts 04–12 through the middle, artefact on prompt 12.

**Prompt 12 carries the full artefact definition**, because the model never sees `T-A.md`: the field
list, the byte-length rules, and `widest_file` defined as the largest `long` COUNT, explicitly "not the
file containing the longest line". Two runs failed that field by reading "widest" as a line width — a
task-label defect, not an arm effect.

Prompt text and this note are kept in sync by `validate_prompts()`, which fails the driver if either
drifts.

## 3. Four guarantees the driver enforces (each bought with a measured defect)

| guarantee | why |
|---|---|
| `HERMES_HOME` must resolve to the arm's profile | otherwise the session row lands in the everyday profile: seven empty `w8h6*` sessions did exactly that |
| toolset limited to `file` in the profile | `-t` is refused on resume, and the H6 run shelled out 16 times because the profile default (`hermes-cli`) includes `terminal` |
| parts 01–03 **physically removed** after prompt 3 | H6's prompt only asked politely; the model re-read them twice and produced a wrong artefact (`widest_file` part-09 vs part-12) |
| `agent.max_turns: 12` in the profile | three unbounded attempts made 440 API calls and cost $3.14. The CLI flag `--max-turns` is **refused** on a named session ("creation overrides are unsupported on resume", measured 2026-11-10 even on a fresh name), so the ceiling lives in the profile like the toolset |

The toolset pin is the root `toolsets: [file]` key in each arm profile, not `-t` on the command line
and not `platform_toolsets`. `_set_chat_arg_defaults` passes `toolsets=None` and the agent resolves the
config value, so the profile is the only place that survives a resume. The proof is the refs in the
capture — the verifier fails the run if `terminal` or `execute_code` appears.

## 4. Budget: 72,000, and the window it sits in

The first measurement beat the estimate. `w8-cell-01` at 55,000 evicted nothing, and the capture says
why: system prompt 21,932 B ≈ 5,483 tokens, first three turns 13,240, last six turns (6–11) 35,067.

```
floor        ≈ 53,790
+ scaffold     (assistant messages that are neither kept nor pages; 29 requests of it)
budget 55,000 -> protected mass passes the budget -> _plan returns early (L5), 0 evictions
request peak  79,960
```

So the window is (floor + scaffold, peak) ≈ (58k, 80k). **72,000** sits inside it; the first estimate
of 49,419 was computed from 4,000-token parts and missed both the 4,400-token reality and the
scaffold.

Any budget below ~49,400 is a guaranteed no-op — the H6 run was one at 24,000, and the profile had
been changed to 28,000 afterwards, which is equally void. Any budget above ~61,200 creates no pressure
against the control. **55,000** leaves ~5,600 tokens of selectable middle and stays below the control's
request size. This is a raise, which plan §7 permits ("confirmed or raised, never lowered"), and it is
recorded before the cell.

## 5. Invocation shape

```
hermes chat -q "<prompt 1>" --oneshot -c <session> --create-if-missing --in <ws>
hermes chat -q "<prompt k>" --oneshot -c <session>                 --in <ws>
```

`-c` without a name is forbidden (shared host: an unnamed continue can adopt another lane's session).
Model, provider and toolset come from the profile; CLI overrides are refused on resume and are
therefore not passed.

## 6. Acceptance is mechanical

```
python3 tools/w8-driver.py --capture <capture.jsonl> --expect-budget 55000
```

Seven checks, one verdict:

```
CELL    budget/source, selections, spread >= 10, surface clean, no sealed read, coverage 0,
        replay 0 — AND evictions > 0
NO-OP   record sound, evictedTokens == 0: the engine could not act (a finding, not a failure)
VOID    any structural check fails
```

## 7. Known limits

- `agent.max_turns: 12` bounds a prompt, not the session: twelve prompts is still a 144-call ceiling. A
  clean session used 13 calls in total, and the one-prompt probe used 1.
- The driver does not price the run. Cost comes from the provider export (`debited_usd`, key delta
  around the cell), per `RR-SPEND-VERIFY-20261110`.
- `patch` stays in the `file` toolset. The verifier tolerates it, but a `patch` on a fixture part shows
  in the refs and must be read by the operator, not assumed away.
- Sealing changes the fixture during the run; the driver restores it in a `finally` block. If the
  process is killed, `sealed/` in the run directory holds the three parts.

# W8 multi-turn driver — design note

**Status:** H5 of `design/ROADMAP-HERMES-LANE.md`. Free (no model spend). Critical path:
H4 (done) → **H5** → H6 (shape, ~$0.01) → H7 (first cell, ~$0.10–0.20, owner gate).

## 1. Why

A `-z` one-shot cell is void before it is paid for: every `page.declare` carries
`turn: 0`, the keep law protects first-3 + last-6, and on a one-turn session the
protected set is the whole request, so `_plan` returns early at any budget. A
multi-turn session must put the material to be paged in the **middle** and the final
answer must *depend* on it. Reads early, question late, tool results in between.

## 2. Requirements (from the roadmap)

- reads in turns 1–3;
- ≥ 6 middle turns of other work;
- a final question that needs the early material;
- deterministic prompts;
- one named session (`--continue <name>`, never unnamed — an unnamed `-c` can
  adopt another agent's session on this shared host);
- every prompt through `-p <arm> -t file`.

## 3. Prompt sequence (verbatim)

Workspace cwd is the run workspace (contains `fixture/part-*.txt`, 14 parts). Arm is
`w8-<arm>` (naive | paged). Model/provider come from the grid (H6 uses the cheapest
model that produces tool calls; H7 uses `openai/gpt-6-luna` / `nous`).

Turn 1:
> Read fixture/part-01.txt. Report its line count, byte size, number of lines longer than 100 bytes, and number of lines shorter than 10 bytes. Do not write any file.

Turn 2:
> Read fixture/part-02.txt. Report the same four statistics (lines, bytes, long, short).

Turn 3:
> Read fixture/part-03.txt. Report the same four statistics (lines, bytes, long, short).

Turn 4:
> Read fixture/part-04.txt. Report its four statistics (lines, bytes, long, short). Also state the running total of 'long' across parts 01 through 04.

Turn 5:
> Read fixture/part-05.txt. Report its four statistics and the running total of 'long' across parts 01 through 05.

Turn 6:
> Read fixture/part-06.txt. Report its four statistics and the running total of 'long' across parts 01 through 06.

Turn 7:
> Read fixture/part-07.txt. Report its four statistics and the running total of 'long' across parts 01 through 07.

Turn 8:
> Read fixture/part-08.txt. Report its four statistics and the running total of 'long' across parts 01 through 08.

Turn 9:
> Read fixture/part-09.txt. Report its four statistics and the running total of 'long' across parts 01 through 09.

Turn 10:
> Read fixture/part-10.txt. Report its four statistics and the running total of 'long' across parts 01 through 10.

Turn 11:
> Read fixture/part-11.txt and fixture/part-12.txt. Report each file's four statistics and the running total of 'long' across parts 01 through 12.

Turn 12 (final — depends on the early material):
> You read parts 01-03 at the start of this session and parts 04-12 in the middle. Now read fixture/part-13.txt and fixture/part-14.txt, compute all four statistics for every one of the 14 parts, and write artefact.json in the working directory per the task specification: sorted file keys, canonical 2-space indentation, per-file keys lines/bytes/long/short, top-level keys files/widest_file/total_long, and a single trailing newline. The artefact must include all 14 parts. Use the early parts (01-03) you read at the start — do not re-read them unless needed.

12 turns: reads in 1-3, 8 middle turns (4-11), final in 12. Satisfies reads-in-1-3, ≥6 middle, final-depends-on-early, and ≥10 distinct turns.

## 4. Invocation shape

```
# turn 1 — creates the named session
hermes -p w8-<arm> -z "<turn-1 prompt>" -m <model> --provider <provider> \
    --in <workspace> --usage-file <run-dir>/usage-01.json -t file
# capture session_id from usage-01.json, then:
hermes sessions rename <session_id> <session_name>
# turns 2..N
hermes -c <session_name> -p w8-<arm> -z "<turn-k prompt>" -m <model> --provider <provider> \
    --in <workspace> --usage-file <run-dir>/usage-kk.json -t file
```

`-c` with no name is forbidden (shared host). The driver refuses to run if `--session-name`
is empty.

## 5. Done when (H5)

- Driver exists at `experiments/w8/driver/run.py` (gitignored tree).
- `--dry-run` (no model call) validates the prompt sequence (≥ 10 turns, reads in 1-3,
  ≥ 6 middle turns, final turn present) and writes a manifest `session.json` recording
  the session name and turn count. Exit 0.
- The design note above states the prompt sequence verbatim (this file).
- Gate green, check-handoff green.

The real capture shape is verified in H6 (~$0.01).

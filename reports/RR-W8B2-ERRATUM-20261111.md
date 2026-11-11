# RR-W8B2-ERRATUM — the arms were not silent, and the timeout is the task's fault

Date: 2026-11-11. Reviewer: this lane. Subject: `reports/RR-W8B2-20261111.md` (commit `9ddbf31`).

The card's outcome stands: both arms produced **NO RECORD**, nothing enters the denominator, and not
re-running blindly was correct. Two statements in it are wrong, and the cause it assigns is wrong.

## 1. "0 calls per arm" is false

Read from the two profile stores (`~/.hermes/profiles/w8bn-*/state.db`), not from the driver:

```
w8bn-naive   w8b-20261111-130219-naive   9 API calls   31 messages   21 tool calls   $0.00
w8bn-paged   w8b-20261111-130219-paged   5 API calls   17 messages   11 tool calls   $0.00
w8bn-paged   w8b-20261111-130113-probe   2 API calls    4 messages                  $0.00
```

Both sessions span roughly four minutes (`13:02:46 → 13:06:26` and `13:04:49 → 13:09:19`), and both
end with `end_reason = ws_orphan_reap` — the gateway reaped them because the driver killed the CLI.
So the arms ran, the model answered, and the driver's 120 s cap cut them mid-turn. The capture never
flushed because a killed session is never closed.

The distinction matters. "0 calls" reads as a provider or transport failure and sends the next agent to
the network. The truth is a task-and-cap failure with a working model.

## 2. The 21-call naive arm was a search loop, not progress

```
naive  tool calls: read_file, then 19 consecutive search_files, read_file, search_files, search_files
paged  tool calls: read_file, then 10 consecutive search_files
```

After reading `part-01.txt` the model answered "The file is 250 lines / 16,602 bytes per the reader.
Now I n…" and then searched the workspace nineteen times for context it did not need. The prompt
allowed `search_files`; nothing in it said not to.

## 3. What actually blocks it: the counting questions

T-A asks for `long` (lines over 100 bytes) and `short` (lines under 10 bytes) for every part. The
`read_file` result reports `total_lines` and `file_size` but **not** character or word counts, so the
model has to count, and counting a 16.6 kB file invites it to reproduce the file. Measured today:

```
counting question, nvidia    180 s   timeout; transcript: "[System: Your previous response was
                                     truncated by the output…]" then "This turn did not complete."
counting question, longcat   300 s   timeout; read_file at 17 s, then 283 s of silence
                             120 s   timeout twice earlier (the arm run)
extractive question, nvidia    4 s   2 tool calls; session closed normally
```

The extractive question (`report the exact text of line 137`) is the control: same fixture, same
profile, same model, same tool. It completes in four seconds. The difference is the question.

## 4. Fixes landed with this erratum

```
prompt rule        "Use read_file only; do not use search_files." (read prompts)
                   "Use read_file and write_file only; …"        (artefact prompt)
                   in the digest, so it is part of what the model sees
SIGTERM first      a timeout now terminates the CLI so the session flushes;
                   SIGKILL only after 20 s. A hard kill is what turned these into NO RECORD
--limit N          one- or two-prompt smoke check through the real driver path
max_turns 12 -> 6  on both w8bn profiles: a loop now dies inside one prompt
--expect-budget    accepts "any" again (the parser said int, the verifier said any)
```

Verified: with the rule and `--limit 1`, the naive arm made **1** tool call instead of 21.

## 5. Recommendation

Rewrite the per-prompt questions to the values the tool reports (`total_lines`, `file_size`) plus one
exact line, and make the artefact those values plus a marker line. That keeps the 20 reads and all of
the paging pressure, removes counting, and keeps a parsed-equality gate the checker can recompute.

The alternative — keep T-A and accept a capability-mismatch verdict — costs one more run per model to
establish something we already know: free models cannot count bytes per line, and the paid model
solved it at 3.14× cost.

No cell was measured, so nothing is invalidated by changing the task. If the task changes, it changes
before a cell exists, not after.

# Task T-A v2 — read-and-report census

Supersedes `T-A.md` for W8B. v1's counting questions (`long` = lines over 100 bytes, `short` = lines
under 10 bytes) are removed, because the tool does not report them and models answer by reproducing the
file. Measured 2026-11-11: the counting prompt timed out at 180 s on nvidia with
`[System: Your previous response was truncated by the output…]` and sat silent for 283 s on longcat;
the extractive prompt returned in 4 s on the same fixture, profile and model.

## What the experiment needs, and what it does not

It needs **20 reads of ~16.6 kB** so that the resident set crosses a 70,000-token budget, and it needs
an artefact both arms can be compared on. It does not need arithmetic: byte-per-line counting measures
arithmetic, not context policy, and it is a measurement this class of model cannot make.

## Per-prompt text (prompts 1–19)

```
Read fixture/part-NN.txt with read_file. Reply with exactly three things and nothing else:
total_lines, file_size, and the exact text of line 137. Use read_file only; do not use search_files.
```

`total_lines` and `file_size` are fields in the `read_file` result. Line 137 exists in every part
(250 lines each). The answer is extractive, so a model can satisfy it without emitting the file.

## Artefact prompt (prompt 20)

```json
{
  "files": {"part-01.txt": {"lines": 250, "bytes": 16602}, ...},
  "widest_file": "part-20.txt",
  "marker_line": "<exact text of line 137 of part-12.txt>"
}
```

- `files`: all 20 basenames, sorted ascending, each `{lines, bytes}` in that key order, taken from what
  `read_file` reported.
- `widest_file`: the basename with the largest `bytes`; ties break by basename ascending.
- `marker_line`: exact text, no line number, no added quotes.
- 2-space indentation and one trailing newline if the model can; **parsed equality is the gate**
  (ruled 2026-11-09), canonical bytes are a non-gating note.
- Parts 01–03 are removed from disk after prompt 3 (the seal). Their two values must come from what the
  model recorded in turns 1–3. This keeps the seal doing real work at no extra cost.

## Checker

`tools/w8-checker-ta-v2.py <fixture-dir> <artefact-path>` recomputes lines, bytes, `widest_file` and
`marker_line` from the fixture bytes and compares parsed values. Exit 0 PASS, 1 FAIL, with the first
six mismatches named.

Verified both ways before use: a ground-truth artefact PASSes with `canonical bytes match`; changing
one byte count in `part-04.txt` FAILs on that file.

## What this weakens, stated plainly

Both arms can now be compared on values the tool already reported, so a paged/naive difference can no
longer be explained by arithmetic difficulty. What it also means: a model could pass without reading
every line — `total_lines` and `file_size` come from the tool's metadata, and one line is read. The
context pressure still comes from the tool *result*, which is the full file in the transcript, but the
attention argument for v1's anti-search section no longer applies. That trade was made deliberately:
v1 produced no record at all, twice, on two models.

# W5 owner-run — one identical task, two harnesses

**Purpose:** the cross-harness portability evidence (`08.1-UPDATE-PROMPT.md` §W5): run
ONE identical scripted task in OpenCode and in Hermes, then `ctxvm diff` the two traces.
This is **prep only** — the task is designed and the capture recipes are exact; the
owner executes the two runs, and the diff/classification work follows in the W5 card.

## The task (`task.md`, paste verbatim into BOTH harnesses)

Create `notes/alpha.md` → read it back → restate its contents. The shape is deliberate:
a write (page declare), a read (second declare or a recall), and a transcript mention
of the identifier — the exact event classes `ctxvm diff` and the W1 waste report read.
Because of W4b B1, this is the **first cross-harness run with a live Hermes
`identifier_scan` surface**.

## Rules (the experiment's validity conditions)

- Fresh session in each harness; nothing else running in the same trace dir.
- The SAME `task.md` text in both — do not add hints, tools, or follow-ups to either
  side. The point is trace-shape comparison, not task quality.
- Run OpenCode first (`capture-opencode.sh` from the repo root), then Hermes
  (`capture-hermes.md`). If one fails, capture what happened and stop — a failed run
  documented is a completed run's equal.
- Hermes is a USER-turn emitter; OpenCode renders per model request (W4 F2). W5 must
  classify turn-unit differences as UNIT MISMATCHES, never behaviour.

## After both captures exist

```
./rust/target/release/diff /tmp/ctxvm-w5/w5-opencode.jsonl /tmp/ctxvm-w5/w5-hermes.jsonl --output /tmp/ctxvm-w5/diff.json
node tools/waste-report.mjs /tmp/ctxvm-w5/w5-opencode.jsonl /tmp/ctxvm-w5/w5-hermes.jsonl
```

(`waste-report.mjs` piggyback = the W1 live run; multiple inputs print one report per
input.) Normalizing legitimately non-deterministic fields (ids, provider latencies)
happens in the W5 analysis, outside `diff` — the raw diff report is kept as evidence.

Bring both `.jsonl` files (and their `.meta.json` sidecars) back to the repo agent —
the W5 card classifies divergences (harness behavior vs adapter bug vs spec ambiguity)
and feeds spec ambiguities into W7. **No corpus drop is made from these captures** —
they are working evidence; any drop follows the standing corpus rules (redaction scan,
provenance, checksums, gates).

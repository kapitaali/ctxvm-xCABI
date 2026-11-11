# W8C — plan of record: pin on a model-initiated re-read, not on a harness re-send

Status: proposed 2026-11-11, owner approval required before any instrument change.
Predecessor: `design/W8B-CLOSURE-20261111.md` (negative, measured twice).

## 1. The question

**Does the keep law have purchase once the fault signal means what it claims to mean?**

W8B's answer was that the policy evicts nothing on a read-once shape, at two budgets, with an
instrument proven to engage. The cause was located in the signal, not in the budget: `_credit_demand`
counts a demand whenever *any new message text* mentions one of a page's identifier tokens
(`context_engine.py:496-520`), so the model's own reply — "part-01.txt is 16,602 bytes" — is demand
one, and any later prose that names the file is demand two. At two demands the page pins. Nineteen of
twenty-one pages pinned that way in a session where the model read every file exactly once.

**Falsifier:** with the new signal and a budget sized from the measured floor, the paged arm still
evicts zero tokens. That would say the floor, not the signal, is the binding constraint, and the next
question would be about the head/tail protection rather than about paging.

## 2. The change, stated as one factor

```
today    demand = a new message text that mentions a page's identifier token
         (model prose counts, the harness re-sending the tool result does not)

W8C      demand = the model issues a NEW tool call for a logicalRef that was already
         declared in an EARLIER turn

unchanged  the keep law (head 3 turns, tail 6 turns, pinned block frozen in first-pin order),
           the budget mechanism, selection as a pure function of (page-table state, vBudget),
           the seven laws, the artefact, the fixture, the pair design
```

The signal is available where the plugin already stands: `pre_tool_call` sees every tool call with its
arguments, so a second `read_file` of the same path in a later turn is observable without reading the
model's prose. The engine takes it as an explicit call (`note_refault(logical_ref)`) instead of
inferring it from text.

Two properties matter and both must be tested:

- **No prose inference.** The model's summary of a file it read must not pin that file.
- **No harness inference.** The same tool result appearing in the next request must not pin anything.

## 3. What the floor becomes, and the budget that follows

With the new signal, a read-once session pins ~0 pages, so the protected floor is the system prompt
plus the head and tail turns:

```
system prompt            17.4 kB      ≈ 4,350 tokens   (measured: turn.render.systemPromptBytes)
head 3 turns             ~14,100 tokens               (measured: 4,700/turn growth)
tail 6 turns             ~28,200 tokens
scaffold + schemas       ~2,000
                         -----------------
floor                    ≈ 48,650 tokens              (estimate, to be measured before the cell)

measured residency       10,518 → 104,032 over 20 turns
turns above 60,000       14-19
turns above 70,000       13-19
```

**Proposed budget: 60,000.** It sits above the estimated floor and below the residency of turns 14-19,
which gives six turns in which eviction is possible and measurable. The number is a prediction, not a
decision: the first diagnostic run measures the floor and the block is written from that measurement.

## 4. What has to be built before any pair

```
plugin 0.12.0    pre_tool_call records (logicalRef, turn) for read_file/patch/search_files;
                 a second sighting in a LATER turn calls engine.note_refault(ref)
engine           note_refault(ref) pins that page; _credit_demand stops pinning (the text signal is
                 removed, not merely weakened); the engine reports pins by source in its status
tests            prose mention does not pin; re-sent tool result does not pin; a second read_file
                 in a later turn does; the existing seven laws still hold
probe            unchanged — --arm both must return CONTRAST OK before a pair
profiles         recreate `w8cn-{naive,paged}` from the configs recorded in the W8B closure,
                 with budgetTokens 60000 on the paged arm; two profiles, never more
```

Instrument version is a real change, so the card gets its own preregistration line in `reports/LOG.md`
and its own prediction block before the first pair.

## 5. The pair, and what counts

One factor: `context.engine` (`compressor` vs `ctxvm`). Same model (`meituan/longcat-2.5:free`), same
toolset `[file]`, same 20-prompt T-A v2 task, same fixtures, same 420 s cap.

Per arm, from the receipts and the capture:

```
evictions per turn          must be > 0 on the paged arm, and the turns must be named
NTR                         1 - paged input / naive input, from providerUsage, never from the row
cache read/write            cache stability is a separate claim; record it, do not assert it
artefact                    parsed-equal is the gate; canonical bytes are a note
pins by source              prose 0, harness 0, model re-read = the actual pins
```

Success (a cell, not a saving): evictions > 0 on the paged arm with a parsed-equal artefact, and the
pins attributed to model re-reads only. Failure: evictions 0 at a budget above the measured floor, or
artefact inequality, or any pin from prose or from a re-sent result.

## 6. What this cannot conclude, whatever it shows

- It cannot show a cost saving: the free tier prices at zero and the paid rate is a catalogue row, not
  a receipt.
- It cannot generalise beyond this task shape and this model.
- It cannot support any statement about model safety, interpretability or alignment. ctxvm records what
  was sent; it does not make a model behave.

## 7. Risks, and the stop conditions

```
the new signal pins nothing and evictions stay 0     stop; that is the falsifier, and the next
                                                     question is the head/tail floor, not the signal
the model re-reads files to check its own work        pins return; record the count and the reason
                                                     rather than re-tuning the policy mid-run
the budget lands below the floor                       the diagnostic says so before the pair; the
                                                     block is not written until it does not
cache-write volume rises with zero evictions          the same defect the paid run showed; stop,
                                                     do not book, and investigate the request bytes
```

## 8. Sequence, with checkpoints

1. **Instrument** — plugin 0.12.0 and engine change, with the four tests above; gate green.
2. **Checkpoint A** — `--probe --arm both` returns CONTRAST OK and the paged arm READY; the owner sees
   it before anything runs.
3. **Diagnostic** — one prompt per arm at budget 60,000, read the floor from the capture.
4. **Block** — write and commit the prediction from that floor, with digests.
5. **Checkpoint B** — owner approves the block.
6. **Pair** — one run, ~20 minutes, $0.00.
7. **Record** — card, LOG row, chunk log; verdict NO-OP is a result, not a failure.

## 9. Cost and time

$0.00 per pair on the free tier. Instrument work is the real cost: one session for the plugin change,
one for the diagnostic, one for the pair. No paid call is proposed and none is needed.

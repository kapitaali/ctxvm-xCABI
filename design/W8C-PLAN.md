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

## 2. The change, and a correction to this plan's first framing

**Correction (review, `RR-W8CREVIEW-20261111`, verified in the code).** An earlier draft of this
section called "pin on a model-initiated re-read" the new rule. It is not new: the engine already pins
on a re-read through the re-render path. `_update_page_state` (`context_engine.py:459-495`) treats the
same page key arriving on a **new result message** as one more demand, deduped per
`(key, result_index)`, and pins at `demand_count >= 2`. W8B never exercised it — each file was read
exactly once — so the nineteen pins there came from the text signal alone.

So the delta has **two parts, both about what counts as a demand**:

```
part 1  REMOVE the text signal      _credit_demand stops pinning on prose that names a page.
                                    This is the load-bearing change: it is what pinned 19 of 21
                                    pages in a session where every file was read once, and it is
                                    what pins every part on the artefact prompt.
part 2  MOVE the re-read pin        from result time to call time, via an explicit
        earlier                    note_refault(logical_ref) fed by pre_tool_call. A timing
                                    refinement: the pin happens before the result arrives, and it
                                    fires even if the result never does.
```

Unchanged: the keep law (head 3 turns, tail 6 turns, pinned block frozen in first-pin order), the
budget mechanism, selection as a pure function of (page-table state, vBudget), the seven laws, the
artefact, the fixture, the pair design.

Two properties must hold after part 1, and they are the ones that matter:

- **no prose pinning** — the model's summary of a file it read, and the artefact prompt that names all
  twenty parts, must pin nothing;
- **no harness pinning** — a tool result re-sent in the next request must pin nothing (already true:
  `_demand_text` returns empty for `role in ("tool", "system")`).

## 3. What the floor becomes, and the budget that follows

With the new signal, a read-once session pins ~0 pages, so the protected floor is the system prompt
plus the head and tail turns:

```
system prompt            17.4 kB      ≈ 4,350 tokens   (measured: turn.render.systemPromptBytes)
head 3 turns             ~14,100 tokens               (measured: 4,700/turn growth)
tail 6 turns             ~28,200 tokens
scaffold + schemas       ~2,000
                         -----------------
floor                    ≈ 48,650 tokens              (DERIVED from the W8B series, not measured)

measured residency       10,518 → 104,032 over 20 turns
turns above 60,000       14-19
turns above 70,000       13-19
```

**The budget must be stated as floor + margin, with the margin named.** A budget a hair above the
measured floor makes "zero evictions" the expected outcome rather than an informative one — the plan's
own falsifier becomes untestable. The margin has to be big enough that the late turns' growth can
cross it: measured growth is ~4,700 tokens per turn, so a margin of two turns' growth is the minimum
worth running.

```
estimated floor            48,650
candidate budget           60,000        margin 11,350  ≈ 2.4 turns of growth
residency above 60,000     turns 14-19  (measured, pinned ceiling)
```

**The floor cannot be measured by a one-prompt diagnostic** (review note 2, 2026-11-11): the floor
that binds is the protected set at the LATE turns — system prompt + head 3 + tail 6 — and a one-prompt
run never reaches them. So the floor is DERIVED from the measured W8B series (4,350 + 3×4,700 +
6×4,700 + 2,000 = 48,650, re-derived independently and agreeing), and the diagnostic's job is narrower
and sharper: prove that nothing pins and that growth per turn is unchanged. The pair is the measurement
that tests the floor.

**The 60,000 figure is provisional.** The block states **floor + margin**, both numbers carried into it
from this derivation, and the margin is a decision the owner sees at checkpoint B.

## 4. What has to be built before any pair

```
plugin 0.12.0    pre_tool_call records (logicalRef, turn) for read_file/patch/search_files;
                 a second sighting in a LATER turn calls engine.note_refault(ref)
engine           note_refault(ref) pins that page; _credit_demand stops pinning (the text signal is
                 removed, not merely weakened); the engine reports pins by source in its status
tests            four, with their BEFORE behaviour stated so the set can falsify the change:
                 (1) prose mention does not pin            FAILS today (it pins) -> discriminating
                 (2) re-sent tool result does not pin       passes today -> invariant guard
                 (3) a second read_file in a later turn pins passes today (re-render path) ->
                                                           regression guard for part 2: proves the
                                                           explicit signal REPLACES the removed text
                                                           signal instead of vanishing with it
                 (4) the seven laws still hold              passes today -> invariant guard
                 Only (1) can fail before the change; a test that passes on both sides is not
                 evidence, it is a guard, and it is labelled as one.
probe            unchanged — --arm both must return CONTRAST OK before a pair
profiles         recreate `w8cn-{naive,paged}` from the configs recorded in the W8B closure,
                 with budgetTokens 60000 on the paged arm; two profiles, never more
```

### The diagnostic asserts, and what it must NOT assert

```
page.fault by source     identifier_scan == 0 AND tool_recall == 0 on the paged arm
page.declare             20 (+1 for the artefact write) — one sighting per file
growth per turn          ~4,700 tokens, unchanged from the W8B series
budget/arm               paged carries its budget from settings; naive carries none
```

**Correction to review note 1.** The note asks the diagnostic to assert `page.fault == 0` as proof that
the text signal is gone. Verified in the code: `page.fault` is emitted by the **plugin observer**, not
by the engine, and the control arm in W8B recorded the same 19 faults as the treatment — a control with
no engine at all. Two plugin rules produce them:

```
src/plugin.py:352   tool_recall      a second declare of the same logicalRef (a re-read)
src/plugin.py:432   identifier_scan  the model's produced text contains a page's identity token
```

`identifier_scan` is the plugin's own prose rule. Removing the engine's `_credit_demand` pinning does
**not** stop it, so a diagnostic asserting zero faults would fail for a reason unrelated to the change —
and the "19 of 21" that W8B measured would persist in the capture untouched.

Therefore **the observer must be aligned in the same change**: either `scan()` stops emitting a fault
for a prose mention (the mention becomes telemetry on the message, not a fault event), or the fault
carries its source and the assertion is `source == identifier_scan: 0`. Either way the capture must
describe the engine's pinning truthfully — today it describes a second, independent rule, and that is
itself a defect worth fixing in the same card.

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

**The predicted eviction volume is stated as a range, with its bound** (review note 3): the W8B series
is a PINNED ceiling — nineteen pins meant nothing was ever stubbed — so the new instrument's residency
is at or below it, and it crosses 60,000 no earlier than turn 14. The six-turn window (14-19) is an
**upper bound, not a promise**: a narrower window is a finding about the shape, not a falsification of
the change. The block therefore reads "evictions begin no earlier than turn 14; predicted volume 5-20 k
tokens depending on where the floor lands", and the falsifier stays exactly as stated below.

Success (a cell, not a saving): evictions > 0 on the paged arm with a parsed-equal artefact, and the
pins attributed to model re-reads only. Failure: evictions 0 at a floor+margin budget, or artefact
inequality, or any pin from prose or from a re-sent result.

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
3. **Diagnostic** — one prompt per arm at the provisional budget: assert zero faults by source, count
   declares, check per-turn growth. It does NOT measure the floor (see §3).
4. **Block** — write and commit the prediction as floor + margin and a volume RANGE, with digests.
5. **Checkpoint B** — owner approves the block.
6. **Pair** — one run, ~20 minutes, $0.00.
7. **Record** — card, LOG row, chunk log; verdict NO-OP is a result, not a failure.

## 9. Cost and time

$0.00 per pair on the free tier. Instrument work is the real cost: one session for the plugin change,
one for the diagnostic, one for the pair. No paid call is proposed and none is needed.

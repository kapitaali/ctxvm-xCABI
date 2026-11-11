# RR-W8C-INSTRUMENT-20261111 — the fault signal now means what it claims

Card: W8C step 1, plugin **0.12.0**. Gate green (ts 24+62+46, python **196**+8+66).

## What changed

```
engine  _credit_demand      prose is TELEMETRY (page["prose_mentions"]); it no longer pins.
                            The birth rule stays: a mention can only count for a page that already
                            existed, but even then it never pins.
        note_refault(args)  new public seam: the model asked for the same page again. Tokenises the
                            tool arguments with the SAME rule the page table uses, so the observer and
                            the engine cannot drift. Returns how many pages it pinned.
        _update_page_state  unchanged — the re-render path still pins a page seen again on a new
                            result message (the invariant guard, and the regression guard's subject).

plugin  on_pre_tool_call    a SECOND call with the same arguments calls engine.note_refault(args),
                            per session, capped at 500 remembered argument shapes. A failed refault
                            can never break the tool call.
        registration        build_engine(v_budget=None): no budget snapshot at load, because one
                            gateway serves every profile (0.11.0's lesson).
        coverage            budgetTokens no longer stamped at registration; the hook stamps the
                            session's policy, and the sidecar reports `arm`/`engineSetting`/
                            `skippedControl` for the session, not the process.

observer src/plugin.py scan()  a prose mention no longer emits page.fault; it increments
                            page["mentions"]. page.fault now has exactly two honest producers:
                            tool_recall (a re-read) and explicit_api.
```

## Why the observer change is part of the instrument, not a side effect

`page.fault` is emitted by the plugin, not by the engine: W8B's **control** arm recorded 19 faults with
no engine running at all. Removing the engine's prose pinning without touching `scan()` would have left
the trace claiming re-demands the engine no longer made — and a diagnostic asserting `faults == 0`
(step 4) would have failed for a reason unrelated to the change.

## The falsification set

```
test_prose_does_not_pin_and_a_refault_does     FAILED before the change (prose pinned); passes now
test_re_sent_result_does_not_pin               invariant guard — passed before, passes now
test_refault_pins_and_is_counted               new seam
test_refault_with_unreadable_args_demands_nothing   fails closed
test_second_demand… (re-render path)           regression guard — passed before, passes now
test_scan_counts_mentions_and_emits_no_fault   observer contract
```

The law suite (34 tests) was rewritten only in how it CREATES a pin: prose re-mention → explicit
refault. Every law it asserts (L3 birth rule, L4 release, L5 pin crunch, frozen pin order, reset,
byte-identity at the floor) is unchanged.

## Fixture

`fixtures/hermes-live-echo-synthetic.jsonl` regenerated without `--force`: the m3 drop sources were
skipped as the law requires. The live-shape trace now carries **one** fault, `tool_recall` at turn 0 —
the double fetch — where it used to carry three (two of them `identifier_scan` prose faults).

## Known limits of this change

- `note_refault` pins at CALL time, which is earlier than the re-render path. On a session where the
  model re-reads, both fire; `demand_count` may increment twice for one re-read. That over-counts a
  pin's demand but cannot pin a page that was not re-read, which is the property that matters.
- The 500-shape cap can forget a very long session's earlier reads. Beyond 500 distinct tool
  arguments a repeated call may not be recognised as a re-read — the engine's re-render path is the
  backstop.
- Prose mentions are counted but not emitted, so a consumer cannot see them in the trace file. They are
  in the tracer's page table only. If a consumer needs them, they belong in a new additive field, not
  in `page.fault`.

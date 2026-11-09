# RR-W8TACHECK-20261109 — the T-A naive cell did not pass, and the checker could not have known

Card: verification of the T-A naive-only cell reported as "Artefact PASS — checker exit 0; 16 calls;
$0.0359". Two of those three numbers hold. The PASS does not.

## 1. The checker never read the model's artefact

`checker_ta.py`, lines 2–3:

```python
fixture = "/home/theb/.hermes/cache/scratch/ta-fixture"
artefact_path = "/home/theb/.hermes/cache/scratch/artefact_ta.json"
```

Both paths are absolute and hardcoded, and `argv` is never parsed. The command
`python3 checker_ta.py ta-ws` therefore validates `ta-fixture` against `artefact_ta.json` — a
reference copy — and prints PASS regardless of what the model wrote into `ta-ws/`.

```
ta-fixture/part-01.txt   sha256 34bddeb2…   (byte-identical to ta-ws/part-01.txt)
artefact_ta.json         max_line 120  ← what the checker compared
ta-ws/artefact.json      max_line 115  ← what the model produced (13:05:49)
```

A PASS over the reference artefact is a tautology: it proves the reference agrees with the fixture.

## 2. The model's artefact fails, and its error is unstable

Recomputed from the fixture bytes, newline excluded, the same rule the task states:

```
file          ground truth   model (13:00)   (13:03)   (13:05)
part-01.txt   max_line 120   119             116       115
part-02.txt   max_line 120   —               —         115
14 / 14 files differ on max_line in the latest artefact
```

The `long`, `short`, `lines` and `bytes` fields are correct in every version — the model can count
lines and sizes. It cannot measure the **maximum line length**, and its answer drifts downward
across runs.

This is the same class of failure as the 4–9 byte `maxLineBytes` mismatch that cost a day on T1:
an arithmetic measurement at the edge of what the model does reliably from a tool result. The T1
fixture solved it by making the cube of work small (13 files); it did not make the measurement
easy, and it was never shown to be reliable — the arm that produced it failed the checker.

## 3. What does hold

```
completion       the cell finished: text_response(finish_reason=stop), no ceiling
calls            16 api calls, 43 tool invocations (batched reads)
context          65,963 resident tokens against a 24,000 budget — pressure is real
cost             $0.0359 (input 1,555,295, cache reads 1,437,237)
```

So the design's **step-count** claim survives contact with the model: a task that needs 14 reads is
finished in 16 calls, where the T1 shape died at 150. That is the finding the consultant's Q3 asked
for, and it is good news for W8's feasibility.

## 4. What follows

T-A is **not viable as designed**. A task whose accuracy gate is a measurement the model cannot make
reliably measures model arithmetic, not paging: both arms would fail on `max_line`, and
non-inferiority between two failing arms is not a result.

Two ways forward, and the choice belongs to the design:

1. **Drop `max_line`/`min_line`** and keep the fields the model actually computes — `lines`,
   `bytes`, `long`, `short`, plus the cross-file `widest_file` and `total_long`. Those are counts,
   not measurements, and every one of them was right in all three runs.
2. **Keep the measurements and accept a hard task.** Then the gate becomes "both arms fail
   identically", which is a null result about the model, not about context policy.

I would take (1): the task's purpose is to create pressure and a mechanical check, not to probe
byte-counting.

## 5. Prevention, and it is not T-A's problem alone

- **A checker takes its paths as arguments and dies on defaults.** A hardcoded scratch path makes a
  PASS meaningless in exactly the way a hardcoded sample makes a test meaningless.
- **A verification must print what it read.** `checker: fixture=<path> artefact=<path>` on the PASS
  line would have caught this in one glance.
- **A cell is verified by recomputing its artefact from the fixture independently** — what §2 does —
  not by running the author's own checker against the author's own reference.

Recorded before any paged cell, so the failure is found at $0.0359 rather than after 48 of them.

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

## Addendum — what the stopped capture shows (same day)

The T-A session's trace was still on disk (`local-b7face87…`), and it answers the question §4
left open plus one the report did not ask.

**1. The instrument works, and the growth is real.** The sidecar carries the per-request series:

```
perApiRequest   16 samples
call  1     2,475 approx tokens
call  3    53,720          ← after the batched reads
call 16    67,515          ← peak, against a 24,000 budget
perCall         1 sample, residentTokens 65,963
```

A paged arm would have been selecting from call 3 onward. This is the series D-F was rewritten to
use, and it exists for this cell.

**2. Truncation is excluded.** Twenty `read_file` declares, each about 4.4k tokens — the whole of a
16–18 KB file. The model saw every byte and still got `max_line` wrong. That closes the
"truncated data" branch of the analysis: the error is arithmetic, not lost input.

**3. The model's behaviour was not thrash.** 34 distinct refs across 43 declares:
20 `read_file`, 17 `search_files`, 6 `patch`. It re-read some files, searched a little, and rewrote
the artefact six times — which is why 43 tool invocations fit into 16 API calls. Compare cell A:
686 searches. The task shape changed the behaviour, as designed.

**4. The arm is still not attested.** The sidecar says:

```
plugin 0.10.6   profile "default"   engine null   engineSelections 0
```

for a run invoked as `-p w8-naive`. Two readings, and they have different consequences:

- the run genuinely used the `default` profile — which is `context.engine: compressor`, so the cell
  is naive by luck rather than by configuration; or
- `_profile_runtime_scope` sets its contextvar only on the multiplexed path, so the witness still
  reads the host home even when `-p` was honoured.

Either way the field cannot yet be trusted, and **the paged arm cannot be attributed at all**. This
is the same defect class as 0.10.4, one layer down: the profile is now read from the right resolver
but the resolver is only correct under multiplexing.

**5. `provider` is still `unknown`** in `session.open` while `usage.json` says `nous` — the hook
payload for that path carries no provider, so settings are the only source and the settings that
reach the plugin are the gateway's.

**Next step, and it is one call.** A single trivial `-p w8-paged` request, then read its sidecar:
if `profile` reads `w8-paged` and `engine` reads `ctxvm` with `engineSelections > 0`, the two-arm
design is attributable and W8 can reopen on T-A minus the line measurements. If it still reads
`default`/null, `-p` does not reach the serving process and no paged cell can be trusted — which is
a blocker to fix before any grid, not after.

## Probe: -p w8-paged, 2026-11-09

- Command (verbatim): `hermes -p w8-paged -z "Reply with the single word OK and nothing else." -m openai/gpt-6-luna --provider nous --usage-file /tmp/w8probe/usage.json`
- Usage: `calls 1 cost 0.0016823 provider nous` (total incl. auxiliary 0.0017159, 2 calls incl. title-gen; `turn_exit_reason: text_response(finish_reason=stop)`)
- Sidecar: `/home/theb/.local/state/ctxvm/traces/local-bafef230b74f06b937a44343af5a09b056c6e5f20cde97af62fc116143d151a0.coverage.json`
- Sidecar `plugin` block (verbatim): `{'version': '0.10.6', 'harness': 'hermes-python-plugin', 'harnessVersion': None, 'engine': 'ctxvm', 'engineSelections': 1, 'profile': 'default'}`
- Sidecar captures: turns 1, pages 0, declares 0, faults 0 (perApiRequest samples: 1). Trace: `local-bafef230b74f06b937a44343af5a09b056c6e5f20cde97af62fc116143d151a0.jsonl`
- `session.open`: `model openai/gpt-6-luna`, `provider unknown`, `environmentId env-2b4652ae9d98`
- **Row C — FAIL(profile).** `-p` does not reach the process that ran the turn (profile reads `default`), though the engine is there (`engine ctxvm`, `engineSelections 1`); no paged cell can be trusted until profile attribution is fixed.
- Gateway PID 4110 (started Mon Nov 9 09:16:19 2026); plugin file on disk 0.10.7 (mtime 12:25:36) — in-memory plugin (0.10.6 per sidecar) is older than the file.
- Surprise: `provider unknown` in session.open while usage.json says `nous` (Row D separate finding); the OK turn made zero tool calls, so the sidecar proves engine activity via `engineSelections` only, not via page residency.

### Correction of the verdict: Row C is arm PASS, label fail

The probe wrote `engine: ctxvm, engineSelections: 1, profile: default` and was reported as Row C
FAIL(profile). The engine field decides it, and it says the opposite of the row:

- `select_context()` increments on entry, before any budget logic, so `engineSelections: 1` means the
  host **called the engine** for that session.
- The host activates the engine from the session's profile (`context.engine: ctxvm`); the default
  profile is `compressor` and would never call it. The engine's construct-then-register is
  unconditional, but *selection* is not.
- Therefore the session was served under `w8-paged`. `-p` reached the process.

What failed is the **label**: `plugin.profile` reads `get_active_profile_name()`, which derives from
`get_hermes_home()`, and the per-turn contextvar is only set on the multiplexed path — so the field
records the host home while the configuration that mattered did arrive.

My decision table was too coarse: Row C conflated "the profile name is unknown" with "the profile was
not applied". They are different failures, and only the second blocks the experiment.

**Consequence for attribution, which is now better than before:** `engineSelections` is a complete
arm witness on its own.

```
paged   engineSelections >= 1   always, because the counter runs on entry
naive   engineSelections == 0   because the compressor profile never calls the engine
```

The ambiguity I worried about — "paged with an inert engine looks like naive" — does not exist: an
inert engine is still *called*, and the call is what is counted.

**What is still unproven** is only the isolation between profiles: this gateway had never served a
paged session before this probe, so a process-wide counter would also have read 1. A single
`-p w8-naive` call after this one settles it — expect `engine: null, engineSelections: 0`. If it
reads 1, the counter is shared and 0.10.7's instance counter is required (it is written, not live:
the gateway runs 0.10.6 from 09:16).

**No restart is needed to proceed.** The engine field works on 0.10.6 as measured; `plugin.profile` is
known-unreliable and should be documented rather than fixed tonight, with the config value recorded
in its place once the gateway next restarts for its own reasons.

## Probe follow-up: -p w8-naive after -p w8-paged, 2026-11-09 (counter isolation)

- Command (verbatim): `hermes -p w8-naive -z "Reply with the single word OK and nothing else." -m openai/gpt-6-luna --provider nous --usage-file /tmp/w8probe2/usage.json`
- Usage: `calls 1 cost 0.00168305 provider nous`, session `local-1b02609cbd626d71c5e34e3199e8c9f3be105bc4f65443d77e0077613fcd68c3`
- Sidecar: `/home/theb/.local/state/ctxvm/traces/local-1b02609cbd626d71c5e34e3199e8c9f3be105bc4f65443d77e0077613fcd68c3.coverage.json`
- Sidecar `plugin` block (verbatim): `{'version': '0.10.6', 'harness': 'hermes-python-plugin', 'harnessVersion': None, 'engine': 'ctxvm', 'engineSelections': 1, 'profile': 'default'}`
- Captures: turns 1, pages 0, declares 0, faults 0 (perApiRequest 1). `session.open`: `model openai/gpt-6-luna`, `provider unknown`.
- Expected (per 1b0fbed): `engine null, engineSelections 0`.
- **Result: falsified.** Naive also reads `engine ctxvm, engineSelections 1`. The 0.10.6 counter is **shared process-wide** (or per-process, not per-session): the first paged session incremented it and the naive session read the inherited count. As measured on this gateway (0.10.6, PID 4110 since 09:16, plugin file 0.10.7 on disk), `engineSelections` is **not** a complete arm witness — paged and naive are indistinguishable on this field.
- Therefore 0.10.7's per-session/instance counter is necessary before `engineSelections` can witness an arm; it is written but not live. No restart performed.

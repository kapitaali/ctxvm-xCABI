# RR — UC3-WINDOWSHEET — canonical P-pathology window families, committed as fixtures

**Card:** UC3-WINDOWSHEET · **Type:** analysis (UC3) · **Ask:** RR-UC3-POLICYSIM §Next 1 ·
**Artifacts:** `benchmarks/metrics/fixtures/window-families.json` (fixture) +
`tools/window-sheet.py` (idempotent generator, deterministic — byte-identical reruns) +
`benchmarks/metrics/test_window_sheet.py` (gate 2b enforcement) ·
**Witness:** ALL GATES GREEN at commit (this card).

## 1. What was asked, and the law this operationalizes

The policy-sim card's next step, verbatim:

> Windowed P-pathology reference sheet — `profile --turns` / `metrics --windows`
> canonical window families per trace, committed as fixtures (thrash claims become
> reproducible).

This makes a standing baseline finding *enforceable* instead of anecdotal —
RR-UC3-BASELINE finding 3:

> P-pathology windows change thrash_index by 3× and must be part of any thrash claim.

`07-benchmarks-go-no-go.md` defines `thrash_index` as fault rate "over sustained-pressure
windows", and `metrics.py` implements the honest default: **whole trace** when no windows
are given. Both facts are true but insufficient together — a thrash number without its
window spec (or the word "whole") is uninterpretable, and until now nothing pinned *which*
windows back a given claim.

## 2. The canonical family (decision on record)

Every corpus trace is recorded against **one** deterministic family:

- **whole** — the fair cross-trace reference (07's default);
- **all non-overlapping 2-turn windows** (`"0-1"`, `"2-3"`, …) — the shape the baseline
  card actually used (`0-1`, `2-3,6-9`), covering the trace exactly once; a trailing odd
  turn becomes its own one-turn window (`"2"`, `"4"`);
- plus two cross-view scalars: `maxWindowThrashRatio` = max window thrash / whole thrash,
  and per-trace `whole.faultsPerTurn` + `unanchoredFaults` (the service metrics that must
  accompany any NTR quote — the fixture is self-sufficient for that citation).

Window grid = max turn index + 1 (`turn_space`); thrash selection itself still runs only
over `turn.render` turns (metrics.py `fault_series`). Metrics come from the **committed
reference implementation through the exact CLI `--policy`-less code path** in-process
(`summarize` + counterfactual `netTokenReduction`, as `main()` attaches them) — no
subprocesses, no float-format drift; CI gate 2b re-derives the entire sheet in ~40 ms and
compares against the committed JSON.

## 3. Anchors — the pinned laws (now machine-readable)

| anchor | value | provenance |
|---|---|---|
| `m2/live-thrash` whole | 1.666… (= 10/6) | RR-UC3-BASELINE §findings 3 |
| `m2/live-thrash` @ `0-1` | **5.0** | the 3× window lesson |
| `m5/opencode-live-session-01` whole | 1.214… (= 17/14) | m5-era capture (RR-M5-OPENSELF) |
| `m4/hermes-live-session-01` whole | 0.5 | hermes live capture |

The fixture carries an `anchors` object (same values), and gate 2b asserts both directions:
a fresh in-process rebuild matches the committed artifact byte-for-byte **and** the
committed values equal the pinned laws. A windowed-claim fixture can no longer silently
diverge.

## 4. The sheet (11 corpus traces)

| trace | turns | whole thrash | max window (spec = value) | max/whole |
|---|---|---|---|---|
| m1/session-healthy | 3 | 0.333 | `"2"` = 1.0 | **3.00** |
| m1/session-thrashing | 10 | 0.300 | `"2-3"`/`"6-7"`/`"8-9"` tie = 0.5 | 1.67 |
| m1/tracer-healthy | 4 | 0.250 | `"2-3"` = 0.5 | 2.00 |
| m1/tracer-recall | 4 | 0.500 | `"0-1"` = 1.0 | 2.00 |
| m1/opencode-echo | 5 | 0.400 | `"0-1"` = 1.0 | 2.50 |
| m2/live-echo | 6 | 0.500 | `"0-1"` = 1.0 | 2.00 |
| m2/live-thrash | 6 | 1.667 | `"0-1"` = 5.0 | **3.00** |
| m3/hermes-echo-synthetic | 5 | 0.600 | `"0-1"` = 1.5 | 2.50 |
| m3/hermes-thrash-synthetic | 5 | 1.000 | `"0-1"` = 2.5 | 2.50 |
| m4/hermes-live-session-01 | 2 | 0.500 | `"0-1"` = 0.5 (degenerate) | 1.00 |
| m5/opencode-live-session-01 | 14 | 1.214 | `"4-5"` = 2.5 | **2.06** |

## 5. Findings

1. **The 3× lesson is the norm, not the exception.** 9 of 11 traces show max/whole ≥ 2.0;
   the sheet-wide median is 2.06 and two traces hit exactly 3.0. Crucially, *healthy*
   traces are not exempt: m1/session-healthy reads 0.333 whole but 1.0 inside `"2"` —
   window choice alone triples a reading on a trace with zero pathology claims. A windowed
   thrash number without its spec is uninterpretable **on any trace**.
2. **m2/live-thrash pressure is precisely localized.** `faultsPerTurn` = `{0: 5, 1: 5}`,
   windows `"2-3"`/`"4-5"` read 0.0. The lesson window `0-1` is not an artifact — it is
   where all of the session's thrash lives; whole-trace reporting dilutes it 3×.
3. **m5 shows distributed pressure with one hot phase** (`"4-5"` = 2.5, twice the
   whole-trace 1.214) rather than a single early burst — a different P-shape from m2's
   concentrated burst, now quantifiable and comparable across harnesses (m5 is opencode;
   m4's hermes capture is degenerate at 2 turns, so the m2/m3 synthetic hermes traces
   carry the harness ladder for now).
4. **NTR is degenerate on eviction-free captures — by construction.** live m2/m5 traces
   never evicted, so recorded == counterfactual and `netTokenReduction` ≡ 0.0 in *every*
   window cell; `faultRecall` is `null` (undefined without evictions — never fudged).
   The fixture's eviction-bearing exemplars (m1/session-thrashing: whole NTR 0.545,
   faultRecall 0.5) show the metrics reaching defined values only under paging pressure.
   Concretely: **do not template-fill an NTR claim from a window cell of a live capture;
   cite the fixture's service metrics alongside.**
5. **m1/session-thrashing keeps a modest whole index (0.300)** despite its name — its T3
   gold-standard claims were always absolute counts (evictions, recall), not windowed
   fault rates. Stated here so nobody over-reads window columns on that fixture either.

## 6. Operational discipline this card installs

- Any `thrash_index` quoted in docs/RRs/READMEs must carry its window spec — `"whole"` if
  whole — or the number is not quotable. The fixture provides the canonical values to cite.
- Windowed NTR footnotes must cite service metrics from the same fixture row
  (`faultsPerTurn`, `faultRecall`, `netTokens`).
- run-ci gate 2b now includes `test_window_sheet.py`: rebuild identity, anchor laws, and a
  structural partition test (windows partition each trace's turn space exactly once).

## Next proposed

1. **UC3-BUDGETSWEEP continuation (§Next 2)** — `--budget` sweeps per trace; when charting
   eviction/fault-vs-capacity curves, reuse these window specs so sweep prose and the sheet
   speak the same window language.
2. **First eviction-bearing live capture** (small-budget opencode or hermes m6): re-run the
   sheet — `faultRecall` becomes defined on live traces and the anchors table gains
   eviction-bearing rows.
3. **RFC-1 candidate (unchanged, standby):** `page.touch` as a first-class fact — the
   touched-token surface is currently fault-derived only (metrics.py header, gap-not-
   invention note); a touch fact would upgrade `touch_ratio`/`waste` interpretation, with
   this fixture as its before/after baseline.

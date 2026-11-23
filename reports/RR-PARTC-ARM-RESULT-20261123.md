# RR-PARTC-ARM-RESULT-20261123 — Part C stub arm: accuracy recovers to 7/8 middle, but no capture attests the stub or re-read

Owner authorized the temp profile (`RR-PARTC-ARMAUTH`) and the Part C stub arm (condition 1). Ran 8 sessions under
`w8cs-paged` (stub `recoverable`, assert-engaged), same frozen bank/scorer/prompts as Part B. $0 free tier, no push.
Review lane, verify-then-record.

## 1. Accuracy result (verified from final replies)

| band | Part B naive | Part B paged (no stub) | **Part C stub arm** |
|---|---|---|---|
| head (part-01) | 8/8 | 8/8 | **8/8** |
| **middle (part-09)** | 8/8 | **1/8** | **7/8** |
| tail (part-20) | 8/8 | 7/8 | **7/8** |

Re-scored clean from all 8 stub-arm `final-reply.txt`: part-09 correct in sessions 01–06 and 08, missed only in 07.
So native paging's middle collapse (1/8) is **largely recovered by the opt-in stub (7/8)** while head stays perfect —
a strong, band-specific recovery signal on the exact-match readout. Tail 7/8 matches Part B paged (noise-level).

## 2. What could NOT be verified — recorded honestly

- **No capture flushed for the stub sessions.** Each session has a fresh ID (`local-4c0c13…` etc.) but **no `.jsonl`,
  no coverage sidecar, and no session-name match** in `~/.local/state/ctxvm/traces/`. Only a single `.live.json`
  (ephemeral) appeared for one session. The `hermes chat --oneshot` flush did not persist these captures, the same
  live-vs-flush gap seen earlier.
- **Stub attestation: UNVERIFIED.** With no sidecar, `enginePlan.stubDropped` / `plugin.stubDropped` cannot be read
  from a capture. The preflight under the gateway interpreter confirmed the profile resolves `recoverable` from
  settings (`RR-PARTC-ARMAUTH`), and the run used that profile with `--assert-engaged`, but no live artifact attests
  the stub was on per session.
- **Re-read readout: UNVERIFIED.** No trace means no `read_file` tool call can be counted. Part C condition 3
  explicitly required the re-read readout from trace tool calls to close Part B's UNVERIFIED half — that closure did
  not happen here. Accuracy recovery is measured; the mechanism (did the model actually re-run the stubbed call?) is
  not observed.

So the stub arm **achieves its accuracy purpose** but **does not satisfy attestation conditions 1 and 3** from the Part C
authorization. This is a result with an evidence gap, not a clean PASS of all conditions.

## 3. What is / is not claimed

- **Established within this shape:** the opt-in stub is associated with middle-band accuracy recovery 1/8 → 7/8 on a
  planted-code task at 24k, head/tail controls intact. This is a fix-for-a-defect result, not a paging-quality claim.
- **Not established:** that the stub was actually on per session (no capture), that the model re-read (no trace), any
  cost saving (law 7; free tier `cost 0` is not a receipt), general paging behavior, model quality, determinism (law 8).
  Nothing pooled with E0/E1/E2/M1/M2/M3. Part B's negative stands untouched (no re-score).

## 4. Cleanup owed / done

Delete the temp profile `~/.hermes/profiles/w8cs-paged` by **exact path** (law 10) and verify the 10-profile baseline
from `/tmp/opencode/profiles-baseline.txt` is restored. This is done in the accompanying action; recorded here.

## 5. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261123.md`.

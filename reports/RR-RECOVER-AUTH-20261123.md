# RR-RECOVER-AUTH-20261123 — owner rules "recover forward": one stub session with raised retention and trace-based re-read readout

Owner decision 2026-11-23, verbatim: **"let's recover forward"** — the first of the two options in
`RR-ONESHOT-DIAG-REVIEW` (falsified flush premise; gap is capture identity + retention). Review lane,
verify-then-record. Experiment-lane work, $0 free tier, no plugin change, no push.

## 1. Scope authorized

- Raise `CTXVM_TRACE_RETAIN_MAX` for **one** controlled stub session (env on the run, not a global config change), so
  its capture is not pruned by the 200-file cap.
- Map the host session ID from the `.live.json` stamp (`sessionID`) to the flushed `.jsonl` + coverage sidecar — the
  host names captures by gateway IDs, not the driver's `-c` name.
- Re-read the stub-arm's two UNVERIFIED readouts from that capture: **stub attestation** (`plugin.stubDropped:
  recoverable`) and **re-read** (`read_file` tool call on part-09 after the final question).
- Same frozen bank-36, scorer, prompts; one session; no re-score/pooling of Part B or Part C's 8-session arm.

## 2. Profile situation (found, not assumed)

At ruling time `~/.hermes/profiles/w8cs-paged` exists as an **empty directory** (created 21:17, after I deleted the
real temp profile post-stub-arm and verified the 10-profile baseline). It has no config/auth — not a usable profile.
A proper `w8cs-paged` must be rebuilt (config from `w8cn-paged` + `stubDropped: recoverable`, auth symlinked, no
duplication) for the one session, then removed again — exact-path cleanup, baseline re-verified.

## 3. Not authorized / held

No plugin change, flush hook, version bump, or restart (the diagnostic falsified the flush-bug premise). No D17
release action, registry/catalog, default-on stub, or push. A recovered attestation updates **this** arm's evidence;
it does not re-open Part B's result or make a paging-quality/cost claim.

## 4. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261123.md`.

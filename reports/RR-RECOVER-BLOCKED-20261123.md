# RR-RECOVER-BLOCKED-20261123 — recover-forward blocked: temp profile cannot create a fresh named session; stopped, cleaned up

Owner ruled "recover forward" (`RR-RECOVER-AUTH`). I built the runner and attempted one controlled stub session, but hit a harness blocker I could not resolve without touching owner config. Stopped and cleaned up. $0 free tier, no plugin change, no push.

## 1. What I built (frozen)

- `experiments/needle-revisit/partB/recover-session.py` (sha `9f5c0e46…`): one stub session, `CTXVM_TRACE_RETAIN_MAX=5000` env on the run, records new `.live.json` stamps for host-ID → capture mapping.
- Rebuilt the temp `w8cs-paged` profile (config from `w8cn-paged` + `stubDropped: recoverable`; auth `state.db` symlinked, no duplication). Preflight under the gateway interpreter confirmed `engine ctxvm / budget 24000 / stub recoverable-from-settings`.

## 2. The blocker

- First run attempt: rc=1 in 5 s — "No session found matching 'recover-stub-…' and a new titled session could not be created." I had omitted `--create-if-missing`, but then discovered that flag is **not** a driver arg — the driver adds it to the *hermes chat* call on prompt 1. Reverted that wrong edit.
- Controlled creation probes showed the difference is the **profile**, not flags: `hermes -p w8cn-paged chat -c <fresh> --create-if-missing` creates a session (rc=120, "Starting fresh"); the identical command with `-p w8cs-paged` returns rc=1 "new titled session could not be created". Adding `state.db`/`-wal`/`-shm` symlinks did not fix it.
- The earlier 8-session stub arm **did** create sessions under `-p w8cs-paged` (cmd-01 confirms the flag, 21 prompts each, rc=0) — so some harness state that made it work then is not reproduced by the symlinked reconstruction now. I did not find what (auth.lock / profile registration are candidates). I stopped rather than keep probing harness internals or editing `~/.hermes/config.yaml` (owner territory).

## 3. Outcome — honest

- **No recovered attestation.** No new stub capture was produced; no `stubDropped: recoverable` sidecar exists on disk; no re-read tool call was observed for a recovery session. The two UNVERIFIED readouts from `RR-PARTC-ARM-RESULT` remain UNVERIFIED.
- Part C's accuracy contrast (1/8 → 7/8 middle, head 8/8) stands untouched — recover-forward did not change it, and no re-score was done.
- `recover-session.py` and its hash are preserved as the attempted harness; no claim rests on it.

## 4. Cleanup (verified)

Deleted `~/.hermes/profiles/w8cs-paged` by **exact path** (law 10) and verified the 10-profile baseline is byte-identical to `/tmp/opencode/profiles-baseline.txt`. No w8cs profile remains. No gateway action, no plugin change, no D17 action, no push.

## 5. Next (owner's call, not taken)

Either (a) accept the gap permanently (`RR-PARTC-ARM-RESULT` as recorded), or (b) have the owner/hermes lane resolve why `w8cs-paged` can't create sessions now (owner config / profile registration), then retry recover-forward. I did not do either.

## 6. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261123.md`.

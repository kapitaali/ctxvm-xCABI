# RR-RETRY-BLOCKED-20261123 — bounded retry: full-copy profile still cannot create a titled session

Lane: hermes. Authority: owner "authorize one bounded entry" — steps 1–2 of the proposed bounded
retry only, with a hard stop if the no-model preflight failed. It did. **No recovery session was run,
no model call beyond the trivial preflight prompt, no plugin/D17/gateway action, no push.**

## 1. What changed from the first attempt

The prior reconstruction (`RR-RECOVER-BLOCKED`) built `w8cs-paged` from config + **auth** `state.db`
symlinks. My hypothesis was that the missing **profile-local** `sessions/` dir and `state.db` caused
"new titled session could not be created." So this retry built `w8cs-paged` as a **full `cp -a` copy of
`w8cn-paged`** (which has `sessions/`, 27 MB `state.db`, WAL/SHM, caches), then patched **only**
`stubDropped: recoverable` into `config.yaml`. No `~/.hermes/config.yaml` edit.

## 2. Preflight results — hypothesis falsified

- Policy under the gateway interpreter: `engine ctxvm, budget 24000, stub recoverable, source settings`
  — the profile setting is correct.
- Session creation: `hermes -p w8cs-paged chat -q "Reply with OK" -c preflight-232359
  --create-if-missing --in <scratch>` → **rc=1**, stderr "No session found matching
  'preflight-232359' and a new titled session could not be created." No stdout.

A full profile copy does **not** fix it. The difference from the working 8-session arm is therefore
not the profile tree — it lies in harness state outside the profile (session registry / `auth.lock` /
gateway registration) or in a host-side rule about which profile names may create titled sessions.
I did not probe further; that is owner config / harness internals, explicitly out of scope.

## 3. Consequence

**Accept the gap.** The two UNVERIFIED readouts from `RR-PARTC-ARM-RESULT` (stub attestation,
re-read) remain UNVERIFIED. Part C's accuracy contrast (1/8 → 7/8 middle, head 8/8) stands untouched;
no re-score, no pooling. Two bounded attempts have now failed on the same host-side session-creation
blocker — further probing has low expected value and risks owner territory.

## 4. Cleanup (verified)

- Scratch preflight workspace removed by exact path (law 10).
- `w8cs-paged` removed by exact path (law 10). Profile list normalized and diffed against
  `/tmp/opencode/profiles-baseline.txt` → **byte-identical, 10 profiles**.

## 5. Not claimed

No cost saving, paging/model-quality claim, or determinism. The free-tier preflight is a launch cost,
not a receipt. No plugin version change (suite/gate not re-run — no code changed).

## 6. Owed

Review lane: verify + record. Owner: the gap is accepted unless they rule otherwise; a future retry
needs the host-side session-creation blocker resolved first, outside this lane.

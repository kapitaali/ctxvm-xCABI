# Corpus drop M7 — first hermes-side typed pause/resume pair

First **capture driven entirely through the gateway service** for the **ctxvm
Trace Corpus**: both sessions are live interactive hermes TUI runs and the typed
mid-session `/ctxvm-handoff` completes the harness-side story that m6 started on
the opencode lane. Session-a is a real user-driven console session whose typed
`/ctxvm-handoff /tmp/ctxvm-m7/a 3` pause operated the design §2 chain
end-to-end **inside `hermes-gateway.service`** (flush → era copies → export
`--turn 3 --odps` → `verified=True`), continued tracing through turn 4 (pause is
not teardown), and flushed the full trace at stop + exit. Session-b is a
genuinely fresh chat (bare `hermes`, no prior context) booted with
`CTXVM_RESUME_FROM` pointing at the package: the boot check verified the
snapshot before any hook work, stamped the canonical `resumeFrom` sidecar
evidence, and the resumed agent then rebuilt its knowledge strictly from the 5
package artifacts — verifying the package itself, finding a real mirror
regression mid-verify, and producing a handoff report.

| File | Origin | Tool calls | Turns | Pages | Faults | Events |
|------|--------|------------|-------|-------|--------|--------|
| `hermes-pause-session-a.jsonl` | session-a full trace (turns 0–4; typed pause packaged turns 0–3 mid-session at the 5723-byte flush, stop flush = 6161) | 12 (11 ok, 1 refused) | 5 | 11 | 0 | 32 |
| `hermes-resume-session-b.jsonl` | session-b trace, resumed from the package | 35 (34 ok, 1 failed probe) | 1 | 34 | 0 | 37 |
| `handoff/turn-3/` | the pause package exactly as produced: `trace-3.jsonl.zst`, `page-table-3.json`, `manifest.yaml`, `llms.txt`, `checksums.sha256` (29 events of turn-3 state: 10 slots, residency 20276) | — | — | 10 | — | 29 |

Per-file provenance (harness version, invocation, flush/pause semantics, honest
misses) is in `provenance.json` and the `.meta.json` sidecars. Session-a's
sidecar carries `resumeFrom: null` (not resuming); session-b's carries the full
evidence object (snapshot path verbatim, `snapshotDigest: sha256:7f746595…`,
`snapTurn: 3`, artifact list, projection, diagnostic diff). Integrity:
`checksums.sha256` (covers both traces + both sidecars + all five package
artifacts + `provenance.json` + this README).

## What this capture shows

1. **Typed dispatch is a service-runtime law.** The whole session (agent turns,
   hook firing, plugin registry, `commands.catalog`, `slash.exec` dispatch) runs
   inside `hermes-gateway.service`; the long-running service never re-imports,
   so TUI shell env exports are inert for it (the canonical discovery witness
   logged `12:18:22 … 60 enabled` only after the restore restart). The capture
   recipe is therefore `systemctl --user set-environment CTXVM_*…` + `systemctl
   --user restart hermes-gateway.service` — see Reproduction.
2. **The typed pause chain on real work.** Witnessed 2026-10-26:
   `/ctxvm-handoff /tmp/ctxvm-m7/a 3` → second 5723-byte flush at 10:48:16Z →
   era copies `session-a-turn-3.{jsonl,meta.json}` →
   `ctxvm-handoff: exit_code=0 verified=True divergences=[]` with
   `relationToSource: "identical"` (29/29 kept events, 10-slot projection) →
   one continuation context (turn 4) → stop flush 6161 bytes. The pause also
   required `CTXVM_HANDOFF_NAME` equal to the trace flush name — run-1's exit 2
   (item 5) is the failure witness.
3. **The package is the era's turn-3 state, replay-deterministically, and the
   digest chain holds from boot to drop.** `diff(era-as-flushed, package slice)
   → identical` over all 29 events; the package's checksums-hex construction
   recomputes the exact digest session-b recorded at boot — even after the
   capture-dir mutation incident (below), which the digest alone made
   detectable.
4. **The knowledge-stateful render-tail law, second measured instance.** The
   full session-a tail (11 pages, incl. the post-pause re-declare) stamps turns
   0–4 with 20904; the turn-3 package stamps turns 0–3 with 20276;
   `diff(full, package)` shares the 21-event lifecycle prefix and departs at
   event 21 (`divergent`, tallyMismatches turns 0–3: 20904 vs 20276) —
   diagnostic only, never verdict-forming.
5. **Negative twins on the same day.** Run-1 (12:21Z) paused the flushed
   `session-a` name against `CTXVM_HANDOFF_NAME` unset (`handoff`) → exit 2 —
   the flush-name-mismatch failure mode; the 11:38Z resume boot fail-closed with
   `verified=False snapshot dir not found` because no package existed yet.
   Session-a's 12:44 pausing run and session-b's 12:53 boot are their lawful
   passing twins; run-1 is archived at `/tmp/ctxvm-m7/a-run1`.
6. **The product on its own capture.** Session-b had no transcript of session-a —
   only the 5 artifacts (llms.txt-led). It reconstructed the repo state,
   verified the package per the verify block (`checksums -c` 4/4, decompress
   byte-identity, replay exit 0, projection match), found a real regression
   (the TS dir-chain env-first leak its mid-verify CI probe hit — fixed as a
   separate mirror commit), and wrote a handoff report to the next agent. The
   package carried the knowledge, not a chat history.
7. **Resume is observation, not injection (v0 §3).** Session-b continues from
   its own fresh state — 37 events, its own 34 pages — the resume evidence is
   the boot-check verification + provenance stamp, per the gated
   handoff-inject beat (v-next).

## Validation (witnessed 2026-10-26)

```
$ venvs/odps/bin/python spec/rfc-0/validate_schema.py hermes-pause-session-a.jsonl
SCHEMA CONFORMANCE: PASS (87 checks)
$ venvs/odps/bin/python spec/rfc-0/validate_schema.py hermes-resume-session-b.jsonl
SCHEMA CONFORMANCE: PASS (92 checks)
$ rust/target/release/replay hermes-pause-session-a.jsonl   # exit 0: 32 events, 0 divergences, 0 violations
$ rust/target/release/replay hermes-resume-session-b.jsonl  # exit 0: 37 events, 0 divergences, 0 violations
$ zstd -d handoff/turn-3/trace-3.jsonl.zst -o trace-3.jsonl && \
  rust/target/release/replay trace-3.jsonl --turn 3         # exit 0, divergences [], violations []
$ rust/target/release/diff <era-as-flushed: /tmp/ctxvm-m7/a/session-a-turn-3.jsonl> trace-3.jsonl
   → relation "identical" (29/29)                           # witnessed at capture, before the era file aged
$ rust/target/release/diff hermes-pause-session-a.jsonl trace-3.jsonl
   → relation "divergent", commonPrefixEvents 21, firstDivergentEvent 21,
     tallyMismatches turns 0–3 (20904 vs 20276)             # the knowledge-stateful tail — see item 4
$ sha256sum -c checksums.sha256                             # 4/4 package artifacts OK
$ (drop root) sha256sum -c checksums.sha256                 # 11/11 files OK
$ snapshotDigest(handoff/turn-3) == sha256:7f746595343528907e1c47edb8aa2cc62e72adc42017dd30ddecab39edef17c2
   # == resumeFrom.snapshotDigest recorded in session-b's sidecar at boot (12:53:12Z)
```

Both traces replay clean because **no faults were recorded** — the two errored
hooks (session-a's Write refusal, session-b's failed `ls` probe) declined before
declaring a page, so they stay lawful non-paged error data; the cold-entry
double-row shape of m5/m6 is absent by construction here.

## Reproduction

```
# Capture runs through the systemd gateway — TUI shell exports are INERT for the
# service runtime; the service never re-imports, so env + plugin state are boot-time.
systemctl --user set-environment \
  CTXVM_FEATURES=trace,handoff \
  CTXVM_TRACE_DIR=/tmp/ctxvm-m7/a CTXVM_TRACE_NAME=session-a \
  CTXVM_HANDOFF_DIR=/tmp/ctxvm-m7/a CTXVM_HANDOFF_NAME=session-a \
  CTXVM_RUST_BIN_DIR=<repo>/rust/target/release \
  CTXVM_AGENT_ID=hermes CTXVM_BUDGET_TOKENS=120000 \
  CTXVM_MODEL=nvidia/nemotron-3.5-super-vl-120b-a12b CTXVM_PROVIDER=nvidia \
  CTXVM_HERMES_VERSION="$(hermes --version | head -1)"
systemctl --user restart hermes-gateway.service
hermes
# → 4 real exchanges (state report → write notes → append status → summarize).
#   Exchanges are 0-based turns: after exchange 4 type
#     /ctxvm-handoff /tmp/ctxvm-m7/a 3
#   CTXVM_HANDOFF_NAME must equal the trace flush name (session-a), else the
#   pause flushes `<default-name>` and packages a nonexistent file (run-1 exit 2).
# → optionally one more exchange, then /ctxvm-trace stop and exit (stop flush).
# … session-b as a genuinely FRESH chat (bare `hermes`, no resume flag):
systemctl --user set-environment \
  CTXVM_TRACE_DIR=/tmp/ctxvm-m7/b CTXVM_TRACE_NAME=session-b \
  CTXVM_RESUME_FROM=/tmp/ctxvm-m7/a/handoff
systemctl --user restart hermes-gateway.service
hermes
# the boot-verify line lands in hooks-witness.log BEFORE the first prompt:
#   resume_from=/tmp/ctxvm-m7/a/handoff verified=True reason="snapshot verified: replay exit 0 at turn 3"
# … hygiene afterwards (leaked CTXVM_* env broke a spawned node --test once):
systemctl --user unset-environment CTXVM_FEATURES CTXVM_TRACE_DIR CTXVM_TRACE_NAME \
  CTXVM_HANDOFF_DIR CTXVM_HANDOFF_NAME CTXVM_RUST_BIN_DIR CTXVM_AGENT_ID \
  CTXVM_BUDGET_TOKENS CTXVM_MODEL CTXVM_PROVIDER CTXVM_HERMES_VERSION CTXVM_RESUME_FROM
systemctl --user restart hermes-gateway.service
```

Snapshot era files immediately after the pause and the exit flush (later runs of
the same `CTXVM_TRACE_NAME` overwrite; the drop copies were taken at capture
time — the sidecar paths and witness lines record the capture-time absolute
paths per the m1–m3 redaction precedent).

## Honest deviations (2026-10-26)

- **Run-1 pause failed (exit 2).** At 12:21Z a 3-exchange run paused with
  `CTXVM_HANDOFF_NAME` unset: the handler flushed under `handoff.jsonl` while
  the session flushed `session-a.jsonl`, so `export` could not read the trace.
  Archived `/tmp/ctxvm-m7/a-run1`; second run at 12:44 with the name
  discipline honored — all green. (Root wart — the hermes handler does not
  pass `handoff_name=CTXVM_TRACE_NAME` like the TS adapter — is a frontier
  item for a hermes card.)
- **The resumed session mutated the live package dir.** Session-b's own verify
  path ran `export --turn N` inside the live snapshot dir, which overwrote the
  shared per-dir files (`manifest.yaml`, `llms.txt`, `checksums.sha256` name
  the last slice written) with later-turn variants. `trace-3.jsonl.zst` /
  `page-table-3.json` survived; the shipped `handoff/turn-3/` is the restored
  package (re-exported from the era-as-flushed input under the original argv,
  byte-cmp'd against the survivors, checksums 4/4, and pinned by the recomputed
  boot-time digest `sha256:7f746595…`). Per-turn export into one dir clobbering
  shared names is a real engine wart this drop exposed (frontier).
- **Post-stop hooks logged, untraced.** Session-b's TUI stayed open a few
  minutes past `/ctxvm-trace stop`; hooks through 11:06Z appear in
  hooks-witness but never entered the trace (bytes at both flushes: 8523).

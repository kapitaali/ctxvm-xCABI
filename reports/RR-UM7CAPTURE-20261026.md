# RR — UM7CAPTURE — corpus/m7, first hermes-side typed pause/resume pair (+ TS pause dir-chain fix)

**Card:** UC1-PLUGIN B4 follow-up — the m7 hermes-side capture (canonical-flow
mid-session typed `/ctxvm-handoff` pause + boot-verified resume into a fresh
chat), assembled off the m6 template, plus one pre-cleared opencode-mirror fix
the capture surfaced (pause dir chain, gate-2 isolation).

**Attribution:** both sessions were user-driven in their own terminal
(operator ruling: m7 pre-gated + user-driven; assistant validates, artifacts,
assembles, commits). Repo work = kapitaali lane. The TS fix is pre-cleared by
the TS-mirror lane rule (PY-side hermes module untouched — frontier noted).

## What was done

1. **Capture env hygiene (before and after).** Per the BUG_REPORT doctrine the
   capture env is service-scoped (`systemctl --user set-environment CTXVM_*…`
   + `systemctl --user restart hermes-gateway.service`), never TUI shell
   exports. After all three phases the keys were unset and the service
   restarted; `systemctl --user show-environment` → CTXVM-clean, gateway
   `active` on the baseline import.
2. **Session-a (canonical pause half, 12:44–12:49).** 4 real exchanges (state
   report → scratch-notes write with one pre-pause refusal → status append →
   summarize), then the typed mid-session command:
   ```
   /ctxvm-handoff /tmp/ctxvm-m7/a 3
   → exit_code=0 verified=True divergences=[] relationToSource "identical"
     keptEvents 29/29, projection 10 slots / 20276 tokens, droppedEvents 0
   ```
   Era copies `session-a-turn-3.{jsonl,meta.json}` (5723 B) taken by the pause;
   tracing continued through turn 4; stop flush 6161 B (32 events: 1
   `session.open` + 11 `page.declare` + 10 `page.render` + 5 `call.meta` + 5
   `turn.render`; turns 5, pages 11, faults 0, residentTokens 20904 in the
   post-hoc tail). The one errored hook is the Write refusal (declared no page
   — lawful non-paged error data).
3. **Package validation (lawful chain).** `sha256sum -c` inside the package →
   4/4 OK; `replay trace-3.jsonl --turn 3` → exit 0, divergences []; rust
   `diff(era-copy, decompressed slice)` → `"relation": "identical"` (29/29,
   `firstDivergentEvent: null`); `cmp` → byte-identical. Rust `export` writes
   its 5 artifacts FLAT into `--output DIR` (no `turn-N/` nesting): m6's
   `handoff/turn-3/` shape is an assembly-time restructure — mirrored.
4. **Session-b (canonical resume half, 12:53–13:03).** Genuinely fresh chat,
   bare `hermes`, armed with `CTXVM_RESUME_FROM=/tmp/ctxvm-m7/a/handoff`.
   Boot-verify witness in `hooks-witness.log` BEFORE any hook work (§3(3)(4)
   evidence lines included):
   ```
   resume_from=/tmp/ctxvm-m7/a/handoff verified=True reason=snapshot verified: replay exit 0 at turn 3
   projection: 10 slot(s) at turn 3
   diff: source=/tmp/ctxvm-m7/a/session-a.jsonl relation=divergent
   ```
   b meta carries the whole `resumeFrom` extension (`snapTurn: 3`,
   `snapshotDigest: sha256:7f746595343528907e1c47edb8aa2cc62e72adc42017dd30ddecab39edef17c2`,
   artifacts, projection, diff). The agent then rebuilt its state strictly
   from the 5 package artifacts (llms.txt-led): verified the package itself
   (checksums 4/4, decompress byte-identity, replay exit 0, projection
   byte-match), found a real regression mid-verify (below), and produced a handoff
   report. Trace: 37 events (8523 B), one giant resume turn, 34 declared pages,
   residentTokens 48080, session_end + stop flushes both 8523 B (stable);
   hooks logged after the stop (11:02–11:06Z) are inert (untraced).
5. **Negative twins on record (same day).** The 11:07–11:31 pre-fix runs never
   dispatched (broken plugin import booted into the frozen service — fixed via
   restart after root-causing; discovery witness `12:18:22 … 60 enabled`).
   The 11:38 Z resume boot fail-closed cleanly (`verified=False`, no package
   existed yet). Run-1 (12:21) captured fine but its pause exited 2 — the
   hermes handler flushed/packaged under the default name while the session
   flushed `session-a.jsonl` (name-chain miss); archived `/tmp/ctxvm-m7/a-run1`.
   The 12:44 rerun honored `CTXVM_HANDOFF_NAME=session-a` — all green.
6. **The gate-2 regression, root-caused and fixed (opencode TS, pre-cleared).**
   The full story in §The gate-2 regression below: `uc1Pause` resolved the dir
   ENV-FIRST against its own name-chain law; the resumed agent's `node --test`
   (spawned from the gateway env where `CTXVM_HANDOFF_DIR` etc. leak)
   replicated it. Fix: dir chain arg-first in `uc1Pause` + `freshTmp` CTXVM_*
   quarantine + a pinned dir-chain law test. 51/51 green clean AND polluted.
7. **Assembly of `corpus/m7` (m6 template).** Root traces renamed at copy
   (`hermes-pause-session-a.{jsonl,meta.json}`,
   `hermes-resume-session-b.{jsonl,meta.json}`), `handoff/turn-3/` = the five
   boot-verified artifacts, `provenance.json` + `README.md` (repro recipe,
   deviations section), drop-level `checksums.sha256` (11 files). The shipped
   package is the RESTORED boot-verified set — §The mutation and the restoration
   below.
8. **Gates wiring.** `tools/run-ci.sh`: FIXTURES += the two m7 traces, counts
   line `ts 13 + 51 / python 74 + 30 + 8`, per-drop checksum line for
   `corpus/m7`. `04-odps-dataproduct-corpus.yaml`: `latestDrop: corpus/m7`,
   `productVersion: 0.7.0`, drop sentence + RE-VALIDATED header line. Hub
   regenerated via their SDK chain and `hub/hub.sha256` re-baselined
   (`tools/build-hub.sh` → regen → baseline stale expected → re-baseline →
   verified).

## Verification (real outputs)

- Ship-side: `venvs/odps/bin/python spec/rfc-0/validate_schema.py` →
  `hermes-pause-session-a.jsonl` **PASS (87 checks)**,
  `hermes-resume-session-b.jsonl` **PASS (92 checks)**; `replay` both traces →
  exit 0 (32 / 37 events, 0 divergences, 0 violations); shipped slice
  `replay --turn 3` exit 0; `diff(full-a, shipped slice)` →
  ```
  commonPrefixEvents 21, firstDivergentEvent 21, relation "divergent"
  tallyMismatches turns 0–3: 20904 vs 20276       # knowledge-stateful, diagnostic
  ```
- Drop integrity: drop `sha256sum -c` → 11/11 OK; package `sha256sum -c` → …
  4/4 OK; credential-pattern scan over the drop → **0 hits**.
- Digest law, end to end:
  `snapshotDigest(corpus/m7/handoff/turn-3)` →
  `sha256:7f746595343528907e1c47edb8aa2cc62e72adc42017dd30ddecab39edef17c2`
  == the digest session-b's sidecar recorded at boot (12:53:12Z). The shipped
  checksums re-derive the exact boot-verified package.
- Full local CI mirror: `bash tools/run-ci.sh` → ALL GATES GREEN
  (schema **629 checks over 25 fixtures**; rust suite + release binaries;
  ts 13 + 51; python 74 + 30 + 8; export round-trip; hub byte-identity).

## The gate-2 regression (opencode lane fix, this card)

Their-mirror facts: the PY reference name chain is arg-first
(`handoff_name or env or "handoff"`) but its DIR line is env-first
(`os.environ.get("CTXVM_HANDOFF_DIR") or trace_dir`, mirrored verbatim in TS).
Symptom witnessed live: a service-env spawning (the resumed agent ran
`node --test` INSIDE the gateway process tree) leaks
`CTXVM_HANDOFF_DIR=/tmp/ctxvm-m7/a`, so the test that passes
`{ traceDir: dir, handoffName: "spot" }` failed with
`ctxvm export: cannot read /tmp/ctxvm-m7/a/spot.jsonl` — the leaked dir
hijacked the explicit dir. Green in clean shells, red in leaked environments —
a real precedence bug, not test flake.

Fixed one card, TS only:
- `uc1Pause` now `handoffDir = traceDir || process.env.CTXVM_HANDOFF_DIR`
  (arg-first, consistent with the name chain); doc updated with the mirror
  divergence + reason.
- `freshTmp()` quarantines every `CTXVM_*` key before creating the temp dir
  (test set-up stays hermetic; deliberate env tests set keys after `freshTmp`).
- New law test "pause dir chain: arg > env" pins the precedence and would be
  RED under the env-first law even in a clean shell.
- `node --test test/` → **51 pass** clean; **51 pass under a polluted env**
  (`CTXVM_HANDOFF_DIR=/tmp/ctxvm-m7/a CTXVM_HANDOFF_NAME=session-a
  CTXVM_TRACE_NAME=session-b node --test test/`) — the exact leak shape that
  went red at gate 2 this morning.
- PY side unchanged (their module law, env-first line) — mirror-parity
  follow-up for a hermes card (frontier).

## The mutation and the restoration (the m7 story that tested the law)

After the verified boot, the resumed agent's own analysis path ran
`export` INSIDE the live snapshot dir (`--turn 2` / `--turn 4` against the
post-stop full trace). The engine names its shared per-dir files WITHOUT the
turn (`manifest.yaml`, `llms.txt`, `checksums.sha256` describe the LAST slice
written; only `trace-N.jsonl.zst` / `page-table-N.json` carry the turn), so the
dir was left with the canonical `trace-3`/`page-table-3` files intact but
generic files describing a turn-2 slice (`sliceTurn: 2, keptEvents 30`).

Forensics + restoration chain:

1. `sha256sum -c` on the live checksums verified the NEW 4 rows — the mutation
   was detectable instantly from the sidecar digest alone: recomputing
   `snapshotDigest` over the mutated checksums could not equal
   `sha256:7f746595…` (the rows changed). The digest-provenance law worked as
   designed.
2. Byte-true restoration by re-derivation: the original package was exported
   from the trace AS FLUSHED MID-SESSION (29 events), while the current file
   holds the 32-event stop-flush — re-exporting against the full trace
   produces the lawful-but-different slice (`keptEvents 31`,
   `relationToSource b_extends_a`) — so the honest input is the era copy
   `session-a-turn-3.jsonl` (the pause's own cp of the flushed file), the
   pause's cp -n copy, byte-identical to the packaged slice.
3. Swap-regen-restore transaction (single shell step, restore guaranteed):
   the live `session-a.jsonl` was briefly swapped to the era bytes and
   restored (sha256 identical `a09aab8f…` before/after), so the re-export runs
   under the ORIGINAL argv string (`/tmp/ctxvm-m7/a/session-a.jsonl`) with the
   original capture env → manifest/llms/checksums regenerate byte-true.
4. Identity witnessed three ways: the two surviving artifacts (`trace-3.jsonl.zst`,
   `page-table-3.json`) `cmp` byte-identical to the restoration; the restored
   `checksums.sha256` self-verifies 4/4; `snapshotDigest` over the restored
   checksums recomputes EXACTLY the boot-time sidecar digest
   `sha256:7f746595…`, which pins the whole artifact set row-hash-wise.
5. The shipped `corpus/m7/handoff/turn-3/` = the restored five artifacts. Live
   debris (`trace-2/4.jsonl.zst`, `page-table-2/4`, decompressed
   `trace-3.jsonl`) stays outside the drop and is documented in
   provenance/README.

## Deviations from card

- Sessions were operator-driven (per ruling D) — no fabrication; the assistant
  validated outputs and assembled. Parts of the b transcript include the
  operator's mid-turn redirect (the resumed agent was asked to stop and hand
  off — which is exactly what a handoff should let a session do).
- The full-trace regen experiment (31-event `b_extends_a` slice) was run
  first, honestly discarded before restoration (recorded above; it also
  explains the era-copy-as-input law).
- Except for the swap-regen-restore dance (whose end state is byte-identical
  to pre-swap, sha-checked) no live capture file was modified; the package
  mutation itself was committed by the RESUMED agent's own session, in-place.

## Discoveries

1. **Export shared-name clobber wart (engine, frontier):** per-turn exports
   into one dir overwrite the three shared generic names; mixed-slice dirs can
   arise and checksums does not cover orphans. Observed on this drop; deserves
   a doc line in the export README (one dir = one slice) or turn-suffixed
   shared names later.
2. **The digest law catches real drift:** the boot-time digest alone was
   enough to detect the live-dir mutation; restoration provenance rides the
   same law (m6 already documented "recomputes from the SHIPPED checksums" —
   m7 is its lived demonstration).
3. **Hermes runtime shape:** `session_end` fires per user turn (5 vs 1
   `session_start`); gateway hook payloads carry `tool=None` (key differs from
   the classic CLI — trace fidelity unharmed, `page.declare` events carry the
   full `logicalRef`); a single-turn session legitimately emits no
   `page.render` rows (they fire at later contexts).
4. **Frontier (hermes lane):** the `/ctxvm-handoff` handler should pass
   `handoff_name=CTXVM_TRACE_NAME` like the TS adapter does (run-1 exit 2 is
   the wire witness); PY dir-chain mirror-parity with the TS arg-first fix; a
   verified-boot "resume brief" line for the resuming agent (UX polish).
5. **Systemic law now proven twice:** service env is boot-frozen (TUI exports
   inert); unset + restart are part of the capture hygiene, and leaked env
   even reaches spawned test subprocesses — hence the freshTmp quarantine.

## Open questions

1. Hermes card proposals: frontiers in Discoveries 4 (three items) + the
   export doc line (item 1).
2. Whether the swap-regen-restore transaction should become a documented
   recipe for restoring digest-pinned packages when a live dir drifts (it is
   fully witnessed here) — orchestrator call.

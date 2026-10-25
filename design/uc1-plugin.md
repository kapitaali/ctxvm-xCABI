# UC1-PLUGIN — within-harness pause/resume + ctxvm-py binding (design pass)

**Status:** design pass v0 (milestone 1 of the `UC1-PLUGIN` M card; implementation beats
follow after this pass) · **Scope rules:** TELEMETRY-FIRST WEDGE HOLDS — the *tracer* never
mutates messages; resume's boot-time injection, if any, is a separately-gated control
feature, not tracer behavior · **Cross-harness handoff is NOT claimed** (memo-UC1 §4:
page identity transfers, turn render bytes do not).
**Sources:** `research/use-case-1-cross-agent-handoff.md` §3/§4/§5 + its Implementation
Plan · T21 export CLI (committed, witness below) · T17 capture substrate · ORG-1
`uc_registry` (feature gating, thin dispatch) · `09-plugin-parity.md` §1/§4 (one plugin
per harness, wire-format DoD rule).
**Deviation from the board-row sketch:** resume is specified **verify-first** (harness-
native continuation + provenance + verification), with boot-time injection parked as an
opt-in beat pending an orchestrator sign-off — rationale in §3.

## 1. Decisions on record (the why)

1. **Pause = package what the engine already trusts.** Every live capture in the corpus
   is deterministic and replay-clean; the committed T21 CLI already produces the full
   memo-specified artifact set (`manifest.yaml`, `llms.txt`, `trace-N.jsonl.zst`,
   `page-table-N.json`, `checksums.sha256`, `snapshot` DQ/KPI block — witnessed:
   `export corpus/m2/live-echo.jsonl --turn 3 --output dir/ --odps`, replay
   determinism true, projection tallies exact). The plugin therefore does not
   reimplement anything: it flushes the live tracer (stop semantics without stopping),
   snapshots the flushed file (KIT-1 era rule), and packages that file with the
   committed export binary — later the same call becomes a ctxvm-py binding call
   (§5). Interim engine access via the committed CLI is a *thin wrapper* per the
   plugin-organization decision, not new engine logic.
2. **Resume = verify + provenance first.** In v0 all recorded sessions are
   eviction-free (empirical corpus law: zero live evictions; evictions exist only
   in-engine under simulated budgets). A resumed session therefore needs nothing that
   the harness's own session continuation cannot supply natively, because "resident"
   is *everything*. The UC1 v0 surface is thus: (a) at boot, verify the snapshot
   (replay exit 0 at turn N; shared-prefix `diff` against its source roots; checksums)
   and (b) stamp provenance (§4) and hand the snapshot's `page-table-N.json` to the
   operator as the fidelity reference. This keeps the wedge intact TODAY and is
   exactly what §4 of the memo promises honestly.
3. **Boot-time injection is the opt-in control beat.** When a session carries real
   evictions (v1 pager or an eviction-bearing capture via a small-budget live run),
   native continuation no longer equals the page table, and injection becomes real:
   materialize resident pages / identity stubs into the new session's assembled
   context at boot, per the `handoff-inject` feature (off by default). Whether each
   harness's plugin surface permits message assembly at boot is UNVERIFIED at design
   time (opencode `context` hook mutation reach; hermes has the 5 observed hooks only)
   — implementation beat B2 resolves per-harness against the pinned contract and
   falls back to verify-only + operator guidance where injection is impossible.
   `explicit_api` faults (memo Step 3's `vm.fault(handle)`) ship ONLY with the v1
   pager (wedge: control, later, opt-in) — interface noted for RFC-1, nothing built.
4. **Provenance rides the sidecar, not the wire.** `session.open` and every other
   event key are locked by `09-plugin-parity.md` §2 with RFC-0-revision-only changes;
   resume provenance is session metadata, not agent-loop semantics → it lives in the
   canonical sidecar (§3) as opt-in keys, extended through the contract's own DoD
   rule (both emitters, both parity tests, the §table — one card).
5. **One module per harness, feature-gated:** `CTXVM_FEATURES=trace,handoff`
   enables `src/uc1-handoff.{ts,py}`; `…,handoff,handoff-inject` additionally arms
   the injection beat. No per-UC plugin, no CLI subcommand invention at tracer
   run-time (hermes gains a `/ctxvm-handoff` slash command ONLY as a front for the
   same env that the module reads — consistent with `/ctxvm-trace` precedent).

## 2. Pause surface (v0, both harnesses)

- **Trigger:** hermes — `/ctxvm-handoff <dir> [turn]` (env-equivalent
  `CTXVM_HANDOFF_DIR`, `CTXVM_HANDOFF_TURN`; unset turn = package at flush);
  opencode — env-gated (`CTXVM_HANDOFF_DIR[_TURN]`), matching the live adapter's
  existing enablement recipe; a turn-shaped trigger fires right after
  `turn.render` of that turn, then tracing CONTINUES unless
  `CTXVM_HANDOFF_STOP=1` is set (pause is not teardown by default).
- **Flow:** flush current events to the trace file (existing flush path, same
  naming law) → `tools/snapshot-capture.sh <dir> <name> turn-N` style era copy
  → package the snapshot through the committed `export` binary
  (`--turn N --output <dir>/handoff/ --odps`) → print the artifact paths + the
  `snapshot` DQ/KPI JSON to the witness log. All bytes come from the engine;
  the module only orchestrates (logo: "thin wrapper").
- **Verification at pause time is automatic** — the export block already runs the
  replay counterproof and shares its exit law (0 ok / 2 usage).

## 3. Resume semantics (v0: verify + provenance; injection gated, later)

- **Boot check (both harnesses):** with `CTXVM_RESUME_FROM=<snapshot dir>`, the
  module verifies the snapshot BEFORE the first model request: (1) manifest +
  checksums validated, (2) `replay trace-N.jsonl.zst --turn N` exit 0,
  (3) `diff <source slice on disk> trace-N` → relations `a_extends_b`/`identical`
  on the shared prefix, (4) the snapshot's `snapshot.projection` (resident
  slots + stubs at turn N) is surfaced to the operator as the fidelity reference.
  Any failure = loud witness line + tracer continues UNVERIFIED (never blocks the
  agent loop; this is diagnosis, not control).
- **Provenance (sidecar extension, §4 DoD):** canonical sidecar gains optional
  opt-in keys `resumeFrom` (`null` default):
  `{ snapshot: "<abs path>", snapshotDigest: "sha256:…", snapTurn: N }` — both
  emitters write the identical shape; both parity tests extend in the same card.
- **Injection (opt-in, later):** `handoff-inject` arms boot-time context assembly
  = unrealized (§1.3). Explicitly NOT in the first implementation beats.

## 4. Ambition check against the wedge and the parity contract

- The TRACER remains read-only in every v0 surface above; injection is a separate,
  default-off feature beat, gated on a harness-level capability check — wedge-respect
  is preserved by construction, and §4 of the memo (fidelity framing, not
  reconstruction claims) is honored verbatim: the deliverable is
  **page-level state transfer + within-harness byte-identical replay evidence**,
  not a cross-harness claim.
- No event-layer change (§2 table untouched — provenance is sidecar, §1.4);
  the sidecar extension is the only contract delta and follows the §4 DoD rule.

## 5. ctxvm-py binding (PyO3/maturin) — the engine home for the hermes lane

- **Location:** `packages/py/` (maturin build, `ctxvm-py` module name), binding the
  existing ctxvm-core surfaces used by the UC modules — the T16/T18/T19/T21 slice:
  `replay(verify at turn)`, `turn slice/export` (+ ODPS manifest packaging),
  `profile`, `diff`. ODPS YAML assembly stays at the edge (binding emits the same
  JSON the CLI prints; YAML templating stays in the module/CLI layer).
- **Shrink plan (binding lands first):** `packages/hermes/src/plugin.py` keeps hook
  wiring + event emission only; its engine functions (render math / page table /
  replay verify) call ctxvm-py instead of the interim Python mirror — per the org
  decision "engine logic converges on shared bindings; per-port stays interim only
  for thin wrappers". Net: one engine (Rust core), two thin ports (TS tracer core in
  `@ctxvm/node` for the node lane — unchanged by this card — and the PyO3-bound
  hermes port).
- **Parity law:** byte-identical outputs vs the committed rust CLI must hold for
  every binding surface (test set compiles to: replay exits, export artifacts
  byte-identity, profile/diff JSON equality vs `rust/target/release/*` on the
  corpus anchors). This is the binding's DoD; the harness modules then call one
  engine on two languages.
- **Fallback discipline:** until the binding lands, the modules shell the committed
  rust binaries (as KIT-1's kit already does); swapping the call site is the
  binding card's entire integration step.

## 6. Implementation beats (same card, in order)

- **B1 (binding):** `packages/py/` ctxvm-py exposing the §5 slice; tests
  byte-compare binding vs rust CLI on m1/m2 anchors; gate 2 gains the binding test
  (count line updated same-card).
- **B2 (pause modules, both packages, ONE beat each):** `uc1-handoff` module +
  `handoff` feature in `uc_registry` (hermes: NEEDS-REVERIFY against ORG-1's
  landed registry; opencode: `CTXVM_FEATURES` parse lands with this beat — TS has
  no registry yet) + trigger/flush/package/witness flow of §2; tests replay the
  echo fixture through the module and byte-compare the packaged dir against a
  direct CLI run.
- **B3 (resume modules, both packages):** `CTXVM_RESUME_FROM` boot checks +
  `resumeFrom` sidecar extension via the 09 contract DoD (both parity tests in the
  same commit); fixture witness: paused snapshot from m2-echo → resumed session-b
  shares the prefix (`diff` relations) and session-b's trace schema-PASSes.
- **B4 (corpus offer, orchestrator-gated):** propose the m6 drop shape = a real
  pause/resume pair (operator runs the beat; packaging rules per corpus/README).

## 7. Open questions for the orchestrator

1. §1.3: confirm `handoff-inject` stays OUT of the first implementation beats
   (verify-only resume ships first).
2. §5: binding build toolchain — maturin/venvs wiring into gate 2 is new CI surface;
   greenlight a S-sized CI addition or keep the binding off-gate until it exists?
3. §2: opencode lacks any slash/command surface in the live adapter — witness-only
   pauses acceptable there for v0 (hermes keeps induction slash), or should the
   opencode module flip `CTXVM_HANDOFF_STOP` semantics (pause = stop) instead?

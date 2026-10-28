# CtxVM — MASTER HANDOFF (agent-facing)

> **You are a fresh AI agent continuing the CtxVM project.** Everything you need is in
> `/home/theb/Documents/ctxvm/`. Read §0–§4 fully before doing anything. Then pick ONE task
> card from §5, execute it, and report per §4. Do not skip ahead, do not re-plan.

*Last updated: 2026-10-25 · Maintainer rule: whoever completes a task MUST update its card
status in §5 and append the report index line in `reports/LOG.md`. This file is always the
single source of truth for "what's next".*

---

## §0. 30-second context

**Project:** `ctxvm` — a virtual-memory manager for LLM agent context, delivered as
(a) **xCABI**: a portable, deterministic agent-trace/page/fault standard (RFC-0 pending),
(b) `ctxvm-core`: a Rust engine (page table, event log, deterministic renderer, replay),
(c) bindings/tooling (TS via napi-rs, Py via PyO3), and (d) an open measurement stack
(trace corpus → simulator → policy leaderboard) packaged as **ODPS 4.1 / LF** data products.

**Strategic wedge (locked):** telemetry-first, control-later. v0 = read-only flight recorder
for any agent loop (OpenTelemetry playbook). Paging control ships later behind an opt-in policy.

**Current state (2026-10-22):** planning artifacts complete; ODPS manifest + ODCS contract
**empirically validated green**; repo initialized (git main); persistent local venvs under
`venvs/`; Rust toolchain user-provided (cargo/rustc 1.99.1 — non-login shells need
`. "$HOME/.cargo/env"` once per invocation).
**M0 COMPLETE (T1a–T1d done):** codec (strict JSONL, byte-identical vectors) + engine
(page table, deterministic renderer) + replay w/ divergence detection + `replay` CLI.
28 tests, 0 warnings.
**Next frontier:** Stage 2 COMPLETE — **T8 DONE** (`@ctxvm/node` v0 tracer), **T9 DONE**
(`@ctxvm/opencode` adapter spike), **T10 DONE** (corpus drop M1 in `corpus/m1/` + the repo
CI gate: `tools/run-ci.sh` mirrors `.github/workflows/ci.yml`; ALL GATES GREEN locally
2026-10-22, re-witnessed 2026-10-23; GitHub-public remote **live** at
`github.com/kapitaali/ctxvm-xCABI` — first Actions run GREEN 2026-10-23, 4/4 jobs
(RR-ACTIONS-GREEN-20261023)).
**umpire M0 DONE 2026-10-22** (orchestrator green-lit): separate repo `~/Documents/umpire/`,
first commit `d7896df` — decision-ledger v0 as an xCABI-0.1 profile; its validator PASSES
(125 checks, 10/10 negatives) with byte-identical roundtrip ×2, and ctxvm's own
validator/replay consume its ledgers verbatim (details: umpire `reports/RR-M0-20261022.md`).
**T12 DONE 2026-10-23 (M2 live capture):** OpenCode v2 promise-plugin adapter
(`packages/opencode/live/ctxvm.ts`, `export default { id, setup }`, env-gated) → two real
sessions in `corpus/m2/` (echo beats + 5×5 sustained re-fetch) on the free-tier
`opencode/deepseek-v4.1-flash-free` at USD 0; both schema-PASS and replay-divergence-free;
manifest → 0.2.0 (`x-cabi.latestDrop`) + hub re-linked (RR-T12-20261023); Actions run
`39945952460` 4/4 jobs green.
Board T0–T12 complete; **T16 DONE 2026-10-24** (replay CLI forensic flags `--turn/--pin/--output`,
`reports/RR-UC2REPLAY-20261024.md`). Umpire-side cards executed in the umpire repo and therefore
closed here by reference: **T13** calibration corpus (v1–v3; of record `cal-v1:057a5a35a9d4ec71`,
umpire `050bffe`) and **T14** direction decided **local-only now; hybrid later** (umpire
`RR-T14-20261023`) with M3 capture/refit/packaging landed; the residual is the *future hybrid-switch
event* gating Phase C's hosted elements (llms.txt/agent port/publication are runnable locally unless
a hosted surface is chosen). **T15** (Vercel AI SDK adapter) **LANDED 2026-10-27** (landing block at the end of §0 + RR-T15-20261027);
**T17** (UC1 Hermes plugin, UCVERIFY build-first chain) **DONE 2026-10-24** — Hermes
workstream delivered `packages/hermes/` (see board row). The earlier "live captures blocked
by gateway architecture" limitation is **superseded**: T17.7 confirmed the real cause was a
plugin defect (not the gateway) and fixed it, and T17.8 landed the first live drop
`corpus/m4` — see `packages/hermes/BUG_REPORT.md` and `reports/RR-T17.8-20261024.md`.
Actions-green remains live (`RR-ACTIONS-GREEN-20261023`).

**2026-10-25 era committed (analysis chains + plugin decisions — §5 rows carry the detail).**
UCVERIFY build-first chain DONE: T18 `ctxvm profile`, T19 `ctxvm diff`, T20 replay
`--pin (ref, hash)` precision, T21 `ctxvm export` handoff snapshot builder — this closed
UC1 §2–§4 and the UC2 CLI surface. UC3 analysis chain DONE: capacity baseline over the
corpus (RR-UC3-BASELINE), eviction-policy simulator with `--policy/--budget`
(RR-UC3-POLICYSIM), 150-cell budget grid with the three-regime law + reactive-wall
equivalence (RR-UC3-BUDGETSWEEP) — standing law: **NTR is reward-inverted under famine;
quote it only beside service metrics**. HYG-1 closed the tracked-`.pyc` and ungated-metrics
hygiene gaps. **M5 DONE:** first interactive self-capture from the instrumented OpenCode
TUI → `corpus/m5`, manifest 0.5.0; flush semantics = graceful TUI exit (SIGTERM) with the
TUI holding the plugin — era snapshots are mandatory (`tools/snapshot-capture.sh`).
**Plugin organization decided** (00-README "What is decided"): one deployable plugin per
harness; use cases are `CTXVM_FEATURES`-gated modules behind a thin `live/` dispatcher;
engine logic converges on shared bindings (opencode keeps `@ctxvm/node`; the ctxvm-py
(PyO3) binding is the engine home for the hermes port's shared logic).
**ORG-1 DONE:** `uc_registry` skeleton + build-hub sha256 self-baseliner. **UC2-PLUGIN
(hermes lane) DONE:** in-harness forensics surface; **post-cards note 2026-10-25:** the
uc suites were briefly local-only (flagged during the §0 refresh), and UC2-PLUGIN's
arrival closed the gap — gate 2 runs `python -m pytest test/`; **counts are now
hermes 51 (23 plugin + 11 uc_registry + 9 uc2_forensics + 1 UC2 golden parity +
7 UC1-B2 pause) with 27 benchmark tests, both gated truth.** **UC2-MIRROR DONE:**
opencode lane forensics = `packages/opencode/src/uc2-forensics.ts` (TS mirror of the
hermes module) + kit entry `tools/uc2-forensics.sh` + the shared golden fixture pinned
by tests on both sides; TS opencode suite is now 21 tests (12 + 21 gated line) and
both gates now build the release binaries (`run-ci.sh` gate 1b, Actions `ts` job)
because the golden tests shell the real CLI. **KIT-1 DONE:** harness-parity
contract `09-plugin-parity.md` — the xCABI event layer is proven identical across both
plugins, `.meta.json` sidecars canonicalized in both emitters, and the SAME verification
kit serves both harnesses (`tools/verify-capture.sh` smoke-proven on hermes m4 AND
opencode m2/m5). **UC3-WINDOWSHEET DONE:** canonical P-pathology window families committed
as a fixture (`benchmarks/metrics/fixtures/window-families.json`; whole + non-overlapping
2-turn windows; anchors include the 3× m2 lesson; claims rule: any thrash quote carries
its window spec or the word whole). Witness: ALL GATES GREEN at `4813773`.
**Next frontier (supersedes the Stage 2 line above; status 2026-10-25):** UC2-PLUGIN DONE
both sides (hermes `/ctxvm-forensics` + opencode TS mirror with the golden parity fixture
pinned by tests on both sides). UC1-PLUGIN DONE through the design pass, B2 pause (RR-UC1-PAUSE)
and B1 binding — ctxvm-py landed as the §5 fallback subprocess wrapper (RR-UC1-BINDING;
orchestrator ruling: one python port, PyO3 = API-stable future upgrade) — COREXTRACT
(RR-COREXTRACT: the four rust run cores are now the single serialization/exit sites,
61-case byte-neutral proof) — B3 resume DONE BOTH SIDES (hermes `8871dda` + opencode
RR-UC1RESUME-MIRROR: TS mirror now `src/uc1-handoff.ts` + `CTXVM_RESUME_FROM` boot check +
`resumeFrom` sidecar LAST slot; golden parity fixture pinned both sides; design §3 witness
chain landed hermes-side) — and now **B2 pause DONE BOTH SIDES** (opencode
RR-UC1PAUSE-MIRROR: full `uc1_handoff.py` mirror `src/uc1-handoff.ts` — the resume mirror
consolidated under it per 09 §1.2 file law — pause() env/arg law, era-snapshot cp -n
never-clobbers, `--odps` packaging, exact result shapes incl. the 4-key early-failure and
values-order witness quirk; flush-time "package at flush" handoff via
`CTXVM_HANDOFF_DIR[_TURN]` in `live/ctxvm.ts`, `/ctxvm-handoff` witness rendering
byte-exact; ARGV-LAW BUG proven + fixed BOTH sides one card — their pause assembled a bare
positional turn the binary rejects (`unexpected second positional`, exit 2 for every
pause(turn=N) since B2 landed) → 2-line hermes patch to the documented `--turn N` form +
the TS mirror emits it, engine untouched; packaged tree byte-compared vs a direct export
CLI run in both languages, closing the design §6 B2 TODO; counts truth
`ts 12 + 34` / `python 58 + 30 + 8`). The follow-up card LANDED (RR-UC1TRIGGER-MIRROR:
TS `@ctxvm/node` `finish()` idempotency — T17.7 parity mirror, tail computed per call
never appended, `pendingMeta` re-rendered each call, single-flush output unchanged
(12 pre-existing node tests unmodified); the law pinned BOTH sides one card — the
reference docstring had never been test-enforced, hermes `TracerTests` pins it now —
plus the design §2 mid-session turn-shaped trigger: `CTXVM_HANDOFF_TURN=N` fires once
per session right after the turn-N boundary (probe = idempotent finish) → same-naming-
law flush → era copy → `--turn N` package → the hermes-rendered witness; tracing
continues unless `CTXVM_HANDOFF_STOP=1` (registration disposal — pause is not teardown
by default); the cleanup package became the FALLBACK only; junk env = arm-but-degrade
loud witness (their reference crashes its command — their lane); counts truth
`ts 13 + 36` / `python 59 + 30 + 8`) — and **B4 EXECUTED (RR-UC1B4-M6CAPTURE):
corpus/m6, the first real pause/resume pair**, opencode both sides per the operator's
rulings on the proposal's open questions — session-a's real run paused MID-SESSION at
turn 3 by the turn-shaped trigger (witnessed chain, then traced on to turn 6), session-b
boot-verified from the package; NEW ENGINE LAW recorded in the drop (**the render tail
is knowledge-stateful** — era-vs-package `diff identical` is the canonical shared-prefix
proof; full-vs-slice legitimately diverges at residency rows when later pages exist);
manifest `latestDrop: corpus/m6` productVersion 0.6.0 + hub regen re-baselined; ALL
GATES GREEN; **§3 v-next EXECUTED (RR-UC1VERIFY-CHECKS): in-module boot checks (1)(3)(4)
on BOTH sides in the approved cross-lane card** — §3(1) byte-level (checksums rows
re-verified against artifact bytes + manifest sliceTurn cross-check; pre-card the digest
hashed only hex strings so a corrupted artifact passed verification, both sides
disclosed), §3(3) law-aware per the operator ruling (era pair canonical requiring
`identical`; derivedFrom diff diagnostic-only — its divergence IS the lawful
knowledge-stateful shape), §3(4) projection + diff surfaced as witness lines + evidence
keys; the shipped corpus/m6 package re-verifies through the new chain; golden fixture
gains manifest/projection/diff fields pinned both sides; counts now `ts 13 + 47` /
`python 70 + 30 + 8`). **UC1-PLUGIN is DONE: B1 binding + B2 pause both sides + B3 resume
both sides + §2 trigger + B4 corpus beat + §3 in-module checks + UC1-PAUSE-WIRE.**
**UC1-PAUSE-WIRE LANDED (their 5e1dcfd + RR-UC1PAUSEWIRE-20261026 approved backfill):**
the pause counterproof is LIVE (era-pair canonical diff expecting `identical`;
`diff_relation` on PauseResult both sides), `/ctxvm-handoff` now flushes before
packaging (their docstring-vs-body gap closed), and junk env is arm-but-degrade on BOTH
sides (their module degrades loudly; this lane's `uc1Pause` catches and degrades to the
same byte-exact loud line while the strict reader keeps throwing for the adapter's own
arm-time catch — closing a latent cleanup crash on the bare-env `pausePackage` call);
disclosed probed asymmetry: `relation=None` on unparseable diff sources SKIPS at pause
(best-effort) but fail-closes at resume (gate), mirrored identically both sides.
**UC1-B4-M7 CAPTURE LANDED (RR-UM7CAPTURE-20261026): corpus/m7 — the first
hermes-side typed pause/resume pair, user-driven through the gateway service
(ruling D).** Session-a (live TUI after 4 real exchanges) typed
`/ctxvm-handoff /tmp/ctxvm-m7/a 3` mid-session: `exit_code=0 verified=True
divergences=[]`, `relationToSource: "identical"` (29/29 kept), era copies,
tracing continued through turn 4 (32-event stop flush: 11 pages, 0 faults, one
lawful errored hook from the pre-pause Write refusal). Session-b is a genuinely
fresh chat (bare `hermes`) that boot-verified the package BEFORE any hook work
(`resume_from=… verified=True reason=snapshot verified: replay exit 0 at turn 3`
+ `projection: 10 slot(s) at turn 3` + diagnostic `diff: … relation=divergent`
— §3(3)(4) surfacing live) and then rebuilt strictly from the 5 package
artifacts: verified the package itself, found the gate-2 mirror regression
mid-verify, produced a handoff report — the package carried the knowledge, not
a chat history. Negative twins witnessed the same day: run-1's pause exit 2
(flush-name mismatch; archived `/tmp/ctxvm-m7/a-run1`) and the 11:38 fail-closed
resume boot (no package yet). The shipped `handoff/turn-3/` is the RESTORED
boot-verified set: the resumed agent's own in-dir analysis exports clobbered
the live dir's shared per-dir names (per-turn export overwrites
manifest/llms/checksums — engine wart, frontier), detected from the sidecar
digest alone and restored by re-export from the era-as-flushed input under the
original argv (surviving artifacts cmp byte-identical; checksums 4/4;
`snapshotDigest` == boot digest `sha256:7f746595…`). Mirror ride-along
(pre-cleared TS lane): pause dir chain ARG-FIRST per the name-chain law +
`freshTmp` CTXVM_* quarantine + dir-chain law test (the m7 gate-2 leak
regression — 51/51 green clean AND polluted; PY dir-chain env-first stays
their module law, mirror-parity frontier). Manifest `latestDrop: corpus/m7`
productVersion 0.7.0 + hub regen re-baselined; counts `ts 13 + 51` /
`python 74 + 30 + 8`; ALL GATES GREEN (schema 629 checks / 25 fixtures).
**Landing commits:** 2bb339a (TS dir-chain fix) + 8aa7949 (corpus/m7 drop) +
eca05a5 (books); pushed to origin/main. **Still OPEN:** the gated `handoff-inject`
beat (v-next); remaining hermes-lane frontier (gateway `tool=None` hook-key
mapping; verified-boot resume-brief UX); T15 (Vercel AI SDK adapter — **LANDED**
2026-10-27, `packages/ai-sdk` + live `corpus/m8`, RR-T15-20261027).
**UC1-PAUSE-PATH LANDED (RR-UC1PAUSEPATH-20261026):** the m7 frontier card DONE —
`/ctxvm-handoff` now passes `handoff_name=_flush_base()` (closes the run-1
name mismatch); `pause()` dir chain ARG-FIRST (`trace_dir or env`, mirrors TS
2bb339a); export one-dir-one-slice doc line; 2 new tests (handoff-name pass-through
+ dir-chain law); counts `ts 13 + 51` / `python 76 + 30 + 8`; ALL GATES GREEN.
Remaining frontier: gated handoff-inject v-next beat (parked).

**T15 LANDED (RR-T15-20261027), 2026-10-27:** the Vercel AI SDK adapter shipped as
`packages/ai-sdk` (`@ctxvm/ai-sdk@0.0.1`, pin `ai@7.0.154`) per
`reports/T15-PROPOSAL-20261027.md`. B0 re-pin survey found **no hook-point drift**;
four formal deltas sealed as `design/adapters.md` Adapter B ERRATUM (V4 middleware
typing; `tool-result.preliminary` skipped + counted; app-layer `text-delta.text`;
`providerOptions[<name>]` spreads raw body fields — the channel that carries
`chat_template_kwargs`). B1 glue = middleware render anchor (`transformParams` one fire
= one xCABI turn, params returned UNCHANGED — mirror law test-pinned) + fullStream
pass-over tap (recall before execute; page on FINAL tool results; per-step scan
attributed to the producing turn; real `tool-error` parts → deny → no page) +
env-gated flush producing RFC-0 JSONL + a meta sidecar whose
`hookStats`/`mirrorCountsAgree` make the design-risk-1 counts witness checkable per
drop. B2 = canonical mock fixtures with the live-stream recipe canon in the generator
header (`stopWhen: stepCountIs(N)` required; mock `finishReason` must be an
`{unified, raw}` object; text/tool-input streaming fences; app-layer `finish-step`
wall-clock fields stripped in canon) — 8/8 suite green, fixture replay through the REAL
tracer byte-identical, double-run sha256 byte-stable. B3 live drop `corpus/m8` on the
**NVIDIA NIM free tier at USD 0** after the **zen-free-lane BLOCKED eyewitness**
(gateway 429 `FreeUsageLimitError` on bare, CLI-credential-Bearer, and
client-emulating calls; the CLI's success path is client-session-gated — a scripted
`streamText` loop cannot drive zen): model `nvidia/nemotron-3.5-super-vl-120b-a12b`
thinking off per beat; echo 31 events / 10 turns / 3 pages / 4 faults incl. the
**thrown** ghost read that pages NOTHING (error-as-result bodies DO page — the no-page
tier is the thrown one, re-witnessed by re-capturing the canon), thrash 22 events / 6
turns / 3 pages / 3 faults = one `tool_recall` per page·source (m2's fault-dedup law on
a third adapter); schema PASS 108 checks, replay exit 0 both traces
(`faultOfResidentPage` 4×/3×, m2's expected class), checksums sealed; manifest 0.8.0 +
hub re-baselined (m7 duplicate-sentence splice repaired ride-along); run-ci counts
`ts 13 + 51 + 8`. **UC1/UC2 adapter ports deferred as separate future cards** (T15
ruling). Landing commits: `d7e2728` (B0–B2) + `801047c` (B3/wiring) + books.
**Pushed 2026-10-27 to origin/main** (tip `3132805`); Actions run `40470047706`
**green 4/4** (rust/ts/schema/hub).

**Current frontier (status 2026-10-28):** T15 closed. Hermes-lane frontier LANDED
2026-10-28 (`reports/RR-HERMES-FRONTIER-20261028.md`: gateway `tool=None` hook-key
mapping fixed + `/ctxvm-resume` verified-boot slash command; all 80 hermes tests
green; pushed 2026-10-28 with the combined batch — Actions run `40713312977`
**green 4/4**). The gated `handoff-inject` beat is LANDED for the library lane as T24
below (injection-as-DATA); the per-harness injection beat for hermes/opencode
stays parked (v-next). T15 follow-ups settled: **UC1
port LANDED as T22** (`reports/RR-T22-20261027.md`: typed pause/resume mirror
into `packages/ai-sdk`, library-shaped explicit API, provider-key-free
synthetic proof; counts `ts 13 + 51 + 39`, suite 39/39 green first run; pushed
2026-10-27 (origin/main at `0e80bfe`); Actions run `40481242116` **green 4/4**
(rust/ts/schema/hub)). **T23 LANDED** (`reports/RR-T23-20261028.md`:
`ctxvm export` dir-hygiene guard — foreign-slice protection closing the
m7-recorded per-turn export clobber wart; block-unless-`--force` law; counts
`ts 13 + 51 + 40`, rust workspace 52 → 58, all gates green; pushed 2026-10-28
(origin/main at `958e5c4`); Actions run `40704790775` **green 4/4**
(rust/ts/schema/hub)). **T23 books closed 2026-10-28 (addendum `7258413`, echo
run green). **T24 LANDED** (`reports/RR-T24-20261028.md`: handoff-inject for
`@ctxvm/ai-sdk` — the design's gated control beat resolved as
injection-as-DATA; the package is content-blind for full pages →
app-supplied resolver, stubs package-complete via `stubText`; middleware
stays a byte-mirror in every case; counts `ts 13 + 51 + 45`, suite 45/45
green first run; pushed 2026-10-28 (origin/main at `6e28923`) with Actions
run `40713312977` **green 4/4** (rust/ts/schema/hub)), while **UC2
needs no port card** (the forensics CLI is RFC-0-trace-based and host-agnostic
already — proposal §6 records the verdict). RFC-0 makes drops harness-agnostic,
so benchmark/UC3 chains already consume `corpus/m8` without adapter awareness.
**T24 books addendum `bd297f4` in flight** (post-push witness records: RR
verification + the counts erratum `python 76` → `80` truth-up — the hermes
lane's +4 tests were already in-tree when the landing gate ran — LOG T24 +
hermes row push tails, §5 tail; it rides THIS push together with this board
refresh; its echo run is witnessed post-push and deliberately unrecorded, the
T22/T23 pattern). **Board EMPTY** — remaining frontier: the per-harness
`handoff-inject` beat — **opencode half now PROPOSED as T25**
(`reports/T25-PROPOSAL-20261028.md`: the pinned `session.context` contract
documents **mutable `messages`**, so the design's UNVERIFIED mutation-reach
question is resolved at pin time; §7 rulings pending, incl. the cross-lane
clearance for `packages/opencode/**`); hermes half stays verify-only (their
`/ctxvm-resume` UX is the design's lawful fallback); and a third-host
live pause/resume pair (B4 shape — parked: requires the operator to stash the
NEW NVIDIA key locally; the old stash is shredded, its replacement never
transited this chat, RR-T22 §disclosed). Current counts `ts 13 + 51 + 45` /
`python 80 + 30 + 8`.

## §1. Workspace map

```
/home/theb/Documents/ctxvm/
├── 00-README.md                 # overview + locked-decisions table + file index
├── 01-PLAN.md                   # full plan: thesis, prior art, architecture, milestones
├── 02-xcabi-events-v0.md        # xCABI event vocabulary draft + log invariants  ← SPEC SOURCE
├── 03-tracer-api-ts.md          # v0 tracer API + CLI surface
├── 04-odps-dataproduct-corpus.yaml   # ODPS manifest — VALIDATED (see header for proof)
├── 05-llms.txt                  # ODPS-recommended AI discovery file
├── 06-odps-integration.md       # ODPS/ODCS findings + validation results + upstream issue list
├── 07-benchmarks-go-no-go.md    # benchmark suites + metric formulas + M0 pass/fail gates
├── 08-HANDOFF.md                # THIS FILE
└── contracts/corpus-0.1.odcs.yaml    # ODCS v3.0.2 contract — LINT GREEN
```

## §2. Environment & tooling (READ — venvs are ephemeral, recreate as needed)

Two validated toolchains, now **persistent as workspace-local venvs** (built by
`tools/setup-env.sh`, committed in T0). Prefer these over any `/tmp` venv.

| Purpose | Command | Interpreter constraint |
|---|---|---|
| ODPS manifest validation (SDK 0.4.0) | `venvs/odps/bin/open-data-products validate 04-…yaml --json` | any ≥3.9 (venv built on py3.14) |
| ODCS contract lint + product audit | `venvs/odcs/bin/datacontract lint contracts/…`; `venvs/odcs/bin/open-data-products product audit 04-…yaml --json` | **must be Python ≤3.12** — `datacontract-cli` is gated `python_version < "3.13"` and pip SILENTLY SKIPS it on ≥3.13 |
| (planned) Rust M0 | **user provisions Rust globally — agents MUST NOT self-install rustup or any toolchain** (user removed a local install on 2026-10-22). Verify with `cargo --version` first | none known |

Historical (may be dead): ODPS venv `/tmp/opencode/ctxvm-venv` (py3.14, base miniforge);
contract venv `/tmp/opencode/odcs-venv` (py3.12, from conda env `ctxvm-odcs`).

## §3. Rules of engagement

1. **Never redesign locked decisions.** §4-LIST below is authoritative. If a task card seems
   to contradict them, stop, write the conflict into your report, and pick a different task.
2. **Stay in the lane of the card.** No scope creep, no "while I'm here" refactors,
   no dependency upgrades. Discoveries go into the report, not the codebase.
3. **Never delete or edit other agents' reports.** Append-only `reports/`.
4. **All validation claims must include the actual command + output** (or truncated JSON)
   in the report. Saying "it worked" without the command output is a failed report.
5. **Do not rename files** (`00-…` numbering is load-bearing). Do not create new top-level
   directories not listed in a card. Reports and task-specified output dirs are exempt.
6. If environment setup fails after two serious attempts: mark the card BLOCKED in §5,
   write the report with exact errors, pick another card that needs no toolchain.

## §4. Reporting protocol (this is how the orchestrator hears from you)

When a card's Definition-of-Done is met:

1. Create `reports/RR-<TASK-ID>-<YYYYMMDD>.md` (e.g. `RR-T0-20261022.md`) containing, in order:
   - **Card executed:** id + title
   - **What was done:** bullet list (files written/changed, commands run)
   - **Verification:** commands + real outputs proving each DoD item
   - **Deviations from card:** anything you did differently and why (or "none")
   - **Discoveries:** facts that should update other files/cards (be specific)
   - **Open questions:** for the orchestrator (or "none")
2. Append one line to `reports/LOG.md`: `| RR-<TASK-ID>-<date> | <task id> | <one-line summary> |`
3. Update the card's **Status** row in §5 below (and shift the "Next frontier" line in §0).
4. Finally, print a ≤10-line summary of the report to the user.

**Integrity rule (added 2026-10-22, after a prior-art audit in `01-PLAN.md`):** any
external/prior-art claim written into a repo doc must carry its locator (URL / arXiv id /
repo path) at first mention. Unverified → mark `UNVERIFIED-<date>`, never cite as fact.
Web-verify before the white paper or any published prose repeats a claim.

**If blocked or confused:** write the report with status `BLOCKED` + exact error text, then
still print the summary. A failed task documented well is a completed task's equal.

**§4-LIST — locked decisions (do not revisit):** Rust core + napi-rs/PyO3 bindings ·
telemetry-first v0 (tracer never mutates messages) · determinism boundary (no LLM/embedding
in core; semantic faults = plugins) · zero prompt pollution in v0 · evictions batched at
turn boundaries · `call.meta` carries estimated cache cost · ODPS/ODCS strictly at the edge
(never in Rust core) · corpus DQ maps replay-determinism→`validity`(ODPS)/`conformity`(ODCS) ·
Vanilla names not yet final (`ctxvm`/`xCABI` working names — renaming is an explicit
orchestrator task only).

## §5. Task board (pick any card whose status is OPEN and whose dependencies are DONE)

| ID | Title | Size | Depends | Status |
|---|---|---|---|---|
| T0 | Repo init + env setup script | S | — | **DONE** (RR-T0-20261022, commit `bba1f8f`) |
| T1a | Rust workspace scaffold (crates only) | S | T0 | **DONE** (RR-T1a-20261022 + RESOLUTION; cargo 1.99.1, 4/4 tests green) |
| T1b | Event model + JSONL codec + roundtrip vectors | M | T1a | **DONE** (RR-T1b-20261022; 15 tests green, vectors byte-identical) |
| T1c | Page table + deterministic renderer | L | T1b | **DONE** (RR-T1c-20261022; 10 core tests, determinism property green) |
| T1d | Replay engine + conformance vectors crate | M | T1c | **DONE** (RR-T1d-20261022; `replay` CLI exit-1-on-divergence, M0 gate met) |
| T2 | Upstream issue drafts (ODPS + CLI + templates) | S | — | **DONE** (RR-T2-20261022; upstream/issues-drafts.md — 5 drafts, validator lines live-reproduced) |
| T3 | Metric simulator reference impl (Python) | M | T1b | **DONE** (RR-T3-20261022; 18/18 green, CLI verified, fixtures schema-PASS 108/108) |
| T4 | xCABI RFC-0: spec md + JSON Schema | M | T1b | **DONE** (RR-T4-20261022; schema PASS 55/55 vs all fixtures) |
| T5 | ODPD hub pipeline: ODPC catalog via odpc-build | S | T0 | **DONE** (RR-T5-20261022; SDK-built catalog+HTML in hub/, clean twice, byte-identical) |
| T6 | MCP tool-shim design note | S | — | **DONE** (RR-T6-20261022, commit `a835af3`; design/mcp-shim.md 145/180 lines) |
| T7 | Harness adapter survey (OpenCode, Vercel AI SDK) | M | — | **DONE** (RR-T7-20261022; design/adapters.md, anchors @ e965774f / 36e4ce7c) |
| T8 | `@ctxvm/node` v0 TS tracer (stage 2) | M | T4,T6,T7 | **DONE** (RR-T8-20261022; packages/node — 12/12 unit tests, both fixtures schema-PASS + replay-divergence-free) |
| T9 | OpenCode adapter spike wiring `@ctxvm/node` (stage 2) | M | T8 | **DONE** (RR-T9-20261022; packages/opencode — 6/6 glue tests, trace schema-PASS (72 checks) + replay divergence-free; RR-T7's two open questions source-resolved) |
| T10 | Trace corpus M1 seed + CI gate (stage 2) | M | T4 | **DONE** (RR-T10-20261022; `corpus/m1/` — 5 provenance-labeled checksummed traces, manifest 0.1.1 SDK-validated + hub re-linked; `tools/run-ci.sh` + `ci.yml` ALL GATES GREEN locally — Actions-green awaits a remote) |
| T11 | Publish prep: Apache-2.0 LICENSE + Actions-green handover (orchestrator-directed 2026-10-23) | S | T10 | **DONE** (RR-T11-20261023; canonical LICENSE added; all gates re-witnessed green; `ci.yml` verified @`335d986`; **pushed 2026-10-23** to `github.com/kapitaali/ctxvm-xCABI` — first Actions run green after fixing a latent YAML bug (`@`-prefixed step names), run `39942443159` 4/4 jobs green — RR-ACTIONS-GREEN-20261023) |
| T12 | M2 live capture: OpenCode wiring + live corpus drop (orchestrator-approved 2026-10-23) | M | T9, T11 | **DONE** (RR-T12-20261023; v2 promise-plugin adapter `packages/opencode/live/` env-gated + 8 tests; live echo + sustained-pressure sessions on free-tier `opencode/deepseek-v4.1-flash-free` at USD 0, v2.1.2-vs-pinned-2.1.3 diff documented; `corpus/m2/` schema-PASS + replay-divergence-free; manifest 0.2.0 + hub re-linked; Actions run `39945952460` 4/4 green) |
| T13 (umpire-side) | umpire M2 calibration corpus | M | T10 | **DONE by umpire execution** (board row closed by reference 2026-10-24: calibration corpus v1–v3 captured/refit/pushed in the umpire repo — of record v3 `cal-v1:057a5a35a9d4ec71`, isotonic/1, umpire commit `050bffe`; umpire reports `RR-M2V2-20261023`/`RR-M3V3-20261024`) |
| T14 (umpire-side) | umpire M3 hosted-vs-local direction | M | T13 | **DONE** (decision 2026-10-23: **local-only now; hybrid later** — umpire `RR-T14-20261023`; M3 full audit + quiescent v3 recapture + isotonic refit + packaging/hub updated to v3 family, umpire `050bffe`. Residual: the *hybrid-switch event* is a future funding/design decision gating Phase C hosted elements only) |
| T17 | Hermes plugin for within-harness session capture (ctxvm UC1 v0) | M | T8, T12 | **DONE** (RR-T17-20261024; `packages/hermes/live/__init__.py` + `src/plugin.py`, env-gated Hermes plugin wiring 5 hooks to RFC-0 xCABI JSONL; 20/20 tests; `hermes plugins doctor --ci` passes (5 hooks + ctxvm-trace slash command); corpus/m3 synthetic drop schema-PASS + replay-divergence-free; manifest 0.3.0 + hub re-linked; run-ci ALL GATES GREEN; live Hermes captures: env-gating needs gateway restart, slash commands work from inside Hermes — recorded as limitation with both recipes) |
| T17.1 | Fix post_tool_call status taxonomy (ok \| error) for live Hermes capture | S | T17 | **DONE** (RR-T17-20261024 T17.1; real Hermes taxonomy from model_tools.py:_tool_result_observer_fields line 656-671 returns status="ok" on success, not "completed" as hooks.py demo payloads suggest; accept both {"ok", "completed"} in on_post_tool_call (src/plugin.py + live/__init__.py); new test test_live_shape_status_ok_declares_page; HOOKS.md errata noting source line; RR-T17 updated with exact live-capture recipe; 18/18 tests; run-ci ALL GATES GREEN; live capture still requires operator-side gateway restart from separate shell — natural corpus/m4 drop pending) |
| T17.2 | Slash commands `/ctxvm-trace start <dir> [name] \| stop \| status` | S | T17 | **DONE** (RR-T17-20261024 T17.2; register via `ctx.register_command()`, sets module-level trace dir so subsequent hook calls produce traces — no gateway restart needed; `stop` flushes via `_flush_traces()` and clears the dir; `status` reports enabled/dir/name/plugin state; backward-compatible with env-gating; new tests `test_slash_command_start_then_stop` and `test_slash_command_unknown_subcommand`; HOOKS.md §6 + live/README.md document both enablement paths; 20/20 tests total; run-ci ALL GATES GREEN; natural corpus/m4 live drop pending) |
| T17.7 | Hermes live capture zero-page defect — confirmed root cause + fixes | M | T17.2 | **DONE** (RR-T17.7-20261024, commit `27822e6`; `hookStats` counts hook FIRES not recorded events — handlers increment before `_ensure_plugin()` returns None while tracing is off, so 258 post / 235 completed with pages=0 meant the tracer did not exist yet; contributing conditions: tracing enabled after the calls, and an installed plugin older than the repo. Fixes: `tool`/`tool_name` fallback; `extract_page_body()` for plain-string results; state on `sys._ctxvm_tracer_state` surviving re-import; flush-all instead of per-session lookup; idempotent `finish()`; `skipped_untraced` counter; `/ctxvm-trace status` reports version/register_calls/per-tracer events+pages. 21/21 tests; isolated e2e through the installed plugin path: tracing-on-first → 3 pages/0 skipped, tracing-late → 1 page/5 skipped; plugin.yaml → 0.2.0; BUG_REPORT.md rewritten with confirmed diagnosis + deployment and operating rules; run-ci ALL GATES GREEN) |
| T17.8 | First LIVE Hermes corpus drop (`corpus/m4`) | M | T17.7 | **DONE** (RR-T17.8-20261024; after the plugin host was reloaded `version=0.2.0`/`register_calls=1` confirmed via status; real gateway-backed session captured with a deliberate beat: 23 events, 13 `page.declare` across read_file/terminal/skill_view/memory, 1 `tool_recall` fault (identical `sha256sum` twice → `faultOfResidentPage`), 1 errored call correctly producing no page (completed 25/errored 1), 2 turns, residentTokens 7540/headroom 112460, `skipped_untraced: 0`; redaction $REPO/$HERMES_HOME/$HOME/$CAPTURE verified structurally; schema PASS 78 checks, replay exit 0 divergences []; manifest 0.4.0 + `latestDrop corpus/m4`, hub rebuilt + re-baselined, run-ci gains m4 fixtures/checksums/replay and python 21 — ALL GATES GREEN (rust 44/44, ts 12+8, python 21/21, schema 435, hub byte-identity); closes the m3 "live capture blocked" limitation) |
| T16 | UC2 build-first: replay forensic flags `--turn/--pin/--output` (user-directed 2026-10-24, follows RR-UCVERIFY delta class F) | S | RR-UCVERIFY | **DONE** (RR-UC2REPLAY-20261024; point-in-time replay `replay_turn` + force-resident overlay `with_forced_resident` in ctxvm-core (4 new tests, core 15), CLI wired: `--turn N` facts+projection, `--pin <ref>` counterfactual (memo `page:<ref>` form), `--output FILE`, `--help`; default no-flag shape/invariants byte-compatible; 11/11 fixture exit codes unchanged; 33/33 workspace green) |
| T18 | UC2 phase-2/3: `ctxvm profile` forensic aggregation (user-directed 2026-10-24, continues the UCVERIFY build-first chain) | S | RR-UCVERIFY, T16 | **DONE** (RR-T18-PROFILE-20261024; core `profile()` — per-page decision history in declaration order + fault/evict rows in stream order + per-turn tallies at turn.render facts + whole-trace `ProfileSummary` (pages/evictions/faults/faultless roster/declared tokens) + 5 tests (core 20; workspace 38/38, 0 warnings); CLI `profile <file> [--event <type>]... [--turns a-b,c-d] [--source <src>] [--output FILE] [--help]` — agg-only exit contract (no divergence exit; replay owns the fact gate); `--source` requires `--event page.fault`; codec gain: `FaultSource` now `Ord` (axis for keyed maps); 11/11 fixtures exit 0, cross-checked vs known anatomy (m1 thrash: 4 evicts/3 faults = 2 tool_recall + 1 identifier_scan; m2 live-thrash: 10 faults/5 pages/0 evicts pre-eviction shape); run-ci ALL GATES GREEN) |
| T19 | UC1 §4: `ctxvm diff` positional two-trace comparison (user-directed 2026-10-24, continues the UCVERIFY build-first chain) | S | RR-UCVERIFY, T18 | **DONE** (RR-T19-DIFF-20261024; core `diff_traces` — common-prefix/first-divergence, relations identical/b-extends-a/a-extends-b/divergent, page-level delta (declared-only sides, divergent-hash M1b class, tally mismatches at common turn.render facts) + 4 tests (core 24; workspace 42/42, 0 warnings); CLI `diff <a.jsonl> <b.jsonl> [--output FILE] [--help]` with cross-check exit contract (0 shared region matches · 1 divergent · 2 usage); witnessed: UC1 extension shape exit 0 with 12→13 events, mutated-hash copy → divergent@1 + exact M1b divergent-hash row exit 1, unrelated corpus pair correctly divergent @0 with disjoint page rosters; run-ci ALL GATES GREEN) |
| T20 | replay `--pin (ref, hash)` precision mode (user-directed 2026-10-24, closes the last `--pin` surface of UCVERIFY class F) | S | RR-UCVERIFY, T16 | **DONE** (RR-T20-PINPRECISION-20261024; core `Pin` enum — `Ref` broad (T16 semantics unchanged) + `Identity{logical_ref, content_hash}` precision; `with_forced_resident` now takes `&[Pin]` (+2 tests, core 26; workspace 44/44, 0 warnings); CLI `--pin '(ref, hash)'` pins one exact variant (memo `page:` prefix composes; mixed kinds allowed; `pins` report field stays string-array with normalized `(ref, hash)` labels — T16 shape kept); validation exit 2: unknown ref w/ roster, declared-but-other-hash w/ per-ref hash roster, malformed tuple forms; last-comma split handles comma/quote/paren-bearing refs; single-variant refs: precision ≡ broad (witnessed on m1); flip counts Stub→Full only (already-Full target valid, no flip); exit contract untouched (divergent vectors still exit 1); run-ci ALL GATES GREEN) |
| T21 | `ctxvm export` handoff snapshot builder — UC1 §2–§3 (user-directed 2026-10-24, closes UC1's CLI surface) | S | UC1 memo, T18, T19, T20 | **DONE** (RR-T21-EXPORT-20261024; core `export.rs` — positional-prefix slice (last event with turn ≤ N; trailing turn-less bookkeeping excluded; tail-flush sweep-ins proven inert), replay counterproof, turn-N projection, pin lint, redaction scan, 3 KPIs with pinned v0 formulas (+8 tests, core 34 / workspace 52, 0 warnings); CLI `export <trace> [--turn N] [--output DIR] [--odps]` — byte-identical trace slice + page-table-N.json, `--odps` = ODPS 4.1-flavored manifest.yaml (dataQuality: replayDeterminism/sourceFidelity/pinLint/redactionScan + KPI targets + verify commands) + llms.txt + zstd trace + checksums.sha256, exit 0-on-success/2-usage; witnessed: m3 echo @2 (replay slice exit 0 divergences [], diff a_extends_b 18/18, byte-identity, checksums OK), m1 thrash @2 net-token 0.2857, --turn 999 ≡ identity, 2-run determinism, exit-law classes; run-ci gate 3 now enforces the export round-trip chain — ALL GATES GREEN) |
| T15 | Vercel AI SDK adapter — Adapter B implementation + first live drop `corpus/m8` (orchestrator-approved proposal reports/T15-PROPOSAL-20261027.md) | M | T7, T8 | **DONE** (RR-T15-20261027; landing commits `d7e2728` B0–B2 + `801047c` B3/wiring + books; `packages/ai-sdk` = `@ctxvm/ai-sdk@0.0.1` at pin `ai@7.0.154`: middleware render anchor (`transformParams` one fire = one turn, params returned unchanged — mirror law test-pinned) + fullStream pass-over tap (recall before execute, page on final tool results, per-step scan attributed to the producing turn, real `tool-error` parts → deny → no page) + env-gated flush with hookStats + `mirrorCountsAgree` counts witness; design/adapters.md Adapter B ERRATUM (no hook-point drift at the pin: V4 middleware typing, `tool-result.preliminary` skipped, app-layer `text-delta.text`, `providerOptions[<name>]` raw body spread); 8-test canonical fixture suite with the recipe canon in the generator header, fixture replay through the REAL tracer byte-identical, double-run sha256 byte-stable; live `corpus/m8` on NVIDIA NIM free tier at USD 0 after the zen-free-lane FreeUsageLimitError BLOCKED eyewitness (CLI lane client-session-gated — scripted streamText cannot drive zen), model `nvidia/nemotron-3.5-super-vl-120b-a12b` thinking off per beat; echo 31 events/10 turns/3 pages/4 faults incl. the thrown ghost read paging NOTHING (error-as-result bodies DO page — re-captured canon shows both tiers), thrash 22 events/6 turns/3 pages/3 faults = one tool_recall per page·source (m2 fault-dedup law); middlewareRenders == tapStepEnds both traces (10/10, 6/6), mirrorCountsAgree true both; schema PASS 108 checks, replay exit 0 both (faultOfResidentPage 4×/3× = m2's expected class), checksums 4/4; run-ci: m8 fixtures + checksum gate + gate-2 ai-sdk suite + counts line `ts 13 + 51 + 8`; manifest 0.8.0 latestDrop corpus/m8 + RE-VALIDATED line + m7 splice-dedup ride-along; hub regen + hub.sha256 re-baseline; ALL GATES GREEN; pushed to origin/main 2026-10-27 (tip 3132805) with Actions run 40470047706 green 4/4 jobs rust/ts/schema/hub) |
| T22 | UC1-SDK-PORT — typed pause/resume for the ai-sdk library adapter (orchestrator-approved proposal reports/T22-PROPOSAL-20261027.md; one commit per the card's own ruling) | M | T15, T21, UC1VERIFY | **DONE** (RR-T22-20261027; `packages/ai-sdk/src/uc1-handoff.ts` = byte-mirror of the validated opencode UC1 module — `uc1Pause` dir-chain ARG-FIRST + cp -n era copies + documented export argv form + live replay counterproof + era-vs-package diff expecting identical, `resumeVerify` zstd-inside-package + replay exit-0 gate + byte-level checksum rows + manifest sliceTurn cross-check + law-aware era/derivedFrom diff + projection surfacing, `snapshotDigest`/`rustBinDir`/`pauseTurnFromEnv` — all reason strings and contracts byte-identical, mirroring ≠ touching: no opencode/node/hermes bytes moved; library wiring in `src/index.ts`: `createCtxvmCapture({ resumeFrom: { dir } })` runs `resumeVerify` FIRST per the m7 verified-boot-before-hook-work law and on an unverifiable package the constructor THROWS `createCtxvmCapture: resumeFrom boot verification FAILED: …` at init (ruled 2026-10-27 — aborting at the boundary beats silently recording an unverified boot), verified → the WHOLE evidence dict is stamped into every flushed sidecar's `resumeFrom` key (09-plugin-parity §3 nesting, canon top-level keys untouched — red-pinned absent on the plain path) while the resumed capture continues as a FRESH trace of its own (the evidence, not a splice, is the provenance in mirror v0); `capture.pauseAll` = flush-first via the same finishAll path, then `uc1Pause` on the FLUSHED name — `options.name` › flush base `CTXVM_TRACE_NAME ?? sessionKey`, never a fresh "handoff" default (the m7 run-1 failure mode made a law: a test red-ensures the RAW no-name `uc1Pause` still exits 2 `cannot read` while `pauseAll` exits 0 on the flushed files), dir chain ARG-FIRST, `pauseTurnFromEnv` junk law intact; raw re-exports keep flush-is-the-caller's-duty reachable; witness lines `resumeFrom verified digest=… turn=…` at boot and `pauseAll: exit_code=N verified=True/False divergences=[…] diff_relation=…`; PROOF is provider-key-free: committed parts fixture replays through the real middleware/tap → capture A stops after turn 2 → `pauseAll({ turn: 2 })` packages + verifies with era pair identical → capture B boots `resumeFrom`-verified and finishes the continued trace whose sidecar carries the whole evidence (digest == independent recompute, sliceTurn 2, projection slots == page-table-2.json); suite 39/39 green first run (8 prior + 26 byte-faithful mirror laws through the port incl. the SAME committed hermes-generated golden fixture deep-equal + 5 wiring tests), one scope simplification disclosed (the proposal-sketched new fixture artifact proved unnecessary — committed bytes already pin the chain); counts `ts 13 + 51 + 39`; UC2 verdict recorded: no port card — the forensics CLI is RFC-0-trace-based and host-agnostic; ALL GATES GREEN; pushed to origin/main 2026-10-27 (tip 0e80bfe) with Actions run 40481242116 green 4/4 jobs rust/ts/schema/hub) |
| T23 | `ctxvm export` dir-hygiene guard — foreign-slice protection at export time (orchestrator-approved proposal reports/T23-PROPOSAL-20261028.md; one commit, all §7 recommendations accepted) | S | T21, UC1-VERIFY-CHECKS | **DONE** (RR-T23-20261028; the m7-recorded per-turn export clobber wart closed at the source: `export_core` (the single exit/serialization site — ctxvm-py inherits through the binary, byte-identity contract, no py-side change) scans the target dir BEFORE any write for foreign-slice artifacts — turn-named `trace-N.jsonl[.zst]`/`page-table-N.json` whose numeric turn differs (`trace-02` == turn 2) plus a `manifest.yaml` whose `sliceTurn` differs — and foreign present + no `--force` = exit 2 with the reason naming every foreign artifact and the remedy, target dir byte-untouched (guard runs before `create_dir_all`), `--force` proceeds with a warning per artifact + report field `dirHygiene` `{status:"forced", foreign:[…]}`, same-turn re-exports (the m6/m7 restore pattern) stay a clean silent pass; bin gains `--force` argv + usage/help; 6 new fs-level CLI tests in cli.rs — blocked+untouched byte-snapshot, forced (disclosed consequence asserted in-file: the older slice survives checksum-uncovered and the resume-side sliceTurn cross-check fail-closes such dirs), same-turn clean + T21 double-run byte-identity, foreign raw trace, foreign manifest sliceTurn, zero-padded numeric compare; rust workspace 52 → 58 green first run; library-lane proof: ai-sdk ride-along test — `pauseAll` at a SECOND turn hits the guard (exit_code=2, stderr pinned, package dir untouched, capture never breaks) pinning the MIRRORED pause verified-default law (a blocked export produces no package → the counterproof never runs → `verified` keeps its default `true`; an initial draft asserted `verified=false`, corrected to the mirror law — no module change, mirroring ≠ redesign); disclosed scope: trio leftovers without a parseable manifest and non-turn-named artifacts undetected (the m7 shape fully covered); counts `ts 13 + 51 + 40`; ALL GATES GREEN; pushed to origin/main 2026-10-28 (tip 958e5c4) with Actions run 40704790775 green 4/4 jobs rust/ts/schema/hub) |
| T24 | handoff-inject for `@ctxvm/ai-sdk` — the design's gated control beat resolved as injection-as-DATA (orchestrator-approved proposal reports/T24-PROPOSAL-20261028.md; one commit, all §7 recommendations accepted) | M | T22, T23, UC1-VERIFY-CHECKS | **DONE** (RR-T24-20261028; the m7 session-b manual rebuild recipe (llms.txt-led, 5 package artifacts) automated and handed to the app as DATA — NEW `src/resume-brief.ts` `assembleResumeBrief(dir, materialize)`: stub texts package-complete from the slice's `page.evict` `stubText` (the exact text the model was told, last-eviction-wins), FULL slots rendered through the app-supplied resolver (the package is content-blind for renders — `page.render` carries references not text, RFC-0 — the library never invents content); null AND a throwing resolver degrade to loud `[unresolved: …]` markers (never break boot), structural package problems throw at init AFTER the verified boot (T22 law unchanged — inject cannot rescue an unverified boot, byte-pinned); `createCtxvmCapture({ resumeFrom, inject: { materialize? } })` explicit arming + `capture.resumeBrief()` + witness `resumeBrief assembled: slots=N full=M stub=K digest=… turn=…`; THE MIDDLEWARE STAYS A BYTE-MIRROR IN EVERY CASE — with inject ARMED `transformParams` still returns the SAME params object (red-pinned; the design-letter `params.prompt` mutation is the recorded v-next control shape, not built); e2e: pause@2 → resume+inject → the app prepends the brief to its OWN prompt and it rides through UNCHANGED → trace completes `mirrorCountsAgree` true, sidecar canon untouched (the brief is derived data, not recorded state — no `brief`/`injected` keys); opencode mirror module untouched (separate library-lane capability importing `snapshotDigest`); 5 new tests, suite 40 → 45 green first run — assembly structure through the m1-thrash @2 package (the only corpus anchor with BOTH modes at one turn), degrade, capture surface, mirror red-pin, e2e; counts `ts 13 + 51 + 45`; ALL GATES GREEN; pushed 2026-10-28 (origin/main at `6e28923`) with Actions run `40713312977` green 4/4 jobs rust/ts/schema/hub) |

---

### T0 — Repo init + env setup script (S)
**Objective:** make the workspace reproducible for all future agents.
**Steps:**
1. `git init` in `/home/theb/Documents/ctxvm/`; create `.gitignore` covering `reports/`? NO —
   reports are committed; ignore instead: `.open-data-products/`, `*.log`, `.DS_Store`,
   `node_modules/`, `target/`.
2. Write `tools/setup-env.sh` (bash, idempotent, `set -euo pipefail`) doing exactly this:
   - venv A `venvs/odps/`: any python ≥3.10 available; `pip install open-data-products`
   - venv B `venvs/odcs/`: a python ≤3.12 (system may have only 3.13/3.14 → check for
     conda: `conda create -y -n ctxvm-odcs python=3.12` then `python -m venv venvs/odcs` from
     that env; if conda is missing, emit a 5-line instruction to a human and exit 0)
   - print final paths of both `bin/open-data-products` binaries
   - if datacontract tooling missing in venv B, exit non-zero with a clear message
3. Run it; commit all files (excluding ignored) with message `T0: repo init + env setup`.
**DoD:** `tools/setup-env.sh` runs green twice in a row (idempotent); vitals committed;
`contracts/corpus-0.1.odcs.yaml` lints green via venv B; report per §4.

### T1a — Rust workspace scaffold (S)
**Objective:** cargo workspace skeleton matching the architecture in `01-PLAN.md` §3-arch.
**Steps:** create `rust/` as a cargo workspace with crates `ctxvm-core`, `ctxvm-codec`,
`ctxvm-tokenizer`, `ctxvm-conformance` (the last two: stub modules + TODOs). Prefer
`serde`/`serde_json` in core-modules participating in codec; no other deps yet (tokenizer
features deferred). `cargo build && cargo test` green for empty tests. Note the workspace
in `reports/` and commit as `T1a: workspace scaffold`.
**DoD:** `cargo --version` output quoted; `cargo test` passes; crate layout maps 1:1 to
§3-arch of the plan; report + commit.

### T1b — Event model + JSONL codec (M)
**Objective:** typed xCABI v0 events as Rust structs + JSONL codec with roundtrip golden vectors.
**Steps:** read `02-xcabi-events-v0.md` (event table + invariants are the spec). In
`ctxvm-codec`: `Page`, `Session`, 9 event types (`session.open`, `page.declare`,
`page.render`, `page.evict`, `page.fault`, `page.pin`, `page.unpin`, `turn.render`,
`call.meta`) with quoted tags (turn #, sources) per the table; JSONL reader/writer
(strings line-delimited); a **corpus-independent golden vector file** (~6 events covering
every type) under `ctxvm-conformance/vectors/`. Roundtrip: bytes → model → bytes MUST
reproduce identical bytes (property test).
**DoD:** unit tests: every event type deserializes from vector + re-serializes byte-identical;
`cargo test` green; vectors are committed artifacts; report notes any spec ambiguity found
(this feeds T4).

### T1c — Page table + deterministic renderer (L)
**Objective:** the heart of M0: from events → deterministic per-turn render, in Rust.
**Steps:** implement the engine described in `01-PLAN.md` §Decisions and `02` invariants:
stateful page table keyed by `(logical_ref, content_hash)`; apply events to build renderer
state: what's resident/stub'd at each turn; render turn messages (full content vs stub string
template from `02`'s stub format — the stub template is the ONLY prose in the spec; do not
invent new stub text); strict rule: **renders must be pure functions of (events, indices)**;
turn.render token accounting; module-level unit tests with ≥3 hand-summed scenario fixtures.
**DoD:** `cargo test` green incl. determinism property test (two renders => equal); a README
section in `ctxvm-core` documenting semantics briefly (≤60 lines); report.

### T1d — Replay engine + conformance vectors crate (M)
**Objective:** wire replay: read JSONL events → re-apply renderer → compare against
expectation embedded in trace (final renderTotals) → `ctxvm replay` semantics as a lib API.
**Steps:** build `ctxvm-conformance` as the place where vectors + replay checks live;
CLI-binnable binary target `replay` (lib-first, thin main). Green path + one divergence
fixture reported as structured error. Cross-check with `07`: M0 gate "Replay determinism:
100% byte-identical".
**DoD:** replay API green on all vectors incl. divergence detection; documented limits in
report; commit per crate.

### T2 — Upstream issue drafts (S)
**Objective:** file-ready GitHub issue texts for ODPS ecosystem upstreams.
**Steps:** read `06-odps-integration.md` (upstream list + all validation-learned frictions).
Produce `upstream/issues-drafts.md` with one full markdown issue per item: ① `hours` missing
from ODPS SLA unit enum ② doc-vs-schema drift pack (license wrapper, DQ executable array,
DQ spec-string-for-Custom, `displaytitle` casing, `dataHolder.en` wrapper, `version` float
hazard) ③ JSONL/Parquet `dataAccess.format` additions ④ `datacontract-cli` python `<3.13`
marker silently skipping `[contracts]` (SDK 0.4.0) ⑤ ODCS v2→v3 era mismatch in ODPS doc
examples. Each: Title, Context (quote actual validator line), Proposed fix, Evidence
(reference 06 + commands).
**DoD:** 5 complete drafts, each ≤80 lines, evidence real; report; commit.

### T3 — Metric simulator reference impl (M)
**Objective:** make `07`'s metric formulas executable and testable NOW (Python, pre-Rust).
**Steps:** write `benchmarks/metrics/metrics.py`: pure functions over JSONL event streams
implementing net_token_reduction / fault_recall / touch_ratio / thrash_index exactly as
defined in `07` (with cache-miss normalization noted, not invented). 40+ line test file with
two synthetic sessions (one healthy, one thrashing). Wire: `python -m` runner printing JSON.
**DoD:** `python -m pytest benchmarks/metrics` green well; CLI prints correct stats on the
two fixtures; formulas exactly match `07`; report.

### T4 — xCABI RFC-0: spec md + JSON Schema (M)
**Objective:** turn `02` (draft) into `spec/rfc-0/`: an RFC-style markdown (scope, status:
Draft, event tables, invariants, stub format, fault taxonomy, determinism boundary) +
`x-cabi.schema-v0.json` (JSON Schema for JSONL events, strict additionalProperties:false at
event level, tolerant at x- ext level per ODPS extension philosophy).
**Steps:** derive tables from `02`; mark every `OPEN QUESTION` unresolved as RFC "Open"
sections; validate schema against the T1b golden vectors IF they exist yet (else
self-test with 3 inline examples).
**DoD:** schema compiles via `jsonschema` (venv A ok); every event type covered; examples
validate; cross-refs to 02 kept exact; report.

### T5 — Hub pipeline: ODPC catalog via odpc-build (S)
**Objective:** prove the `hub.ctxvm.dev`-as-ODPC-repo claim from `06`.
**Steps:** in a scratch dir, run their SDK's `odpc-build` (see `open-data-products odpc-build
--help`) with fragments generated from `04` (`resources` + explain output as needed); build a
catalog.yaml + static HTML; add wrapper script `tools/build-hub.sh` (idempotent, uses venv A
or B as required).
**DoD:** catalog.yaml + HTML built by script; artifacts committed under `hub/`; script runs
clean twice; report with actual stdout tail.

### T6 — MCP tool-shim design note (S)
**Objective:** specify the loader-side shim that turns MCP tool results into ad-page handles
(fundamental approach in `03`).
**Steps:** produce `design/mcp-shim.md`: call interception point, handle shape (the JSON
seen by model), fault-through-tool_recall matching (Pichay method: same tool+args ⇒ fault),
zero-config flag surface, risk: double-fetch elimination vs cost of gathering; pseudocode ≤40
lines; keep all in pure markdown (no code yet).
**DoD:** doc ≤180 lines; consistent with `02` fault taxonomy; report.

### T7 — Harness adapter survey (M)
**Objective:** concrete, function-level integration plans for the two M2 target harnesses.
**Steps:** inspect OpenCode's session/agent loop (find repo, read the message-loop and
tool-result ingestion paths) and the Vercel AI SDK's streaming/tool-call API; write
`design/adapters.md`: for EACH, the exact hook point (file/function), what `vm.page()`
wraps, what `vm.observe()` needs, test strategy, risk list.
**DoD:** doc has file/function-level anchors (with absolute repo URLs/commit hashes),
both adapters plausible ≤50 LoC glue; report.

### T8 — `@ctxvm/node` v0 TS tracer — stage 2 (M)
**Objective:** TypeScript telemetry-first mirror tracer implementing the T6/T7 contract
surfaces, emitting RFC-0-valid JSONL. No paging/eviction logic (mirror only).
**Steps:** scaffold `packages/node/` (zero runtime deps; Node ≥22.6 type-stripping, sources
run directly); identity minting per T6 §2 (keys-sorted canonical-JSON args, `sha256:<8hex>`,
>120-char refs truncate + `#hash8`); tracer = page/recall/render/scan/pin/unpin/finish;
committed fixtures via `test/generate.ts`.
**DoD:** unit suite green (`npm test` in packages/node); two fixture traces PASS the repo
schema validator AND are replay-divergence-free (`cargo replay`, exit 0, both); report +
commit per §4.

### T9 — OpenCode adapter spike — stage 2 (M)
**Objective:** realize the T7 "Adapter A" mapping in an OpenCode plugin; resolve RR-T7's
two open questions by reading the pinned source; produce a validated session trace.
Mirror-only.
**Steps:** implement `packages/opencode/` handler-per-hook against the pinned payload
contracts (`anomalyco/opencode` @ `e965774f`); reconstruct one echo-session hook-payload
fixture (realistic shapes); generate the xCABI trace; resolve
`toolOutput.truncate` reach-through (`runner/step.ts` + `core/tool-output.ts`) and the
provider-executed gap (same file).
**DoD:** committed fixture set + validator-passing, replay-divergence-free trace + glue
tests + report. (Live dev-build echo session deferred: needs an orchestrator-approved
provider spend and a build at/past the pinned SHA.)

### T10 — Trace corpus M1 seed + CI gate — stage 2 (M)
**Objective:** first ODPS-packaged public corpus slice with honest provenance; re-link the
hub; stand up the repository CI gate — authored as a byte-equivalent local mirror too,
since the repo has no git remote.
**Steps:** materialize `corpus/m1/` (5 traces copied from committed fixtures/generators,
`provenance.json` + `checksums.sha256`); manifest → 0.1.1 + `x-cabi.firstDrop` (SDK
re-validated); `tools/build-hub.sh` regen + `hub/hub.sha256` baseline; `tools/run-ci.sh`
+ `.github/workflows/ci.yml` (pins: py 3.14, jsonschema 4.26.0, open-data-products==0.4.0,
node 26, rust stable); `build-hub.sh` gains venv-or-PATH SDK resolution for CI.
**DoD:** (a) corpus manifest re-validated by their SDK ✓ (b) hub re-linked, regen
byte-identity baselined ✓ (c) green gate witnessed by the local mirror ✓. Deferred:
Actions-green (needs a git remote) and the live thrashing capture (M2, shares T9's
approved-spend prerequisite).

### T11 — Publish prep: Apache-2.0 LICENSE + Actions-green handover (S) — orchestrator-directed 2026-10-23
**Objective:** make the repo pushable to a public GitHub remote without loose ends.
**Steps:** add `LICENSE` (canonical Apache-2.0 text, appendix copyright "2026 the ctxvm
authors"); re-witness `tools/run-ci.sh` ALL GATES GREEN; verify `.github/workflows/ci.yml`
is committed; prepare the create-repo + push handover block for the owner; keep board/LOG
current. Do not touch `research/` (in-progress external work, untracked by design).
**DoD:** gates green; LICENSE present; handover block in RR-T11; report per §4. Owner-only
residue (needs their credentials): repo creation + push + the first Actions run.

### T12 — M2 live capture: OpenCode wiring + live corpus drop (M) — orchestrator-approved 2026-10-23
**Objective:** replace the M1 "live lands with M2" placeholder with real harness captures.
**Steps:** wire the T9 mapping through the OpenCode v2 external plugin surface (no source
patch); capture one echo-beat session and one sustained-pressure session on the free tier;
package `corpus/m2/` (traces + metas + provenance + checksums); bump the manifest and re-link
the hub; extend both CI gates. Version honesty: the available binary was v2.1.2 while T9
pinned contracts at v2.1.3 (`e965774f`) — the observed payload diff is documented in
`corpus/m2/provenance.json`.
**DoD:** schema PASS + replay-divergence-free for both traces ✓; corpus checksummed and
provenance-labeled ✓; manifest SDK-validated + hub byte-identity ✓; all gates green ✓;
Actions green after push.
| UC3-BASELINE | observed corpus-wide capacity-planning baseline, two KPI lenses (post-T21 queue, user-directed) | S | UC3 memo, T18, T21 | **DONE** (RR-UC3-BASELINE-20261024; read-only sweep of tools @ `59f6091` over all 9 committed traces — replay 9/9 exit 0 divergences-free, profile/metrics/export 9/9 exit 0; only m1/session-thrashing carries evictions (4 evict/3 faults → counterfactual netTokenReduction 54.5% ≥ the 40% kpi-net-token target, faultRecall 50% = 2 recoveries ÷ 4 evictions, honest nulls on the other 8); m2/live-thrash = real-traffic fault-rate pathology without pressure (10 faults/5 pages/0 evictions; thrash_index 1.67/turn whole-trace vs 5.0/turn within `--windows 0-1` — window spec is mandatory for thrash claims); T21-vs-UC3 KPI namespace divergence documented (process vs end-state laws; 50%↔0% recall, 54.5%↔100% netTokRed, 22.6%↔100% touchRatio on the fixture — both correct in law, manifests must state namespace); memo §3 policy-comparison command block confirmed placeholder (`metrics --baseline` takes a trace file; cross-session pairing demonstrated invalid at a meaningless "76%") — policy sim stays a v1 build-first proposal; touch-ratio 60% target unreachable under the v0 fault-evidence proxy (max 22.6%); `export --turn 0..9` dynamics reproduce T21's 0.2857 witness at N∈{1,2}; no code changed, no gate renamed) |
| UC3-POLICYSIM | eviction-policy simulator build-first — UC3 §3 (post-baseline queue, user-directed) | S | UC3 memo, T18, RR-UC3-BASELINE | **DONE** (RR-UC3-POLICYSIM-20261025; `benchmarks/metrics/policies.py` — reference-string reconstruction (serve = full renders, recall = faults; stubs/evicts/pins = realized pager answers dropped, pins counted as `droppedPinFacts`) + deterministic sim (`lru`, `fault-pin` @2nd-demand + pinCrunch, `size-based`; reactive overflow-only law; cold entry = fault then serve; double-fetch recalls preserved verbatim) evaluated by the SAME 07 functions over an in-memory synthetic stream (never persisted); `metrics.py` gains `--policy lru\|fault-pin\|size-based` + `--budget` (pairing guard exit 2, `--windows` composes, default path byte-compatible); 9 hand-summed tests → 27/27, 0 warnings; one-out capacity convention `max(Σdemanded − min_demanded, max_demanded)` (half-roster obsoleted — unserviceability wall on unequal pages); one-out sweep 10 traces × 3 policies incl. m4 with unserviced = 0 everywhere: healthy traces cannot separate policies, only sustained demand can (P-pathology premise re-validated on recorded data); m2/live-thrash discriminates: lru 10 ev/50% recall vs size-based 5 ev/100% recall @ NTR 20.5%; recall 200% on live-echo = formula-faithful (2 recoveries ÷ 1 eviction); m4 sim NTR 82.9–87.5% mostly measures its roster under-serving (961 demanded vs 7540 declared)) |
| UC3-BUDGETSWEEP | budget-parametric policy curves over the corpus (UC3 §3→§4; post-POLICYSIM queue, user-directed) | S | UC3 memo, T18, RR-UC3-POLICYSIM | **DONE** (RR-UC3-BUDGETSWEEP-20261025; analysis-only through the committed CLI at `56ae0c1` — 150 invocations rc=0, artifacts local, no code/corpus changes; grid f ∈ {12.5, 25, 50, 75, 100}% × Σdemanded × 3 policies × 10 traces incl. m4 with asserted anchors: A1 reactive law f=100% ⇒ 0 evictions on all 30 curves, A2 wall equivalence on all 150 cells; three-regime law — starvation wall erases policy differences with vacuous-high NTR, pressure band separates, plateau → NTR 0 except m4 flat 82.2–93.1% at every capacity (declaration over-mastery, 961 demanded vs 7540 declared); healthy rosters wall-dominated (m1/healthy wall = 0.9152) ⇒ no discriminating band at any budget — workload shape, not budget level, poses the policy question; NTR reward-inverted under famine (opencode-echo @75% fault-pin 52.8% vs lru 30.5% via under-serving) ⇒ quote NTR only paired with service metrics; live-thrash size-based strict in-band dominance replicated on m3-synthetic; fault-pin pinCrunch shrinks with budget at flat evictions and climbing recall — wins only echo-doubles shapes; two wall-boundary non-monotonicities documented; live-thrash one-out point 239 interpolates the band exactly back to the POLICYSIM cell; ALL GATES GREEN witness re-run; CI-mirror gap (metrics pytest not gated) flagged to the hygiene card, not silently patched) |
| HYG-1 | repo hygiene — tracked-`.pyc` de-tracking + metrics CI gate | XS | T3, RR-UC3-POLICYSIM §Next, RR-UC3-BUDGETSWEEP §Next | **DONE** (RR-HYG-1-20261025; de-tracked the 4 T3-era `.pyc` files via index-only `git rm --cached` + `.gitignore` `__pycache__/ *.pyc .pytest_cache/`; closed the CI-mirror gap — `run-ci.sh` gate 2b runs `pytest benchmarks/metrics -q` (27 tests) and `ci.yml` mirrors it with `pip install pytest`, closing the ungated-since-landing window; fresh ALL GATES GREEN witness incl. the new gate; `packages/opencode/live/ctxvm.ts` diagnostic instrumentation left uncommitted for the m5 self-capture card) |
| M5 | first interactive self-capture (OpenCode TUI) into corpus/m5 + v2.1.4 flush-semantics erratum | M | morning silent-quit incident + T17.8/m4 drop precedent + UC3 live-capture queue | **DONE** (RR-M5-OPENSELF-20261025; instrumented adapter (hooks-witness) committed; flush WITNESSED at graceful TUI exit on era1 snapshot: 80 events, 17 pages, 17 cold-entry identifier_scan faults, 14 turns, zero evictions, 2055 tokens; schema 135 checks on drop, replay rc 0 divergences [], NTR 0.0 quoted beside service metrics per the BUDGETSWEEP reading rule; opencodeVersion null honest + recipe erratum adds CTXVM_OPENCODE_VERSION; manifest 0.5.0 (RE-VALIDATED 2026-10-25 latestDrop corpus/m5), hub regen + hub.sha256 re-baselined, run-ci.sh + ci.yml + 00-README updated; ALL GATES GREEN 21 fixtures / 515 checks) |
| ORG-1 | plugin feature-registry skeleton + build-hub.sh sha256 self-baseliner (2026-10-25 org decision; no behavior change) | S | 2026-10-25 plugin-org decision (00-README "What is decided"), m5-era plugin facts | **DONE** (RR-ORG-1-20261025; `packages/hermes/src/uc_registry.py` — FEATURE_* constants, parse_features (default {trace}), UCModule base; `src/uc1_handoff.py`, `src/uc2_forensics.py`, `src/uc3_planner.py` — no-op stubs; `live/__init__.py` register() is thin dispatcher gating tracer on `trace` feature + dispatching to enabled UC stubs; `test/test_uc_registry.py` — 11 tests (feature parsing, stub no-ops, dispatcher); `tools/build-hub.sh` step 5 self-baselines hub.sha256; run-ci.sh/ci.yml redundant checksum checks removed; hermes 34/34 + opencode 9/9 green; capture path byte-compatible) |
| UC2-PLUGIN | in-harness forensics surface (memo-UC2): expose the committed CLI half (replay --turn/--pin, profile, diff, export) as plugin commands with the verdict decomposition (context-management fault vs model reasoning fault) | S | UC2 memo §3, T16/T18/T19/T20/T21 CLI, ORG-1 | **DONE** (RR-UC2-PLUGIN-20261025; `packages/hermes/src/uc2_forensics.py` — UC2Forensics class wrapping Rust replay/profile/diff/export binaries + verdict decomposition (context-management vs model reasoning fault); `live/__init__.py` — `/ctxvm-forensics` slash command gated by `CTXVM_FEATURES=uc2-forensics`; `test/test_uc2_forensics.py` — 9 tests; hermes suite 34→43 tests; ALL GATES GREEN (schema 515, hub byte-identity); engine untouched — thin per-port wrapper per org decision) OPENCODE MIRROR LANDED (RR-UC2-MIRROR-20261025): TS module `packages/opencode/src/uc2-forensics.ts` + kit entry `tools/uc2-forensics.sh diagnose` (no command hook exists in the opencode v2.1.2 plugin surface — 3 hooks only) + golden parity fixture pinned by tests on BOTH sides (opencode 21 TS tests, hermes suite 51); both gates build the release binaries now (run-ci.sh gate 1b, Actions ts job); count line corrected to truthful 12+21 / 51+27) |
| UC1-PLUGIN | within-harness pause/resume (memo-UC1) + ctxvm-py PyO3 binding card | M | UC1 memo §3, T21 export snapshot builder, T17 capture substrate, ORG-1, bindings decision | **DONE (B2 pause, B1 binding, B3 resume)** (RR-UC1-PAUSE-20261025 + RR-UC1-BINDING-20261025 + RR-UC1-RESUME-20261025; `packages/hermes/src/uc1_handoff.py` — UC1Handoff.pause() flushes live tracer → era snapshot → packages via export --turn N --output handoff/ --odps → replay counterproof; UC1Handoff.resume() verifies snapshot (zstd decompress → replay --turn N exit 0 → SHA-256 digest); `live/__init__.py` — `/ctxvm-handoff` slash command gated by CTXVM_FEATURES=handoff; `CTXVM_RESUME_FROM` boot check writes loud witness lines, never blocks; `_canon_meta()` emits `resumeFrom` (null default, object when resuming); `test/test_uc1_handoff.py` — 9 pause + 3 resume tests; `packages/py/ctxvm_py/` — ctxvm-py binding wrapping Rust replay/profile/diff/export binaries; `packages/py/test/test_ctxvm_py.py` — 9 tests byte-compare vs rust CLI on m1/m2 anchors (42 subtests); `tools/run-ci.sh` + `ci.yml` — binding test added to gate 2, python count 51 + 30 + 8; ALL GATES GREEN (schema 515, hub byte-identity); B4 corpus m6 pause/resume corpus offer (orchestrator-gated)) OPENCODE B3 MIRROR LANDED (RR-UC1RESUME-MIRROR-20261025, kapitaali lane): TS mirror `packages/opencode/src/uc1-resume.ts` line-for-lines resume() `8871dda` (zstd-in-snapshot-dir decompress, replay counterproof, checksums digest, byte-identical reasons/evidence shapes, own helper topology); `live/ctxvm.ts CTXVM_RESUME_FROM` boot check mirroring the hermes witness lines (Python-cased `True`/`False`) + sidecar `resumeFrom` LAST (`{}` early-failure, `null` default); golden fixture generated by the hermes reference pinned BOTH sides same card (TS gold + hermes `UC1ResumeGoldenParityTests`) under cwd=repo-root + relative-anchor discipline; `UC1ResumeWitnessTests` proves the design §3 chain: m2-echo @2 → diff `a_extends_b` → replay `--turn 2` exit 0 → page-table turn-stamped (in-module checks (1)(3)(4) stay v-next); `verify-capture.sh` CANON + run-ci count truth-up `ts 12 + 27` / `python 56 + 30 + 8` (absorbs stale hermes 51); disclosed: zstd-missing latent crash + pause-time dead counterproof (hermes lane); ALL GATES GREEN; **UC1-PAUSE-MIRROR LANDED** (RR-UC1PAUSE-MIRROR-20261025, kapitaali lane): opencode half of B2 — mirror module `packages/opencode/src/uc1-handoff.ts` = full `uc1_handoff.py` (pause + resume consolidated under the 09 §1.2 file law → the B3 appendix's `src/uc1-resume.ts` is superseded/renamed, golden fixture name unchanged); **ARGV-LAW BUG proven + FIXED BOTH sides same card** (hermes pause assembled the bare positional `[trace, str(turn), --output DIR, --odps]` the real binary rejects — `unexpected second positional`, exit 2 for EVERY pause(turn=N) since B2 landed; the shape-only test missed the wire; 2-line hermes patch to the documented `--turn N` form + TS mirror emits it, engine untouched; new hermes tests pin exit-0 success + the cp -n era law); flush-time handoff wired (design §2 package-at-flush via `CTXVM_HANDOFF_DIR[_TURN]` in `live/ctxvm.ts`, `/ctxvm-handoff` witness rendering byte-exact Python-cased); byte-compare test — packaged tree ≡ direct export CLI, both languages — closes the design §6 B2 TODO; slice-turn artifact naming (T21) respected (tests glob `trace-*.jsonl.zst`, `--turn` beyond last window slices identity); disclosed unpatched (hermes lane): pause counterproof dead code (literal-name retarget), `/ctxvm-handoff` never flushes before packaging, junk-env loud-raise parity; TS `@ctxvm/node` `finish()` idempotency (T17.7 parity) + mid-session turn-shaped trigger = explicit follow-up card; counts `ts 12 + 34` / `python 58 + 30 + 8`; ALL GATES GREEN; **UC1-TRIGGER LANDED** (RR-UC1TRIGGER-MIRROR-20261026, kapitaali lane): the pause card's deferred scope DONE — TS `@ctxvm/node` `finish()` idempotency (T17.7 parity mirror in `packages/node/src/tracer.ts`: tail computed per call and never appended to the live event stream, `pendingMeta` never cleared — re-rendered each call; single-flush output byte-unchanged, 12 pre-existing node tests pass unmodified) pinned BOTH sides same card (the reference docstring law had never been test-enforced — hermes `TracerTests.test_finish_idempotent_tail_regenerates` pins it in the same commit as the node twin test); + the design §2 mid-session turn-shaped trigger in `live/ctxvm.ts` (`CTXVM_HANDOFF_TURN=N` — positive int, `"0"`/unset stays the flush-time path — fires ONCE per session right after the turn-N boundary via an idempotent-finish probe → same-naming-law flush (now one shared `flushTraces()` incl. the sidecar truth) → era copy `label=turn-N` → `--turn N` package via the module's own env re-read → the hermes-rendered witness line; tracing CONTINUES unless `CTXVM_HANDOFF_STOP=1` = hook-registration disposal; the cleanup flush-time package is now the FALLBACK only — skipped once any trigger fired, still runs for the no-turn recipe and the ended-before-N case); disclosed: armed-context probe is a full idempotent finish per fire (v0), multi-session one-fired-suppresses-all (v0 — recipes single-session), STOP re-dispose idempotent-safe; junk env arm-but-degrade = loud witness (their reference crashes the slash command — their lane); counts `ts 13 + 36` / `python 59 + 30 + 8`; ALL GATES GREEN; **B4 LANDED — corpus/m6** (RR-UC1B4-M6CAPTURE-20261026, kapitaali lane): the orchestrator-gated corpus beat EXECUTED opencode both sides per the operator's rulings on the proposal's open questions (cross-harness not claimed per design §4; their `/ctxvm-handoff` still ships flush-before-package-broken — their lane); two REAL one-shot agent runs: session-a `CTXVM_HANDOFF_TURN=3` witnessed mid-session (trigger → flush → era copies → `ctxvm-handoff exit_code=0 verified=True`) then CONTINUED to turn 6 → exit flush (32/7/6/5) — UC1-TRIGGER's first real-run witness; session-b `CTXVM_RESUME_FROM` boot-verified before hook work (13/3) with `resumeFrom.snapshotDigest` recomputing from the SHIPPED package; NEW ENGINE LAW: the render tail is knowledge-stateful (diff full-vs-slice shares the 10-event pre-tail prefix, diverges at turn.render residency 253-vs-93) → canonical counterproof = diff(era-as-flushed, package) identical; drop shipped per proposal shape (handoff/turn-3/, m5-style provenance + README + per-drop checksums); run-ci m6 gate lines + manifest latestDrop corpus/m6 v0.6.0 + hub regen re-baselined; hermes lane untouched; ALL GATES GREEN; **§3 v-next CHECKS LANDED** (RR-UC1VERIFY-CHECKS-20261026): design §3 (1)(3)(4) implemented in-module on BOTH sides in the approved cross-lane card — §3(1) byte-level (checksums row re-verification + manifest sliceTurn cross-check; the digest hashed only hex strings, so a corrupted artifact passed boot verification pre-card on both sides — closed, plus their resume() docstring-vs-body gap now real), §3(3) law-aware (era pair canonical requiring identical; derivedFrom diagnostic-only — divergent is the LAWFUL shape), §3(4) projection + diff witness lines at both call sites; success contract unchanged; shipped corpus/m6 package re-verifies through the NEW chain; 11+11 mirrored tests + golden fixture manifest/projection/diff fields; counts `ts 13 + 47` / `python 70 + 30 + 8`; ALL GATES GREEN; **UC1-PAUSE-WIRE LANDED** (their lane ctxvm 5e1dcfd one commit 4 files + opencode mirror pre-cleared same-commit; covered by RR-UC1PAUSEWIRE-20261026 = the operator-approved kapitaali backfill after review found the retargeted verified-semantics shipping with ZERO new tests and no books): their (1) counterproof LIVE (glob trace-*.jsonl.zst → turn parsed from the zst filename → temp decompress outside the package → replay --turn N → type-guarded reader → era-vs-package expecting identical, m6 law; new diff_relation on PauseResult BOTH sides), (2) /ctxvm-handoff flushes before packaging (their docstring-vs-body gap closed), (3) junk CTXVM_HANDOFF_TURN arm-but-degrade (loud line + trigger off); backfill: hermes UC1PauseWireTests (4 new + the happy-path pause now pins diff_relation identical, stale dead-path comment refreshed) + TS module junk-law convergence (uc1Pause catches the turnFromEnv throw → their exact loud line with the RAW env value → turn=null, mirror parity with their Fix 3; strict turnFromEnv/pauseTurnFromEnv keep throwing so the adapter's own arm-time catch stays; LATENT CLEANUP CRASH fixed — pausePackage bare-env call would have thrown out of the untried cleanup gate) + TS tests (3 new: junk degrade, lawful divergent pre-seed via session-thrashing surviving cp -n, pauseTurnFromEnv still-throws pin; argv-law test gains the diff_relation assert); disclosed: relation-None asymmetry probed (the diff CLI fail-closes on unparseable era bytes — pause best-effort skips, resume fail-closes; mirrored identically both sides); counts `ts 13 + 50` / `python 74 + 30 + 8`; ALL GATES GREEN; **UC1-PAUSE-PATH LANDED (RR-UC1PAUSEPATH-20261026):** /ctxvm-handoff handoff_name pass-through + pause dir chain ARG-FIRST + export one-dir-one-slice doc; counts ts 13+51/python 76+30+8; ALL GATES GREEN. **UC1-B4-M7 CAPTURE LANDED (RR-UM7CAPTURE-20261026, kapitaali lane; sessions user-driven)** — corpus/m7, the first hermes-side typed pause/resume pair through the gateway service: session-a typed `/ctxvm-handoff /tmp/ctxvm-m7/a 3` mid-session after 4 real exchanges (exit 0 verified=True divergences=[] relationToSource identical 29/29 kept, era copies, tracing continued through turn 4, stop flush 32 events / 11 pages / 0 faults / resident 20904, one lawful errored hook = the pre-pause Write refusal), session-b a genuinely fresh chat boot-verified from the package BEFORE any hook work (`resume_from=… verified=True reason=snapshot verified: replay exit 0 at turn 3` + `projection: 10 slot(s) at turn 3` + diagnostic `diff: … relation=divergent`) and then rebuilt strictly from the 5 package artifacts (llms.txt-led), verified the package itself and produced a handoff report (37 events / 34 pages / 48080 tokens — package-carried knowledge demonstrated in the wild); negative twins on record: run-1's pause exit 2 (flush-name mismatch; archived /tmp/ctxvm-m7/a-run1) and the 11:38 fail-closed resume boot; the resumed agent's own in-dir analysis exports CLOBBERED the live package dir's shared per-dir names (per-turn export into one dir overwrites manifest/llms/checksums — engine wart, frontier item) and was detectable from the sidecar digest alone: the shipped `handoff/turn-3/` is the RESTORED boot-verified set (re-exported from the era-as-flushed input under the original argv; surviving artifacts cmp byte-identical, checksums 4/4, `snapshotDigest` recomputes exactly the boot digest `sha256:7f746595…`); mirror fix ride-along (pre-cleared TS lane): pause dir chain made ARG-FIRST per the name-chain law + freshTmp CTXVM_* quarantine + dir-chain law test — the m7 gate-2 leak regression (service env leaked to a spawned node --test; 51/51 green clean AND polluted; PY dir-chain env-first stays their module law, mirror-parity frontier); drop: 11 files incl. provenance + README with repro recipe (single-session discipline, unset+restart hygiene), redaction scan 0 hits; run-ci m7 fixture + checksum lines, counts now `ts 13 + 51` / `python 74 + 30 + 8`; manifest latestDrop corpus/m7 productVersion 0.7.0; hub regen + re-baseline; ALL GATES GREEN (schema 629 checks / 25 fixtures) |
| KIT-1 | shared capture kit + harness-parity contract (sidecars canonicalized, event layer locked by tests, one verification tool for both harnesses) | M | user parity mandate 2026-10-25 + ORG-1 org-decision context | **DONE** (contract = 09-plugin-parity.md; LOG row KIT-1 has the full detail; core: canonical .meta.json both emitters (hermes _canon_meta + _witness + _flush_base rename parity; opencode harnessVersion+pluginVersion+extraHookStats), parity tests 9/9 TS + 23/23 hermes, tools/verify-capture.sh smoke-proven on m4 hermes AND m2/m5 opencode, tools/snapshot-capture.sh era snapshots; ALL GATES GREEN 12+9/23+27 tests, 515 schema checks) |
| UC3-WINDOWSHEET | canonical windowed P-pathology sheet: whole + 2-turn-window family committed as a reproducible fixture | M | POLICYSIM next-1 + RR-UC3-BASELINE finding 3 | **DONE** (RR-UC3-WINDOWSHEET-20261025.md; tools/window-sheet.py re-derives benchmarks/metrics/fixtures/window-families.json byte-identically; gate 2b test_window_sheet.py enforces rebuild identity and the 4 pinned anchors incl. the 3x m2 lesson; claims rule: thrash quotes carry window spec or whole; ALL GATES GREEN) |
| COREXTRACT | UC1-PLUGIN B1-CORE (post-binding org ruling): rust CLI run cores extracted into ctxvm-conformance::cli — the single serialization/exit-code sites; bins become thin mains | S | T18/T19/T21 CLI chain + RR-UC1-BINDING (their fallback binding landed first without touching rust/) + 2026-10-25 orchestrator ruling | **DONE** (RR-COREXTRACT-20261025; `ctxvm-conformance/src/cli.rs` 1030 lines = replay/profile/diff/export cores + all previously bin-local helpers + `CliOutcome{exit,stdout,fatal,warnings}` with exact-CLI stderr reproduction; bins 329/295/130/629 → 136/170/101/137 thin mains, parse_args/help verbatim, classic replay report keeps its direct struct serialization (key order preserved); byte-neutral proof: scratch HEAD reference build vs working tree — 61 cases byte-identical (16 pre-refactor baselines + 4 help + 41 argv/error edges incl. read→parse→pin-guard ordering, eq/empty/unknown flags, malformed pins, parse-error files) + both export trees hash-identical old-vs-new and vs baseline (7 odps files incl. zstd frame); cargo test 52/52 across 12 suites, 0 warnings, unchanged — no new tests by design; two disclosed behavior notes: `--event=<bad>` eq-form never validated before → now exit 2 like the flag form (the only matrix divergence; latent bug fix) and `--turns` parse-time `turn_windows` re-wired in the bin for argv-order parity (same function twice = one truth); PyO3 de-scoped by orchestrator ruling (hermes B1 subprocess binding stands as THE python port; design/uc1-plugin.md §6/§7.2 updated); run-ci ALL GATES GREEN fresh witness) |

---

## §6. If you finish the whole board

Do NOT invent new scope. Write a report `RR-BOARD-COMPLETE-<date>.md` summarizing state and
proposing the next three tasks for orchestrator approval. Then stop.

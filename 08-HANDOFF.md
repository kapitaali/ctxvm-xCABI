# CtxVM — MASTER HANDOFF (agent-facing)

> **You are a fresh AI agent continuing the CtxVM project.** Everything you need is in
> `/home/theb/Documents/ctxvm/`. Read §0–§4 fully before doing anything. Then pick ONE task
> card from §5, execute it, and report per §4. Do not skip ahead, do not re-plan.
>
> **Several lanes work here at once.** Read `handoff/LANES.md` before your first edit: it names
> who owns which paths, and the rules for `reports/LOG.md`, `handoff/PROJECT-STATE.md`, the one
> installed plugin copy and the gateway. A shared file is claimed by a commit, not by a message.

*Last updated: 2026-10-30 · Maintainer rule: whoever completes a task MUST update its card
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
`handoff-inject` beat — **BOTH executable halves LANDED**: the library lane
as T24 (injection-as-DATA) and the opencode half as **T25** (2026-10-29,
`reports/RR-T25-20261029.md`: gated mutation at the `session.context` hook —
the pinned contract's mutable payload made the design letter executable;
system surface, inject-then-capture, resolver-less; counts
`ts 13 + 58 + 45`); the hermes half stays verify-only (their `/ctxvm-resume`
UX is the design's lawful fallback); and a third-host
live pause/resume pair (B4 shape — parked: requires the operator to stash the
NEW NVIDIA key locally; the old stash is shredded, its replacement never
transited this chat, RR-T22 §disclosed). **The adoption push now governs new
work** (`08.1-UPDATE-PROMPT.md`, 12 workstreams; intake
`reports/RR-ADOPTIONINTAKE-20261029.md`: conflict check clean, citation
spot-check ALL CONFIRMED): **W2 v0 LANDED** (2026-10-29,
`reports/RR-W2-20261029.md` — the tokenizer stub replaced: `apx4-char`
baseline byte-mirrored + tiktoken BPE backends behind the `tiktoken` feature
+ the `ctxvm tokens` CLI + the `tokens_source` marking vocabulary;
provider-reported usage wiring = W2b pending lane clearance; rust 59 default
/ 60 with the feature); **W1 dry-run LANDED** (2026-10-29,
`reports/RR-DOGFOOD-20261029.md` — `tools/waste-report.mjs`, parity with the
reference metrics.py byte-identical; zero evictions on every real capture →
measured paging waste = 0 and W8 must create pressure deliberately; same-args
re-executions 10–18% but true duplicates 0 — every re-call saw a changed
world; live run scheduled after W4b B1 — owner 2026-10-30, RR-DECISIONS-20261030). **W3 LANDED** (2026-10-29,
`reports/RR-W3-20261029.md` — falsifiability fix: `refetch_rate` rename +
`hard_fault_recall` ground truth per Pichay §3.2 (explicit re-calls only;
n = 4 on real captures → the re-anchored M0 gate is UNMEASURED, falsifiable
in principle, W8 supplies volume); deterministic bootstrap CIs on every gate
metric; pinned `prices.json` v1 (nulls never substituted); counts
`python 80 + 44 + 8`). **Pushed 2026-10-29**: origin/main at
`7a4f499` with Actions run `40845029026` green 4/4 (schema/hub/rust/ts) —
the W3 commit solo on top of the `2a39ddc` batch (whose run `40843322867`
was green 4/4; the rust job's 7 steps include the new tiktoken-feature
gate). Current counts `ts 20 + 58 + 45` / `python 91 + 44 + 8` (hermes +3 from W4b B1
and +4 from W4b B2, 2026-10-30, +2 more from its R4-ts card and +2 from the R5/R4
`page.declare` card, 2026-10-31; node +3 from
the W2b tracer usage API +2 from the node R4-ts card +2 from the R5/R4 card, 2026-10-31;
was `80 + 44 + 8`
through 2026-10-29).
**W4 audit LANDED** (2026-10-29, `reports/RR-W4-20261029.md` — docs-anchored:
`packages/hermes/OBSERVABILITY.md` records the verified contract, the measured
hook cost and the four findings; the load-bearing one is **F1: `identifier_scan`
is DEAD on live Hermes payloads** (`_transcript_texts` expects a parts list;
Hermes sends `content` as a plain string — `conversation_loop.py:350`), so every
live hermes trace (m4, m7) under-reports to zero faults and W1's hermes rows are
not measurements; m7's provenance now carries the erratum).
**W6 LANDED** (2026-10-29, `design/otel-mapping.md` + `tools/otel-export.mjs`):
the OTel view is a **lossy projection, not a container** — xCABI has no clock,
`residentTokens` is not `gen_ai.usage.input_tokens`, and `page.declare` carries no
turn; Langfuse would ingest the projection unchanged (any `gen_ai.*` attribute)
while Phoenix treats `gen_ai.*` as second class (Arize: OpenInference Stable, GenAI
still in development). D3 open — the doc recommends layered as an input only.
**W11 LANDED** (2026-10-29, `README.md` + `01-PLAN.md` §7): the root README now
leads with **adoption status** (one author, one machine, nothing published, no
external adopter) and **measured limitations** (7 rows with evidence pointers —
no real session has ever paged, the hard-fault gate is n=4, tokens are
`apx4-char`, 0/85 provider-reported, the hermes fault surface is dead), and the
"claims nothing you can't re-run" / "Switzerland (LF-governed)" claims are gone,
replaced by what the gates prove and what they do not.
**W12 Steps 0–1 LANDED** (2026-10-29, `design/runtime-abi/00-reconciliation-and-
justification.md`): no `00-SPEC.md` exists and today's "xCABI" is an exchange
format, so the runtime-ABI drafts use the provisional name `ctxvm-rt` (D7);
and the zero-copy justification **fails its own test** — 5 of 85 `call.meta` carry
`latencyMs` and all five are in the synthetic m1 seed, so the benefit is
unmeasurable and the ABI shrinks to safe handles (0.26 ms to hash a 50 KB result
vs any model round trip). Implementation stays gated on W8/D7.
**W7 PROPOSAL LANDED** (2026-10-29, `design/rfc-0.1-proposal.md` +
`design/rfc-0.1/`, proposal only — the sealed `spec/rfc-0/` tree is untouched):
umpire's friction reproduced exactly (three `faultOfResidentPage` violations at
seq 2/3/5 on its intentional A/B ledger; its validator still PASS 113 checks),
and the proposal covers five motivations plus one boundary — R1 new fault source
`intentional_rerun` (safe by default; an `intentional` flag leaves every
source-keyed classifier wrong), R2 `model_pin`/`seed` stay OUT of the ref
(clarification only — moving them in would destroy the priced re-decide), R3
optional `call.meta.providerUsage` (W4B B3's routing target), R4 optional `ts`
on every event + `page.declare.latencyMs` (the clock W6/W12 also want), R5
optional `page.declare.turn`, R0 optional `session.open.schemaVersion` `"0.1"`
as the version boundary. Compatibility is demonstrated: every v0.1-only line is
REJECTED by the sealed v0 validator / parser (exit 2), which is the intended
strictness, not a bug. Umpire's Python minting cross-check is **byte-identical**
(4 decide / 4 hash / 9 approx / canon; 17/17 committed records re-mint) but is
a declared mirror of `ident.ts @ 361043e`, so it is a conformance check and the
repo may NOT claim a "second implementation". Unsealing is **D4**.
**Push witness (2026-10-29):** the accumulated stack — W4 → W6 → W11 → W12
Steps 0–1 → books → W7 — is now origin/main at `cf11d3c`; the stacked push
produced ONE run at the tip, Actions run `40941042878` green 4/4 jobs
hub/schema/rust/ts (the rust job includes the tiktoken-feature step; the ts job
includes the hermes suite, the py binding and the benchmarks suite). This
addendum's own echo run will be witnessed but NOT recorded (books law).
**W10 PREPARE LANDED** (2026-10-29, `design/packaging.md` + README quickstart;
**nothing published, submitted, tagged, or renamed**): the audit found the npm
package is **not publishable as-is** — `exports` points at `./src/index.ts` and
Node "refuses to handle TypeScript files inside folders under a `node_modules`
path" (`https://nodejs.org/api/typescript.html`), so a JS build + `files`/
LICENSE metadata is a prerequisite (`engines >=22.6.0` also predates default
type stripping, v22.18/v23.6); crates.io has a **version-requirement blocker**
(`cargo publish --dry-run -p ctxvm-core` exit 101 — workspace path deps lack
`version`; `ctxvm-codec` alone packages and verifies, EXIT 0); the PyPI wheel
builds (`ctxvm_py-0.1.0-py3-none-any.whl`, 4,939 B) but is a subprocess wrapper
that needs the Rust binaries, so a clean install would be broken. Names:
`ctxvm`/`xcabi` are free on npm, crates.io, PyPI and GitHub; `umpire` is TAKEN
on all four (unrelated incumbents: npm logical framework, crates "Combat Quest
of the Millennium", PyPI Signiant resolver, GitHub org since 2013) ⇒ any future
publication needs a qualified name; npm scope `@ctxvm` ownership UNVERIFIED
(org page 403). License audit: all resolved Rust deps are MIT/Apache-2.0/
Unicode-3.0/Unlicense class, **no copyleft**; npm runtime deps zero; Python
stdlib-only; gate-only ODPS SDK license NOASSERTION/UNVERIFIED. Trademark: web
search only, no record surfaced, **UNVERIFIED** (not a clearance search);
Cursor's "Agent Trace" RFC is an adjacent-words risk, different semantics.
Hermes catalog + OpenCode ecosystem entries are DRAFTED, not submitted; the
Hermes index URL was 404 at check time so exact JSON keys are UNVERIFIED. The
README gains a 5-minute checkout quickstart after the adoption-status block
(W11 first), with OpenCode shim + Hermes `/ctxvm-trace` recipes.
**Push witness (2026-10-29):** W10 is origin/main at `5b15754`; Actions run
`40944095816` green 4/4 jobs ts/rust/hub/schema. This addendum's own echo run
will be witnessed but NOT recorded (books law).
**XERJ INDEX SELECTION — PENDING, NOT ADOPTION** (2026-10-29): XERJ's founder
emailed the maintainer that XERJ selected the W3 metrics commit `7a4f499` for
inclusion in its public Corpus Hub (`https://hub.xerj.org/`) index, under
Apache-2.0 with attribution. The README now records this in the adoption status
and keeps "no external adopter" (it is a reference-index selection of one
artifact, not an XERJ trace, a second implementation, or an outside downstream
xCABI reader).
The listing is **UNVERIFIED/pending**: the live Hub catalogue
(`https://hub.xerj.org/llms.txt`, 530 corpora) and the `corpus-hub` branch tree
in `xerj-org/xerj` (12,257 entries) contain no `ctxvm`/`xcabi` match, and
GitHub issue/commit searches over that repo return none. Owner action: reply
sent 2026-10-29 — the maintainer thanked XERJ and stated no requirements; no
opt-out.
**Push witness (2026-10-29):** the combined push — W10 books addendum
`95adf9e` + XERJ README/books `15e689b` — is origin/main at `15e689b`; Actions
run `40945691069` green 4/4 jobs schema/rust/hub/ts. This addendum's own echo
run will be witnessed but NOT recorded (books law).
**OWNER DECISIONS SETTLED (2026-10-30 — full record `reports/RR-DECISIONS-20261030.md`,
session 2026-10-29→30):** D1 **D1-c substrate now** (lead with capture/replay/measure/
diff; virtual memory stays the roadmap thesis, never a measured claim — W1: zero real
evictions, zero true duplicates); D2 **umpire = demo/reference consumer** (W9 hardening
reproducibility-only; W9 baselines FREE-TIER only — no paid spend outside D5); D3
**D3-c layered** (JSONL canonical + exporter as a declared lossy projection; drift
guard required at exporter promotion); D4 **RFC-0.1 APPROVED as proposed** (R1
`intentional_rerun` source, R2 clarification, R3–R5 optional behind R0
`schemaVersion: "0.1"`; the implementation card is authorized, sealed v0 stays
byte-identical; umpire fixture regeneration is the cross-repo tail; cache-write stays
unmodeled ⇒ pilot reports state ACTUAL BILLED SPEND); D5 **USD 25 hard cap**
(preregistration fits or W8 stops; paid-model `prices.json` row needs a locator + date
BEFORE the run; "inconclusive" is a reportable outcome; W8's outcome reopens D5+D7);
D6 **qualified ctxvm family, no publish until W8** (prepare only — no tags/registry/
index submissions; `@ctxvm` scope + free names unreserved = accepted risk); D7 **hold;
separate project** (W12 stops at Steps 0–1 until W8; `ctxvm-rt` is a separate consumer
project; xCABI remains the trace format, never a C ABI).
**Lane clearances (same session):** `packages/node/**` cleared for the JS build +
metadata with PyPI repo-only until PyO3 and no publish/tag (coupling check done: the
opencode plugin imports node source by relative path, `plugin.ts:24`, so the exports
change cannot break in-repo gates); W4b **B1 only** (B2 deferred to immediately after
W5; B3/B4 → W7); W2b cleared on **all four lanes**, work starts after RFC-0.1 lands;
W1/W5 owner-run scheduled after W4b B1.
**W4b B1 LANDED** (2026-10-30, `reports/RR-W4B-20261030.md`): `_transcript_texts`
accepts the live plain-string `content` shape, so `identifier_scan` is alive on future
Hermes captures (red-before regression pin; hermes 80 → 83, counts `python 83 + 44 + 8`);
B2 followed the same day — see the W4b B2 entry below.
**Support section** (owner-directed, 2026-10-30, `reports/RR-SUPPORT-20261030.md`):
README "Support this project" after Governance — checksum-validated Bitcoin address +
donation policy (all donations → compute + development); funding options analyzed in
the report (grants / credits / paid ports), nothing applied — applications are owner
gates.
**W5 EXECUTED + CLASSIFIED** (2026-10-30, `reports/RR-W5-20261030.md`; owner ran both
captures): both traces RFC-0-valid (replay exit 0); the raw diff's divergences are
classified — turns 3 vs 1 = unit mismatch (W4 F2 confirmed live), tool vocabulary /
args shape / receipt-body hashes = harness-faithful minting + five W7 spec items (a
canonical-ref/body law is REQUIRED for cross-harness byte-comparability);
`identifier_scan` fired twice on opencode (the first live R1-remention evidence),
zero on hermes (pre_llm-at-turn-start granularity — mid-user-turn pages are
unscannable in a single-user-turn session, not a B1 regression); session.open
`unknown/unknown` on hermes = the env law didn't reach that boot (capture-validity
note, capture itself valid); W1 piggyback recorded (opencode waste 0.667; hermes
1.0 metric-degenerate at one turn; zero hard faults — W3 M0 stays unmeasured);
`01-PLAN.md` M2 wording updated; **no corpus drop**, captures stay owner-held.
**W4b B2 LANDED** (2026-10-30, `reports/RR-W4B2-20261030.md`, owner rider): the hermes
generator now emits the LIVE shapes (`make_live_shape_trace()`: plain-string history
via `live_message()`, `tool_name` hooks, `"ok"` string results, `INIT_LIVE`
`unknown/unknown`@200000) with in-emitter self-checks — a generator run cannot produce a
dead-surface trace; NEW fixture `hermes-live-echo-synthetic.jsonl` = the frozen echo's
exact composition through pure live shapes (20/5/3, faults `[identifier_scan@0,
tool_recall@0, identifier_scan@1]`, replay clean, sealed-validator PASS); NEW
`test_generate_traces.py` (4 tests, red-before proven): the end-to-end B1-class death
guard, the returned-history audit, sha-verified byte parity against the sealed
`corpus/m3` drop, and the frozen-write guard (the m3 drop sources can no longer be
overwritten without `--force`). Hermes 83 → 87.
**RFC-0.1 IMPLEMENTED (2026-10-30, `reports/RR-RFC01-20261030.md`):** the D4-approved
addendum landed additively — `git diff --stat spec/rfc-0/ 02-xcabi-events-v0.md` is
empty, so the sealed surface is byte-identical. NEW `spec/rfc-0.1/` = schema
(`schemaVersion` const "0.1", `intentional_rerun`, `providerUsage`, `ts` everywhere,
`turn`+`latencyMs` on declare), normative R0–R5 text, and a validator that also proves
the sealed v0 schema still rejects v0.1-only lines. Rust: `IntentionalRerun` variant,
`ProviderUsage`, `check_version`; core tracks the negotiated version and **exempts
intentional_rerun from the fault-resident rule only in v0.1** (version-branched, not
source-branched — both directions pinned). The gate is wired into all four CLI read
sites, because verification found it had been **dead code**: `replay` exited 0 on
`ab-demo.after.jsonl` (v0 trace + `intentional_rerun`) — the exact "guess" R0 forbids.
A regression test goes red if the wire is removed. v0 unregressed: all 17 corpus traces
replay exit 0, v0 schema gate unchanged at 682 checks / 27 fixtures. Rust 59 → 66.
**Consequence for the queue:** no adapter emits `schemaVersion` (0 matches under
`packages/`), so `providerUsage`/`ts` cannot be emitted today — an emitter card is now
the critical path for W2b and for W1's `providerReported 0/32`.
**RFC-0.1 EMITTER CARD 1 LANDED (2026-10-31, `reports/RR-RFC01E1-20261031.md`):** the
version switch per D8 — `schemaVersion: "0.1"` on session.open in node's tracer
(node/opencode/ai-sdk lanes inherit; opencode imports node by relative path) and the
hermes python port, red-before proven on four standing pins plus two field-order pins
caught mid-work; both derived fixtures truth-up'd (ai-sdk trace: exactly one line
changed, parts frozen, validator leg moved to v0.1; hermes live fixture regenerated
with the frozen m3 corridor holding via the B2 guard); the seal holds (`git diff
spec/rfc-0/ 02-xcabi-events-v0.md` empty) and the v0 gate stays 682/27. Counts
unchanged (`ts 13 + 58 + 45`, `python 87 + 44 + 8`). `providerUsage`/`ts` are now
**emittable** — W2b is unblocked.
**Next frontier:** W2b provider-usage wiring, per-lane (D8: the additive fields follow
as their own cards) → `ts` policy per D9 (default-ON, `CTXVM_TRACE_TS=0` opt-out) →
W10 node build/metadata → umpire cross-repo tail (needs owner coordination — dirty
worktree) → W8 ($25, preregistered) → D3-c exporter promotion (with drift guard) →
W12 Steps 2+ (post-W8).
**W2b CARD 1 LANDED (2026-10-31, `reports/RR-W2B1-20261031.md`):** provider-usage
emission wired — the reference tracer gains `noteUsage` (strict all-or-nothing
intake; orphan-slot claim) and the ai-sdk tap relays each `finish-step` receipt into
its own turn's `call.meta`; opencode and hermes are source-audited **no source**
(their hook terrains carry no usage facts) so per-lane omission is the R3 law there;
the canon trace fixture regen is a 3-line diff (one `providerUsage` per call.meta),
replay clean, v0.1-validator clean — CI now exercises a providerUsage-carrying
fixture. `cacheEstimate` untouched: the est→provider-truth upgrade (and flipping
`providerReported`) is an OPEN owner question with W3/W6 consequences (report §6).
Counts: `ts 16 + 58 + 45` (node +3).
**Next frontier 2 (W2b-1 landed; status 2026-10-31):** owner answer on the
cacheEstimate upgrade question (or skip) → `ts` emission cards (D9 policy: default-ON,
`CTXVM_TRACE_TS=0` opt-out), per lane → W10 node build/metadata → umpire
cross-repo tail (owner coordination — dirty worktree) → W8 ($25, preregistered) →
D3-c exporter promotion (with drift guard) → W12 Steps 2+ (post-W8).
**D12 SETTLED (2026-10-31, this books commit):** the cacheEstimate upgrade question
(RR-W2B1 §6) is answered — **defer to W8** (recommended option taken): est* keep
their page-table semantics everywhere, the provider receipt rides the separate
`providerUsage` fact only, and the est→truth decision moves into the W8 capture
design (W3 price arithmetic + W6 OTel cache_read gate priced there). Recorded in
`reports/RR-DECISIONS-20261031.md` §3; the question is stamped RESOLVED in
RR-W2B1 §6.
**Push status:** `5567d86` (W2b card 1) AND this books commit are committed,
law-signed, UNPUSHED — one owner push command lands both; the Actions run for the
stack gets witnessed on landing (echo; the card's run id is then cited in the
next books pass, per the established echo law).
**Next frontier 3 (D12 settled; status 2026-10-31):** owner push → witness →
`ts` emission cards (D9 policy: default-ON, `CTXVM_TRACE_TS=0` opt-out), per
lane, node lane first → W10 node build/metadata (owner-cleared, no publish/tag)
→ umpire cross-repo tail (owner coordination — dirty worktree) → W8 ($25,
preregistered; D12's est* decision is made there) → D3-c exporter promotion
(with drift guard) → W12 Steps 2+ (post-W8).
**R4-ts CARD LANDED (2026-10-31, `reports/RR-R4TS1-20261031.md`):** per-event `ts`
on the node lane — RFC-0.1 §R4 + D9 default-ON with the `CTXVM_TRACE_TS=0` per-trace
opt-out; opencode + ai-sdk inherit through `@ctxvm/node` (the whole TS mono-tree in
one card); tail facts mint-and-cache their stamps at turn close so repeated
`finish()` flushes stay byte-idempotent UNDER default-on; the three byte-compare
pins run under the named opt-out; the canon ai-sdk fixture stays byte-identical
(= the ts-less v0.1 golden); opencode meta-parity table + both doc anchors extended;
hermes stamps in its own per-lane card. Counts: `ts 18 + 58 + 45` (node +2).
**Next frontier 4 (R4-ts-1 landed; status 2026-10-31):** hermes python-port ts card
(per-lane law — same `CTXVM_TRACE_TS` env + turn-close caching semantics) →
`page.declare` `turn`/`latencyMs` (R5 + R4 halves) cards → W10 node build/metadata
(owner-cleared, no publish/tag) → umpire cross-repo tail (owner coordination —
dirty worktree) → W8 ($25, preregistered; D12's est* decision made there) →
D3-c exporter promotion → W12 Steps 2+ (post-W8).
**R4-ts CARD 2 LANDED (2026-10-31, `reports/RR-R4TS2-20261031.md`):** the hermes
python port stamps `ts` — same law as the node card (per-trace opt-out, one mint
per turn at render() close feeding both tail facts, idempotency under default-ON,
byte-compare pins under the named opt-out); the live-echo fixture regen gained ts
on all 20 lines with the B2 frozen corridor printing SKIPPED and the artifact
staying v0.1-validator-CLEAN; both parity tables + the §2 note updated. ALL FOUR
LANES now stamp per-event `ts` (RFC-0.1 §R4 fully in force on the emission side;
only the `page.declare ` latencyMs half of R4 and R5's turn remain as later cards).
Counts: `python 89 + 44 + 8` (hermes +2); `ts 18 + 58 + 45`.
**Next frontier 5 (R4-ts-2 landed; status 2026-10-31):** `page.declare` `turn`/
`latencyMs` (R5 + R4 halves) cards → W10 node build/metadata (owner-cleared, no
publish/tag) → umpire cross-repo tail (owner coordination — dirty worktree) →
W8 ($25, preregistered; D12's est* decision made there) → D3-c exporter promotion →
W12 Steps 2+ (post-W8).
**Owner decisions D8–D11 recorded (2026-10-31, `reports/RR-DECISIONS-20261031.md`):**
D8 emitter split (version switch first — landed above as `7aa6972`) · D9 `ts`
default-ON with the `CTXVM_TRACE_TS=0` per-trace opt-out (implemented with a lane's
ts card) · D10 `productVersion: "0.1"` bump at the first v0.1 drop + hub regen ·
D11 the three `ctxvm <ctxvm@local>`-signed pushed commits (`36cec7c`, `f0f2710`,
`d21bcb7`) are RECORDED, rewritten never — root cause a transient local git
identity override (removed, verified absent; global config was always law-correct);
standing law now explicit: future mis-signed commits are recorded, never force-pushed.

**R5/R4 `page.declare` CARD LANDED (2026-10-31, `reports/RR-R5TURN-20261031.md`):**
`page.declare` now carries `turn` (RFC-0.1 §R5 — the tracer's counter AT DECLARATION
TIME, pre-first-render −1 stamping as 0 per the RFC-0 §5 convention `page.fault`
already uses) and accepts `latencyMs` (§R4's emit half) — BOTH emitters in ONE card:
node `declarePage()` choke point over both push sites + `declareLatencyOf()` strict
intake (safe integer ≥ 0, `0` is a fact, absent/invalid ⇒ key omitted), hermes
`_declare_page()` + `declare_latency_ms()` mirror with `bool` excluded (bool IS int in
Python). Wire order `type,page,turn,latencyMs?,ts`. Reveal bookkeeping UNCHANGED — a
declaration turn and its render turn can differ by more than one, now pinned on both
ports. **`latencyMs` is accepted-but-unemitted: no lane has the fact** (opencode
`session.context`/`tool.execute.*`, hermes tool pairs + `pre_llm_call` history —
RR-W2B1 §1 audit), so both parity tables gained `turn` and NOT `latencyMs` (the pin
deep-equals the observed key set; the providerUsage precedent, documented in both
tables). Fixtures: ai-sdk canon regen = EXACTLY one line (the single declare gains
`"turn":0`), hermes live-echo regen = 3 declares gain turn 0/1/2 with all 20 `ts`
values REminted (disclosed, not pinned) and the m3 corridor printing SKIPPED.
Disclosed drafting error: the first node turn pin expected turn 1 right after the
first render — the counter law is 0 (the first `render()` advances it to 0); caught by
the implementation run, pin corrected and extended to pin the reveal turn. Counts
`ts 20 + 58 + 45` / `python 91 + 44 + 8`; ALL GATES GREEN; sealed + frozen untouched.
**UMPIRE CROSS-REPO TAIL LANDED (2026-10-31, umpire `d8ecef4` + `a701072`):** the last
open item of the RFC-0.1 chain is closed on the consumer side. umpire adopted the profile —
`session.open` declares `schemaVersion:"0.1"` (R0) and a deliberate re-decide emits
`page.fault source:"intentional_rerun"` (R1), with its validator's L4 rule
version-branched (v0 ledgers keep the strict `tool_recall`-only rule) and its vendored
schema RE-VENDORED from this repo at `36cec7c` (the old `$defs` fork of the v0 schema is
gone, so the next bump is a re-copy). Measured proof with THIS repo's tools on the
verbatim ledgers: `replay fixtures/ab-demo.ledger.jsonl` went from **3×
faultOfResidentPage** (the exact friction RFC-0.1 was written for) to **0 violations /
0 divergences**, all four ledgers clean, and `spec/rfc-0.1/validate_schema_v0_1.py`
passes each. umpire's own gates stayed green (fixtures 207 checks / 14 negatives, 4×
replay BYTE-IDENTICAL, corpus 905/945 + v3 2505/2625, checksums 9/9, hub
byte-identical) and its calibration corpora were deliberately left v0 — their hashes are
the calibration of record, and a v0 ledger is a true statement about a capture that
predates the field. Accounts: umpire `reports/RR-RFC01-20261031.md` (the card) and
`reports/RR-REVIEW-20261031.md` (the measured state review that also fixed two
`.gitignore` defects: `tests/` had been ignored while holding tracked gate artifacts, and
the `research/` line matched nothing because of an inline comment). No byte of this repo
changed for the tail.
**CI-1 LANDED (2026-10-31, `reports/RR-CIALIGN-20261031.md`):** the workflow is now
TESTABLE before a push — `tools/ci-rehearsal.py` clones the repo, overlays the working tree
and runs each job's `run:` steps in order with a per-job venv, stopping at the first failure
like Actions; `tools/export-roundtrip.sh` is the T21 chain shared by the mirror and the
workflow. Diffing the two found three real gaps, now closed: six fixtures (corpus/m6, m7, m8)
were never validated in CI, three drop checksum steps were missing (m6–m8 — the entire UC1/
M8 era had no integrity check in CI), and the export round-trip chain was absent altogether.
Rehearsal red-before proven (`run: exit 7` → FAIL, exit 1); rehearsal OK 4/4 jobs in a
pristine clone; ALL GATES GREEN. VERIFIED ON GITHUB: run 41240870951 on `31bd84f` — 4/4 jobs,
34 s, every new step executed (step conclusions only; the job-log endpoint needs auth here).
**DAY CLOSE 2026-10-31 — `reports/RR-DAY-20261031.md`.** Fifteen commits: the RFC-0.1 emitter
switch (`7aa6972`), W2b provider usage (`5567d86`), R4-ts on both lanes (`7292c42`, `6695baa`),
R5/R4 `page.declare turn`+`latencyMs` (`0da0afb`), W10 node build (`72360f1`) and its CI wiring
(`1aeee16`), CI-1 + rehearsal tool (`efef2c2`, `31bd84f`), and four books commits. Verified the
same day: `ALL GATES GREEN`, Rust 66, ts 20+58+45, python 91+44+8, schema v0 682 checks, node
build parity 16 events, export round-trip green; GitHub run `41240870951` 4/4 jobs in 34 s with
every new step executed. Two red-before probes on record (`rewriteRelativeImportExtensions`
off → `TS5096`; `run: exit 7` → rehearsal exits 1). Defects found by verification, not by plan:
three CI↔mirror drifts (now closed), and my own overstated npm framing (corrected in the report
and `design/packaging.md` §9). State: `HEAD 715c31e`, `origin/main` agrees, tree clean, sealed
surfaces untouched. Open and NOT started: W8 (owner-gated, $25 + preregistration), D3-c, W12,
CI option 3 (release card), the `engines` floor (unverified, so unchanged), rehearsal-in-CI, and
job-log detail from GitHub (endpoint needs auth; step conclusions only).
**Next frontier 7 (umpire tail landed; status 2026-10-31):** the RFC-0.1 chain is closed
end to end; remaining work is the emitter-side feed for `latencyMs` only if a lane ever
measures a hook latency → W10 node build/metadata (owner-cleared, no publish/tag) → W8
($25, preregistered; D12's est* decision made there) → D3-c exporter promotion (with
drift guard) → W12 Steps 2+ (post-W8). umpire's own open queue (hermes integration
tracking, the two drifted MCP servers, Phase C) is ranked in its
`reports/RR-REVIEW-20261031.md` §5 and needs no ctxvm action.
**W8 PREREGISTRATION LANDED (2026-11-01, `reports/RR-W8PREREG-20261101.md` + the freeze
`design/w8-capture-design.md`):** the decisive experiment is designed and frozen BEFORE
any run (08.1 §W8 prereg-before-run law; D5) — no data, no engine code, no spend in the
card. Arms: naive (stock built-in compressor, must record never-fired at the
preregistered scales else the task drops both-arms) vs paged (a NEW ctxvm context-engine
plugin implementing the v1 `FaultPinPolicy` law); ONE-FACTOR = only the
`context.engine` selection differs. Seam verified at source on the v0.22.5 pin
(`agent/agent_init.py:1904` `_select_context_engine()` + the full `ContextEngine` ABC:
`select_context()` per-request resident-set replacement running before cache-control,
`prune_tool_results_only()` no-op in v1, `update_from_response()` canonical buckets incl
the cache split, `clone_for_agent` copy law; safe-worker mode must be OFF) — the design
records the FITS verdict for FaultPinPolicy v1 and folds in the W12 Step 1 fork-forfeits-
cache finding as the pinned-first append-stable ordering law. Grid k = 6 real-repo
templates + mechanical checkers, R = 3 per cell alternating; metrics are the 07-verbatim
formulas over RECORDED arm baselines (the counterfactual fenced to non-gate use) with
deterministic CIs; gates = the 07 §M0 rows exact (NTR ≥ 1.5× at a preregistered δ = 10 pp
paired-accuracy non-inferiority + `hard_fault_recall` ≥ 95% @ CI lower bound with n ≥ 30
hard faults pooled BOTH arms + replay determinism 100%). Stopping: coverage stop
(cell ≥3 AND n ≥ 30) with preregistered round-robin continuation (no
cherry-picking rounds), the naive-arm 75%-real-window abort = a named design-pressure
shortfall, 4 engine crashes total = BLOCKED report, and NO mid-run expansion (a defect
after runs start makes the runs a PILOT record; the gate re-runs under a new design
version). D5: USD 25 hard cap, append-only `reports/W8-SPEND.md`, the
`priceModelVersion` 2 paid-row lock (locator + access date) BEFORE the first paid run,
free tier legal at ledger 0 (tokens stay the primary unit), a binding pre-run projection
stop, est-arithmetic USD + actual billed spend side by side. D12 fork RULED (owner
ratifies): est* keep page-table semantics; the hermes port gains the
`post_api_request` → provider-usage wiring as a W8 implementation precondition
(`providerReported` TRUE in W8 captures; the W6 OTel gate untouched). Redaction DQ law
registered (08.1 §4): mkdtemp workspaces + automated zero-match credential scan before
ANY ship + provenance per m8 shape + publish default hashes/counts; a corpus drop stays
a separate owner gate (W5 precedent). ALL GATES GREEN, counts unchanged.
**DAY CLOSE 2026-11-01 — `reports/RR-DAY-20261101.md`.** Six commits across both lanes:
research lane `27f1e68` (white-paper cleanup — attribution corrected to Mason, the abstract-vs-body
token figure stated, and `research/white-paper/build-pdf.sh` because the documented command could
never have produced the committed PDF; 15 pp / 93 KB / zero mojibake / 12 sections / 8 references);
coordinator lane `849dc1e` (W8 prereg frozen), `14d7c38` (CI-2: ts red classified runner-locked, the
step now records its environment; next run green), `d726533` (naming evidence), `e132de7` (engines
floor verified), `547b594` (npm scope mechanics). State: `HEAD 547b594`, 3 unpushed (coordinator),
tree clean, ALL GATES GREEN. Open: W8 owner ratification + implementation GO, CI-2 runner-locked until
a recurrence yields logs, the sibling repo's W9 transfer run queued on owner GO (CPU only), and the
owner calls on the W9 KPI targets / D2 / D3-c + W12 order.
**PLUGIN-DEFAULTS (2026-11-01, `reports/RR-PLUGIN-DEFAULTS-20261101.md`):** capture now works
without a manual — `~` expanded (it used to land in a literal `~` dir), ON by default into
`${XDG_STATE_HOME:-~/.local/state}/ctxvm/traces` at 0700 with a documented opt-out
(`CTXVM_TRACE=0` / empty dir), a `stop` that reports `N trace(s) flushed` or `0 traces written`,
and model/provider read from the hook payload instead of env. First default-ON capture (gateway
with ZERO `CTXVM_*` vars): 1,530 bytes, 6 events, `model` correct, `provider` unknown (payload
gap), `session_start` never fires in this build (tracer is created lazily by `pre_llm_call`).
Tests 91→95 hermes, 58→59 opencode; counts trued up; ALL GATES GREEN. Open on this thread:
write-through flushing (a crash loses the session) and a retention cap — the price of default-ON.
**PLUGIN-DEFAULTS addenda (same day):** both debts are paid. Write-through persists a partial
snapshot every N units of activity (per EVENT in hermes, per HOOK FIRE in opencode — the TS plugin
hides its event list, and the divergence is stated in `09-plugin-parity.md` §5.1); a complete flush
deletes the partial before writing the final pair. Retention prunes oldest-first on count (200),
age (30 d) and bytes (512 MiB), never the file just written. Not claimed: sidecars and the witness
log do not count, and pruning runs at flush time only. Plugin 0.4.0.

**W13 (2026-11-01, `reports/RR-W13-20261101.md`):** `turn.render` gains an optional `prefix` —
`toolSchemas`, `messageCount`, `requestChars`, `systemPromptBytes`, `approxInputTokens`, and a
REQUIRED `source` (measured/estimated/unknown). Filled from hermes' `pre_api_request`
(`agent/turn_api_request.py:60-79`: tool_count, message_count, request_char_count, system_prompt,
approx_input_tokens); opencode honest-reports `unknown`. Version-gated, allowlisted in the strict
codec, three validator negatives + v0 boundary case, conformance vector updated. rust 66→67,
hermes 98→99. Why: arXiv:2610.22732v1 removes 13.2–17.7% of cost by pruning tool schemas that are
billed every turn — a cost class our ledger could not see, and the reason our one real capture
reported a degenerate waste of 1.000. **NOT claimed: no live trace yet (gateway restart needed for
`prefix.toolSchemas > 0`), and nothing here reduces cost — it makes cost measurable.** The same
payload carries `provider`, so the `provider: unknown` gap is now a small card, not a redesign.

**Prompt:** `08.1-UPDATE-PROMPT.md` gained W13–W16 (prefix, environment key, side-effect class,
causal edges) plus a §9 line that forbids claiming a token saving we have not measured.

**DAY CLOSE 2026-11-03 — W15 finished on a handover, W14, W16 design, one flake.**
W15 (`3efc250`): `page.declare.toolEffect` (READ_ONLY|MUTATING), registration-owned, name-only,
fail-safe, valid only on tool_result; the draft's three defects fixed (fused docstring line blocking
the Python gate, nested check_version, unstarted TS lane). W14 (`b6fb370`): `session.open.
environmentId` = env- plus 12 hex over the credential-stripped remote or the worktree path — digest
only, no path/remote/branch; opencode+ai-sdk derive from cwd, HERMES EMITS ONLY FROM AN EXPLICIT
`CTXVM_ENVIRONMENT_ID` because the gateway process's cwd is not the session's workspace. W16
(`3261df6`): design note only — a page/turn DAG is derivable at zero bytes, instance identity is
not, and all three lanes already expose a per-call id. Flake (`3073532`): the gate went red on a
docs-only commit and green on an immediate re-run of the same commit; recorded with the next step
(capture the failing suite's stdout) rather than treated as fixed. Tests: rust 70, ts 21+61+45,
python 104+44+8, validator OK, ALL GATES GREEN; plugin 0.6.0. **Live confirmation of prefix,
toolEffect and the READ_ONLY:MUTATING split still needs a gateway restart.**

**DAY OPEN 2026-11-04 — two cards landed, then the live wire facts started proving out.**
Books correction (`6070b0c`): the 11-03 index above was committed at 12:46 and named only the
four commits that existed then; the day ran to 15:35. Hermes environmentId (`2d6bff5`):
SUPERSEDES the clause in the 11-03 close above that reads "HERMES EMITS ONLY FROM AN EXPLICIT
`CTXVM_ENVIRONMENT_ID`" — the audit found the opposite: hooks run in the gateway process's own
cwd (`plugin_session.py`), but the plugin handle exposes the session workspace
(`ctx.session_cwd()`, plugins.py:605, documented "never the gateway process's own cwd"), so the
hermes lane derives the digest-only id per session, cached, explicit env still wins, empty
workspace still absent, and each TraceInit carries its own id (one gateway, several workspaces).
Remote normalisation was fixed in BOTH lanes at once (https and ssh forms of one repository
hashed differently); python and node now AGREE (env-2b4652ae9d98 for this repository).
First real 0.7.0-import capture (13:00, `reports/RR-LIVE-20261104.md`): **W13 prefix rides a
real turn.render measured (toolSchemas 21)** and **W15 toolEffect rides every completed
tool_result (terminal fails safe to MUTATING)** — two of the three pending facts PROVEN.
`provider "unknown"` stands as the no-backfill absence until the owner writes
`plugins.entries.ctxvm-tracer.settings.provider`; `environmentId` rides the NEXT capture
because the restart (gateway PID 23146, 13:03:38) postdates the 0.8.0 sync (12:57:19); old
traces keep (unknown) by append-only. Tests: hermes 112 + 44 + 8, node 21; ALL GATES GREEN;
plugin 0.8.0 (yaml pinned by test).
**DAY CLOSE 2026-11-05 (index cutoff 10:38) — five commits; the paper gained its safety half, and
the capture gained a checker.** The stream's `turns` column was reading MAX turn INDEX, so a
one-turn session displayed zero turns (`0ac1746`, rust 72→73; corrected live read: 2 sessions /
2 turns / 20 declarations for `env-2b4652ae9d98`). A post-restart capture reused the default trace
name and the write-through replaced the 13:0x evidence at the same filenames; `18e1123` re-anchored
`RR-LIVE` to the surviving bytes and turned the collision into a candidate card. Two independent
safety notes converged into `research/synthesis-20261105.md` as the record (`e171a0b`; the sources
stay on disk under the gitignored `research/uncommitted/`). The white paper (`0e1168c`,
`reports/RR-WPSAFETY-20261105.md`) now carries the seven research questions as §8.7–§17 — threat
model, counterfactual replay, evaluation infrastructure, monitor views, provenance, control,
audit and regulation, what ctxvm cannot do, and a status table that marks every row unanswered —
with three body-level figures marked UNVERIFIED and one measurement (417 declared / 312 rendered /
303 faults / 99.3% on rendered, reported as definition-bound caution). `index.md` had drifted from
the paper; `sync-index.py --check` now enforces the rule the README states. W17 (`e9656fe`,
`reports/RR-COVERAGE-20261105.md`): the flush is a triple, `tools/coverage_check.py` is the law,
and the checker caught the live `tool_name` defect that had classified every live hermes declare
MUTATING on 0.8.0 (447 witness rows read `tool=None`). Tests: rust 73, ts 21+61+45, python
117+44+8, plugin 0.9.0, ALL GATES GREEN. **Live proof of W17 and of the stamp fix still needs the
gateway restarted.** The installed copy at `~/.hermes/plugins/ctxvm-tracer/` is now 0.9.0 and proven
by import and by a smoke flush in a temp dir: the triple landed, the declare stamped READ_ONLY from
`tool_name`, and `tools/coverage_check.py` returned 0 on the pair. The running gateway still holds
0.8.0 in memory, so live traffic keeps the old behaviour until the owner restarts it. **TS ORDER (`RR-TSORDER-20261105`):** the gate was red on the docs-only W19 commit — the node test
asserted "the tail is time-monotonic", but `finish()` groups the tail by class (all `turn.render`,
then all `call.meta`) with each pair sharing the turn's render stamp, so the sequence is a sawtooth
that looks monotonic only inside one millisecond. The 11-03 fix had swapped one clock-luck assertion
for another; both lanes now assert stamp equality per turn plus ascending turn stamps, and the
red-before probe (fresh meta stamp → 2 red) is recorded. Same day, same block: W19's commit landed
with a red gate because `run-ci.sh | tail -2` returns `tail`'s status — the gate is run unpiped now.
W18 (`RR-MONITOR-20261105`) extends the index
past its first cutoff: a deterministic tier-1 monitor-replay harness over `corpus/m1`-`m8`, three
nulls with their reasons, and the honest finding that benign `corpus/m5` (1.214 faults/turn) scores
above two labelled thrash traces — fault counts are not a pathology proxy, and the corpus has no
safety labels to measure against.

**Next frontier 8 (W8 prereg landed; status 2026-11-01):** owner ratifies the freeze +
names the model/price row + climbs the implementation-card gate (ctxvm context-engine
plugin + hermes `post_api_request` usage wiring + `tools/dq-secret-scan.py` + frozen
task texts/checkers) → owner-run W8 capture (D5 language) → the W8 analysis card with
the M0 table (result reopens D5+D7 per the D5 text) → D3-c exporter promotion (with
drift guard) → W12 Steps 2+ (post-W8) → W9 umpire-quality items (the CROSS-MACHINE
determinism check; the W10 riders) as parallel follow-ups.
**CI-2 (2026-11-01, `reports/RR-CIDIAG-20261101.md`):** the W8-prereg push run
`41286052160` @ `849dc1e` failed the ts job ONLY (step 6, `node --test test/`,
"Process completed with exit code 1", no test name in annotations; logs admin-gated)
while the local mirror was green — and the step passes on every nearby environment:
this host v26.10.0, the latest release v26.13.0, docker `ubuntu:26.04` AND
`ubuntu:26.10` (all 20/20 on a pristine clone). The run's annotations carry the
`ubuntu-latest` → Ubuntu 26 migration notice (`actions/runner-images#14748`),
so the red is classified RUNNER-LOCKED, unresolved; nothing in the packages is
environment-sensitive (no `process.env` except `CTXVM_TRACE_TS`). Landed: ci.yml
step 6 self-records `os-release`/`node --version`/`npm --version` inside the step
(exit code still owned by `node --test`); rehearsal green after the edit. The
owner-side dispositive: re-run failed jobs on `41286052160` (transient ⇒ green
with the new env lines on record) or paste the step-6 tail so the mirror can be
fixed precisely.
**CI-2 OUTCOME (same day):** run `41290419904` @ `14d7c38` (my CI-2 push)
**completed success** — identical content green hours after the red; the
failure stays classified runner-locked (not reproducible anywhere reachable
from this machine), the env-echo stays in the workflow for any future red,
and no owner log is needed to close it.
**D6/W10 NAMING EVIDENCE (2026-11-01, `reports/RR-NAMING-20261101.md`):** registry
availabilities observed read-only — `ctxvm`/`xcabi` FREE on npm-unscoped/PyPI/crates
(the crates API 403s without its required UA header; observed then retried) and the
planned crate names free; `umpire` TAKEN on all three (none an agent project — cosmetic
collision, a standalone distribution needs a distinguishing identity); `@ctxvm/*`
scoped 404s are NOT decidable (no pre-reservation; the scope belongs to the first
publish under it — a publication-ordering fact for D6) and the PyPI reserved-names
caveat stands. The web/domain collision pass could not run (the search integration
errored this session) ⇒ stands UNVERIFIED-2026-11-01. Evidence only: D6 stays the
owner's decision.
**W10 RIDER CLOSED — ENGINES FLOOR (2026-11-01, `reports/RR-NODEFLOOR-20261101.md`):**
real older-node binaries (nodejs.org dist tarballs) verified what the W10 build card
could not: the pinned `engines >=22.6.0` floor is REAL for sources — the ts suite
passes 20/20 on node v22.6.0 with the explicit `--experimental-strip-types` flag and
FILE args (`--test test/tracer.test.ts`); the repo's directory-arg invocation
`node --test test/` FAILS at 22.6.0 with `ERR_MODULE_NOT_FOUND` (an invocation-surface
fact, not an artifact defect — no consumer of the published package ever runs
`node --test`). The DIST ARTIFACT runs LOWER: a dist-only consumer (import
`dist/index.js`, one echo trace, `CTXVM_TRACE_TS=0`) is byte-identical across node
20.20.2 / 22.6.0 (flagged) / 26.13.0 — sha256 `40a9618f60bd…` all three; node 20 has
NO type-stripping at all, so the shipped JS needs none: the artifact's true floor is
BELOW the pin (node 20 LTS observed green). `engines` UNCHANGED (publish-adjacent,
D6 discipline) — the lowering candidate is a publish-time package-metadata decision.
Equality claim scoped to the observed trace shape; nothing below node 20 measured;
one build, three consumers (no rebuild-on-each-node claim).
**NPM SCOPE MECHANICS PINNED + one RR-NAMING finding corrected (2026-11-01,
`reports/RR-SCOPEMECH-20261101.md`):** the naming card's `UNVERIFIED-2026-11-01`
gates land. Pinned (three npm-doc fetches, the pages' footer edit dates recorded):
a scope name is granted "when you sign up for an npm user account or create an
organization" — the namespace claim act is ACCOUNT/ORG CREATION, not first
publish (the naming card's "the scope belongs to the first publish under it" is
corrected on this detail; its availability verdict and discipline are unchanged
— creating the account IS the ownership act, so scoped availability is still
not decidable anonymously); org creation is FREE under the "Unlimited public
packages" plan and "Your organization name will also be your organization
scope"; scoped packages are private by default — public visibility needs
`npm publish --access public`. D6 implication refined: at publish time, create
the free org/user named `ctxvm` promptly (owner action; nothing created or
reserved by me). The LOG carries the same supersession; the W10 board row is
deliberately untouched (its "npm scope `@ctxvm` UNVERIFIED (org page 403)"
note stays exactly true).
**PLUGIN IDENTITY AT CREATION (2026-11-02, `reports/RR-PLUGIN-ID-20261102.md`):**
the default-ON lane's `provider: unknown` closed as far as hooks allow. Source-pinned
gap: the turn-prep `pre_llm_call` payload carries `model`/`platform` but NO provider
(`packages/hermes/HOOKS.md` §1, v0.22.5), and `provider` only reaches the
`pre_api_request`/`post_api_request` payloads after the tracer exists — identity is
stamped ONCE (it rides `session.open` + every `call.meta`; write-through persists per
event), so the NO-BACKFILL law is now written into `09-plugin-parity.md` §5.1. Landed:
the identity priority chain **payload > plugin settings > env > unknown** — the middle
layer reads the host-owned plugin settings subtree (`ctx.get_config`,
`plugins.entries.<id>.settings.model`/`.provider`) at register(), fail-open in every
hostile ctx shape; `PLUGIN_VERSION`+manifest → 0.4.1; hermes suite 97→**101 pass**
(2 new tests) in a CTXVM-clean shell, ALL GATES GREEN. Two install defects fixed by
the §6 re-install DoD: the installed `plugin.py` was one refactor BEHIND (missing the
whole W13 block — the previous sync updated the wrapper only; a restart would have
no-op'd the W13 prefix silently) and the installed dir lacked a root `plugin.yaml`
(loader contract, `plugins.py:7`); after the full re-sync (hashes equal) `hermes
plugins doctor` passes (manifest 0.4.1, 6 hooks). The stale `live/` sub-copy inside
the installed dir was left for an owner look. Live proof of the settings source and
of the W13 prefix still ride the SAME owner-side act: a gateway restart.
**PROCESS NOTE (books law):** this session's tool shell carries the full `CTXVM_*`
capture family (`CTXVM_TRACE_TS=0` included); pytest swallowed that at import time
and produced 4 phantom failures — gates must run in a CTXVM-clean shell
(`env | grep ^CTXVM` first; unset, then `tools/run-ci.sh`).
**D3-C EXPORTER PROMOTION LANDED (2026-11-08, `reports/RR-D3COTEL-20261108.md`) — the
OTLP projection is a supported surface.** The last un-gated branch of frontier 8's
chain (the W8-analysis card is moot: W8 closed FAILED 2026-11-07; W12 is D7-held; the
books' "owner calls on … D3-c + W12 order" resolved by the owner in-session). D3-c
"layered" stands as decided — JSONL canonical, exporter a declared lossy projection,
mapping semantics UNCHANGED from the audited W6 prototype: CLI outputs byte-identical
(13/14/17/10 spans on m1/m6/m7/m8 reproduced; scope string stays `"0.1.0-prototype"`;
D12 law honored — the est branches stay keyed on `cacheEstimate.providerReported`, the
R3 `providerUsage` receipt is DECLARED DROPPED, not consumed; a providerUsage-carrying
frozen input joins the goldens). The rider's drift guard is mechanical: EXPORT_SPEC
consumed/dropped tables per event type (+ global `ts` drop) kept in sync with the
RFC-0.1 schema's flattened field set by `tools/otel-export.test.mjs` (4 tests green:
sync/golden/structure/determinism+CLI; three red-before probes recorded — phantom
declaration, undeclared field, golden drift — each exit 1 with the assertion named;
logs `/tmp/opencode/otel/red-{a,b,c}.log`). Five golden OTLP/JSON projections over
frozen byte-inputs (the four W6-audited corpus traces + the ai-sdk `echo-thrash`
v0.1 fixture with its tracer-vs-provider est disagreement), 124,319 B total. The TS
gate gains the step (run-ci + ci.yml mirrored, ts job). TWO MIRROR-LAW DEFECTS
found by verification and fixed in the same card: ci.yml never had the
`@ctxvm/ai-sdk` TEST step (run-ci has run the suite since T15 B3 `801047c` —
Actions never exercised ai-sdk tests) and never had the
`packages/node/LICENSE` cmp step (run-ci's since the W10 build `72360f1`; the
W10BUILD-CI claim missed it) — both steps now in the ts job with the finding in the
step name; workflow parse asserts presence (ts steps 17). AGENTS.md §9 refreshed
from the books as the rider (its own "keep this section current" duty). Gate:
ALL GATES GREEN exit 0 under the nine-key chain on the final tree (first gate run
to exercise exporter guard + both mirror fixes; the Actions equivalent lands with
the owner's next push).
**PUSH WITNESS E7BF6FF (2026-11-08, run 42468046847 = run №90, completed success in
52 s, 09:38:35–09:39:27Z, all four jobs green):** the first Actions execution of ALL
THREE steps this card added — "@ctxvm/ai-sdk tests" (the suite Actions has silently
skipped since T15 B3 `801047c`) passed, "packages/node/LICENSE must match ..." passed
(absent since the W10 build `72360f1`), and "otel-export drift guard (D3-c
promotion: EXPORT_SPEC vs schema + golden bytes + OTLP structure + CLI)" passed —
so the D3-c surface is CI-proven on the hosted side, the two mirror fixes hold on
`ubuntu-latest`, and every job (hub rust ts schema, 4/4) is green at HEAD
`e7bf6ff`. Jobs evidence retained in `/tmp/opencode/otel/run90-jobs.json`.
**Next frontier 9 (D3-c landed; status 2026-11-08):** every agent-buildable card on
the books is now landed or closed; remaining work is owner-gated — W8 reopen (D16 +
the §12 amended conditions), W12 Steps 2+ (D7), publication (D17), the white-paper
lane's D13/D14 absorb — and the reviewer round: P1 answered (DIFFNORM), P2/P3
pending owner answers (`handoff/QUESTIONS.md`), then any resulting cards; W9
umpire-side quality items (cross-machine determinism; the W10 riders closed 2026-11-01)
run in the umpire repo on owner coordination.

**PUSH WITNESS CD43555 (2026-11-09, run 42589188792 = run №94, push event at head `cd43555`,
completed success in 37 s, 08:53:14–08:53:51Z, all four jobs green — hub 9 s, schema 12 s,
rust 28 s, ts 33 s):** the first hosted execution of the P3 stack — the Packet-3 answer card
`ae46b63` (D14 recorded; release rule bound at D6; redaction card authored proposal-only,
sidecar-first) and the placement follow-through `cd43555` (card of record
`design/redaction-block.md`, owner-cleared) — plus the P2 close-out kit bytes `2761acc` carried in
the same fast-forward (lineage through `e1281bd`, run №93's head). Facts from the hosted runs+jobs
API; the kit did not change between push and witness. Logged `RR-PUSHP3-20261109` under the echo
law as witnessed AND recorded (the stack carries real cards, not a books-echo).
**Next frontier 10 (P3 landed + run №94 witnessed; status 2026-11-09):** the reviewer round is
closed on the kit side — P1 (D13; `design/diff-normalisation.md`), P2 (demo keeps; `identifier_scan`
cause located), P3 (D14; release rule bound at D6; `design/redaction-block.md`) are answered,
recorded, and hosted-green at `cd43555`; the reviewer queue in turn does NOT stay empty — the adoption lane has
queued the next batch, P4 (umpire `ts`: consumer rule vs additive mandate), P5 (calibration
transfer, n=180), P6 (determinism scope: same-build vs cross-machine), P7 (baselines: embedding-NN
and friends) — pending owner paste (packet files exist; `handoff/QUESTIONS.md` rows not yet
written). What remains beyond it consumes no reviewer answer: owner
ratification of D13 + D14 and the §4-LIST release rule (first-run-notice minimum) at D6/D17; routing the white-paper bundle (Pillar-1 split; `:635` echo sweep; the P2 sentence at `:333`/`:339`
with the `identifier_scan` cause; the R1 3-to-0 contrast; the consent-paragraph replacement at
`white-paper.md:620–623` + the index twin + Part II `:368`; Part II's card-citation rule) to the
white-paper lane's working tree; then the owner gates D16 (W8 reopen) and D17 (publication); the
adoption lane (A1–A6) continues per adoption prompt §4; W9 umpire-side quality items on owner
coordination.

**Frontier 10 addendum (2026-11-09, P4 answered):** Packet P4 is answered and recorded — verdict
(a)+(c): umpire `ts` stays optional; the one-clause ordering rule (line order governs; absent
`ts` = unknown, never zero; no cross-ledger order) is DRAFTED PROPOSAL-ONLY for
`umpire/00-SPEC.md` §2 in `reports/RR-P4TS-20261109.md`, awaiting owner approval + fresh
D-number; (b) refused on D9 + 0.1/v0 grounds verified in the card (the freeze's zero-`ts` corpus
is the mechanism). No 5-touchpoint card. Remaining reviewer queue: P5 (D-U1 calibration
transfer), P6 (D-U3 determinism scope), P7 (D-U2 baselines) — pastes pending. The AGENT-PROMPT
§1 session-state block predates `227beb0` and needs its one-line refresh at the next policy
touch (proposed, not edited).

**Frontier 10 addendum 2 (2026-11-10, P5 answered):** D-U1 resolved in kit form per
`reports/RR-P5CAL-20261110.md` — publish per-corpus calibration WITH the caveat; NO transfer
claim until a preregistered equivalence test on ≥5 held-out new label sets (±2 pt margin,
Brier/log-loss primary, cluster bootstrap, sizing n ≈ 180×(h/2)²). Point estimates worsened on
transfer scopes (A1 7.5→12.2, A2 4.9→6.8 ECE, `RR-W9TRANSFER-20261101:136`). The caller
sentence is a PROPOSAL for the calibrated-confidence surface (owner-gated, P4 pattern).
Remaining reviewer queue: P6 (D-U3 determinism scope), P7 (D-U2 baselines); P8 stays queued
owner-flagged. AGENT-PROMPT §1 is now ~5 commits stale (proposal outstanding).

**Frontier 10 addendum 3 (2026-11-10, P6 answered):** D-U3 resolved in kit form per
`reports/RR-P6DET-20261110.md` — verdict = register option (a): keep the replay claim
same-build, TIGHTEN the vocabulary to "replay-reproducible with 10 documented exceptions"
("deterministic" unavailable even same-build at 470/480; the ten classify at a quiescent
(concurrency-1) recapture before stronger wording; page-table-only softening refused for umpire
— the split is identity 480/480 + strict output 470/480). Cross-machine only after a
preregistered matrix (pinned image+weights, ≥2 hardware configs, OS variation, hash
seed/threads/concurrency axes, full 480 per config); cross-build reports identity only. Serving
is local-only by T14/D-U4. The claim-today sentence is a PROPOSAL (owner-gated). Remaining
reviewer queue: P7 (D-U2 baselines); P8 owner-flagged.

**Frontier 10 addendum 4 (2026-11-10, P7 answered + P6 erratum):** D-U2 resolved in kit form per
`reports/RR-P7BASE-20261110.md` — two zero-spend baselines FIRST (majority-class + logistic-on-
embeddings for the accuracy AND calibration claims; zero-shot embedding similarity for the
caller-labels claim — a fixed-label classifier cannot take a new label set), stronger model only
before a product claim WITH a spend packet, fine-tuned deferred; the same-split protocol (same
**240 fit / 120 calibration / 120 test** rows of the 480-row 4-label corpus — reviewer UNKNOWNs
resolved: `RR-M2V2` "240/120/120 split, test n=120") with preregistered margins (~8-point
half-width at n=120; <5-point differences unresolvable). Positioning flips preregistered as
PROPOSALS (ledger-layer vs accuracy-case vs "cheap and local", logistic-ECE ≤ 0.0302 triggers
the calibration wording's own recalibration). ERRATUM: the committed P6 card's Limitations were
wrong — the quiescent concurrency-1 recapture exists (`RR-M3V3-20261024`: **capture-time-
concurrency attribution CONFIRMED**; ten rows = documented capture-side exceptions at 5/4/1
splits) — Roadmap U4 ticks, P6's falsifier stands resolved recapture-clean; erratum recorded as
appended blocks, no committed text rewritten. Remaining reviewer queue: P8 owner-flagged.

**Frontier 11 addendum 5 (2026-11-11, umpire gates run):** the umpire↔xCABI friction list was
verified against the books and the gates re-run (umpire `validate_ledger.py` PASS 130 checks,
negatives 14/14; ctxvm replay of the ab-demo ledger 6 events / 0 divergences / 0 violations; the
SEALED v0 validator rejects the same ledger's four v0.1 lines while the v0.1 validator accepts it;
`check-handoff.sh` + three pastes green). Result: F1/F2/F3/F4/F5/F6/F7 closed (F2's norm for `seed`
is umpire's 00-SPEC, not RFC-0.1 — R2 names `model_pin` only; F4 was missing from the pasted list);
F8 is P4-answered (awaiting ratification); F9 is accepted but its documentation line has NO packet
and no owner. The one open item is the flat-vs-nested `page.id` asymmetry — REAL, inherited from
sealed v0 (`spec/rfc-0/RFC-0-xCABI.md:61-62`), absent from the friction card, and its "second
consumer" trigger has ALREADY fired: umpire's Python (`ledger_tools.py:85`,
`validate_ledger.py:228`) and ctxvm's own OTLP exporter (`tools/otel-export.mjs:72-73` nested vs
`:86/:96/:106/:116/:125` flat) both branch. Packet **P10** cut and registered (queued); the agent's
recommendation is (a)/(b) over (c) because an additive declare-side field would make EVERY declare
line invalid for strict v0 consumers. Card `reports/RR-UGATE-20261111.md`; ruling is owner-gated
(D-number in the umpire register). Remaining reviewer queue: P8 owner-flagged; P10 queued.

**Frontier 11 addendum 6 (2026-11-11, after the push):** the push landed (remote `main` == local HEAD
`63472f4`) and the full CI was re-run at that HEAD with the env-correct invocation → **ALL GATES
GREEN** (rust; node build parity — 16 events byte-identical; TS 22+62+46; python 187+8+66;
benchmarks/metrics; `SCHEMA CONFORMANCE: PASS (682 checks)`; export round-trip; hub byte-identity).
The umpire MCP surface was re-checked: `health` → connection refused (the pinned server listens on
127.0.0.1:8081 and is not running — `ss`/`pgrep` agree), while `pins` and `calibration_info` answer.
**NEW finding:** the MCP's default calibration artifact is the SUPERSEDED v2 map
(`cal-v1:aceb881587b3b3a6`, test ECE 0.026684) — not the v3 map of record
(`cal-v1:057a5a35a9d4ec71`, ECE 0.030163, `RR-M3V3`) — and the two are not one map under two labels
(`isotonic.points`, `raw_sha256`, `provenance.git_head`, `selection` and the test metrics all differ).
The default is injected by the launcher (`mcp_server.py:54` has none): the hermes gateway config sets
`UMPIRE_CALIBRATION=…/umpire-cal-v2.json` (`~/.hermes/config.yaml:2114` + the arm profile copy
`:2115`), so the MCP as configured cannot reproduce the calibration of record. Fix = one config line
+ gateway restart; NOT done here (hermes lane's machine config; the umpire repo is read-only from
this lane) — board item U6, owner-routed. F9's ownership gap is closed by packet **P11** (canonical
ordering; queued; the crux: `ts`-last vs sorted keys differ by construction, so "both accepted" is
the only honest rule). Friction points use the F-series from now on — never an R-number. Remaining
reviewer queue: P8 owner-flagged; P10 + P11 queued.

**Frontier 11 addendum 7 (2026-11-11, the 16 KB paste budget):** `session-start.sh 8 --with-context`
reported OVER 16 KB (16,617 > 16,384). Diagnosis: `session-start.sh` takes the PACKET NUMBER as its
argument, so "8" assembles P8's paste — nothing was sent to the reviewer, and P8's drop-or-keep
ruling is still the owner's. The defect was wider than P8: with PROJECT-STATE 6,137 B + CONTEXT-PACK
7,417 B, only 2,826 B remained for the packet, and P8 (3,059), P10 (3,045) and P11 (3,048) all
exceeded it — every one of their with-context pastes was over budget. Fixed per the tool's own
instruction (glossary rows / excerpt lines / label rows, never a heading): CONTEXT-PACK 7,417 →
**6,837 B** (-580; the `trace` and `touch ratio` glossary rows dropped — both still defined in the
repo — plus citation trims across §1/§2/§3/§8). Re-measured: all 11 packets' with-context pastes
fit, worst **P8 = 16,037 B** (347 B spare); the worst theoretical case (PROJECT at its 6,144 cap + a
3,072 packet) is 16,057 B, so the budget holds for anything the checker accepts; checker ALL PASS and
the three standing pastes exit 0. Card `reports/RR-CTXPACK-20261111.md`.

**Frontier 11 addendum 8 (2026-11-11, kit cap repaired):** the w8b lane's commit `ada48de` added a
**549 B** line to `handoff/PROJECT-STATE.md` as a FOURTH item of the "Done (last 3 items)" window,
taking the file to **6,686 B > 6,144 B** and turning `check-handoff.sh` RED; the background watcher
surfaced it two minutes after the landing. Repaired by this lane (the cap is a shared law and the kit
was red): the w8b line compacted to a pointer that keeps every finding id
(RR-W8CACHE/NOOPBYTES/SIM/GRID + RR-SPEND-RECON2), the P9 = A answer and the closure card
`design/W8-CLOSURE-20261110.md` — the narrative stays in that lane's own card and LOG rows, so no
fact was dropped — and the window restored to its 3-item contract (w8b close-out, paste-budget
repair, umpire-residue sweep; this lane's umpire-gates line rotated out with its locator intact).
**6,123/6,144 B, checker ALL PASS, three pastes exit 0.** Pre-repair snapshot in
`/tmp/opencode/20261111/kitcap/`. Standing rule added to the lane prompt: any lane writing
PROJECT-STATE must re-run `check-handoff.sh` BEFORE committing — 21 B of headroom is thin, and a
long index line turns the whole kit red. Card `reports/RR-KITCAP-20261111.md`.

**Frontier 11 addendum 9 (2026-11-11, second CONTEXT-PACK cut):** the owner's paste of the tool's
cut instruction ("cut from CONTEXT-PACK (largest part, 6837 bytes)") pins the overflow's
arithmetic: that error came from a run AFTER the first trim but BEFORE the PROJECT-STATE repair,
i.e. while the w8b lane's 549 B line was still in the file — 6,686 + 6,837 + 3,059 + 4 = **16,586 B
> 16,384** (over by 202), CONTEXT-PACK correctly named the largest part. Both terms are now fixed.
Second trim (glossary rows / excerpt lines / label rows, never a heading): CONTEXT-PACK 6,837 →
**6,440 B** (-397; heading set byte-identical, 9 = 9) — the `fault recall` glossary row dropped
(its formula is §4's `metrics.py:159`, the `refetch_rate` successor §4's `:146`), the `protected
floor` row shortened, §4's `thrash_index` excerpt lost a path but kept its rule + locator, §8's
W8-vocabulary row lost the arm-witness clause, plus citation trims in §1/§3/§6; no fact left the
file that is not in the repo or a sibling section. Re-measured: every packet's with-context paste
≤ **15,626 B** (P8; 758 B spare), worst theoretical case 15,660 B; arithmetic now 16,384 − 6,123 −
6,440 − 4 = 3,817 B for the packet against a 3,072 B cap, so ANY packet the checker accepts fits.
Checker ALL PASS; the three standing pastes exit 0. Both overflows had one shape: a shared file
grew inside the kit's caps and the paste budget (a paste rule, not a checker rule) absorbed it until
it did not — the kit checker never flagged it, `session-start.sh` did, and the owner felt it first.
Card `reports/RR-CTXPACK2-20261111.md`.

**Frontier 11 addendum 10 (2026-11-11, packet P8 answered):** the reviewer's cache-stable-selection
answer (packet-only, one assumption) is recorded in `reports/RR-P8CACHE-20261111.md`. The RANKING is
adopted — bounding residency and keeping the prefix cache cannot both hold per call; watermark
compaction (evict once on a trigger, hold) is the candidate and is already the in-tree design
(`design/w8-cache-stable-selection.md` §3 parts 2–4) with a four-condition acceptance gate; (c) cannot
bound residency (the keep law protects first-3 + last-6 turns, so on a one-turn session the floor IS
the request). TWO NUMBERS CORRECTED from the books: **w/r = 10.0, not 12.5** (the owner's catalogue
row-013: GPT-6 Luna $0.10 in / $0.50 out / $0.01 cached read, no cache-write row — writes bill at
input; the card's decomposition reproduces both reported costs to the dollar) so the reviewer's
62/25/125 calls become 50/20/100; and the **evictable share is 5.3 % session-weighted** (25,404 of
479,076 request tokens, `RR-W8SIM` §2 — the reviewer's 12 % is the last-request quantity, which the
books reconcile), giving break-even **n\* ≈ 189 calls** against 5–30 measured calls. **DECISION-
RELEVANT FINDING the packet could not see: (d)'s "no worse than control" guarantee is already
falsified** — the books MEASURED the no-op arm (9 selections, 0 evictions) at **$0.0765 vs naive
$0.0175 = 4.4×** (`RR-NOOP-20261109`); the driver is session growth plus output volume (6.5× the
output), not selection, so (d) may gate a COMPACTION but cannot promise control-cost. The packet's
internal inconsistency is resolved: the no-op IS byte-identical (`RR-W8NOOPBYTES`, three cases pass),
so churn is the growing SESSION under the keep law; the cache-write cause stays UNKNOWN
(`RR-W8CACHE` H3). Q2's five-condition metric-replacement rule is ADOPTED as a standing lane rule
(symmetry test included; existing cells stay under tokens; no cost-saving claim, law 7). **Q3 was
already executed a day earlier**: `design/W8-CLOSURE-20261110.md` (owner Option A, packet P9) closed
W8 negative with no further paid cells; the replacement run is `design/W8B-FREE-PLAN.md`. The
compaction engine does NOT exist yet (`selectionMode` appears only in the design card). No paid
cache-stable cell is justified by the books' numbers as they stand — the next step is owner-routed.

**Frontier 11 addendum 11 (2026-11-11, erratum on the P8 card):** the replacement run that card
named as the live next step HAS NOW RUN and produced **NO RECORD** — `RR-W8B2-20261111` (commit
`9ddbf31`): both arms NO RECORD on `nous/longcat-2.5:free`, prompt 1 TIMEOUT after 120 s, no capture
flushed, $0.0000, 0 calls, wall 123 s / 125 s; preflight green, `[-t file]` surface pinned, budget
70,000 from settings, 20-part fixture intact, runner timeout path verified. Their card's rule —
"nothing goes in the denominator — no paging, eviction or artefact claim" — matches the discipline
this lane's P8 card adopted from the design card. **No P8 verdict changes** (ranking, w/r = 10, the
5.3 % evictable share, n\* ≈ 189 calls, the (d) amendment, the Q2 rule, Q3-executed all stand). What
changes: the blocker is now a MODEL-SIDE TIMEOUT, and the owner must choose an alternative subject
(stepfun fallback, nvidia, or accept longcat is too slow for the 120 s cap) with both arms on prompt
v2. Recorded as an appended erratum block on `reports/RR-P8CACHE-20261111.md` — no new LOG row
(errata are blocks; the card already has its row) and no PROJECT-STATE rotation (no new card).

**Frontier 11 addendum 12 (2026-11-11, packet P9 confirmed):** the reviewer's P9 answer is **A — an
independent confirmation**, not a new decision; the closure (`design/W8-CLOSURE-20261110.md`, owner
Option A) stands. Their four closure-text corrections were checked against the artefacts rather than
applied on trust: **(1)** the closure ALREADY complies — item 5 says the extra cache writes are not
explained by the engine's message list (append-only, byte-constant system prompt, byte-identical
no-op) with cause UNKNOWN, the not-claimed list ends with "A cause for the cache-write volume", and
the file carries no "forfeits the cache" phrasing; the stale "the paged arm rewrote the prefix 14
times" lives in `design/w8-cache-stable-selection.md` §1 + its LOG row — **another lane's plan of
record, so ROUTED to its owner as an appended erratum, not edited here**; **(2)** the zero-spend
narrowing was ALREADY run and returned NOT-TESTABLE for a stated reason: the provider export is a
per-day/per-key AGGREGATE (17 rows; no per-request rows, no timestamps), the call gaps are ~18 s
(09:43:34 → 09:47:07 for 29 requests) and the cache lifetime is UNVERIFIED ⇒ H1 NOT SUPPORTED, H2 NOT
TESTABLE, **H3 UNKNOWN cause** (candidates: provider accounting; session boundaries); **(3)** keep
the closure's three-part cap wording (billed >= $7.14 / store estimate $9.16 / true total UNKNOWN —
"at least $9.16" would promote an estimate to a floor; the 11-07 and 11-09 exports are still
missing); **(4)** the closure already states the weaker claim. Their UNKNOWN answered from the
books: the free replacement run (unpaid models, no cache price, descriptive only) is NOT a
substitute for a longer-session paid variant, which would need n\* ≈ 189 calls (≈ 43 even at the free
plan's 23 %-of-peak middle) against a 14–29 call session, plus the lifetime sourced and per-request
cache attribution recorded — and the free run produced NO RECORD (`RR-W8B2-20261111`, timeout at
120 s, $0.0000). Card `reports/RR-P9CLOSE-20261111.md`.

**Frontier 11 addendum 13 (2026-11-11, packet P10 answered):** the reviewer's page-id ruling is
**(b) + (a) — ONE RFC-0.1 compatibility-note line stating the type-dispatch rule, plus prose docs, and
NO field** (sealed v0 data keeps both shapes forever; a field would add a third). The rule is verified
WORD FOR WORD against both schemas: sealed v0's `page.declare.page` -> `$defs/pageRef` = `{id:
pageId{logicalRef,contentHash}, kind, tokens}` (nested) while `page.render`/`page.evict`/`page.fault`/
`page.pin`/`page.unpin` -> `$defs/pageId` = `{logicalRef,contentHash}` (flat); RFC-0.1 keeps the same
`$defs` and the same nine verbs; no verb carries both shapes. The "never sniff fields" clause is what
both in-repo consumers already do (the ai-sdk resume-brief dispatches on `event.type` before reading
the flat shape; umpire's `ledger_tools.py:85` dispatches on the verb — though umpire's branch is
profile-specific, so the note must state the general rule). **Two of three reviewer UNKNOWNs
resolved from the books:** `schemaVersion` is on the `session.open` line ONLY and optional
(`RFC-0.1-xCABI.md:8`), so their "if every v0.1 line carried schemaVersion" premise is false; the
note needs a **D-number** (RFC-0.1: "Applied (D4 approved 2026-10-30)") and can land as a **NEW file
under `spec/rfc-0.1/`** (that document's scope: "new files under `spec/rfc-0.1/` only" — neither the
sealed RFC-0 nor the existing RFC text is touched); a conformance vector is a **fixture**
(`rust/crates/ctxvm-conformance/vectors/`), not a spec edit. Still open: a v0-only consumer outside
these repos. **ERRATUM** on this lane's own framing: the blast-radius argument for an additive field
was overstated (a strict v0 consumer already rejects a v0.1 trace at its `session.open` line — measured,
4 failures on the ab-demo fixture); the marginal costs are (i) every v0.1-aware consumer must be
updated, (ii) two identity sources per line, (iii) a consistency rule between them. The ruling is
unchanged. Falsifiers adopted verbatim. Not done, owner-gated: the note file, the D-number, and the
vector (one line per shape plus a NEGATIVE — a `page.declare` carrying a flat `page.logicalRef`, which
a sniffing reader would accept and the validator must reject). No spec, schema or vector byte was
written. Card `reports/RR-P10ID-20261111.md`.

**Frontier 11 addendum 14 (2026-11-11, correction to addendum 11):** the w8b lane's own erratum to
their W8B2 card (`reports/RR-W8B2-ERRATUM-20261111.md`, in flight) corrects a figure **this lane**
quoted in addendum 11 and in the P8 erratum block: "**0 calls**" is FALSE. The profile stores say
naive 9 API calls / 31 messages / 21 tool calls, paged 5 / 17 / 11 (a third session 2), each session
~4 minutes long (13:02:46 -> 13:06:26 and 13:04:49 -> 13:09:19) and ending
`end_reason = ws_orphan_reap` — the gateway reaped them because the driver killed the CLI. So the arms
RAN, the model answered, the driver's 120 s per-prompt cap cut them mid-turn, and the capture never
flushed (a killed session is never closed). The OUTCOME (both arms NO RECORD, nothing in the
denominator) stands; the CAUSE is a task-and-cap failure with a WORKING model, and the deeper blocker
is the task's counting questions — `read_file` reports `total_lines` and `file_size` only, so T-A's
per-line byte counts cannot be read off the tool, while the extractive control question (same fixture,
profile, model, tool) completes in 4 s with 2 tool calls. Their lane has landed the fixes (SIGTERM
first so a timeout flushes; a `--limit N` smoke check; `max_turns` 12 -> 6; prompt rules;
`--expect-budget any`; verified 1 tool call instead of 21 with `--limit 1`), so the W8 thread's next
step is now CONCRETE — rewrite the questions to the values the tool reports — rather than abstract.
**No P8 verdict changes** (ranking, w/r = 10, the 5.3% evictable share, n\* ~ 189 calls, the (d)
amendment, the Q2 rule, Q3-executed — none depends on the W8B2 call count). The committed LOG row
never claimed "0 calls", so no committed row needs an erratum. Card `reports/RR-W8B2CORR-20261111.md`.

**Frontier 11 addendum 15 (2026-11-11, packet P11 answered):** the canonical-ordering ruling stands —
**(c) as the owner, with (a) as a short POINTER — and the ORDER is test-first**: write the
conformance test, then the note can state a fact the test enforces (F9 is otherwise a claim nobody can
falsify). The test belongs to ctxvm (its replay makes the acceptance claim; umpire's 00-SPEC may
mention it but cannot own it) and asserts, in order of strength, equal parsed model -> equal page table
-> equal replay report (incl. divergences and violations), NEVER equal bytes, with a trace WITH `ts` and
one WITHOUT (the sorted form puts `ts` before `type`), plus a numeric case — in BOTH places: a vector
pair with the expected report in `rust/crates/ctxvm-conformance/vectors/` and a Rust unit test that
parses the pair. The note's line is a COMPATIBILITY STATEMENT ONLY (verbatim: "Key order within an event
is not significant to parsing or replay … the codec remains strict about unknown fields"). Two of the
reviewer's UNKNOWNs resolved: `events-v0-1.jsonl` carries `ts` on 6 lines (the v0 and session vectors
carry none) and a vector is a FIXTURE, not a spec edit; the note's route is a D-number (RFC-0.1:
"Applied (D4 approved 2026-10-30)") and a NEW file under `spec/rfc-0.1/` (its scope: "new files under
`spec/rfc-0.1/` only"), bundling the P10 type-dispatch line and this line as two lines under one
D-number. **One premise corrected:** a TS-to-Python byte comparison DOES exist (`RR-W7-20261029.md` §4:
17 records, mismatches=0) with the scope caveats "ASCII-only …, floats banned" and the verdict
"byte-compatible, NOT an independent implementation" — and the hash-input inference is narrowed
(content hashes hash the content string; only the ref's truncation digest is over canonical JSON).
**TWO DIVERGENCES MEASURED TODAY, so the reviewer's third falsifier is TRIGGERED:** umpire's Python
canonical_json vs ctxvm's TS canonicalJson agree on ascii, non-ASCII values and nested keys, but
DIFFER on astral-plane KEY names (Python sorts by code point, JS's default sort by UTF-16 code unit) and
on number text forms in four of six cases (1.0 vs 1; 1e+16 vs 10000000000000000; 1e-07 vs 1e-7; big
ints past 2^53 lose precision in JS). Since umpire's ref digest IS a digest over serialised bytes, the
note needs a normative canonical form FOR HASH INPUTS ONLY — "byte-for-byte across languages" is not
satisfiable as stated. Duplicate keys measured: the v0.1 validator accepts them (exit 0) and no
duplicate-key check exists in the codec or either validator (last value wins in all three parsers -
uniform by accident, specified nowhere). No spec, schema or vector byte was written. Card
`reports/RR-P11CANON-20261111.md`.

**Frontier 11 addendum 16 (2026-11-11, late additions):** the P11 conformance pair is DRAFTED in
`reports/RR-P11CANON-20261111.md` §9 — the exact generator for the sorted twin, the first three lines
of the new vector file (`ts` before `type`, the discriminating case) and the Rust test sketch (equal
parsed model -> equal page table -> equal replay report; never equal bytes) — because the existing
`events-v0-1.jsonl` is already struct-ordered and umpire's ledger is sorted-ordered (both byte forms
exist, never of the same trace), and the vectors are compiled in with `include_str!`, so a pair is ONE
new file plus ONE test. **No vector or test byte was written; the owner's (c) is the only step.** The
lane prompt now also carries the COLD-START path (the session is not the memory; the kit is) and the
environment dependencies that do not survive a reboot (the pinned model server on 8081 is the owner's
to start; the watcher is per-session).

**Frontier 11 addendum 17 (2026-11-11, while T-A runs):** the owner asked what they have to decide.
**One time-sensitive call — diagnostic or cell.** If it is a probe/smoke, keep it labelled a
diagnostic: it cannot enter any denominator (the free plan's section 5 claim ceiling; P9: "any new
test is a fresh preregistration, not W8"; law 7). If it is a Phase 2 pair, **their own gate says it
must not start yet**: `reports/W8-SPEND.md` section Prediction ("A cell does not start until this block
is filled, committed, and matches the verifier afterwards") is still **unfilled placeholders**, with no
filled instance in the file — so fill and commit it before the result is read, or record no cell as
measured. **Not the owner's call today:** what the result may claim (already capped by section 5) —
plus two review-side guardrails: an unpaid-model run has no cache price and so cannot speak to cache
economics (the cache-write cause stays H3 unknown-cause), and a PAID cell on this shape cannot pay
back (n\* ~ 43 calls at the plan's 23%-of-peak middle, ~ 189 at W8's measured 5.3%, against a 14-29
call session) — so do not buy one without resizing the session, which is a fresh preregistration.
**Outcome-triggered, not now:** the subject choice (stepfun fallback / nvidia / accept longcat too
slow for the 120 s cap). T-A v2 is a different task shape, so the W8 closure stands untouched and its
cells cannot be compared with W8's numbers. Card `reports/RR-TADEC-20261111.md`.

**Frontier 11 addendum 18 (2026-11-11, hub `$ref` edit):** the uncommitted `hub/catalog.yaml` edit
(bare `$ref` instead of the hub-relative `../04-…`) will be **undone by the generator** —
`tools/build-hub.sh` step 3 rewrites it back on every run, and step 5 checks the result against the
baseline hashed from the hub-relative form. Both forms validate against the owner's own SDK (checked
today: `valid: true` each), so the edit buys no validity, and the failure mode is silent (a `hub/`
diff after every gate run). Either revert it, or change the generator's rewrite AND re-hash
`hub/hub.sha256` together. This lane wrote no hub byte. Card `reports/RR-HUBREF-20261111.md`.

**Frontier 11 addendum 19 (2026-11-11, the owner's T-A classification verified + two review-side
findings):** the owner's records check out — the classification (probe/smoke = diagnostic; the 13:46
pair = PAIR ATTEMPT, not bookable: block unfilled) is committed in `99d1e38` + `8889a67`, and the
**filled** block for the next attempt is committed in the card (`w8b-cell-01`, digests
`eac8b37b1602`/`e9e587e60f1f`, ~29,000 evictions, $0.00, PASS parsed-equal, INSTRUMENT-BUG verdict,
`engineSelections > 0` precondition). `reports/W8-SPEND.md` §Prediction stays the template — correct,
since its gate is for a PAID cell. **Finding A: the break-even now lands inside the session, the first
time in these books** — n\* = (w/r)(P′/S) = 10 × (98,934 / 28,934) = **34.2 calls** against the **41
calls measured** (w/r = 10 per the catalogue; the reviewer's 12.5 was corrected in `RR-P8CACHE`); W8's
own shape gave n\* ≈ 189 calls against 14–29. It is a preregistrable number for a future PAID cell (fresh
preregistration per P9; still needs the cache lifetime sourced and per-request attribution recorded) —
**not** a cost claim (free tier, $0.00, no cache price; law 7). **Finding B: the open blocker is ARM
ATTRIBUTION, not only engine engagement** — the P8 constraint says the arms are separated by the
profile each was invoked with and by nothing in the trace, so `profile "default"` under `w8bn-paged`
means that arm was not the paged arm (`engine: null` + `engineSelections: 0` is the in-trace
signature): the pair was void for TWO instrument reasons, and the one-prompt precondition should
assert **both** `engineSelections > 0` AND the invocation's profile is `w8bn-paged` — an engine
engaging under the wrong profile would look instrumented and still be mis-attributed, with nothing in
the trace saying so. Also: the free plan's shape estimate is stale (~21k/~90k assumed vs ~28.9k/98.9k
measured) — the w8b lane's file to amend — and the ~99k request quantifies the context-window risk the
plan flagged. Card `reports/RR-W8BBLOCK-20261111.md`.

**Frontier 11 addendum 20 (2026-11-11, CI witness + the P11 pair's missing level):** the full CI is
**GREEN at the current HEAD** (`env -u CTXVM_TRACE_TS -u CTXVM_HERMES_VERSION bash tools/run-ci.sh`:
rust incl. the new `ctxvm-conformance` integration test; node-build parity — 16 events byte-identical;
TS 22+62+46; python 187+8+66; benchmarks/metrics; `SCHEMA CONFORMANCE: PASS (682 checks)` over 677
lines in 27 fixtures with 5 negatives rejected; export-roundtrip OK; hub byte-identity green). The new
`order-*` vectors are rust-side, so the schema gate's totals are unchanged. **Gap found in the landed
pair:** the test documents THREE levels (parsed model, derived page table, replay report) and its
assertion message says "replay report (**page table**, divergences, violations)" — but
`ctxvm_core::ReplayReport` carries **events, divergences and violations only**
(`ctxvm-core/src/replay.rs:48-55`), so no page table is derived or compared: level 2 is asserted in
prose only. The API to assert it exists and is a pure function of the decisions fed —
`ctxvm_core::render::derive_projection(events, turn) -> TurnProjection { turn, slots, tally,
violations }` — so the fix is one call; the alternative is to correct the two comments and drop the
claim. Either assert level 2 or stop claiming it. The test file is the owner's in-flight work, so
this lane writes no test byte. An erratum on this lane's own P11 card corrects its two wrong
statements (a helper that does not exist, and the report-carries-the-page-table claim).
Card `reports/RR-P11GAP-20261111.md`.

**Frontier 11 addendum 21 (2026-11-11, the RFC-0.1 compatibility note LANDED under D18):** the P10 and
P11 answers were already the authorisation, so what remained was execution — the note is now
`spec/rfc-0.1/COMPATIBILITY.md` (a NEW file under `spec/rfc-0.1/`, that document's own declared
scope; **D18**, renumberable by the owner). Three clauses: **C1** a page's identity is
verb-dependent — nested for `page.declare`, flat for the other five page-carrying verbs — and a
consumer MUST dispatch on the event type, never on which fields happen to be present (the P10 rule
verbatim in substance; its reason measured here: the validator rejects a flat-identity
`page.declare`, and `tools/waste-report.mjs:79` is exactly such a sniffing reader in this repo);
**C2** key order within an event is not significant to parsing or replay, the codec stays strict,
see the conformance test (the P11 line, with the test locator added — and the inference made
explicit: the page table is a PURE FUNCTION of the parsed model, so equal models entail equal tables);
**C3** the canonical form of a hash input, normative FOR HASH INPUTS ONLY: code-point key order,
minimal separators, no ASCII escaping, values restricted to strings/exact integers/bools/null/arrays/
objects, floats inadmissible — the P11 answer's own conditional, triggered by umpire's ref truncation
digest and by the two measured divergences (astral-plane key names; number spelling). The note adds NO
field, says nothing normative about a trace line's key order (law 3), and touches neither the sealed
`spec/rfc-0/` nor the existing RFC-0.1 text. **No gate moves:** hub regen + `hub.sha256` self-baseline
verified (the manifest pins no `spec/` inventory) and the full CI is **ALL GATES GREEN** with the note
present (schema PASS 682 checks; hub byte-identity green). Card `reports/RR-NOTE-20261111.md`.

**Frontier 11 addendum 22 (2026-11-11, two owner rulings recorded + the level-2 patch drafted):** the
owner confirmed the note's content as proposed (including **C3's ordering rule** — Unicode code
point, not UTF-16 code unit), so the note's status line now records the confirmation and its C2 cites
the exact doc wording — `derive_projection` is "pure derive from a raw event slice — **identical
bytes for identical inputs, guaranteed**" — which is stronger than the earlier paraphrase and is what
lets C2 speak of replay without the test asserting that level directly. And decision 2 of the
six-item list is now **owner-ruled**: the subject fallback order — **nvidia** (nemotron-super, the
tested path) → **stepfun** → accept longcat too slow for the 120 s cap only if both fail; recorded in
PROJECT-STATE's decisions ledger and in `reports/RR-TADEC-20261111.md` §8, which also states what the
ruling does NOT fix: the arm-attribution precondition (assert `engineSelections > 0` AND profile
`w8bn-paged`) sits in front of the next attempt — a subject change does not repair a mis-attributed
arm — and the free tier still cannot speak to dollars (no cache price; law 7). The P11 pair's third
level is now a **drafted patch** (`reports/RR-P11GAP-20261111.md` §7): a per-turn `assert_eq` on
`derive_projection(&a, turn)` vs `(&b, turn)` (`TurnProjection` derives `PartialEq`), or else correct
the two comments that claim the report carries the page table; the owner's in-flight test file is
not touched by this lane. Card `reports/RR-NOTE-20261111.md` + `reports/RR-TADEC-20261111.md` §8.

**Frontier 11 addendum 23 (2026-11-11, C3 made TRUE of our own tree):** the review of the landed note
found the load-bearing defect — **C3 was false for ctxvm itself**: `packages/node/src/ident.ts:20`
sorted keys with the default `Array#sort` (UTF-16 code units) while Python sorts by code points, so
the two implementations canonicalise the same input differently and hash it differently, SILENTLY. The
owner took option (a): fix it. **Fixed**: `compareCodePoints` in `ident.ts` (code-point order, with a
prefix-first tie-break — the order Python uses and C3 requires; Rust's serde_json BTreeMap agrees by
construction, so TypeScript was the odd one out); two TS tests; and a 12-case vector file
(`rust/crates/ctxvm-conformance/vectors/canonical-form-cases.jsonl`) generated by **Python's**
`canonical_json`, carrying input text + expected canonical bytes + expected digest (NFC vs NFD with
different digests — the no-normalisation rule, pinned; reject cases: beyond 2^53, integral float, -0,
lone surrogate). `validateHashInput` added as the consumer half of C3 (exported + tested, **not** wired
into the minting path: that would make a tool call with an integral float fail to mint a ref — a
behavioural change beyond the note, owner-routed and named). **C3's wording amended**: reject-not-coerce
with the producer/consumer duty split (the spelling is unrecoverable downstream — `JSON.parse("1.0")` is
the number `1`), integers within ±(2^53−1) else rejected or carried as a string, `-0` inadmissible,
lone surrogates rejected, no normalisation, plus a pointer to the committed enforcement.
**No digest moved**: an independent scan of 44 hashed input files found **0 keys outside the BMP and 0
astral characters in values**, and only keys are sorted — so the fix cannot move an existing digest;
the full CI is **ALL GATES GREEN** after it (`check-node-build: OK — 16 events byte-identical`, corpus
checksums verified, schema PASS 682, export round-trip OK, hub green, TS suites 24). Named edge case: a
tool call whose arguments carry an astral-plane KEY would get a different `logicalRef` after this
change. **Routed, not done here**: the `decision.md` approval record (not locatable from this lane — what
it must say is in the card), the W8SIM 5.3 % overstatement, the C3 naming collision (the note now
disambiguates explicitly), and C2's locator (real once the owner's P11 pair + test land).
Card `reports/RR-C3FIX-20261111.md`.

**Frontier 11 addendum 24 (2026-11-11, U6 applied and verified live):** the owner approved U6, and
the change turned out to be **three files, not two** — the MCP server's environment comes from
opencode's OWN config (`~/.config/opencode/opencode.jsonc:20`) as well as the hermes gateway's — so
`opencode.jsonc:20`, `~/.hermes/config.yaml:2114` and the arm-profile copy
`~/.hermes/profiles/w8bo-paged/config.yaml:2115` all now name `umpire-cal-v3.json` (pre-change
backups in `/tmp/opencode/20261111/u6/`). **Verified live through the tool**: `calibration_info()` now
reports `data_version: cal-v1:057a5a35a9d4ec71` — the record named in umpire's `00-SPEC.md` — with
test ECE **0.030163**, Brier 0.172597, accuracy 0.708333 (n=120), i.e. the numbers P5/P7/P11 cite;
before the change the same call returned the v2 map (`cal-v1:aceb881587b3b3a6`, ECE 0.026684) — a
*different map*, not a different label. The opencode side needed no manual restart (the MCP client
respawned on the config change). **One process still holds v2 and it is named**: the hermes gateway's
own wrapper (pid 7513) reads its config at start → it needs a **gateway restart** (the owner's timing:
a restart reaps gateway sessions, and the w8b lane has runs in flight). `health` remains DOWN (the
pinned model server on 8081 is still not running), so U2 stands. Card `reports/RR-U6FIX-20261111.md`.

**Frontier 11 addendum 25 (2026-11-11, U2 verified live; and a correction):** with the pinned model
server started, `health()` returns **ok (200)** and a real `decide` returns key **billing** with
calibrated confidence **0.905882** at **`data_version: cal-v1:057a5a35a9d4ec71`** — the record's map
applied END-TO-END, not merely reported (U6 verified where it matters; latency 5.3 s; the ledger and
records sidecars were written). **U2 is done**; the only environment tail is the gateway-scoped MCP
(its wrapper still holds v2 until a gateway restart — the owner's timing, since a restart reaps gateway
sessions and the w8b lane has runs in flight). **CORRECTION:** this lane's records referred to a
"`decision.md` approval record" — **no such file exists in this repo and never did**; it was the
owner's temporary scratch file for naming the discussion. The ratification lives in the note's status
line, PROJECT-STATE's decisions ledger and the two cards → that item is **closed, not routed**, and the
index lines are corrected. Card `reports/RR-U2LIVE-20261111.md`.

**Frontier 11 addendum 26 (2026-11-11, a small prompt for the W8B lane; and U6 closed on both
surfaces):** the owner asked for a small prompt for the other lane → `design/W8B-LANE-PROMPT.md`, a
companion to `design/W8B-PROMPT.md` (the master) carrying only what changed: the measured state (W8
closed negative; T-A v2 landed asking only what `read_file` reports; the v2 run's NO RECORD classified
as a pair attempt, with the block now filled for `w8b-cell-01`; the measured shape peak 98,934 /
evictable ~28.9k against the plan's ~90k / ~21k), the owner's ruled decisions (subject order nvidia ->
stepfun -> accept longcat too slow; a new subject means new digests, so the block is rewritten and
re-committed before the pair; the arm-attribution precondition — the paged arm ran as profile
"default" under w8bn-paged, so assert BOTH engineSelections > 0 AND profile w8bn-paged before any
pair; no cost-saving claim from a free run, while a future paid variant's break-even is n* ~ 34 calls
against 41 measured), and four small items the lane owes (assert level 2 in the P11 test — the
one-call derive_projection patch; the shape erratum in design/W8B-FREE-PLAN.md; scope the W8SIM 5.3%
sentence to this engine's keep law; rename one "C3"). **U6 closed on both surfaces**: the gateway
restart replaced the wrapper that still held v2 — a new gateway-spawned mcp_server.py carries
umpire-cal-v3.json — so every MCP surface now applies the record's map. Card
`reports/RR-UGATEPROMPT-20261111.md`.

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

**Commit attribution (law, confirmed by the owner 2026-10-31):** every commit in this repo
is authored `kapitaali <teppo@kapitaali.com>`. The global `~/.gitconfig` already resolves
to it, so a plain `git commit` is correct — reach for `git -c user.name/user.email` ONLY
if an override is suspected. Any commit signed otherwise is a mis-signing: record it in the
books and never rewrite it (D11; three 2026-10-30 commits `36cec7c`/`f0f2710`/`d21bcb7`
are the recorded case). Pushing stays the owner's act in every card.

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
| T25 | per-harness injection-as-DATA for `packages/opencode` — the design's per-harness beat resolved as gated mutation (orchestrator-approved proposal reports/T25-PROPOSAL-20261028.md; one commit, all §7 recommendations accepted; §7 acceptance doubled as the cross-lane clearance for `packages/opencode/**`) | M | T24, UC1-RESUME-MIRROR, UC1-PAUSE-MIRROR | **DONE** (RR-T25-20261029; the plugin HOLDS the assembled request draft at `session.context` — pinned contract: `SessionContext extends SessionRequest` with mutable `messages`, design/adapters.md; no app above the plugin — so the design-letter shape is executable as written, off by default; NEW `src/resume-brief.ts` = line-for-lines mirror of the ai-sdk module (T24) with ONE ruled delta — resolver-less v0: stubs package-complete verbatim (`page.evict` `stubText`), full slots degrade loudly to `[unresolved: …]` markers; live wiring: arm at boot AFTER the unchanged resume check (verified boot + `CTXVM_FEATURES` containing `handoff-inject` — the hermes `parse_features` law's shape — + assembly succeeds; failure = loud NOT-armed witness, the plugin must never break capture), then INJECT FIRST in the context hook (Q4 ruling), exactly once per session, `(input as {system: unknown[]}).system.unshift(brief.text)` (Q2 surface ruling), witness `resumeBrief injected turn=N session=… surface=system`; hostile payload → loud FAILED witness, capture continues, never retried; sidecar canon UNTOUCHED (derived data — the T24 law; the witness log is the provenance channel); tracer stays read-only in every path; DISCLOSED: the system surface is NOT metered by the v0 transcript view (`transcriptTexts` reads messages only — provenance lives in the witness log + `resumeFrom` evidence; a messages-surface variant is the recorded v-next alternative); NO corpus drop (the m6/m7 observation-not-injection law stays true for every shipped package); hermes stays verify-only (their `/ctxvm-resume` IS the design's fallback); 7 new tests, suite 51 → 58 green first run; counts `ts 13 + 58 + 45`; ALL GATES GREEN; pushed 2026-10-29, run 40843322867 green 4/4) |
| W2 | real tokenization (adoption push): the `ctxvm-tokenizer` stub replaced | S | — | **v0 LANDED** (RR-W2-20261029: `apx4-char` backend byte-mirrors node `approx4` + `tiktoken-rs 0.12.1` o200k/cl100k behind the non-default `tiktoken` feature + `ctxvm tokens` CLI + the `tokens_source` marking vocabulary; rust 59 default / 60 with the feature, ALL GATES GREEN incl. the new feature gate line; W2b = provider-reported usage wiring CLEARED on all four lanes (owner 2026-10-30, RR-DECISIONS-20261030) — work starts after RFC-0.1 lands (`call.meta` is closed in sealed v0); pushed 2026-10-29, run 40843322867 green 4/4) |
| W1 | dogfood the profiler (adoption push) | M | W2 marks | **dry-run LANDED** (RR-DOGFOOD-20261029: `tools/waste-report.mjs`, parity with metrics.py byte-identical; 6 real traces + snapshot + synthetic validation; zero evictions on real captures → waste = 0 measured, W8 must create pressure; dup-args 10–18% all content-hash DIVERGENT, true dups 0; providerReported 0/32; hermes fault-surface gap → W4; live run scheduled after W4b B1 lands (owner 2026-10-30, RR-DECISIONS-20261030); pushed 2026-10-29, run 40843322867 green 4/4) |
| W3 | fix the metrics — falsifiability (adoption push) | M | W2 marks | **LANDED** (RR-W3-20261029: `refetch_rate` rename + `hard_fault_recall` ground truth per Pichay §3.2 — explicit re-calls only, n=4 on real captures → gate UNMEASURED, falsifiable in principle, ablation = W8-grade; `bootstrap.py` deterministic CIs seed 20261029/2000 on every gate metric; `prices.json` pinned v1 — observed free tiers nvidia/opencode, openai UNVERIFIED nulls, cache-write unmodeled in v0; M0 gate re-anchored hard-fault ≥95% CI-lower n≥30; 07 §W3 section; python 30→44, counts `80 + 44 + 8`; ALL GATES GREEN; pushed 2026-10-29, run 40845029026 green 4/4) |
| W4 | Hermes adapter — official-docs hook-surface verification + cheap-hooks audit + `turn.render` gap in provenance (adoption push) | M | W1 findings | **DONE (audit; no code change — hermes lane)** (RR-W4-20261029: docs-anchored against `developer-guide/observer-hooks` + source @bf0203a794; NEW `packages/hermes/OBSERVABILITY.md` — contract table with locators, what the hooks CANNOT see (system prompt, tool schemas, cache breakpoints, `select_context`/`prune_tool_results_only` replacements, post-`post_tool_call` `transform_tool_result` bodies ⇒ `turn.render` is a page-table mirror, never the request), measured hook cost (no network import, one flush, scan 5.86 ms @34 pages/222 tokens/80k chars vs the 30 s hook budget); FOUR FINDINGS: F1 `identifier_scan` DEAD on live payloads (`_transcript_texts` parses `content` as a parts list; Hermes sends a plain string — conversation_loop.py:350/oneshot.py:103 — so `''` every live turn; census m3 synthetic 2 vs m4/m7 LIVE 0; patch proven red→green in memory), F2 turn units = USER turn (docs) vs model request on opencode/ai-sdk → W5 must classify unit mismatches, F3 provider `usage` available on `post_api_request` but `call.meta` is `additionalProperties:false` → W2b is a SPEC question (W7), F4 `telemetry_schema_version` unrecorded; m7 provenance gains the capture-surface ERRATUM (faults:0 = artifact, share UNMEASURED not 0) + checksum re-baselined, no trace byte touched; ALL GATES GREEN ts 13+58+45 / python 80+44+8 / schema 682 checks · 27 fixtures; pushed 2026-10-29, run 40941042878 green 4/4) |
| W4b | Hermes capture-surface fix — live-shape `_transcript_texts` + live-shape generator (B1 + B2 LANDED) | S | RR-W4, lane clearance | **B1 LANDED (2026-10-30; owner cleared B1-only, RR-DECISIONS-20261030)** (RR-W4B-20261030: `_transcript_texts` now accepts the LIVE plain-string `content` (agent/conversation_loop.py:350 / oneshot.py:103) that made `identifier_scan` DEAD on every live Hermes capture (m4/m7 faults:0 = artifact); ~12 lines + 3 tests — live-shape regression pin RED-before→green-after (0≠1, `''`≠text proofs recorded), block-shape guard, unit shape matrix; hermes suite 80 → 83, counts truth-up `python 83 + 44 + 8` (run-ci.sh:67; ci.yml has no counts line); ALL GATES GREEN; B2 live-shape generator DEFERRED to immediately after W5; B3/B4 → W7/RFC-0.1; F2 stays NOT proposed — W5 classifies unit mismatches) · **B2 LANDED same day per the rider (RR-W4B2-20261030)** (`generate_traces.py` gains `make_live_shape_trace()` — m3 echo beats through the LIVE shapes (plain-string history via `live_message()`, `tool_name` hooks, `"ok"` string results, `INIT_LIVE` = W5-observed `unknown/unknown`@200000 so the fixture invents nothing the plugin lacked evidence for) + in-emitter self-checks (all-string history, identifier_scan ≥ 1, beat structure 5/3) so a generator run cannot emit a dead-surface trace; NEW committed fixture `hermes-live-echo-synthetic.jsonl` = frozen echo's exact composition through pure live shapes — 20 events/5 turns/3 pages, faults `[identifier_scan@0, tool_recall@0, identifier_scan@1]` (replay exit 0 = 3× faultOfResidentPage R1-remention class; sealed v0 validator PASS 75 checks); NEW `test_generate_traces.py` 4 tests, red-before = 3× AttributeError: (1) end-to-end B1-class death guard — identifier_scan alive on all-string history pinned SPECIFICALLY (tool_recall ref-based and parser-immune) = the first committed artifact of the multi-user-turn D6 activation shape, (2) returned-history audit (block-only generator regression fails even with a healthy parser), (3) sha-verified BYTE PARITY packages/hermes/fixtures ↔ corpus/m3 + the RR-T17 counts (echo 20/3/3/5, thrash 26/5/5/5), (4) `_write_fixture` FROZEN guard — the generator refuses to overwrite the m3 drop sources without --force (frozen bytes verified untouched, m3 provenance door closed — the deliberate extra beyond the rider); hermes 83 → 87, counts truth-up `python 87 + 44 + 8`; the fix ACTIVATES the measured 5.86 ms/turn scan; `identifier_scan` remains an INFERENCE surface, never ground truth) |
| W5 | Cross-harness portability — one identical scripted task in OpenCode AND Hermes → `ctxvm diff` (adoption push; replaces the Vercel-SDK second adapter as M2 portability evidence) | M | prep landed, owner-run window | **EXECUTED + CLASSIFIED — LANDED (2026-10-30; owner ran both captures)** (RR-W5-20261030: both traces RFC-0-valid, replay exit 0 — opencode 2× faultOfResidentPage logged per RFC-0:121 = FIRST LIVE R1-remention evidence, hermes clean; raw diff divergent at event 0 classified: D1/D2 tool vocabulary + args shape = harness-faithful minting + spec ambiguity (W7#1 canonical-ref law), D3 no same-ref pair → "no hash mismatch" vacuous — read pair matches refs under name canonicalization and still diverges hashes (receipt bodies dominate tokens; W7#2 page-body semantics), D4 turns 3 vs 1 = UNIT MISMATCH never behaviour (W4 F2 confirmed live: hermes pre_llm once per user turn), D5 tally 24 vs 94 = v0 no-evict law × token regime, D6 faults 2 vs 0 = pre_llm-at-turn-start granularity — pages declared mid-user-turn never scanned in single-turn sessions, NOT a B1 regression (W7#3), D7 session.open unknown/unknown = env law didn't reach the hermes boot, /ctxvm-trace start command args carried it (W7#5/RFC-0.1 R2 validated), D8 sidecar hygiene; NO adapter bug in either trace; W1 piggyback: opencode waste 0.667, hermes 1.0 metric-degenerate at 1 turn, duplicates 0, ZERO hard faults (W3 M0 gate stays unmeasured); NO corpus drop (owner ruling; verify gates: opencode promotable-passed, hermes exits 1 at the faults:0 gate by design); 01-PLAN.md:115 M2 wording updated, :78 untouched; W7 intake = 5 items; captures stay working evidence in owner-held /tmp/ctxvm-w5/) |
| W6 | OpenTelemetry decision — mapping note (design) + exporter prototype | M | W5 findings (informative only) | **LANDED (analysis + prototype; D3 DECIDED 2026-10-30: D3-c layered)** (RR-W6-20261029: NEW `design/otel-mapping.md` — semconv vocabulary verified from `open-telemetry/semantic-conventions-genai` (pushed 2026-10-29; the OTel site now redirects there) + OTLP 1.11.1 §JSON encoding, every GenAI signal `Development`; event→signal table (session.open→`invoke_agent`, turn.render→`chat`, page.declare→`execute_tool`, fault/evict/render/pin→`ctxvm.*` span events, cacheEstimate→`gen_ai.usage.cache_read` ONLY when providerReported); THREE structural gaps: xCABI has NO clock (schema has zero time fields ⇒ time-less OTel spans), `residentTokens` ≠ `gen_ai.usage.input_tokens` (filling it would reintroduce W3 dishonesty), `page.declare` carries no turn (tool spans cannot parent) — the first and third are RFC-0.1 candidates routed to W7; coexistence WITH LOCATORS (Langfuse exports any span carrying a `gen_ai.*` attr; Arize: OpenInference Stable vs GenAI still-in-development and Phoenix reads `gen_ai.*` with reduced UI); prototype `tools/otel-export.mjs` 235 lines, no deps/network, NOT wired into CI by design — m1/m6/m7/m8 project with 0 OTLP-JSON violations (13/14/17/10 spans); D3 options table, layered recommended as INPUT ONLY — D3 now DECIDED: D3-c layered, with a drift-guard rider at exporter promotion (RR-DECISIONS-20261030); ALL GATES GREEN; pushed 2026-10-29, run 40941042878 green 4/4) **D3-c PROMOTED (2026-11-08, `RR-D3COTEL-20261108`):** the exporter is a supported surface — mapping semantics unchanged (CLI output byte-identical to the audited prototype; scope string stays `0.1.0-prototype`; D12 law honored: est branches stay keyed on `cacheEstimate.providerReported`, `providerUsage` DECLARED DROPPED) + the rider's drift guard mechanical: `EXPORT_SPEC` per-type consumed/dropped tables (+ global `ts` drop) sync-tested against the RFC-0.1 schema's flattened field set in `tools/otel-export.test.mjs` (4 tests green; red-before probes on phantom/undeclared/golden-drift all exit 1, logs kept); golden OTLP/JSON fixtures over frozen byte-inputs (W6's four corpus traces 13/14/17/10 spans reproduced + the providerUsage-carrying ai-sdk fixture, 124,319 B); the `gen_ai.usage.cache_read` gate remains as designed (fires only where a capture flips the key). Two ci.yml mirror-law gaps found by verification and fixed in the same card (ai-sdk TEST step absent since T15 B3 `801047c`; LICENSE cmp absent since W10 build `72360f1`); gate ALL GATES GREEN with the exporter step in both the mirror and the workflow (parsed: 17 ts steps) |
| W11 | Scope discipline — README honesty pass (adoption status, measured limitations, governance) | S | W1, W3, W4 findings | **DONE** (RR-W11-20261029: root `README.md` rewritten around Adoption status (one author/one machine/nothing published/no external adopter — umpire is the same author), Measured limitations (7 rows w/ evidence pointers: no real session ever paged — 4 evicts all on synthetic m1, 10 real captures at 0; hard-fault gate UNMEASURED n=4<30; apx4-char estimates and 0/85 call.meta provider-reported; hermes identifier surface dead ⇒ m4/m7 under-report; cross-harness turn units differ; single corpus on free tiers; the 1.5× control-plane milestone untested), Status 2026-10-29 (rust 59/60, schema 682 checks/27 fixtures, ts 13+58+45, python 80+44+8, 17 traces), and Governance + a 4-step roadmap (portability evidence → capture surface → RFC-0.1 + conformance kit → governance only after the first external implementer); the "claims nothing you can't re-run" overclaim replaced by what-the-gates-prove / what-they-do-NOT-prove; `01-PLAN.md` §7 rewritten — the "Switzerland (LF-governed)" line is gone (Apache-2.0, no hosted product, one author, not a foundation) and ODPS is named as a distribution format, not governance; NO hub/llms.txt/manifest/package-metadata edits — W10 owns packaging and publication stays gated; every number re-measured before writing; ALL GATES GREEN; pushed 2026-10-29, run 40941042878 green 4/4) |
| W12 (S0–S1) | Runtime ABI architecture — Steps 0–1 reconciliation + justification (design-only, gated) | S | W4, W6 findings | **DONE (Steps 0–1 only; D7 DECIDED 2026-10-30: hold — `ctxvm-rt` is a separate consumer project; implementation and `ctxvm_abi.h` stay gated on W8)** (RR-W12-S01-20261029: `design/runtime-abi/00-reconciliation-and-justification.md` — Step 0: no `00-SPEC.md` exists (spec surface = `02` + sealed `spec/rfc-0/`), today's "xCABI" is an EXCHANGE format so W12's C-ABI usage is a NAME COLLISION → drafts use provisional `ctxvm-rt`, flagged under D7; Step 1: the prescribed real-latency measurement is IMPOSSIBLE — 5 of 85 call.meta carry latencyMs and all five are in the SYNTHETIC m1 seed, zero real latency anywhere — so the owned path is measured instead (canon+sha256 0.26 ms @50 KB / 192 MB/s, 5.7 ms @1 MB, JSONL parse 40 MB/s, whole corpus 4 ms) ⇒ ≤0.1% of a model round trip ⇒ "benefit not measurable, shrink the ABI to safe handles": opaque generation-tagged handles + explicit ownership + error codes, nothing more; arena/CoW/bytecode dispatch stay unbuilt; discovery: W6, W7 and W12 all want the SAME missing clock field, and `post_api_request` already carries `api_duration` ⇒ strongest case yet for one clock card; pushed 2026-10-29, run 40941042878 green 4/4) |
| W7 | RFC-0.1 from umpire's friction — **CHAIN CLOSED 2026-10-31** (proposal + D4 + implementation + the consumer adoption) | M | RR-W4 findings, RR-W6 gaps | **CHAIN CLOSED (umpire `d8ecef4` + `a701072`, 2026-10-31 — see §0):** the consumer adopted the profile and the friction is measurably gone — umpire `replay fixtures/ab-demo.ledger.jsonl` 3× faultOfResidentPage → 0 violations, all four of its ledgers clean under this repo's v0.1 validator, its vendored schema re-vendored from `36cec7c` (fork eliminated), L4 version-branched, calibration corpora deliberately left v0. PRIOR: **IMPLEMENTED (2026-10-30; RR-RFC01-20261030 — full note in §0)** — additive: `git diff --stat spec/rfc-0/ 02-xcabi-events-v0.md` EMPTY, so the sealed surface is byte-identical; NEW `spec/rfc-0.1/` schema + normative R0–R5 text + validator that proves the sealed v0 schema still rejects v0.1-only lines; rust `IntentionalRerun` + `ProviderUsage` + `check_version`, core version-branched R1 exemption (intentional_rerun on a resident page logs no violation in v0.1, still violates in v0 — both pinned), gate wired into all four CLI read sites after verification found it was DEAD CODE (`replay` exited 0 on a v0 trace carrying intentional_rerun — the exact guess R0 forbids), regression test red-if-unwired; new conformance vector `events-v0-1.jsonl` (serializer-canonical); run-ci + ci.yml v0.1 step; 07 §W3 note; v0 UNREGRESSED (17/17 corpus traces replay exit 0, v0 schema gate 682/27 with FIXTURES untouched); sealed validator NOT edited (proposal §7.2 refused — branch lives in the new file, both directions proven there) and R1 emission deferred (§5.1) — which makes an EMITTER card the critical path, since no adapter emits schemaVersion today (0 matches) and providerUsage/ts are therefore unemittable (blocks W2b + W1's providerReported 0/32); rust 59 → 66; ALL GATES GREEN. **EMITTER CARD 1 LANDED (2026-10-31, RR-RFC01E1-20261031 — D8 split: version switch first):** `schemaVersion: "0.1"` now emitted on session.open by node's tracer (node/opencode/ai-sdk inherit — opencode imports node by relative path) and the hermes python port; red-before on four standing pins (both TS `undefined !== '0.1'`, both kit parity key-drift messages updated in the same card both sides + 09-plugin-parity.md §2 row) + two field-order pins caught mid-work; derived-fixture truth-ups with frozen provenance held (ai-sdk trace regen = exactly 1 line, parts untouched, validator leg → v0.1 `OK: all checks passed`; hermes live fixture regen with the B2 frozen corridor printing SKIPPED + m3 checksums OK); NEW driver.ts freeze-guard for `opencode-echo.jsonl` (m1 drop source, refusal exit 3 proven live); run-ci.sh:72 + ci.yml v0.1 step now validates the vector PLUS both emitter-produced artifacts; counts unchanged (rust untouched; `ts 13 + 58 + 45`, `python 87 + 44 + 8`); providerUsage/ts now EMITTABLE → W2b unblocked (next: per-lane wiring per D8); ALL GATES GREEN. PRIOR: **PROPOSAL LANDED — D4 APPROVED 2026-10-30 (all four §8 questions as proposed; RR-DECISIONS-20261030); implementation card next, sealed v0 stays byte-identical, umpire fixture regeneration is the cross-repo tail** (RR-W7-20261029: `design/rfc-0.1-proposal.md` + `design/rfc-0.1/` fixtures; friction reproduced exactly — `ab-demo.before.jsonl` replay yields 3 `faultOfResidentPage` violations at seq 2/3/5, exit 0, and umpire's own validator PASS 113 checks; SIX items: R1 fault source `intentional_rerun` (new enum value, valid resident-or-stubbed, exempt from the fault-resident rule, never deduped, never ground truth — an `intentional` flag is the recorded smaller-change fallback but leaves source-keyed classifiers wrong by default), R2 pin/seed stay OUT of the ref as a normative clarification (moving them in would turn A/B into new pages), R3 optional `call.meta.providerUsage` (input/output/cached, provider-reported, omitted when unknown — W4B B3's target), R4 optional `ts` on every event + `page.declare.latencyMs` (the one clock W6/W12 also want; excluded from replay state, omitted in golden fixtures), R5 optional `page.declare.turn`, R0 optional `session.open.schemaVersion` `"0.1"` as the version boundary; compatibility DEMONSTRATED — the after-file and every v0.1-only line are rejected by the sealed v0 parser/validator (exit 2 / FAILURES on all 5 lines), intended strictness not a bug; after-file classification 3 intentional / 0 paging is rule-level, no v0.1 replayer exists; minting cross-check byte-identical (4 decide / 4 hash / 9 approx / canon; 17/17 umpire records re-mint) but umpire's module declares itself a Python MIRROR of `ident.ts @ 361043e` ⇒ conformance check, NOT a second implementation, phrase must not be used; no schema/spec/validator/replayer/metric/package/corpus byte edited; proposal fixtures deliberately NOT in the CI list (v0.1 shapes, invalid under sealed v0); ALL GATES GREEN, counts unchanged; pushed 2026-10-29, run 40941042878 green 4/4) |
| W8 | the decisive experiment — does paging help? (adoption push; prereg-before-run law, D5 USD 25 cap) | M | W2, W3, W4 (all **DONE**) + owner gates | **PREREGISTRATION LANDED (2026-11-01, RR-W8PREREG-20261101 + the freeze `design/w8-capture-design.md` — see §0):** capture design committed BEFORE any run — arms naive (stock compressor, never-fires recorded as a design fact) vs paged (NEW ctxvm ContextEngine plugin = v1 FaultPinPolicy; the seam verified at source `agent_init.py:1904` + the full ABC, FITS verdict recorded with safe-worker + clone_for_agent + select_context-before-cache-control laws); k=6 real-repo templates + mechanical checkers, R=3 alternating, T0 freeze for texts/model/price-row/vBudget; 07-verbatim metrics over RECORDED arm baselines with seed-20261029 CIs; M0 gates = NTR ≥1.5× @ preregistered δ=10pp paired accuracy non-inferiority + hard_fault_recall ≥95% @ CI lower n≥30 pooled + replay 100%; stopping = coverage + round-robin continuation, no mid-run expansion (defect ⇒ PILOT record); D5 ledger: `reports/W8-SPEND.md` + priceModelVersion 2 paid-row lock BEFORE first paid run + binding pre-run projection stop + est-vs-billed side by side; D12 fork RULED (est* keep page-table semantics; hermes post_api_request→providerUsage wiring = implementation precondition); redaction DQ law registered (mkdtemp + zero-match credential scan + m8-shaped provenance; corpus drop = separate owner gate); no data/no code/no spend; ALL GATES GREEN, counts unchanged. **IMPLEMENTATION LANDED (2026-11-06, `RR-W8IMPL-20261106`, plugin 0.10.0):** the implementation card the prereg named is in — (a) `providerUsage` intake on `post_api_request`, strict (whole-number buckets only; `inputTokens` = prompt minus BOTH cache buckets, clamped; absence never a zero), last-write-wins per pending meta with orphan pairing, wire order `latencyMs`->`providerUsage`->`ts`; `cacheEstimate.providerReported` stays FALSE by the owner's option-A ruling (a recorded erratum against the frozen design text, analysis-neutral: the gate reads `cacheEstimate`); (b) the paged arm's `FaultPinPolicy` engine (`live/context_engine.py`, selection not compaction, seven laws, `vBudget` 24000 confirm-or-raise only, `register_context_engine` fail-open, inactive unless a profile carries `context.engine: "ctxvm"`); (c) `tools/dq-secret-scan.py`, the zero-match pre-drop gate that never prints matched bytes. hermes 171 tests; docs updated in the same card (parity §2 W8 note, HOOKS seven hooks, OBSERVABILITY F3 resolution). **ARM INERT AT 24k (2026-11-06, RR-ENGINEGAP):** a live capture shipped 358,616 tokens with the engine attached and compaction disabled — `_plan` returns early when the protected floor (system prompt + 3 head + 6 tail + pins) exceeds vBudget, which six real tool results do. Probes: 600,200 chars with a large tail -> no selection; 1,372,470 with a small tail -> 92,477 out. **The W8 paged arm only measures something on tasks whose floor sits below 24,000 tokens**; choose the task set accordingly or amend the prereg before the run. Daily use: raise `CTXVM_VBUDGET` or revert to `compressor`. The engine emits no record of its selections. **ENGINE ENABLED (2026-11-06, owner request, RR-ENGINEON):** `context.engine` is now `ctxvm` on this machine — the paged arm applies to agents built after the change, selects to 24,000 tokens (never compacts, silent), and the naive arm can no longer be captured on this profile while the key is set. **Blocked on owner:** freeze ratification, model+price row, execution window; the 0.10.0 install sync is DONE and smoke-proven through the installed package; a gateway restart is still owed before a live provider receipt can appear. **BLOCKED 2026-11-07 (`RR-W8CHUNK-20261107-2` §11):** two paid cells exist and neither counts — chunk 1's naive cell (42.5 min, 150 calls, $0.3303, no artefact, `max_iterations_reached(150/150)`, capture verified: 721 events, coverage exit 0, replay byte-identical) and the post-0.10.4 slice's naive cell (37 min, 150 calls, $0.3077, same ceiling, same no-artefact, 840 events, 133→150 `perApiRequest` samples growing 3,010→268,635 tokens). Spend $1.1541 of the $25 cap; 0 cells count, 48 pending. THE HALTING DEFECT: the arm witness added in `c947530` records the observer, not the observed — `__init__.py:489` reads `engine_registered`, which `build_engine()` sets unconditionally at plugin load, so every cell reads `engine: "ctxvm"` including the naive arm; `__init__.py:490` reads `basename(HERMES_HOME)` of the flushing gateway, which is `.hermes` for all three profiles the single multiplexer serves, so `-p w8-naive` cannot appear in the capture. Six harness defects are inventoried with locators in the report (§11), four now fixed by prior cards, #3/#4 open and blocking, #5 the `-z` turn-boundary gap worked around by the receipt-based NTR in plan §4d, #6 the 150-step ceiling binding the deliverable at both 33 and 13 parts, decision deferred. REOPEN CONDITIONS (all three): a capture attests the activated engine and the session's profile; a cell produces its artefact or fails on content rather than steps; the fixture/ceiling question is decided. No paid cell until then; `--plan` returns 48 of 48 because the slice's row is recorded ABORTED, so the cell is retryable. **CORRECTION (19:30, same report §12):** plugin **0.10.5** (`efeeeb1`, installed 19:19:16) closes #3 on disk — `engine` now reads activation (`select_context()` count; `engine` null with `engineSelections: 0` is a real observation) — and re-scopes #4 from a witness bug to a deployment rule: activation is a PROCESS fact, so one gateway per arm is required and the runner must refuse a multi-profile gateway. The running gateway is 0.10.4 (PID 200441, 18:14:39), so no process has the counter, and the single multiplexer violates the rule; W8 STAYS BLOCKED. #6 is re-framed by the same card: cell A's 700 declares were 686 `search_files` (69,439 tok) against 14 `read_file` (57,489 tok) over 632 refs, so the task is search-bound and the fixture question is a TOOL-SURFACE question, not a file-count or ceiling question. Amended reopen conditions: 0.10.5 per arm, a runner refusal of multi-profile gateways, the tool-surface decision, and a cell that produces its artefact. The runbook's pre-flight still says 0.10.4 against an installed 0.10.5 — the next executor stops there unless the book is bumped |
| W10 | Packaging and distribution — prepare only; publish/submit/tag only with approval (adoption push) | M | W11 (README ownership), owner gates | **NODE BUILD LANDED (2026-10-31, RR-W10BUILD):** the npm hard blocker recorded in `design/packaging.md` §6.2 is cleared — `tsconfig.build.json` emits `dist/` (JS + `.d.ts`), `exports` resolves to it, `files`/`repository`/`build`/`prepack` set, devDeps typescript + @types/node (dev only, zero runtime deps preserved), `dist/` gitignored; in-repo development still needs NO build (`tsconfig.json` stays `noEmit`, tests run the `.ts` sources). `tools/check-node-build.sh` is the gate: one full trace replayed through sources AND `dist/` under the D9 opt-out must be BYTE-IDENTICAL (16 events) — a behaviour-changing build fails there. `npm pack --dry-run` → 9 files / 13.9 kB with LICENSE+README+dist (the root LICENSE is copied into the package and `cmp`-guarded in run-ci gate 2 because npm cannot include it). CI was wired the same day (option 2): the ts job now runs the source suite, then `npm ci` + build, then the parity gate — so the publishable artifact is rebuilt and proven on every push; `tools/run-ci.sh` mirrors the steps exactly (all gates green, `npm ci` 0.8 s warm). REMAINING DISCLOSURES: `engines` unchanged (no older Node to verify a lower floor), the Actions run itself not executed locally (workflow parsed + every step exercised through the mirror), nothing published/tagged. PRIOR: **PREPARE DONE — nothing published/submitted/tagged; owner cleared 2026-10-30 (RR-DECISIONS-20261030): `packages/node/**` JS build + metadata, PyPI repo-only until PyO3, NO publish/tag until W8 (D6)** (RR-W10-20261029: NEW `design/packaging.md` + README 5-minute checkout quickstart; four hard blockers found and evidenced — npm `@ctxvm/node` cannot ship as-is because `exports` is `./src/index.ts` and Node refuses TypeScript under `node_modules` (needs a JS build + `files`/LICENSE/repository; `engines >=22.6` predates default type stripping 22.18/23.6), `cargo publish --dry-run -p ctxvm-core` exit 101 (workspace path deps lack `version`; `ctxvm-codec` alone EXIT 0 with no repo/readme warnings), PyPI `ctxvm-py` wheel builds (4,939 B) but is a subprocess wrapper needing the Rust binaries (needs platform wheels or a documented prerequisite), and bare `umpire` is taken on npm/crates/PyPI/GitHub org by unrelated projects so any publication needs a qualified name; `ctxvm`/`xcabi` names are free on all four, npm scope `@ctxvm` UNVERIFIED (org page 403); license audit clean — Rust deps MIT/Apache-2.0/Unicode-3.0/Unlicense, no copyleft, zero npm runtime deps, Python stdlib-only, gate-only ODPS SDK license UNVERIFIED; trademark is a web observation only (no record surfaced, UNVERIFIED) with Cursor's "Agent Trace" RFC recorded as an adjacent-words risk; Hermes catalog + OpenCode ecosystem entries DRAFTED and NOT submitted (Hermes index URL 404 at check, exact keys UNVERIFIED; OpenCode entry is a docs-table PR); no `packages/node`/`packages/hermes` metadata edited (lane rule) and no hub/llms.txt changes; pushed 2026-10-29, run 40944095816 green 4/4) **RIDER CLOSED — ENGINES FLOOR VERIFIED (2026-11-01, RR-NODEFLOOR-20261101):** the "no older Node to test a lower floor" gap closed with real nodejs.org binaries — the pinned floor `>=22.6.0` verified REAL for sources (ts suite 20/20 on node v22.6.0 under the explicit `--experimental-strip-types` flag with FILE args `--test test/tracer.test.ts`; the repo's directory-arg invocation `node --test test/` FAILS there with `ERR_MODULE_NOT_FOUND` — an invocation-surface fact, not an artifact defect, no consumer ever runs `node --test`), and the DIST ARTIFACT runs LOWER: a dist-only consumer (one echo trace, `CTXVM_TRACE_TS=0`) is byte-identical across node 20.20.2 / 22.6.0 / 26.13.0 (sha256 `40a9618f60bd…`; node 20 has no type-stripping at all) ⇒ true floor ⊆ 20 LTS; `engines` UNCHANGED — the lowering candidate is a publish-time decision (D6); equality claim scoped to the observed trace shape |
| W11b | External-correction pass — XERJ Corpus Hub selection in the adoption status (W11 follow-up) | S | W11, XERJ founder email 2026-10-29 | **DONE** (RR-XERJ-20261029: README adoption status names XERJ (`https://xerj.org/`, `https://github.com/xerj-org/xerj`) as selecting the W3 metrics commit `7a4f499` for inclusion in its public Corpus Hub (`https://hub.xerj.org/`) index under Apache-2.0 with attribution — explicitly a reference-index selection of one artifact, NOT xCABI adoption; listing **pending/UNVERIFIED**: the live Hub catalogue (`https://hub.xerj.org/llms.txt`, 530 corpora) and the `corpus-hub` branch tree (12,257 entries) contain no `ctxvm`/`xcabi` match, GitHub issue/commit search over `xerj-org/xerj` returns none, and the email's "5 files / ~490 lines" claim matches the W3 code/tool subset (5 files, 494 changed lines; the full commit is 9 files with docs/books); "no external adopter" stands and "only consumer" is narrowed to *runtime* consumer; owner action: reply sent 2026-10-29 (thanks; no requirements); no code/schema/corpus/package/publication change; ALL GATES GREEN, counts unchanged; pushed 2026-10-29, run 40945691069 green 4/4) |
| SUPPORT-1 | Funding surface — README "Support this project" + Bitcoin address (owner-directed) | S | owner 2026-10-30 | **DONE** (RR-SUPPORT-20261030: README section after Governance — validated bech32 P2WSH address `bc1qrdah…0268` (BIP-173 checksum verified before publishing; verbatim from the owner's untracked `~/Documents/bitcoin.txt`), donation policy stated plainly (all donations → compute + development; no entity, no tax deductibility, no perks; donations raise the corpus budget above the preregistered cap, spend recorded in `reports/`), funding-options analysis recorded with UNVERIFIED markers (Sponsors/Liberapay feasibility UNVERIFIED; NLnet/NGI Zero UNVERIFIED + applying is an owner gate; NVIDIA credits UNVERIFIED; paid harness-port work = realistic near-term; ODPS data-product sales flagged with trade-offs, NOT recommended now; token schemes rejected); public funding ledger = v-next owner option; no code/schema/corpus/package change; ALL GATES GREEN, counts unchanged) |

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
| HYG-2 | repo hygiene — research sources tracked, white-paper source committed, 7 MB of build noise ignored | XS | W11 (honesty pass), white-paper delivery | **DONE** (`d21bcb7`, 2026-10-30; documented 2026-10-31 in RR-HYG2-20261031): the committed `research/white-paper.pdf` had NO source in the repo — its numbers were unreproducible — so the source set (`white-paper.md`, `index.md`, `conf.py`, `RESEARCH-PLAN.md`) is now tracked with a NEW `research/white-paper/README.md` declaring the silent duplication (PDF source vs MyST site source, same twelve sections, edit both until one is generated); absolute home paths removed from the two source files (the PDF was already clean); `research/white-paper/_build/` (~7 MB), `.opencode/` (capture shim re-exporting by ABSOLUTE path) and `/notes/` ignored and removed from the tree; tree clean apart from deliberate ignores, sealed untouched, ALL GATES GREEN, counts unchanged |
| CI-1 | CI↔mirror alignment + local workflow rehearsal (`tools/ci-rehearsal.py`) | S | W10 build, run-ci mirror law | **DONE** (RR-CIALIGN-20261031): the owner asked how the CI is tested; the answer included that it had drifted from the mirror it claims to be. NEW `tools/ci-rehearsal.py` clones + overlays the WORKING TREE, then runs each job's `run:` steps in order with a per-job venv, stopping at the first failure like Actions (`uses:` steps skipped, host tool versions printed) — so a workflow edit is testable BEFORE a push. NEW `tools/export-roundtrip.sh` extracts the T21 chain so mirror and workflow run one text. THREE DRIFTS FIXED: six fixtures (corpus/m6, m7, m8) never validated in CI (24 in the mirror vs 18 in the workflow), three drop checksum steps missing (CI verified m1–m5 only, so every drop after M5 had no integrity check), and the export round-trip chain absent from CI entirely. Rehearsal RED-BEFORE proven (`run: exit 7` → `FAIL schema`, exit 1). Result: rehearsal OK 4/4 jobs in a pristine clone; ALL GATES GREEN. GITHUB-VERIFIED the same day: run 41240870951 on `31bd84f`, 4/4 jobs success in 34 s — the three new checksum steps and the export round-trip executed there for the first time. No `act` (still not the real runner). |
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


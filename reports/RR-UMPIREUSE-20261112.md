# RR-UMPIREUSE-20261112 — how umpire is currently used, and how it works right now (a note, for the
## next agent: the mechanism, this lane's use of it, and the limits that must not be forgotten)

Card: a note, written at the owner's request, on the state of the umpire side on 2026-11-12. Everything
below was verified by calling the live MCP today, not recalled.

## 1. The mechanism, as it stands

**Three parts.** A stdlib JSON-RPC **MCP server** (`umpire/mcp_server.py`, six tools) → a **pinned local
model server** (llama.cpp v0.7.0, `runners/src/build/bin/llama-server`, Qwen3-1.7B Q8_0, on
`127.0.0.1:8081`) → the **calibration artifact** plus the **ledgers**. The MCP is a thin proxy over the
model server: with the model server down it answers *"connection refused"* while the service looks alive.

**The pins make drift a hard error** (`harness/pins.json`): three models pinned by SHA-256 — weights,
decoding (`json-label-enum-v0@llama.cpp-v0.7.0/sha256:0f60e0483`), prompt template, runner binary; the
default pin is `qwen3-1.7b` ✓. The **calibration of record** (`cal-v1:057a5a35a9d4ec71`,
`calibration/umpire-cal-v3.json`, isotonic/1, confidence statistic `top_probability`, labels
billing/other/sales/technical, seed 7) is **bound to that pin's hashes** — so a drifted model *or
template* invalidates the calibration by construction ✓.

**The decision path** (one `decide` today, `latency_ms 6300`, $0 of money): state text + a label set →
the pinned model returns constrained label probabilities → the MCP returns exactly **one key**, the raw
probabilities, the entropy-complement confidence, optionally `calibrated.confidence` (fitted P(key is
correct) — *not* a correctness guarantee, opt-in), and **mints an xCABI RFC-0.1 trace**: `ref` =
`tool:decide({labels,state})`, `contentHash`, `model_pin` (with every hash), labels, seed, latency —
written as a **ledger** (the events) plus a **records** sidecar under
`~/.local/state/umpire/ledgers/`.

**Two gates on the output, both exercised today:**

| gate | what it does | today |
|---|---|---|
| `validate` | the xCABI-0.1 validator: shape + semantics + **14/14 engineered negatives** (version-branched: v0 → 12, v0.1 → 14) + the calibrated-record cross-checks (raw stays authoritative; the calibrated confidence must recompute from the raw probabilities) | today's fresh ledger → **PASS (111 checks)**; the `intent-router` fixture → **PASS (134 checks)** |
| `replay` | re-derive the page table from ledger+records and compare **byte-for-byte** with the committed baseline | the `intent-router` fixture → **BYTE-IDENTICAL, page-table sha256:bd3fd7beff3f963e** ✓; a *fresh* ledger has no committed baseline yet, so it reports a DIVERGENCE — correctly, and not a defect |

The determinism object is the **derivation bytes**, never the validator's prose; and the claim is scoped
(page-table replay determinism on one machine/build — 470/480 strict), never "deterministic" unqualified.

## 2. How this lane uses umpire — as an instrument, not as a decision-maker

Today it was used exactly twice, both in the **umpire** repo and both about the service itself:

1. **Diagnosing the post-reboot failure**: `health` → `ok: false`, *"Connection refused"* — which
   identified the missing model server (the MCP processes were alive).
2. **Proving the chain after the restart**: one real `decide` → key `billing`, raw probabilities,
   confidence 1, `calibrated.confidence 0.855263` on the record's map, `ref`/`contentHash` minted, ledger
   + records written.

**No judgement in the ctxvm lane's work was made by umpire.** Checkpoint A's reading, cell-01's
verification, the endorsement of the "no `page.evict`" decision, and the CI-red diagnosis all came from
the books: committed bytes, captures, the hermes DB, the GitHub API. And structurally it could not be
otherwise: umpire is a typed-decision primitive over opaque state text with caller-owned labels, while
the review lane's questions are not label sets, and **a model cannot check a locator** — using a local
model to decide what the files say would be a self-referential loop. The lane's discipline is
*verify-then-record against the books*; umpire's role here is exactly what its own instructions name —
*"use pins to inspect pin identities, health before a batch, and validate/replay on ledgers."*

## 3. What umpire is **not** used for here, and why

- **Not as a source of truth for the repo.** The books are the record (the rule: *if a chat summary and a
  file disagree, the file wins*).
- **Not for cost or savings reasoning.** Law 7 forbids a cost-saving claim on our data; umpire runs on a
  local model and its own corpus, so it says nothing about the economics of a *paid* provider.
- **Not as a substitute for a preregistration.** The umpire side has its own law 4 (pre-register before
  running) ✓ and the ctxvm side has the prediction-block rule ✓; both are unaffected by umpire's
  existence.

## 4. The limits that must travel with every umpire number

- **The calibration does not transfer, and the sentence that says so is still missing.** The artifact was
  fitted on umpire's own label sets; the P5 answer was *publish per-corpus calibration WITH the caveat,
  no transfer claim* — and the MCP's current caveat ("it is not a correctness guarantee and is opt-in") is
  a **different, weaker** claim. The transfer caveat is **G2** and is ready to apply
  (`reports/RR-UMPIREREADY-20261111.md`).
- **Determinism is scoped** to one machine and one build; cross-machine and cross-build are unmeasured.
- **`calibrated.confidence` is a fitted P(key is correct)**, not a promise.
- **The model is small and local**: 1.7B, ~6 s per decide, free — which is also why the free-tier
  economics of the *other* side (W8B/W8C) are not comparable to a paid provider's.

## 5. The direction of travel, and the operational facts

**umpire consumes the ctxvm wire standard and contributes nothing back** (the umpire repo's `AGENTS.md`
§1) — so ctxvm's schema, corpus and conformance gates are the **consumer side** of umpire's output, and
the D18 note's **C2** (key order) and **C3** (canonical form for hash inputs) were both derived from
umpire's behaviour (its `ref` digest is a digest over serialised bytes).

**Operationally:** the model server is the **owner's** to start; it does not survive a reboot while the
MCP does; and the failure mode is "connection refused" on a service that looks alive. That is now a
script — `umpire/scripts/start-llama-server.sh` (hash-verified against the pins, idempotent, with
`--status`/`--stop`) — and the umpire repo's `README-MCP.md` names it in the Prerequisites ✓ (that
section also still named the **v2** calibration while the served artifact of record is **v3**;
corrected).

## 6. Executed agent-doings

- The mechanism was re-read at the committed bytes (`mcp_server.py`, `harness/pins.json`,
  `calibration/umpire-cal-v3.json`, `spec/validate_ledger.py`, `spec/determinism.py`) and the pins'
  hashes were checked against the files on disk ✓.
- The live MCP was exercised today: `health` (200, `{"status":"ok"}`), `pins` (three pins, default
  `qwen3-1.7b`), `calibration_info` (`cal-v1:057a5a35a9d4ec71`, isotonic/1, seed 7), one `decide` (key
  `billing`, calibrated 0.855263), `validate` on the fresh ledger (PASS, 111 checks) and on the fixture
  (PASS, 134 checks), and `replay` on the fixture (BYTE-IDENTICAL) ✓ — and the one honest negative: a
  fresh ledger has no committed baseline, so `replay` reports a divergence ✓.
- The umpire repo's own `README-MCP.md` was corrected (the runner dependency + the script + the artifact
  of record), and the note itself is recorded here.
- Kit: this card + LOG row + the day file + the roadmap's umpire pointer, and (in the umpire repo) the
  README-MCP.md correction + its LOG row + its day file. Nothing pushed; no model bytes or credentials
  added.

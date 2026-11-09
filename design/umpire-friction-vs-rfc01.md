# Umpire friction vs RFC-0.1 — where each friction point stands

**Date:** 2026-11-09. **Workstream:** A2 (adoption prompt §3 A2). No spec file edited per acceptance. Sources: `spec/rfc-0.1/RFC-0.1-xCABI.md`, `reports/RR-W7-20261029.md`, `reports/RR-RFC01-20261030.md`, umpire `00-SPEC.md` §2, `spec/ledger_tools.py:40-54`, `spec/validate_ledger.py:47-54`, `README.md:101-123`.

## R0–R5 at a glance (what landed 2026-10-30/31, D4)

| item | field | status |
|---|---|---|
| R0 | `session.open.schemaVersion "0.1"` boundary | landed |
| R1 | `faultSource intentional_rerun` (resident-valid, priced, never W3 ground truth) | landed, exempt in `ctxvm-core` only for 0.1 |
| R2 | `model_pin` excluded from ref (normative clarification) | landed |
| R3 | `call.meta.providerUsage` optional | landed |
| R4 | `ts` (RFC 3339 ms, every event) + `page.declare.latencyMs` | landed |
| R5 | `page.declare.turn` optional | landed |

R6-R8 (W13 prefix, W15 toolEffect, W14 environmentId) are later additive items; not in R0-R5 scope of this card.

## Friction-by-friction

### F1. Deliberate re-execution — RESOLVED (R1)
Before R1, `ab-demo.ledger.jsonl` replayed with 3 `faultOfResidentPage` violations at seq 2/3/5 (RR-W7 §2.1), because RFC-0 §8 requires faults target stubbed pages and umpire pages nothing out. R1 adds `intentional_rerun`: valid resident-or-stubbed, exempt in v0.1 only, never deduped per (page,source), never W3 ground truth (`RFC-0.1-xCABI.md:12-19`). Today all 4 umpire fixtures replay exit 0, no violations (see RR-IMPL2 §5). The v0 ledger (no schemaVersion) may not use it (`validate_ledger.py:47-52`), preserving the sealed boundary. **No residual.**

### F2. `model_pin` + `seed` in ref — RESOLVED (R2)
Umpire locked decision (00-SPEC §2, `ledger_tools.py:43-45`): both excluded from ref. Had they been included, A/B arms would mint different refs instead of priced re-decides (same `(state, labels)` under new pin/seed). R2 makes this normative (`RFC-0.1:21-24`). Evidence: `ab-demo` same ref `sha256:52114663` ×2 under one pin, then `sha256:abf8ca0d` under another pin — same ref, second slot, fault row. **No residual.**

### F3. A/B ledger 3 violations → 0 — RESOLVED (R1, count)
See F1. The 3→0 drop is the A/B demo's three deliberate rows (two same-pin re-decides + one A/B comparison). **No residual.**

### F4. Clock missing (emitter clock) — RESOLVED (R4)
Pre-R4, emitters had no `ts`. R4 adds optional `ts` (RFC 3339 ms) on every event + `latencyMs` on `page.declare` (`RFC-0.1:32-35`). Hermes already had `api_duration`/`duration_ms`; R4 generalises. Umpire ledgers carry no `ts` (verified: no `ts` key in `fixtures/*.ledger.jsonl`) — still unadopted upstream. Not a spec gap, an adoption gap. See residual F8.

### F5. Provider usage missing — RESOLVED (R3)
`call.meta.providerUsage {inputTokens, outputTokens, cachedInputTokens?}` optional, omitted never null (`RFC-0.1:26-30`). Needed by W4B B3. **No residual.**

### F6. `page.declare` has no turn — RESOLVED (R5)
`turn` optional on `page.declare` (`RFC-0.1:37-39`). **No residual.**

### F7. Version boundary (how a consumer knows v0 vs v0.1) — RESOLVED (R0)
`schemaVersion` on `session.open`; unknown values rejected, sealed v0 rejects v0.1-only lines (RR-IMPL2 §4). **No residual.**

### F8. RESIDUAL: umpire does not emit `ts` (R4) — why it matters
Umpire's ledger has no wall-clock per decision (only `latency_ms` in records sidecar). Ordering across decisions relies on turn index, not `ts`. RFC-0.1 R4 makes `ts` optional, so-omission is conformant — not a spec bug. The friction is downstream: cross-session stream ordering (W14 environmentId + ts) cannot be applied to umpire ledgers today. Options below.

### F9. RESIDUAL: canonical JSON sorted vs Rust struct order — spec ambiguity, not friction
Python/TS canonicalise by sorted keys; Rust roundtrips by struct order. Both parse to same model; byte-identical *lines* across crates not expected (RR-IMPL2 §2). No consumer workaround needed (replay accepts either). **Accept the friction** — document, do not change spec.

## Residuals — options and recommendations (no spec edit made)

### F8 (`ts` absence)
- (a) No spec change — consumer-side rule (e.g., order by turn). Recommend **(a)** for the next card; `ts` is emitterClock, not replay state. Adding mandatory `ts` would break sealed-v0 producers.
- (b) Additive field — would need all five touchpoints (Rust model before `ts`, FIELD_ALLOWLIST, v0.1 schema branch `additionalProperties:false`, `check_version` gate, validator negative, then conformance vector) and an owner decision (D-number). Not recommended now: makes omission non-conformant, counter to the "optional, omitted when unknown" principle.
- (c) Accept friction — true today for conformant traces.

Recommendation: (a) now, revisit (b) if stream-ordering across umpire ledgers is needed (W14). Packet for this residual (top residual): `handoff/packets/P4-ts-umpire.md`.

### F9 (canonical order)
Recommend (c) accept + document in RFC-0.1 compatibility note (already notes v0 validators reject v0.1 lines; sorted vs struct order deserves one line — proposed as packet P5, not applied).

## What umpire still works around (verified by grep, no TODO files outside runner)

- Version-branching in `validate_ledger.py:47-54` (v0 strict `tool_recall` only vs 0.1 adds `intentional_rerun`) — that's the R0/R1 consumer law implemented correctly, not a workaround.
- `latency_ms` in records (not ledger `ts`) — local workaround for ordering, see F8.
- No other `TODO`/`FIXME` in umpire docs/spec beyond `runners/src` (third-party llama.cpp docs). UNKNOWN: GitHub issues/TODOs not exhausted — no remote read per "verify before you build".

## Open questions

- Should umpire emit `ts` under R4? Owner/umpire decision (D-U candidate for A6).
- Should canonical order be normative (sorted) vs struct order? UNKNOWN — owner decision.

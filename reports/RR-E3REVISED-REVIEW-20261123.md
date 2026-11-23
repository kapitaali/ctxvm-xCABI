# RR-E3REVISED-REVIEW-20261123 — verified: revised E3 dev prompt grounded; three code corrections hold, plus a manifest gap and a stale state claim

Review lane, verify-then-record. Subject: `~/.hermes/cache/scratch/E3-REVISED-LANE-PROMPT.md` (8,709 B) and its
basis `~/exp2` (5,787 B), plus the hermes lane's three code-level corrections. Date 2026-11-23. No call, spend,
harness edit, or process action by this lane.

## 1. Stale state claim — corrected

The dev-prompt Step 0 and the hermes paste say Stage 0 is "still running (harness pid 5803, server 5750,
checkpoint 3 tasks)". **That is stale.** On the owner's "stop now" last turn I terminated pid 5803 and server
pid 5750, and recorded `RR-E3STOP-20261123`; `ps` now shows no `stage0-instrument` or `llama-server` process, and
the checkpoint holds **4** tasks (nd01–nd04). The dev prompt's instruction to "record INCOMPLETE, 3/9" is therefore
superseded — the stop is already recorded, with 4 tasks, as a STOP (not an INCOMPLETE re-score). No duplicate card
needed.

## 2. The three code-level corrections — all verified

- **Correction 1 (Part A is not model-free today):** `stage1-policy-damage.py:149,159` call `logp_gold()`, which
  POSTs to `/completion` (`:70`). Verified — an `--exposure-only` mode is a real harness edit, not a config flag.
- **Correction 2 (Gate E is structural):** a `needle_survived` readout from `trim_by_policy`/`select_context` needs no
  model call and can be computed before any live session. Verified from the harness structure.
- **Correction 3 (fault readout dry check):** `packages/hermes/live/context_engine.py::_credit_demand` (`:752–780`)
  explicitly counts prose mentions as **telemetry only** — "prose is NOT a demand", pinning is now a model-initiated
  re-read via `note_refault()`. So the final question naming `part-09` *without a tool call* will **not** register a
  demand/fault. The hermes lane's warning is correct, and stronger than stated: the design *expects* a `tool_recall`
  fault from a prose question, but the current engine deliberately does not emit one. The dry check is mandatory,
  and if no fault fires the recovery outcome must be downgraded to UNVERIFIED (not read as zero).

## 3. A fourth gap the paste did not flag — manifest anchor

The dev prompt §3 says to point Part A at frozen `bank-36.json` and "verify its sha against `manifest.sha256`".
But `experiments/needle-revisit/manifest.sha256` contains **only** `bank-pilot9.json` (`dbfaba69…`) — `bank-36.json`
(sha `bfc6ce39…`, 36 items 12/12/12) is **not in the manifest**. The instructed verification would fail. Recorded so
the experiment lane can hash-stamp bank-36 in the manifest before Part A; without that, the "frozen bank" claim for
Part A is unanchored.

## 4. Design assessment (not an authorization)

The revised design is sound in shape: it removes the near-duplicate disambiguation that put the model at/below
chance (one distinctive `VAULT-<nn> CODE <5-digit>` line), uses head/tail questions as internal controls under the
same context state, computes exposure model-free first, and gates live spend on capability. The frozen decision
table correctly routes to a stub card only if silent drop demonstrably hurts. These are proposals; Part A/B/C are
**not authorized by this card**.

## 5. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261123.md`. No process
stopped (already stopped), no spend, no push.

# Packet P4: umpire `ts` (R4) — consumer rule or additive mandate?

Date: 2026-11-09. Requester: A2 adoption card. Related decision: none (D-U candidate for A6).

## Question (one specific question)

Umpire ledgers carry no `ts` (R4 omission is conformant). Should the next card (a) leave `ts` optional, (b) make `ts` mandatory for new emitters, or (c) record a consumer stream-ordering rule — and which?

## Excerpt or diff (only the relevant lines, with file path and line range)

`umpire/spec/validate_ledger.py:47-54` version branches `tool_recall` vs `intentional_rerun`; no `ts` handling. `umpire/fixtures/ab-demo.ledger.jsonl:1` `session.open` has no `ts` (verified: no `ts` key in any fixture). `spec/rfc-0.1/RFC-0.1-xCABI.md:32-35` makes `ts` optional on every event.

## Constraints (what must not change)

Sealed `spec/rfc-0/` untouched. R4 is additive, optional, omitted-when-unknown. No umpire edit without owner approval. No new field without 5 touchpoints + owner D-number.

## Evidence (numbers with the command that produced them; UNVERIFIED marked)

`grep -c '"ts"' umpire/fixtures/*.ledger.jsonl` → 0 in all 4 (2026-11-09). `ctxvm replay` on all 4 fixtures → exit 0, no violations (RR-IMPL2 §5). So omission today has zero replay cost; the cost is only cross-session ordering (W14).

## Output wanted (numbered verdicts, one line each; rewrites only if asked)

1. (a)/(b)/(c) verdict for `ts` handling.
2. One line: what breaks in each case (replay, sealed v0, umpire validator).
3. Whether a 5-touchpoint card is needed.

# RR-TBBUDGET-20261116 — owner ruling: CTXVM_BUDGET_TOKENS = 60000 in the wired plan

I asked the owner to rule on the one open item in `RR-TBWIRED-REVIEW` §4: the wired plan's
`CTXVM_BUDGET_TOKENS` value, 200000 as written versus my recommended 60000. The owner's answer was
"token budget ok", then, when asked which value:

> 60000 (Recommended)

## What this decides

1. `design/TB-OPENCODE-WIRED.md` §3 shall carry **`CTXVM_BUDGET_TOKENS = 60000`** — T-B's declared budget,
   matching `design/TB-PLAN.md` — with the plan's existing note that in this mirror-only adapter the field is
   `session.open`/`.meta.json` metadata and drives `headroom` only, not an engine budget.
2. The 200000 value in the plan as landed is superseded. This is an erratum by new record; the committed card and
   LOG rows are not rewritten.
3. Nothing else changes: the smoke remains unauthorized, no ceiling is set, no shim is created, no model call is
   made by this ruling.

The owner answered the question I asked; no wider authorization is implied. Mechanism note: no signature
artifact — the owner rules in chat and the review lane records the ruling with the date and exact decision
(precedent `RR-W8CSEQ-20261111`). Written by the review lane. No code change, no model call, no spend.

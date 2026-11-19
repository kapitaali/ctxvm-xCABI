# PROJECT-STATE archive

Created 2026-11-15 by the lane registration of W22 (owner-directed cross-lane edit). Reason: `handoff/PROJECT-STATE.md` sits at its hard ceiling (6,144 bytes checked by `tools/check-handoff.sh`); this file's own rule is **rotation, not compression** — answered or closed entries move here verbatim and the live file keeps a pointer.

Append-only. Never edit a line here; a correction is a new entry.

## Rotated 2026-11-15 — Done items 1–2 (verbatim)

1. W8C replay verified (0.13.21 capture): 81 events, 0 divergences, stdout hash `fe27e29c813c4e06` ×3; `export --turn 12` = 21 slots / 86,569 / 0 stubbed (`RR-W8CREPLAY*`).
2. Representation gap confirmed by the provider's receipts: the derived table is turn-invariant (21 slots / 86,569, turns 0–19) and false about the request (12 pages / 47,805); provider ratio 0.563 ⇒ table false (`RR-SHAPEGAP-20261113`).

## Rotated 2026-11-19 — Done item 2 (verbatim; hermes lane books delta, RR-HBOOKS-20261119)

2. W8D erratum reviewed: 5 inputs verified, 3 arithmetic errors ⇒ hold-once is a no-op (`RR-W8DERRATUM-20261113`).

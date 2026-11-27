# RR-SHADOW-VARIED-PLAN-20261127 — varied shadow-session run plan proposed; owner authorization owed

Review/experiment lane. Date 2026-11-27. No model call, spend, gateway/profile change, or push.

## Plan

Created `design/experiment-runs/SHADOW-VARIED-20261127.md` using the run-plan template. It proposes six
additional anonymous `w8-shadow` sessions on 0.13.37:

- two sessions with many small pages;
- two with medium middle pages;
- two with mixed page sizes.

Each shape uses unique markers and tiny tail reads, requires rc=0, zero shadow write failures, and at least
one persisted drop to count as informative. The existing offline join remains unchanged.

## Why

The current n=3 corpus is one forced-pressure shape: 18 selections, 3 drops, no later observed reuse, no
candidate pins. More varied workloads are needed before interpreting rates. This plan freezes the workloads,
sample target, metrics, stop rules, privacy, and claim ceiling before execution.

## Authorization boundary

The plan is **PROPOSED**, not authorized. It needs an owner ruling for six free-model calls. No model switch
after failure, no prompt broadening to force drops, no named sessions, no gateway/profile/config edits, no
candidate-pin activation, no publish, and no push.

## Applied

This card, the run plan, one four-pipe LOG02 row, a day-file section, and a PROJECT-STATE next-action update.

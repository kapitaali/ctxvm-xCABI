# RR-REVIEWER-PARTC-REVIEW-20261124 — verified reviewer comment on Part C; its three data requests cannot be met from disk

Review lane, verify-then-record. Subject: the external reviewer's comment on the Part C seam (checks 1–5, `page.evict`
follow-up, stub-arm notes), posted by the owner to the hermes lane, which reacted with the bounded fix card routed in
`RR-PARTC-FIX-ROUTE` (scratch `PARTC-FIX-LANE-PROMPT.md`). Date 2026-11-24. No code, model call, spend, or push.

## 1. What I verified about the reviewer's claims

- **Part B result stated by the reviewer matches the books:** middle 8/8 → 1/8, head control 8/8, recovery 0/8
  re-reads from capture bytes (`RR-PARTB-RESULT`, `RR-PARTB-REREAD`). "First time the pager's effect on answers has
  been measured" is consistent with the record — every earlier attempt died at an instrument gate.
- **The seam is scoped as the reviewer says:** opt-in `stubDropped` profile setting, no env channel
  (`test_ambient_env_cannot_enable_the_stub`), default off, originals unmutated, stub = tool name + args + hint only
  (`context_engine.py::_stub_message`, `:1021–1041`), sidecar attests `stubDropped`. Conditions 1/2/5 match; condition 3
  (re-read readout) is experiment-lane and remains UNVERIFIED.
- **`page.evict` in stub mode** is the reviewer's follow-up; already carved out as a separate owner-gated card in the
  routed fix (`RR-PARTC-FIX-ROUTE §3`). Not here.

## 2. The three data requests — none answerable from current disk

The reviewer asked the hermes lane for (a) stub-mode before/after numbers from one synthetic transcript, (b) one real
stub string from a Part B tool call, (c) the first stub session's sidecar. Verified:
- **(a) before/after numbers:** exist only in the scratch fix prompt §1 (off 44,154 → 27,600 at budget 30,000;
  recoverable after 27,717, 3 stubs = 78 nats-tokens). No landed card carries them — they are the reviewer's own
  measurements forwarded in chat, not review-derived. Locator = scratch prompt, not a repo card.
- **(b) real stub string:** not on disk anywhere. `_stub_message` builds content by f-string interpolation of
  `{name}`/`{args}` at call time (`:1041`); no literal stub was ever persisted. That is precisely why the reviewer's
  check 2 (hostile args) is a real defect — the dq scan covered the template, not runtime stubs.
- **(c) first stub session's sidecar:** **does not exist** — the accepted gap from `RR-PARTC-ARM-RESULT` /
  `RR-RETRY-BLOCKED`. No `coverage.json` anywhere carries `stubDropped: recoverable`. Cannot be sent.

So none of the three can be handed over as repo artifacts today. This is recorded as an evidence gap, not papered over.

## 3. Two cross-references the implementing lane must reconcile

- **Version:** the reviewer's preflight says require `plugin.version == 0.13.30`. The routed fix bumps **0.13.30 →
  0.13.31**. After the fix lands, the preflight constant must be 0.13.31 — the fix card already notes a future arm must
  cite the new version; flagged here so the reviewer's text isn't applied literally.
- **Budget caveat:** the reviewer says keep the live profile's 24,000 for comparability and restate Part A's
  24,271–24,414 range — consistent with my earlier record.

## 4. Scope

Reviewer comment is a check-list, not an authorization. The six checks and three notes are already routed to hermes via
`RR-PARTC-FIX-ROUTE` (checks 2/4/5 + hygiene); `page.evict` stays a separate owner-gated card. I wrote none of it. No
hypothesis/cost/paging claim. Applied: this card, an append-only LOG row (four pipes), and a day-file section.

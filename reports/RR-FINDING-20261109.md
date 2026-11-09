# RR-FINDING-20261109 — A5: one finding from existing data

**Date:** 2026-11-09. **Workstream:** A5 (adoption prompt §3 A5). **Condition:** ctxvm `HEAD cd43555`, no new sessions run. `spec/rfc-0/` untouched. No spend.

## Question

Does the existing corpus (plus the owner's everyday capture) contain a finding that is reproducible by one command, meaningful without any paging claim, and safe to publish after redaction?

## Method

Counted duplicate `page.declare` refs (same `logicalRef` within a trace) across corpus m1–m8 and the everyday capture. Duplicate = extra declares beyond the first per unique ref. The single-command reproduction (stdlib only, takes any trace path):

```sh
python3 -c "import json,collections,sys;
refs=[json.loads(l)['page']['id']['logicalRef'] for l in open(sys.argv[1]) if l.strip() and json.loads(l)['type']=='page.declare'];
dup=sum(c-1 for c in collections.Counter(refs).values() if c>1);
print(len(refs), len(set(refs)), dup, round(dup/len(refs),4) if refs else 0)" <trace.jsonl>
```

Outsider reproduction: `python3 <above> <your-trace.jsonl>` and `python3 spec/rfc-0/validate_schema.py <your-trace.jsonl>` + `./rust/target/release/replay <your-trace.jsonl>`.

## Result

- Everyday capture (`ctxvm-dev-7f757529`, Hermes plugin 0.10.5, model `reflection/beam-1.0-501b-a23b:free` via nous, budget 200,000, captured 2026-11-07; 21 turns, 347 declares, 385 hook before / 369 completed): **223 unique refs, 124 extra declares, duplicate rate 124/347 = 35.73%**. Wilson 95% CI for a proportion: **30.9%–40.9%** (deterministic, `random` seed irrelevant — closed form). Content-hash repeats are only 13/347, so most repeats are same call shape with fresh results.
- Corpus m1–m8 (17 traces, 2026-10-22–2026-10-26, models per `corpus/*/provenance.json`; total 118 declares): **7 extra duplicates, pooled 5.93%, Wilson 95% CI 2.9%–11.7%**. Per-trace rates: 0% in 11 traces, 16.7%–50% in 6 (scripted beats that re-read by design).

The gap (everyday 35.7% vs corpus 5.9%) is itself the finding: scripted corpus traces **understate** duplicate calls. The everyday rate is **directional and single-source** (one session, one harness, one model). It is meaningful without paging: xCABI records content-addressed tool-call identity, so a duplicate ledger (same `logicalRef` re-declared) is directly countable — no eviction or cache claim needed. Fault breakdown in everyday capture: `identifier_scan` 329, `tool_recall` 10 (339 total). Corpus: 41 + 21 = 62. Tool-family split (everyday, declares): terminal 109, search_files 69, read_file 57, patch 46, execute_code 45.

## Limitations

- n=1 everyday session; CIs assume binomial draws within that session only. Cross-session/harness generalisation is UNMEASURED / UNVERIFIED.
- Duplicate defined as same `logicalRef`; same-shape calls on changed state are not necessarily wasted work — the rate is a duplicate *ledger*, not a waste claim (no cost-saving claim, law 7).
- No provider token data (`providerReported=false` throughout capture and corpus) — token counts are estimates; this card makes no cost claim.
- Window: single calendar day for everyday capture. Corpus spans six days.

## Redaction audit

Report contains counts only (no session IDs, no refs, no paths beyond repo-relative `corpus/` and `spec/` locators, no file contents, no keys). Tool-family names are aggregate categories. Absolute home-prefix grep in this report and draft: NONE (see Verification).

## Invitation (written, not sent) — for one outside project

> Emit xCABI v0 traces from your harness: `session.open` first, then `page.declare` per tool result (`logicalRef` + `contentHash` + `kind` + `tokens`), `page.render` per turn, `turn.render` with `residentTokens`. Validate locally: `python3 spec/rfc-0/validate_schema.py <trace.jsonl>` (expect PASS) and `./rust/target/release/replay <trace.jsonl>` (expect exit 0). Share counts only (declares, unique refs, duplicate rate via the one-liner above) plus the validator/replay outputs — no raw traces needed. If duplicate rate >10% we will compare counting methods and publish the join; if recording breaks, we will file the gap as a spec ambiguity.

## Verification

- Re-ran the one-liner on corpus m5 (17 declares, 17 unique, 0 dup) and everyday (347/223/124). Absolute home-prefix grep in both files: NONE.
- `bash tools/check-handoff.sh` PASS. `bash tools/run-ci.sh` ALL GATES GREEN exit 0.
- Publication waits on D14 (redaction) + D17 (publication) gates — this card is not sent or posted.

## Conflicts

None beyond A1 header (docs/drafts dirs created as prompted).

# RR-REDACTIMPL-20261119 — G4 implemented: the sidecar assertion record, narrow GO

Lane: hermes. Implementation of `RR-G4GO-20261118` (owner GO, verbatim) via the revised card
`RR-REDACT-20261118` and the routing `RR-G4ROUTE-20261119` / `design/G4-LANE-DEVELOPER-PROMPT.md`.
**No wire byte, no emitter change, no fixture regeneration, no plugin bump, no model call, no spend,
no push.** D17 remains held. `stubText`/`reason` stays DEFERRED (card §6).

## 1. What shipped

| file | role |
|---|---|
| `tools/redaction-block.py` (new) | writer + consumer of `<drop>/redaction.json`; frozen-drop refusal; the §4 contract strings/exits |
| `tools/dq-secret-scan.py` (extended) | additive `--write-redaction --stage … [--policy-id --rules --replaced --logical-ref]`; writes the sidecar **only on SHIP-UNBLOCKED**; `redaction.json` recognized as drop-set shape so a re-scan lints the sidecar's own bytes |
| `tools/redaction-contract-test.py` (new) | the gate step: 24 tests asserting every contract string/exit, the three meta-assertions, writer refusal, scanner integration, kit/gate wiring |
| `tools/fixtures/redaction/` (new) | `fresh-noblock/`, `two-stages/`, `contradiction/` — synthetic, dq-clean, NOT corpus; README names the frozen-write fixture (`corpus/m1`) |
| `tools/verify-capture.sh` (extended) | final step runs the consumer on the trace's drop dir; a contradiction (exit 1) fails the kit loudly under `set -e` |
| `tools/run-ci.sh` + `.github/workflows/ci.yml` | new step "redaction sidecar contract (G4)" — gate 3 after corpus checksums / schema job after m8 checksums; mirror kept |

## 2. Decisions ratified inside the narrow GO (card §3 "or the name you ratify")

- **Name/shape**: `redaction.json` beside `provenance.json`; `{stages: [{stage, policyId,
  ruleSetVersion, replacedFieldCount}], logicalRef, channelsModelled: ["logicalRef"]}`. Stage entries
  **append** (one artifact may be redacted more than once); existing entries are never rewritten.
- **Shipped declaration**: `logicalRef: raw`, `policyId: raw-passthrough`, `ruleSetVersion: w8-dq-v1`,
  `replacedFieldCount: 0` — a declaration of no treatment, not an emitter. `keyed-hashed`/`dropped`
  remain vocabulary only; no code hashes a ref.
- **Raw-ref lint definition** (assertion 3 needs a mechanical count): a ref is keyed only if it matches
  `scheme:(sha256:)?<hex ≥ 32>`; anything else present is raw. For `dropped`, any surviving ref counts
  (it was not dropped). For `raw`, no count is needed. This is a **lint-level shape check**, documented
  as such — no verifier, no chain, no canary.
- **Frozen rule**: any directory under `<repo>/corpus/` (resolved) is refused **before any byte is
  written** — law 5 pins all eight drops, not just m1.
- **Consumer surface**: standalone CLI (`consume DROP_OR_TRACE`) **and** the shared kit
  (`verify-capture.sh`) — the card's "only if that is the agreed surface" resolved to the kit because
  the kit is the shared post-capture path; the step is additive and prints `redaction: unknown` on
  every existing drop.
- **Scanner stamp**: the `scanToolSha256` self-hash changes because the scanner file changed; the
  stamp *mechanism* and the `w8-dq-v1` zero-match wording are unchanged. `test_dq_scan.py` derives the
  hash dynamically and stayed green (216-test suite unchanged).

## 3. The consumer contract, as gated (card §4)

| case | printed | exit |
|---|---|---|
| block absent (incl. all frozen m1–m8) | `redaction: unknown` | 0 |
| block present | `redaction: declared` + `stage=<s> policy=<id> rules=<v> replaced=<n>` per stage + `logicalRef: <enum>` + `channels modelled: logicalRef` | 0 |
| declares keyed-hashed/dropped, raw refs present | `redaction: inconsistent — declared <value>, <n> raw refs present` | 1 |
| unreadable / missing required fields | `redaction: invalid — <reason>` | 2 |

Meta-assertions, all gated: (1) absence never prints the word `none` (word-boundary check); (2) no
output line contains `verified` or claims the artifact *is* redacted; (3) the contradiction exit is
non-zero and names both the declared value and the raw-ref count. Invalid cases covered: broken JSON,
non-object, empty/missing stage list, missing stage field, unknown stage, bad/missing enum, negative
count, float count, unreadable trace under a non-raw declaration, missing drop.

## 4. Verification (every line of the card §8 bar)

- **Gate**: `bash tools/run-ci.sh` unpiped, ambient `CTXVM_*` enumerated and unset, 2026-11-19 →
  **rc=0 ALL GATES GREEN**, including the new step. Totals: ts 24 + 62 + 46 + 14; python 216 + 8 + 66
  (unchanged — the scanner extension broke nothing); schema 682 checks (677 lines / 27 fixtures +
  5 negatives); export round-trip + hub byte-identity green.
- **Contract step**: `python3 tools/redaction-contract-test.py` → **Ran 24 tests, OK, rc=0**.
- **Red-before proof** (the guard can fail): substituting `redaction: none` for `redaction: unknown`
  in the consumer → contract step **rc=1** (`AssertionError: 'redaction: none\n' != 'redaction: unknown\n'`);
  restored → rc=0. Logs kept durably (§5).
- **Kit smoke**: `OUT=<scratch> bash tools/verify-capture.sh corpus/m1/tracer-healthy.jsonl` → rc=0,
  new step prints `redaction: unknown`, `VERIFY-CAPTURE DONE` (full stack: replay/profile/export/metrics/sim).
- **Frozen refusal**: writer CLI on `corpus/m1` → exit 2, `write refused: frozen drop (law 5)`;
  sha256 of every m1 file identical before/after; `git status --short corpus/` empty; no
  `redaction.json` created. Scanner-level attempt also exit 2 with m1 digests unchanged (gated).
- **DQ scan on a fresh non-frozen fixture dir**: exit 0, `verdict: SHIP-UNBLOCKED`, `dq-scan list
  w8-dq-v1` wording unchanged, sidecar written with the four fields per stage, consumer prints
  `channels modelled: logicalRef` (gated). CANNOT-SHIP writes no sidecar (gated).
- **deepseek bar** (card §8 bullet 1, W22 carry-over): no adapter file touched (`git diff --stat
  packages/` empty); the gate's dsh suite ran green (14 tests) — "unchanged" satisfied.
- `bash tools/check-handoff.sh` → ALL PASS; `bash tools/git-hygiene.sh` → OK (at close).
- Sweeps over the 907 added lines: CJK 0, secret shapes 0, `/home/` 1 — the hit is the sweep-pattern
  mention in this line, not a path disclosure (fixture paths are repo-relative).

## 5. Durable evidence

`~/.local/state/ctxvm/w8-runs/g4-impl-20261119/`: `g4-red.log` (failed guard proof), `g4-green.log`
(24 tests OK), `g4-kit.log` (kit smoke), `checksums.sha256`. Gate log `/tmp/ci-g4.log` is transient;
the totals above are the durable record.

## 6. Refused / deferred, honored

No keyed-hash emitter; no wire field (spec/ untouched, `ts` order untouched); no verifier/tamper/canary
claim; no backfill (writer refuses corpus/); no release action (D17 held); no plugin version bump, no
sync, no gateway restart (no plugin code changed). `stubText`/`reason` placement **deferred, owner
decision owed**; seeded-canary on the books; consent/release card bound at D6/D17.

## 7. Repro

```
python3 tools/redaction-block.py consume tools/fixtures/redaction/two-stages      # declared, exit 0
python3 tools/redaction-block.py consume tools/fixtures/redaction/contradiction   # inconsistent, exit 1
python3 tools/redaction-block.py write corpus/m1 --stage capture                  # refused, exit 2
python3 tools/redaction-contract-test.py                                          # 24 tests
bash tools/run-ci.sh                                                              # ALL GATES GREEN
```

## 8. Open after this card

- Review lane: verify + record this card (the routing card says review records, does not re-implement).
  G4's Done condition (`RR-G4GO`: an `RR-REDACT*` card with passing kit + CI) is mechanically met by
  this card; the review verdict is the record's closing step.
- Owner: `stubText`/`reason` ruling (deferred in writing, `RR-REDACT` §6) — not folded in.
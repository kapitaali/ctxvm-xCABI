# RR-REDACTIMPL-REVIEW — verified: G4's done-condition is mechanically met

Review lane, verify-then-record. Subject: `9e755d4` (19-file implementation) and `c67fb76` (PROJECT-STATE delta),
plus the hermes lane's `reports/RR-REDACTIMPL-20261119.md`. Date 2026-11-19. This lane wrote no `tools/**` byte,
made no model call, no spend, and no push.

## 1. Verdict

**G4's done condition is met**, as the roadmap defines it (`design/ROADMAP-OPENCODE-LANE.md:884`): an implementation
card `RR-REDACT*` exists *with a passing kit + CI gate*. I re-derived every load-bearing claim rather than relying on
the pasted summary. The roadmap box at `:881` is still unchecked — it is now tickable with the commands below; I
leave it to the lane/owner that owns that plan of record (design placement is the owner's), as I did with H13.

## 2. Evidence re-derived

| claim | command | result |
|---|---|---|
| two commits landed | `git log --oneline -5` | `c67fb76` → `9e755d4` → `21a12a5` (mine) → … |
| 19-file scope | `git show --stat --oneline 9e755d4` | writer, scanner hook, 24-test contract file, `run-ci.sh`, `ci.yml`, `verify-capture.sh`, 8 fixture files, card + LOG + day file, one developer prompt |
| contract 24/24 | `python3 tools/redaction-contract-test.py` | `Ran 24 tests … OK`, `CT_RC=0` |
| frozen refusal | `python3 tools/redaction-block.py write corpus/m1 --stage capture --replaced 1` | `WRITE_RC=2`, `write refused: frozen drop (law 5): corpus/m1`; `corpus/m1/checksums.sha256` digest unchanged; `git status corpus/` → 0 entries |
| kit smoke | `bash tools/verify-capture.sh corpus/m1/opencode-echo.jsonl` | `SMOKE_RC=0`, prints `redaction: unknown` |
| CI gate | `bash tools/run-ci.sh` unpiped, `CTXVM_*` cleared, re-run by me | `GATE_RC=0`, `[ctxvm-ci] ALL GATES GREEN` |
| mirror wired | `grep -n redaction tools/run-ci.sh .github/workflows/ci.yml` | `run-ci.sh:170` runs the contract test in gate 3; `ci.yml:152–153` mirrors it in the schema job |
| kit + hygiene | `check-handoff.sh`, `git-hygiene.sh` | ALL HANDOFF CHECKS PASS; OK, shared index agrees with HEAD |
| exec bits restored | `git ls-files -s` + `stat` | `run-ci.sh` and `verify-capture.sh` both `100755` in the index and `755` on disk — the `--cacheinfo 644` defect is genuinely fixed |
| red-before proven | `g4-red.log` evidence | substituting `none` for `unknown` makes `test_absent_is_unknown_exit0_and_never_none` and two other tests FAIL with `AssertionError: 'redaction: none\n' != 'redaction: unknown\n'` |
| evidence durable | `ls ~/.local/state/ctxvm/w8-runs/g4-impl-20261119/` | `g4-red.log`, `g4-green.log`, `g4-kit.log`, `checksums.sha256` |
| sweeps clean | added lines of `9e755d4` | 0 CJK characters, 0 secret-shaped or absolute `/home/` strings |
| PROJECT-STATE cap | `wc -c` | 6,116 / 6,144 B — 28 B headroom |

## 3. Refusals honored

The card's §6 and the narrow GO (`RR-G4GO-20261118`) are matched by what was actually shipped: no keyed-hash emitter
(the enum is vocabulary only), no wire field (`spec/` and `ts` order untouched), no verifier/tamper/canary claim
(the consumer prints "assertion, not verifier"), no backfill (writer refuses frozen drops — proven above), no release
action (D17 held), no plugin bump/sync/restart (no plugin code changed). `stubText`/`reason` placement and the
seeded-canary test remain explicitly **deferred** — the owner's ruling is still open. No cost, paging, determinism or
model-quality claim.

## 4. Applied by the review lane

This card, an append-only LOG row (four pipes), and a day-file section. The G4 roadmap box and the
`RR-REDACT-20261118.md` draft status line were **not** edited here — both are other lanes'/owner's property; this
card is the verification that entitles whoever owns them to close them.

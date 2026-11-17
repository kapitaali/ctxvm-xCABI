# RR-W22C-REVIEW — acceptance #4 ruled DONE on a baseline-controlled normalized diff

Review lane, verify-then-record and ruling. Subject: the dsh lane's handoff 12 execution result (2026-11-17)
and acceptance #4 in `reports/RR-W22-20261115.md`. No code change, no model call, no spend by this lane.

## 1. Ruling

**Acceptance #4 is DONE**, with the claim ceiling stated in the finalized card text: identity after masking
volatile ids/times **and** model-output nondeterminism that appeared in both OFF arms, therefore not
attributable to the adapter. This is **not** a raw byte-identity claim. The handoff's own precondition — that the
OFF-vs-OFF baseline must pass — is met, so the ON-vs-OFF pair is interpretable.

The reasoning, briefly: the acceptance asks whether the adapter changes what the model sees. Two OFF arms with
the plugin disabled differ from each other in exactly the same model-owned fields (reasoning text, `responseId`,
`thinkingSignature`, token counts, stream timings) as the ON arm; once volatile and model-owned fields are
masked, OFF1 ≡ OFF2 and ON ≡ OFF1. The ON arm alone wrote a trace. That is the mirror-mode claim with a
controlled baseline; nothing in the evidence points to a model-visible effect of the adapter.

## 2. Evidence I re-derived

| claim | how | result |
|---|---|---|
| three sessions exist | `find ~/.dsh/sessions -type d -name <id>` | ON `7efca72f…`, OFF1 `2d38d7f0…`, OFF2 `e3cd6a82…` — all FOUND |
| each log has 20 lines | `zstd -dc … | wc -l` | **20, 20, 20** |
| raw ON/OFF1 differ | `cmp` of decompressed logs | **DIFFERS**, as expected |
| baseline + pair identity | my **own** normalizer (independent of the handoff's jq), masking ids/times and model-owned fields across the whole tree | **OFF1 vs OFF2 diff exit 0 (0 lines); ON vs OFF1 diff exit 0 (0 lines)** |
| ON arm trace | parse the named trace | exists, `0600`, 5 events: `session.open`, 2 × `page.declare`, `turn.render`, `call.meta` |
| validation | `spec/rfc-0.1/validate_schema_v0_1.py` | **exit 0**, OK: all checks passed |
| replay | `rust/target/release/replay` | **exit 0**, events 5, `divergences: []`, `violations: []` |
| gate | my own re-run during this review | rc=0 **ALL GATES GREEN** (`/tmp/opencode/20261117-planc-ci.log`, ambient `CTXVM_*` cleared) |

## 3. What the record must say — and what it must not

- **Say:** DONE with a baseline-controlled normalized diff; two OFF arms; model-output nondeterminism in both OFF
  arms; one private trace on the ON arm; validator and replay exits; the date.
- **Do not say:** raw byte identity across two live sessions, model-output determinism, a cost claim, or that the
  adapter was proven to have no effect on model quality. The masking is exactly what makes the comparison
  interpretable, and it must be named.
- **Documentation defect in the dsh lane's workspace** (their file, not edited here): handoff 12's title and
  opening still say *"prepared, NOT run"* and *"no pair was run"*, while §"Execution result" records the three
  completed runs. Their file should be corrected in their own lane.

## 4. Applied

- `reports/RR-W22-20261115.md` acceptance #4 finalized: BLOCKED → DONE with the qualified text.
- This card + an append-only LOG row (four pipes) + a day-file section record the ruling and the evidence.
- Plans: A landed (`a2669c9`), B landed (`b701cc2`), **C now closed by this ruling**, D remains with the other
  lane's file owner. No LOG row of another lane was rewritten.

Kit: `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK.

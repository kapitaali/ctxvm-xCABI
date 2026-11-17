# RR-TBDSHCOUNTER-FIX-20261117 — verified: counter defect root-caused and fixed (workspace driver only)

Review lane, verify-then-record. Subject: dsh handoff 19. No model call, no re-run, no repo write, no spend by
this lane. The fix lives in the dsh workspace driver, not in any repo file.

## 1. Verdict

**The fix is verified and accepted. Root cause H1 (double `session-` prefix) is proven; H2 (flush race) is
unsupported and not asserted.** This closes the UNVERIFIED note in `RR-TBDSHCOUNTER-20261117` §2 and corrects the
"competing hypotheses" wording in `RR-TBDSHFULL-20261117` §3.1. No outcome was lost — the completed run's external
counts remain its evidence — but the CEILING control would now actually fire.

## 2. What I re-derived

| claim | how | result |
|---|---|---|
| old glob empty | ran `counter-check.sh` in the run dir | `ls -td …/session-"session-9fd…"` → `[]` — reproduced |
| fixed glob resolves | same | `ls -td …/"session-9fd…"` → the workspace-named session dir |
| count | same dry-run | `CALLS=581` against the preserved session log — matches the handoff and my earlier independent count |
| self-test | same | `forced CALLS=581 → SELFTEST=[none]`; `forced 0 → COUNTER_SELFTEST_FAIL prompt 1: CALLS=0 but direct=581` — fires only on a false zero |
| fix in driver bytes | `grep -n` on `driver.sh` | line 54 `SESSION_DIR=$(ls -td ~/.dsh/sessions/*/"$SID" …)`; `SELFTEST` at 60/66/73/76; `CEILING=588` unchanged |
| syntax | `bash -n driver.sh` | OK |
| suite / kit | re-ran | 15 tests / 14 pass / 0 fail / 1 named skip; `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK |
| cross-reference | grep handoff 18 | its correction note now says root cause PROVEN as H1 and points to handoff 19 |

No hardcoded path; no reuse of 198/579/451; no retry-until-green introduced. The `CEILING` row shape is unchanged.

## 3. Scope and carry-forward

- The accepted COMPLETE / CAPTURE-FIDELITY PASS verdict in `RR-TBDSHFULL-20261117` stands untouched. Nothing was
  re-run, and no new count replaces the externally watched 581.
- The self-test is the important addition beyond the one-line fix: a silent zero now stops the run rather than
  producing a false "no ceiling issue". Keep it in any future driver copy.
- No new task is authorized by this fix. A re-run would need a fresh owner authorization and ceiling
  preregistration; no cost, paging, H3/H4, eviction, determinism, or model-quality claim follows from the fix.

Kit/gate were green at the checks above; this card changes no gate input.

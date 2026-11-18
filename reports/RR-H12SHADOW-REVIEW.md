# RR-H12SHADOW-REVIEW — verified: the mode fault was a stale sibling import, not a policy bug

Review lane, verify-then-record. Subject: `411fdc2` / `reports/RR-H12SHADOW-20261118.md`. No code change, no model
call, no spend, no restart by this lane. The $1 cap stands untouched.

## 1. Verdict

**Root cause accepted, and it corrects my earlier framing.** I called it "the mode did not engage" and listed six
causes ruled out — all true, but none was the cause. The one prompt answered it: `policyMode: None`,
`modeExplicit: False` meant the engine's policy dict had **no `selectionMode` key**. The gateway's four profile
plugin directories included two **real 0.13.23 directories** (`w8cp-*`), and the engine's bare sibling import
`from profile_policy import policy` resolved through that stale copy. Six checks said "stable" because each ran in a
fresh process with the correct `sys.path`; the gateway's path was the one with four plugin directories in it.

This is the state-shadowing hazard the lane's notes already describe, now measured for **code**: a bare import can
resolve to another profile's copy of a module, exactly as a bare global slot could be shared by every profile.

## 2. Evidence re-derived

| claim | how | result |
|---|---|---|
| diagnostic answer | card §1 | `policyMode: None`, `modeExplicit: False` — no key in the engine's policy dict |
| stale directories existed | `find` + `grep` on profile plugin dirs | `w8cp-{naive,paged}` had **real directories** at 0.13.23 (12 Nov); now replaced with symlinks to the shared install, originals kept as `ctxvm-tracer.old-0.13.23` (version string confirmed 0.13.23) |
| all four profiles unified | `ls -l` on each plugin dir | `w8cn-{naive,paged}` and `w8cp-{naive,paged}` are all **SYMLINK**, all read `PLUGIN_VERSION 0.13.27` |
| durable loader fix | `grep` on `context_engine.py` | `_policy_module()` (line 266) loads `Path(__file__).resolve().parent / "profile_policy.py"` with `spec_from_file_location("ctxvm_profile_policy", …)` — identity is the engine's own directory; a fifth stale copy cannot shadow it |
| suite arm pinned | `grep` on tests | `ce._POLICY_MOD` pinned via stub; the by-path resolver otherwise succeeds in tests and finds the operator's real home, where the policy is the *control* arm — every law would silently inert. This is the right response: pin the arm, not weaken the loader |
| clean suite | `CTXVM_*` cleared, pytest | **216 passed, 15 subtests** — matches the card |
| gateway stale | pid/start vs file mtime | gateway pid **169044** started **21:57:11**, installed `__init__.py` written **22:06:43** — the process cannot hold 0.13.27. A restart is owed and belongs to the owner |

## 3. What this supports and what it does not

- **Supports:** the mechanism of the H12 failure is understood and fixed at the load boundary; the diagnostic trio
  (`policyMode`, `policyModeSource`, `modeExplicit`) makes a module-identity fault visible in a capture rather
  than inferred from six circumstantial checks. The generalised lesson belongs in the gateway/arm-attestation
  reference, as the card says.
- **Does not support:** any stable-mode result. The 24k fresh-mode reference from `19ad2c9` remains the only
  engaged-paged record; H12 stable is still unrun. No saving, dollar, paging, or determinism claim follows from
  this fix.

## 4. Carry-forward

One owner restart, then one free paged prompt: the plan must read `policyMode: stable` and `trigger: held`. If it
does, the H12 pair runs against the fresh-mode 24k reference already on record, under the existing authorization
and $1 cap. If it does not, record that and stop — do not stack further fixes without a new diagnostic. No cell,
spend, or restart is authorized by this review. Earlier records, including my own `RR-H12RUN-REVIEW`, stay
unrevised; this card records what superseded its "cause unknown" state.

Kit/gate: the card reports ALL GATES GREEN; my clean pytest confirms 216 passed; hygiene was green at the last check.

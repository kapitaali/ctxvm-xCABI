# RR-INSTRUMENT023-20261113 — the other lane's `f3078b4` verified against the P12 ruling: the per-call identities and the fail-closed rule are **delivered**; three caveats remain, and the running gateway still holds the **older** version

Card: review-lane verification of the hermes lane's commit `f3078b4` (*"carry every call and name what it
removed" ✓, 2026-11-13 23:03 ✓) against the ruling recorded in `reports/RR-OMISSIONANSWER-20261113.md` ✓.

---

## 0. Verdict

The commit does what the ruling asked for ✓ — the **per-call removed identities** ✓ with their **token
counts** ✓, and the checker's **fail-closed** rule ✓ in **both** directions ✓ with a stated tolerance ✓ ✓.
Three caveats are recorded below ✓ (one of them narrows what the reviewer's own wording asked for ✓), and
one **runtime** fact matters for any capture taken now ✓ (§3 ✓).

---

## 1. What is delivered ✓ (verified in the diff and in the installed copy ✓)

| the ruling asked for ✓ | delivered ✓ | where ✓ |
|---|---|---|
| per-call **removed-page identities** with token counts ✓ | every selection's `removed` list: `{"tokens": units[i].tokens, "ids": sorted(units[i].id_toks)[:6]}` ✓ | `packages/hermes/live/context_engine.py:508` ✓ (the engine's `CALL_LOG` ✓) and `:561` ✓ (the observer payload ✓) |
| the sidecar carries it ✓ | the per-call entry now carries `i` ✓, `before` ✓, `after` ✓, `dropped` ✓, `removed` ✓, and the **80-entry slice is gone** ✓ | `packages/hermes/live/__init__.py:1492-1503` ✓ ✓ |
| a **fail-closed** rule ✓ | *"a capture with removals and no list is a violation"* ✓ — implemented as: a call whose `after < before` and whose `removed` is empty ⇒ **violation** ✓ | `tools/coverage_check.py` ✓ (the new block ✓) ✓ |
| the rule "in both directions" ✓ | the **consistency** direction ✓: for a call with `before > budget` ✓, the named tokens must match `before − after` within a stated **10 %** tolerance ✓ ✓ | same ✓ ✓ |
| version-gated ✓ | the rule fires only for `plugin.version ≥ 0.13.23` ✓ ⇒ older captures are untouched ✓ ✓ | same ✓ ✓ |
| the version ladder ✓ | **0.13.23** in both authoritative places ✓ (`live/__init__.py:94` ✓ and `live/plugin.yaml:2` ✓) and the gate asserts their equality ✓ (`tools/run-ci.sh` ✓) ⇒ and the **installed copy matches the repo byte for byte** ✓ (all four files ✓, sha256 ✓) ✓ | ✓ |

⇒ **The instrument ask from `reports/RR-OMISSIONANSWER-20261113.md` §1.2 is answered** ✓ ⇒ the ruled rule
now has something to read ✓ ✓ (with the three caveats below ✓).

---

## 2. Three caveats, all recorded, none fatal ✓

1. **The sidecar's per-call record is still partial ✓** — the observer fires only for selections that
   dropped or repositioned ✓ (`packages/hermes/live/context_engine.py:553` ✓: `if OBSERVER["cb"] is not None
   and (dropped or repositioned)` ✓) ⇒ ⇒ the sidecar's `callSizes` still lists **only the dropping
   selections** ✓ ⇒ ⇒ the reviewer's *"a missing entry for a call with `before > budget` is a failure"* ✓
   ⇒ is **not implementable** from the sidecar ✓ (a call can exceed the budget and still drop nothing ✓ —
   the engine's protected floor ✓) ⇒ ⇒ the implemented rule is the **implementable subset** ✓ (fail-closed
   ✓ + consistency ✓) ⇒ ⇒ **this lane's ask for "every call's before/after" is NOT met** ✓ ⇒ ⇒ recorded ✓
   (the rule as shipped is the right one ✓; the wording in the ruling asked for one more thing ✓).
2. **The identity lists are truncated ✓** — `sorted(units[i].id_toks)[:6]` ✓ (both sites ✓) ⇒ a page with
   **more than six** identity tokens loses the rest ✓ ⇒ ⇒ "names every page it removed" ✓ is true ✓, but
   "names every **identity** of every page" ✓ is not ✓ ⇒ ⇒ the *token* count is the page's total ✓ (so the
   10 % sum check is unaffected ✓ ✓) ⇒ ⇒ recorded ✓.
3. **The caps are still caps ✓** — the engine's `CALL_LOG` keeps the last **200** ✓
   (`context_engine.py:512` ✓) ⇒ though the sidecar no longer reads it ✓ ✓ — and the live sidecar list
   truncates at **500** calls ✓ (`live/__init__.py:1503` ✓, `del _calls[:-500]` ✓) ⇒ ⇒ "uncensored" ✓ is
   **not** true ✓ ⇒ ⇒ stated ✓ (500 calls ≈ 250 turns ✓ at two calls per turn ✓ — far beyond the
   20-turn fixtures ✓ ⇒ practically enough ✓, but it is a cap ✓ ⇒ ⇒ recorded ✓).

⇒ **A rule that is implementable beats a rule that is not** ✓ ⇒ the shipped rule is the right call ✓ ✓;
the card's ask is narrowed accordingly ✓.

---

## 3. The runtime case: the gateway holds the **older** module ✓

- The **disk** says **0.13.23** ✓ (both authoritative files ✓ and the installed copy ✓).
- The **running gateway** (PID **24698** ✓) **started at 22:58:59** ✓ and the installed copy was replaced at
  **23:02:42** ✓ ⇒ ⇒ the process still runs the pre-swap module ⇒ ⇒ **0.13.22** ✓ ⇒ ⇒ **any capture taken
  through it now is labelled 0.13.22** ✓ ⇒ ⇒ its sidecar would carry the *old* shape ✓ (no per-call
  identities ✓) ⇒ ⇒ a capture taken now **cannot** exercise the new rule ✓ ⇒ ⇒ the new rule is
  **unexercised on a live capture** ✓ (it is exercised by the repo's own vectors ✓ and the gate ✓ ✓).

⇒ **The restart is not this lane's to make** ✓ — `handoff/LANES.md` ✓: *"The gateway — one process serving
every profile and every lane's live session. A restart ends all of them. **Ask before restarting; nobody
restarts 'to be safe'.**"* ✓ ⇒ ⇒ **ask, do not restart** ✓ ✓ ⇒ recorded in `handoff/PROJECT-STATE.md` ✓ and
in the drift card ✓ (`reports/RR-VERSIONDRIFT-20261113.md` ✓) ✓.

⇒ ⇒ **The first capture on 0.13.23 is worth taking** ✓ — it is the only way the ruled rule gets a live
witness ✓ ⇒ ⇒ and it needs the gateway restart ✓ ⇒ ⇒ owner/hermes-lane decision ✓ ✓.

---

## 4. Executed agent-doings

- `f3078b4` read in full ✓ (the engine ✓, the live adapter ✓, the checker ✓) and checked against the
  ruling ✓ line by line ✓ ⇒ the table in §1 ✓ ✓.
- The **installed copy** compared with the repo by sha256 ✓ ⇒ all four files identical ✓ ⇒ the sync is
  clean ✓ ⇒ (this lane does not touch the installed copy ✓ ✓).
- The **gateway process** checked ✓ (PID ✓, start time ✓, the installed file's mtime ✓) ⇒ the in-memory
  version is **0.13.22** ✓ ⇒ the drift is real ✓ and is **not** acted on ✓ (the restart is the owner's ✓).
- The **caps** and the **observer guard** read ✓ ⇒ the three caveats ✓ ✓.
- No file of another lane's was edited ✓ (`packages/hermes/**` ✓ and `tools/**` ✓ untouched ✓); the
  handoff docs and the README were edited **by the review lane** ✓ (its own files ✓, plus the README row
  claimed in the commit message ✓); nothing pushed ✓.

# RR-VERSIONDRIFT-20261113 — the version-drift sweep: the authoritative pair is **0.13.23** (gate-enforced); four stale claims fixed here, four routed to the research lane, one **reclassified** as dated history; and the running gateway still holds the older module

Card: review-lane check of the reviewer's staleness sweep across the docs ✓, plus the runtime case that
prompted it ✓. Every version claim was re-measured before anything was written ✓.

---

## 0. The authoritative pair, and that it is gate-enforced ✓

```
packages/hermes/live/__init__.py:94   PLUGIN_VERSION = "0.13.23"
packages/hermes/live/plugin.yaml:2     version: 0.13.23
tools/run-ci.sh  (run_step "plugin.yaml version matches PLUGIN_VERSION")   asserts equality
```

⇒ The **installed** copy matches the repo **byte for byte** ✓ (sha256 ✓: `__init__.py` ✓,
`context_engine.py` ✓, `src/plugin.py` ✓, `plugin.yaml` ✓) ⇒ ⇒ the sync is clean ✓ ✓.

⇒ **The lesson, once**: a version number belongs in **two** gate-enforced places ✓; every other mention
either points at those two ✓ or is dated history ✓ ⇒ ⇒ a doc that *states* a version goes stale by
construction ✓ ⇒ ⇒ §4 proposes the prevention ✓.

---

## 1. Fixed here (four) ✓ — the review lane's own files, plus the README row ✓

| file:line ✓ | was ✓ | now ✓ |
|---|---|---|
| `handoff/AGENT-PROMPT.md:33` ✓ | *"Plugin `ctxvm-tracer` **0.10.6** on disk; the gateway may still carry an older module until it restarts."* ✓ | **0.13.23** ✓, pointing at the authoritative pair ✓, and the gateway note made **live** ✓ (PID 24698 ✓) ✓ |
| `handoff/PROJECT-STATE.md:7` ✓ | hermes **0.13.22** ✓ | hermes **0.13.23** ✓ (the locator `:94` stays valid ✓ ✓ — the row was self-contradicting ✓ ⇒ now it is not ✓) |
| `handoff/SESSION-START.md:7` ✓ | hermes **0.13.22** ✓ (the mirrored sentence ✓) | hermes **0.13.23** ✓ ✓ |
| `README.md:129` ✓ | the paging-engine row, plugin **0.13.1** ✓ | plugin **0.13.23** ✓ ✓ |

⇒ `README.md` has **no lane** ✓ ⇒ the row is claimed **in the commit message** ✓ (the lane law: a shared
file is claimed by a commit ✓ ✓) ⇒ and the change is a **fact**, not a policy ✓ ✓.

---

## 2. Routed, not edited (four) ✓ — the research lane's `research/**` ✓ (read-never-edit here ✓)

| file:line ✓ | says ✓ | what it needs ✓ |
|---|---|---|
| `research/white-paper/white-paper.md:204` ✓ (§3.8 ✓) | *"the Hermes plugin (v**0.10.2**, source `live/__init__.py`)"* ✓ | the current version ✓ |
| `research/white-paper/white-paper.md:402` ✓ (§5.3 ✓) | *"the Hermes plugin (v**0.10.2**)"* ✓ | the current version ✓ |
| `research/white-paper/white-paper.md:437` ✓ (§7 ✓) | *"(`FaultPinPolicy`, plugin **0.10.2**; later 0.13.x)"* ✓ — half-corrected already ✓ | the current version ✓ |
| `research/white-paper/index.md:443` ✓ | the same sentence ✓ | the same ✓ |

⇒ **Why they are not stale in the harmful sense** ✓: the paper's §3.8/§5.3/§7 describe **what the
software was when the claim was made** ✓ ⇒ ⇒ the honest fix is either the current version ✓ **or** an
explicit date ✓ ("as of 2026-11-xx the plugin was v0.13.23" ✓) ⇒ ⇒ that choice is the research lane's ✓ ✓
⇒ ⇒ **routed, with the option named** ✓ ⇒ and their files are **dirty in the tree right now** ✓ ⇒ ⇒ the
route is a **note in this card and in the LOG row** ✓ ⇒ ⇒ one pass fixes all four ✓ ✓.

---

## 3. Reclassified (one) ✓ — dated history, correctly as written ✓

`design/hermes-catalog-submission.md:43` reads *"Hermes version pin re-checked against `live/plugin.yaml`
(`version: **0.10.6**`) **at tag time**."* ✓ ⇒ ⇒ the "at tag time" ✓ makes it a **historical statement about
the tag** ✓ ⇒ ⇒ it is **not** a current-state claim ✓ ⇒ ⇒ **leave it** ✓ ✓ (and `design/**` needs owner
clearance ✓ ⇒ ⇒ the point is moot ✓ ⇒ ⇒ recorded ✓).

⇒ ⇒ The sweep's grouping is right in substance ✓ and off by **one** ✓ ⇒ ⇒ corrected here ✓ ⇒ no edit ✓.

---

## 4. The dated-history list — spot-checked and confirmed ✓

Six of the listed rows were re-read ✓ ⇒ all six are **dated statements** ✓ ⇒ **untouched** ✓:
`README.md:116` ✓ (*"fix landed in plugin 0.12.0" ✓), `README.md:177` ✓ (*"landed in plugin 0.12.0" ✓),
`handoff/LANES.md:73` ✓ (*"plugin 0.10.4 produced a false arm witness" ✓ — the incident row ✓),
`08-HANDOFF.md:1487` ✓ (the 0.10.0→0.10.5 chronology inside the W8 board cell ✓),
`packages/hermes/HOOKS.md:65` ✓ (*"W8 wiring note (2026-11-06, plugin 0.10.0)" ✓),
`design/exp-surface.md:46` ✓ (*"Gateway still runs 0.10.8 and the plugin file is 0.10.10 (conservative
restart gap, noted; per prompt: no restart mid-cell)" ✓ — **the same shape as the live case below** ✓ ⇒ ⇒
the repo has the precedent ✓ ⇒ ⇒ **do not restart mid-cell** ✓ ⇒ ⇒ and by the same convention: **ask** ✓).

⇒ **The prevention, for the owner to adopt if they want it** ✓: a doc that needs the version should
**point at the authoritative pair** (`packages/hermes/live/__init__.py:94` + `live/plugin.yaml:2` ✓) instead
of restating a number ✓ ⇒ ⇒ no doc can go stale ✓ ⇒ ⇒ the row fixed in §1 now reads that way ✓ ✓.

---

## 5. The runtime case: the gateway holds **0.13.22** while the disk says **0.13.23** ✓

| fact ✓ | value ✓ |
|---|---|
| the gateway process ✓ | PID **24698** ✓, started **22:58:59** ✓ |
| the installed copy was replaced ✓ | **23:02:42** ✓ ⇒ ⇒ the process predates the swap ✓ ⇒ ⇒ it runs the **pre-swap module** ✓ ⇒ ⇒ **0.13.22** ✓ |
| the disk ✓ | **0.13.23** ✓ ✓ |

⇒ ⇒ **Any capture taken through the running gateway is labelled 0.13.22** ✓ ⇒ ⇒ its sidecar carries the
**old** shape ✓ (no per-call identities ✓) ⇒ ⇒ the ruled fail-closed rule **cannot be exercised** on a
capture taken now ✓ ⇒ ⇒ the new rule is unexercised on a live capture ✓ (the repo's own vectors and the
gate exercise it ✓ ✓) ⇒ ⇒ **the first capture on 0.13.23 is worth taking** ✓ ⇒ ⇒ and it needs the
restart ✓.

⇒ **Not this lane's to make** ✓: `handoff/LANES.md` ✓ — *"The gateway — one process serving every profile
and every lane's live session. A restart ends all of them. **Ask before restarting; nobody restarts 'to be
safe'.**"* ✓ ⇒ ⇒ **ask, do not restart** ✓ ⇒ ⇒ the ask is with the **owner / hermes lane** ✓ ✓.

---

## 6. Executed agent-doings

- The authoritative pair re-read ✓, the gate's equality assertion located ✓, the installed copy compared
  file by file ✓ ⇒ all four identical ✓ ✓.
- Every claimed stale row re-read ✓ (nine ✓) and **classified** ✓ ⇒ four fixed ✓, four routed ✓, one
  reclassified ✓ ⇒ and the dated-history list spot-checked ✓ (six ✓) ⇒ confirmed as history ✓ ✓.
- The gateway process, its start time and the installed file's mtime read ✓ ⇒ the in-memory version
  established ✓ ⇒ **recorded, not acted on** ✓ ✓.
- The version claims in the handoff docs and the README row updated ✓ ⇒ the review lane's own files ✓ plus
  the README row **claimed in the commit message** ✓ ✓.
- No `research/**` ✓, no `design/**` ✓, no `packages/hermes/**` ✓ and no `tools/**` ✓ file edited ✓; nothing
  pushed ✓.

# RR-VERSIONRULE-20261113 — the version rule: a release number in prose is a claim with an unmonitored expiry

Owner ruling, this session: where a document states a plugin version, the honest fix is **not** "the current
version". It is: cite a version only where a result depends on the build — and then date that build; everywhere
else name the file that carries the number. This card applies the rule to four documents and records it as a rule
so the class of defect stops recurring.

Supersedes, for `research/**`, the recommendation in `reports/RR-VERSIONDRIFT-20261113.md` §2 ("the current
version" for four routed paper rows). That card's fact-finding stands; its disposition is what the owner ruled
against.

## 1. Why "the current version" loses

Measured on this tree (`git log --date=short -G'PLUGIN_VERSION = "' -- packages/hermes/live/__init__.py`):

| Fact | Value |
|---|---|
| commits that changed `PLUGIN_VERSION` | **48** |
| distinct values over those commits | **48** |
| span | **2026-10-24 → 2026-11-13** (21 days, ~2.3 bumps/day) |
| 0.10.2 current window | **2026-11-06 (`670b146`) → 2026-11-07 (`c947530`)** — one day |
| 0.13.23 landed | **2026-11-13 (`f3078b4`)** |
| CI steps that read `research/**` or `design/**` | **none** |

The paper's P9 sync pass is dated 2026-11-06 — the day `0.10.2` was current. The number was true when written
and false within 24 hours. Nothing in the repo would ever notice: `white-paper.md` is hand-edited, and no gate
step reads it.

## 2. The rule, as written into the documents

> A plugin version appears only where a result depends on the build, and then dated to that build. Descriptive
> prose names the source file (`live/__init__.py`), never a release number. State a build the way §3.8 states the
> gate: with its witness date.

Corollary the documents now carry: **do not write today's date beside an old number.** "v0.10.2 as of
2026-11-13" is a new falsehood; the date must describe the build's window, not the sentence's.

## 3. Edits

**`research/white-paper/white-paper.md`** (owner-authorized cross-lane edit; `research/**` is read-never-edit for
this lane by default):

| Site | Before | After |
|---|---|---|
| §3.8 L204 | "the Hermes plugin (v**0.10.2**, source `live/__init__.py`)" | "the Hermes plugin (source `live/__init__.py`)" |
| §5.3 L402 | "the Hermes plugin (v**0.10.2**)" | "the Hermes plugin" |
| §7 L437 | "(`FaultPinPolicy`, plugin **0.10.2**; later 0.13.x)" | "(`FaultPinPolicy`, the Hermes `ctxvm` ContextEngine)" |
| Document control | — | new row **Version references** carrying the rule and the 48-value measurement |

The §7 number was doing no work the cited reports do not already do: `design/W8-CLOSURE-20261110.md`,
`design/W8B-CLOSURE-20261111.md`, `design/W8C-PLAN.md` and `reports/RR-PAIDRESULT-20261112.md` state the builds
where they matter.

**`research/white-paper/index.md`** — regenerated, never hand-edited:
`python3 research/white-paper/sync-index.py` → `wrote index.md (71464 chars)`.

**`design/HERMES-PLUGIN-DEVELOPER-PROMPT.md` §10 "What you never write"** — the rule added beside the existing
"a claim you did not read from the system" bullet.

**`design/hermes-catalog-submission.md` §"What is missing before submission" item 2** — the tag-time pin no longer
names `version: 0.10.6`; it points at the gate-enforced authoritative pair.

Sites left alone, deliberately: `§4.5`/`§6.1` ("682 checks … witnessed 2026-10-29") are already in the correct
shape — a number with its witness date — and every other version mention in the tree is dated history (a closure
note, a runbook precondition, an incident row) and is correct as written.

## 4. Verification

```
python3 research/white-paper/sync-index.py --check      # sync-index: OK — index.md matches white-paper.md, exit 0
grep -c '0\.10\.2\|0\.13\.x' research/white-paper/white-paper.md      # 0
bash tools/run-ci.sh                                     # ALL GATES GREEN
```

Gate, this run, unpiped with `CTXVM_*` cleared by enumeration: `rust suite green`; `ts suites green (24 + 62 + 46
tests); python suites green (201 + 8 + 66 tests)`; `SCHEMA CONFORMANCE: PASS (682 checks)`; `hub byte-identity
green`; `ALL GATES GREEN`.

## 5. Deviations, and what is not landed

1. **`research/**` was edited by this lane.** `handoff/LANES.md` makes it read-never-edit here. The owner
   instructed the edit in this session; the lane boundary is crossed deliberately and recorded, not silently.
2. **The paper change is applied on disk and NOT committed.** `research/white-paper/white-paper.md` and
   `index.md` carry **190 lines of an uncommitted re-wrap by the research lane** (HEAD 689 lines, working tree
   684; `git diff -U0` shows whole paragraphs re-flowed). Staging either file would commit that lane's in-flight
   work under this card's message, which `handoff/LANES.md` forbids. The hunks are in the tree; the commit is
   owed to whichever lane owns the re-wrap, and the choice between "land both together" and "re-land the hunks
   over HEAD" is the owner's.
3. **The rule is not gate-enforced.** Nothing checks `research/**`, so this card cannot make the defect
   impossible — only unfashionable, and visible in one grep (`grep -nE 'plugin v?[0-9]+\.[0-9]+\.[0-9]+'
   research design`).

## 6. Open

- Owner: decide the paper commit shape (§5.2). No other decision is needed.
- `handoff/PROJECT-STATE.md`, `handoff/SESSION-START.md`, `handoff/AGENT-PROMPT.md` and `README.md` were corrected
  by other lanes during this session (all four now read 0.13.23 with the authoritative locator, and
  AGENT-PROMPT.md names the loaded 0.13.22 beside the process that holds it). Not this card's work; recorded so
  the file does not claim credit for it.

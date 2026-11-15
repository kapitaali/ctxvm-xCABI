# RR-PAPER-REVIEW-20261115 — the white paper's PDF deliverable is stale against its own source, and two central claims outrun the shipped emitters

**Lane:** review (verify-then-record). **Date:** 2026-11-15. **Subject:** the research lane's white-paper
working tree (`research/white-paper/**` ✓) and the committed deliverable (`research/white-paper.pdf` ✓).

**What this card does NOT do:** it does not edit `research/**` ✓ (read-never-edit for this lane ✓) ⇒ the fixes
below are routed, not applied ✓. It spends nothing ✓ and changes no code ✓.

---

## 0. Method

Every number below was measured on 2026-11-15 from the working tree, with the command printed beside it ✓.
The gate was re-run before writing: `bash tools/run-ci.sh` ⇒ **ALL GATES GREEN** ✓
(log at `/tmp/opencode/20261115-ci.log` ✓: rust ✓, ts 24+62+46 ✓, python 207+8+66 ✓, schema 682 checks ✓,
hub byte-identity ✓).

The research lane's tree state at the time of the review ✓:

| file | mtime | state |
|---|---|---|
| `research/white-paper/white-paper.md` | 2026-11-13 23:42 | WIP, uncommitted ✓ |
| `research/white-paper/index.md` | 2026-11-13 23:43 | WIP, uncommitted ✓ (in sync with the above ✓) |
| `research/white-paper-Part-II.md` | 2026-11-13 16:22 | WIP, untracked ✓ |
| `research/white-paper.pdf` | **2026-11-06 21:58** | rebuilt after the last commit ✓, **not** from the WIP ✓ |
| `research/white-paper/README.md` | — | WIP, uncommitted ✓ |

---

## 1. What is correct (measured, not assumed)

The routed bundle landed ✓ — all six items, with **one** deviation that is a **correction** (see §4) ✓:

| routed item (`reports/RR-WPROUTE-20261112.md`) | state in the WIP |
|---|---|
| 1 — Pillar-1 split & the scoped absence claim | **applied** ✓ |
| 2 — closing the Pillar-1 echo + the "same bytes" sweep | **applied** ✓ |
| 3 — the located `seq: 7` cause | **applied** ✓ |
| 4 — the RFC-0.1 §R1 `intentional_rerun` contrast | **applied, corrected** ✓ (§4) |
| 5 — `profile` / `replay` wording | **applied** ✓ |
| 6 — the redaction-card citation rule (2 sites) | **applied** ✓ |

The routed card's own three verification commands, run on the WIP ✓:

```
diff -u <(tail -n +1 research/white-paper/white-paper.md) <(tail -n +7 research/white-paper/index.md)
  -> one line differs: the title. The two files are in sync. ✓
grep -c 'diffable\|This paper does not contain that audit' research/white-paper/{white-paper,index}.md research/white-paper-Part-II.md
  -> 0 / 0 / 0 ✓ (the sweep is complete ✓)
grep -c 'identifier_scan\|intentional_rerun\|CTXVM_TRACE=0\|design/redaction-block.md\|design/diff-normalisation.md' ...
  -> 12 / 12 / 3 ✓ (all five markers present ✓)
```

The four routed version claims (`reports/RR-VERSIONDRIFT-20261113.md`) ✓: **no bare plugin version is left**
in either paper file ✓ (`grep -cE '0\.1[0-3]\.[0-9]+'` ⇒ 0 / 0 ✓), and the "Version references" rule row is in
the document-control table ✓ (`white-paper.md:684` ✓) with its witness date ✓.

**Two negative results worth recording** (both checked, both clean ✓):

1. The paper's example trace (`white-paper.md:357-359` ✓) claims to be the **first three lines of the frozen
   `corpus/m1/tracer-healthy.jsonl`, verbatim** ✓ — and it **is** ✓ (byte-identical ✓). The sealed v0 validator
   accepts it ✓ (`python3 spec/rfc-0/validate_schema.py` ⇒ PASS ✓). The nested `page.id` / `kind` / `tokens`
   shape is the sealed v0 shape ✓ (`spec/rfc-0/x-cabi.schema-v0.json` ⇒ `pageRef` ✓), not a draft leftover ✓.
2. The paid live capture validates against RFC-0.1 ✓ (`python3 spec/rfc-0.1/validate_schema_v0_1.py` ⇒
   **OK: all checks passed** ✓), so the wire claims in the paper are not contradicted by the shipped emitter ✓.

**No claim this lane has falsified earlier survives in the WIP** ✓ — the strings `"86,569"`, `"0.570"`,
`"210,856"`, `"16 rewrite"`, `"0 stubs"` are all absent ✓, and the law-7 guard is present ✓
(`"no saving may be claimed"` ✓, at `white-paper.md:440` ✓).

---

## 2. F1 — the PDF deliverable is stale against its own source, and its source generation exists nowhere

`research/white-paper.pdf` was rebuilt **2026-11-06 21:58** ✓, i.e. **seven days before** the WIP markdown
(2026-11-13 23:42 ✓), and **after** the last commit of that file (`8b2cbcd`, 2026-11-05 22:40 ✓).

Marker-by-marker, PDF text against the WIP markdown ✓ (`pdftotext` ⇒ flat text ✓):

| marker | in the PDF | in the WIP markdown |
|---|---|---|
| `design/redaction-block.md` (routed item 6) | 0 | 1 |
| `seq: 7` (routed item 3) | 0 | 1 |
| `logged diagnostic class` (routed item 3) | 0 | 1 |
| `W8/W8B/W8C paged arm` | 0 | 1 |
| `design/W8-CLOSURE-20261110.md` | 0 | 4 |
| `25,404` (the W8 evictable ceiling) | 0 | 1 |
| `no saving may be claimed` (law 7) | 0 | 1 |
| **`its 24k-budget inertness on real traffic is the open finding in §7, not a stable flag`** | **1** | **0** |

⇒ The PDF carries **none** of the routed items and **none** of the W8/W8B/W8C results ✓, and it still carries
the **withdrawn** §7 wording ✓ (the WIP replaced it with *"its results are in §7 — 24k inertness closed
negative, and larger budgets page at the cost of the provider prefix cache"* ✓, `white-paper.md:373` ✓).

⇒ **The deliverable is not reproducible from anything in the repository** ✓: the PDF's §7 sentence appears in
**no** committed markdown ✓ (searched 40 commits of `research/white-paper/` ✓) and **not** in the working tree
✓ ⇒ the PDF was built from an **intermediate generation that was never committed** ✓ (it does carry the WIP's
`73 tests green` ✓, so it is *after* the M0 edit and *before* the W8C edit ✓).

⇒ **Consequence:** the committed PDF is a deliverable whose source is lost ✓ ⇒ a reader who trusts the PDF
reads a §7 that the markdown has already superseded ✓ ⇒ and the paper's own "Phase 6 of 6 complete" status line
✓ points at that PDF ✓.

---

## 3. F2 — four page counts, three artefacts, no two agree

| artefact | says | actual |
|---|---|---|
| HEAD `research/white-paper.pdf` | — | **23 pages** (124,245 B ✓) |
| HEAD `research/white-paper/README.md:9` | "the PDF deliverable, **15** pages" | — |
| HEAD `research/white-paper/index.md:5` | "PDF **22** pages" | — |
| tree `research/white-paper.pdf` | — | **24 pages** (134,155 B ✓) |
| tree `research/white-paper/README.md:9` | "the PDF deliverable, **24** pages" | — |
| tree `research/white-paper/index.md:5` | "PDF **24** pages" | — |
| **rebuild of the WIP markdown** | — | **25 pages** ✓ |
| rebuild of HEAD's markdown | — | 24 pages ✓ |

⇒ HEAD's three numbers (23 / 15 / 22 ✓) contradict each other ✓ ⇒ the WIP's two numbers agree with the tree
PDF ✓ but **not** with a rebuild of their own source ✓ (25 ✓).

The rebuild is the repo's own script ✓ (`research/white-paper/build-pdf.sh` ✓ — Markdown → HTML → WeasyPrint ✓),
run with the repo's venv ✓ (`venvs/odps/bin/python` ✓, `venvs/odps/bin/weasyprint` ✓, WeasyPrint **70.0** ✓,
markdown **3.11.2** ✓), and it is **deterministic** ✓ (two builds ⇒ md5 `43e253815fac` ✓ both times ✓).
The script's own HTML output was compared byte-for-byte with an independent rebuild ✓ ⇒ identical ✓.

**Limitation, stated because it matters** ✓: the original build's tool versions are **not recorded** in the repo
✓ ⇒ the 25 is *"a rebuild in this environment"* ✓, not a claim about what the original build produced ✓ — the
version-independent findings are the **marker table** (§2 ✓) and the **four disagreeing numbers** (§3 ✓).

---

## 4. F4 (erratum to my own card) — the routed bundle's item 4 carried a wrong field name and a counterfactual

`reports/RR-WPROUTE-20261112.md` §"Item 4" routed this sentence ✓:

> `page.fault` also accepts `"reason": "intentional_rerun"`, … (Umpire's `ab-demo` ledger **drops from 3**
> `faultOfResidentPage` **violations under v0 rules to 0** under RFC-0.1 R1 …)

The WIP writes ✓ (`white-paper.md:362` ✓, `index.md:368` ✓):

> `page.fault` also accepts `"source": "intentional_rerun"`, … (Umpire's `ab-demo` ledger **carries 3**
> `intentional_rerun` faults on a resident page: **under v0 the source is rejected**, and under RFC-0.1 R1 it is
> valid and exempt from `faultOfResidentPage` …)

⇒ **The WIP is right on both points and my routed text was wrong** ✓:

1. **Field name** ✓: the wire field is **`source`** ✓ — `spec/rfc-0/x-cabi.schema-v0.json` ⇒ `page.fault`
   requires `source` ⇒ `$ref: faultSource` ✓, and `spec/rfc-0.1/x-cabi.schema-v0.1.json` extends that enum with
   `intentional_rerun` ✓. **`reason` is `page.pin`'s field** ✓ (`spec/rfc-0/x-cabi.schema-v0.json` ⇒
   `page.pin` requires `reason` ✓) ⇒ my routed text confused the two events ✓.
2. **Framing** ✓: under sealed v0 the `intentional_rerun` **source value is not in the enum** ✓ ⇒ such a line is
   **rejected** by the sealed validator ✓ ⇒ "3 violations under v0 rules" is a counterfactual ✓ ⇒ the paper's
   phrasing is the accurate one ✓.

⇒ **Erratum** (the LOG is append-only ⇒ this is a new row, not a rewrite ✓): `RR-WPROUTE-20261112` item 4's
`reason` ⇒ `source` ✓, and its v0 framing ⇒ "the source is rejected" ✓. **The research lane corrected my
routing** ✓ ⇒ that is the routing working as intended ✓.

---

## 5. F3 — the M0 test count is stale by four

`white-paper.md:204` ✓ (and `index.md:210` ✓) says:

> "M0 is complete: **73 tests green (74 with the `tiktoken` feature)**, 0 warnings, replay determinism
> byte-identical."

Measured today ✓:

```
(cd rust && cargo test)                                            -> 77 tests ok ✓
(cd rust && cargo test --features ctxvm-tokenizer/tiktoken)        -> 78 tests ok ✓
(cd rust && cargo test 2>&1 | grep -c '^warning')                  -> 0 ✓
```

⇒ the count moved at **`82f6a03`** ✓ (2026-11-11, *"P11: the pair lands committed and level 2 (the derived page
table) becomes an assertion"* ✓) ⇒ that commit added **exactly 4** `#[test]`/`#[tokio::test]` attributes ✓ ⇒
the tree carried **74** attributes at `8b2cbcd` ✓ (2026-11-05 ✓, the PDF's commit ✓) and **78** at HEAD ✓
(= the 78 measured with the feature ✓ ⇒ the attribute count is a faithful proxy ✓).

⇒ the paper's "73 (74)" **predates 2026-11-11** ✓ and is now **four low** ✓ ⇒ and it was already **one low**
against the tree at the time the PDF was built ✓ (74 attributes ✓) ⇒ so the number was never measured against
the tree it describes ✓.

The rest of that sentence still holds ✓: "Conformance is 682 checks over 27 fixtures (17 corpus traces)" ✓ —
measured today ⇒ **682 checks** ✓, **27 fixtures** ✓, **17** corpus traces ✓ (`ls corpus/m*/ | grep -c jsonl`
⇒ 17 ✓), and the gate prints the same ✓ ⇒ that number is fine ✓.

---

## 6. F5 — "`page.render` captures the exact render mode (full or stub) for every page, every turn" is true of the wire and false of the shipped adapters

The claim (`white-paper.md:265` ✓, `index.md:271` ✓):

> "ctxvm's tracer already records all of this. The `page.render` event captures the exact render mode (full or
> stub) for every page, every turn."

Measured ✓:

| what | measurement |
|---|---|
| the two shipped emitters | `packages/node/src/tracer.ts:378` ✓ and `packages/hermes/src/plugin.py:290-297` ✓ both write `mode: "full"` ✓, **once per page** ✓ (`p.revealed = true` ✓ / `page["revealed"] = True` ✓; the turn loop only reveals unrevealed pages ✓ — `plugin.py:416` ✓) |
| a `mode: "stub"` render | **no shipped emitter writes one** ✓ (`grep -rn '"stub"'` over `packages/{node,hermes,opencode,ai-sdk}/src` ⇒ no hit ✓; the `page.evict` hits in the TS packages are **readers** ✓ — `packages/opencode/src/resume-brief.ts:138` ✓, `packages/opencode/src/uc2-forensics.ts:237` ✓) |
| live captures | **176** `.jsonl` files ✓ ⇒ **54** with ≥1 `page.render` ✓ ⇒ **2,050** `page.render` events ✓ ⇒ **0** with `mode: "stub"` ✓ ⇒ **0** `page.evict` events ✓ |
| the repo's only stub renders | `corpus/m1/session-thrashing.jsonl` ✓ — 12 stub + 8 full renders ✓ and 4 `page.evict` rows ✓ ⇒ a **hand-built** fixture ✓ whose own provenance says *"SYNTHETIC, not a live harness capture"* ✓ (`corpus/m1/provenance.json` ✓) |
| the wire's capability | `renderMode` = `["full","stub"]` ✓ (`spec/rfc-0/x-cabi.schema-v0.json` ✓) and `page.render` **requires** `mode` ✓ ⇒ the **format** can say it ✓ |

⇒ **The format can carry it; no shipped adapter emits it** ✓ ⇒ the sentence, read as a claim about *"ctxvm's
tracer"* ✓ (the shipped thing ✓), is **not true today** ✓.

⇒ **What a live trace therefore cannot say** ✓, measured on the paid paged capture ✓
(`local-c0b4ff62…` ✓, arm = paged ✓, 20 turns ✓, 42 API requests ✓): **21** pages declared ✓ ⇒ **19**
`page.render` rows ✓ ⇒ one per turn ✓ ⇒ **0** stub renders ✓ ⇒ so the trace **cannot say which pages a given
turn's request contained** ✓, nor that a page was stubbed ✓.

⇒ **Ask A3** (routing, §8 below) ✓.

---

## 7. F6 — the one-liner "reconstruct and replay the exact request the harness sent" is unqualified where the limits live

The claim, in **six** places ✓ — `white-paper.md:17` ✓, `:237` ✓, `:633` ✓ and `index.md:23` ✓, `:243` ✓,
`:639` ✓ — plus *"the exact rendered message array"* at `white-paper.md:247` ✓ (`index.md:253` ✓):

> "**Context tracing is not logging — it is the ability to reconstruct and replay the exact request the harness
> sent.**"

⇒ The routed item 2 correction landed **once** ✓ (`white-paper.md:629` ✓: *"re-derives any trace's page-table
state and render projection"* ✓) ⇒ but the same over-claim survives in the three sites above ✓ ⇒ the sweep was
**partial** ✓.

**Measured against the shipped artefacts** ✓ (the paid paged capture ✓):

| what the trace says | value across the 20 turns |
|---|---|
| `turn.render.residentTokens` | **86,569 — constant** ✓ |
| `turn.render.evictedTokens` | 0 → 64,506 ✓ (a lagging cumulative ✓) |
| `turn.render.prefix.approxInputTokens` | 12,060 → **59,747** ✓ (the request grew ✓) |
| the provider's own receipts (`call.meta.providerUsage`) | 14,557 → **114,766** ✓ |

⇒ the trace's **resident total does not track the request** ✓ (constant 86,569 against a request that grew
~5× ✓) ⇒ and the trace holds **no request content** ✓: the wire's only free-text field is
`page.evict.stubText` ✓, which **no shipped emitter writes** ✓ (§6 ✓) ⇒ ⇒ what replay re-derives is the
**page-table state and the render projection** ✓ — *not* the request's bytes ✓.

⇒ The paper **does** state the content-blindness, in one place ✓: *"A trace holds page identities, content
hashes, token counts, and references"* ✓ (`white-paper.md:617` ✓) ⇒ but that sentence lives in §9 (consent ✓)
and **not** in §16 *"What ctxvm cannot do"* ✓ (which lists six limits ✓ and does not include this one ✓) ⇒ ⇒
the paper's own rule — *"What a trace cannot do is in §16, in one place"* ✓ — is **not** met for this limit ✓.

⇒ **Ask A4** (routing, §8 below) ✓.

---

## 8. The asks

| id | ask | owner | cost |
|---|---|---|---|
| **A1** | rebuild the PDF from the WIP markdown ✓ (`bash research/white-paper/build-pdf.sh` ✓) and set **both** page-count claims from the rebuild ✓ (25 in this environment ✓, with the tool versions named ✓) | research lane | minutes, no spend ✓ |
| **A2** | update the M0 count ✓ — either the measured numbers with the command and the date ✓ (*"77 cargo tests green (78 with `--features ctxvm-tokenizer/tiktoken`), measured 2026-11-15"* ✓) or drop the count and point at the gate ✓ | research lane | minutes ✓ |
| **A3** | **scope the `page.render` sentence** ✓ — two candidates below ✓ | owner / reviewer ✓ | one sentence ✓ |
| **A4** | **scope the one-liner** ✓ — two candidates below ✓ | owner / reviewer ✓ | one sentence + one §16 bullet ✓ |
| **A5** | **erratum** to `reports/RR-WPROUTE-20261112.md` item 4 ✓ (§4 ✓) — this card is the erratum ✓ | review lane (mine) ✓ | done here ✓ |

**A3 candidates** ✓ (the claim is the paper's; the choice is the owner's ✓):

- **(a) format-scoped** ✓: *"The `page.render` event can carry the render mode (`full` or `stub`) per page per
  turn. The shipped adapters today emit `full` only, once per page, at its first reveal."* ✓
- **(b) adapter-scoped** ✓: *"The tracer records a `page.render` per page at its first reveal, mode `full`. The
  v0 wire has a `stub` mode that no shipped adapter emits yet, so a live trace cannot yet say which pages a
  given turn stubbed."* ✓

⇒ **the review lane's recommendation** ✓: **(a) + (b) merged** ✓ — the format is the paper's subject ✓ and the
adapter state is the honest caveat ✓ ⇒ but the wording is the owner's ✓.

**A4 candidates** ✓:

- **(a) narrow the one-liner** ✓: *"…the ability to reconstruct the page-table state and the render projection
  of a turn — not the request's bytes: the trace holds page identities, content hashes, token counts and
  references."* ✓
- **(b) keep the one-liner and state the limit once in §16** ✓: *"A trace cannot reconstruct the request's
  bytes. It records page identities, content hashes, token counts and the measured size of each request; the
  shipped adapters do not yet emit the stub renders that would record a turn's omissions."* ✓

⇒ **the review lane's recommendation** ✓: **(b)** ✓ — the one-liner is the paper's pitch ✓ and the routed item 2
already fixed one instance of the same over-claim ✓ ⇒ the limit belongs in the one place the paper promises
(§16 ✓) ⇒ plus a footnote at the first mention ✓.

---

## 9. Repro

One script prints every number in this card ✓ (the commands are also inline above ✓):

```bash
# §2 — the PDF against its source
pdftotext research/white-paper.pdf - | grep -c 'design/redaction-block.md\|seq: 7\|no saving may be claimed'
git log --format=%h -40 -- research/white-paper/ | while read c; do
  git show $c:research/white-paper/white-paper.md 2>/dev/null | grep -q 'not a stable flag' && echo "found in $c"
done   # -> no output: the PDF's source generation is in no commit
# §3 — the page counts
pdfinfo research/white-paper.pdf | grep Pages
git show HEAD:research/white-paper/README.md | grep 'PDF deliverable'
git show HEAD:research/white-paper/index.md  | grep 'PDF [0-9]* pages'
bash research/white-paper/build-pdf.sh && pdfinfo research/white-paper.pdf | grep Pages
# §5 — the M0 count
(cd rust && cargo test 2>&1 | grep -cE '^test .* \.\.\. ok$')                       # 77
(cd rust && cargo test --features ctxvm-tokenizer/tiktoken 2>&1 | grep -cE '^test .* \.\.\. ok$')   # 78
# §6 — the render modes
grep -rn 'mode: "full"\|"mode": "full"' packages/node/src/tracer.ts packages/hermes/src/plugin.py
python3 - <<'PY'
import json, glob, os
pats = glob.glob(os.path.expanduser('~/.local/state/ctxvm/traces/*.jsonl'))
stub = evict = renders = 0
for p in pats:
    evs = [json.loads(l) for l in open(p) if l.strip()]
    pr = [e for e in evs if e.get('type') == 'page.render']
    renders += len(pr)
    stub += sum(1 for e in pr if e.get('mode') == 'stub')
    evict += sum(1 for e in evs if e.get('type') == 'page.evict')
print(len(pats), 'captures |', renders, 'renders |', stub, 'stub |', evict, 'evict')
PY
# §7 — the request series of the paid paged capture
python3 - <<'PY'
import json, os
f = os.path.expanduser('~/.local/state/ctxvm/traces/local-c0b4ff6295f5876d1161b491b51cb511d21094feb87328b6b1488223a7af799e.jsonl')
evs = [json.loads(l) for l in open(f) if l.strip()]
tr = [e for e in evs if e['type'] == 'turn.render']
print('residentTokens:', sorted({e['residentTokens'] for e in tr}))
print('approxInputTokens:', tr[0]['prefix']['approxInputTokens'], '->', tr[-1]['prefix']['approxInputTokens'])
print('provider receipts:', evs[[i for i,e in enumerate(evs) if e['type']=='call.meta'][0]]['providerUsage'])
PY
```

---

## 10. Limitations and what stays unverified

- **The PDF rebuild's page count is environment-bound** ✓ (WeasyPrint 70.0 ✓, markdown 3.11.2 ✓): the original
  build's versions are not recorded ✓ ⇒ 25 is *this* rebuild ✓ ⇒ the marker table (§2 ✓) and the four
  disagreeing numbers (§3 ✓) are the version-independent findings ✓.
- **No `research/**` file was modified** ✓ ⇒ the findings are measured on the research lane's WIP as it stands
  at 2026-11-15, 10:30–11:20 CEST ✓ ⇒ a later WIP edit invalidates the marker table ✓ ⇒ re-run §9 before
  acting ✓.
- **The live-capture census is a snapshot** ✓ (176 files ✓ at 10:5x ✓): a capture taken after this card can add
  a stub render ✓ — that would be evidence **for** the paper's claim ✓ and would not change the shipped-emitter
  reading ✓ (§6 ✓).
- **UNVERIFIED**: whether the paper's one-liner is intended as a **design** claim about the format (in which case
  §7 is about the wrong claim) or as a claim about **today's artefacts** (in which case it is false as written ✓)
  ⇒ that reading is the owner's ✓ ⇒ A4 offers both ✓.
- **Not re-measured here**: the W8/W8B/W8C numbers the paper now cites ✓ (they were measured in
  `reports/RR-PAIDRESULT-20261112.md` ✓ and `design/W8*-CLOSURE-*.md` ✓; this card only checks that the paper
  cites them with their locators ✓ and that the guard sentence is present ✓).

⇒ **The gate is green** ✓ (`bash tools/run-ci.sh` ⇒ ALL GATES GREEN ✓) ⇒ and this card changes nothing in the
tree ✓ ⇒ the next session's first task is **A1 + A2** (mechanical ✓) and the owner's is **A3 + A4** ✓ ✓.

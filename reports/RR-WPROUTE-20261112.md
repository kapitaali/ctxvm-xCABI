# RR-WPROUTE-20261112 — D13 + D14 ratified and the six-item white-paper bundle routed to the research lane (G5 closed)

Card: owner ratification of **D13** (Packet 1, `design/diff-normalisation.md`) and **D14** (Packet 3,
`design/redaction-block.md`) and execution of **G5** — routing the six-item white-paper edit bundle to
the research/white-paper lane with exact working-tree file paths, line numbers, before/after text, and
verification commands.

Per `handoff/LANES.md` (`research/** is read-never-edit for every other lane`), zero bytes in
`research/**` are edited by this commit; this card is the self-contained, paste-ready routing spec
against the current working-tree bytes of:
- `research/white-paper/white-paper.md` (689 lines in working tree)
- `research/white-paper/index.md` (695 lines in working tree; +6 line offset twin of `white-paper.md`)
- `research/white-paper-Part-II.md` (558 lines in working tree, untracked)

---

## Item 1 — Pillar-1 split & scoped absence claim (D13 / Packet 1, `RR-DIFFNORM-20261108`, `design/diff-normalisation.md`)

- **Locations**:
  - `research/white-paper/white-paper.md:117`
  - `research/white-paper/index.md:123`
- **Current working-tree text**:
  > `**Pillar 1 — xCABI, a portable trace standard.** Every agent system keeps a private mutation log. None is cross-harness replayable, diffable, or conformance-testable. xCABI ("eXchangeable Context ABI") fills that gap. It defines a deterministic log of pages, renders, evictions, and faults. A consumer reconstructs any turn without knowing which harness produced the trace.`
- **Routed replacement**:
  > `**Pillar 1 — xCABI, a portable trace standard.** Every agent system keeps a private mutation log; in the systems reviewed here (§2, §8), we found none that is cross-harness replayable or conformance-testable. xCABI ("eXchangeable Context ABI") fills that gap. It defines a deterministic log of pages, renders, evictions, and faults: traces from different harnesses validate against one schema and replay in one engine, while a cross-harness diff requires the consumer-side normalisation profile proposed for RFC-0.1 (`design/diff-normalisation.md`). Within a single trace, a consumer reconstructs the page-table and render projection of any turn without knowing which harness produced the trace.`

---

## Item 2 — Closing Pillar-1 echo at `:635` and `"same bytes"` / `"byte-identically"` sweep (D13 / Packet 1, `RR-DIFFNORM-20261108`)

 Pages travel as `(logical_ref, content_hash)` identities (`rust/crates/ctxvm-codec/src/model.rs:14–21`),
so replay determinism reconstructs the **page-table state and render projection** of a single trace,
not raw prompt bytes across harnesses.

- **Locations & routed replacements**:
  1. `research/white-paper/white-paper.md:9` (`research/white-paper/index.md:15`):
     - **Current**: `1. **xCABI** — an open standard for agent traces. It records pages, renders, evictions, and faults in a deterministic log. Any consumer can replay any turn and get the same bytes.`
     - **Replace with**: `1. **xCABI** — an open standard for agent traces. It records pages, renders, evictions, and faults in a deterministic log. Any consumer can replay any turn of a trace and derive the same page-table state and render projection byte-for-byte.`
  2. `research/white-paper/white-paper.md:101` (`research/white-paper/index.md:107`):
     - **Current**: `2. A Rust engine that replays any trace byte-identically.`
     - **Replace with**: `2. A Rust engine that re-derives any trace's page-table state and render projection byte-identically.`
  3. `research/white-paper/white-paper.md:522` (`research/white-paper/index.md:528`):
     - **Current**: `**Byte-identical replay** takes a trace and re-derives the same facts. It is deterministic, it runs offline, and it is the basis of every claim in this paper. Given the same bytes it returns the same bytes.`
     - **Replace with**: `**Byte-identical replay** takes a trace and re-derives the same facts. It is deterministic, it runs offline, and it is the basis of every claim in this paper. Given the same trace bytes it returns the same derived projection bytes.`
  4. `research/white-paper/white-paper.md:635` (`research/white-paper/index.md:641`):
     - **Current**: `ctxvm is that shared layer. xCABI defines a deterministic, append-only, cross-harness trace format. \`ctxvm-core\` is a Rust engine that replays any trace byte-identically. The measurement stack — simulator, corpus, leaderboard — is packaged as ODPS 4.1 open data products.`
     - **Replace with**: `ctxvm is that shared layer. xCABI defines a deterministic, append-only trace format whose traces validate against one schema and replay in one engine across harnesses (with cross-harness diffing behind the consumer-side normalisation profile in \`design/diff-normalisation.md\`). \`ctxvm-core\` is a Rust engine that re-derives any trace's page-table projection byte-identically. The measurement stack — simulator, corpus, leaderboard — is packaged as ODPS 4.1 open data products.`
  5. `research/white-paper-Part-II.md:68`:
     - **Current**: `- **Deterministic replay.** The renderer is a pure function of the events. The same trace gives the same bytes.`
     - **Replace with**: `- **Deterministic replay.** The renderer is a pure function of the events. The same trace gives the same derived page-table and render-projection bytes.`

---

## Item 3 — Healthy-fixture `faultOfResidentPage` demo sentence with located `seq: 7` cause (Packet 2, `RR-P2DEMO-20261108`)

- **Locations**:
  - `research/white-paper/white-paper.md:333–340`
  - `research/white-paper/index.md:339–346`
- **Current working-tree text (`:340` / `:346`)**:
  > `\`profile\` prints per-page decision history and per-turn residency (agg-only, no divergence exit). \`replay\` enforces byte-identical re-render (exit 1 on divergence). \`diff\` compares two traces at page granularity (exit 0 shared prefix, 1 divergent). \`export --odps\` packages a session as an ODPS data product (manifest + llms.txt + checksum).`
- **Routed replacement (keep demo block at `:332–333` unchanged; add one sentence explaining the logged class and located `seq: 7` cause)**:
  > `\`profile\` prints per-page decision history and per-turn residency (agg-only, no divergence exit). \`replay\` enforces byte-identical re-render (exit 1 on divergence). In the \`tracer-healthy.jsonl\` output above, \`violations\` is a logged diagnostic class, not a replay failure ("healthy" in the fixture name means divergence-free, \`divergences: []\`, exit 0): at \`seq: 7\` (turn 2, \`page.fault\` source \`identifier_scan\`), the model named an identifier whose page (\`tool:read_file({"path":"src/auth/session.ts"})\` @ \`sha256:d5bf10dd\`, declared at seq 2 and rendered full at seq 5) was still resident. \`diff\` compares two traces at page granularity (exit 0 shared prefix, 1 divergent). \`export --odps\` packages a session as an ODPS data product (manifest + llms.txt + checksum).`

---

## Item 4 — RFC-0.1 §R1 `intentional_rerun` 3-to-0 contrast (Packet 2, `RR-P2DEMO-20261108`, `08-HANDOFF.md` §0 2026-10-31)

- **Locations**:
  - `research/white-paper/white-paper.md:362`
  - `research/white-paper/index.md:368`
- **Current working-tree text**:
  > `Further events (turn boundaries, faults, \`call.meta\`) follow the sealed \`spec/rfc-0/x-cabi.schema-v0.json\` shape; RFC-0.1 emitters add \`schemaVersion:"0.1"\` on \`session.open\` and may add \`ts\` last. The sealer validator (\`spec/rfc-0/validate_schema.py\`) passes 682 checks over 27 fixtures (17 corpus traces), witnessed 2026-10-29; it rejects every v0.1-only line.`
- **Routed replacement**:
  > `Further events (turn boundaries, faults, \`call.meta\`) follow the sealed \`spec/rfc-0/x-cabi.schema-v0.json\` shape; RFC-0.1 emitters add \`schemaVersion:"0.1"\` on \`session.open\` and may add \`ts\` last. Under RFC-0.1 §R1, \`page.fault\` also accepts \`"reason": "intentional_rerun"\`, which exempts deliberate re-executions from \`faultOfResidentPage\` under a v0.1 session while sealed v0 continues to log the class (for example, Umpire's \`ab-demo\` ledger drops from 3 \`faultOfResidentPage\` violations under v0 rules to 0 under RFC-0.1 R1). The sealer validator (\`spec/rfc-0/validate_schema.py\`) passes 682 checks over 27 fixtures (17 corpus traces), witnessed 2026-10-29; it rejects every v0.1-only line.`

---

## Item 5 — Consent paragraph replacement: three mends (D14 / Packet 3, `RR-P3REDACT-20261109`)

- **Locations**:
  - `research/white-paper/white-paper.md:620–623`
  - `research/white-paper/index.md:626–629`
  - `research/white-paper-Part-II.md:368`
- **Current working-tree text (`white-paper.md:620–623` / `index.md:626–629`)**:
  > `**Consent.** Capture is on by default in the plugin we ship, and that is a product decision with a cost: a user who does not know a trace exists cannot consent to it. The mitigations already in place are the state directory at \`0700\`, local-only storage, and documented opt-out. A paper cannot substitute for a consent process, and this one does not claim to.`
- **Routed replacement (`white-paper.md:620–623` / `index.md:626–629`, reviewer's verbatim replacement)**:
  > `**Consent.** Capture is on by default in the plugin we ship, and that is a product decision with a cost: a user who does not know a trace exists cannot consent to it. A trace holds page identities, content hashes, token counts, and references; the references, stub text, and reason fields can contain file paths and tool arguments. Page content is not stored. The state directory is mode \`0700\`, which protects against other local users but not against the agent process or a backup tool running as the same user. Storage is local-only. The opt-out is \`CTXVM_TRACE=0\`, which a user finds only by reading the documentation; a first-run notice is a proposed change, not a shipped one. A paper cannot substitute for a consent process, and this one does not claim to.`
- **Current working-tree text (`research/white-paper-Part-II.md:368`)**:
  > `Part I states that capture is on by default in the plugin it ships. A user who does not know a trace exists cannot consent to it. The state directory at mode 0700, local-only storage, and a documented opt-out reduce the risk. They do not replace consent.`
- **Routed replacement (`research/white-paper-Part-II.md:368`)**:
  > `Part I states that capture is on by default in the plugin it ships. A user who does not know a trace exists cannot consent to it. A trace holds page identities, content hashes, token counts, and references; the references, stub text, and reason fields can contain file paths and tool arguments, though page content is not stored. The state directory is mode 0700, which protects against other local users but not against the agent process or a backup tool running as the same user; storage is local-only; and the opt-out (\`CTXVM_TRACE=0\`) is found only by reading the documentation (a first-run notice is a proposed change, bound before any registry release under D6/D17, not a shipped one). These mitigations reduce the risk; they do not replace consent.`

---

## Item 6 — Redaction card citation rule & §9.3 field-audit pointer (D14 / Packet 3, `RR-P3REDACT-20261109`, `design/redaction-block.md`)

- **Locations**:
  - `research/white-paper-Part-II.md:340`, `:354`, `:360`
  - `research/white-paper/white-paper.md:615–618` (`research/white-paper/index.md:621–624`)
- **Routed replacements**:
  1. `research/white-paper-Part-II.md:340`:
     - Replace `the redaction stages applied;` with `the redaction record (as defined in proposal card \`design/redaction-block.md\`, \`RR-P3REDACT-20261109\`);`
  2. `research/white-paper-Part-II.md:354` (and align `white-paper.md:615–618` / `index.md:621–624`):
     - **Current (`Part-II.md:354`)**: `Part I proposes a redaction block on the session. This paper refines it into a list of stages, because one trace can be redacted at capture and again at export. Each entry carries the policy id, the rule-set version, the stage, and the number of fields replaced. Pages keep their identity and the hashes of the redacted content. Replay stays consistent within the redacted artifact and does not pretend to reproduce the original.`
     - **Replace with**: `Proposal card \`design/redaction-block.md\` (\`RR-P3REDACT-20261109\`, proposal-only, sidecar-first so sealed v0 and RFC-0.1 wire schemas stay untouched) defines the redaction record as an ordered list of stages (\`capture | flush | export\`), because one trace can be redacted at capture and again at export. Each stage entry carries the policy id, the rule-set version, the stage, the number of fields replaced, and a reference-policy declaration (\`raw | keyed-hashed | dropped\`); an absent record means **unknown, never unredacted**, and the block is an assertion without tamper evidence. Pages keep their identity and the hashes of the redacted content, so replay stays consistent within the redacted artifact and does not pretend to reproduce the original.`
  3. `research/white-paper-Part-II.md:360`:
     - **Current**: `The first task is an audit: a table of every field that can hold user-derived content (page content, stub text, \`logical_ref\`, tool arguments, paths, model output) and whether each is stored raw, hashed, or counted. This paper does not contain that audit.`
     - **Replace with**: `The first task is an audit: a table of every field that can hold user-derived content (page content, stub text, \`logical_ref\`, tool arguments, paths, model output) and whether each is stored raw, hashed, or counted. That audit is recorded in \`reports/RR-FIELDAUD-20261107.md\` across all nine event types and 22 corpus traces, identifying raw \`logicalRef\`, \`stubText\`, and \`reason\` as the primary conduct channels while page bodies and model outputs are absent from the wire.`

---

## Companion Note for the White-Paper Lane — W8 / W8B / W8C Empirical Update (Part I §1.3, §4.4, §4.7, §7)

When updating Part I's working-tree lines `:13`, `:105`, `:348`, `:373`, `:440`, and `§7` (which
currently cite only W8's 24k-budget floor inertness), the books now carry three completed results that
can be cited with their locators:
1. **W8 closed negative** (`design/W8-CLOSURE-20261110.md`, `reports/RR-P9CLOSE-20261111.md`): at the
   24k budget, the protected floor owned ~88–95% of request tokens (session-weighted evictable ceiling
   5.3% = 25,404 / 479,076 request tokens).
2. **W8B closed negative** (`design/W8B-CLOSURE-20261111.md`, `reports/RR-W8BCLOSURE-20261111.md`): at
   budgets 70,000 and 90,000 on a 20-turn / 21-page task, 43 selections produced **0 evictions** because
   prose-mention demand pinning (`_credit_demand`) pinned 19 of 21 pages.
3. **W8C measured after removing prose-mention pinning** (`design/W8C-PLAN.md`):
   - **Free cell-02** (`w8b-20261112-101410`, `meituan/longcat-2.5:free`, budget 60,000,
     `reports/RR-W8CCELL02RUN-20261112.md`): final request capped at **64,693 vs 107,810 (0.60×)**,
     session tokens **0.85×** (net reduction 167,793 tokens; `turn.render.evictedTokens` re-drop sum
     210,856), uncached input **4.73×** control.
   - **Paid cell-03** (`w8b-20261112-112711`, `openai/gpt-6-luna` via `nous`, budget 60,000, 42/42
     calls, `reports/RR-PAIDRESULT-20261112.md`): final request **59,747 vs 104,842 (0.57×)**, session
     tokens **0.82×** (net reduction 201,719; `evictedTokens` sum 275,362), total pair spend **$0.2534**
     (control **$0.0748**, paged **$0.1580 → 2.11× dollars**), because mid-prefix dropping invalidated
     the provider prefix cache (`cache_write` **4.49×**: 1,025,825 vs 228,382; `cache_read` **0.61×**:
     2,656,246 vs 4,348,503). Priced ceiling for a cache-stable watermark policy on this shape:
     **~$0.0089/session (~12% of control)** (`reports/RR-POLICYCHOICE-20261112.md`).
   - **Call-granularity clamp bound (`sim(S3)`)** (`w8b-20261112-201127`, plugin `0.13.13/0.13.14`,
     `reports/RR-W8SIM3-20261112.md`, `reports/RR-SIM3CRITIQUE-20261112.md`): all 16 dropping calls lie
     inside the whole-page quantization interval `(51,152, 60,000]` (`after = 55,449..59,834`, diagnostic
     median `|after - budget| / budget = 1.15%`, page size `~4,424` apx4 tokens ≈ 7.4% of budget).

---

## Verification Commands for the White-Paper Lane After Applying Items 1–6

```bash
# 1. Confirm index.md stays synchronized with white-paper.md (after frontmatter offset)
diff -u <(tail -n +1 `echo research/white-paper/white-paper.md`) <(tail -n +7 research/white-paper/index.md) | head -40

# 2. Confirm no unqualified "cross-harness ... diffable" or "This paper does not contain that audit" remains
grep -n 'diffable\|This paper does not contain that audit' research/white-paper/white-paper.md research/white-paper/index.md research/white-paper-Part-II.md

# 3. Confirm the located seq-7 cause, R1 3->0 contrast, CTXVM_TRACE=0 consent mend, and design/redaction-block.md citation are present
grep -n 'identifier_scan\|intentional_rerun\|CTXVM_TRACE=0\|design/redaction-block.md\|design/diff-normalisation.md' research/white-paper/white-paper.md research/white-paper/index.md research/white-paper-Part-II.md
```

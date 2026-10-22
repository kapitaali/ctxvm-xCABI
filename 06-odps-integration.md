# ODPS Integration Notes (post-dig)

## What ODPS 4.1 actually is (validated)

- Family, not a spec: **ODPS** (product) + **ODPC v1.0** (catalog/portfolio; the v4.1
  sidecar catalog, now graduated) + **ODPV** (controlled vocabulary) +
  **ODPG** (product graphs, in progress) + SDK (`open-data-products` on PyPI),
  all Apache-2.0, Linux Foundation.
- Their two agent-focused FAQs: `ai-agent-consumption.md` & `odps-llms-txt.md`.

## Their own recommendations (followed here)

1. **"ODPS provides the 'what' (declaration), MCP handles the 'how' (runtime)."**
   ⇒ xCABI sits exactly between: declaration (ODPS) → content (xCABI) → runtime (MCP).
2. **Design for the full autonomous consumption lifecycle** (discovery→evaluation→
   onboarding→provisioning→monitoring). For a free corpus: use MLG (lean gates), still
   declare DQ/SLA machinery so agents can self-serve. Skip pricing/payment (open-data).
3. **Derive llms.txt from the ODPS YAML**, host at root, point `dataAccess.agent.specsURL`
   at it. Implemented in `05-llms.txt`.
4. **Minimum Lovable Governance**: productStrategy gates (contributesToKPI.name required;
   ≥1 productKPIs w/ unit+target+calculation). Adopted as release gates.
5. **Catalog as code**: public Git repo, `*.yaml` per product, CI schema validation, static
   generation. hub.ctxvm.dev = Git repo + ODPC + Actions. No bespoke hub server.
6. **Composition over extension**: don't mutate ODPS; sidecar+`x-`. Our `x-cabi` block is the
   prescribed pattern.

## Artifact → template/type mapping

| Artifact | Template | `type` | Key ODPS knobs |
|---|---|---|---|
| Trace corpus / benches / golden vectors | Reusable Data Product (+ MCP port from Agentic) | `dataset` | DQ weights (validity= replay determinism 60, completeness 25, uniqueness 15), SLA updateFrequency/timeToDetect/errorRate |
| Enterprise session traces | Product Profile → Reusable | `dataset` | `visibility: organisation\|dataspace`, `governanceProfile: audit_ready` (xCABI determinism = audit-grade traceability) |
| Trained paging policies (v2) | Agentic Product | `algorithm` | bi-directional; policy marketplace ODPS-native |

## Frictions discovered (post-dig)

1. **`dataAccess.format` enum excludes JSONL/Parquet** (only TOON/JSON/XML/CSV/Excel/zip/
   plain text/GraphQL/MCP). Mitigations: upstream PR → else `format: JSON` + `x-format`.
   Manifest currently carries both.
2. **Template family vs core schema drift** — family drafts use `dataAccess: []` arrays;
   core + published skeleton use named maps (`default:` + `$ref`). Family DQ `declarative`
   is array-shaped, core requires `declarative.default` map. **Rule: core odps.yaml schema
   is truth; validate with their SDK; file drift issues upstream.**
3. No ODPS DQ dimension for "deterministic replay" — semantic lives in the `x-cabi`
   sidecar; ODPS `validity` is its declared proxy.
4. SLA enums are ops-shaped; benchmark claims belong in `productStrategy.productKPIs`.
   Division confirmed and used.

## Upstream engagement list (line-itemed, not aspirational)

- [ ] PR: add `JSONL`, `Parquet`, `zst`-pairing to `dataAccess.format` enum (or an `x-` note
      first if maintainers prefer)
- [ ] Issue: `purpose-agentic-product.yml` vs `drafts/odps-template-family-plan.md` shape
      drift (dataAccess/DQ)
- [ ] Issue: propose a "trace/memory data product" template as a future family member
- [ ] Contribute: our conformance-kernel `Custom` DQ spec as a Knowledge Base FAQ example
      ("How do I make every trace replay byte-identically?")

## Empirical validation results — DONE (2026-10-22)

Environment: venv `/tmp/opencode/ctxvm-venv`, **SDK `open-data-products` 0.4.0**, Python 3.14

**Result on `04-odps-dataproduct-corpus.yaml`: `valid: true` · `compliance_level: full` ·
`production_ready: true`; `product audit`: product valid, 1 contract reference detected.**

### First pass produced 5 errors — every one a schema-vs-docs drift discovery

| # | Validator error | Docs said | Bundled schema said | Fix applied |
|---|---|---|---|---|
| 1 | `version: 4.1 is not of type 'string'` | (unquoted example) | string required | quote `"4.1"` (YAML float hazard) |
| 2 | SLA `unit: 'hours'` rejected | doc's unit list | enum: percent, milliseconds, seconds, minutes, days, weeks, months, years, never, date, null — **no `hours`** | 24h → objective 1, unit `days` |
| 3 | `dataHolder: expected legalName` | doc + template show `dataHolder.en:` wrapper | **flat** object, fields directly under `dataHolder` | removed wrapper |
| 4 | DQ `description: {'en':…}` not a string | doc example shows `{en:…}` map | plain `string` | string |
| 5 | DQ `executable` "not of type 'object'" | doc shows a flat **array** of monitoring blocks | **named object** keyed by stable profile names, values = DQDefinition | three named checks: `replayDeterminism` / `pinLint` / `redactionScan` |
| 6 | (compliance) DQ `spec` forced to object | doc: "plain string allowed if type Custom" | `type: object`, even for Custom | spec blocks → YAML objects |
| 7 | (compliance) `displayTitle` shapes differ by level | lowercase `displaytitle` | DQDefinition: **array of language maps**; DQDimension: plain string | array form |
| 8 | audit `CONTRACT_REFERENCE_MISSING` | "contract optional" | Agentic template mandates; audit warns without it | `contract: {type: ODCS, contractURL…}` added; contract artifact itself = follow-up |

Rule confirmed by data: **bundled JSON schema is the only truth.** The HTML spec page and the
official templates would *fail their own validator* today.

### Audit residuals (environmental, not manifest defects)

- `contract_valid: false` — remote contract URLs not loaded by SDK yet → author
  `contracts/corpus-0.1.odcs.yaml` **locally**, and install `open-data-products[contracts]`
  (datacontract-cli) to go green.
- `DATACONTRACT_CLI_NOT_INSTALLED` — same remediation.

### Bonus discovery (strengthens the stack story)

The SDK itself ships an **MCP server** (`open-data-products serve`), an agent **manifest**
emitter, ODPC catalog builders, ODPG graph tooling, and OKF knowledge-bundle export — with
`--json` flags designed for agent consumption throughout. The tooling ecosystem is more
real than their docs page suggested; our hub pipeline should be built on exactly these
commands in CI.

## Next step

1. ~~Author minimal ODCS contract~~ **DONE — audit fully green** (`contract track` below).
2. Rust M0 spike (`ctxvm-core`).
3. File upstream issues: `hours` SLA-unit gap; doc-vs-schema drift; JSONL/Parquet format enum;
   datacontract-cli missing-python marker fallback messaging.

## Contract track results (2026-10-22)

**`product audit`: `passed: true` · `product_valid: true` · `contract_valid: true`**
(datacontract-cli 1.2.7, ODCS v3.0.2 lint green; 1 contract reference resolved locally;
zero blocking findings. Residual: info-level "add dataset fields to ODPS metadata for static
alignment" — non-blocking, served by the linked contract itself.)

### Authoring learnings (all empirically derived)

- **`datacontract-cli` 1.2.7 natively lints ODCS v3.0.2** — Bitol's v2.2.2-era vocabulary
  (`quantumName`, `dataset`, `datasetName`) is obsolete on main; current shape is
  `kind: DataContract`, `apiVersion: v3.0.2`, `schema: [...]`.
- **ODCS v3 `description` is an object** `{purpose, usage, limitations}` — not a string.
- **`quality` lives on schema elements** (array of typed check objects; dims:
  accuracy/completeness/conformity/consistency/coverage/timeliness/uniqueness — **no
  `validity`** in ODCS, so replay-determinism = `conformity` there, while ODPS-side keeps
  `validity` as the proxy). Custom checks require `engine` + `implementation` objects.
  Per-property `library` checks available (session_id `duplicateCount` = 0).
- **Service levels = top-level `slaProperties`** (`property/value/unit/element/driver`),
  not the 2.x `servicelevels` block.
- **Our own manifest bug caught:** ODPS `contractVersion` = the *standard's* version
  (`"3.0.2"`), not the document's — fixed from our wrong `0.1.0`.
- **Remote contract URLs are not loadable by the SDK yet** → manifest uses
  `contract.$ref: contracts/corpus-0.1.odcs.yaml` (local path; ODPS `Contract.$ref` allows it).

### Tooling constraint (worth an upstream issue)

`datacontract-cli` is gated `python_version < "3.13"` in the SDK's extra — pip **silently
skips** `[contracts]` on Python 3.13/3.14. Windows into the workaround:

```
conda create -y -n ctxvm-odcs python=3.12          # miniforge env
/home/theb/miniforge3/envs/ctxvm-odcs/bin/python -m venv /tmp/opencode/odcs-venv
/tmp/opencode/odcs-venv/bin/python -m pip install "open-data-products[contracts]"
```

Run all contract-track commands (validate, product audit) from `/tmp/opencode/odcs-venv/bin/`.
CI note: contract checks must run in a 3.12 job; validation-only can stay ≥3.13.

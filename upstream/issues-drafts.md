# Upstream issue drafts (file-ready)

Prepared from T0/T5 validation evidence + today's (2026-10-22) live reproduction runs
against **SDK `open-data-products` 0.4.0** (Python 3.14.7) and **`datacontract-cli`
1.2.7**. Source dig: `06-odps-integration.md` (friction log, validation table).
Filing note: strip this preamble; each block below is a standalone issue. Repo/venue
pointers to be confirmed at filing time (opendataproducts.org GitHub + Bitol CLI repo).

---

## Issue ① — `hours` missing from the ODPS SLA unit enum (and from the SDK's own templates)

**Context:** SLA `unit` is a closed enum that specs ops-time units only down to days — but
every support-level example uses "hours" (response times, support windows). This is not
hypothetical: the SDK's own generation template emits `unit: hours` and the validator rejects it.

Live validator line (0.4.0, `validate --json` on a scratch manifest with one TLC change):

```
$ open-data-products validate --json scratch.yaml
/product/SLA/declarative/default/dimensions/0/unit: 'hours' is not one of
['percent', 'milliseconds', 'seconds', 'minutes', 'days', 'weeks', 'months', 'years', 'never', 'date', 'null']
```

Bundled schema truth (`odps-v4.1.json`, `$defs/SLADimension/properties/unit`):

```json
{"type": "string", "enum": ["percent", "milliseconds", "seconds", "minutes",
 "days", "weeks", "months", "years", "never", "date", "null"],
 "description": "Measurement unit for the SLA objective."}
```

Bundled template contradiction (`generation/data/prompts/odps_product_assemble_yaml.md`,
L163/L179 in SDK 0.4.0 — `unit: hours` emitted twice):

```yaml
- dimension: updateFrequency
  displaytitle:
    en: Update Frequency
  objective: 24
  unit: hours
  weight: 40
```

The docs page shows an SLA unit list including `hours` (see T0 dig, `06`, row 2:
"SLA `unit: 'hours'` rejected... doc's unit list").

**Proposed fix:** add `hours` to `$defs/SLADimension/properties/unit` enum (and mirror in the
HTML spec unit table). Optional consistency: KPIs already accept free-string units
(`$defs/KPI/properties/unit` is plain `string`), so the schema is inconsistent with itself.

**Evidence:** `ctxvm/06-odps-integration.md` rows 2 + "First pass produced 5 errors"; commands
above; SDK 0.4.0 template quoted. Ready to be filed by the maintaining team; we can open
a PR against the schema JSON alongside.

---

## Issue ② — Docs vs schema drift pack (six rows; the HTML spec page would fail `validate` today)

**Context:** The bundled JSON schema is the only shape the validator accepts; the HTML spec
page and official examples still teach the rejected shapes. Each row = one recorded
validator error (T0, 06 rows 1–8) with today's live reproduction against 0.4.0.

| # | Docs/templates show | Schema truth (`odps-v4.1.json`) | Live validator line (0.4.0 today) |
|---|---|---|---|
| a | `version: 4.1` unquoted (float hazard) | `properties.version {"type":"string","examples":["v4.1","dev"]}` | `/version: 4.1 is not of type 'string'` |
| b | `dataHolder.en.legalName` wrapper | `$defs/DataHolder`: flat — `legalName`, `businessID`, `contactName`, … directly under `dataHolder` | `/product/dataHolder: required fields missing or invalid; expected legalName` |
| c | DQ `executable` = flat array of monitoring blocks | `DataQuality.properties.executable` = **named object** keyed by stable names, values = DQDefinition | `/product/dataQuality/executable: [...] is not of type 'object'` |
| d | DQ `spec` "plain string allowed if type Custom" | `DQDefinition.properties.spec {"type":"object"}` (inline YAML/URL object) even for `Custom` | `/product/dataQuality/executable/replayDeterminism/spec: '…' is not of type 'object'` |
| e | lowercase `displaytitle` in DQ dimension examples | DQ accepts camelCase `displayTitle` only; **SLADimension double-defines BOTH spellings** (`displayTitle` and `displaytitle` — see below) | recorded T0 (06 row 7); today's SLA-side repro `pass` confirms the double definition |
| f | legacy license object (e.g. `license: {name, file}`) | `$defs/License {scope, termination, governance}`; SDK template instructs "do not emit legacy license fields" | recorded T0; current validated shape quoted below |

Supporting real quotes:

```yaml
# odps-v4.1.json — schema defines BOTH spellings only for SLA dims:
/$defs/SLADimension/properties/displayTitle {"type":"object",...,"$ref":"#/$defs/Languages"}
/$defs/SLADimension/properties/displaytitle {"type":"object",...,"$ref":"#/$defs/Languages"}
# DQ — camelCase only:
/$defs/DQDefinition/properties/displayTitle {"type":"array","items":{"$ref":"#/$defs/Languages"}}
/$defs/DQDimension/properties/displayTitle {"type":"string"}
# generation/data/prompts/odps_product_assemble_yaml.md L24–26 (SDK 0.4.0):
- Preserve productStrategy, dataHolder, paymentGateways, and license
  as ODPS objects when drafted. For license, use scope, termination, and
  governance; do not emit legacy license fields. 
```

Our validated product (passes `validate` + `product audit` green) uses the schema-side
shapes for all six rows: quoted `version: "4.1"`, flat `dataHolder`, named-object
`executable` with `replayDeterminism`/`pinLint`/`redactionScan`, object `spec` blocks,
camelCase `displayTitle`, `license: {scope, termination, governance}`.

**Proposed fix:** re-sync HTML spec examples to the bundled schema (rows a–f), then
make the schema self-consistent: pick ONE `displayTitle` spelling per definition (row e
double-definition is a schema bug in its own right; SLA currently accepts both spellings
while DQ accepts only camelCase, so the same key is valid or invalid depending on section).

**Evidence:** `06` friction 2 + rows 1–8 table; commands and quotes above; our manifest
`04-odps-dataproduct-corpus.yaml` (valid, `compliance_level: full`) as the working
counterexample.

---

## Issue ③ — `dataAccess.format` enum: add `JSONL` / `Parquet` (llm-era corpus I/O)

**Context:** Agent-era corpora exchange line-delimited JSON and columnar Parquet by default;
the format enum predates them, forcing products to lie (`format: JSON`) or fork the schema.

Live validator line (0.4.0):

```
/product/dataAccess/default/format: 'JSONL' is not one of
['TOON', 'JSON', 'XML', 'CSV', 'Excel', 'zip', 'plain text', 'GraphQL', 'MCP']
```

Schema truth: `$defs/DataAccessItem/properties/format` = that enum. Note the schema's own
`product.details.*.outputFileFormats` array exists (unconstrained strings), so a legal
"declare elsewhere" workaround exists but breaks access-channel semantics.

Our current mitigation (`04-odps-dataproduct-corpus.yaml` L184–185, quoted):

```yaml
format: JSON           # NOTE: 'JSONL'/'Parquet' not in format enum — upstream PR pending
# x-format: jsonl+zstd
```

**Proposed fix:** add `JSONL` and `Parquet` to the enum (+ `zst` if pairing is
condoned, or guidance to pair `zip`). Pairs well with Issue ② row c cleanup as one PR.

**Evidence:** `06` friction 1 + PR plan; commands above. Our trace-corpus product is a
ready data point: replayable xCABI JSONL + Parquet bundles, currently mis-described as
`JSON` + `x-format`.

---

## Issue ④ — `open-data-products[contracts]` silently skips `datacontract-cli` on Python ≥ 3.13

**Context:** The `[contracts]` extra is gated `python_version < "3.13"` inside the
distribution's deps, so pip resolves the extra to *nothing* on 3.13/3.14 and reports
success while the tooling is simply absent. Users following the Product "audit" path
freshly on 3.13+/3.14 get `DATACONTRACT_CLI_NOT_INSTALLED` at audit time with no hint.

Live evidence (Python 3.14.7, SDK 0.4.0):

```
$ python -m pip install --dry-run --no-deps "open-data-products[contracts]"
Requirement already satisfied: open-data-products[contracts] in ./.../python3.14/site-packages (0.4.0)

$ python -m pip show datacontract-cli
WARNING: Package(s) not found: datacontract-cli
```

Note: `open-data-products[contracts]` checks as "satisfied" while its entry-point tool
is missing — the marker elision makes the extra look installed but empty. Manual fix we
adopted (per 06 "Tooling constraint"): conda/py3.12 venv →
`pip install "open-data-products[contracts]"` → datacontract-cli 1.2.7 lands and audit
goes green (`contract_valid: true`).

**Proposed fix:** either (a) publish a 3.13-sdk datacontract dependency version for the
extra, or (b) at minimum raise a post-install check: the `contracts` entry-point
(auditor) should print a remediation hint to conda/pip pinning when it cannot import
the CLI, instead of the bare `DATACONTRACT_CLI_NOT_INSTALLED` token.

**Evidence:** `06` "Tooling constraint" + residual audit rows; commands above.

---

## Issue ⑤ — ODPS doc examples embed ODCS v2-era contracts (tooling converts with a deprecation clock)

**Context:** Current ODCS on main (v3.0.2; datacontract-cli 1.2.7 lints natively) replaced
the v2.2.2-era vocabulary (`quantumName`, `dataset`, `datasetName`; `servicelevels` →
`slaProperties`) — but ODPS documentation examples and older templates still embed v2-shape
contract snippets. Today the CLI only agrees to read them through an auto-conversion path
that is scheduled for removal in January 2027.

Live evidence (datacontract-cli 1.2.7 linting a v2-shaped snippet):

```
$ datacontract lint v2-token.yaml          # kind/apiVersion 2.2.2, quantumName, dataset...
│ passed  │ Data contract is syntactically valid │
│ warning │ Check that data contract is an ODCS │ Data Contract Specification (DCS) contracts
│         │ contract                            │ are auto-converted to the new ODCS format.
│         │                                     │ Support will be removed in the next major
│         │                                     │ version (January 2027). Convert the contract
```

Also validated empirically during T0 authoring (06 "Authoring learnings"): our contract
was authored directly in ODCS v3.0.2 (`kind: DataContract`, `apiVersion: v3.0.2`,
`schema: [...]`, `slaProperties`) and lints clean; the v2 vocabulary above is the only
translation friction between the two docs.

**Proposed fix:** refresh ODPS doc examples (esp. contract-embedding pages and bundled
older templates) to ODCS v3 vocabulary; link the migration table in the upstream CLI
CHANGELOG so doc consumers can migrate at a glance.

**Evidence:** `06` authoring sections + commands above; our `contracts/corpus-0.1.odcs.yaml`
green under datacontract-cli 1.2.7 as the v3 working example.

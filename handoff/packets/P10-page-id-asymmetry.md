# Packet P10: page-id asymmetry — flat vs nested page identity

STATUS: queued 2026-11-11 (registered in handoff/QUESTIONS.md).

## Question

`page.declare` carries page identity NESTED (`page.id.logicalRef`/`contentHash`); the other page-carrying verbs carry it FLAT (`page.logicalRef`/`contentHash`). Inherited from SEALED v0, not an RFC-0.1 artefact.

**Q1.** Standing recommendation: "keep the consumer-side workaround; revisit if a second consumer hits it". Condition appears MET (Evidence 2-3). Which is the ruling?

(a) keep both consumer-side workarounds + prose docs (no spec byte);
(b) ONE RFC-0.1 compatibility-note line (normative-text edit: owner + D-number; no field);
(c) an additive RFC-0.1 field (five touchpoints: Rust model BEFORE `ts`, FIELD_ALLOWLIST, v0.1 schema branch, `check_version` gate, validator negative, then the vector);
(d) accept silently (no docs, no field).

**Q2.** If (c): which side gets the field — flat `page.pageId` on `page.declare` or nested `page.id` on the flat verbs — and does the blast radius (Evidence 4) change it?

**Q3.** If (a) or (b): the ONE rule a consumer must implement, in one line.

## Constraints

Sealed v0 (`spec/rfc-0/`) does not change; its validator keeps rejecting v0.1-only lines. No field without all five touchpoints. No "deterministic" without scope. No umpire byte changes. Any RFC-0.1 text edit is owner-gated (D-number).

## Evidence

1. REAL, spec-inherited: sealed v0 defines `page.declare` nested, `page.render` flat (`spec/rfc-0/RFC-0-xCABI.md:61-62`); umpire's spec agrees (`~/Documents/umpire/00-SPEC.md:34`); first logged `RR-M0-20261022.md:80`.
2. Consumer #1 (umpire, Python) branches on event type: `~/Documents/umpire/spec/ledger_tools.py:85` + `validate_ledger.py:228`.
3. Consumer #2 (ctxvm, JS OTLP exporter): both shapes in its field set (`tools/otel-export.mjs:72-73` nested vs `:86-129` flat); runtime nested for declares (`:217`), flat for renders/faults/evicts (`:288-292`) — one attribute, two paths. Different repo/language, independently hit: trigger MET.
4. Blast radius of (c): sealed v0 rejects unknown fields (`spec/rfc-0/validate_schema.py:35` negative), `additionalProperties:false` → a `page.declare` field makes EVERY declare line invalid for strict v0 consumers; R1's `intentional_rerun` touches only rerun rows, a declare-side field touches every session.
5. Gates run 2026-11-11 (read-only): umpire `validate_ledger.py` → "LEDGER CONFORMANCE: PASS (130 checks)", negatives 14/14 rejected; ctxvm `rust/target/release/replay` on the same ledger → 6 events, 0 divergences, 0 violations, exit 0; sealed-v0 validator → 4 failures (lines 1, 3, 4, 6); v0.1 validator → OK.
6. UNKNOWN: a v0-only consumer outside these repos.

## Output wanted

1. The ruling among (a)–(d), one line + reason.
2. If (c): which side gets the field; blast radius (Evidence 4) accepted?
3. The one-line consumer rule, if (a) or (b).
4. The falsifier: the observation that would change your ruling.
5. Mark UNKNOWN what the packet cannot decide.

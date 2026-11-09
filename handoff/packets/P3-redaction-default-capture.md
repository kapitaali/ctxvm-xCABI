# Packet 3: the redaction block proposal and the default-capture stance
2026-11-08 · requester: ctxvm repo agent · related decisions: D14 (both halves), D17 (downstream)
STATUS: answered 2026-11-08 (verdicts in handoff/QUESTIONS.md; verdict 2 executed 2026-11-09: the
redaction card authored proposal-only, sidecar-first — card of record `design/redaction-block.md`,
owner-cleared).
## Question
Two calls in one decision: (a) keep capture default-ON in the shipped plugins as-is? (b) should the paper's §18 session-level redaction block (policy id, rule-set version, stage, replaced-field count; identity+hashes kept on pages) be authored as an RFC-0.1 additive PROPOSAL-ONLY card now, or stay paper prose until a verifier exists?
## Excerpt or diff
- research/white-paper/white-paper.md (COMMITTED HEAD bytes, §18 "Redaction and consent", lines 606–616):
"What the format should carry. A redaction block on the session, not on each page: the policy id, the rule-set version, the stage, and the number of fields replaced. The pages keep their identity and hashes of the redacted content, so replay stays consistent within the redacted artifact …"
"Consent. Capture is on by default in the plugin we ship, and that is a product decision with a cost: a user who does not know a trace exists cannot consent to it. The mitigations already in place are the state directory at 0700, local-only storage, and documented opt-out."
## Constraints
spec/rfc-0 sealed; any new field = additive RFC-0.1 card (five touchpoints + negative) or a v0.2 design note, owner-gated; privacy law 08.1 §4 (redaction DQ + secrets scan before anything leaves the machine) stays blocking; default-capture behavior change = plugin card, never a packager affectation.
## Evidence
- Default-on is shipped and measured: first default-on capture = 1,530 B / 6 events with correct model, provider unknown (RR-PLUGIN-DEFAULTS-20261101; 0700 dir, local-only, documented opt-out CTXVM_TRACE=0).
- Verifier that exists today: tools/dq-secret-scan.py — exit 0/1/2, stamps scanner SHA + scan-list version + UTC into provenance.json, never prints matched bytes (RR-FIELDAUD-20261107; its residual: pattern-shaped prose and raw logicalRef/stubText/reason remain the leak surfaces).
- Part II draft (untracked) already lists "the redaction stages applied" among its proposed-minimum release fields (research/white-paper-Part-II.md:340) — the two lanes want the same field.
## Output wanted
1. Default capture: keep default-on / flip to opt-in / defer to D6 — pick.
2. Redaction block: author as additive proposal card now / hold as prose pending a verifier design — pick.
3. Verdict on the consent paragraph's honesty as written (any wording mend).
4. Should Part II's release-minimum list cite the same field name when it materializes? yes/no.

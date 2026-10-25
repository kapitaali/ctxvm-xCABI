# Compliance Layer Planning Document

**Status:** Planning — not yet implemented
**Date:** 2026-10-25
**Scope:** Compliance packaging layer on top of ctxvm traces (HIPAA, SOC2 Type II, financial audit)
**Relationship to ctxvm:** Consumer, not component. Same relationship as umpire: consumes ctxvm artifacts through published interfaces only. Does not modify ctxvm code, spec, or normative files.

---

## 1. The Core Idea

ctxvm is a developer tool. It produces traces, replay, and metrics. The compliance layer is an auditor tool. It consumes ctxvm traces and produces regulatory-specific audit evidence.

The separation is by audience and deliverable, not by technology:

| Dimension | ctxvm | Compliance layer |
|-----------|-------|-----------------|
| User | Developer | Auditor / compliance officer |
| Input | Agent session | ctxvm trace (JSONL) |
| Output | Trace, replay result, KPIs | Audit report, retention archive, certification evidence |
| Interface | CLI, plugin | Web dashboard, report generator, API |
| Value proposition | "What did the agent see?" | "Prove to the regulator what the agent saw" |

The compliance layer does not modify ctxvm. It reads traces, maps ctxvm events to regulatory requirements, enforces retention, and generates auditor-facing reports.

---

## 2. Why This Is a Separate Product

Three conditions make this a separate product, not a ctxvm feature:

1. **Different user.** ctxvm's user is a developer who wants to debug, optimize, or hand off sessions. The compliance layer's user is an auditor or compliance officer who wants to verify that controls are operating. These are different people with different needs, different vocabularies, and different success criteria.

2. **Different deliverable.** ctxvm delivers traces and metrics. The compliance layer delivers audit reports, retention archives, and certification evidence. A developer wants `ctxvm replay` exit code 0. An auditor wants a PDF that says "control CC6.1 operated continuously from Jan to Jun, evidence attached."

3. **Different lifecycle.** ctxvm traces are ephemeral (session-scoped, exported on demand). Compliance evidence must be retained for 6 years (HIPAA), 6-12 months (SOC2 Type II audit period), or indefinitely (financial regulatory). The compliance layer manages retention, access control, and archival — concerns that have no place in ctxvm's design.

---

## 3. The Three Verticals

### 3.1 HIPAA (highest priority)

**Regulatory requirement:** HIPAA Security Rule requires audit controls that record and examine activity in systems handling electronic protected health information (ePHI). Records must include timestamp, accessor identity, action performed, and reference to PHI accessed. Retention: 6 years minimum. Integrity controls to protect logs from alteration.

**What ctxvm provides:**
- Page-level tracking of what data entered context (page.declare with logical_ref and content_hash)
- Deterministic replay (byte-identical re-render, exit code 0)
- SHA-256 checksums on all artifacts (tamper evidence)
- `skipped_untraced` counter (detects undeclared context — a fidelity gap)
- Touch ratio (which pages the model actually read vs. had access to)

**What the compliance layer adds:**

| Requirement | ctxvm provides | Compliance layer adds |
|-------------|---------------|----------------------|
| Audit trail | Trace (JSONL) | HIPAA-format audit report with event mapping |
| Accessor identity | Agent ID | User-level identity attribution (who initiated the session) |
| PHI reference | logical_ref + content_hash | PHI field-level tracking (which fields were read vs. present) |
| "Minimum necessary" | Touch ratio per page | Compliance dashboard: pages with touch_ratio=0 that contained PHI |
| Retention | On-demand export | 6-year retention with integrity verification |
| Integrity | SHA-256 checksums | Tamper-evident archive with chain-of-custody |
| Breach notification | Not applicable | 60-day reporting support (which sessions touched which PHI) |

**The key mapping:** HIPAA's "minimum necessary" standard (Privacy Rule) requires that access to PHI be limited to the minimum necessary to accomplish the intended purpose. ctxvm's touch ratio directly measures this: if a page contained PHI and touch_ratio = 0, the agent had access to more PHI than it needed. This is a HIPAA finding, not just a waste metric.

**Product shape:** "HIPAA-compliant agent audit trail" — a service that ingests ctxvm traces from healthcare agent deployments, maps page.declare events to PHI access events, generates HIPAA-format audit reports, enforces 6-year retention, and alerts on "minimum necessary" violations.

### 3.2 SOC2 Type II

**Regulatory requirement:** SOC2 Type II (not Type I) covers a sustained audit period (6-12 months). Relevant trust service criteria: CC6 (logical and physical access controls), CC7 (system operations monitoring), CC8 (change management), CC9 (risk mitigation). Audit evidence must show controls operating continuously, not just at audit time.

**What ctxvm provides:**
- Continuous trace generation (every turn, every session)
- ODPS packaging with DQ checks (replay determinism, pin lint, redaction scan)
- KPI tracking over time (fault recall, net token reduction, touch ratio, thrash index)
- SHA-256 checksums (evidence integrity)

**What the compliance layer adds:**

| Requirement | ctxvm provides | Compliance layer adds |
|-------------|---------------|----------------------|
| Continuous evidence | Traces | Monitoring dashboard with anomaly alerts |
| CC6 (access controls) | Agent ID in trace | Fine-grained access attribution (user → agent → tool → data) |
| CC7 (monitoring) | KPIs | Automated alerting on KPI degradation (thrash_index spike, fault_recall drop) |
| CC8 (change management) | Not applicable | Correlation between config/prompt changes and session behavior changes |
| CC9 (risk mitigation) | Not applicable | Risk scoring based on context pressure, fault rates, touch ratios |
| Retention | On-demand export | Continuous archival throughout audit period |
| Auditor interface | CLI + JSONL | SOC2-specific report format (auditor-facing, not developer-facing) |

**The key mapping:** SOC2 CC7 requires system operations monitoring. ctxvm's KPIs (thrash_index, fault_recall, touch_ratio) are operational metrics that demonstrate the system is being monitored. The compliance layer surfaces these as SOC2 evidence: "thrash_index remained below 0.5 for 99.2% of sessions during the audit period."

**Product shape:** Less clearly a separate product than HIPAA. SOC2 compliance is broader (it covers the entire system, not just AI agents). The compliance layer's SOC2 module would be a feature of a larger SOC2 compliance platform, not a standalone product. ctxvm traces are one input among many.

### 3.3 Financial audit (SR 11-7, DORA, NYDFS Part 500, EU AI Act)

**Regulatory requirement:** Financial regulators require complete traceability of AI-driven decisions. SR 11-7 (Federal Reserve) requires model documentation, validation, and ongoing monitoring. DORA (EU) requires ICT risk management and incident reporting. NYDFS Part 500 requires cybersecurity controls. EU AI Act requires fundamental rights impact assessment and serious incident reporting for high-risk systems.

**What ctxvm provides:**
- Full decision trail (every page declared, rendered, evicted, faulted)
- Per-turn cost attribution (call.meta with cache estimates)
- Latency tracking (page.fault latencyMs)
- Deterministic replay (regulators can re-run any decision)
- KPI tracking over time (drift detection via thrash_index trends)

**What the compliance layer adds:**

| Requirement | ctxvm provides | Compliance layer adds |
|-------------|---------------|----------------------|
| Decision traceability | Full trace | Regulatory report format (SR 11-7, DORA, NYDFS) |
| Model documentation | Not applicable | Model identity, version, weights hash, training data provenance |
| Validation evidence | Replay determinism | Performance standard comparison (model vs. baseline) |
| Drift detection | KPI trends | Automated alerting + drift report |
| Human oversight | Not applicable | Human approval/rejection evidence for agent decisions |
| Incident reporting | Fault events | Serious incident detection and EU AI Act reporting format |
| Retention | On-demand export | Regulatory retention period (varies by jurisdiction) |

**The key mapping:** SR 11-7 requires "documentation of purpose, training data, and testing methodology" for each model. ctxvm doesn't track model-level metadata, but the compliance layer could correlate ctxvm traces with model registry entries (which model, which version, which weights were used for each session). The trace provides the "what happened"; the model registry provides the "what model"; the compliance layer joins them.

**Product shape:** The most likely standalone product. Financial services have the strictest requirements, the highest willingness to pay, and the most established audit culture. A "financial AI audit trail" product built on ctxvm traces could be a real business. But it needs model-level documentation that ctxvm doesn't track — this is a gap that the compliance layer must fill independently.

---

## 4. The Product Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Compliance Layer                      │
│  ┌───────────┐ ┌───────────┐ ┌──────────────────┐  │
│  │ HIPAA     │ │ SOC2      │ │ Financial Audit  │  │
│  │ module    │ │ module    │ │ module           │  │
│  └─────┬─────┘ └─────┬─────┘ └────────┬─────────┘  │
│        │             │                │             │
│  ┌─────┴─────────────┴────────────────┴─────────┐  │
│  │         Compliance Core                       │  │
│  │  - Event-to-requirement mapping                │  │
│  │  - Retention policy engine                    │  │
│  │  - Identity attribution                       │  │
│  │  - Report generator                           │  │
│  │  - Auditor dashboard                          │  │
│  └─────────────────────┬─────────────────────────┘  │
└────────────────────────┼─────────────────────────────┘
                         │ reads
┌────────────────────────┼─────────────────────────────┐
│                 ctxvm (unchanged)                     │
│  ┌──────────┐ ┌──────────┐ ┌────────────────────┐  │
│  │ Tracer   │ │ Replay   │ │ Metric Simulator   │  │
│  │ (JSONL)  │ │ Engine   │ │ (KPIs)             │  │
│  └──────────┘ └──────────┘ └────────────────────┘  │
│  ┌──────────┐ ┌──────────┐                         │
│  │ ODPS     │ │ Schema   │                         │
│  │ Export   │ │ Validator│                         │
│  └──────────┘ └──────────┘                         │
└─────────────────────────────────────────────────────┘
```

**Key principle:** The compliance layer reads ctxvm artifacts. It never writes to ctxvm. It never modifies ctxvm code, spec, or normative files. Same boundary as umpire.

---

## 5. The Event-to-Requirement Mapping

The compliance layer's core function is mapping ctxvm events to regulatory requirements. This is the IP.

| ctxvm event | HIPAA requirement | SOC2 criterion | Financial audit |
|-------------|-------------------|----------------|-----------------|
| `session.open` | Accessor identity, system identification | CC6 (access control), CC9 (risk) | Model documentation, system identification |
| `page.declare` | PHI access event (data entered context) | CC6 (data access) | Data access event |
| `page.render` | What the agent actually saw (full or stub) | CC7 (monitoring) | Decision context reconstruction |
| `page.evict` | Data removed from context (retention control) | CC8 (change management) | Context lifecycle event |
| `page.fault` | Data re-requested (access pattern) | CC7 (monitoring) | Decision re-evaluation trigger |
| `turn.render` | Context pressure at decision time | CC7 (monitoring) | Decision context snapshot |
| `call.meta` | Cost and latency of decision | CC7 (monitoring) | Cost and latency attribution |

This mapping is the compliance layer's core value. It's not just "here's the trace" — it's "here's how each trace event satisfies a specific regulatory requirement."

---

## 6. Prioritization

| Vertical | Priority | Rationale |
|----------|----------|-----------|
| HIPAA | 1 | Clearest requirements, "minimum necessary" maps to touch ratio, highest regulatory risk, 6-year retention creates recurring revenue |
| Financial audit | 2 | Highest willingness to pay, most established audit culture, but needs model-level documentation that ctxvm doesn't track |
| SOC2 | 3 | Broadest market, but less differentiated — SOC2 is about the whole system, not just AI agents. ctxvm traces are one input among many. |

**Recommended starting point:** HIPAA. The "minimum necessary" requirement is unique to healthcare and maps directly to ctxvm's touch ratio KPI. No other tracing tool measures this. The compliance layer's HIPAA module would be the only product that can prove "the agent had access to 47 PHI fields but only read 3 of them."

---

## 7. What Needs to Be Built

### Phase 1: Event mapping (no new infrastructure)
- Map ctxvm events to regulatory requirements (table above)
- Define the compliance report schema (what fields, what format)
- Build the report generator (trace → regulatory report)

### Phase 2: Retention and identity
- Retention policy engine (6 years HIPAA, configurable)
- Identity attribution layer (user → agent → session)
- Integrity verification (chain-of-custody for archived traces)

### Phase 3: "Minimum necessary" analysis (HIPAA-specific)
- PHI field-level tracking (which fields were in context vs. read)
- Touch ratio as a compliance metric
- Automated "minimum necessary" violation alerts

### Phase 4: Auditor interface
- Web dashboard for compliance officers (not developers)
- Auditor-facing report format (PDF, not JSONL)
- Evidence packaging for external auditors

### Phase 5: Model-level documentation (financial audit)
- Model registry integration (which model, which version, which weights)
- Drift detection alerting
- Human-in-the-loop evidence capture

---

## 8. What ctxvm Must NOT Change

The compliance layer must not require changes to ctxvm. Specifically:

- ctxvm's trace format stays sealed (RFC-0). The compliance layer reads the existing event vocabulary.
- ctxvm's core engine stays pure (no LLM, no embedding, no network). The compliance layer can use LLMs for report generation, but not inside ctxvm.
- ctxvm's metric simulator stays as-is. The compliance layer can compute additional metrics, but doesn't modify the four existing KPIs.
- ctxvm's ODPS packaging stays at the edge. The compliance layer can re-package traces, but doesn't modify the ODPS export.

If the compliance layer needs data that ctxvm doesn't capture (e.g., user identity, model version), it must capture that data independently and join it to ctxvm traces by session ID. It cannot require ctxvm to add new event types or fields.

---

## 9. Open Questions

1. **HIPAA "minimum necessary" granularity:** ctxvm tracks page-level touch ratio, not field-level. If a page contains 50 PHI fields and the model reads 3, the touch ratio is 1.0 (the page was touched) but the "minimum necessary" violation is at the field level. Does the compliance layer need field-level tracking, or is page-level sufficient for HIPAA?

2. **Retention cost:** 6-year retention of all traces for all sessions is expensive. Can the compliance layer archive traces in compressed form and only decompress on audit request? ctxvm's zstd compression (used in B3 resume) could help.

3. **Identity attribution:** ctxvm traces don't include user identity. The compliance layer must capture this separately. Should it be a separate identity service, or integrated into the tracer? If integrated, it modifies the tracer — violating the "ctxvm must not change" principle. If separate, it requires a join key (session ID) that both systems agree on.

4. **Model registry:** Financial audit requires model-level documentation. Does the compliance layer maintain its own model registry, or does it integrate with an existing one (MLflow, Weights & Biases)? If existing, the integration is an adapter, not a new system.

5. **Certification:** Can the compliance layer itself be certified (HIPAA, SOC2)? Or does it just produce evidence that the customer's system is compliant? The answer affects the product's value proposition and pricing.

---

## 10. The One-Line Summary

The compliance layer is to ctxvm what umpire is to ctxvm: a separate product that consumes ctxvm artifacts and adds value for a different audience. ctxvm answers "what did the agent see?" The compliance layer answers "prove to the regulator what the agent saw." The trace is the evidence; the compliance layer is the courtroom.

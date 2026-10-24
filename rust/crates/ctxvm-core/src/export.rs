//! Export: the handoff snapshot builder (UC1 §2–§3, T21).
//!
//! At a handoff turn N the trace up to N must be a complete, self-contained
//! snapshot of what the model has seen (UC1: the trace up to turn N is the
//! determinism unit). The snapshot ships two derived artifacts — the trace
//! slice itself and the page-table snapshot (`derive_projection(&prefix, N)`)
//! — plus DQ checks over both (replay determinism, source fidelity, pin lint,
//! redaction scan) and the three memo KPIs.
//!
//! ## The slice rule (pinned here for RFC-0)
//!
//! The slice for turn N is the **positional prefix** `events[..= cut]` where
//! `cut` is the LAST index whose event carries a turn `≤ N`. Turn-less events
//! before that index are kept (declaration bookkeeping, `session.open`,
//! `page.pin`/`page.unpin`); turn-less events after it — true trailing
//! bookkeeping emitted beyond the last turn fact — are excluded.
//!
//! The prefix stays honest even though tail-flushed tracer streams interleave
//! turns physically (turn-level facts flush at `finish()`, each row carrying
//! its own turn label, so rows of turns `> N` can be swept into the prefix):
//! `Playback::mode_at(N)` ignores every state change whose effective turn is
//! `> N`, so swept-in decisions are inert for the turn-N projection. The only
//! projection-forming inputs are turn-less declares (all pre-cut for
//! tracer-ordered streams) and changes with turn `≤ N` (all pre-cut by the
//! cut's own definition — `cut` is the maximum position among those events).
//!
//! Two properties fall out (both test-gated here):
//! - `replay(&slice)` is divergence-free whenever the source is clean: any
//!   fact inside the prefix derives from changes with turn ≤ (its turn) ≤ N,
//!   which are all pre-cut; swept-in facts check against the same schedule
//!   the source fed.
//! - `diff_traces(slice, source)` is an extension relation with a shared
//!   positional prefix — the UC1 §3 step-4 verify UX (`diff session-a.jsonl
//!   trace-142.jsonl` → "shared prefix matches; only new events after 142").

use serde::Serialize;

use ctxvm_codec::{Event, RenderMode};

use crate::diff::{diff_traces, event_turn, TraceRelation};
use crate::page_table::Playback;
use crate::replay::{replay, ReplayReport};
use crate::render::TurnProjection;

/// The trace prefix for turn N: events up to and including the last event
/// whose turn is ≤ N (see the slice rule in the module docs). Equal to the
/// whole input when N ≥ the stream's maximum turn.
pub fn handoff_prefix(events: &[Event], turn: u64) -> &[Event] {
    let cut = events
        .iter()
        .rposition(|e| event_turn(e).is_some_and(|t| t <= turn))
        .map_or(0, |i| i + 1);
    &events[..cut]
}

/// Credential-shaped plaintext patterns the v0 redaction scan looks for over
/// the artifact texts (basic hygiene, not a full redaction review).
pub const REDACTION_PATTERNS: &[&str] =
    &["sk-", "AKIA", "ghp_", "github_pat_", "xoxb-", "xoxp-", "Bearer "];

/// One pattern and how often it appeared in the scanned text.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RedactionHit {
    pub pattern: String,
    pub hits: usize,
}

/// Scan artifact text for credential-shaped patterns (counts, in pattern order).
pub fn scan_redaction(text: &str) -> Vec<RedactionHit> {
    REDACTION_PATTERNS
        .iter()
        .map(|p| RedactionHit {
            pattern: (*p).to_string(),
            hits: text.matches(p).count(),
        })
        .collect()
}

/// The three memo KPIs (UC1 §3: fault recall, net token reduction, touch
/// ratio), computed over the slice. `None` marks a vacuous denominator (the
/// KPI is reported as `null` rather than a fabricated value).
#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct HandoffKpis {
    /// Faults recorded at some turn ≤ N whose page is Full again at N.
    /// None when the slice carries no faults.
    pub fault_recall: Option<f64>,
    /// stubbedTokens ÷ (resident + stubbed tokens) at the slice turn — the
    /// v0 stub-cost fraction (policy-free; policy-vs-policy "net" is UC3).
    /// None when the turn carries no tokens at all.
    pub net_token_reduction: Option<f64>,
    /// Distinct pages with a recorded full `page.render` (turn ≤ N) ÷ the
    /// declared slot roster of the snapshot. None when no pages are declared.
    pub touch_ratio: Option<f64>,
}

/// Handoff snapshot: slice-shape bookkeeping, the replay counterproof over the
/// slice, the derived page-table state, the pin lint, and the KPIs.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct HandoffSnapshot {
    /// The slice turn (all kept facts have turn ≤ this).
    pub turn: u64,
    /// Events in the source stream.
    pub source_events: usize,
    /// Events kept in the slice (`handoff_prefix(source, turn).len()`).
    pub kept_events: usize,
    /// Events excluded (turn > N plus trailing turn-less bookkeeping).
    pub dropped_events: usize,
    /// Slice-internal replay counterproof — the `replayDeterminism` DQ check.
    pub replay: ReplayReport,
    /// Derived page-table state at the slice turn (the `page-table-N.json`).
    pub projection: TurnProjection,
    /// Relation of the slice to the source (`BExtendsA` = the source extends
    /// the shared positional prefix; `Identical` = the full export).
    pub relation_to_source: TraceRelation,
    /// Length of the shared positional prefix (`kept_events` on a well-formed
    /// export; surfaced so consumers can cross-check with `ctxvm diff`).
    pub source_common_prefix_events: usize,
    /// Pin-lint hits: pin-family playback violations in the slice plus slots
    /// pinned yet stubbed at the slice turn (working-set zombies).
    pub pin_lint: Vec<String>,
    /// The three KPIs over the slice.
    pub kpis: HandoffKpis,
}

impl HandoffSnapshot {
    /// The manifest's three DQ checks, in ODPS-flavored dimension naming.
    pub fn replay_determinism(&self) -> bool {
        self.replay.divergences.is_empty()
    }

    /// The source extends the slice exactly (shared positional prefix match) —
    /// the export-side witness of the UC1 verify UX.
    pub fn source_fidelity(&self) -> bool {
        matches!(
            self.relation_to_source,
            TraceRelation::BExtendsA | TraceRelation::Identical
        ) && self.source_common_prefix_events == self.kept_events
    }
}

/// Build the turn-N handoff snapshot over a full source stream.
///
/// Pure: same input → byte-identical report (constituent shapes are
/// deterministic over the fed decision stream; rosters iterate in
/// declaration order, violations in stream order).
pub fn build_handoff_snapshot(source: &[Event], turn: u64) -> HandoffSnapshot {
    let prefix = handoff_prefix(source, turn);

    let mut pb = Playback::new();
    pb.feed_all(prefix);
    let projection = pb.projection_at(turn);

    // Fault recall: faults recorded at some turn ≤ N whose page is Full at N.
    let mut fault_total = 0usize;
    let mut fault_recovered = 0usize;
    for event in prefix {
        if let Event::PageFault { turn: t, page, .. } = event {
            if *t <= turn {
                fault_total += 1;
                if pb
                    .page(page)
                    .is_some_and(|track| track.mode_at(turn) == RenderMode::Full)
                {
                    fault_recovered += 1;
                }
            }
        }
    }

    // Touch: distinct page identities with a recorded full render, turn ≤ N…
    let mut touched: std::collections::BTreeSet<String> = std::collections::BTreeSet::new();
    for event in prefix {
        if let Event::PageRender { turn: t, page, mode: RenderMode::Full } = event {
            if *t <= turn {
                touched.insert(format!("{}|{}", page.logical_ref, page.content_hash));
            }
        }
    }
    // …over the declared slot roster of the snapshot.
    let declared = projection.slots.len();

    let kpis = HandoffKpis {
        fault_recall: (fault_total > 0)
            .then(|| fault_recovered as f64 / fault_total.max(1) as f64),
        net_token_reduction: {
            let total = projection.tally.resident_tokens + projection.tally.stubbed_tokens;
            (total > 0).then(|| projection.tally.stubbed_tokens as f64 / total as f64)
        },
        touch_ratio: (declared > 0).then(|| touched.len() as f64 / declared as f64),
    };

    // Pin lint: pin-family playback violations (whole slice) + pinned stubs at N.
    let mut pin_lint = Vec::new();
    for violation in pb.violations() {
        let detail = match &violation.kind {
            crate::page_table::ViolationKind::DecisionOfUnknownPage { page, decision } => {
                (*decision == "pin" || *decision == "unpin").then(|| {
                    format!("pin violation: {decision} of undeclared page {}", page.logical_ref)
                })
            }
            crate::page_table::ViolationKind::EvictWhilePinned { page } => Some(format!(
                "pin violation: evicted pinned page {}",
                page.logical_ref
            )),
            crate::page_table::ViolationKind::UnpinOfUnpinned { page } => Some(format!(
                "pin violation: unpin of unpinned page {}",
                page.logical_ref
            )),
            _ => None,
        };
        if let Some(detail) = detail {
            pin_lint.push(detail);
        }
    }
    for slot in &projection.slots {
        if slot.pinned && slot.mode == RenderMode::Stub {
            pin_lint.push(format!(
                "pin lint: pinned page {} is stubbed at turn {} (working-set zombie)",
                slot.reference.id.logical_ref, turn
            ));
        }
    }

    let slice_diff = diff_traces(prefix, source);

    HandoffSnapshot {
        turn,
        source_events: source.len(),
        kept_events: prefix.len(),
        dropped_events: source.len() - prefix.len(),
        replay: replay(prefix),
        projection,
        relation_to_source: slice_diff.relation,
        source_common_prefix_events: slice_diff.common_prefix_events,
        pin_lint,
        kpis,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ctxvm_codec::{CacheEstimate, FaultSource, PageId, PageKind, PageRef};

    fn open() -> Event {
        Event::SessionOpen {
            agent_id: "harness".into(),
            model: "m".into(),
            provider: "p".into(),
            budget_tokens: 120000,
            tokenizer_id: "apx4-char".into(),
        }
    }

    fn declare(logical: &str, hash: &str, tokens: u64) -> Event {
        Event::PageDeclare {
            page: PageRef {
                id: PageId {
                    logical_ref: logical.into(),
                    content_hash: hash.into(),
                },
                kind: PageKind::File,
                tokens,
            },
        }
    }

    fn pid(logical: &str, hash: &str) -> PageId {
        PageId { logical_ref: logical.into(), content_hash: hash.into() }
    }

    fn evict(turn: u64, logical: &str, hash: &str) -> Event {
        Event::PageEvict {
            turn,
            page: pid(logical, hash),
            stub_text: "[stub] re-call the tool to re-materialize".into(),
        }
    }

    fn fault(turn: u64, logical: &str, hash: &str) -> Event {
        Event::PageFault {
            turn,
            page: pid(logical, hash),
            source: FaultSource::ToolRecall,
            latency_ms: None,
        }
    }

    fn render_full(turn: u64, logical: &str, hash: &str) -> Event {
        Event::PageRender {
            turn,
            page: pid(logical, hash),
            mode: RenderMode::Full,
        }
    }

    fn turn_render(turn: u64, tokens: u64) -> Event {
        Event::TurnRender { turn, resident_tokens: tokens, evicted_tokens: 0, headroom: None }
    }

    fn call_meta(turn: u64) -> Event {
        Event::CallMeta {
            turn,
            provider: "p".into(),
            cache_estimate: CacheEstimate {
                est_hit_tokens: 0,
                est_miss_tokens: 0,
                provider_reported: false,
            },
            latency_ms: None,
        }
    }

    /// Mini tracer-shaped stream over 3 turns: mid-stream decision events
    /// (born at their beat) + a tail-flushed block of turn facts; turn-2
    /// activity sits mid-stream and sweeps into earlier slices, exactly like
    /// the corpus traces. Timing law shape (evict@t → stub visible at t,
    /// fault@t → full from t+1) so the recorded facts replay clean. Note the
    /// `turn.render` rows record the FINAL-schedule derivation per the locked
    /// replay gate (what m3's constant 19 also shows):
    /// - a: evicted @0, never refaulted → Stub @0.. (100 tok)
    /// - b: evicted @1, faulted @1 → Stub @1, Full @2 (50 tok)
    /// - c: declared mid-turn 2 (turn-less), evicted @2, faulted @2 → Full @0..1
    ///   (declared ⇒ in-pool per v0 semantics), Stub @2, Full @3 (30 tok)
    fn flush_tail_stream() -> Vec<Event> {
        vec![
            open(),                       // 0
            declare("file:a", "h-a", 100), // 1
            evict(0, "file:a", "h-a"),     // 2
            declare("tool:b", "h-b", 50),  // 3
            evict(1, "tool:b", "h-b"),     // 4
            fault(1, "tool:b", "h-b"),     // 5
            declare("file:c", "h-c", 30),  // 6  (turn-2 sweep case, turn-less)
            evict(2, "file:c", "h-c"),     // 7  (turn-2 sweep case)
            fault(2, "file:c", "h-c"),     // 8  (turn-2 sweep case)
            render_full(2, "tool:b", "h-b"), // 9  b recovered at turn 2
            render_full(3, "file:c", "h-c"), // 10 c recovered at turn 3
            turn_render(0, 80),            // 11 ─┐  (a stub; b+c Full per the
            turn_render(1, 30),            // 12  │   final schedule accounting)
            turn_render(2, 50),            // 13  │ the tail flush block (turn
            call_meta(0),                  // 14  │ facts flush at end; each row
            call_meta(1),                  // 15  │ carries its own turn label)
            call_meta(2),                  // 16 ─┘
        ]
    }

    fn source_clean(stream: &[Event]) -> bool {
        crate::replay::replay(stream).divergences.is_empty()
    }

    /// Turn-filtered projection state (the union of what the flashed decision
    /// events with turn ≤ N imply) — what the positional prefix must derive.
    #[track_caller]
    fn assert_projection(slice: &[Event], turn: u64, resident: u64, stubbed: u64, slots_r: usize, slots_s: usize) {
        let mut pb = Playback::new();
        pb.feed_all(slice);
        let tally = pb.tally_at(turn);
        assert_eq!(
            (tally.resident_tokens, tally.stubbed_tokens, tally.resident_slots, tally.stubbed_slots),
            (resident, stubbed, slots_r, slots_s),
            "unexpected projection at turn {turn}"
        );
    }

    #[test]
    fn slice_rule_is_positional_prefix_over_the_flush_tail() {
        let src = flush_tail_stream();
        assert!(source_clean(&src), "fixture stream itself replays clean");

        // Turn 1: cut lands on call.meta(1); pre-cut events (including the
        // swept turn-2 interleave and the tail rows with turn ≤ 1) are kept;
        // only the rows after the ≤1 tail are dropped.
        let slice = handoff_prefix(&src, 1);
        assert_eq!(slice.len(), 16, "cut before call.meta(2)");
        assert!(matches!(slice[0], Event::SessionOpen { .. }));
        assert!(matches!(slice[15], Event::CallMeta { turn: 1, .. }));

        // The projection from the slice is the projection the turn-1 facts
        // recorded: a + b stubbed, c Full (its turn-2 changes are inert).
        assert_projection(slice, 1, 30, 150, 1, 2);

        // Full export (N ≥ max turn) is the identity.
        assert_eq!(handoff_prefix(&src, 9), src.as_slice());
    }

    #[test]
    fn replay_and_diff_witness_the_slice() {
        let src = flush_tail_stream();
        let slice = handoff_prefix(&src, 1);

        // Replay determinism: clean source ⇒ clean slice, even with swept-in
        // facts (sweeps check against the same schedule).
        assert!(crate::replay::replay(slice).divergences.is_empty());
        assert!(crate::replay::replay_turn(slice, 1).divergences.is_empty());

        // UC1 §3 step 4: diff(slice, source) = extension relation, shared
        // prefix == slice length.
        let d = diff_traces(slice, &src);
        assert_eq!(d.relation, TraceRelation::BExtendsA);
        assert_eq!(d.common_prefix_events, slice.len());

        let snapshot = build_handoff_snapshot(&src, 1);
        assert!(snapshot.source_fidelity());
        assert!(snapshot.replay_determinism());
        assert_eq!(snapshot.kept_events, 16);
        assert_eq!(snapshot.dropped_events, 1);
        assert_eq!(snapshot.projection.turn, 1);
    }

    #[test]
    fn projection_ignores_swept_turn_two_eviction() {
        let src = flush_tail_stream();
        let slice = handoff_prefix(&src, 1);
        // c's turn-2 evict/fault are swept in (positions 7–8 < cut) but inert
        // for turn 1: c is Full at 1 while a and b are stubbed.
        assert_projection(slice, 1, 30, 150, 1, 2);
    }

    #[test]
    fn trailing_turn_less_bookkeeping_is_excluded() {
        let mut src = flush_tail_stream();
        // Trailing bookkeeping after the last turn fact — excluded by the rule.
        src.push(declare("file:trail", "h-t", 5));
        src.push(Event::PagePin { page: pid("file:trail", "h-t"), reason: "hot".into() });

        let whole = handoff_prefix(&src, 9);
        assert_eq!(whole.len(), src.len() - 2, "trailing declare+pin excluded");
        assert_eq!(whole, &src[..src.len() - 2]);

        // Turn-less bookkeeping BEFORE the cut stays.
        let slice = handoff_prefix(&src, 1);
        assert!(matches!(slice[3], Event::PageDeclare { .. }));
        assert!(matches!(slice[6], Event::PageDeclare { .. }));
    }

    #[test]
    fn kpis_math_and_vacuous_cases() {
        let src = flush_tail_stream();
        let at_one = build_handoff_snapshot(&src, 1);
        // At turn 1: a(100) and b(50) stubbed, c(30) Full.
        assert_eq!(at_one.projection.tally.resident_tokens, 30);
        assert_eq!(at_one.projection.tally.stubbed_tokens, 150);
        assert_eq!(at_one.kpis.fault_recall, Some(0.0), "b faulted @1, still stubbed at 1");
        assert_eq!(at_one.kpis.net_token_reduction, Some(150.0 / 180.0));
        assert_eq!(at_one.kpis.touch_ratio, Some(0.0), "no full renders recorded ≤1");

        // At turn 2: b is Full (50), a and c stubbed (130).
        let at_two = build_handoff_snapshot(&src, 2);
        assert_eq!(at_two.projection.tally.resident_tokens, 50);
        assert_eq!(at_two.projection.tally.stubbed_tokens, 130);
        assert_eq!(at_two.kpis.fault_recall, Some(0.5), "b recovered, c not yet");
        assert_eq!(at_two.kpis.net_token_reduction, Some(130.0 / 180.0));
        assert_eq!(at_two.kpis.touch_ratio, Some(1.0 / 3.0), "b's full render recorded @2");

        // Full export at 4: b and c full (80), a stubbed (100).
        let at_end = build_handoff_snapshot(&src, 4);
        assert_eq!(at_end.projection.tally.resident_tokens, 80);
        assert_eq!(at_end.kpis.fault_recall, Some(1.0));
        assert_eq!(at_end.kpis.net_token_reduction, Some(100.0 / 180.0));

        // A quiet trace: no faults → recall is null, not 0.
        let quiet_src = vec![
            open(),
            declare("file:x", "h-x", 10),
            render_full(0, "file:x", "h-x"),
            turn_render(0, 10),
            call_meta(0),
        ];
        let quiet = build_handoff_snapshot(&quiet_src, 0);
        assert_eq!(quiet.kpis.fault_recall, None);
        assert_eq!(quiet.kpis.net_token_reduction, Some(0.0));
        assert_eq!(quiet.kpis.touch_ratio, Some(1.0));
    }

    #[test]
    fn pin_lint_catches_violations_and_pinned_stubs() {
        let src = vec![
            open(),
            declare("file:p", "h-p", 10),
            Event::PagePin { page: pid("file:p", "h-p"), reason: "hot".into() },
            evict(0, "file:p", "h-p"), // evict-while-pinned violation + stray stub
            turn_render(0, 0),
            call_meta(0),
        ];
        let snapshot = build_handoff_snapshot(&src, 0);
        assert_eq!(snapshot.pin_lint.len(), 2, "violation + pinned-stub zombie");
        assert!(snapshot.pin_lint.iter().all(|detail| detail.contains("file:p")));
        assert!(snapshot.pin_lint.iter().any(|d| d.contains("evicted pinned page")));
        assert!(snapshot.pin_lint.iter().any(|d| d.contains("stubbed at turn 0")));

        let clean = build_handoff_snapshot(&flush_tail_stream(), 1);
        assert!(clean.pin_lint.is_empty());
    }

    #[test]
    fn redaction_scan_counts_in_pattern_order() {
        let text = "tok: sk-abc123 AKIA0123456789ABCDEF ghp_ xoxb-x Bearer xyz sk-";
        let hits = scan_redaction(text);
        let count = |p: &str| hits.iter().find(|h| h.pattern == p).map(|h| h.hits);
        assert_eq!(count("sk-"), Some(2));
        assert_eq!(count("AKIA"), Some(1));
        assert_eq!(count("ghp_"), Some(1));
        assert_eq!(count("xoxb-"), Some(1));
        assert_eq!(count("Bearer "), Some(1));
        assert_eq!(scan_redaction("clean trace text").iter().map(|h| h.hits).sum::<usize>(), 0);
    }

    #[test]
    fn dq_gate_flags_dirty_slice() {
        // A recorded fact that the derived schedule cannot reproduce stays
        // dirty inside the slice — the DQ gate IS the replay gate.
        let mut src = flush_tail_stream();
        src.push(Event::TurnRender { turn: 4, resident_tokens: 999, evicted_tokens: 0, headroom: None });
        let snapshot = build_handoff_snapshot(&src, 4);
        assert!(!snapshot.replay_determinism());
        assert!(snapshot.replay.divergences.iter().any(|d| matches!(
            d,
            crate::replay::Divergence::ResidentTokensMismatch { turn: 4, .. }
        )));
        // The extension witnesses still hold (the slice is a true prefix).
        assert!(snapshot.source_fidelity());
    }
}

//! Profile: forensic aggregation over a trace — the UC2 phase-2/3 surface.
//!
//! Pure derived view of the decision ledger (no fact checking — that is
//! `replay`'s job): per-page decision history in declaration order, fault and
//! eviction rows in stream order, per-turn token tallies at recorded
//! `turn.render` facts, end-state summary + violations. Everything here is a
//! deterministic function of the event slice; "touched"/waste semantics stay in
//! the metric simulator (`benchmarks/metrics/metrics.py`) — this module never
//! re-derives them.

use std::collections::{BTreeMap, BTreeSet};

use serde::Serialize;

use ctxvm_codec::{Event, FaultSource, PageId, PageRef, RenderMode};

use crate::page_table::{Playback, Violation};
use crate::render::TurnTally;

/// Per-page decision history, in first-declaration order.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PageProfile {
    pub reference: PageRef,
    /// 0-based stream index of the page's first `page.declare`.
    pub declared_at_event: usize,
    /// `page.evict` rows against this page.
    pub evictions: usize,
    /// Faults against this page, by source.
    pub fault_sources: BTreeMap<FaultSource, usize>,
    /// Scheduled mode after the stream (u64::MAX turn — all changes applied).
    pub mode_after_stream: RenderMode,
    /// The stub text a final stub would show (verbatim from the last evict).
    pub last_stub_text: Option<String>,
    pub pinned: bool,
}

/// Whole-trace aggregates derived from the rows below (never re-derived by the CLI).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ProfileSummary {
    pub events: usize,
    pub pages: usize,
    /// Pages whose mode after the stream is Full.
    pub resident_at_end: usize,
    /// Pages whose mode after the stream is Stub.
    pub stubbed_at_end: usize,
    /// Σ declared tokens over all pages (the naive-stuffing window cost).
    pub declared_tokens: u64,
    pub evictions: usize,
    pub faults: usize,
    /// Pages never faulted — the waste-candidate roster the memo worries about.
    pub faultless_pages: usize,
    /// Σ declared tokens on those never-faulted pages.
    pub faultless_tokens: u64,
    /// Distinct turns referenced by any scheduled decision (evict/fault) or
    /// `turn.render` fact.
    pub turns_with_rows: usize,
}

/// One `page.fault`, stream order.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FaultRow {
    pub turn: u64,
    pub page: PageId,
    pub source: FaultSource,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub latency_ms: Option<u64>,
}

/// One `page.evict`, stream order.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct EvictRow {
    pub turn: u64,
    pub page: PageId,
    pub stub_text: String,
}

/// Full profile outcome (the CLI slices/filters this; the aggregates here stay whole-trace).
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ProfileReport {
    pub summary: ProfileSummary,
    pub pages: Vec<PageProfile>,
    pub faults: Vec<FaultRow>,
    pub evictions: Vec<EvictRow>,
    /// `turn.render` facts' derived tallies, per turn (stream-latest wins on repeats).
    pub turn_tallies: BTreeMap<u64, TurnTally>,
    pub violations: Vec<Violation>,
}

/// Aggregate a trace into the forensic profile view.
pub fn profile(trace: &[Event]) -> ProfileReport {
    let mut pb = Playback::new();
    pb.feed_all(trace);

    // First-declaration stream index per page identity.
    let mut declared_at: BTreeMap<(String, String), usize> = BTreeMap::new();
    for (idx, event) in trace.iter().enumerate() {
        if let Event::PageDeclare { page } = event {
            let key = page_id_key(&page.id);
            declared_at.entry(key).or_insert(idx);
        }
    }

    let mut faults: Vec<FaultRow> = Vec::new();
    let mut evictions: Vec<EvictRow> = Vec::new();
    let mut turn_tallies: BTreeMap<u64, TurnTally> = BTreeMap::new();
    let mut turn_refs: BTreeSet<u64> = BTreeSet::new();
    for event in trace {
        match event {
            Event::PageEvict { turn, page, stub_text } => {
                turn_refs.insert(*turn);
                evictions.push(EvictRow {
                    turn: *turn,
                    page: page.clone(),
                    stub_text: stub_text.clone(),
                });
            }
            Event::PageFault { turn, page, source, latency_ms } => {
                turn_refs.insert(*turn);
                faults.push(FaultRow {
                    turn: *turn,
                    page: page.clone(),
                    source: *source,
                    latency_ms: *latency_ms,
                });
            }
            Event::TurnRender { turn, .. } => {
                turn_refs.insert(*turn);
                turn_tallies.insert(*turn, pb.tally_at(*turn));
            }
            _ => {}
        }
    }

    let pages: Vec<PageProfile> = pb
        .pages_in_declaration_order()
        .map(|track| {
            let reference = track.reference.clone();
            let declared_at_event = declared_at
                .get(&page_id_key(&reference.id))
                .copied()
                .unwrap_or(0);
            let mut evictions_of = 0usize;
            for row in &evictions {
                if row.page == reference.id {
                    evictions_of += 1;
                }
            }
            let mut fault_sources: BTreeMap<FaultSource, usize> = BTreeMap::new();
            for row in &faults {
                if row.page == reference.id {
                    *fault_sources.entry(row.source).or_insert(0) += 1;
                }
            }
            PageProfile {
                declared_at_event,
                evictions: evictions_of,
                fault_sources,
                mode_after_stream: track.mode_at(u64::MAX),
                last_stub_text: track.last_stub_text().map(str::to_owned),
                pinned: track.pins() > 0,
                reference,
            }
        })
        .collect();

    let resident_at_end = pages.iter().filter(|p| p.mode_after_stream == RenderMode::Full).count();
    let stubbed_at_end = pages.iter().filter(|p| p.mode_after_stream == RenderMode::Stub).count();
    let declared_tokens: u64 = pages.iter().map(|p| p.reference.tokens).sum();
    let faultless: Vec<&PageProfile> = pages.iter().filter(|p| p.fault_sources.is_empty()).collect();
    let summary = ProfileSummary {
        events: trace.len(),
        pages: pages.len(),
        resident_at_end,
        stubbed_at_end,
        declared_tokens,
        evictions: evictions.len(),
        faults: faults.len(),
        faultless_pages: faultless.len(),
        faultless_tokens: faultless.iter().map(|p| p.reference.tokens).sum(),
        turns_with_rows: turn_refs.len(),
    };

    ProfileReport {
        summary,
        pages,
        faults,
        evictions,
        turn_tallies,
        violations: pb.violations().to_vec(),
    }
}

fn page_id_key(id: &PageId) -> (String, String) {
    (id.logical_ref.clone(), id.content_hash.clone())
}

/// Parse a `--turns` spec: comma-separated turns or inclusive ranges (`2-4,9`).
/// Returns the expanded turn list in spec order (CLI dedups via a set).
pub fn turn_windows(spec: &str) -> Result<Vec<u64>, String> {
    if spec.trim().is_empty() {
        return Err("turns spec may not be empty".into());
    }
    let mut turns = Vec::new();
    for part in spec.split(',') {
        let part = part.trim();
        if let Some((a, b)) = part.split_once('-') {
            let a: u64 = a
                .trim()
                .parse()
                .map_err(|_| format!("turns spec: `{part}` is not `start-end`"))?;
            let b: u64 = b
                .trim()
                .parse()
                .map_err(|_| format!("turns spec: `{part}` is not `start-end`"))?;
            if a > b {
                return Err(format!("turns spec: `{part}` has start > end"));
            }
            turns.extend(a..=b);
        } else {
            turns.push(
                part.parse()
                    .map_err(|_| format!("turns spec: `{part}` is not a turn number"))?,
            );
        }
    }
    Ok(turns)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::page_table::ViolationKind;
    use ctxvm_codec::{CacheEstimate, PageKind};

    fn declare(logical: &str, hash: &str, tokens: u64) -> Event {
        Event::PageDeclare {
            page: PageRef {
                id: PageId { logical_ref: logical.into(), content_hash: hash.into() },
                kind: PageKind::File,
                tokens,
            },
        }
    }

    fn evict(turn: u64, logical: &str, hash: &str) -> Event {
        Event::PageEvict {
            turn,
            page: PageId { logical_ref: logical.into(), content_hash: hash.into() },
            stub_text: format!("[Paged out: {logical}]"),
        }
    }

    fn fault(turn: u64, logical: &str, hash: &str, source: FaultSource) -> Event {
        Event::PageFault {
            turn,
            page: PageId { logical_ref: logical.into(), content_hash: hash.into() },
            source,
            latency_ms: None,
        }
    }

    fn turn_render(turn: u64, tokens: u64) -> Event {
        Event::TurnRender { turn, resident_tokens: tokens, evicted_tokens: 0, headroom: None }
    }

    fn sample_trace() -> Vec<Event> {
        vec![
            Event::SessionOpen {
                agent_id: "test-agent".into(),
                model: "m".into(),
                provider: "p".into(),
                budget_tokens: 200_000,
                tokenizer_id: "apx4-char".into(),
            },
            declare("file:a", "h-a", 120),
            declare("tool:b", "h-b", 400),
            evict(1, "file:a", "h-a"),
            fault(2, "file:a", "h-a", FaultSource::ToolRecall),
            fault(2, "file:a", "h-a", FaultSource::IdentifierScan),
            turn_render(0, 520),
            turn_render(1, 400),
            call_meta(3),
        ]
    }

    fn call_meta(turn: u64) -> Event {
        Event::CallMeta {
            turn,
            provider: "p".into(),
            cache_estimate: CacheEstimate {
                est_hit_tokens: 400,
                est_miss_tokens: 0,
                provider_reported: false,
            },
            latency_ms: Some(10),
        }
    }

    #[test]
    fn aggregates_match_the_decision_ledger() {
        let trace = sample_trace();
        let p = profile(&trace);
        assert_eq!(p.summary.events, 9);
        assert_eq!(p.summary.pages, 2);
        assert_eq!(p.summary.evictions, 1);
        assert_eq!(p.summary.faults, 2);
        assert_eq!(p.summary.declared_tokens, 520);
        // a faulted twice (two sources), b never — faultless roster is {b}.
        assert_eq!(p.summary.faultless_pages, 1);
        assert_eq!(p.summary.faultless_tokens, 400);
        // a: evicted@1 → stub@1; fault@2 → full from turn 3 ⇒ after stream, Full.
        let a = &p.pages[0];
        assert_eq!(a.reference.id.content_hash, "h-a");
        assert_eq!(a.mode_after_stream, RenderMode::Full);
        assert_eq!(a.evictions, 1);
        assert_eq!(a.fault_sources.get(&FaultSource::ToolRecall), Some(&1));
        assert_eq!(a.fault_sources.get(&FaultSource::IdentifierScan), Some(&1));
        assert_eq!(a.last_stub_text, Some("[Paged out: file:a]".to_string()));
        // b: untouched.
        let b = &p.pages[1];
        assert_eq!(b.mode_after_stream, RenderMode::Full);
        assert!(b.fault_sources.is_empty());
        assert_eq!(b.last_stub_text, None);
        // Tallies keyed by recorded turn.render facts only.
        assert_eq!(p.turn_tallies.len(), 2);
        assert_eq!(p.turn_tallies.get(&1).unwrap().resident_tokens, 400);
        assert_eq!(p.turn_tallies.get(&3), None);
        // Fault rows in stream order with sources.
        assert_eq!(p.faults.len(), 2);
    }

    #[test]
    fn end_state_stays_stub_without_a_fault() {
        let trace = vec![declare("file:a", "h-a", 120), evict(1, "file:a", "h-a")];
        let p = profile(&trace);
        assert_eq!(p.pages[0].mode_after_stream, RenderMode::Stub);
        assert!(p.pages[0].last_stub_text.is_some());
        assert_eq!(p.summary.stubbed_at_end, 1);
        assert_eq!(p.summary.resident_at_end, 0);
        assert_eq!(p.summary.faultless_pages, 1);
    }

    #[test]
    fn profile_is_deterministic_per_input() {
        let t1 = profile(&sample_trace());
        let t2 = profile(&sample_trace());
        assert_eq!(t1, t2);
        assert_eq!(
            serde_json::to_string(&t1).unwrap(),
            serde_json::to_string(&t2).unwrap()
        );
    }

    #[test]
    fn violations_surface_telemetry_first() {
        // Fault of a resident page is a violation, not a divergence — profile rows reflect it.
        let trace = vec![
            declare("file:a", "h-a", 120),
            fault(0, "file:a", "h-a", FaultSource::ExplicitApi),
        ];
        let p = profile(&trace);
        assert_eq!(p.summary.faults, 1);
        assert_eq!(p.faults[0].source, FaultSource::ExplicitApi);
        assert!(matches!(p.violations[0].kind, ViolationKind::FaultOfResidentPage { .. }));
    }

    #[test]
    fn turn_windows_parse_and_reject() {
        assert_eq!(turn_windows("9").unwrap(), vec![9]);
        assert_eq!(turn_windows("2-4,9").unwrap(), vec![2, 3, 4, 9]);
        assert!(turn_windows("").is_err());
        assert!(turn_windows("9-2").is_err());
        assert!(turn_windows("b-2").is_err());
    }
}

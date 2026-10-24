//! Diff: positional two-trace comparison — the UC1 handoff cross-check.
//!
//! The memo's usage (`ctxvm diff session-a.jsonl trace-142.jsonl` → "page-level
//! divergence: only new events after turn 142; shared prefix matches") reduces
//! to a strict positional relation over decoded events:
//!
//! - identical · `a-extends-b` · `b-extends-a` → the shared region matches;
//!   the extension suffix carries everything new (the handoff snapshot case).
//! - `divergent` → the streams disagree inside the shared length; the diff
//!   reports where (event index) plus page-level state delta.
//!
//! Page-level views: declared-only-on-one-side pages (full identity), the
//! divergent-hash class (same logical_ref, disjoint content_hash sets — the M1b
//! A/B shape), and derived resident-token mismatches at common `turn.render`
//! facts. Like `profile`, this is an analytical surface, NOT a fact gate —
//! byte-identity of a single trace is `replay`'s job.

use std::collections::{BTreeMap, BTreeSet};

use serde::Serialize;

use ctxvm_codec::Event;

use crate::page_table::Playback;

/// Which turn an event belongs to, when the event carries one (`page.pin`/
/// `page.unpin` and `session.open` do not; `page.declare` carries no turn in v0).
pub fn event_turn(event: &Event) -> Option<u64> {
    match event {
        Event::PageEvict { turn, .. }
        | Event::PageFault { turn, .. }
        | Event::PageRender { turn, .. }
        | Event::TurnRender { turn, .. }
        | Event::CallMeta { turn, .. } => Some(*turn),
        Event::SessionOpen { .. } | Event::PageDeclare { .. } | Event::PagePin { .. } | Event::PageUnpin { .. } => None,
    }
}

/// Positional relation between the two decoded streams.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TraceRelation {
    /// Byte-for-byte equal as decoded events, same length.
    Identical,
    /// Every event of `b` matches `a`'s stream in order, then `b` continues —
    /// the UC1 handoff expectation (b = original-a-region + new events).
    BExtendsA,
    /// Mirror case: `a` is the extension.
    AExtendsB,
    /// The streams disagree inside the shared length.
    Divergent,
}

/// A page declared on exactly one side (full identity kept separate from refs
/// that exist on both sides with different content).
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PageOnly {
    pub logical_ref: String,
    pub content_hash: String,
}

/// Same logical_ref declared on both sides with disjoint content_hash sets —
/// the divergent-identity class (M1b shape): the two streams observed
/// different content for the same logical page.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DivergentHash {
    pub logical_ref: String,
    /// First-declared hash on A (deterministic: BTreeMap first).
    pub a_hash: String,
    /// First-declared hash on B.
    pub b_hash: String,
}

/// Derived resident-token disagreement at a common recorded turn.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TallyMismatch {
    pub turn: u64,
    pub a_resident: u64,
    pub b_resident: u64,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TraceDiff {
    /// Length of the identical leading run of events (events are compared as
    /// decoded structs — file-level key order/whitespace is not identity).
    pub common_prefix_events: usize,
    /// Set only when `relation` is `divergent` (the 0-based event index where
    /// the two streams first disagree).
    pub first_divergent_event: Option<usize>,
    pub relation: TraceRelation,
    pub a_events: usize,
    pub b_events: usize,
    pub a_last_turn: Option<u64>,
    pub b_last_turn: Option<u64>,
    pub pages_declared_only_in_a: Vec<PageOnly>,
    pub pages_declared_only_in_b: Vec<PageOnly>,
    pub divergent_hash: Vec<DivergentHash>,
    pub tally_mismatches: Vec<TallyMismatch>,
}

/// Positional diff of two event slices (decoded structs; shared prefix vs new).
pub fn diff_traces(a: &[Event], b: &[Event]) -> TraceDiff {
    let common = a.iter().zip(b.iter()).take_while(|(x, y)| x == y).count();
    let relation = if a.len() == b.len() && common == a.len() {
        TraceRelation::Identical
    } else if common == a.len() {
        TraceRelation::BExtendsA
    } else if common == b.len() {
        TraceRelation::AExtendsB
    } else {
        TraceRelation::Divergent
    };

    let mut declared_a: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    let mut declared_b: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    for (side, stream) in [(&mut declared_a, a), (&mut declared_b, b)] {
        for event in stream {
            if let Event::PageDeclare { page } = event {
                side.entry(page.id.logical_ref.clone())
                    .or_default()
                    .insert(page.id.content_hash.clone());
            }
        }
    }
    let only_a = set_minus(&declared_a, &declared_b);
    let only_b = set_minus(&declared_b, &declared_a);
    let mut divergent = Vec::new();
    for (logical_ref, a_hashes) in &declared_a {
        if let Some(b_hashes) = declared_b.get(logical_ref) {
            if a_hashes.is_disjoint(b_hashes) {
                divergent.push(DivergentHash {
                    logical_ref: logical_ref.clone(),
                    a_hash: first_hash(a_hashes),
                    b_hash: first_hash(b_hashes),
                });
            }
        }
    }

    let mut pb_a = Playback::new();
    let mut pb_b = Playback::new();
    pb_a.feed_all(a);
    pb_b.feed_all(b);
    let turns_a: BTreeSet<u64> = a
        .iter()
        .filter_map(|e| match e {
            Event::TurnRender { turn, .. } => Some(*turn),
            _ => None,
        })
        .collect();
    let turns_b: BTreeSet<u64> = b
        .iter()
        .filter_map(|e| match e {
            Event::TurnRender { turn, .. } => Some(*turn),
            _ => None,
        })
        .collect();
    let tally_mismatches = turns_a
        .intersection(&turns_b)
        .filter_map(|turn| {
            let a_resident = pb_a.tally_at(*turn).resident_tokens;
            let b_resident = pb_b.tally_at(*turn).resident_tokens;
            (a_resident != b_resident).then(|| TallyMismatch {
                turn: *turn,
                a_resident,
                b_resident,
            })
        })
        .collect();

    TraceDiff {
        common_prefix_events: common,
        first_divergent_event: (relation == TraceRelation::Divergent).then_some(common),
        relation,
        a_events: a.len(),
        b_events: b.len(),
        a_last_turn: a.iter().filter_map(event_turn).max(),
        b_last_turn: b.iter().filter_map(event_turn).max(),
        pages_declared_only_in_a: only_a,
        pages_declared_only_in_b: only_b,
        divergent_hash: divergent,
        tally_mismatches,
    }
}

fn first_hash(hashes: &BTreeSet<String>) -> String {
    hashes.iter().next().cloned().unwrap_or_default()
}

fn set_minus(
    left: &BTreeMap<String, BTreeSet<String>>,
    right: &BTreeMap<String, BTreeSet<String>>,
) -> Vec<PageOnly> {
    let mut out = Vec::new();
    for (logical_ref, hashes) in left {
        if !right.contains_key(logical_ref) {
            out.extend(hashes.iter().map(|h| PageOnly {
                logical_ref: logical_ref.clone(),
                content_hash: h.clone(),
            }));
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use ctxvm_codec::{CacheEstimate, PageKind, PageRef};

    fn declare(logical: &str, hash: &str, tokens: u64) -> Event {
        Event::PageDeclare {
            page: PageRef {
                id: PageId { logical_ref: logical.into(), content_hash: hash.into() },
                kind: PageKind::File,
                tokens,
            },
        }
    }

    use ctxvm_codec::PageId;

    fn evict(turn: u64, logical: &str, hash: &str) -> Event {
        Event::PageEvict {
            turn,
            page: PageId { logical_ref: logical.into(), content_hash: hash.into() },
            stub_text: "[stub]".into(),
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
                est_hit_tokens: 10,
                est_miss_tokens: 0,
                provider_reported: false,
            },
            latency_ms: None,
        }
    }

    fn base_stream() -> Vec<Event> {
        vec![
            declare("file:a", "h-a", 120),
            declare("tool:b", "h-b", 400),
            evict(1, "file:a", "h-a"),
            turn_render(0, 520),
            turn_render(1, 400),
            call_meta(2),
        ]
    }

    #[test]
    fn identical_and_extension_relations() {
        let a = base_stream();
        let mut b = a.clone();
        b.push(call_meta(3));
        let d = diff_traces(&a, &b);
        assert_eq!(d.relation, TraceRelation::BExtendsA);
        assert_eq!(d.common_prefix_events, 6);
        assert!(d.first_divergent_event.is_none());
        assert_eq!(d.a_events, 6);
        assert_eq!(d.b_events, 7);
        assert!(d.tally_mismatches.is_empty());
        assert!(d.divergent_hash.is_empty());

        let mirror = diff_traces(&b, &a);
        assert_eq!(mirror.relation, TraceRelation::AExtendsB);
        assert_eq!(diff_traces(&a, &a).relation, TraceRelation::Identical);
    }

    #[test]
    fn mid_stream_divergence_locates_the_event() {
        let a = base_stream();
        let mut b = a.clone();
        // B evicts tool:b at turn 1 as well → the decision streams diverge at
        // index 2 and the derived tallies disagree at their common turn fact.
        b.insert(2, evict(1, "tool:b", "h-b"));
        let d = diff_traces(&a, &b);
        assert_eq!(d.relation, TraceRelation::Divergent);
        assert_eq!(d.first_divergent_event, Some(2));
        assert_eq!(d.tally_mismatches.len(), 1);
        assert_eq!(d.tally_mismatches[0].turn, 1);
        assert_eq!(d.tally_mismatches[0].a_resident, 400);
        assert_eq!(d.tally_mismatches[0].b_resident, 0);
        // Last scheduled turn unchanged in both streams.
        assert_eq!(d.a_last_turn, d.b_last_turn);
    }

    #[test]
    fn divergent_hash_and_declared_only_sides() {
        let mut a = base_stream();
        a.insert(0, declare("file:c", "h-c1", 60));
        let mut b = base_stream();
        // same logical ref as a's file:a, different observe hash …
        b[0] = declare("file:a", "h-a2", 120);
        let d = diff_traces(&a, &b);
        assert_eq!(d.pages_declared_only_in_a.len(), 1);
        assert_eq!(d.pages_declared_only_in_a[0].content_hash, "h-c1");
        assert!(d.pages_declared_only_in_b.is_empty());
        assert_eq!(d.divergent_hash.len(), 1);
        assert_eq!(d.divergent_hash[0].logical_ref, "file:a");
        assert_eq!(d.divergent_hash[0].a_hash, "h-a");
        assert_eq!(d.divergent_hash[0].b_hash, "h-a2");
    }

    #[test]
    fn diff_is_deterministic_and_tolerant_of_event_turn_gaps() {
        let a = base_stream();
        let side_a = diff_traces(&a, &a);
        let side_b = diff_traces(&a, &a);
        assert_eq!(side_a, side_b);
        // pin/unpin/declare/session.open carry no turn — event_turn stays None.
        for event in [
            Event::PageDeclare {
                page: PageRef {
                    id: PageId { logical_ref: "x".into(), content_hash: "h".into() },
                    kind: PageKind::File,
                    tokens: 1,
                },
            },
            Event::PagePin { page: PageId { logical_ref: "x".into(), content_hash: "h".into() }, reason: "r".into() },
        ] {
            assert_eq!(event_turn(&event), None);
        }
    }
}

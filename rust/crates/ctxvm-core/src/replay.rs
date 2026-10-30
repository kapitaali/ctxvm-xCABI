//! Replay: re-derive recorded facts from decision events and report divergences.
//!
//! Replay answers the standard's central claim (02 invariant 2/4): any consumer,
//! given only the trace, reconstructs each turn's page/stub composition — and the
//! trace's own `page.render` / `turn.render` facts must agree with the inference.
//!
//! Comparison semantics (documented for RFC-0):
//! - Facts are checked against the FINAL derived schedule (`mode_at(t)` after the
//!   whole stream): replay is a static analysis, not a point-in-time simulation.
//! - A fact referencing a never-declared page is a divergence of its own kind.
//! - `turn.render.residentTokens` is compared against derived resident tokens.
//!   `evictedTokens` is recorded but unchecked in v0 (stub sizes tokenize outside
//!   the decision layer; flagged for RFC-0).
//! - Exit-code contract (`replay` CLI): 0 clean · 1 divergences · 2 usage/IO/parse.

use serde::Serialize;

use ctxvm_codec::{Event, PageId, RenderMode};

use crate::page_table::{Playback, Violation};

/// One disagreement between derived state and recorded facts.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub enum Divergence {
    /// `page.render` mode ≠ inferred mode at that turn.
    RenderModeMismatch {
        turn: u64,
        page: PageId,
        /// What the decision events imply.
        inferred: RenderMode,
        /// What the trace claims was rendered.
        recorded: RenderMode,
    },
    /// `page.render` references a page never declared in the trace.
    RenderOfUnknownPage { turn: u64, page: PageId },
    /// `turn.render.residentTokens` ≠ derived resident tokens at that turn.
    ResidentTokensMismatch {
        turn: u64,
        inferred: u64,
        recorded: u64,
    },
}

/// Full replay outcome: fact counterproof, decision-ledger violations, and size.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ReplayReport {
    /// Total number of stream events consumed.
    pub events: usize,
    /// Facts the decisions could not reproduce (empty = the trace is replay-proved).
    pub divergences: Vec<Divergence>,
    /// Decision-ledger anomalies (informative; not part of the exit gate).
    pub violations: Vec<Violation>,
}

/// Replay a full trace: feed decisions, then check every fact against them.
pub fn replay(trace: &[Event]) -> ReplayReport {
    let mut pb = Playback::new();
    pb.feed_all(trace);
    ReplayReport {
        events: trace.len(),
        divergences: check_facts(trace, &pb, |_| true),
        violations: pb.violations().to_vec(),
    }
}

/// Point-in-time replay: check only the facts recorded **at `turn`**.
///
/// Otherwise identical to [`replay`]: the decision-ledger violations still cover
/// the whole stream (the table must be advanced to its end state because
/// `mode_at` reads the final schedule) and the exit gate stays
/// `divergences.is_empty()`. This is the `--turn N` CLI mode: probe one turn
/// without taking a position on any other turn's facts.
pub fn replay_turn(trace: &[Event], turn: u64) -> ReplayReport {
    let mut pb = Playback::new();
    pb.feed_all(trace);
    ReplayReport {
        events: trace.len(),
        divergences: check_facts(trace, &pb, |t| t == turn),
        violations: pb.violations().to_vec(),
    }
}

/// Fact-check core shared by [`replay`] / [`replay_turn`]. `at` filters which
/// recorded turns are checked (`|_| true` = the whole trace).
fn check_facts(trace: &[Event], pb: &Playback, at: impl Fn(u64) -> bool) -> Vec<Divergence> {
    let mut divergences = Vec::new();
    for event in trace {
        match event {
            Event::PageRender { turn, page, mode, .. } if at(*turn) => match pb.page(page) {
                None => divergences.push(Divergence::RenderOfUnknownPage {
                    turn: *turn,
                    page: page.clone(),
                }),
                Some(track) => {
                    let inferred = track.mode_at(*turn);
                    if inferred != *mode {
                        divergences.push(Divergence::RenderModeMismatch {
                            turn: *turn,
                            page: page.clone(),
                            inferred,
                            recorded: *mode,
                        });
                    }
                }
            },
            Event::TurnRender { turn, resident_tokens, .. } if at(*turn) => {
                let inferred = pb.tally_at(*turn).resident_tokens;
                if inferred != *resident_tokens {
                    divergences.push(Divergence::ResidentTokensMismatch {
                        turn: *turn,
                        inferred,
                        recorded: *resident_tokens,
                    });
                }
            }
            _ => {}
        }
    }
    divergences
}

#[cfg(test)]
mod tests {
    use super::*;
    use ctxvm_codec::{CacheEstimate, PageKind, PageRef};

    fn declare(id: PageId, tokens: u64) -> Event {
        Event::PageDeclare {
            page: PageRef { id, kind: PageKind::File, tokens },
            latency_ms: None,
            ts: None,
            turn: None,
        }
    }

    #[test]
    fn unknown_render_fact_is_its_own_divergence() {
        let trace = [Event::PageRender {
            turn: 0,
            page: PageId { logical_ref: "ghost".into(), content_hash: "h".into() },
            mode: RenderMode::Full,
            ts: None,
        }];
        let report = replay(&trace);
        assert_eq!(report.divergences.len(), 1);
        assert!(matches!(
            report.divergences[0],
            Divergence::RenderOfUnknownPage { turn: 0, .. }
        ));
    }

    #[test]
    fn replay_is_deterministic_on_the_same_trace() {
        let trace = vec![
            declare(
                PageId { logical_ref: "a".into(), content_hash: "h-a".into() },
                100,
            ),
            Event::TurnRender { turn: 0, resident_tokens: 100, evicted_tokens: 0, headroom: None, ts: None },
            Event::TurnRender { turn: 1, resident_tokens: 200, evicted_tokens: 0, headroom: None, ts: None },
            Event::CallMeta {
                turn: 1,
                provider: "p".into(),
                cache_estimate: CacheEstimate {
                    est_hit_tokens: 90,
                    est_miss_tokens: 10,
                    provider_reported: false,
                },
                latency_ms: None,
                provider_usage: None,
                ts: None,
            },
        ];
        let r1 = replay(&trace);
        let r2 = replay(&trace);
        assert_eq!(r1, r2);
        assert_eq!(r1.divergences.len(), 1); // turn 1: 200 ≠ 100
        assert!(matches!(
            r1.divergences[0],
            Divergence::ResidentTokensMismatch { turn: 1, inferred: 100, recorded: 200 }
        ));
    }

    fn turn_probe_trace() -> Vec<Event> {
        vec![
            declare(
                PageId { logical_ref: "a".into(), content_hash: "h-a".into() },
                100,
            ),
            Event::TurnRender { turn: 0, resident_tokens: 100, evicted_tokens: 0, headroom: None, ts: None },
            Event::TurnRender { turn: 1, resident_tokens: 200, evicted_tokens: 0, headroom: None, ts: None },
        ]
    }

    #[test]
    fn replay_turn_checks_only_that_turn() {
        // Whole trace: 1 divergence (turn 1). Point-in-time at turn 0: clean.
        let trace = turn_probe_trace();
        assert_eq!(replay(&trace).divergences.len(), 1);
        assert!(replay_turn(&trace, 0).divergences.is_empty());
        let at_fault_turn = replay_turn(&trace, 1);
        assert_eq!(at_fault_turn.divergences.len(), 1);
        assert!(matches!(
            at_fault_turn.divergences[0],
            Divergence::ResidentTokensMismatch { turn: 1, inferred: 100, recorded: 200 }
        ));
        // A turn with no recorded facts is trivially clean (projection still derived).
        assert!(replay_turn(&trace, 42).divergences.is_empty());
    }

    #[test]
    fn replay_turn_keeps_violations_whole_stream() {
        // Fault of a resident page at turn 0 is a violation (not a divergence);
        // it must appear even when probing turn 1 only.
        let trace = vec![
            declare(
                PageId { logical_ref: "a".into(), content_hash: "h-a".into() },
                100,
            ),
            Event::PageFault {
                turn: 0,
                page: PageId { logical_ref: "a".into(), content_hash: "h-a".into() },
                source: ctxvm_codec::FaultSource::ToolRecall,
                latency_ms: None,
                ts: None,
            },
            Event::TurnRender { turn: 1, resident_tokens: 100, evicted_tokens: 0, headroom: None, ts: None },
        ];
        let report = replay_turn(&trace, 1);
        assert!(report.divergences.is_empty());
        assert_eq!(report.violations.len(), 1);
    }
}

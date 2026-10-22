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

    let mut divergences = Vec::new();
    for event in trace {
        match event {
            Event::PageRender { turn, page, mode } => match pb.page(page) {
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
            Event::TurnRender { turn, resident_tokens, .. } => {
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

    ReplayReport {
        events: trace.len(),
        divergences,
        violations: pb.violations().to_vec(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ctxvm_codec::{CacheEstimate, PageKind, PageRef};

    fn declare(id: PageId, tokens: u64) -> Event {
        Event::PageDeclare {
            page: PageRef { id, kind: PageKind::File, tokens },
        }
    }

    #[test]
    fn unknown_render_fact_is_its_own_divergence() {
        let trace = [Event::PageRender {
            turn: 0,
            page: PageId { logical_ref: "ghost".into(), content_hash: "h".into() },
            mode: RenderMode::Full,
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
            Event::TurnRender { turn: 0, resident_tokens: 100, evicted_tokens: 0, headroom: None },
            Event::TurnRender { turn: 1, resident_tokens: 200, evicted_tokens: 0, headroom: None },
            Event::CallMeta {
                turn: 1,
                provider: "p".into(),
                cache_estimate: CacheEstimate {
                    est_hit_tokens: 90,
                    est_miss_tokens: 10,
                    provider_reported: false,
                },
                latency_ms: None,
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
}

//! ctxvm-conformance — golden vectors + replay conformance.
//!
//! The vector artifacts under `vectors/` are the executable truth of the xCABI v0
//! trace standard: any binding (Rust, TS, Py) passes iff it roundtrips them
//! byte-identically. T1b wires the codec layer; T1d adds replay semantics on top.

/// All nine documented event verbs of xCABI v0 (`02-xcabi-events-v0.md` §Events).
/// Public: other crates (and future bindings) may reuse the vocabulary gate.
pub const EXPECTED_TAGS: [&str; 9] = [
    "session.open",
    "page.declare",
    "page.render",
    "page.evict",
    "page.fault",
    "page.pin",
    "page.unpin",
    "turn.render",
    "call.meta",
];

/// Shared run cores for the four CLI bins — the single serialization /
/// exit-code sites (byte-identity contract for the ctxvm-py binding, see the
/// module docs). Since UC1-B1 the bins are thin mains that drive these.
pub mod cli;

#[cfg(test)]
mod tests {
    use super::*;
    use ctxvm_codec::{parse_line, read_jsonl, to_line, write_jsonl, RenderMode};

    const VECTORS: &str = include_str!("../vectors/events-v0.jsonl");

    #[test]
    fn vector_file_roundtrips_byte_identical() {
        let events = read_jsonl(VECTORS).expect("vector file must parse");
        assert_eq!(
            write_jsonl(&events),
            VECTORS,
            "vector file is not canonical: written form diverges from committed bytes"
        );
    }

    #[test]
    fn every_vector_line_roundtrips_individually() {
        for (idx, line) in VECTORS.lines().enumerate() {
            let event = parse_line(line).unwrap_or_else(|e| panic!("line {}: {e}", idx + 1));
            assert_eq!(to_line(&event), line, "line {} not canonical", idx + 1);
        }
    }

    #[test]
    fn vector_file_covers_all_nine_event_types() {
        let events = read_jsonl(VECTORS).expect("vector file must parse");
        let mut tags: Vec<&str> = events.iter().map(|e| e.tag()).collect();
        tags.sort_unstable();
        tags.dedup();
        let mut expected = EXPECTED_TAGS.to_vec();
        expected.sort_unstable();
        assert_eq!(tags, expected, "coverage drift against the v0 event vocabulary");
    }

    #[test]
    fn error_line_numbers_are_accurate() {
        let lines: Vec<&str> = VECTORS.lines().collect();
        let bad_src = format!("{}\n\n{}\nnot canonical\0??\n", lines[0], lines[2]);
        let err = read_jsonl(&bad_src).unwrap_err();
        assert_eq!(err.line, Some(4), "offending line should be 4, got {err}");
    }

    // ── replay conformance (T1d) ─────────────────────────────────────────────

    use ctxvm_core::replay;

    const CLEAN: &str = include_str!("../vectors/session-clean.jsonl");
    const DIVERGENT: &str = include_str!("../vectors/session-divergent.jsonl");

    /// The green-path session: every recorded fact is derived by the decisions.
    #[test]
    fn session_clean_fixture_is_replay_proved() {
        let trace = read_jsonl(CLEAN).expect("clean fixture must parse");
        let report = replay(&trace);
        assert_eq!(
            report.divergences,
            Vec::new(),
            "clean fixture must reproduce every fact — {report:?}"
        );
        assert_eq!(report.violations, Vec::new(), "clean fixture has no anomalies");
        assert_eq!(report.events, CLEAN.lines().count());
    }

    /// The red-path session: a resident-total lie at turn 1 and a rendered-stub
    /// lie at turn 3 (a page the decisions re-materialized but the trace claims
    /// stayed stubbed) — exactly two divergences, nothing else.
    #[test]
    fn session_divergent_fixture_reports_exactly_two_divergences() {
        let trace = read_jsonl(DIVERGENT).expect("divergent fixture must parse");
        let report = replay(&trace);
        assert_eq!(report.divergences.len(), 2, "{report:?}");
        assert!(
            report.divergences.iter().any(|d| matches!(
                d,
                ctxvm_core::Divergence::ResidentTokensMismatch { turn: 1, inferred: 760, recorded: 1460 }
            )),
            "turn 1 resident lie must be reported: {report:?}"
        );
        assert!(
            report.divergences.iter().any(|d| matches!(
                d,
                ctxvm_core::Divergence::RenderModeMismatch {
                    turn: 3, inferred: RenderMode::Full, recorded: RenderMode::Stub, ..
                }
            )),
            "turn 3 stub-vs-full lie must be reported: {report:?}"
        );
    }

    /// CLI-able outputs serialize deterministically (same trace → same report bytes).
    #[test]
    fn replay_report_serialization_is_deterministic() {
        let t1 = read_jsonl(CLEAN).unwrap();
        let t2 = read_jsonl(DIVERGENT).unwrap();
        for t in [&t1, &t2] {
            let a = replay(t);
            let b = replay(t);
            assert_eq!(
                serde_json::to_string(&a).unwrap(),
                serde_json::to_string(&b).unwrap()
            );
        }
    }

    /// The codec-glyph file from T1b stays resolvable here as a corpus-level
    /// smoke: it parses (its turn.render totals differ by design — codec-only).
    #[test]
    fn codec_vector_corpus_parses() {
        let events = read_jsonl(VECTORS).unwrap();
        assert_eq!(events.len(), 10);
    }
}

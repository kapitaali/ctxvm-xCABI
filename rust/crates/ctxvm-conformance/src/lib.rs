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

#[cfg(test)]
mod tests {
    use super::*;
    use ctxvm_codec::{parse_line, read_jsonl, to_line, write_jsonl};

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
}

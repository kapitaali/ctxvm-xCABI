//! P11: key order inside an event is not significant to parsing or replay.
//!
//! Ruled 2026-11-11 (owner, packet P11): the conformance test is the owner of the claim, and the RFC
//! note is a pointer to it. The assertion is deliberately three levels of *parsed* equality —
//! model, derived page table, replay report — and never byte equality: law 3 puts `ts` last in the
//! emitter's order, while a sorted-key writer puts it before `type`, so the two byte forms differ by
//! construction.
//!
//! Four vectors, two pairs: v0.1 (every line carries `ts` — the discriminating case) and v0 (no `ts`
//! at all). Each pair is the same event set written twice.
//!
//! A failure here says which level broke: `parsed model`, `page table`, or `report`.
//!
//! Level 2 compares the DERIVED page table — `ctxvm_core::derive_projection`, one projection per
//! turn the trace carries — and pins it against `order-expected-projection.json`. The replay report
//! carries events/divergences/violations only, so the page table is NOT inside it and must be
//! derived here; the pinned golden makes the check independent of the two forms merely agreeing
//! with each other.

use ctxvm_codec::jsonl::read_jsonl;
use ctxvm_codec::Event;
use ctxvm_core::replay;

const STRUCT_TS: &str = include_str!("../vectors/order-struct-ts.jsonl");
const SORTED_TS: &str = include_str!("../vectors/order-sorted-ts.jsonl");
const STRUCT_NO_TS: &str = include_str!("../vectors/order-struct-nots.jsonl");
const SORTED_NO_TS: &str = include_str!("../vectors/order-sorted-nots.jsonl");
const EXPECTED_REPORT: &str = include_str!("../vectors/order-expected-report.json");
const EXPECTED_PROJECTION: &str = include_str!("../vectors/order-expected-projection.json");

/// The turns a trace carries, in first-appearance order.
///
/// Read through the model's own serialisation, so this stays true if the codec's event set grows:
/// every event that has a `turn` contributes it, `session.open` has none.
fn turns_in(events: &[Event]) -> Vec<u64> {
    let mut turns: Vec<u64> = Vec::new();
    for e in events {
        let v = serde_json::to_value(e).expect("event serialises");
        if let Some(t) = v.get("turn").and_then(|t| t.as_u64()) {
            if !turns.contains(&t) {
                turns.push(t);
            }
        }
    }
    turns
}

fn report_json(report: &ctxvm_core::ReplayReport) -> String {
    serde_json::to_string(report).expect("replay report serialises")
}

/// Level 1: both byte forms parse to the same model, line for line.
/// Level 2: both derive the same page table — the derived projection, turn by turn, and it equals
///   the pinned expectation.
/// Level 3: both produce the same report, divergences and violations included.
fn assert_same_semantics(
    struct_form: &str,
    sorted_form: &str,
    label: &str,
    pinned_projection: &serde_json::Value,
) {
    assert_ne!(
        struct_form, sorted_form,
        "{label}: the two files must differ in bytes, or the test proves nothing"
    );

    let a = read_jsonl(struct_form).unwrap_or_else(|e| panic!("{label}: struct form must parse: {e}"));
    let b = read_jsonl(sorted_form).unwrap_or_else(|e| panic!("{label}: sorted form must parse: {e}"));

    assert_eq!(a.len(), b.len(), "{label}: line count differs");
    for (i, (x, y)) in a.iter().zip(b.iter()).enumerate() {
        assert_eq!(x, y, "{label}: parsed model differs at line {}", i + 1);
    }

    // Level 2 — the derived page table. The replay report does not carry it (it carries
    // events/divergences/violations only), so it is derived here, per turn the trace carries.
    let turns = turns_in(&a);
    assert!(!turns.is_empty(), "{label}: the trace carries no turn to project");
    for turn in &turns {
        let pa = ctxvm_core::derive_projection(&a, *turn);
        let pb = ctxvm_core::derive_projection(&b, *turn);
        assert_eq!(pa, pb, "{label}: derived page table differs at turn {turn}");
        let expected = pinned_projection
            .get(&turn.to_string())
            .unwrap_or_else(|| panic!("{label}: no pinned projection for turn {turn}"));
        assert_eq!(
            serde_json::to_value(&pa).expect("projection serialises"),
            *expected,
            "{label}: derived page table differs from the pinned projection at turn {turn}"
        );
    }

    let ra = replay(&a);
    let rb = replay(&b);
    assert_eq!(
        report_json(&ra),
        report_json(&rb),
        "{label}: replay report (events, divergences, violations) differs"
    );

    // The pair must not be two references to the same clean trace: the replay has to have run over
    // real events. This is a guard against a pair that passes because both files are empty.
    assert!(!a.is_empty(), "{label}: parsed zero events");
}

/// The pinned page tables, keyed by the struct-form file of each pair.
fn pinned_projections() -> serde_json::Value {
    let doc: serde_json::Value =
        serde_json::from_str(EXPECTED_PROJECTION).expect("expected projection parses");
    doc.get("pairs")
        .cloned()
        .expect("expected projection carries a `pairs` map")
}

#[test]
fn key_order_is_insignificant_with_ts() {
    let pinned = pinned_projections();
    let p = pinned
        .get("order-struct-ts.jsonl")
        .expect("the ts pair has a pinned page table");
    assert_same_semantics(STRUCT_TS, SORTED_TS, "v0.1 (ts on every line)", p);
    // The discriminating property: struct order puts ts last, sorted order puts it before type.
    let struct_first = STRUCT_TS.lines().next().expect("a first line");
    let sorted_first = SORTED_TS.lines().next().expect("a first line");
    // ts is an RFC3339 string; what matters is that it is the LAST key on the line.
    let at = struct_first.rfind(",\"ts\":").expect("ts present in struct form");
    assert!(
        struct_first[at..].ends_with("\"}") && !struct_first[at..].contains("\",\""),
        "struct form must carry ts last, got: {struct_first}"
    );
    assert!(
        sorted_first.find("\"ts\"").expect("ts present") < sorted_first.find("\"type\"").expect("type present"),
        "sorted form must carry ts before type, got: {sorted_first}"
    );
}

/// The pair's report is pinned as a vector, so an implementation in another language can run the same
/// assertion: both forms must project to exactly this, and to each other.
#[test]
fn both_forms_report_the_pinned_summary() {
    let expected: serde_json::Value = serde_json::from_str(EXPECTED_REPORT).expect("expected report parses");
    for (label, text) in [("struct", STRUCT_TS), ("sorted", SORTED_TS)] {
        let events = read_jsonl(text).expect("parses");
        let r = replay(&events);
        assert_eq!(
            r.events as u64,
            expected["events"].as_u64().expect("events is an integer"),
            "{label}: event count differs from the pinned report"
        );
        assert_eq!(
            r.divergences.is_empty(),
            expected["divergences"].as_array().expect("array").is_empty(),
            "{label}: divergences differ from the pinned report"
        );
        assert_eq!(
            r.violations.is_empty(),
            expected["violations"].as_array().expect("array").is_empty(),
            "{label}: violations differ from the pinned report"
        );
    }
}

#[test]
fn key_order_is_insignificant_without_ts() {
    let pinned = pinned_projections();
    let p = pinned
        .get("order-struct-nots.jsonl")
        .expect("the v0 pair has a pinned page table");
    assert_same_semantics(STRUCT_NO_TS, SORTED_NO_TS, "v0 (no ts)", p);
}

#[test]
fn sorted_form_carries_no_ts_in_the_v0_pair() {
    for line in SORTED_NO_TS.lines().filter(|l| !l.trim().is_empty()) {
        assert!(!line.contains("\"ts\""), "v0 sorted form must not gain a ts: {line}");
    }
}

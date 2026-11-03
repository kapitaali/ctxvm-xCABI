//! Strict JSONL codec for [`Event`]s.
//!
//! Canonical form:
//! - one compact JSON object per line (`serde_json::to_string`, field order = declaration order)
//! - trailing newline after the last line written by [`write_jsonl`]
//! - blank lines are tolerated on read and never produced on write
//!
//! Byte-identity contract (02 log invariant 2): `read_jsonl(s)` → `write_jsonl` MUST
//! reproduce the exact bytes. This holds only if the source is canonical — which the
//! golden vectors in `ctxvm-conformance/vectors/` are by construction and by test.
//!
//! Strictness note (feeds RFC-0): serde's internally-tagged enums silently DROP
//! unknown fields, which would quietly rewrite traces. This codec therefore enforces
//! strictness at the JSON level before model deserialization: unknown `"type"` tags,
//! unknown fields, and float-encoded token counts are hard errors.

use std::fmt;

use serde_json::Value;

use crate::model::Event;

/// Codec error with optional 1-based source line number.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CodecError {
    /// 1-based line number in the JSONL source (absent for single-value API misuse).
    pub line: Option<usize>,
    pub message: String,
}

impl CodecError {
    pub fn new(line: Option<usize>, message: impl Into<String>) -> Self {
        CodecError { line, message: message.into() }
    }
}

impl fmt::Display for CodecError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self.line {
            Some(n) => write!(f, "line {}: {}", n, self.message),
            None => write!(f, "jsonl: {}", self.message),
        }
    }
}

impl std::error::Error for CodecError {}

impl From<serde_json::Error> for CodecError {
    fn from(e: serde_json::Error) -> Self {
        CodecError::new(None, e.to_string())
    }
}

/// Exhaustive field allowlists per event tag. Keep in sync with `model::Event` —
/// the conformance suite fails if a line carrying a valid tag trips its allowlist
/// (i.e. the vector corpus exercises every declared field).
const FIELD_ALLOWLIST: &[(&str, &[&str])] = &[
    ("session.open", &["agentId", "model", "provider", "budgetTokens", "tokenizerId", "schemaVersion", "ts"]),
    ("page.declare", &["page", "turn", "latencyMs", "toolEffect", "ts"]),
    ("page.render", &["turn", "page", "mode", "ts"]),
    ("page.evict", &["turn", "page", "stubText", "ts"]),
    ("page.fault", &["turn", "page", "source", "latencyMs", "ts"]),
    ("page.pin", &["page", "reason", "ts"]),
    ("page.unpin", &["page", "reason", "ts"]),
    ("turn.render", &["turn", "residentTokens", "evictedTokens", "headroom", "ts", "prefix"]),
    ("call.meta", &["turn", "provider", "cacheEstimate", "latencyMs", "providerUsage", "ts"]),
];

fn allowlist_for(tag: &str) -> Option<&'static [&'static str]> {
    FIELD_ALLOWLIST.iter().find_map(|(t, fields)| (*t == tag).then_some(*fields))
}

/// Parse one canonical JSON line into an event, enforcing the field allowlist
/// before handing off to serde (unknown fields are a hard error, not a silent drop).
pub fn parse_line(line: &str) -> Result<Event, CodecError> {
    let line = line.trim();
    parse_line_inner(line, None)
}

/// Parse a whole JSONL document into events. Blank lines are skipped; line numbers
/// in errors refer to the 1-based line in the original text.
pub fn read_jsonl(src: &str) -> Result<Vec<Event>, CodecError> {
    let mut events = Vec::new();
    for (idx, line) in src.split('\n').enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        events.push(parse_line_inner(line, Some(idx + 1))?);
    }
    Ok(events)
}

fn parse_line_inner(line: &str, line_no: Option<usize>) -> Result<Event, CodecError> {
    let wrap = |e: CodecError| CodecError::new(line_no.or(e.line), e.message);
    (|| {
        let value: Value = serde_json::from_str(line)
            .map_err(|e| CodecError::new(None, format!("invalid JSON: {e}")))?;

        let tag = value
            .get("type")
            .and_then(Value::as_str)
            .ok_or_else(|| CodecError::new(None, "missing field `type`"))?;

        let allowed = allowlist_for(tag)
            .ok_or_else(|| CodecError::new(None, format!("unknown event type `{tag}`")))?;

        let obj = value
            .as_object()
            .ok_or_else(|| CodecError::new(None, format!("event `{tag}` must be a JSON object")))?;

        let unexpected: Vec<&str> = obj
            .keys()
            .filter(|k| k.as_str() != "type" && !allowed.contains(&k.as_str()))
            .map(String::as_str)
            .collect();
        if !unexpected.is_empty() {
            return Err(CodecError::new(
                None,
                format!("unknown field(s) for event `{tag}`:{}", unexpected
                    .iter()
                    .map(|k| format!(" `{k}`"))
                    .collect::<String>()),
            ));
        }

        serde_json::from_value::<Event>(value)
            .map_err(|e| CodecError::new(None, format!("invalid event: {e}")))
    })()
    .map_err(wrap)
}

/// Serialize one event to a canonical (compact, single-line) JSON string.
pub fn to_line(event: &Event) -> String {
    serde_json::to_string(event).expect("Event serialization is infallible")
}

/// Serialize events to canonical JSONL (compact lines, trailing newline).
pub fn write_jsonl(events: &[Event]) -> String {
    let mut out = String::new();
    for event in events {
        out.push_str(&to_line(event));
        out.push('\n');
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::*;

    // ── fixture builder covering every event type ──────────────────────────
    fn page() -> PageId {
        PageId {
            logical_ref: "tool:read_file(path=\"src/auth/session.ts\")".into(),
            content_hash: "sha256:9f2ac17d".into(),
        }
    }

    fn all_events() -> Vec<Event> {
        vec![
            Event::SessionOpen {
                agent_id: "demo-agent".into(),
                model: "openai/gpt-5".into(),
                provider: "openai".into(),
                budget_tokens: 120_000,
                tokenizer_id: "tiktoken-o200k_base".into(),
                schema_version: None,
                ts: None,
            },
            Event::PageDeclare {
                page: PageRef { id: page(), kind: PageKind::ToolResult, tokens: 8200 },
                turn: None,
                latency_ms: None,
                tool_effect: None,
                ts: None,
            },
            Event::PageRender { turn: 0, page: page(), mode: RenderMode::Full, ts: None },
            Event::PageEvict {
                turn: 1,
                page: page(),
                stub_text: "[Paged out: read src/auth/session.ts (8.2k tok, 187 lines).\n \
                            Re-call read_file(path=\"src/auth/session.ts\") to re-materialize.]"
                    .into(),
                ts: None,
            },
            Event::PageRender { turn: 1, page: page(), mode: RenderMode::Stub, ts: None },
            Event::TurnRender { turn: 1, resident_tokens: 47_800, evicted_tokens: 82, headroom: Some(64_000), ts: None, prefix: None },
            Event::PageFault { turn: 2, page: page(), source: FaultSource::ToolRecall, latency_ms: Some(180), ts: None },
            Event::PagePin { page: page(), reason: "explicit_api: harness re-materialized the page".into(), ts: None },
            Event::PageUnpin { page: page(), reason: "budget headroom restored".into(), ts: None },
            Event::CallMeta {
                turn: 2,
                provider: "openai".into(),
                cache_estimate: CacheEstimate {
                    est_hit_tokens: 47_000,
                    est_miss_tokens: 1_000,
                    provider_reported: false,
                },
                latency_ms: Some(1_240),
                provider_usage: None,
                ts: None,
            },
        ]
    }

    // ── tests ──────────────────────────────────────────────────────────────

    #[test]
    fn every_event_type_roundtrips_byte_identical() {
        for event in all_events() {
            let line = to_line(&event);
            let parsed = parse_line(&line).unwrap();
            assert_eq!(parsed, event, "model mismatch for `{}`", event.tag());
            assert_eq!(to_line(&parsed), line, "bytes mismatch for `{}`", event.tag());
        }
    }

    /// Combinatorial property check: for every fault source, without/with latency,
    /// and for every single-option permutation of the optional rending fields,
    /// parse→serialize is the identity.
    #[test]
    fn option_permutations_roundtrip_exactly() {
        for source in [FaultSource::ToolRecall, FaultSource::IdentifierScan, FaultSource::ExplicitApi, FaultSource::Semantic] {
            for latency in [None, Some(0), Some(u64::MAX)] {
                let e = Event::PageFault { turn: 7, page: page(), source, latency_ms: latency, ts: None };
                let line = to_line(&e);
                assert_eq!(parse_line(&line).unwrap(), e);
                assert_eq!(to_line(&parse_line(&line).unwrap()), line);
            }
        }
        for headroom in [None, Some(0), Some(u64::MAX)] {
            let e = Event::TurnRender { turn: 0, resident_tokens: 1, evicted_tokens: 0, headroom, ts: None, prefix: None };
            let line = to_line(&e);
            assert_eq!(parse_line(&line).unwrap(), e);
            assert_eq!(to_line(&parse_line(&line).unwrap()), line);
        }
        for reported in [true, false] {
            let e = Event::CallMeta {
                turn: 3,
                provider: "p".into(),
                cache_estimate: CacheEstimate {
                    est_hit_tokens: 9,
                    est_miss_tokens: 1,
                    provider_reported: reported,
                },
                latency_ms: None,
                provider_usage: None,
                ts: None,
            };
            let line = to_line(&e);
            assert_eq!(parse_line(&line).unwrap(), e);
        }
    }

    #[test]
    fn unknown_type_is_hard_error() {
        let err = parse_line(r#"{"type":"page.crash"}"#).unwrap_err();
        assert!(err.message.contains("unknown event type `page.crash`"), "{err}");
    }

    #[test]
    fn unknown_field_is_hard_error_not_a_silent_drop() {
        let e = Event::PagePin { page: page(), reason: "r".into(), ts: None };
        let mut line = to_line(&e);
        // splice a bogus extra field into the canonical line
        line = line.replace(
            &format!(",\"reason\":"),
            &format!(",\"x_shadow\":\"evil\",\"reason\":"),
        );
        let err = parse_line(&line).unwrap_err();
        assert!(err.message.contains("unknown field(s) for event `page.pin`"), "{err}");
        assert!(err.message.contains("`x_shadow`"), "{err}");
    }

    #[test]
    fn missing_fields_are_errors() {
        let err = parse_line(r#"{"type":"session.open"}"#).unwrap_err();
        assert!(err.message.contains("missing field"), "{err}");
    }

    #[test]
    fn float_token_counts_are_rejected() {
        let err = parse_line(
            r#"{"type":"turn.render","turn":0,"residentTokens":47.5,"evictedTokens":0}"#,
        )
        .unwrap_err();
        assert!(err.message.contains("invalid type"), "{err}");
    }

    #[test]
    fn read_jsonl_reports_the_offending_line() {
        let good = to_line(&Event::PageRender { turn: 0, page: page(), mode: RenderMode::Full, ts: None });
        let src = format!("{good}\nnot json at all\n{good}\n");
        let err = read_jsonl(&src).unwrap_err();
        assert_eq!(err.line, Some(2), "{err}");
        assert!(err.message.contains("invalid JSON"), "{err}");
    }

    #[test]
    fn blank_lines_are_skipped() {
        let e = all_events();
        let src = format!("\n\n\n{}\n", write_jsonl(&e).trim_end());
        assert_eq!(read_jsonl(&src).unwrap(), e);
    }

    /// Exhaustive per-line contract: valid tag must roundtrip out of the file as
    /// rendered-before-parse and after — guards against the codec and vectors
    /// drifting apart (the file is the standard's fixture).
    #[test]
    fn vector_file_is_canonical_byte_for_byte() {
        // This test lives in conformance; here we pin the codec's emission shape
        // independently: every line of a fresh text must be stable.
        for event in all_events() {
            let l1 = to_line(&event);
            let l2 = to_line(&parse_line(&l1).unwrap());
            assert_eq!(l1, l2);
        }
    }
}

#[cfg(test)]
mod rfc01_tests {
    use super::*;
    use crate::{CacheEstimate, Event, FaultSource, PageId, PageKind, PageRef, PrefixCost, ProviderUsage, ToolEffect};
    use crate::model::check_version;

    /// Same fixture identity as `tests::page()` (this module has its own scope).
    fn page() -> PageId {
        PageId {
            logical_ref: "tool:read_file(path=\"src/auth/session.ts\")".into(),
            content_hash: "sha256:9f2ac17d".into(),
        }
    }

    #[test]
    fn intentional_rerun_round_trips() {
        let e = Event::PageFault {
            turn: 0,
            page: PageId { logical_ref: "x".into(), content_hash: "h".into() },
            source: FaultSource::IntentionalRerun,
            latency_ms: None,
            ts: None,
        };
        let line = to_line(&e);
        assert!(line.contains("\"intentional_rerun\""), "{line}");
        assert_eq!(parse_line(&line).unwrap(), e);
    }

    #[test]
    fn provider_usage_round_trips_and_omitted_stays_omitted() {
        let with = Event::CallMeta {
            turn: 0,
            provider: "p".into(),
            cache_estimate: CacheEstimate {
                est_hit_tokens: 1,
                est_miss_tokens: 2,
                provider_reported: true,
            },
            latency_ms: None,
            provider_usage: Some(ProviderUsage {
                input_tokens: 7,
                output_tokens: 3,
                cached_input_tokens: None,
            }),
            ts: None,
        };
        let line = to_line(&with);
        assert!(line.contains("\"providerUsage\":{\"inputTokens\":7,\"outputTokens\":3}"), "{line}");
        assert_eq!(parse_line(&line).unwrap(), with);
    }
    #[test]
    fn w13_prefix_cost_roundtrips_and_is_version_gated() {
        let ev = Event::TurnRender {
            turn: 0,
            resident_tokens: 268,
            evicted_tokens: 0,
            headroom: None,
            ts: None,
            prefix: Some(PrefixCost {
                tool_schemas: Some(23),
                message_count: Some(4),
                request_chars: Some(8192),
                system_prompt_bytes: Some(3120),
                approx_input_tokens: Some(2048),
                source: "measured".into(),
            }),
        };
        let line = to_line(&ev);
        assert_eq!(ev, parse_line(&line).unwrap(), "prefix must survive a JSONL round trip");
        assert!(line.contains("\"toolSchemas\":23"));
        assert!(line.contains("\"source\":\"measured\""));

        // v0.1-only: a v0 trace carrying a prefix is invalid, never guessed at.
        let v0 = vec![
            Event::SessionOpen {
                agent_id: "demo-agent".into(),
                model: "openai/gpt-5".into(),
                provider: "openai".into(),
                budget_tokens: 120_000,
                tokenizer_id: "tiktoken-o200k_base".into(),
                schema_version: None,
                ts: None,
            },
            ev,
        ];
        let err = check_version(&v0).unwrap_err();
        assert!(err.contains("prefix requires schemaVersion"), "got: {err}");

        let mut v01 = v0;
        if let Event::SessionOpen { schema_version, .. } = &mut v01[0] {
            *schema_version = Some("0.1".into());
        }
        check_version(&v01).unwrap();

        // An adapter that cannot see the request says so instead of reporting zero.
        let unknown = PrefixCost { tool_schemas: None, message_count: None, request_chars: None,
            system_prompt_bytes: None, approx_input_tokens: None, source: "unknown".into() };
        let line = to_line(&Event::TurnRender { turn: 0, resident_tokens: 1, evicted_tokens: 0,
            headroom: None, ts: None, prefix: Some(unknown) });
        assert!(!line.contains("toolSchemas"), "unknown must omit the count, never coerce it to 0");
        assert!(line.contains("\"source\":\"unknown\""));
    }

    #[test]
    fn w15_tool_effect_roundtrips_between_latency_and_ts() {
        // W15 §R7: key order is type,page,turn,latencyMs?,toolEffect?,ts — ts
        // still rides last; the class reflects the registration table, not the
        // model text.
        let decl = |tool_effect: Option<ToolEffect>| Event::PageDeclare {
            page: PageRef { id: page(), kind: PageKind::ToolResult, tokens: 19 },
            turn: Some(0),
            latency_ms: Some(42),
            tool_effect,
            ts: Some("2026-10-29T15:16:58.120Z".into()),
        };
        let ev = decl(Some(ToolEffect::ReadOnly));
        let line = to_line(&ev);
        assert_eq!(ev, parse_line(&line).unwrap(), "toolEffect must survive a JSONL round trip");
        let tool = line.find("\"toolEffect\"").expect("toolEffect emitted");
        let latency = line.find("\"latencyMs\"").expect("latencyMs emitted");
        let late_ts = line.find("\"ts\"").expect("ts emitted");
        assert!(latency < tool && tool < late_ts, "order must be latencyMs, toolEffect, ts — got {line}");
        assert!(line.contains("\"toolEffect\":\"READ_ONLY\""), "{line}");
        // unclassified stays absent (the core never invents a class).
        let bare_line = to_line(&decl(None));
        assert_eq!(bare_line.find("\"toolEffect\""), None);
    }

    #[test]
    fn w15_tool_effect_is_version_gated() {
        let v0 = vec![
            Event::SessionOpen {
                agent_id: "demo-agent".into(),
                model: "openai/gpt-5".into(),
                provider: "openai".into(),
                budget_tokens: 120_000,
                tokenizer_id: "tiktoken-o200k_base".into(),
                schema_version: None,
                ts: None,
            },
            Event::PageDeclare {
                page: PageRef { id: page(), kind: PageKind::ToolResult, tokens: 19 },
                turn: None,
                latency_ms: None,
                tool_effect: Some(ToolEffect::Mutating),
                ts: None,
            },
        ];
        let err = check_version(&v0).unwrap_err();
        assert!(err.contains("toolEffect requires schemaVersion"), "got: {err}");
        let mut v01 = v0;
        if let Event::SessionOpen { schema_version, .. } = &mut v01[0] {
            *schema_version = Some("0.1".into());
        }
        check_version(&v01).unwrap();
    }

    #[test]
    fn w15_tool_effect_requires_tool_result_kind() {
        let v01_only = vec![
            Event::SessionOpen {
                agent_id: "demo-agent".into(),
                model: "openai/gpt-5".into(),
                provider: "openai".into(),
                budget_tokens: 120_000,
                tokenizer_id: "tiktoken-o200k_base".into(),
                schema_version: Some("0.1".into()),
                ts: None,
            },
            // a file page is not a tool call — the class is invalid on it.
            Event::PageDeclare {
                page: PageRef { id: page(), kind: PageKind::File, tokens: 19 },
                turn: Some(0),
                latency_ms: None,
                tool_effect: Some(ToolEffect::Mutating),
                ts: None,
            },
        ];
        let err = check_version(&v01_only).unwrap_err();
        assert!(err.contains("toolEffect requires kind tool_result"), "got: {err}");
    }

}

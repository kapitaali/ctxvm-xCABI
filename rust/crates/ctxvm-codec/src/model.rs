//! Typed xCABI v0/v0.1 event model.
//!
//! Source of truth: `02-xcabi-events-v0.md` (event table + log invariants) +
//! RFC-0.1 addendum (`spec/rfc-0.1/RFC-0.1-xCABI.md`).
//! Naming rules:
//! - Event type tags keep the documented dotted-lowercase form: `\"session.open\"`, `\"call.meta\"`, …
//! - JSON field names are camelCase (TS/JS-facing tracing surface mirrors 03-tracer-api-ts.md).
//! - Enum *values* (page kinds, fault sources, render modes) keep the documented
//!   snake_case form: `\"tool_result\"`, `\"tool_recall\"`, `\"full\"`, …
//! - No floats anywhere: token counts/u64 only — floats are a determinism hazard.

use serde::{Deserialize, Serialize};

/// Stable page identity: `(logical_ref, content_hash)` per 02 §Pages.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PageId {
    /// e.g. `tool:read_file(path=\"src/auth.ts\")` | `file:sha256:…` | `summary:t9`
    pub logical_ref: String,
    /// Content identity half of the page key.
    pub content_hash: String,
}

/// Page kinds per 02 §Pages.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PageKind {
    File,
    ToolResult,
    Summary,
    ImageRef,
}

/// Render mode per 02: a page is either seen in full or as its identity stub.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RenderMode {
    Full,
    Stub,
}

/// Fault taxonomy sources per 02 §Fault taxonomy + RFC-0.1 R1.
/// `semantic_*` plugin sources are v1; v0 carries the marker value only.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum FaultSource {
    /// Model re-calls the same tool/args → fault-in (Pichay-proven).
    ToolRecall,
    /// Scan of model output for paths/keys/URLs/symbols → fault-in.
    IdentifierScan,
    /// Harness or plugin explicitly calls the fault API.
    ExplicitApi,
    /// Non-deterministic plugin class (v1, always flagged).
    Semantic,
    /// RFC-0.1 R1: deliberate re-execution of a resident page. Valid whether
    /// the page is resident or stubbed; exempt from the fault-resident rule;
    /// never deduped per (page, source); never ground truth for W3.
    IntentionalRerun,
}

/// Tool side-effect class per W15 (RFC-0.1 §R7): tagged at tool REGISTRATION
/// by the harness adapter, never inferred from model text or result content.
/// Everything outside the registration table is `Mutating` — fail safe.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ToolEffect {
    ReadOnly,
    Mutating,
}

/// Provider-reported usage for `call.meta` (RFC-0.1 R3). Omittable; omitted
/// when the provider did not report (never null).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProviderUsage {
    pub input_tokens: u64,
    pub output_tokens: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cached_input_tokens: Option<u64>,
}

/// The full page descriptor used by `page.declare` (\"page desc\" in 02).
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PageRef {
    pub id: PageId,
    pub kind: PageKind,
    /// Tokenizer-tagged token count.
    pub tokens: u64,
}

/// Estimated cache hit/miss accounting for `call.meta` (02: \"cache-cost honesty\").
/// Estimates are estimates: `provider_reported` must be threaded into consumers,
/// never averaged away (log invariant 5).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CacheEstimate {
    pub est_hit_tokens: u64,
    pub est_miss_tokens: u64,
    /// true = numbers came from the provider; false = locally estimated
    pub provider_reported: bool,
}

/// RFC-0.1 W13: the static cost billed on every turn whether or not anything touches it.
///
/// Motivation (arXiv:2610.22732v1 §2.2): 23 tool schemas load on every turn, no repository
/// calls more than 7. A ledger that models only touched pages cannot see the largest
/// measured source of removable cost. Every field is optional because a harness that does
/// not expose its request cannot honestly report zero; `source` says how the numbers were
/// obtained, and `unknown` is a first-class answer.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PrefixCost {
    /// Loaded tool schemas for this call (host counter, e.g. `len(agent.tools)`).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_schemas: Option<u64>,
    /// Messages in the request (host counter).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub message_count: Option<u64>,
    /// Characters in the whole request (host counter).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub request_chars: Option<u64>,
    /// Bytes of the system/instruction prefix (host counter, when passed to the hook).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub system_prompt_bytes: Option<u64>,
    /// The host's own estimate of input tokens. An ESTIMATE, never billed tokens.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub approx_input_tokens: Option<u64>,
    /// "measured" (host counters) or "unknown" (the adapter cannot see the request).
    pub source: String,
}

/// The nine xCABI v0 event verbs + RFC-0.1 additive fields.
///
/// Wire shape: one JSON object per JSONL line, internally tagged by the `\"type\"` key,
/// tag values exactly as documented in 02.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all_fields = "camelCase")]
pub enum Event {
    /// Namespaces a trace: agent id, model, provider, budget, tokenizer id.
    #[serde(rename = "session.open")]
    SessionOpen {
        agent_id: String,
        model: String,
        provider: String,
        /// Token budget the session was opened under.
        budget_tokens: u64,
        /// Tokenizer identity; token counts are only comparable within one tokenizer.
        tokenizer_id: String,
        /// RFC-0.1 R0: version boundary. Absent = v0. Present must be \"0.1\".
        #[serde(skip_serializing_if = "Option::is_none")]
        schema_version: Option<String>,
        /// RFC-0.1 R4: optional capture clock (UTC RFC 3339).
        #[serde(skip_serializing_if = "Option::is_none")]
        ts: Option<String>,
    },
    /// A page entered the pager.
    #[serde(rename = "page.declare")]
    PageDeclare {
        page: PageRef,
        /// RFC-0.1 R5: optional turn on which the page was declared.
        #[serde(skip_serializing_if = "Option::is_none")]
        turn: Option<u64>,
        /// RFC-0.1 R4: optional declare latency.
        #[serde(skip_serializing_if = "Option::is_none")]
        latency_ms: Option<u64>,
        /// RFC-0.1 R7 (W15): side-effect class of the tool call that produced
        /// this result. Requires v0.1 and `kind == "tool_result"` (check_version).
        #[serde(skip_serializing_if = "Option::is_none")]
        tool_effect: Option<ToolEffect>,
        /// RFC-0.1 R4: optional capture clock.
        #[serde(skip_serializing_if = "Option::is_none")]
        ts: Option<String>,
    },
    /// Ground truth for \"waste\" measurements: how this page was seen at a turn.
    #[serde(rename = "page.render")]
    PageRender {
        turn: u64,
        page: PageId,
        mode: RenderMode,
        /// RFC-0.1 R4: optional capture clock.
        #[serde(skip_serializing_if = "Option::is_none")]
        ts: Option<String>,
    },
    /// Paging decision + exactly what the model was told (the stub text used).
    #[serde(rename = "page.evict")]
    PageEvict {
        turn: u64,
        page: PageId,
        stub_text: String,
        /// RFC-0.1 R4: optional capture clock.
        #[serde(skip_serializing_if = "Option::is_none")]
        ts: Option<String>,
    },
    /// The economics event: a measured eviction mistake.
    #[serde(rename = "page.fault")]
    PageFault {
        turn: u64,
        page: PageId,
        source: FaultSource,
        #[serde(skip_serializing_if = "Option::is_none")]
        latency_ms: Option<u64>,
        /// RFC-0.1 R4: optional capture clock.
        #[serde(skip_serializing_if = "Option::is_none")]
        ts: Option<String>,
    },
    /// Working-set decision, persists across turns until unpinned.
    #[serde(rename = "page.pin")]
    PagePin {
        page: PageId,
        reason: String,
        /// RFC-0.1 R4: optional capture clock.
        #[serde(skip_serializing_if = "Option::is_none")]
        ts: Option<String>,
    },
    /// Reverse of pin; auditable pairing.
    #[serde(rename = "page.unpin")]
    PageUnpin {
        page: PageId,
        reason: String,
        /// RFC-0.1 R4: optional capture clock.
        #[serde(skip_serializing_if = "Option::is_none")]
        ts: Option<String>,
    },
    /// The render set for that call: resident/evicted token totals + headroom.
    #[serde(rename = "turn.render")]
    TurnRender {
        turn: u64,
        resident_tokens: u64,
        evicted_tokens: u64,
        #[serde(skip_serializing_if = "Option::is_none")]
        headroom: Option<u64>,
        /// RFC-0.1 W13: static per-turn cost (tool schemas, prefix bytes).
        #[serde(skip_serializing_if = "Option::is_none")]
        prefix: Option<PrefixCost>,
        /// RFC-0.1 R4: optional capture clock.
        #[serde(skip_serializing_if = "Option::is_none")]
        ts: Option<String>,
    },
    /// Provider + cache-cost honesty + latency for one model call.
    #[serde(rename = "call.meta")]
    CallMeta {
        turn: u64,
        provider: String,
        cache_estimate: CacheEstimate,
        #[serde(skip_serializing_if = "Option::is_none")]
        latency_ms: Option<u64>,
        /// RFC-0.1 R3: optional provider-reported usage.
        #[serde(skip_serializing_if = "Option::is_none")]
        provider_usage: Option<ProviderUsage>,
        /// RFC-0.1 R4: optional capture clock.
        #[serde(skip_serializing_if = "Option::is_none")]
        ts: Option<String>,
    },
}

impl Event {
    /// The on-wire type tag (the `\"type\"` value).
    pub fn tag(&self) -> &'static str {
        match self {
            Event::SessionOpen { .. } => "session.open",
            Event::PageDeclare { .. } => "page.declare",
            Event::PageRender { .. } => "page.render",
            Event::PageEvict { .. } => "page.evict",
            Event::PageFault { .. } => "page.fault",
            Event::PagePin { .. } => "page.pin",
            Event::PageUnpin { .. } => "page.unpin",
            Event::TurnRender { .. } => "turn.render",
            Event::CallMeta { .. } => "call.meta",
        }
    }
}

/// RFC-0.1 version boundary helper. Returns the schemaVersion of the trace
/// (from the first session.open event) if present.
pub fn schema_version_of(events: &[Event]) -> Option<&str> {
    events.iter().find_map(|e| match e {
        Event::SessionOpen { schema_version, .. } => schema_version.as_deref(),
        _ => None,
    })
}

/// RFC-0.1 version gate: returns Err if the trace uses RFC-0.1-only features
/// without declaring schemaVersion \"0.1\", or declares an unknown version.
pub fn check_version(events: &[Event]) -> Result<(), String> {
    let version = schema_version_of(events);
    match version {
        Some(v) if v != "0.1" => {
            return Err(format!(
                "unknown schemaVersion `{v}` (consumer must reject, never guess)"
            ));
        }
        _ => {}
    }
    // IntentionalRerun requires v0.1.
    let has_intentional = events.iter().any(|e| match e {
        Event::PageFault {
            source: FaultSource::IntentionalRerun,
            ..
        } => true,
        _ => false,
    });
    if has_intentional && version != Some("0.1") {
        return Err("intentional_rerun requires schemaVersion \"0.1\"".to_string());
    }
    // providerUsage requires v0.1.
    let has_provider_usage = events.iter().any(|e| match e {
        Event::CallMeta {
            provider_usage: Some(_),
            ..
        } => true,
        _ => false,
    });
    if has_provider_usage && version != Some("0.1") {
        return Err("providerUsage requires schemaVersion \"0.1\"".to_string());
    }
    // prefix (W13) requires v0.1.
    let has_prefix = events.iter().any(|e| match e {
        Event::TurnRender { prefix: Some(_), .. } => true,
        _ => false,
    });
    if has_prefix && version != Some("0.1") {
        return Err("prefix requires schemaVersion \"0.1\"".to_string());
    }
    // turn on page.declare requires v0.1.
    let has_declare_turn = events.iter().any(|e| match e {
        Event::PageDeclare { turn: Some(_), .. } => true,
        _ => false,
    });
    if has_declare_turn && version != Some("0.1") {
        return Err("page.declare.turn requires schemaVersion \"0.1\"".to_string());
    }
    // W15 §R7, rule 1: toolEffect requires v0.1 (the version boundary).
    let has_tool_effect = events.iter().any(|e| match e {
        Event::PageDeclare {
            tool_effect: Some(_),
            ..
        } => true,
        _ => false,
    });
    if has_tool_effect && version != Some("0.1") {
        return Err("toolEffect requires schemaVersion \"0.1\"".to_string());
    }
    // W15 §R7, rule 2: the class belongs to a tool CALL, so it is valid only on a
    // tool_result page. Files, summaries and image refs are not tool calls.
    let bad_kind = events.iter().any(|e| match e {
        Event::PageDeclare {
            tool_effect: Some(_),
            page,
            ..
        } => page.kind != PageKind::ToolResult,
        _ => false,
    });
    if bad_kind {
        return Err("toolEffect requires kind tool_result".to_string());
    }
    // ts on any event requires v0.1.
    let has_ts = events.iter().any(|e| match e {
        Event::SessionOpen { ts: Some(_), .. } => true,
        Event::PageDeclare { ts: Some(_), .. } => true,
        Event::PageRender { ts: Some(_), .. } => true,
        Event::PageEvict { ts: Some(_), .. } => true,
        Event::PageFault { ts: Some(_), .. } => true,
        Event::PagePin { ts: Some(_), .. } => true,
        Event::PageUnpin { ts: Some(_), .. } => true,
        Event::TurnRender { ts: Some(_), .. } => true,
        Event::CallMeta { ts: Some(_), .. } => true,
        _ => false,
    });
    if has_ts && version != Some("0.1") {
        return Err("ts requires schemaVersion \"0.1\"".to_string());
    }
    // latencyMs on page.declare requires v0.1.
    let has_declare_latency = events.iter().any(|e| match e {
        Event::PageDeclare {
            latency_ms: Some(_),
            ..
        } => true,
        _ => false,
    });
    if has_declare_latency && version != Some("0.1") {
        return Err("page.declare.latencyMs requires schemaVersion \"0.1\"".to_string());
    }
    Ok(())
}

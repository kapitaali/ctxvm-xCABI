//! Typed xCABI v0 event model.
//!
//! Source of truth: `02-xcabi-events-v0.md` (event table + log invariants).
//! Naming rules:
//! - Event type tags keep the documented dotted-lowercase form: `"session.open"`, `"call.meta"`, …
//! - JSON field names are camelCase (TS/JS-facing tracing surface mirrors 03-tracer-api-ts.md).
//! - Enum *values* (page kinds, fault sources, render modes) keep the documented
//!   snake_case form: `"tool_result"`, `"tool_recall"`, `"full"`, …
//! - No floats anywhere: token counts/u64 only — floats are a determinism hazard.

use serde::{Deserialize, Serialize};

/// Stable page identity: `(logical_ref, content_hash)` per 02 §Pages.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PageId {
    /// e.g. `tool:read_file(path="src/auth.ts")` | `file:sha256:…` | `summary:t9`
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

/// Fault taxonomy sources per 02 §Fault taxonomy.
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
}

/// The full page descriptor used by `page.declare` ("page desc" in 02).
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PageRef {
    pub id: PageId,
    pub kind: PageKind,
    /// Tokenizer-tagged token count.
    pub tokens: u64,
}

/// Estimated cache hit/miss accounting for `call.meta` (02: "cache-cost honesty").
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

/// The nine xCABI v0 event verbs (02 §Events, draft vocabulary).
///
/// Wire shape: one JSON object per JSONL line, internally tagged by the `"type"` key,
/// tag values exactly as documented in 02.
///
/// Resolution notes vs the draft table (marked; feeds RFC-0):
/// - `page.pin`/`page.unpin` carry no `turn` by design: a pin is a working-set decision
///   that persists across the turn boundary unless unpinned.
/// - `call.meta` carries `turn` (added): without it the cache estimate cannot be joined
///   back to the turn it describes, which breaks invariant 5.
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
    },
    /// A page entered the pager.
    #[serde(rename = "page.declare")]
    PageDeclare { page: PageRef },
    /// Ground truth for "waste" measurements: how this page was seen at a turn.
    #[serde(rename = "page.render")]
    PageRender { turn: u64, page: PageId, mode: RenderMode },
    /// Paging decision + exactly what the model was told (the stub text used).
    #[serde(rename = "page.evict")]
    PageEvict { turn: u64, page: PageId, stub_text: String },
    /// The economics event: a measured eviction mistake.
    #[serde(rename = "page.fault")]
    PageFault {
        turn: u64,
        page: PageId,
        source: FaultSource,
        #[serde(skip_serializing_if = "Option::is_none")]
        latency_ms: Option<u64>,
    },
    /// Working-set decision, persists across turns until unpinned.
    #[serde(rename = "page.pin")]
    PagePin { page: PageId, reason: String },
    /// Reverse of pin; auditable pairing.
    #[serde(rename = "page.unpin")]
    PageUnpin { page: PageId, reason: String },
    /// The render set for that call: resident/evicted token totals + headroom.
    #[serde(rename = "turn.render")]
    TurnRender {
        turn: u64,
        resident_tokens: u64,
        evicted_tokens: u64,
        #[serde(skip_serializing_if = "Option::is_none")]
        headroom: Option<u64>,
    },
    /// Provider + cache-cost honesty + latency for one model call.
    #[serde(rename = "call.meta")]
    CallMeta {
        turn: u64,
        provider: String,
        cache_estimate: CacheEstimate,
        #[serde(skip_serializing_if = "Option::is_none")]
        latency_ms: Option<u64>,
    },
}

impl Event {
    /// The on-wire type tag (the `"type"` value).
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

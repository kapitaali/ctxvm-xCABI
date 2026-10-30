//! ctxvm-codec — typed xCABI v0 events + strict JSONL codec.
//!
//! - [`model`]: the nine event verbs (`session.open`, `page.declare`, `page.render`,
//!   `page.evict`, `page.fault`, `page.pin`, `page.unpin`, `turn.render`, `call.meta`),
//!   page identity/kind/ref types, fault sources, cache estimates — per
//!   `02-xcabi-events-v0.md`.
//! - [`jsonl`]: canonical JSONL reader/writer. Lines are compact JSON, one event per
//!   line, byte-identical roundtrip guaranteed for canonical input; unknown types,
//!   unknown fields, and float token counts are hard errors (strictness note feeds RFC-0).
//!
//! Golden vectors live in `ctxvm-conformance/vectors/` (referenced artifacts of the
//! standard); this crate keeps inline per-type fixtures in unit tests.

pub mod jsonl;
pub mod model;

pub use jsonl::{parse_line, read_jsonl, to_line, write_jsonl, CodecError};
pub use model::{
    check_version, schema_version_of, CacheEstimate, Event, FaultSource, PageId, PageKind,
    PageRef, ProviderUsage, RenderMode,
};

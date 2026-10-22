//! ctxvm-core — deterministic context VM engine.
//!
//! Layers (M0, pure Rust — no FFI, no LLM, no embedding in here ever):
//! - [`page_table`] — the stateful page table keyed by `(logical_ref, content_hash)`.
//!   A streaming `Playback` ingests decision events (`page.declare/evict/fault/pin/unpin`)
//!   and schedules per-page render-mode changes at turn boundaries. Anomalies are
//!   telemetry-first: logged as [`page_table::Violation`]s, never thrown.
//! - [`render`] — the deterministic renderer: pure functions `(fed decisions, turn)
//!   → slots + token tallies`. Slot structure depends only on the trace; full-content
//!   bytes are environment-attached and never influence decisions.
//!
//! Timing table (locked for v0; RFC-0 MUST record it):
//! `page.evict@t` → stub visible at turn t · `page.fault@t` → full from turn t+1 ·
//! same-turn conflicts → later stream event wins · pins carry no turn (v0).
//!
//! TODO(T1d): replay API + recorded-fact divergence detection (`page.render`,
//! `turn.render` cross-checks) on top of this module. → landed: `module replay`.

pub mod page_table;
pub mod render;
pub mod replay;

pub use page_table::{PageKey, PageTrack, Playback, Violation, ViolationKind};
pub use replay::{replay, Divergence, ReplayReport};
pub use render::{derive_projection, Slot, TurnProjection, TurnTally};

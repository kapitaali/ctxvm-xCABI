//! ctxvm-core — deterministic context VM engine.
//!
//! T1a scaffold only. Future contents (per 01-PLAN.md / 02-xcabi-events-v0.md):
//! - `page_table`: pages keyed by `(logical_ref, content_hash)`; kinds: file/tool_result/summary/image_ref
//! - `render`: pure `(events, turn) -> messages` (full content vs identity stub; byte-identical re-render)
//! - `budget`: token budgets, evictions batched at turn boundaries
//! - `policy`: pluggable eviction traits (FaultPinPolicy in T-series later); LLM/embedding = never here
//!
//! TODO(T1c): page table + deterministic renderer.

#[cfg(test)]
mod tests {
    /// Workspace smoke test (T1a): engine crate occupies the graph.
    #[test]
    fn core_crate_is_wired() {
        assert!(true, "placeholder until T1c");
    }
}

//! ctxvm-codec — typed xCABI v0 events + JSONL codec.
//!
//! T1a scaffold only. T1b implements the 9 event types (session.open, page.declare,
//! page.render, page.evict, page.fault, page.pin, page.unpin, turn.render, call.meta)
//! per 02-xcabi-events-v0.md, with byte-identical roundtrip golden vectors.

#[cfg(test)]
mod tests {
    /// Workspace smoke test (T1a).
    #[test]
    fn codec_crate_is_wired() {
        assert!(true, "placeholder until T1b");
    }
}

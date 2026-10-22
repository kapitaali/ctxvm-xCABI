//! ctxvm-conformance — golden vectors + replay conformance (T1a scaffold only).
//!
//! T1b: JSONL roundtrip vectors · T1d: replay API + divergence detection.
//! Vector artifacts should live under `vectors/` as committed files.

#[cfg(test)]
mod tests {
    /// Workspace smoke test (T1a).
    #[test]
    fn conformance_crate_is_wired() {
        assert!(true, "placeholder until T1b/T1d");
    }
}

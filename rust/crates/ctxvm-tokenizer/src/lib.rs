//! ctxvm-tokenizer — token counting backends (W2).
//!
//! Two laws meet here:
//!
//! 1. **Tokenizer identity** (02-xcabi-events-v0 §`session.open`): token counts
//!    are `tokenizer_id`-scoped and stable per session — numbers are only
//!    comparable within one tokenizer, and unknown ids are carried, never
//!    invented.
//! 2. **Count provenance** (W2 marking law): every token count is either
//!    provider-reported (authoritative when available) or estimated locally —
//!    [`tokens_source`] — and the two are never averaged together
//!    (`CacheEstimate.provider_reported` is the on-trace mark; adapters thread
//!    it, consumers must not average it away).
//!
//! Backends:
//!
//! - `apx4-char` — the documented v0 baseline ALL deployed traces use:
//!   ceil(Unicode code points ÷ 4). NOT a real tokenizer. Byte-mirror of
//!   `packages/node/src/ident.ts` `approx4` (the tracer's estimator) so a rust
//!   count and a node count agree on the same bytes — cross-harness counts must
//!   not fork at the estimator.
//! - `tiktoken-o200k_base` / `tiktoken-cl100k_base` — real BPE vocabularies via
//!   `tiktoken-rs`, behind the `tiktoken` feature (off by default: embedded
//!   ranks add compile time and binary size; CI exercises the feature). NOTE:
//!   these are OpenAI vocabularies. Counting a non-OpenAI model with them is an
//!   ESTIMATE in a NAMED vocabulary (the id records which) — never a provider
//!   number; the provider-reported mark stays authoritative where the harness
//!   records usage (adapter wiring is the remaining W2 lane; the default choice
//!   stays with the owner).

/// Count-provenance vocabulary (W2 marking law).
pub mod tokens_source {
    /// Count came from the provider (authoritative when available).
    pub const PROVIDER: &str = "provider";
    /// Count was estimated locally by a named tokenizer.
    pub const ESTIMATED: &str = "estimated";
}

/// The documented v0 baseline id (≈ chars/4) — every deployed trace uses it.
pub const APX4_CHAR: &str = "apx4-char";
/// OpenAI o200k_base BPE vocabulary (tiktoken-rs; feature `tiktoken`).
pub const TIKTOKEN_O200K_BASE: &str = "tiktoken-o200k_base";
/// OpenAI cl100k_base BPE vocabulary (tiktoken-rs; feature `tiktoken`).
pub const TIKTOKEN_CL100K_BASE: &str = "tiktoken-cl100k_base";

/// The `apx4-char` law, byte-identical to `packages/node/src/ident.ts`
/// `approx4`: `Math.ceil([...content].length / 4) || 0` — Unicode code points,
/// not bytes (a surrogate pair counts once on both sides); empty input is 0,
/// never 1. (Lone-surrogate divergence is impossible on both sides: JS tool
/// content reaches the tracer as a valid string and Rust `&str` is valid UTF-8.)
pub fn apx4(text: &str) -> u64 {
    (text.chars().count() as u64).div_ceil(4)
}

/// A named counting backend: identity + a total count for a text.
pub trait Tokenizer: Send + Sync {
    /// The `tokenizer_id` this backend's counts are scoped to.
    fn id(&self) -> &'static str;
    /// Total tokens for `text` (the unit every downstream metric consumes).
    fn count(&self, text: &str) -> u64;
}

/// The `apx4-char` backend.
#[derive(Debug, Clone, Copy, Default)]
pub struct Apx4Char;

impl Tokenizer for Apx4Char {
    fn id(&self) -> &'static str {
        APX4_CHAR
    }
    fn count(&self, text: &str) -> u64 {
        apx4(text)
    }
}

/// Every id this build can resolve (the tiktoken ids appear only when the
/// `tiktoken` feature is on).
pub fn known_ids() -> Vec<&'static str> {
    #[cfg(feature = "tiktoken")]
    let ids: Vec<&'static str> = vec![APX4_CHAR, TIKTOKEN_O200K_BASE, TIKTOKEN_CL100K_BASE];
    #[cfg(not(feature = "tiktoken"))]
    let ids: Vec<&'static str> = vec![APX4_CHAR];
    ids
}

/// Resolve a `tokenizer_id` to its backend. `None` = unknown id, or a tiktoken
/// id in a build compiled WITHOUT the feature — callers must report that
/// distinctly and must never substitute another tokenizer's count (identity
/// law: counts are only comparable within one tokenizer).
pub fn for_id(id: &str) -> Option<Box<dyn Tokenizer>> {
    match id {
        APX4_CHAR => Some(Box::new(Apx4Char)),
        #[cfg(feature = "tiktoken")]
        TIKTOKEN_O200K_BASE => Some(Box::new(tiktoken_backends::O200kBase)),
        #[cfg(feature = "tiktoken")]
        TIKTOKEN_CL100K_BASE => Some(Box::new(tiktoken_backends::Cl100kBase)),
        _ => None,
    }
}

/// Whether a build CAN resolve `id` given its features, distinct from
/// [`for_id`] (which conflates "unknown" and "compiled out").
pub fn is_known_id(id: &str) -> bool {
    known_ids().contains(&id)
}

#[cfg(feature = "tiktoken")]
mod tiktoken_backends {
    use super::{Tokenizer, TIKTOKEN_CL100K_BASE, TIKTOKEN_O200K_BASE};
    use std::sync::OnceLock;
    use tiktoken_rs::{cl100k_base, o200k_base, CoreBPE};

    /// Embedded vocabularies load once per process (construction parses the
    /// BPE ranks); the backend is stateless afterwards.
    fn o200k() -> &'static CoreBPE {
        static BPE: OnceLock<CoreBPE> = OnceLock::new();
        BPE.get_or_init(|| o200k_base().expect("embedded o200k_base vocab"))
    }

    fn cl100k() -> &'static CoreBPE {
        static BPE: OnceLock<CoreBPE> = OnceLock::new();
        BPE.get_or_init(|| cl100k_base().expect("embedded cl100k_base vocab"))
    }

    /// Plain-text counting = BPE encode length. Special tokens are NOT matched
    /// in ordinary text by this entry point (stable across tiktoken-rs
    /// versions); the count is the vocabulary's, so the id carries WHICH vocab.
    fn count_with(bpe: &CoreBPE, text: &str) -> u64 {
        bpe.encode_with_special_tokens(text).len() as u64
    }

    /// `tiktoken-o200k_base`.
    #[derive(Debug, Clone, Copy, Default)]
    pub struct O200kBase;

    impl Tokenizer for O200kBase {
        fn id(&self) -> &'static str {
            TIKTOKEN_O200K_BASE
        }
        fn count(&self, text: &str) -> u64 {
            count_with(o200k(), text)
        }
    }

    /// `tiktoken-cl100k_base`.
    #[derive(Debug, Clone, Copy, Default)]
    pub struct Cl100kBase;

    impl Tokenizer for Cl100kBase {
        fn id(&self) -> &'static str {
            TIKTOKEN_CL100K_BASE
        }
        fn count(&self, text: &str) -> u64 {
            count_with(cl100k(), text)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Byte-parity anchors vs `packages/node/src/ident.ts` `approx4` — the two
    /// implementations must agree on the same bytes or trace counts fork across
    /// harnesses (the cross-harness law).
    #[test]
    fn apx4_matches_the_node_approx4_law() {
        assert_eq!(apx4(""), 0);
        assert_eq!(apx4("a"), 1); // ceil(1/4)
        assert_eq!(apx4("abcd"), 1);
        assert_eq!(apx4("abcde"), 2);
        // Code points, NOT bytes: α is 2 bytes in UTF-8 but one code point;
        // 👍 is 4 bytes but one code point (one surrogate pair in JS — still 1).
        assert_eq!(apx4("αααα"), 1);
        assert_eq!(apx4("ααααα"), 2);
        assert_eq!(apx4("👍"), 1);
        assert_eq!(apx4("👍👍👍👍👍"), 2);
        assert_eq!(apx4("hello world"), 3); // 11 code points
        assert_eq!(Apx4Char.count("hello world"), 3, "backend == the free law");
    }

    #[test]
    fn registry_law_apx4_always_available_unknown_carried_never_invented() {
        let t = for_id(APX4_CHAR).expect("apx4-char is always available");
        assert_eq!(t.id(), APX4_CHAR);
        assert!(is_known_id(APX4_CHAR));
        assert!(!is_known_id("not-a-tokenizer"));
        assert!(for_id("not-a-tokenizer").is_none(), "unknown ids are carried, never invented");
        assert!(known_ids().contains(&APX4_CHAR));
        // The marking vocabulary (W2 law) — spellings are load-bearing.
        assert_eq!(tokens_source::PROVIDER, "provider");
        assert_eq!(tokens_source::ESTIMATED, "estimated");
    }

    /// Feature-on: the real BPE backends are deterministic, monotone in input,
    /// and count multibyte text non-trivially (the point of W2 — `apx4-char`
    /// cannot see subwords). Exact-value pins are avoided on purpose: the
    /// embedded vocabulary snapshot is tiktoken-rs's, not ours, and a vocab
    /// bump must not break the gate — structural invariants are the contract.
    #[cfg(feature = "tiktoken")]
    #[test]
    fn tiktoken_backends_are_real_deterministic_and_monotone() {
        for id in [TIKTOKEN_O200K_BASE, TIKTOKEN_CL100K_BASE] {
            let t = for_id(id).unwrap_or_else(|| panic!("{id} resolves with the feature on"));
            assert_eq!(t.id(), id);
            assert!(is_known_id(id));
            assert_eq!(t.count(""), 0, "empty text: zero tokens");
            let one = t.count("hello world");
            assert!(one > 0 && one < 100, "{id} sane count for 'hello world': {one}");
            assert_eq!(t.count("hello world"), one, "{id} deterministic");
            let longer = "hello world, and a much longer text with many more tokens in it";
            assert!(t.count(longer) >= one, "{id} monotone in input");
            let multibyte = t.count("αααα αααα 日本語のテキスト");
            assert!(multibyte > 0, "{id} counts multibyte text: {multibyte}");
            assert_eq!(t.count("αααα αααα 日本語のテキスト"), multibyte, "{id} deterministic on multibyte");
        }
    }
}

//! Deterministic per-turn rendering: from fed decision events → the page-layer
//! projection of what the model saw at a turn (full content vs identity stub).
//!
//! Determinism boundary (02 invariants, 01 §Decisions):
//! - The slot STRUCTURE (which pages, which modes, which stub bytes, declared token
//!   counts) is a pure function of the event stream and the turn index.
//! - Full-content BYTES are environment-supplied (`Playback::attach_content`); the
//!   trace stores only `content_hash`. Two replays with the same trace + same
//!   attached content are byte-identical (serialized slot stream 1:1).
//! - The v0 projection covers PAGES only; provider message mirroring is a v1
//!   tracer concern.

use ctxvm_codec::{Event, PageId, PageRef, RenderMode};

use crate::page_table::{PageTrack, Playback, Violation};

/// A slot for one page in one turn — full content or the logged stub, never both.
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Slot {
    /// Declaring descriptor (id + kind + declared tokens). In stub mode, `tokens`
    /// still records the page's full size for waste accounting.
    pub reference: PageRef,
    pub mode: RenderMode,
    /// The stub text actually shown to the model (verbatim from `page.evict`).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stub_text: Option<String>,
    /// Environment-attached content bytes (None = unmaterialized; decision layer
    /// does not depend on it).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    /// Latest stream pin state (pin events carry no turn in v0).
    pub pinned: bool,
}

/// Token accounting for one turn, derived from decisions.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TurnTally {
    /// Σ declared tokens of pages rendered in full.
    pub resident_tokens: u64,
    /// Σ declared tokens of pages rendered as stubs (the pending-return debt).
    pub stubbed_tokens: u64,
    /// Number of stubbed slots.
    pub stubbed_slots: usize,
    /// Number of resident (full) slots.
    pub resident_slots: usize,
}

/// Pure-function snapshot: every declared page, in first-declaration order,
/// with its turn-specific mode — plus stream-health captured alongside.
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TurnProjection {
    pub turn: u64,
    pub slots: Vec<Slot>,
    pub tally: TurnTally,
    /// Telemetry-first state-machine violations observed while building the table
    /// (the projection itself never fails because of them).
    pub violations: Vec<Violation>,
}

impl Playback {
    /// Slots for one turn, in first-declaration order. Pure function of decisions fed.
    pub fn slots_at(&self, turn: u64) -> Vec<Slot> {
        self.pages_in_declaration_order()
            .map(|track| {
                let mode = track.mode_at(turn);
                Slot {
                    reference: track.reference.clone(),
                    mode,
                    stub_text: match &mode {
                        RenderMode::Stub => track.last_stub_text().map(str::to_owned),
                        RenderMode::Full => None,
                    },
                    content: track.content.clone(),
                    pinned: track.pins() > 0,
                }
            })
            .collect()
    }

    /// Derived token accounting for one turn.
    pub fn tally_at(&self, turn: u64) -> TurnTally {
        let (mut resident_tokens, mut stubbed_tokens, mut stubbed_slots, mut resident_slots) =
            (0u64, 0u64, 0usize, 0usize);
        for track in self.pages_in_declaration_order() {
            let tokens = track.reference.tokens;
            match track.mode_at(turn) {
                RenderMode::Full => {
                    resident_tokens = resident_tokens.saturating_add(tokens);
                    resident_slots += 1;
                }
                RenderMode::Stub => {
                    stubbed_tokens = stubbed_tokens.saturating_add(tokens);
                    stubbed_slots += 1;
                }
            }
        }
        TurnTally { resident_tokens, stubbed_tokens, stubbed_slots, resident_slots }
    }

    /// Slots + tally + violations for one turn.
    pub fn projection_at(&self, turn: u64) -> TurnProjection {
        TurnProjection {
            turn,
            slots: self.slots_at(turn),
            tally: self.tally_at(turn),
            violations: self.violations().to_vec(),
        }
    }
}

/// Convenience: pure derive from a raw event slice — identical bytes for identical
/// inputs, guaranteed (BTreeMap iteration + stream-ordered tiebreaks + canonical serde).
pub fn derive_projection(events: &[Event], turn: u64) -> TurnProjection {
    let mut pb = Playback::new();
    pb.feed_all(events);
    pb.projection_at(turn)
}

/// One force-resident flip applied by the counterfactual overlay.
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ForcedResident {
    /// The page whose stub slot was flipped to Full.
    pub page: PageId,
    /// Declared token size of the page (+= to ctxvm tally contributions).
    pub tokens: u64,
}

/// A `--pin` argument in its matching form (UC2 visibility probe).
///
/// - `Ref` — the T16 broad form: flip **every** Stub slot whose `logical_ref`
///   matches (all content-hash variants of the ref).
/// - `Identity` — the T20 precision form `--pin (ref, hash)`: flip only the
///   Stub slot with that exact page identity (one variant of the ref).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Pin {
    /// Broad match on the logical ref.
    Ref(String),
    /// Exact match on the full page identity.
    Identity {
        logical_ref: String,
        content_hash: String,
    },
}

impl Pin {
    pub fn ref_pin(reference: impl Into<String>) -> Self {
        Pin::Ref(reference.into())
    }

    pub fn identity(logical_ref: impl Into<String>, content_hash: impl Into<String>) -> Self {
        Pin::Identity {
            logical_ref: logical_ref.into(),
            content_hash: content_hash.into(),
        }
    }
}

impl TurnProjection {
    /// Counterfactual force-resident overlay (UC2 visibility probe): in this
    /// projection — only — flip Stub slots to Full (stub text dropped) and
    /// re-tally.
    ///
    /// Facts and violations are **untouched**: the overlay answers "could the
    /// model have *seen* this page at this turn?" — a visibility probe verified
    /// against the real decision schedule, not a rewrite of it. Visibility is
    /// not correctness: whether the model would have *used* the content is
    /// outside the decision layer.
    ///
    /// Returns the projected-with-overlay state plus the list of flips applied
    /// (matching slots that were already Full are not flips — they don't appear
    /// in the list). Matching per [`Pin`]: [`Pin::Ref`] flips every
    /// content-hash variant of the ref; [`Pin::Identity`] flips exactly the one
    /// (logical_ref, content_hash) page.
    pub fn with_forced_resident(mut self, pins: &[Pin]) -> (Self, Vec<ForcedResident>) {
        let mut forced = Vec::new();
        for slot in &mut self.slots {
            if slot.mode != RenderMode::Stub {
                continue;
            }
            let matched = pins.iter().any(|pin| match pin {
                Pin::Ref(reference) => *reference == slot.reference.id.logical_ref,
                Pin::Identity {
                    logical_ref,
                    content_hash,
                } => {
                    *logical_ref == slot.reference.id.logical_ref
                        && *content_hash == slot.reference.id.content_hash
                }
            });
            if matched {
                slot.mode = RenderMode::Full;
                slot.stub_text = None;
                forced.push(ForcedResident {
                    page: slot.reference.id.clone(),
                    tokens: slot.reference.tokens,
                });
            }
        }
        self.tally = TurnTally {
            resident_tokens: self
                .slots
                .iter()
                .filter(|s| s.mode == RenderMode::Full)
                .fold(0u64, |acc, s| acc.saturating_add(s.reference.tokens)),
            stubbed_tokens: self
                .slots
                .iter()
                .filter(|s| s.mode == RenderMode::Stub)
                .fold(0u64, |acc, s| acc.saturating_add(s.reference.tokens)),
            stubbed_slots: self.slots.iter().filter(|s| s.mode == RenderMode::Stub).count(),
            resident_slots: self.slots.iter().filter(|s| s.mode == RenderMode::Full).count(),
        };
        (self, forced)
    }
}

impl PageTrack {
    /// The stub text of the most recent evict in stream order — shown verbatim in
    /// stub slots ("what the model was told", 02 §Events). Kept on the track so the
    /// record stays self-contained; later evicts overwrite earlier stubs.
    pub fn last_stub_text(&self) -> Option<&str> {
        self.last_stub_text_cached.as_deref()
    }
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeSet;

    use super::*;
    use crate::page_table::ViolationKind;
    use ctxvm_codec::{CacheEstimate, FaultSource, PageId, PageKind};

    const SPEC_STUB: &str = "[Paged out: read src/auth/session.ts (8.2k tok, 187 lines).\n \
         Re-call read_file(path=\"src/auth/session.ts\") to re-materialize.]";

    fn declare_file(logical: &str, hash: &str, tokens: u64) -> Event {
        Event::PageDeclare {
            page: PageRef {
                id: PageId { logical_ref: logical.into(), content_hash: hash.into() },
                kind: PageKind::File,
                tokens,
            },
        }
    }

    fn evict_stubs(turn: u64, logical: &str, hash: &str) -> Event {
        Event::PageEvict {
            turn,
            page: PageId { logical_ref: logical.into(), content_hash: hash.into() },
            stub_text: SPEC_STUB.into(),
        }
    }

    fn fault_at(turn: u64, logical: &str, hash: &str) -> Event {
        Event::PageFault {
            turn,
            page: PageId { logical_ref: logical.into(), content_hash: hash.into() },
            source: FaultSource::ToolRecall,
            latency_ms: None,
        }
    }

    fn pin(page: PageId, reason: &str) -> Event {
        Event::PagePin { page, reason: reason.into() }
    }

    fn unpin(page: PageId, reason: &str) -> Event {
        Event::PageUnpin { page, reason: reason.into() }
    }

    /// ── Scenario 1 — stable session: everything resident, no paging. ─────────
    /// Hand-sum: A=1000 (file) + B=400 (tool_result) + C=60 (summary) ⇒ 1460
    /// resident at every turn until something is evicted.
    #[test]
    fn scenario_stable_session_no_paging() {
        let events = vec![
            Event::SessionOpen {
                agent_id: "demo".into(),
                model: "m".into(),
                provider: "p".into(),
                budget_tokens: 120_000,
                tokenizer_id: "t".into(),
            },
            declare_file("file:auth.ts", "h-a", 1000),
            Event::PageDeclare {
                page: PageRef {
                    id: PageId {
                        logical_ref: "tool:read_file(src/db/schema.sql)".into(),
                        content_hash: "h-b".into(),
                    },
                    kind: PageKind::ToolResult,
                    tokens: 400,
                },
            },
            Event::PageDeclare {
                page: PageRef {
                    id: PageId { logical_ref: "summary:t0".into(), content_hash: "h-c".into() },
                    kind: PageKind::Summary,
                    tokens: 60,
                },
            },
        ];
        let mut pb = Playback::new();
        pb.feed_all(&events);
        assert!(pb.violations().is_empty(), "{:?}", pb.violations());

        for turn in [0u64, 1, 9, 999] {
            let p = pb.projection_at(turn);
            assert_eq!(p.tally.resident_tokens, 1460, "turn {turn}"); // 1000+400+60
            assert_eq!(p.tally.stubbed_tokens, 0);
            assert_eq!(p.tally.resident_slots, 3);
            assert_eq!(p.tally.stubbed_slots, 0);
            assert_eq!(p.slots[0].reference.id.logical_ref, "file:auth.ts");
            assert_eq!(p.slots[1].reference.id.logical_ref, "tool:read_file(src/db/schema.sql)");
            assert_eq!(p.slots[2].reference.id.logical_ref, "summary:t0");
            assert!(p.slots.iter().all(|s| s.mode == RenderMode::Full));
        }

        // identical re-declaration is idempotent — no violation
        pb.feed(&declare_file("file:auth.ts", "h-a", 1000));
        assert!(pb.violations().is_empty());

        // mismatched re-declaration → DuplicateDeclare, first descriptor wins
        pb.feed(&declare_file("file:auth.ts", "h-a", 1001));
        let vk: Vec<&ViolationKind> = pb.violations().iter().map(|v| &v.kind).collect();
        assert_eq!(
            vk,
            vec![&ViolationKind::DuplicateDeclare {
                page: PageId { logical_ref: "file:auth.ts".into(), content_hash: "h-a".into() }
            }]
        );
        let a_track = pb.page(&PageId {
            logical_ref: "file:auth.ts".into(),
            content_hash: "h-a".into(),
        })
        .unwrap();
        assert_eq!(a_track.reference.tokens, 1000, "first declaration wins");
    }

    /// ── Scenario 2 — evict → stub → fault → re-materialize. ──────────────────
    /// Hand-summed tallies: turn 0 → 1460 full / 0 stubbed · turn 1 → 1060 full
    /// (1000+60), B stubbed with 400 pending · turn 2 → still stubbed (fault@2
    /// lands at 3) · turn 3 → 1460 full / 0 stubbed.
    #[test]
    fn scenario_evict_fault_rematerialize() {
        let events = vec![
            declare_file("file:auth.ts", "h-a", 1000),
            declare_file("tool:read_file(path=\"src/auth/session.ts\")", "h-b", 400),
            declare_file("summary:t0", "h-c", 60),
            evict_stubs(1, "tool:read_file(path=\"src/auth/session.ts\")", "h-b"),
            fault_at(2, "tool:read_file(path=\"src/auth/session.ts\")", "h-b"),
        ];
        let pb = Playback::new_with(&events);
        assert!(pb.violations().is_empty(), "{:?}", pb.violations());

        for (turn, resident, stubbed) in [(0u64, 1460u64, 0u64), (1, 1060, 400), (2, 1060, 400), (3, 1460, 0)] {
            let p = pb.projection_at(turn);
            assert_eq!(p.tally.resident_tokens, resident, "turn {turn}");
            assert_eq!(p.tally.stubbed_tokens, stubbed, "turn {turn}");
        }

        let b_slot = &pb.slots_at(1)[1];
        assert_eq!(b_slot.mode, RenderMode::Stub);
        assert_eq!(b_slot.stub_text.as_deref(), Some(SPEC_STUB), "verbatim from page.evict");
        assert_eq!(b_slot.reference.tokens, 400, "full size recorded even when stubbed");
        assert!(pb.slots_at(3)[1].content.is_none(), "content unattached ⇒ None");
    }

    /// ── Scenario 3 — pins: audit, pinned-evict policy breach, unpin clamp. ────
    /// Violation ledger (hand-count): EvictWhilePinned (A evicted while pinned) ·
    /// UnpinOfUnpinned (second unpin) · EvictWhileStubbed (the REPEAT evict of B —
    /// the first evict was legitimate).
    #[test]
    fn scenario_pin_audit_and_policy_breaches() {
        let a_id = PageId { logical_ref: "file:a.ts".into(), content_hash: "h-a".into() };
        let b_id = PageId { logical_ref: "file:b.ts".into(), content_hash: "h-b".into() };
        let events = vec![
            declare_file("file:a.ts", "h-a", 10),
            declare_file("file:b.ts", "h-b", 20),
            pin(a_id.clone(), "hot loop"),
            evict_stubs(0, "file:a.ts", "h-a"), // policy breach while pinned — applied + logged
            unpin(a_id.clone(), "cool"),
            unpin(a_id.clone(), "double unpin"),
            evict_stubs(1, "file:b.ts", "h-b"), // legitimate: B was full
            evict_stubs(1, "file:b.ts", "h-b"), // repeat → EvictWhileStubbed
        ];
        let pb = Playback::new_with(&events);
        let vk: Vec<ViolationKind> = pb.violations().iter().map(|v| v.kind.clone()).collect();
        assert_eq!(
            vk,
            vec![
                ViolationKind::EvictWhilePinned { page: a_id.clone() },
                ViolationKind::UnpinOfUnpinned { page: a_id.clone() },
                ViolationKind::EvictWhileStubbed { page: b_id },
            ]
        );

        // state applied anyway (telemetry-first): A stubbed at turn 0 despite pin
        let p0 = pb.projection_at(0);
        assert_eq!(p0.tally.resident_tokens, 20, "hand-sum: only B resident");
        assert_eq!(p0.tally.stubbed_slots, 1);
        // pin flag reflects the LATEST stream state (v0: pins carry no turn — RFC item)
        assert_eq!(p0.slots[0].pinned, false);
        assert!(p0.slots.iter().all(|s| s.pinned == false));
    }

    /// ── Scenario 4 — unknown pages + content attach guard. ───────────────────
    /// Hand-count: 5 violations (evict/fault/pin/unpin of an undeclared ghost +
    /// mismatched content re-attach). Ghost never enters the table.
    #[test]
    fn scenario_unknown_pages_and_content_guard() {
        let ghost = PageId { logical_ref: "file:ghost.ts".into(), content_hash: "h-g".into() };
        let a = PageId { logical_ref: "file:a.ts".into(), content_hash: "h-a".into() };
        let mut pb = Playback::new();
        pb.feed(&evict_stubs(0, "file:ghost.ts", "h-g"));
        pb.feed(&fault_at(0, "file:ghost.ts", "h-g"));
        pb.feed(&pin(ghost.clone(), "r"));
        pb.feed(&unpin(ghost.clone(), "r"));
        pb.feed(&declare_file("file:a.ts", "h-a", 5));
        pb.attach_content(&a, "hello");
        pb.attach_content(&a, "other"); // mismatch → ContentAttach, content kept

        let vk: Vec<ViolationKind> = pb.violations().iter().map(|v| v.kind.clone()).collect();
        assert_eq!(
            vk,
            vec![
                ViolationKind::DecisionOfUnknownPage { page: ghost.clone(), decision: "evict" },
                ViolationKind::DecisionOfUnknownPage { page: ghost.clone(), decision: "fault" },
                ViolationKind::DecisionOfUnknownPage { page: ghost.clone(), decision: "pin" },
                ViolationKind::DecisionOfUnknownPage { page: ghost, decision: "unpin" },
                ViolationKind::ContentAttach {
                    page: a.clone(),
                    reason: "content differs from previous attach; page identity is (ref, hash)"
                },
            ]
        );
        // ghost was never declared → only A is in the table (5 tokens resident)
        assert_eq!(pb.tally_at(0).resident_tokens, 5);
        assert_eq!(pb.slots_at(0).len(), 1);
        // first attach wins, exactly like declarations
        assert_eq!(
            pb.page(&a).unwrap().content.as_deref(),
            Some("hello"),
            "first content attach wins"
        );
    }

    /// Determinism property (card DoD): two derives of the same trace are EQUAL —
    /// structurally AND byte-for-byte in canonical JSON projection.
    #[test]
    fn determinism_property_two_derives_are_identical() {
        let events = vec![
            declare_file("file:auth.ts", "h-a", 1000),
            declare_file("tool:read_file(path=\"src/auth/session.ts\")", "h-b", 400),
            declare_file("summary:t0", "h-c", 60),
            evict_stubs(1, "tool:read_file(path=\"src/auth/session.ts\")", "h-b"),
            fault_at(2, "tool:read_file(path=\"src/auth/session.ts\")", "h-b"),
            pin(
                PageId { logical_ref: "file:auth.ts".into(), content_hash: "h-a".into() },
                "explicit_api: turn 2",
            ),
            Event::CallMeta {
                turn: 2,
                provider: "openai".into(),
                cache_estimate: CacheEstimate {
                    est_hit_tokens: 47_000,
                    est_miss_tokens: 1_000,
                    provider_reported: false,
                },
                latency_ms: Some(1_240),
            },
        ];

        let run1: Vec<TurnProjection> = (0..=4).map(|t| derive_projection(&events, t)).collect();
        let run2: Vec<TurnProjection> = (0..=4).map(|t| derive_projection(&events, t)).collect();
        assert_eq!(run1, run2, "structural identity");
        assert_eq!(
            serde_json::to_string(&run1).unwrap(),
            serde_json::to_string(&run2).unwrap(),
            "byte-level determinism"
        );
    }

    /// ── Force-resident overlay (UC2 visibility probe). ────────────────────────
    /// A stubbed page forced Full in the projection: stub text dropped, tally
    /// re-derived, facts/violations untouched, multi-variant refs all flipped.
    #[test]
    fn overlay_flips_stub_to_full_and_re_tallies() {
        let events = vec![
            declare_file("tool:read_file(src/a)", "h-a1", 120),
            declare_file("tool:read_file(src/b)", "h-b", 400),
            evict_stubs(1, "tool:read_file(src/a)", "h-a1"),
        ];
        let proj = derive_projection(&events, 1);
        // Turn 1: a evicted -> Stub (evict@t is visible at turn t), b resident.
        assert_eq!((proj.tally.resident_tokens, proj.tally.stubbed_tokens), (400, 120));

        let refs = vec![Pin::ref_pin("tool:read_file(src/a)")];
        let (pinned, forced) = proj.clone().with_forced_resident(&refs);
        assert_eq!(forced.len(), 1);
        assert_eq!(forced[0].page.content_hash, "h-a1");
        assert_eq!(forced[0].tokens, 120);
        let a_slot = pinned.slots.iter().find(|s| s.reference.id.content_hash == "h-a1").unwrap();
        assert_eq!(a_slot.mode, RenderMode::Full);
        assert!(a_slot.stub_text.is_none(), "stub text dropped on override");
        assert_eq!(pinned.tally.resident_tokens, 520);
        assert_eq!(pinned.tally.stubbed_slots, 0);
        // Facts/violations untouched by the overlay.
        assert_eq!(pinned.violations, proj.violations);

        // Unknown ref: no flip, nothing forced, projection identical.
        let ghost = vec![Pin::ref_pin("ghost")];
        let (same, forced_none) = proj.clone().with_forced_resident(&ghost);
        assert!(forced_none.is_empty());
        assert_eq!(same, proj);
    }

    #[test]
    fn overlay_flips_every_content_hash_variant_of_one_ref() {
        let events = vec![
            declare_file("tool:read_file(src/a)", "h-a1", 120),
            declare_file("tool:read_file(src/a)", "h-a2", 120),
            evict_stubs(1, "tool:read_file(src/a)", "h-a1"),
            evict_stubs(1, "tool:read_file(src/a)", "h-a2"),
        ];
        let proj = derive_projection(&events, 1);
        let refs = vec![Pin::ref_pin("tool:read_file(src/a)")];
        let (pinned, forced) = proj.with_forced_resident(&refs);
        assert_eq!(forced.len(), 2, "both variants flipped");
        assert_eq!(pinned.tally.resident_tokens, 240);
        assert_eq!(pinned.tally.stubbed_tokens, 0);
    }

    #[test]
    fn precision_pin_flips_only_the_exact_identity() {
        // Two content-hash variants of one ref, both stubbed at turn 1.
        let events = vec![
            declare_file("tool:read_file(src/a)", "h-a1", 120),
            declare_file("tool:read_file(src/a)", "h-a2", 120),
            evict_stubs(1, "tool:read_file(src/a)", "h-a1"),
            evict_stubs(1, "tool:read_file(src/a)", "h-a2"),
        ];
        let proj = derive_projection(&events, 1);
        let (pinned, forced) =
            proj.clone().with_forced_resident(&[Pin::identity("tool:read_file(src/a)", "h-a1")]);
        assert_eq!(forced.len(), 1, "only the exact identity flips");
        assert_eq!(forced[0].page.content_hash, "h-a1");
        let one = pinned
            .slots
            .iter()
            .find(|s| s.reference.id.content_hash == "h-a2")
            .unwrap();
        assert_eq!(one.mode, RenderMode::Stub, "sibling variant untouched");
        assert_eq!(
            (pinned.tally.resident_tokens, pinned.tally.stubbed_tokens),
            (120, 120)
        );

        // Contrast: the broad T16 form flips both variants of the ref.
        let (broad, forced_broad) =
            proj.with_forced_resident(&[Pin::ref_pin("tool:read_file(src/a)")]);
        assert_eq!(forced_broad.len(), 2);
        assert_eq!(broad.tally.resident_tokens, 240);
    }

    #[test]
    fn mixed_pin_list_applies_both_kinds() {
        // a and b stubbed at turn 1; c never evicted (Full — pinning it is a
        // no-op flip). One broad pin + one precision pin + one identity on a
        // Full page.
        let events = vec![
            declare_file("file:a", "h-a", 100),
            declare_file("file:b", "h-b", 200),
            declare_file("file:c", "h-c", 400),
            evict_stubs(1, "file:a", "h-a"),
            evict_stubs(1, "file:b", "h-b"),
        ];
        let proj = derive_projection(&events, 1);
        let pins = vec![
            Pin::ref_pin("file:b"),
            Pin::identity("file:a", "h-a"),
            Pin::identity("file:c", "h-c"),
        ];
        let (pinned, forced) = proj.with_forced_resident(&pins);
        // Flips count Stub→Full only: the Full c identity is not a flip.
        let flipped: BTreeSet<&str> =
            forced.iter().map(|f| f.page.content_hash.as_str()).collect();
        assert_eq!(flipped, BTreeSet::from(["h-a", "h-b"]));
        assert_eq!(pinned.tally.stubbed_slots, 0);
        assert_eq!(pinned.tally.resident_tokens, 700);
    }
}

//! Stateful page table for decision events ('02' invariants), incl. render-mode
//! scheduling, pin counting, and telemetry-first violations.
//!
//! Timing semantics (RFC-0 duty: the event effect timing table):
//!     page.evict @ t   → stub visible AT turn t (evictions batch at the boundary
//!                        before the turn they are tagged with)
//!     page.fault @ t   → page re-materialized (full) FROM turn t + 1: a fault is
//!                        discovered while observing turn t's model output; the
//!                        page returns to the transcript at the next boundary
//!     page.pin/unpin   → no turn (v0): a working-set decision; "effective turn"
//!                        unknown until the draft gains it. Flagged for RFC-0.
//!     same-turn rule   → ordering is by (effective_turn, stream seq): the change
//!                        with the latest such pair with turn ≤ t wins. Stream seq
//!                        breaks same-turn ties; a scheduled re-materialization at
//!                        t+1 is NOT cancelled by an earlier-effective later-seq evict.

use std::collections::BTreeMap;

use ctxvm_codec::{Event, PageId, PageRef, RenderMode};

/// Page identity: `(logical_ref, content_hash)` — the standard's page key.
pub type PageKey = (String, String);

/// Serde support so projections (and future CLI output) serialize deterministically.
/// Kinds serialize as stable labels, not full variant dumps.
impl serde::Serialize for ViolationKind {
    fn serialize<S: serde::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        use ViolationKind::*;
        let label = match self {
            DuplicateDeclare { .. } => "duplicateDeclare",
            DecisionOfUnknownPage { .. } => "decisionOfUnknownPage",
            EvictWhileStubbed { .. } => "evictWhileStubbed",
            EvictWhilePinned { .. } => "evictWhilePinned",
            FaultOfResidentPage { .. } => "faultOfResidentPage",
            DuplicateFault { .. } => "duplicateFault",
            UnpinOfUnpinned { .. } => "unpinOfUnpinned",
            ContentAttach { .. } => "contentAttach",
        };
        serializer.serialize_str(label)
    }
}

impl serde::Serialize for Violation {
    fn serialize<S: serde::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        use serde::ser::SerializeStruct;
        let mut s = serializer.serialize_struct("Violation", 2)?;
        s.serialize_field("seq", &self.seq)?;
        s.serialize_field("kind", &self.kind)?;
        s.end()
    }
}

///Telemetry-first outcome of processing an event: the pager LOGS anomalies and keeps
/// going (03: "errors are events too — never thrown").
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Violation {
    /// 0-based index of the offending event in stream order.
    pub seq: usize,
    pub kind: ViolationKind,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ViolationKind {
    /// Same page key re-declared with a different descriptor — first wins.
    DuplicateDeclare { page: PageId },
    /// Decision targets a page that was never declared.
    DecisionOfUnknownPage { page: PageId, decision: &'static str },
    /// Evicting an already-stubbed page (no state change; still logged).
    EvictWhileStubbed { page: PageId },
    /// Evicting a pinned page (policy error; state change still applied and logged).
    EvictWhilePinned { page: PageId },
    /// Fault against a resident page — faults must target evicted pages.
    FaultOfResidentPage { page: PageId },
    /// Redundant fault against an already-faulted (stub) page without an intervening
    /// evict; deterministic, but flagged for the profiler.
    DuplicateFault { page: PageId },
    /// Unpin of a page that is not pinned. State clamps to zero; logged.
    UnpinOfUnpinned { page: PageId },
    /// Content attached to an unknown page, or mismatched re-attach.
    ContentAttach { page: PageId, reason: &'static str },
}

/// Scheduled render-mode changes for one page, in strict stream order.
type Changes = Vec<(u64, usize, RenderMode)>;

/// Per-page table record + render-mode state machine.
#[derive(Debug, Clone, PartialEq)]
pub struct PageTrack {
    /// The declaring descriptor — first declaration wins (`DuplicateDeclare` otherwise).
    pub reference: PageRef,
    /// Environment-supplied content (None = unmaterialized host-side; NOT trace data).
    pub content: Option<String>,
    /// Deterministic slot ordering key: first-declaration stream order.
    pub declared_seq: usize,
    /// Net pin count (pin++ / unpin-- clamped at 0 with a violation).
    pins: usize,
    /// Stub text shown while stubbed: verbatim from the most recent evict (stream order).
    pub(crate) last_stub_text_cached: Option<String>,
    /// (effective_turn, stream_seq, mode) — mode_at scans backwards; the latest
    /// stream event with turn ≤ t wins.
    changes: Changes,
}

impl PageTrack {
    /// Render mode in effect at `turn`. Pure: state only depends on fed decisions.
    /// Ordering rule: the change with the latest (effective_turn, stream_seq) whose
    /// turn ≤ `turn` wins — effective turn dominates, stream order breaks ties.
    pub fn mode_at(&self, turn: u64) -> RenderMode {
        self.changes
            .iter()
            .filter(|(t, _s, _)| *t <= turn)
            .max_by_key(|(t, s, _)| (*t, *s))
            .map(|(_t, _s, m)| *m)
            .unwrap_or(RenderMode::Full)
    }

    /// How many render-mode changes were scheduled (audit surface).
    pub fn scheduled_changes(&self) -> usize {
        self.changes.len()
    }
}

/// The streaming engine: a page table that ingests decision events, scheduling
/// state changes at turn boundaries, and collecting violations (never throwing).
#[derive(Debug, Clone, Default, PartialEq)]
pub struct Playback {
    pages: BTreeMap<PageKey, PageTrack>,
    order: Vec<PageKey>,
    violations: Vec<Violation>,
    seq: usize,
}

impl Playback {
    pub fn new() -> Self {
        Self::default()
    }

    /// Build by replaying Decisions from an event slice in stream order.
    pub fn new_with(events: &[Event]) -> Self {
        let mut pb = Self::new();
        pb.feed_all(events);
        pb
    }

    /// Process one event in stream order. Returns the violations caused by THIS
    /// event only (also retained in `self.violations()`).
    pub fn feed(&mut self, event: &Event) -> Vec<Violation> {
        let seq = self.seq;
        self.seq += 1;
        let before = self.violations.len();

        match event {
            Event::PageDeclare { page } => {
                let key = page_key(&page.id);
                match self.pages.get(&key) {
                    Some(existing) if existing.reference == *page => {}
                    Some(_mismatched) => self.log(seq, ViolationKind::DuplicateDeclare {
                        page: page.id.clone(),
                    }),
                    None => {
                        self.order.push(key.clone());
                        self.pages.insert(
                            key,
                            PageTrack {
                                reference: page.clone(),
                                content: None,
                                declared_seq: seq,
                                pins: 0,
                                last_stub_text_cached: None,
                                changes: Vec::new(),
                            },
                        );
                    }
                }
            }
            Event::PageEvict { turn, page, stub_text } => {
                // Clone-then-mutate: violation checks read a private copy, so
                // logging never races the table borrow.
                let key = page_key(page);
                match self.pages.get(&key).cloned() {
                    None => self.log_unknown(seq, page, "evict"),
                    Some(track) => {
                        if track.pins() > 0 {
                            // Policy error, but telemetry-first: apply + log.
                            self.log(seq, ViolationKind::EvictWhilePinned { page: page.clone() });
                        }
                        if track.mode_at(*turn) == RenderMode::Stub {
                            self.log(seq, ViolationKind::EvictWhileStubbed { page: page.clone() });
                        }
                        let real = self.pages.get_mut(&key).expect("present (cloned above)");
                        real.last_stub_text_cached = Some(stub_text.clone());
                        real.push_change(*turn, seq, RenderMode::Stub);
                    }
                }
            }
            Event::PageFault { turn, page, .. } => {
                // Fault discovered at turn t; page re-materializes at t + 1.
                let next_turn = turn.saturating_add(1);
                let key = page_key(page);
                match self.pages.get(&key).cloned() {
                    None => self.log_unknown(seq, page, "fault"),
                    Some(track) => match track.mode_at(*turn) {
                        RenderMode::Full => {
                            self.log(
                                seq,
                                ViolationKind::FaultOfResidentPage { page: page.clone() },
                            );
                        }
                        RenderMode::Stub => {
                            // Redundant fault against an already-pending rematerialize?
                            if track
                                .changes
                                .iter()
                                .rev()
                                .take_while(|(t, _s, _)| *t > *turn)
                                .any(|(_t, _s, m)| *m == RenderMode::Full)
                            {
                                self.log(
                                    seq,
                                    ViolationKind::DuplicateFault { page: page.clone() },
                                );
                            }
                            self.pages
                                .get_mut(&key)
                                .expect("present (cloned above)")
                                .push_change(next_turn, seq, RenderMode::Full);
                        }
                    },
                }
            }
            Event::PagePin { page, .. } => {
                let key = page_key(page);
                match self.pages.get_mut(&key) {
                    Some(track) => track.pin_increment(),
                    None => self.log_unknown(seq, page, "pin"),
                }
            }
            Event::PageUnpin { page, .. } => {
                let key = page_key(page);
                match self.pages.get(&key).cloned() {
                    None => self.log_unknown(seq, page, "unpin"),
                    Some(track) if track.pins() == 0 => {
                        self.log(seq, ViolationKind::UnpinOfUnpinned { page: page.clone() });
                    }
                    Some(_) => {
                        self.pages.get_mut(&key).expect("present (cloned above)").pin_decrement();
                    }
                }
            }
            // Facts and metadata events do not schedule state (facts are T1d's
            // comparison surface; session/call events are profiler metadata).
            Event::PageRender { .. }
            | Event::TurnRender { .. }
            | Event::SessionOpen { .. }
            | Event::CallMeta { .. } => {}
        }

        self.violations[before..].to_vec()
    }

    /// Feed a whole event slice in stream order.
    pub fn feed_all(&mut self, events: &[Event]) {
        for event in events {
            self.feed(event);
        }
    }

    /// Attach host-side content for a declared page. Content is environment data
    /// (the trace stores only `content_hash`); it never influences decisions.
    /// Violations from this out-of-band call are seq-stamped with the next unused
    /// stream index (there is no event to point at).
    pub fn attach_content(&mut self, page: &PageId, content: impl Into<String>) {
        let key = page_key(page);
        match self.pages.get_mut(&key) {
            None => self.log(
                self.seq,
                ViolationKind::ContentAttach {
                    page: page.clone(),
                    reason: "unknown page",
                },
            ),
            Some(track) => {
                let content = content.into();
                match &track.content {
                    Some(existing) if existing != &content => {
                        self.log(
                            self.seq,
                            ViolationKind::ContentAttach {
                                page: page.clone(),
                                reason: "content differs from previous attach; page identity is (ref, hash)",
                            },
                        );
                    }
                    Some(_) => {}
                    None => {
                        track.content = Some(content);
                    }
                }
            }
        }
    }

    // ── accessors ───────────────────────────────────────────────────────────

    /// All violations observed so far, in stream order.
    pub fn violations(&self) -> &[Violation] {
        &self.violations
    }

    /// Page record lookup by full page key.
    pub fn page(&self, page: &PageId) -> Option<&PageTrack> {
        self.pages.get(&page_key(page))
    }

    /// Pages in first-declaration order — the deterministic slot order.
    pub fn pages_in_declaration_order(&self) -> impl Iterator<Item = &PageTrack> + '_ {
        self.order.iter().filter_map(|key| self.pages.get(key))
    }

    // ── internals ───────────────────────────────────────────────────────────

    fn log(&mut self, seq: usize, kind: ViolationKind) {
        self.violations.push(Violation { seq, kind });
    }

    fn log_unknown(&mut self, seq: usize, page: &PageId, decision: &'static str) {
        self.log(
            seq,
            ViolationKind::DecisionOfUnknownPage {
                page: page.clone(),
                decision,
            },
        );
    }
}

fn page_key(page: &PageId) -> PageKey {
    (page.logical_ref.clone(), page.content_hash.clone())
}

impl PageTrack {
    fn push_change(&mut self, turn: u64, seq: usize, mode: RenderMode) {
        self.changes.push((turn, seq, mode));
    }

    pub fn pins(&self) -> usize {
        self.pins
    }

    /// Module-internal pin bookkeeping (clamped at 0 with a violation recorded by
    /// the table, reflected here as a no-op).
    pub(crate) fn pin_increment(&mut self) {
        self.pins += 1;
    }

    pub(crate) fn pin_decrement(&mut self) {
        self.pins = self.pins.saturating_sub(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ctxvm_codec::{FaultSource, PageId, PageKind, PageRef};

    fn aid(name: &str, hash: &str) -> PageId {
        PageId {
            logical_ref: format!("file:{name}"),
            content_hash: hash.to_owned(),
        }
    }

    fn declare(id: &PageId, kind: PageKind, tokens: u64) -> Event {
        Event::PageDeclare {
            page: PageRef { id: id.clone(), kind, tokens },
        }
    }

    fn evict(turn: u64, id: &PageId) -> Event {
        Event::PageEvict { turn, page: id.clone(), stub_text: format!("stub for {}", id.logical_ref) }
    }

    fn fault(turn: u64, id: &PageId) -> Event {
        Event::PageFault { turn, page: id.clone(), source: FaultSource::ToolRecall, latency_ms: None }
    }

    #[test]
    fn mode_at_is_full_before_any_change() {
        let mut pb = Playback::new();
        let a = aid("a.ts", "h1");
        pb.feed(&declare(&a, PageKind::File, 10));
        assert_eq!(pb.page(&a).unwrap().mode_at(999), RenderMode::Full);
    }

    /// Same-turn tiebreak: the LATER stream event wins.
    #[test]
    fn same_turn_conflicts_resolved_by_stream_order() {
        let mut pb = Playback::new();
        let a = aid("a.ts", "h1");
        pb.feed_all(&[declare(&a, PageKind::File, 10), evict(4, &a), fault(4, &a), evict(4, &a)]);
        // evicts at seq 1 and 3, fault at seq 2 (schedules full@5).
        // events @ turn 4: last one is an evict → stub at 4; full scheduled @5.
        let track = pb.page(&a).unwrap();
        assert_eq!(track.mode_at(3), RenderMode::Full);
        assert_eq!(track.mode_at(4), RenderMode::Stub);
        assert_eq!(track.mode_at(5), RenderMode::Full);
    }

    #[test]
    fn violations_carry_their_stream_index() {
        let mut pb = Playback::new();
        let ghost = aid("ghost.ts", "h0");
        pb.feed(&evict(0, &ghost));
        pb.feed(&declare(&aid("a.ts", "h1"), PageKind::File, 10));
        let v = &pb.violations()[0];
        assert_eq!(v.seq, 0);
        assert_eq!(
            v.kind,
            ViolationKind::DecisionOfUnknownPage {
                page: ghost.clone(),
                decision: "evict"
            }
        );
    }

    #[test]
    fn fault_effect_lands_on_next_turn_exactly() {
        let mut pb = Playback::new();
        let a = aid("a.ts", "h1");
        pb.feed_all(&[declare(&a, PageKind::File, 10), evict(1, &a), fault(2, &a)]);
        let track = pb.page(&a).unwrap();
        assert_eq!(track.mode_at(1), RenderMode::Stub); // evicted@1
        assert_eq!(track.mode_at(2), RenderMode::Stub); // fault@2 → not yet
        assert_eq!(track.mode_at(3), RenderMode::Full); // materialized@3
        // hand-summed changes: exactly two scheduled changes
        assert_eq!(track.scheduled_changes(), 2);
    }
}

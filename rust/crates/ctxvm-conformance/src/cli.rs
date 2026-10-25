//! Shared run cores for the four conformance CLI bins (`replay`, `profile`,
//! `diff`, `export`) — the single serialization / exit-code sites.
//!
//! Byte-identity contract (card UC1-B1, org decision "engine logic converges on
//! shared bindings; per-port stays interim only for thin wrappers"): the thin
//! CLI mains and the ctxvm-py (PyO3) binding both drive [`replay_core`] and
//! friends, so `ctxvm replay <t> --turn N` and `ctxvm_py.replay("t", turn=N)`
//! emit byte-identical stdout and identical exit codes by construction —
//! remainder parity belongs to the binding parity tests (packages/py).
//!
//! [`CliOutcome`] carries exactly what the CLI would do: `stdout` is the
//! payload the bin prints (canonical JSON + trailing newline, `""` when the
//! CLI prints nothing), `fatal` is the error for the bin's `fail()` path
//! (the bin adds the `ctxvm <bin>: ` prefix), and `warnings` carry the
//! non-fatal `warning: ` lines the CLI writes after its report (export only).
//! File-mode (`--output`) writes the same bytes the stdout mode prints and
//! leaves `stdout` empty — identical behavior for both drivers.

use std::{collections::BTreeSet, fs};

use serde_json::json;

use ctxvm_codec::{read_jsonl, to_line, Event, FaultSource};
use ctxvm_core::{
    build_handoff_snapshot, derive_projection, diff_traces, event_turn, handoff_prefix, profile,
    replay, replay_turn, scan_redaction, turn_windows, EvictRow, FaultRow, HandoffSnapshot, Pin,
    ReplayReport, TraceRelation, TurnProjection,
};

/// Vocabulary types accepted by `profile --event` (mirrors the bin usage text).
pub const EVENT_TYPES: [&str; 9] = [
    "session.open",
    "page.declare",
    "page.render",
    "page.evict",
    "page.fault",
    "page.pin",
    "page.unpin",
    "turn.render",
    "call.meta",
];

pub const SOURCES: [FaultSource; 4] = [
    FaultSource::ToolRecall,
    FaultSource::IdentifierScan,
    FaultSource::ExplicitApi,
    FaultSource::Semantic,
];

pub const SOURCES_STR: [&str; 4] = ["tool_recall", "identifier_scan", "explicit_api", "semantic"];

pub fn parse_source(s: &str) -> Option<FaultSource> {
    Some(SOURCES[SOURCES_STR.iter().position(|c| {
        c.eq_ignore_ascii_case(s) || c.replace('_', "").eq_ignore_ascii_case(&s.replace('_', ""))
    })?])
}

#[derive(Debug, Clone)]
pub struct CliOutcome {
    pub exit: u8,
    pub stdout: String,
    pub fatal: Option<String>,
    pub warnings: Vec<String>,
}

impl CliOutcome {
    fn fail(code: u8, message: impl Into<String>) -> Self {
        Self { exit: code, stdout: String::new(), fatal: Some(message.into()), warnings: Vec::new() }
    }

    fn empty() -> Self {
        Self { exit: 0, stdout: String::new(), fatal: None, warnings: Vec::new() }
    }

    /// stderr text exactly as the CLI emits it (`ctxvm <bin>: ` prefix for the
    /// fatal path, `warning: ` lines for non-fatal warnings).
    pub fn stderr_text(&self, bin: &str) -> String {
        let mut text = String::new();
        if let Some(message) = self.fatal.as_deref() {
            text.push_str(&format!("ctxvm {bin}: {message}\n"));
        }
        for warning in &self.warnings {
            text.push_str(&format!("warning: {warning}\n"));
        }
        text
    }
}

// ---------------------------------------------------------------------------
// replay
// ---------------------------------------------------------------------------

/// Declared logical_refs, deterministic (sorted, unique) order for error text.
fn declared_refs(trace: &[Event]) -> Vec<String> {
    trace
        .iter()
        .filter_map(|e| match e {
            Event::PageDeclare { page } => Some(page.id.logical_ref.clone()),
            _ => None,
        })
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect()
}

/// Declared full identities (sorted, unique) for precision-pin resolution.
fn declared_identities(trace: &[Event]) -> BTreeSet<(String, String)> {
    trace
        .iter()
        .filter_map(|e| match e {
            Event::PageDeclare { page } => {
                Some((page.id.logical_ref.clone(), page.id.content_hash.clone()))
            }
            _ => None,
        })
        .collect()
}

/// One `--pin` value → its matching form ([`Pin`]).
///
/// - `ref` / `page:ref` → broad form: every stubbed content-hash variant of the
///   ref flips.
/// - `(ref, hash)` / `(page:ref, hash)` → T20 precision form: only the stubbed
///   slot with that exact identity flips. Split at the **last** comma — refs
///   may contain commas (tool-call shapes) while the hash is always the final
///   component.
fn parse_pin(raw: &str) -> Result<Pin, String> {
    const MALFORMED: &str = "malformed precision pin — the form is `(ref, hash)`";
    let trimmed = raw.trim();
    // The memo `page:` prefix composes with both forms: strip it up front.
    let without_memo = trimmed.strip_prefix("page:").unwrap_or(trimmed);
    if let Some(inner) = without_memo.strip_prefix('(') {
        let inner = inner
            .strip_suffix(')')
            .ok_or_else(|| format!("{MALFORMED}: `{raw}`"))?;
        let (reference, hash) = inner
            .rsplit_once(',')
            .ok_or_else(|| format!("{MALFORMED}: `{raw}`"))?;
        let reference = reference.trim();
        if reference.is_empty() || hash.trim().is_empty() {
            return Err(format!("{MALFORMED}: `{raw}`"));
        }
        return Ok(Pin::identity(reference, hash.trim()));
    }
    Ok(Pin::ref_pin(without_memo))
}

/// All `--pin` values → pin forms (broad + precision mixed allowed).
fn build_pins(raw: &[String]) -> Result<Vec<Pin>, String> {
    raw.iter().map(|s| parse_pin(s)).collect()
}

/// The report label for a pin: the normalized broad ref, or the normalized
/// `(ref, hash)` textual form for precision pins.
fn pin_label(pin: &Pin) -> String {
    match pin {
        Pin::Ref(reference) => reference.clone(),
        Pin::Identity {
            logical_ref,
            content_hash,
        } => format!("({logical_ref}, {content_hash})"),
    }
}

/// Resolve every pin against the trace's declared pages: Err = the exact
/// problem for the first (in argument order) unresolvable pin (exit 2).
fn resolve_pins(pins: &[Pin], trace: &[Event]) -> Result<(), String> {
    let refs = declared_refs(trace);
    let ref_set: BTreeSet<String> = refs.iter().cloned().collect();
    let identities = declared_identities(trace);
    for pin in pins {
        match pin {
            Pin::Ref(r) if !ref_set.contains(r) => {
                return Err(format!(
                    "--pin: no declared page matches `{r}` · declared refs: {}",
                    refs.join(", ")
                ));
            }
            Pin::Identity {
                logical_ref,
                content_hash,
            } if !ref_set.contains(logical_ref) => {
                return Err(format!(
                    "--pin: no declared page matches `({logical_ref}, {content_hash})` · declared refs: {}",
                    refs.join(", ")
                ));
            }
            Pin::Identity {
                logical_ref,
                content_hash,
            } => {
                let key = (logical_ref.clone(), content_hash.clone());
                if !identities.contains(&key) {
                    let hashes: Vec<String> = identities
                        .iter()
                        .filter(|(r, _)| r == logical_ref)
                        .map(|(_, h)| h.clone())
                        .collect();
                    return Err(format!(
                        "--pin: `{logical_ref}` is declared but not under hash `{content_hash}` · declared hashes for it: {}",
                        hashes.join(", ")
                    ));
                }
            }
            _ => {}
        }
    }
    Ok(())
}

/// `ctxvm replay` — everything after argument parsing (also used by ctxvm-py).
pub fn replay_core(trace: &str, turn: Option<u64>, pins: &[String], output: Option<&str>) -> CliOutcome {
    let src = match fs::read_to_string(trace) {
        Ok(s) => s,
        Err(e) => return CliOutcome::fail(2, format!("cannot read `{trace}`: {e}")),
    };
    let trace = match read_jsonl(&src) {
        Err(e) => return CliOutcome::fail(2, format!("parse error: {e}")),
        Ok(t) => t,
    };

    // Guard AFTER read/parse — phase order mirrors the pre-extraction CLI
    // (read → parse → pin guard → report) so the argv-driven behavior is
    // unchanged (UC1-B1 byte-neutral proof).
    if !pins.is_empty() && turn.is_none() {
        return CliOutcome::fail(2, "--pin requires --turn (the overlay is per-turn)");
    }

    // Fact check: whole trace by default, only `turn`'s facts under --turn.
    let report: ReplayReport = match turn {
        Some(n) => replay_turn(&trace, n),
        None => replay(&trace),
    };
    let clean = report.divergences.is_empty();
    let divergence_note = match (clean, output) {
        (true, _) => None,
        (false, Some(_)) => Some("replay reported divergences (see report file)"),
        (false, None) => Some("replay reported divergences (see JSON above)"),
    };

    let mut body = match turn {
        None => serde_json::to_string_pretty(&report).expect("report is serializable"),
        Some(n) => {
            let pin_specs = match build_pins(pins) {
                Err(e) => return CliOutcome::fail(2, e),
                Ok(p) => p,
            };
            if let Err(e) = resolve_pins(&pin_specs, &trace) {
                return CliOutcome::fail(2, e);
            }
            let mut value = json!({
                "turn": n,
                "divergences": report.divergences,
                "violations": report.violations,
                "events": report.events,
            });
            if !pins.is_empty() {
                let projection: TurnProjection = derive_projection(&trace, n);
                let (projection, forced) = projection.with_forced_resident(&pin_specs);
                let labels: Vec<String> = pin_specs.iter().map(pin_label).collect();
                let obj = value
                    .as_object_mut()
                    .expect("json! builds an object");
                obj.insert("pins".into(), serde_json::to_value(&labels).expect("labels serialize"));
                obj.insert(
                    "forcedResident".into(),
                    serde_json::to_value(&forced).expect("forced residents serialize"),
                );
                obj.insert(
                    "projection".into(),
                    serde_json::to_value(&projection).expect("projection is serializable"),
                );
            } else {
                let obj = value.as_object_mut().expect("json! builds an object");
                obj.insert(
                    "projection".into(),
                    serde_json::to_value(derive_projection(&trace, n))
                        .expect("projection is serializable"),
                );
            }
            serde_json::to_string_pretty(&value).expect("Value is serializable")
        }
    };
    body.push('\n');

    let mut outcome = CliOutcome::empty();
    match output {
        Some(path) => {
            if let Err(e) = fs::write(path, &body) {
                return CliOutcome::fail(2, format!("cannot write `{path}`: {e}"));
            }
        }
        None => outcome.stdout = body,
    }
    if let Some(note) = divergence_note {
        outcome.exit = 1;
        outcome.fatal = Some(note.to_string());
    }
    outcome
}

// ---------------------------------------------------------------------------
// profile
// ---------------------------------------------------------------------------

/// Turns filter for row families: None = every turn; Some(set) = membership.
fn turn_passes(turns: &Option<Vec<u64>>, turn: u64) -> bool {
    turns.as_ref().map_or(true, |set| set.contains(&turn))
}

/// Events without a turn field (`session.open`, `page.declare`, `page.pin`,
/// `page.unpin`) cannot be windowed — they pass a `--turns` filter unchanged.
fn turn_of(event: &Event) -> Option<u64> {
    match event {
        Event::PageEvict { turn, .. }
        | Event::PageFault { turn, .. }
        | Event::TurnRender { turn, .. }
        | Event::CallMeta { turn, .. } => Some(*turn),
        _ => None,
    }
}

/// The dotted event type of an event (mirrors the JSON type tag).
fn event_event_type(event: &Event) -> &'static str {
    match event {
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

/// `ctxvm profile` — everything after argument parsing (also used by ctxvm-py).
///
/// Validation order mirrors the CLI phase order: `--event` vocabulary, then
/// `--source` taxonomy, then the `--turns` window spec, then the run-time
/// `--source requires --event page.fault` guards, then IO. The typed binding
/// surface passes the same raw strings, so every validation message is the
/// CLI's byte-for-byte.
pub fn profile_core(
    trace: &str,
    events: &[String],
    turns: Option<&str>,
    source: Option<&str>,
    output: Option<&str>,
) -> CliOutcome {
    for event in events {
        if !EVENT_TYPES.contains(&event.as_str()) {
            return CliOutcome::fail(
                2,
                format!("--event: `{event}` is not a vocabulary type · valid: {}", EVENT_TYPES.join(", ")),
            );
        }
    }
    if let Some(source_raw) = source {
        if parse_source(source_raw).is_none() {
            return CliOutcome::fail(
                2,
                format!("--source: `{source_raw}` is not a taxonomy source · valid: {:?}", SOURCES_STR),
            );
        }
    }
    let turns = match turns {
        Some(spec) => match turn_windows(spec) {
            Err(e) => return CliOutcome::fail(2, e),
            Ok(expanded) => Some(expanded.into_iter().collect::<BTreeSet<_>>().into_iter().collect()),
        },
        None => None,
    };
    if source.is_some() {
        if !events.iter().any(|e| e == "page.fault") {
            return CliOutcome::fail(2, "--source requires --event page.fault");
        }
        if events.iter().any(|e| e.as_str() != "page.fault") {
            return CliOutcome::fail(
                2,
                "--source applies only to fault rows (drop other --event selections)",
            );
        }
    }

    let src = match fs::read_to_string(trace) {
        Err(e) => return CliOutcome::fail(2, format!("cannot read `{trace}`: {e}")),
        Ok(s) => s,
    };
    let trace = match read_jsonl(&src) {
        Err(e) => return CliOutcome::fail(2, format!("parse error: {e}")),
        Ok(t) => t,
    };

    let report = profile(&trace);

    let mut value = json!({
        "events": report.summary.events,
        "summary": report.summary,
        "pages": report.pages,
        "turnTallies": report.turn_tallies,
        "violations": report.violations,
    });
    let obj = value.as_object_mut().expect("json! builds an object");

    let wants_faults = events.iter().any(|e| e == "page.fault");
    let wants_evictions = events.iter().any(|e| e == "page.evict");
    let wants_raw: Vec<&str> = events
        .iter()
        .filter(|e| e.as_str() != "page.fault" && e.as_str() != "page.evict")
        .map(String::as_str)
        .collect();

    if wants_faults {
        let wanted = source.map(|s| parse_source(s).expect("validated above"));
        let rows: Vec<FaultRow> = report
            .faults
            .iter()
            .filter(|row| turn_passes(&turns, row.turn))
            .filter(|row| wanted.map_or(true, |w| row.source == w))
            .cloned()
            .collect();
        obj.insert("faults".into(), serde_json::to_value(&rows).expect("fault rows serialize"));
    }
    if wants_evictions {
        let rows: Vec<EvictRow> = report
            .evictions
            .iter()
            .filter(|row| turn_passes(&turns, row.turn))
            .cloned()
            .collect();
        obj.insert(
            "evictions".into(),
            serde_json::to_value(&rows).expect("evict rows serialize"),
        );
    }
    if !wants_raw.is_empty() {
        let rows: Vec<serde_json::Value> = trace
            .iter()
            .filter(|event| wants_raw.contains(&event_event_type(event)))
            .filter(|event| turn_of(event).map_or(true, |t| turn_passes(&turns, t)))
            .map(|event| serde_json::to_value(event).expect("event serializes"))
            .collect();
        obj.insert("filteredEvents".into(), serde_json::Value::Array(rows));
    }

    let pretty = serde_json::to_string_pretty(&value).expect("report serializes");
    let mut body = pretty;
    body.push('\n');

    let mut outcome = CliOutcome::empty();
    match output {
        Some(path) => {
            if let Err(e) = fs::write(path, &body) {
                return CliOutcome::fail(2, format!("cannot write `{path}`: {e}"));
            }
        }
        None => outcome.stdout = body,
    }
    outcome
}

// ---------------------------------------------------------------------------
// diff
// ---------------------------------------------------------------------------

/// `ctxvm diff` — everything after argument parsing (also used by ctxvm-py).
pub fn diff_core(a: &str, b: &str, output: Option<&str>) -> CliOutcome {
    let read = |path: &str| -> Result<Vec<Event>, CliOutcome> {
        let src = match fs::read_to_string(path) {
            Ok(s) => s,
            Err(e) => return Err(CliOutcome::fail(2, format!("cannot read `{path}`: {e}"))),
        };
        match read_jsonl(&src) {
            Ok(t) => Ok(t),
            Err(e) => Err(CliOutcome::fail(2, format!("parse error in `{path}`: {e}"))),
        }
    };
    let trace_a = match read(a) {
        Ok(t) => t,
        Err(outcome) => return outcome,
    };
    let trace_b = match read(b) {
        Ok(t) => t,
        Err(outcome) => return outcome,
    };

    let report = diff_traces(&trace_a, &trace_b);
    let pretty = serde_json::to_string_pretty(&report).expect("report is serializable");
    let mut body = pretty;
    body.push('\n');

    let mut outcome = CliOutcome::empty();
    match output {
        Some(path) => {
            if let Err(e) = fs::write(path, &body) {
                return CliOutcome::fail(2, format!("cannot write `{path}`: {e}"));
            }
        }
        None => outcome.stdout = body,
    }
    match &report.relation {
        TraceRelation::Divergent => {
            outcome.exit = 1;
            outcome.fatal = Some("traces diverge inside the shared length (see JSON above)".to_string());
        }
        _ => {}
    }
    outcome
}

// ---------------------------------------------------------------------------
// export (T21 handoff snapshot builder)
// ---------------------------------------------------------------------------

/// One file shipped by the snapshot.
pub struct Artifact {
    path: String,
    media_type: String,
    /// Payload formatter for wrapping media (e.g. zstd frames).
    payload: Option<&'static str>,
    compression: Option<&'static str>,
    bytes: u64,
}

impl Artifact {
    fn to_json(&self) -> serde_json::Value {
        json!({
            "path": self.path,
            "mediaType": self.media_type,
            "payload": self.payload,
            "compression": self.compression,
            "bytes": self.bytes,
        })
    }

    fn yaml_line(&self) -> String {
        let compression = self
            .compression
            .map(|c| format!("    compression: {c}\n"))
            .unwrap_or_default();
        let payload = self
            .payload
            .map(|p| format!("    payload: {}\n", y(p)))
            .unwrap_or_default();
        format!(
            "  - path: {}\n    mediaType: {}\n{payload}{compression}    bytes: {}\n",
            y(&self.path),
            y(&self.media_type),
            self.bytes
        )
    }
}

/// Session identity from `session.open` (best-effort fallbacks).
struct SessionHeader {
    agent: String,
    model: String,
    provider: String,
    budget_tokens: u64,
    tagged: bool,
}

fn session_header(events: &[Event]) -> SessionHeader {
    events.first().and_then(|e| match e {
        Event::SessionOpen { agent_id, model, provider, budget_tokens, .. } => {
            Some(SessionHeader {
                agent: agent_id.clone(),
                model: model.clone(),
                provider: provider.clone(),
                budget_tokens: *budget_tokens,
                tagged: true,
            })
        }
        _ => None,
    })
    .unwrap_or(SessionHeader {
        agent: "unknown".into(),
        model: "unknown".into(),
        provider: "unknown".into(),
        budget_tokens: 0,
        tagged: false,
    })
}

/// YAML scalar safe for every value this CLI emits (single-quoted form).
fn y(s: &str) -> String {
    format!("'{}'", s.replace('\'', "''"))
}

/// Verify-command text: replay/diff need plain JSONL, so a compressed
/// package decompresses first.
fn verify_lines(snapshot: &HandoffSnapshot, trace_name: &str, compressed: bool, source_display: &str) -> Vec<String> {
    let n = snapshot.turn;
    let (pref, plane) = if compressed && trace_name.ends_with(".zst") {
        let plain = trace_name.trim_end_matches(".zst").to_string();
        (
            format!("zstd -d {trace_name} -o {plain}"),
            plain,
        )
    } else {
        (String::new(), trace_name.to_string())
    };
    let mut lines = Vec::new();
    if !pref.is_empty() {
        lines.push(format!("  decompress: {}", y(&pref)));
    }
    lines.push(format!(
        "  replay: {}",
        y(&format!("ctxvm replay {plane} --turn {n}   # expect exit 0, divergences: []"))
    ));
    lines.push(format!(
        "  diff: {}",
        y(&format!(
            "ctxvm diff {source_display} {plane}   # expect extension relation; shared prefix matches turn {n}"
        ))
    ));
    lines
}

fn kpi_value(v: Option<f64>) -> String {
    match v {
        Some(x) => format!("{x:.4}"),
        None => "null".to_string(),
    }
}

fn manifest_yaml(
    snapshot: &HandoffSnapshot,
    session: &SessionHeader,
    artifacts: &[Artifact],
    source_display: &str,
    trace_name: &str,
    compressed: bool,
    redaction_hits: usize,
    redaction_texts: usize,
) -> String {
    let n = snapshot.turn;
    let mut out = Vec::<String>::new();
    out.push("# xCABI handoff snapshot manifest — turn %N% slice (ODPS 4.1 flavored)".replace("%N%", &n.to_string()));
    out.push("# Generated by `ctxvm export` (ctxvm v0); every artifact is checksummed in checksums.sha256.".into());
    out.push("schema: https://opendataproducts.org/v4.1/schema/odps.yaml".into());
    out.push("version: \"4.1\"".into());
    out.push("kind: xCABI-handoff-snapshot".into());
    out.push(String::new());
    out.push("product:".into());
    out.push("  metadata:".into());
    out.push(format!("    id: ctxvm-handoff-turn-{n}"));
    out.push(format!("    name: {}", &y(&format!("xCABI handoff snapshot at turn {n}"))));
    out.push(format!("    derivedFrom: {}", y(source_display)));
    if session.tagged {
        out.push(format!("    agent: {}", y(&session.agent)));
        out.push(format!("    model: {}", y(&session.model)));
        out.push(format!("    provider: {}", y(&session.provider)));
        out.push(format!("    budgetTokens: {}", session.budget_tokens));
    }
    out.push(format!("    sliceTurn: {n}"));
    out.push(format!("    sourceEvents: {}", snapshot.source_events));
    out.push(format!("    keptEvents: {}", snapshot.kept_events));
    out.push("  x-cabi:".into());
    out.push("    format: xCABI".into());
    out.push("    traceFormatVersion: \"0.1\"".into());
    out.push(format!(
        "    coverage: {}",
        y(&format!(
            "positional prefix through turn {n} (last event with a turn <= {n}; trailing turn-less bookkeeping excluded)"
        ))
    ));
    out.push(String::new());
    out.push("distribution:".into());
    let distribution = artifacts
        .iter()
        .map(|a| a.yaml_line().trim_end_matches('\n').to_string())
        .collect::<Vec<_>>()
        .join("\n");
    out.push(distribution);
    let dq_replay = snapshot.replay_determinism();
    let dq_fidelity = snapshot.source_fidelity();
    out.push(String::new());
    out.push("dataQuality:".into());
    out.push("  - check: replayDeterminism".into());
    out.push("    dimension: validity".into());
    out.push(format!("    passed: {dq_replay}"));
    out.push(format!(
        "    detail: {}",
        y(&format!(
            "{} slice events replayed; {} divergences",
            snapshot.replay.events,
            snapshot.replay.divergences.len()
        ))
    ));
    out.push("  - check: sourceFidelity".into());
    out.push("    dimension: validity".into());
    out.push(format!("    passed: {dq_fidelity}"));
    out.push(format!(
        "    detail: {}",
        y(&format!(
            "shared positional prefix {} of {} source events; relation {:?}",
            snapshot.source_common_prefix_events,
            snapshot.source_events,
            snapshot.relation_to_source
        ))
    ));
    out.push("  - check: pinLint".into());
    out.push("    dimension: completeness".into());
    out.push(format!("    passed: {}", snapshot.pin_lint.is_empty()));
    out.push(format!(
        "    detail: {}",
        y(&format!(
            "{} pin-lint hits (pin-family violations + pinned-stub slots at turn {n})",
            snapshot.pin_lint.len()
        ))
    ));
    out.push("  - check: redactionScan".into());
    out.push("    dimension: uniqueness".into());
    out.push(format!("    passed: {}", redaction_hits == 0));
    out.push(format!(
        "    detail: {}",
        y(&format!(
            "v0 credential-shaped token scan over {} artifact texts (trace slice + page table): {} hits",
            redaction_texts, redaction_hits
        ))
    ));
    out.push(String::new());
    out.push("kpi:".into());
    out.push("  - id: kpi-fault-recall".into());
    out.push(format!("    value: {}", kpi_value(snapshot.kpis.fault_recall)));
    out.push("    target: 0.95".into());
    out.push("    formula: 'faults recorded at turn <= N whose page is Full at N / faults recorded <= N; null when no faults'".into());
    out.push("  - id: kpi-net-token-reduction".into());
    out.push(format!("    value: {}", kpi_value(snapshot.kpis.net_token_reduction)));
    out.push("    target: 0.40".into());
    out.push("    formula: 'stubbedTokens / (residentTokens + stubbedTokens) at the slice turn; v0 stub-cost fraction (policy-vs-policy net cost is UC3)'".into());
    out.push("  - id: kpi-touch-ratio".into());
    out.push(format!("    value: {}", kpi_value(snapshot.kpis.touch_ratio)));
    out.push("    target: 0.60".into());
    out.push("    formula: 'distinct pages with a recorded full render <= N / declared slot roster; null when empty'".into());
    out.push(String::new());
    out.push("verify:".into());
    out.extend(verify_lines(snapshot, trace_name, compressed, source_display));
    let mut text = out.join("\n");
    text.push('\n');
    text
}

fn llms_txt(
    snapshot: &HandoffSnapshot,
    trace_name: &str,
    compressed: bool,
    source_display: &str,
) -> String {
    let n = snapshot.turn;
    let mut out = Vec::<String>::new();
    out.push(format!("# ctxvm handoff snapshot — turn {n}"));
    out.push(String::new());
    out.push(format!(
        "xCABI v0.1 trace slice for resuming an agent session within one harness. The trace up to turn {n} is a complete, self-contained snapshot of what the model has seen."
    ));
    out.push(String::new());
    out.push("## Artifacts".into());
    out.push(String::new());
    out.push(format!(
        "- {trace_name} — {}/{} source events from {}. Slice rule: events up to the last event with a turn <= {n} (trailing turn-less bookkeeping excluded).{}",
        snapshot.kept_events, snapshot.source_events, source_display,
        if compressed { " zstd-compressed; decompress to verify." } else { "" },
    ));
    out.push(format!(
        "- page-table-{n}.json — {} page slots at turn {n}: {} resident, {} stubbed. Derived deterministically from the slice (slot structure is a pure function of the events).",
        snapshot.projection.slots.len(),
        snapshot.projection.tally.resident_slots,
        snapshot.projection.tally.stubbed_slots
    ));
    out.push("- manifest.yaml — ODPS 4.1-flavored manifest: DQ checks (replay determinism, source fidelity, pin lint, redaction scan) and the three KPIs.".into());
    out.push("- checksums.sha256 — SHA-256 of every other artifact.".into());
    out.push(String::new());
    out.push("## Verify (before trusting the handoff)".into());
    out.push(String::new());
    let plane = if compressed && trace_name.ends_with(".zst") {
        trace_name.trim_end_matches(".zst").to_string()
    } else {
        trace_name.to_string()
    };
    if plane != trace_name {
        out.push(format!("- (decompress first: zstd -d {trace_name} -o {plane})"));
    }
    out.push(format!("- ctxvm replay {plane} --turn {n}   # expect exit 0, divergences: []"));
    out.push(format!(
        "- ctxvm diff {} {plane}   # expect extension relation; shared prefix matches",
        source_display
    ));
    out.push(String::new());
    out.push("## Resume (same harness)".into());
    out.push(String::new());
    out.push(format!(
        "Seed the next loop from page-table-{n}.json: resident pages render full; stubbed pages show their re-materialization instructions in the slice's page.evict rows."
    ));
    let mut text = out.join("\n");
    text.push('\n');
    text
}

/// `ctxvm export` — everything after argument parsing (also used by ctxvm-py).
/// Writes the artifact tree itself; the report is the stdout payload and
/// warning lines ride `warnings` (the CLI prints them after the report).
pub fn export_core(trace: &str, turn: Option<u64>, output: Option<&str>, odps: bool) -> CliOutcome {
    let out_dir = match output {
        None => {
            return CliOutcome::fail(2, "missing --output DIR (refusing to write into the working directory)")
        }
        Some(dir) => dir,
    };

    let raw_lines: Vec<String>;
    let source: Vec<Event> = {
        let text = match fs::read_to_string(trace) {
            Ok(t) => t,
            Err(e) => return CliOutcome::fail(2, format!("cannot read `{trace}`: {e}")),
        };
        raw_lines = text
            .lines()
            .filter(|l| !l.trim().is_empty())
            .map(|l| l.to_string())
            .collect();
        match read_jsonl(&text) {
            Ok(t) => t,
            Err(e) => return CliOutcome::fail(2, format!("parse error in `{trace}`: {e}")),
        }
    };

    // Slice turn: explicit or the trace's last turn fact.
    if turn.is_none() && source.iter().all(|e| event_turn(e).is_none()) {
        return CliOutcome::fail(2, "trace carries no turn facts; pass --turn N");
    }
    let turn = turn.unwrap_or_else(|| {
        source
            .iter()
            .filter_map(event_turn)
            .max()
            .expect("checked above: at least one turn fact")
    });

    let snapshot = build_handoff_snapshot(&source, turn);
    let slice = handoff_prefix(&source, turn);

    if let Err(e) = fs::create_dir_all(out_dir) {
        return CliOutcome::fail(2, format!("cannot create output directory `{out_dir}`: {e}"));
    }

    let mut warnings: Vec<String> = Vec::new();

    // Trace slice — verbatim source lines when they align with the decoded
    // events (byte-faithful handoff); canonical re-encoding as fallback.
    let byte_faithful = raw_lines.len() == source.len();
    let trace_body: String = if byte_faithful {
        // The slice is a positional prefix of the source: keep the FIRST
        // kept_events raw lines, verbatim.
        raw_lines[..slice.len()].iter().map(|l| format!("{l}\n")).collect()
    } else {
        warnings.push("trace re-encoded to canonical lines (raw line/event count mismatch)".into());
        slice.iter().map(|e| format!("{}\n", to_line(e))).collect()
    };
    let raw_trace_name = format!("trace-{turn}.jsonl");
    let raw_path = format!("{out_dir}/{raw_trace_name}");
    if let Err(e) = fs::write(&raw_path, &trace_body) {
        return CliOutcome::fail(2, format!("cannot write `{raw_path}`: {e}"));
    }

    // Page-table snapshot (the projection state the memo ships at turn N).
    let page_table_name = format!("page-table-{turn}.json");
    let page_table_path = format!("{out_dir}/{page_table_name}");
    let page_table_body = format!(
        "{}\n",
        serde_json::to_string_pretty(&snapshot.projection).expect("projection is serializable")
    );
    if let Err(e) = fs::write(&page_table_path, &page_table_body) {
        return CliOutcome::fail(2, format!("cannot write `{page_table_path}`: {e}"));
    }

    // --odps: zstd compression of the trace.
    let (trace_name, compressed) = if odps {
        let zst_name = format!("trace-{turn}.jsonl.zst");
        let status = std::process::Command::new("zstd")
            .arg("-q")
            .arg("-f")
            .arg(&raw_trace_name)
            .arg("-o")
            .arg(&zst_name)
            .current_dir(out_dir)
            .status();
        match status {
            Ok(status) if status.success() => match fs::remove_file(&raw_path) {
                Ok(()) => (zst_name, true),
                Err(e) => {
                    warnings.push(format!("compressed the trace but could not remove the raw file: {e}"));
                    (raw_trace_name.clone(), false)
                }
            },
            _ => {
                warnings.push("compression fallback: `zstd` not found/failed; keeping the uncompressed trace".into());
                (raw_trace_name.clone(), false)
            }
        }
    } else {
        (raw_trace_name.clone(), false)
    };

    let artifact_of = |path: &str, media_type: &str, payload: Option<&'static str>, compression: Option<&'static str>| Artifact {
        bytes: fs::metadata(format!("{out_dir}/{path}")).map(|m| m.len()).unwrap_or(0),
        path: path.to_string(),
        media_type: media_type.to_string(),
        payload,
        compression,
    };
    let mut artifacts: Vec<Artifact> = vec![
        artifact_of(
            &trace_name,
            if compressed { "application/zstd" } else { "application/x-ndjson" },
            Some("xCABI 0.1 JSONL (one RFC-0 event per line)"),
            if compressed { Some("zstd") } else { None },
        ),
        artifact_of(&page_table_name, "application/json", None, None),
    ];

    // Redaction scan over the data artifact texts (trace slice + page table).
    let scan_texts = [&trace_body, &page_table_body];
    let hits: Vec<_> = scan_texts.iter().flat_map(|t| scan_redaction(t)).collect();
    let redaction_hits = hits.iter().map(|h| h.hits).sum::<usize>();
    if redaction_hits > 0 {
        let detail = hits
            .iter()
            .filter(|h| h.hits > 0)
            .map(|h| format!("{}={}", h.pattern, h.hits))
            .collect::<Vec<_>>()
            .join(", ");
        warnings.push(format!(
            "redaction scan: {redaction_hits} credential-shaped pattern hits ({detail})"
        ));
    }
    if !snapshot.pin_lint.is_empty() {
        warnings.push(format!("pinLint: {} hits (see snapshot.pinLint)", snapshot.pin_lint.len()));
    }
    if !snapshot.replay_determinism() {
        warnings.push(format!(
            "replayDeterminism failed: {} divergences (manifest carries verification)",
            snapshot.replay.divergences.len()
        ));
    }
    if !snapshot.source_fidelity() {
        warnings.push("sourceFidelity failed: the slice is not a shared positional prefix of the source".into());
    }

    if odps {
        let session = session_header(&source);
        let manifest_name = "manifest.yaml";
        let manifest_text = manifest_yaml(
            &snapshot,
            &session,
            &artifacts,
            trace,
            &trace_name,
            compressed,
            redaction_hits,
            scan_texts.len(),
        );
        let manifest_path = format!("{out_dir}/{manifest_name}");
        if let Err(e) = fs::write(&manifest_path, &manifest_text) {
            return CliOutcome::fail(2, format!("cannot write `{manifest_path}`: {e}"));
        }
        artifacts.push(artifact_of(manifest_name, "text/yaml", None, None));

        let llms_name = "llms.txt";
        let llms_text = llms_txt(&snapshot, &trace_name, compressed, trace);
        let llms_path = format!("{out_dir}/{llms_name}");
        if let Err(e) = fs::write(&llms_path, &llms_text) {
            return CliOutcome::fail(2, format!("cannot write `{llms_path}`: {e}"));
        }
        artifacts.push(artifact_of(llms_name, "text/plain", None, None));

        // Checksums for every artifact except the checksums file itself.
        let mut names: Vec<String> = artifacts.iter().map(|a| a.path.clone()).collect();
        names.sort();
        let checksums_name = "checksums.sha256";
        let checksums_path = format!("{out_dir}/{checksums_name}");
        match std::process::Command::new("sha256sum")
            .args(&names)
            .current_dir(out_dir)
            .output()
        {
            Ok(out) if out.status.success() => {
                let text = String::from_utf8_lossy(&out.stdout).to_string();
                if text.lines().count() != names.len() {
                    warnings.push("checksums.sha256 not written: sha256sum printed unexpected output".into());
                } else if let Err(e) = fs::write(&checksums_path, &text) {
                    warnings.push(format!("checksums.sha256 not written: {e}"));
                } else {
                    artifacts.push(artifact_of(checksums_name, "text/plain", None, None));
                }
            }
            _ => warnings.push("checksums.sha256 not written: `sha256sum` not found/failed".into()),
        }
    }

    // Report (stdout).
    let report = json!({
        "command": "export",
        "trace": trace,
        "turn": turn,
        "output": out_dir,
        "odps": odps,
        "artifacts": artifacts.iter().map(|a| a.to_json()).collect::<Vec<_>>(),
        "dq": {
            "replayDeterminism": snapshot.replay_determinism(),
            "sourceFidelity": snapshot.source_fidelity(),
            "pinLintHits": snapshot.pin_lint.len(),
            "redactionHitCount": redaction_hits,
        },
        "snapshot": snapshot,
        "warnings": warnings.clone(),
    });
    let pretty = serde_json::to_string_pretty(&report).expect("report is serializable");
    let mut body = pretty;
    body.push('\n');

    let mut outcome = CliOutcome::empty();
    outcome.stdout = body;
    outcome.warnings = warnings;
    outcome
}

// ---------------------------------------------------------------------------
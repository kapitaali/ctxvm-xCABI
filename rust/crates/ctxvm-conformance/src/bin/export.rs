//! `ctxvm export` — the handoff snapshot builder CLI (UC1 §2–§3, T21).
//!
//! Usage:
//!   export <trace.jsonl> --turn N --output DIR        slice + page-table
//!   export <trace.jsonl> --turn N --output DIR --odps full ODPS-flavored
//!                                                     package (manifest.yaml,
//!                                                     llms.txt, checksums,
//!                                                     zstd-compressed trace)
//!   export <trace.jsonl> --output DIR                 slice at the last turn
//!   export --help
//!
//! Slice rule (pinned in `ctxvm-core::export`): keep events up to and
//! including the LAST event whose turn ≤ N; turn-less events before that cut
//! stay, trailing turn-less bookkeeping is excluded. The turn-N projection
//! only sees changes with effective turn ≤ N, so swept tail-flush facts are
//! inert — the page table stays honest and both memo verify commands work:
//! `replay trace-N.jsonl --turn N` (exit 0, divergences []) and
//! `diff <source> trace-N.jsonl` (extension relation, shared prefix matches).
//!
//! Exit:   0 = snapshot written (DQ failures do NOT change the exit — the
//!         manifest carries verification; warnings go to stderr) ·
//!         2 = usage/IO/parse error
//! Output: JSON report on stdout; artifacts under --output DIR. `--odps`
//! shells out to `zstd`/`sha256sum` when present and degrades with warnings.

use std::{env, fs, process::ExitCode};

use serde_json::json;

use ctxvm_codec::{read_jsonl, to_line, Event};
use ctxvm_core::event_turn;
use ctxvm_core::{build_handoff_snapshot, handoff_prefix, scan_redaction, HandoffSnapshot};

const USAGE: &str = "usage: export <trace.jsonl> [--turn N] [--output DIR] [--odps]";

fn fail(code: u8, message: &str) -> ExitCode {
    eprintln!("ctxvm export: {message}");
    ExitCode::from(code)
}

fn help() -> ExitCode {
    println!(
        "{USAGE}\n\n  --turn N           slice turn (default: the trace's last turn fact)\n\
         --output DIR       output directory, created if missing (required)\n\
         --odps             full package: manifest.yaml (ODPS 4.1-flavored, DQ checks,\n\
         KPIs), llms.txt, checksums.sha256, and a zstd-compressed trace\n\
         (`zstd`/`sha256sum` binaries required; falls back with a warning)\n\
         --help | -h        this usage\n\n\
         Exit: 0 snapshot written (DQ failures are warnings — the manifest\n\
         carries verification) · 2 usage/IO/parse error. Slice rule: events up\n\
         to the last event with turn ≤ N; turn-less bookkeeping before the cut\n\
         stays, trailing turn-less events are excluded."
    );
    ExitCode::SUCCESS
}

struct Args {
    trace: String,
    turn: Option<u64>,
    output: Option<String>,
    odps: bool,
}

fn parse_args() -> Result<Args, String> {
    let mut argv = env::args().skip(1);
    let (mut trace, mut turn, mut output, mut odps, mut help) = (None, None, None, false, false);
    while let Some(arg) = argv.next() {
        macro_rules! value_of {
            ($name:literal) => {
                match argv.next() {
                    Some(v) => v,
                    None => return Err(concat!($name, " requires a value").to_string()),
                }
            };
        }
        match arg.as_str() {
            "--help" | "-h" => help = true,
            "--odps" => odps = true,
            "--turn" => {
                let v = value_of!("--turn");
                turn = match v.parse() {
                    Ok(n) => Some(n),
                    Err(_) => return Err(format!("--turn: `{v}` is not a turn number")),
                };
            }
            "--output" => output = Some(value_of!("--output")),
            _ if arg.starts_with("--") => {
                let (name, val) = match arg.split_once('=') {
                    Some((name, v)) => (name.to_owned(), Some(v.to_owned())),
                    None => (arg.clone(), None),
                };
                match (name.as_str(), val) {
                    ("--turn", Some(v)) if !v.is_empty() => {
                        turn = match v.parse() {
                            Ok(n) => Some(n),
                            Err(_) => return Err(format!("--turn: `{v}` is not a turn number")),
                        };
                    }
                    ("--output", Some(v)) if !v.is_empty() => output = Some(v),
                    _ => return Err(format!("unknown flag `{name}` (try --help)")),
                }
            }
            _ if trace.is_none() => trace = Some(arg),
            _ => return Err(format!("unexpected second positional `{arg}`")),
        }
    }
    if help {
        // Sentinel consumed by the caller (help exits 0 through its own path).
        return Err("HELP".into());
    }
    let trace = trace.ok_or("missing trace argument")?;
    if output.is_none() {
        return Err("missing --output DIR (refusing to write into the working directory)".into());
    }
    Ok(Args { trace, turn, output, odps })
}

/// One file shipped by the snapshot.
struct Artifact {
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

fn main() -> ExitCode {
    run()
}

fn run() -> ExitCode {
    let args = match parse_args() {
        Err(e) if e == "HELP" => return help(),
        Err(e) => return fail(2, &e),
        Ok(a) => a,
    };

    let raw_lines: Vec<String>;
    let source: Vec<Event> = {
        let text = match fs::read_to_string(&args.trace) {
            Ok(t) => t,
            Err(e) => return fail(2, &format!("cannot read `{}`: {e}", args.trace)),
        };
        raw_lines = text
            .lines()
            .filter(|l| !l.trim().is_empty())
            .map(|l| l.to_string())
            .collect();
        match read_jsonl(&text) {
            Ok(t) => t,
            Err(e) => return fail(2, &format!("parse error in `{}`: {e}", args.trace)),
        }
    };

    // Slice turn: explicit or the trace's last turn fact.
    if args.turn.is_none() && source.iter().all(|e| event_turn(e).is_none()) {
        return fail(2, "trace carries no turn facts; pass --turn N");
    }
    let turn = args.turn.unwrap_or_else(|| {
        source
            .iter()
            .filter_map(event_turn)
            .max()
            .expect("checked above: at least one turn fact")
    });

    let snapshot = build_handoff_snapshot(&source, turn);
    let slice = handoff_prefix(&source, turn);

    let out_dir = args.output.expect("parse_args guarantees --output");
    if let Err(e) = fs::create_dir_all(&out_dir) {
        return fail(2, &format!("cannot create output directory `{out_dir}`: {e}"));
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
        return fail(2, &format!("cannot write `{raw_path}`: {e}"));
    }

    // Page-table snapshot (the projection state the memo ships at turn N).
    let page_table_name = format!("page-table-{turn}.json");
    let page_table_path = format!("{out_dir}/{page_table_name}");
    let page_table_body = format!(
        "{}\n",
        serde_json::to_string_pretty(&snapshot.projection).expect("projection is serializable")
    );
    if let Err(e) = fs::write(&page_table_path, &page_table_body) {
        return fail(2, &format!("cannot write `{page_table_path}`: {e}"));
    }

    // --odps: zstd compression of the trace.
    let (trace_name, compressed) = if args.odps {
        let zst_name = format!("trace-{turn}.jsonl.zst");
        let status = std::process::Command::new("zstd")
            .arg("-q")
            .arg("-f")
            .arg(&raw_trace_name)
            .arg("-o")
            .arg(&zst_name)
            .current_dir(&out_dir)
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

    if args.odps {
        let session = session_header(&source);
        let manifest_name = "manifest.yaml";
        let manifest_text = manifest_yaml(
            &snapshot,
            &session,
            &artifacts,
            &args.trace,
            &trace_name,
            compressed,
            redaction_hits,
            scan_texts.len(),
        );
        let manifest_path = format!("{out_dir}/{manifest_name}");
        if let Err(e) = fs::write(&manifest_path, &manifest_text) {
            return fail(2, &format!("cannot write `{manifest_path}`: {e}"));
        }
        artifacts.push(artifact_of(manifest_name, "text/yaml", None, None));

        let llms_name = "llms.txt";
        let llms_text = llms_txt(&snapshot, &trace_name, compressed, &args.trace);
        let llms_path = format!("{out_dir}/{llms_name}");
        if let Err(e) = fs::write(&llms_path, &llms_text) {
            return fail(2, &format!("cannot write `{llms_path}`: {e}"));
        }
        artifacts.push(artifact_of(llms_name, "text/plain", None, None));

        // Checksums for every artifact except the checksums file itself.
        let mut names: Vec<String> = artifacts.iter().map(|a| a.path.clone()).collect();
        names.sort();
        let checksums_name = "checksums.sha256";
        let checksums_path = format!("{out_dir}/{checksums_name}");
        match std::process::Command::new("sha256sum")
            .args(&names)
            .current_dir(&out_dir)
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
        "trace": args.trace,
        "turn": turn,
        "output": out_dir,
        "odps": args.odps,
        "artifacts": artifacts.iter().map(|a| a.to_json()).collect::<Vec<_>>(),
        "dq": {
            "replayDeterminism": snapshot.replay_determinism(),
            "sourceFidelity": snapshot.source_fidelity(),
            "pinLintHits": snapshot.pin_lint.len(),
            "redactionHitCount": redaction_hits,
        },
        "snapshot": snapshot,
        "warnings": warnings,
    });
    println!("{}", serde_json::to_string_pretty(&report).expect("report is serializable"));

    for warning in &warnings {
        eprintln!("warning: {warning}");
    }
    ExitCode::SUCCESS
}

//! `ctxvm profile` — forensic aggregation CLI (UC2 phases 2–3).
//!
//! Usage:
//!   profile <session.jsonl>                             whole-trace summary + page roster + tallies
//!   profile <session.jsonl> --event page.fault          fault rows (memory-safe row list)
//!   profile <session.jsonl> --event page.fault --source tool_recall
//!   profile <session.jsonl> --event turn.render --turns 2-4,9
//!   profile <session.jsonl> ... --output FILE           report JSON → FILE
//!   profile --help
//!
//! `--event <type>` filters event rows: `page.fault` → typed fault rows,
//! `page.evict` → eviction rows, any other vocabulary type → its raw tagged
//! events. `--source` narrows fault rows by taxonomy source (requires
//! `--event page.fault`). `--turns a-b,c-d` windows every turn-bearing row
//! family. The summary/pages/violations blocks are ALWAYS whole-trace — this is
//! a read-only aggregation, not a fact check: exit 0 = success, 2 = usage/IO/
//! parse; there is no divergence exit. Waste/touch semantics live in the metric
//! simulator, never here.
//!
//! Exit:   0 = success · 2 = usage/IO/parse error
//! Output: canonical JSON report on stdout, or the `--output` file.

use std::{collections::BTreeSet, env, fs, process::ExitCode};

use ctxvm_codec::{read_jsonl, Event, FaultSource};
use ctxvm_core::{profile, turn_windows, EvictRow, FaultRow};

const EVENT_TYPES: [&str; 9] = [
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

const SOURCES: [FaultSource; 4] = [
    FaultSource::ToolRecall,
    FaultSource::IdentifierScan,
    FaultSource::ExplicitApi,
    FaultSource::Semantic,
];

const SOURCES_STR: [&str; 4] = ["tool_recall", "identifier_scan", "explicit_api", "semantic"];

fn parse_source(s: &str) -> Option<FaultSource> {
    Some(SOURCES[SOURCES_STR.iter().position(|c| {
        c.eq_ignore_ascii_case(s) || c.replace('_', "").eq_ignore_ascii_case(&s.replace('_', ""))
    })?])
}

const USAGE: &str =
    "usage: profile <session.jsonl> [--event <type>]... [--turns a-b,c-d] [--source <fault-source>] [--output FILE]";

fn fail(code: u8, message: &str) -> ExitCode {
    eprintln!("ctxvm profile: {message}");
    ExitCode::from(code)
}

fn help() -> ExitCode {
    println!(
        "{USAGE}\n\n  --event <type>     filter rows by event type; `page.fault` prints typed fault\n\
         rows, `page.evict` prints eviction rows, any other vocabulary type prints\n\
         its raw tagged events ({}; repeatable)\n\
         --turns <spec>     window row families to these turns, `a-b` ranges or single\n\
         turns, comma-separated (`2-4,9`); summary stays whole-trace\n\
         --source <src>     narrow fault rows ({:?}; requires --event page.fault)\n\
         --output FILE      write the report JSON to FILE (stdout stays silent)\n\
         --help | -h        this usage\n\n\
         Exit: 0 success · 2 usage/IO/parse error (no divergence exit — this is an\n\
         aggregation, not a fact check; run `replay` for the fact gate)",
        EVENT_TYPES.join(", "),
        SOURCES_STR
    );
    ExitCode::SUCCESS
}

struct Args {
    trace: String,
    events: Vec<String>,
    turns: Option<Vec<u64>>,
    source: Option<String>,
    output: Option<String>,
}

fn parse_args() -> Result<Args, String> {
    let mut argv = env::args().skip(1);
    let (mut trace, mut events, mut turns, mut source, mut output, mut help) =
        (None, Vec::new(), None, None, None, false);

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
            "--event" => {
                let v = value_of!("--event");
                if !EVENT_TYPES.contains(&v.as_str()) {
                    return Err(format!(
                        "--event: `{v}` is not a vocabulary type · valid: {}",
                        EVENT_TYPES.join(", ")
                    ));
                }
                events.push(v);
            }
            "--turns" => {
                let spec = value_of!("--turns");
                let expanded = turn_windows(&spec)?;
                turns = Some(expanded.into_iter().collect::<BTreeSet<_>>().into_iter().collect());
            }
            "--source" => {
                let v = value_of!("--source");
                let parsed = parse_source(&v);
                if let Some(_) = parsed {
                    source = Some(v);
                } else {
                    return Err(format!(
                        "--source: `{v}` is not a taxonomy source · valid: {:?}",
                        SOURCES_STR
                    ));
                }
            }
            "--output" => {
                output = Some(value_of!("--output"));
            }
            _ if arg.starts_with("--") => match arg.split_once('=') {
                Some(("--event", v)) if !v.is_empty() => events.push(v.to_owned()),
                Some(("--turns", v)) if !v.is_empty() => {
                    let expanded = turn_windows(v)?;
                    turns = Some(expanded.into_iter().collect::<BTreeSet<_>>().into_iter().collect());
                }
                Some(("--source", v)) => source = Some(v.to_owned()),
                Some(("--output", v)) if !v.is_empty() => output = Some(v.to_owned()),
                Some((name, _)) => {
                    if matches!(name, "--event" | "--turns" | "--source" | "--output") {
                        return Err(format!("{name} requires a value"));
                    }
                    return Err(format!("unknown flag `{name}` (try --help)"));
                }
                None => return Err(format!("unknown flag `{arg}` (try --help)")),
            },
            _ if trace.is_none() => trace = Some(arg),
            _ => return Err(format!("unexpected second positional `{arg}`")),
        }
    }
    if help {
        return Err("HELP".into());
    }
    Ok(Args {
        trace: trace.ok_or("missing trace argument")?,
        events,
        turns,
        source,
        output,
    })
}

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

fn run() -> ExitCode {
    let args = match parse_args() {
        Err(e) if e == "HELP" => return help(),
        Err(e) => return fail(2, &e),
        Ok(a) => a,
    };

    if args.source.is_some() {
        if !args.events.iter().any(|e| e == "page.fault") {
            return fail(2, "--source requires --event page.fault");
        }
        if args.events.iter().any(|e| e.as_str() != "page.fault") {
            return fail(
                2,
                "--source applies only to fault rows (drop other --event selections)",
            );
        }
    }

    let src = match fs::read_to_string(&args.trace) {
        Err(e) => return fail(2, &format!("cannot read `{}`: {e}", args.trace)),
        Ok(s) => s,
    };
    let trace = match read_jsonl(&src) {
        Err(e) => return fail(2, &format!("parse error: {e}")),
        Ok(t) => t,
    };

    let report = profile(&trace);

    let mut value = serde_json::json!({
        "events": report.summary.events,
        "summary": report.summary,
        "pages": report.pages,
        "turnTallies": report.turn_tallies,
        "violations": report.violations,
    });
    let obj = value.as_object_mut().expect("json! builds an object");

    let wants_faults = args.events.iter().any(|e| e == "page.fault");
    let wants_evictions = args.events.iter().any(|e| e == "page.evict");
    let wants_raw: Vec<&str> = args
        .events
        .iter()
        .filter(|e| e.as_str() != "page.fault" && e.as_str() != "page.evict")
        .map(String::as_str)
        .collect();

    if wants_faults {
        let wanted = args.source.as_ref().map(|s| parse_source(s).expect("validated at parse"));
        let rows: Vec<FaultRow> = report
            .faults
            .iter()
            .filter(|row| turn_passes(&args.turns, row.turn))
            .filter(|row| wanted.map_or(true, |w| row.source == w))
            .cloned()
            .collect();
        obj.insert("faults".into(), serde_json::to_value(&rows).expect("fault rows serialize"));
    }
    if wants_evictions {
        let rows: Vec<EvictRow> = report
            .evictions
            .iter()
            .filter(|row| turn_passes(&args.turns, row.turn))
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
            .filter(|event| turn_of(event).map_or(true, |t| turn_passes(&args.turns, t)))
            .map(|event| serde_json::to_value(event).expect("event serializes"))
            .collect();
        obj.insert("filteredEvents".into(), serde_json::Value::Array(rows));
    }

    let body = format!("{}\n", serde_json::to_string_pretty(&value).expect("Value serializable"));
    match args.output.as_deref() {
        Some(path) => match fs::write(path, body) {
            Ok(()) => ExitCode::SUCCESS,
            Err(e) => fail(2, &format!("cannot write `{path}`: {e}")),
        },
        None => {
            print!("{body}");
            ExitCode::SUCCESS
        }
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

fn main() -> ExitCode {
    run()
}

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
//!
//! Since UC1-B1 the run core lives in [`ctxvm_conformance::cli::profile_core`]
//! (the single serialization / exit-code site): this main is a thin shell and
//! ctxvm-py drives the same core (byte-identity contract — see cli.rs). The
//! raw `--turns` spec is passed through and parsed by the core (`turn_windows`)
//! so both drivers produce the identical spec error.

use std::{env, process::ExitCode};

use ctxvm_conformance::cli::{self, EVENT_TYPES, SOURCES_STR, parse_source};
use ctxvm_core::turn_windows;

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
    turns: Option<String>,
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
                // Parse-order parity (UC1-B1): like the pre-extraction bin,
                // `--turns` errors surface at parse in argv order. The shared
                // core re-validates with the same function for the typed
                // binding path — one truth (`turn_windows`), twice called.
                turn_windows(&spec)?;
                turns = Some(spec);
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
                    // Mirror the old argv contract (see the flag-form branch).
                    turn_windows(v)?;
                    turns = Some(v.to_owned());
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

fn main() -> ExitCode {
    let args = match parse_args() {
        Err(e) if e == "HELP" => return help(),
        Err(e) => return fail(2, &e),
        Ok(a) => a,
    };
    let outcome = cli::profile_core(
        &args.trace,
        &args.events,
        args.turns.as_deref(),
        args.source.as_deref(),
        args.output.as_deref(),
    );
    print!("{}", outcome.stdout);
    let stderr = outcome.stderr_text("profile");
    if !stderr.is_empty() {
        eprint!("{stderr}");
    }
    ExitCode::from(outcome.exit)
}

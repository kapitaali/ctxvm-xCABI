//! `ctxvm diff` — positional two-trace comparison (UC1 handoff cross-check).
//!
//! Usage:
//!   diff <a.jsonl> <b.jsonl> [--output FILE]    compare as decoded events
//!   diff --help
//!
//! Relations: `identical` · `a-extends-b` · `b-extends-a` (shared region
//! matches; the extension suffix carries everything new — the UC1 handoff
//! expectation) · `divergent` (first disagreement inside the shared length;
//! the report carries the event index plus page-level state delta:
//! declared-only sides, divergent-hash pairs, resident-token mismatches at
//! common turn.render facts).
//!
//! Exit:   0 = shared region matches (identical or extension) ·
//!         1 = divergent inside the shared length · 2 = usage/IO/parse
//! Output: canonical JSON report on stdout, or the `--output` file.

use std::{env, fs, process::ExitCode};

use ctxvm_codec::read_jsonl;
use ctxvm_core::diff_traces;

const USAGE: &str = "usage: diff <a.jsonl> <b.jsonl> [--output FILE]";

fn fail(code: u8, message: &str) -> ExitCode {
    eprintln!("ctxvm diff: {message}");
    ExitCode::from(code)
}

fn help() -> ExitCode {
    println!(
        "{USAGE}\n\n  --output FILE      write the report JSON to FILE (stdout stays silent)\n\
         --help | -h        this usage\n\n\
         Exit: 0 shared region matches (identical/extension) · 1 divergent ·\n\
         2 usage/IO/parse error. Events compare as decoded structs; byte-identity\n\
         of a single trace is `replay`'s fact gate, not this command."
    );
    ExitCode::SUCCESS
}

struct Args {
    a: String,
    b: String,
    output: Option<String>,
}

fn parse_args() -> Result<Args, String> {
    let mut argv = env::args().skip(1);
    let (mut a, mut b, mut output, mut help) = (None, None, None, false);
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
            "--output" => output = Some(value_of!("--output")),
            _ if arg.starts_with("--") => match arg.split_once('=') {
                Some(("--output", v)) if !v.is_empty() => output = Some(v.to_owned()),
                Some((name, _)) => {
                    if name == "--output" {
                        return Err("--output requires a value".into());
                    }
                    return Err(format!("unknown flag `{name}` (try --help)"));
                }
                None => return Err(format!("unknown flag `{arg}` (try --help)")),
            },
            _ if a.is_none() => a = Some(arg),
            _ if b.is_none() => b = Some(arg),
            _ => return Err(format!("unexpected third positional `{arg}`")),
        }
    }
    if help {
        return Err("HELP".into());
    }
    let a = a.ok_or("missing first trace argument")?;
    let b = b.ok_or("missing second trace argument")?;
    Ok(Args { a, b, output })
}

fn run() -> ExitCode {
    let args = match parse_args() {
        Err(e) if e == "HELP" => return help(),
        Err(e) => return fail(2, &e),
        Ok(a) => a,
    };

    let read = |path: &String| {
        fs::read_to_string(path)
            .map_err(|e| fail(2, &format!("cannot read `{path}`: {e}")))
            .and_then(|s| {
                read_jsonl(&s)
                    .map_err(|e| fail(2, &format!("parse error in `{path}`: {e}")))
            })
    };
    let trace_a = match read(&args.a) {
        Ok(t) => t,
        Err(code) => return code,
    };
    let trace_b = match read(&args.b) {
        Ok(t) => t,
        Err(code) => return code,
    };

    let report = diff_traces(&trace_a, &trace_b);
    let body = format!(
        "{}\n",
        serde_json::to_string_pretty(&report).expect("report is serializable")
    );
    match args.output.as_deref() {
        Some(path) => {
            if let Err(e) = fs::write(path, body) {
                return fail(2, &format!("cannot write `{path}`: {e}"));
            }
        }
        None => print!("{body}"),
    }
    match report.relation {
        ctxvm_core::TraceRelation::Divergent => fail(1, "traces diverge inside the shared length (see JSON above)"),
        _ => ExitCode::SUCCESS,
    }
}

fn main() -> ExitCode {
    run()
}

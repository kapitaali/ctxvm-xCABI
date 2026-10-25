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
//!
//! Since UC1-B1 the run core lives in [`ctxvm_conformance::cli::export_core`]
//! (the single serialization / exit-code site): this main is a thin shell and
//! ctxvm-py drives the same core (byte-identity contract — see cli.rs). The
//! `missing --output DIR` guard is enforced in both (same message).

use std::{env, process::ExitCode};

use ctxvm_conformance::cli;

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

fn main() -> ExitCode {
    let args = match parse_args() {
        Err(e) if e == "HELP" => return help(),
        Err(e) => return fail(2, &e),
        Ok(a) => a,
    };
    let outcome = cli::export_core(
        &args.trace,
        args.turn,
        args.output.as_deref(),
        args.odps,
    );
    print!("{}", outcome.stdout);
    let stderr = outcome.stderr_text("export");
    if !stderr.is_empty() {
        eprint!("{stderr}");
    }
    ExitCode::from(outcome.exit)
}

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
//!
//! Since UC1-B1 the run core lives in [`ctxvm_conformance::cli::diff_core`]
//! (the single serialization / exit-code site): this main is a thin shell and
//! ctxvm-py drives the same core (byte-identity contract — see cli.rs).

use std::{env, process::ExitCode};

use ctxvm_conformance::cli;

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

fn main() -> ExitCode {
    let args = match parse_args() {
        Err(e) if e == "HELP" => return help(),
        Err(e) => return fail(2, &e),
        Ok(a) => a,
    };
    let outcome = cli::diff_core(&args.a, &args.b, args.output.as_deref());
    print!("{}", outcome.stdout);
    let stderr = outcome.stderr_text("diff");
    if !stderr.is_empty() {
        eprint!("{stderr}");
    }
    ExitCode::from(outcome.exit)
}

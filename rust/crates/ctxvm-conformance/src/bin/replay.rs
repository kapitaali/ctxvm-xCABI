//! `ctxvm replay` — the exit-code-backed replay CLI (03-tracer-api-ts.md).
//!
//! Usage:
//!   replay <session.jsonl>                          full-trace fact check (default)
//!   replay <session.jsonl> --turn N                 point-in-time: facts at turn N +
//!                                                   the turn-N render projection
//!   replay <session.jsonl> --turn N --pin <ref>...  counterfactual force-resident
//!                                                   overlay on the turn projection
//!   replay <session.jsonl> ... --output FILE        write the report JSON to FILE
//!   replay --help
//!
//! `--pin <ref>` matches pages by exact logical_ref (the `page:<ref>` memo form is
//! accepted; one ref flips every declared content-hash variant that is stubbed at
//! that turn). The precision form `--pin (ref, hash)` matches one exact page
//! identity — one variant of a ref — for traces that declare several content
//! hashes under a single logical ref. The overlay answers the UC2 visibility
//! question — "could the model have SEEN this page at turn N?" — and never
//! rewrites facts, violations, or the divergence gate; visibility is not
//! correctness.
//!
//! Exit:   0 = divergences-free within the checked scope ·
//!         1 = divergences · 2 = usage/IO/parse error
//! Output: canonical JSON report on stdout, or the `--output` file. The classic
//! (no-flags) report keeps its exact shape and field order `{events, divergences,
//! violations}`; the `--turn` modes extend it (`turn`, `pins`, `forcedResident`,
//! `projection` keys are alphabetical in those shapes — acid note for consumers).
//!
//! Since UC1-B1 the run core lives in [`ctxvm_conformance::cli::replay_core`]
//! (the single serialization / exit-code site): this main is a thin shell and
//! ctxvm-py drives the same core (byte-identity contract — see cli.rs).

use std::{env, process::ExitCode};

use ctxvm_conformance::cli;

const USAGE: &str =
    "usage: replay <session.jsonl> [--turn N] [--pin <logical-ref>|(ref, hash)]... [--output FILE]";

fn fail(code: u8, message: &str) -> ExitCode {
    eprintln!("ctxvm replay: {message}");
    ExitCode::from(code)
}

fn help() -> ExitCode {
    println!(
        "{USAGE}\n\n  --turn N           point-in-time replay: divergence check restricted to\n\
         turn N, plus the derived turn-N render projection in the report\n\
         --pin <ref>        counterfactual force-resident overlay (requires --turn):\n\
         flip the stub slots of matching pages to Full in the projection;\n\
         repeatable; `page:<ref>` memo form accepted; the T20 precision\n\
         form `(ref, hash)` pins one exact content-hash variant instead\n\
         of every variant of the ref\n\
         --output FILE      write the report JSON to FILE (stdout stays silent)\n\
         --help | -h        this usage\n\n\
         Exit: 0 divergences-free within the checked scope · 1 divergences ·\n\
         2 usage/IO/parse error"
    );
    ExitCode::SUCCESS
}

struct Args {
    trace: String,
    turn: Option<u64>,
    pins: Vec<String>,
    output: Option<String>,
}

fn parse_args() -> Result<Args, String> {
    let mut argv = env::args().skip(1);
    let (mut trace, mut turn, mut pins, mut output, mut help) =
        (None, None, Vec::new(), None, false);

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
            "--turn" => {
                let v = value_of!("--turn");
                turn = match v.parse() {
                    Ok(n) => Some(n),
                    Err(_) => return Err(format!("--turn: `{v}` is not a turn number")),
                };
            }
            "--pin" => pins.push(value_of!("--pin")),
            "--output" => output = Some(value_of!("--output")),
            _ if arg.starts_with("--") => {
                match arg.split_once('=') {
                    Some(("--turn", v)) if !v.is_empty() => {
                        turn = match v.parse() {
                            Ok(n) => Some(n),
                            Err(_) => return Err(format!("--turn: `{v}` is not a turn number")),
                        };
                    }
                    Some(("--pin", v)) if !v.is_empty() => pins.push(v.to_owned()),
                    Some(("--output", v)) if !v.is_empty() => output = Some(v.to_owned()),
                    Some(("--turn", _)) | Some(("--pin", _)) | Some(("--output", _)) => {
                        let name = arg.split('=').next().unwrap_or(&arg);
                        return Err(format!("{name} requires a value"));
                    }
                    Some((name, _)) => return Err(format!("unknown flag `{name}` (try --help)")),
                    None => return Err(format!("unknown flag `{arg}` (try --help)")),
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
    Ok(Args { trace: trace.ok_or("missing trace argument")?, turn, pins, output })
}

fn main() -> ExitCode {
    let args = match parse_args() {
        Err(e) if e == "HELP" => return help(),
        Err(e) => return fail(2, &e),
        Ok(a) => a,
    };
    let outcome =
        cli::replay_core(&args.trace, args.turn, &args.pins, args.output.as_deref());
    print!("{}", outcome.stdout);
    let stderr = outcome.stderr_text("replay");
    if !stderr.is_empty() {
        eprint!("{stderr}");
    }
    ExitCode::from(outcome.exit)
}

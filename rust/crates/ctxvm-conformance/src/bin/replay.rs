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
//! that turn). The overlay answers the UC2 visibility question — "could the model
//! have SEEN this page at turn N?" — and never rewrites facts, violations, or the
//! divergence gate; visibility is not correctness.
//!
//! Exit:   0 = divergences-free within the checked scope ·
//!         1 = divergences · 2 = usage/IO/parse error
//! Output: canonical JSON report on stdout, or the `--output` file. The classic
//! (no-flags) report keeps its exact shape and field order `{events, divergences,
//! violations}`; the `--turn` modes extend it (`turn`, `pins`, `forcedResident`,
//! `projection` keys are alphabetical in those shapes — acid note for consumers).

use std::{collections::BTreeSet, env, fs, process::ExitCode};

use ctxvm_codec::{read_jsonl, Event};
use ctxvm_core::{derive_projection, replay, replay_turn, ReplayReport, TurnProjection};

const USAGE: &str =
    "usage: replay <session.jsonl> [--turn N] [--pin <logical-ref>]... [--output FILE]";

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
         repeatable; `page:<ref>` memo form accepted\n\
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

/// Memo-style `page:<ref>` form → bare logical_ref.
fn normalize_ref(pin: &str) -> &str {
    pin.strip_prefix("page:").unwrap_or(pin)
}

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

fn run() -> ExitCode {
    let args = match parse_args() {
        Err(e) if e == "HELP" => return help(),
        Err(e) => return fail(2, &e),
        Ok(a) => a,
    };

    let src = match fs::read_to_string(&args.trace) {
        Ok(s) => s,
        Err(e) => return fail(2, &format!("cannot read `{}`: {e}", args.trace)),
    };
    let trace = match read_jsonl(&src) {
        Err(e) => return fail(2, &format!("parse error: {e}")),
        Ok(t) => t,
    };

    if !args.pins.is_empty() && args.turn.is_none() {
        return fail(2, "--pin requires --turn (the overlay is per-turn)");
    }

    // Fact check: whole trace by default, only `turn`'s facts under --turn.
    let report: ReplayReport = match args.turn {
        Some(n) => replay_turn(&trace, n),
        None => replay(&trace),
    };
    let clean = report.divergences.is_empty();
    let divergence_note = match (clean, args.output.as_deref()) {
        (true, _) => None,
        (false, Some(_)) => Some("replay reported divergences (see report file)"),
        (false, None) => Some("replay reported divergences (see JSON above)"),
    };

    let body = match args.turn {
        None => serde_json::to_string_pretty(&report).expect("report is serializable"),
        Some(n) => {
            let unknown: Vec<&str> = args
                .pins
                .iter()
                .map(|p| normalize_ref(p))
                .filter(|r| !declared_refs(&trace).contains(&(*r).to_owned()))
                .collect();
            if !unknown.is_empty() {
                return fail(
                    2,
                    &format!(
                        "--pin: no declared page matches {} · declared refs: {}",
                        unknown
                            .iter()
                            .map(|u| format!("`{u}` "))
                            .collect::<String>()
                            .trim_end(),
                        declared_refs(&trace).join(", ")
                    ),
                );
            }
            let mut value = serde_json::json!({
                "turn": n,
                "divergences": report.divergences,
                "violations": report.violations,
                "events": report.events,
            });
            if !args.pins.is_empty() {
                let projection: TurnProjection = derive_projection(&trace, n);
                let (projection, forced) = projection
                    .with_forced_resident(
                        &args.pins.iter().map(|p| normalize_ref(p).to_owned()).collect(),
                    );
                let pins: Vec<&str> = args.pins.iter().map(|p| normalize_ref(p)).collect();
                let obj = value
                    .as_object_mut()
                    .expect("json! builds an object");
                obj.insert("pins".into(), serde_json::to_value(&pins).expect("refs serialize"));
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

    // Write/print the report; then interpret the exit code from the checked scope.
    match args.output.as_deref() {
        Some(path) => match fs::write(path, format!("{body}\n")) {
            Ok(()) => {}
            Err(e) => return fail(2, &format!("cannot write `{path}`: {e}")),
        },
        None => println!("{body}"),
    }
    match divergence_note {
        Some(note) => fail(1, note),
        None => ExitCode::SUCCESS,
    }
}

fn main() -> ExitCode {
    run()
}

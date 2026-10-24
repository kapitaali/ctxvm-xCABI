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

use std::{collections::BTreeSet, env, fs, process::ExitCode};

use ctxvm_codec::{read_jsonl, Event};
use ctxvm_core::{derive_projection, replay, replay_turn, Pin, ReplayReport, TurnProjection};

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
            let pin_specs = match build_pins(&args.pins) {
                Err(e) => return fail(2, &e),
                Ok(p) => p,
            };
            if let Err(e) = resolve_pins(&pin_specs, &trace) {
                return fail(2, &e);
            }
            let mut value = serde_json::json!({
                "turn": n,
                "divergences": report.divergences,
                "violations": report.violations,
                "events": report.events,
            });
            if !args.pins.is_empty() {
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

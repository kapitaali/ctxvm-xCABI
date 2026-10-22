//! `ctxvm replay` — the exit-code-backed replay CLI (03-tracer-api-ts.md).
//!
//! Usage:  replay <session.jsonl>
//! Exit:   0 = divergences-free (facts match decisions) · 1 = divergences ·
//!         2 = usage/IO/parse error
//! Output: canonical JSON report on stdout.

use std::{env, fs, process::ExitCode};

use ctxvm_codec::read_jsonl;
use ctxvm_core::{replay, ReplayReport};

fn fail(code: u8, message: &str) -> ExitCode {
    eprintln!("ctxvm replay: {message}");
    ExitCode::from(code)
}

fn run() -> ExitCode {
    let path = match env::args().nth(1) {
        Some(p) => p,
        None => {
            eprintln!("usage: replay <session.jsonl>");
            return fail(2, "missing trace argument");
        }
    };

    let src = match fs::read_to_string(&path) {
        Ok(s) => s,
        Err(e) => return fail(2, &format!("cannot read `{path}`: {e}")),
    };
    let trace = match read_jsonl(&src) {
        Ok(t) => t,
        Err(e) => return fail(2, &format!("parse error: {e}")),
    };

    let report: ReplayReport = replay(&trace);
    println!("{}", serde_json::to_string_pretty(&report).expect("report is serializable"));

    match report.divergences.is_empty() {
        true => ExitCode::SUCCESS,
        false => fail(1, "replay reported divergences (see JSON above)"),
    }
}

fn main() -> ExitCode {
    run()
}

//! `ctxvm stream` — group trace files by environment, in start order (W14 §R8).
//!
//! Usage:
//!   stream <dir|file>...        human table, grouped by environment
//!   stream <dir|file>... --json stable JSON (groups → sessions)
//!   stream --help
//!
//! Exit: 0 = read and grouped · 2 = usage, IO or parse error.
//!
//! Reads only events that already exist; the output is a pure function of the
//! inputs, ordered by (environment, started, file).

use std::{env, path::PathBuf, process::ExitCode};

use ctxvm_conformance::stream;

const USAGE: &str = "usage: stream <dir|file>... [--json]";

fn main() -> ExitCode {
    let mut paths: Vec<PathBuf> = Vec::new();
    let mut json = false;
    for arg in env::args().skip(1) {
        match arg.as_str() {
            "--json" => json = true,
            "--help" | "-h" => {
                println!("{USAGE}");
                return ExitCode::SUCCESS;
            }
            other if other.starts_with('-') => {
                eprintln!("ctxvm stream: unknown flag {other}\n{USAGE}");
                return ExitCode::from(2);
            }
            other => paths.push(PathBuf::from(other)),
        }
    }
    if paths.is_empty() {
        eprintln!("ctxvm stream: at least one directory or file is required\n{USAGE}");
        return ExitCode::from(2);
    }
    match stream::collect(&paths) {
        Ok(rows) => {
            print!("{}", if json { stream::render_json(&rows) } else { stream::render_text(&rows) });
            ExitCode::SUCCESS
        }
        Err(err) => {
            eprintln!("ctxvm stream: {err}");
            ExitCode::from(2)
        }
    }
}

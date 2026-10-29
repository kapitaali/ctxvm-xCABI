//! `ctxvm tokens` — count a text with a named tokenizer (W2's executable face).
//!
//! Prints exactly one JSON object — the marking law's shape:
//!
//! ```text
//! {"tokenizer":"apx4-char","tokens_source":"estimated","tokens":3}
//! ```
//!
//! Counts are `tokenizer`-scoped (02 §session.open: only comparable within one
//! tokenizer) and `tokens_source` is `estimated` here BY CONSTRUCTION — the CLI
//! estimates; provider-reported usage is the adapters' lane and stays
//! authoritative where the harness records it. The mark is never averaged away.
//!
//! Usage:
//!
//! ```text
//! tokens [--tokenizer <id>] [--file <path>] [TEXT...]
//! tokens [--tokenizer <id>] < text        (stdin when no --file and no TEXT)
//! ```
//!
//! `TEXT` pieces are joined with `\n` (multi-arg == one newline-joined doc).
//! Exactly one input source per run: `--file` XOR `TEXT` XOR stdin.
//! The tiktoken ids need a build with `--features tiktoken` (the error says
//! so); the default `apx4-char` baseline always resolves.

use std::io::Read;
use std::process::ExitCode;

use ctxvm_tokenizer::{for_id, is_known_id, known_ids, tokens_source, APX4_CHAR};

const USAGE: &str = "usage: tokens [--tokenizer <id>] [--file <path>] [TEXT...]\n       tokens [--tokenizer <id>] < text (stdin when no --file and no TEXT)\n\nids: apx4-char (default, ≈ chars/4 baseline) | tiktoken-o200k_base | tiktoken-cl100k_base (need --features tiktoken)";

fn fail(msg: &str) -> ExitCode {
    eprintln!("ctxvm tokens: {msg}");
    ExitCode::from(2)
}

fn main() -> ExitCode {
    let mut tokenizer = APX4_CHAR.to_string();
    let mut file: Option<String> = None;
    let mut pieces: Vec<String> = Vec::new();
    let mut argv = std::env::args().skip(1);
    while let Some(arg) = argv.next() {
        match arg.as_str() {
            "--tokenizer" => match argv.next() {
                Some(v) => tokenizer = v,
                None => return fail("--tokenizer needs a value"),
            },
            "--file" => match argv.next() {
                Some(v) => file = Some(v),
                None => return fail("--file needs a value"),
            },
            "--help" | "-h" => {
                println!("{USAGE}");
                return ExitCode::SUCCESS;
            }
            _ => pieces.push(arg),
        }
    }

    // Exactly one input source (the `--file` vs argv vs stdin law).
    let text = if let Some(path) = &file {
        if !pieces.is_empty() {
            return fail("give ONE input source: --file XOR TEXT pieces");
        }
        let mut buf = String::new();
        if let Err(err) = std::fs::File::open(path).and_then(|mut f| f.read_to_string(&mut buf)) {
            return fail(&format!("cannot read --file {path}: {err}"));
        }
        buf
    } else if !pieces.is_empty() {
        pieces.join("\n")
    } else {
        let mut buf = String::new();
        if std::io::stdin().read_to_string(&mut buf).is_err() {
            return fail("no input: pass TEXT, --file, or pipe stdin");
        }
        buf
    };

    if !is_known_id(&tokenizer) {
        let known = known_ids()
            .iter()
            .map(|id| format!("'{id}'"))
            .collect::<Vec<_>>()
            .join(", ");
        return fail(&format!(
            "unknown tokenizer id '{tokenizer}' (this build knows: {known}; tiktoken ids need a rebuild with --features tiktoken)"
        ));
    }
    // Unreachable for a known id, but the None arm stays loud (never substitute
    // another tokenizer's count — identity law).
    let Some(t) = for_id(&tokenizer) else {
        return fail(&format!("tokenizer '{tokenizer}' did not resolve"));
    };
    println!(
        "{}",
        serde_json::json!({
            "tokenizer": t.id(),
            "tokens_source": tokens_source::ESTIMATED,
            "tokens": t.count(&text),
        })
    );
    ExitCode::SUCCESS
}

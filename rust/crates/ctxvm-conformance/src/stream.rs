//! `ctxvm stream` — sessions grouped into environments (W14 §R8).
//!
//! W14 gave each trace an opaque `environmentId`. This module is what makes that
//! key worth carrying: it groups trace files by environment and orders them by
//! start time, so cross-session quantities become observable — how much a
//! repository's sessions repeat, and whether the same pages are re-declared in
//! session after session.
//!
//! It reads only events that already exist. No new wire field, no schema change,
//! and the output is a pure function of the inputs: grouping is a `BTreeMap` and
//! the final order is `(environment, started, file)`, so two runs over the same
//! files agree byte for byte. Known environments come first, `(unknown)` last.
//!
//! What it deliberately does NOT do: it does not call a page "waste" without a
//! touch fact. `pages` minus `rendered` counts declarations no `page.render` ever
//! showed — an upper bound on unused content, named as such.

use std::collections::{BTreeMap, BTreeSet};
use std::path::{Path, PathBuf};

use ctxvm_codec::{parse_line, Event};

/// One session, as the stream view sees it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SessionRow {
    /// `None` when the trace has no `environmentId` (absent, never guessed).
    pub environment: Option<String>,
    pub started: Option<String>,
    pub agent: String,
    pub model: String,
    pub turns: u64,
    /// Distinct declared pages (logicalRef + contentHash).
    pub pages: usize,
    /// Distinct pages a `page.render` actually showed.
    pub rendered: usize,
    pub faults: u64,
    /// Resident tokens at the last `turn.render`.
    pub resident_tokens: u64,
    pub file: String,
}

impl SessionRow {
    /// Declarations no render ever showed — an upper bound on unused content,
    /// not a measurement of waste.
    pub fn unrendered(&self) -> usize {
        self.pages.saturating_sub(self.rendered)
    }
}

fn read_events(path: &Path) -> Result<Vec<Event>, String> {
    let text = std::fs::read_to_string(path)
        .map_err(|e| format!("{}: {e}", path.display()))?;
    let mut events = Vec::new();
    for (idx, line) in text.lines().enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        events.push(parse_line(line).map_err(|e| format!("{}:{}: {e}", path.display(), idx + 1))?);
    }
    Ok(events)
}

/// Summarize one trace file.
pub fn session_row(path: &Path) -> Result<SessionRow, String> {
    let events = read_events(path)?;
    let mut row = SessionRow {
        environment: None,
        started: None,
        agent: String::new(),
        model: String::new(),
        turns: 0,
        pages: 0,
        rendered: 0,
        faults: 0,
        resident_tokens: 0,
        file: path.display().to_string(),
    };
    let mut declared: BTreeSet<(String, String)> = BTreeSet::new();
    let mut rendered: BTreeSet<(String, String)> = BTreeSet::new();
    let mut last_turn = 0u64;

    for event in &events {
        match event {
            Event::SessionOpen {
                agent_id,
                model,
                environment_id,
                ts,
                ..
            } => {
                row.agent = agent_id.clone();
                row.model = model.clone();
                row.environment = environment_id.clone();
                row.started = ts.clone();
            }
            Event::PageDeclare { page, .. } => {
                declared.insert((page.id.logical_ref.clone(), page.id.content_hash.clone()));
            }
            Event::PageRender { page, .. } => {
                rendered.insert((page.logical_ref.clone(), page.content_hash.clone()));
            }
            Event::PageFault { .. } => row.faults += 1,
            Event::TurnRender {
                turn,
                resident_tokens,
                ..
            } => {
                if *turn >= last_turn {
                    last_turn = *turn;
                    row.resident_tokens = *resident_tokens;
                }
            }
            _ => {}
        }
    }

    row.pages = declared.len();
    row.rendered = rendered.len();
    row.turns = last_turn;
    Ok(row)
}

/// Expand the given paths: a directory contributes its `*.jsonl` files, a file
/// contributes itself. Results are sorted so the caller's order never leaks into
/// the output.
pub fn expand(paths: &[PathBuf]) -> Result<Vec<PathBuf>, String> {
    let mut files = Vec::new();
    for path in paths {
        let meta = std::fs::metadata(path).map_err(|e| format!("{}: {e}", path.display()))?;
        if meta.is_dir() {
            let entries =
                std::fs::read_dir(path).map_err(|e| format!("{}: {e}", path.display()))?;
            for entry in entries {
                let entry = entry.map_err(|e| format!("{}: {e}", path.display()))?;
                let p = entry.path();
                if p.extension().and_then(|e| e.to_str()) == Some("jsonl") {
                    files.push(p);
                }
            }
        } else {
            files.push(path.clone());
        }
    }
    files.sort();
    Ok(files)
}

/// Read every trace under `paths` and order the rows by
/// `(environment, started, file)` — the stream order.
pub fn collect(paths: &[PathBuf]) -> Result<Vec<SessionRow>, String> {
    let files = expand(paths)?;
    let mut rows = Vec::with_capacity(files.len());
    for file in &files {
        rows.push(session_row(file)?);
    }
    // Known environments first, then `(unknown)`; inside a group, start time, then
    // file name. Sorting on the Option directly would put every unknown session at
    // the top, which reads as if absence were the primary fact.
    rows.sort_by(|a, b| {
        let key = |row: &SessionRow| {
            (
                row.environment.is_none(),
                row.environment.clone().unwrap_or_default(),
                row.started.clone().unwrap_or_default(),
                row.file.clone(),
            )
        };
        key(a).cmp(&key(b))
    });
    Ok(rows)
}

/// Group rows by environment, preserving the stream order inside a group.
pub fn groups(rows: &[SessionRow]) -> BTreeMap<String, Vec<SessionRow>> {
    let mut out: BTreeMap<String, Vec<SessionRow>> = BTreeMap::new();
    for row in rows {
        let key = row.environment.clone().unwrap_or_else(|| "(unknown)".to_string());
        out.entry(key).or_default().push(row.clone());
    }
    out
}

fn short_file(path: &str) -> String {
    Path::new(path)
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or(path)
        .to_string()
}

/// Human-readable table. One line per session, then a per-environment summary
/// that says how much the group repeats — the question the key exists for.
pub fn render_text(rows: &[SessionRow]) -> String {
    let mut out = String::new();
    for (environment, group) in groups(rows) {
        out.push_str(&format!("environment {environment}\n"));
        out.push_str("  started              turns  pages  shown  unshown  faults  residTokens  file\n");
        for row in &group {
            out.push_str(&format!(
                "  {:<19} {:>6} {:>6} {:>6} {:>8} {:>7} {:>12}  {}\n",
                row.started.as_deref().unwrap_or("-"),
                row.turns,
                row.pages,
                row.rendered,
                row.unrendered(),
                row.faults,
                row.resident_tokens,
                short_file(&row.file),
            ));
        }
        let turns: u64 = group.iter().map(|r| r.turns).sum();
        let pages: usize = group.iter().map(|r| r.pages).sum();
        let faults: u64 = group.iter().map(|r| r.faults).sum();
        let declared_twice = repeated_pages(&group);
        out.push_str(&format!(
            "  summary: {} session(s), {} turn(s), {} declaration(s), {} repeated across sessions, {} fault(s)\n\n",
            group.len(),
            turns,
            pages,
            declared_twice,
            faults,
        ));
    }
    out
}

/// Pages declared in more than one session of the group (by logicalRef+hash).
fn repeated_pages(group: &[SessionRow]) -> usize {
    let mut seen: BTreeMap<(String, String), usize> = BTreeMap::new();
    for row in group {
        if let Ok(events) = read_events(Path::new(&row.file)) {
            let mut local: BTreeSet<(String, String)> = BTreeSet::new();
            for event in &events {
                if let Event::PageDeclare { page, .. } = event {
                    local.insert((page.id.logical_ref.clone(), page.id.content_hash.clone()));
                }
            }
            for key in local {
                *seen.entry(key).or_insert(0) += 1;
            }
        }
    }
    seen.values().filter(|count| **count > 1).count()
}

/// Stable JSON: keys alphabetical, one object per session, groups as arrays.
pub fn render_json(rows: &[SessionRow]) -> String {
    let mut groups_out: Vec<String> = Vec::new();
    for (environment, group) in groups(rows) {
        let sessions: Vec<String> = group
            .iter()
            .map(|row| {
                format!(
                    "{{\"agent\":{},\"environment\":{},\"faults\":{},\"file\":{},\"model\":{},\"pages\":{},\"rendered\":{},\"residentTokens\":{},\"started\":{},\"turns\":{},\"unrendered\":{}}}",
                    json_str(&row.agent),
                    match &row.environment {
                        Some(env) => json_str(env),
                        None => "null".to_string(),
                    },
                    row.faults,
                    json_str(&row.file),
                    json_str(&row.model),
                    row.pages,
                    row.rendered,
                    row.resident_tokens,
                    match &row.started {
                        Some(ts) => json_str(ts),
                        None => "null".to_string(),
                    },
                    row.turns,
                    row.unrendered(),
                )
            })
            .collect();
        groups_out.push(format!(
            "{{\"environment\":{},\"sessions\":[{}]}}",
            json_str(&environment),
            sessions.join(",")
        ));
    }
    format!("{{\"groups\":[{}]}}", groups_out.join(","))
}

fn json_str(value: &str) -> String {
    let mut out = String::with_capacity(value.len() + 2);
    out.push('"');
    for ch in value.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use ctxvm_codec::{Event, PageId, PageKind, PageRef, FaultSource};

    fn write(path: &Path, events: &[Event]) {
        let text: String = events.iter().map(|e| ctxvm_codec::to_line(e) + "\n").collect();
        std::fs::write(path, text).unwrap();
    }

    fn session(env: Option<&str>, ts: &str) -> Event {
        Event::SessionOpen {
            agent_id: "agent".into(),
            model: "m".into(),
            provider: "p".into(),
            budget_tokens: 1000,
            tokenizer_id: "apx4-char".into(),
            schema_version: Some("0.1".into()),
            environment_id: env.map(str::to_string),
            ts: Some(ts.into()),
        }
    }

    fn declare(ref_: &str, hash: &str) -> Event {
        Event::PageDeclare {
            page: PageRef {
                id: PageId { logical_ref: ref_.into(), content_hash: hash.into() },
                kind: PageKind::ToolResult,
                tokens: 3,
            },
            turn: Some(0),
            latency_ms: None,
            tool_effect: None,
            ts: None,
        }
    }

    #[test]
    fn groups_two_sessions_of_one_environment_and_orders_by_start() {
        let dir = std::env::temp_dir().join(format!("ctxvm-stream-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let a = dir.join("b-later.jsonl");
        let b = dir.join("a-earlier.jsonl");
        let other = dir.join("c-other-env.jsonl");

        write(&a, &[session(Some("env-0a1b2c3d4e5f"), "2026-11-03T10:00:00.000Z"), declare("tool:x()", "h1")]);
        write(&b, &[session(Some("env-0a1b2c3d4e5f"), "2026-11-02T09:00:00.000Z"), declare("tool:x()", "h1")]);
        write(&other, &[session(None, "2026-11-03T11:00:00.000Z")]);

        let rows = collect(&[dir.clone()]).unwrap();
        // Stream order: environment id first, then start time.
        assert_eq!(rows.len(), 3);
        assert_eq!(rows[0].environment.as_deref(), Some("env-0a1b2c3d4e5f"));
        assert_eq!(rows[0].started.as_deref(), Some("2026-11-02T09:00:00.000Z"));
        assert_eq!(rows[1].started.as_deref(), Some("2026-11-03T10:00:00.000Z"));
        assert_eq!(rows[2].environment, None, "an absent id is not guessed");

        let grouped = groups(&rows);
        assert_eq!(grouped["env-0a1b2c3d4e5f"].len(), 2);
        assert_eq!(grouped["(unknown)"].len(), 1);

        let text = render_text(&rows);
        assert!(text.contains("environment env-0a1b2c3d4e5f"));
        assert!(text.contains("1 repeated across sessions"), "the same page in two sessions must be counted: {text}");

        let json = render_json(&rows);
        assert!(json.starts_with("{\"groups\":["));
        assert!(json.contains("\"environment\":\"(unknown)\""));
        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn counts_unrendered_declarations_as_an_upper_bound() {
        let dir = std::env::temp_dir().join(format!("ctxvm-stream2-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let file = dir.join("one.jsonl");
        write(
            &file,
            &[
                session(None, "2026-11-03T10:00:00.000Z"),
                declare("tool:a()", "h1"),
                declare("tool:b()", "h2"),
                Event::PageRender {
                    turn: 0,
                    page: PageId { logical_ref: "tool:a()".into(), content_hash: "h1".into() },
                    mode: ctxvm_codec::RenderMode::Full,
                    ts: None,
                },
                Event::PageFault {
                    turn: 1,
                    page: PageId { logical_ref: "tool:a()".into(), content_hash: "h1".into() },
                    source: FaultSource::ToolRecall,
                    latency_ms: None,
                    ts: None,
                },
            ],
        );
        let row = session_row(&file).unwrap();
        assert_eq!(row.pages, 2);
        assert_eq!(row.rendered, 1);
        assert_eq!(row.unrendered(), 1);
        assert_eq!(row.faults, 1);
        std::fs::remove_dir_all(&dir).ok();
    }
}

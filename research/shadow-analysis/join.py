#!/usr/bin/env python3
"""Offline join for ctxvm-shadow-selection/v1 records.

Implements reports/RR-SHADOW-JOIN-20261126.md. Reads private shadow records and
xCABI traces, but emits only hashed session/page ids, counts, denominators and
reason codes. No raw refs, bodies, arguments, prompts, answers or host paths.

Usage:
  python3 research/shadow-analysis/join.py \
    --shadow ~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl \
    --trace-dir ~/.local/state/ctxvm/traces \
    --out research/shadow-analysis/out
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

MIN_VALID_SESSIONS = 3
PIN_MIN_SESSIONS = 2
PIN_MIN_EVENTS = 3


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    candidate = here.parents[2]
    if (candidate / "packages/hermes/live/shadow_schema.py").exists():
        return candidate
    env = os.environ.get("CTXVM_REPO")
    if env:
        return Path(env).resolve()
    return Path.cwd()


def _load_validator(repo: Path):
    path = repo / "packages/hermes/live/shadow_schema.py"
    spec = importlib.util.spec_from_file_location("ctxvm_shadow_schema", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load shadow schema validator")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _session_key(session_id: str) -> str:
    return "sha256:" + _sha256_bytes(session_id.encode("utf-8"))[:16]


def _page_id(logical_ref: str, content_hash: str) -> str:
    return "sha256:" + _sha256_bytes((logical_ref + "|" + content_hash).encode("utf-8"))


def _event_page_id(row: Dict[str, Any]) -> Optional[str]:
    page = row.get("page")
    if not isinstance(page, dict):
        return None
    if row.get("type") == "page.declare":
        ident = page.get("id")
        if not isinstance(ident, dict):
            return None
        ref, digest = ident.get("logicalRef"), ident.get("contentHash")
    else:
        ref, digest = page.get("logicalRef"), page.get("contentHash")
    if not isinstance(ref, str) or not isinstance(digest, str):
        return None
    return _page_id(ref, digest)


def _parse_ts(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        text = value[:-1] + "+00:00" if value.endswith("Z") else value
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _version_tuple(value: Any) -> Optional[Tuple[int, int, int]]:
    if not isinstance(value, str):
        return None
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", value)
    return tuple(map(int, m.groups())) if m else None


def _is_later(event: Dict[str, Any], record: Dict[str, Any]) -> Optional[bool]:
    """True=later, False=not later, None=same-turn ambiguous."""
    eturn, rturn = event.get("turn"), record.get("turn")
    if not isinstance(eturn, int) or not isinstance(rturn, int):
        return None
    if eturn != rturn:
        return eturn > rturn
    ets, rts = _parse_ts(event.get("ts")), _parse_ts(record.get("ts"))
    if ets is None or rts is None:
        return None
    if ets == rts:
        return None
    return ets > rts


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def _mean(values: Iterable[float]) -> Optional[float]:
    vals = list(values)
    return sum(vals) / len(vals) if vals else None


def _summary(values: Iterable[float]) -> Optional[Dict[str, float]]:
    vals = list(values)
    if not vals:
        return None
    return {"mean": sum(vals) / len(vals), "min": min(vals), "max": max(vals)}


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception as exc:
                raise ValueError(f"invalid JSON at line {line_no}: {exc}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"non-object at line {line_no}")
            rows.append(obj)
    return rows


def _load_coverages(trace_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for path in sorted(trace_dir.glob("*.coverage.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        sid = (data.get("session") or {}).get("sessionID")
        if isinstance(sid, str) and sid:
            out[sid].append(data)
    return out


def _trace_rows(trace_dir: Path, coverage: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    name = coverage.get("traceFile")
    expected = coverage.get("traceDigest")
    if not isinstance(name, str) or not isinstance(expected, str):
        raise ValueError("missing traceFile or traceDigest")
    path = trace_dir / name
    if path.parent != trace_dir:
        raise ValueError("traceFile must be a basename inside trace-dir")
    raw = path.read_bytes()
    actual = _sha256_bytes(raw)
    if actual != expected:
        raise ValueError("trace digest mismatch")
    rows = _load_jsonl(path)
    return rows, actual


def _build_event_index(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], set[str], Dict[str, Dict[str, Any]]]:
    events: List[Dict[str, Any]] = []
    declared: set[str] = set()
    meta: Dict[str, Dict[str, Any]] = {}
    for seq, row in enumerate(rows):
        pid = _event_page_id(row)
        if pid is None:
            continue
        declared.add(pid)
        if row.get("type") == "page.declare":
            page = row.get("page") or {}
            meta[pid] = {"kind": page.get("kind") or "unknown", "tokens": page.get("tokens") or 0}
        events.append({
            "seq": seq,
            "page_id": pid,
            "type": row.get("type"),
            "source": row.get("source"),
            "mode": row.get("mode"),
            "turn": row.get("turn"),
            "ts": row.get("ts"),
        })
    return events, declared, meta


def _is_label_event(event: Dict[str, Any]) -> bool:
    if event.get("type") == "page.fault":
        return event.get("source") in ("tool_recall", "identifier_scan")
    if event.get("type") == "page.render":
        return event.get("mode") == "stub"
    return event.get("type") == "page.evict"


def _session_result(session_id: str, records: List[Dict[str, Any]], coverage: Dict[str, Any],
                    trace_dir: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return (public session summary, internal detail for pin aggregation)."""
    rows, trace_digest = _trace_rows(trace_dir, coverage)
    events, declared, page_meta = _build_event_index(rows)
    records = sorted(records, key=lambda r: r.get("call_index", -1))

    page_opps = 0
    unmatched_pages = 0
    later_tool = 0
    later_ident = 0
    never = 0
    ambiguous = 0
    ambiguous_opps = 0
    scope_violation = False
    pin_events: Counter[str] = Counter()
    pin_event_keys: Dict[str, set[int]] = defaultdict(set)
    pin_sessions: Dict[str, set[str]] = defaultdict(set)
    churn: List[float] = []
    pressure: List[float] = []
    floor_pressure: List[float] = []
    drop_share: List[float] = []
    drop_records = 0
    previous: Optional[set[str]] = None

    for rec in records:
        dropped_ids = {p["page_id"] for p in rec.get("dropped_pages", [])}
        if previous is not None:
            churn.append(_jaccard(previous, dropped_ids))
        previous = dropped_ids
        if dropped_ids:
            drop_records += 1
        budget = rec.get("budget_tokens") or 0
        resident = rec.get("resident_tokens") or 0
        floor = rec.get("floor_tokens") or 0
        dropped_tokens = rec.get("dropped_tokens") or 0
        if budget:
            pressure.append(resident / budget)
            floor_pressure.append(floor / budget)
        if resident:
            drop_share.append(dropped_tokens / resident)

        for page in rec.get("dropped_pages", []):
            pid = page["page_id"]
            if pid not in declared:
                unmatched_pages += 1
                continue
            page_opps += 1
            page_ambiguous = False
            matched_events = [e for e in events if e["page_id"] == pid and _is_label_event(e)]
            later = []
            for event in matched_events:
                order = _is_later(event, rec)
                if order is None:
                    ambiguous += 1
                    page_ambiguous = True
                elif order:
                    later.append(event)
            tool_events = [e for e in later if e["type"] == "page.fault" and e.get("source") == "tool_recall"]
            ident_events = [e for e in later if e["type"] == "page.fault" and e.get("source") == "identifier_scan"]
            stub_count = sum(1 for e in later if e["type"] == "page.render" and e.get("mode") == "stub")
            evict_count = sum(1 for e in later if e["type"] == "page.evict")
            if stub_count or evict_count:
                scope_violation = True
            if tool_events:
                later_tool += 1
                for event in tool_events:
                    if event["seq"] not in pin_event_keys[pid]:
                        pin_event_keys[pid].add(event["seq"])
                        pin_events[pid] += 1
                pin_sessions[pid].add(session_id)
            if ident_events:
                later_ident += 1
            if not later and page_ambiguous:
                ambiguous_opps += 1
            elif not later:
                never += 1

    public = {
        "session_key": _session_key(session_id),
        "selections": len(records),
        "dropped_records": drop_records,
        "dropped_pages": sum(len(r.get("dropped_pages", [])) for r in records),
        "page_opportunities": page_opps,
        "unmatched_page_ids": unmatched_pages,
        "later_tool_recall_opportunities": later_tool,
        "later_identifier_scan_opportunities": later_ident,
        "never_observed_opportunities": never,
        "ambiguous_opportunities": ambiguous_opps,
        "ambiguous_same_turn_events": ambiguous,
        "scope_violation": scope_violation,
        "trace_digest": trace_digest,
        "pressure": _summary(pressure),
        "floor_pressure": _summary(floor_pressure),
        "drop_share": _summary(drop_share),
        "selection_churn": _summary(churn),
    }
    internal = {"pin_events": pin_events, "pin_sessions": pin_sessions, "page_meta": page_meta,
                "pressure": pressure, "floor_pressure": floor_pressure,
                "drop_share": drop_share, "selection_churn": churn}
    return public, internal


def run(shadow_path: Path, trace_dir: Path, out_dir: Path, repo: Path) -> Dict[str, Any]:
    validator = _load_validator(repo)
    raw_shadow = shadow_path.read_bytes()
    rows = _load_jsonl(shadow_path)
    coverages = _load_coverages(trace_dir)

    by_session: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    exclusions: Dict[str, set[str]] = defaultdict(set)
    schema_invalid = 0
    for row in rows:
        try:
            validator.validate_record(row)
        except Exception:
            schema_invalid += 1
            sid = row.get("session_id")
            if isinstance(sid, str) and sid:
                exclusions[sid].add("schema_invalid")
            continue
        sid = row.get("session_id")
        if not isinstance(sid, str) or not sid:
            continue
        by_session[sid].append(row)

    valid: List[Tuple[str, List[Dict[str, Any]], Dict[str, Any]]] = []
    for sid, records in sorted(by_session.items()):
        if exclusions[sid]:
            continue
        matches = coverages.get(sid, [])
        if len(matches) != 1:
            exclusions[sid].add("coverage_missing" if not matches else "coverage_multiple")
            continue
        cov = matches[0]
        plugin = cov.get("plugin") or {}
        ver = _version_tuple(plugin.get("version"))
        if ver is None or ver < (0, 13, 37):
            exclusions[sid].add("version_too_old")
        if plugin.get("profile") != "w8-shadow":
            exclusions[sid].add("wrong_profile")
        if plugin.get("shadowSelection") is not True:
            exclusions[sid].add("shadow_disabled")
        if plugin.get("shadowWriteFailures") != 0:
            exclusions[sid].add("session_write_failures")
        if any(r.get("policy", {}).get("mode") != "fresh" for r in records):
            exclusions[sid].add("not_fresh")
        if any(r.get("policy_applied") is not False for r in records):
            exclusions[sid].add("policy_applied")
        if any(r.get("request_unchanged") is not True for r in records):
            exclusions[sid].add("request_changed")
        if exclusions[sid]:
            continue
        valid.append((sid, records, cov))

    session_summaries: List[Dict[str, Any]] = []
    pooled_pressure: List[float] = []
    pooled_floor_pressure: List[float] = []
    pooled_drop_share: List[float] = []
    pooled_churn: List[float] = []
    pin_events: Counter[str] = Counter()
    pin_sessions: Dict[str, set[str]] = defaultdict(set)
    page_meta: Dict[str, Dict[str, Any]] = {}
    for sid, records, cov in valid:
        try:
            summary, internal = _session_result(sid, records, cov, trace_dir)
        except Exception as exc:
            exclusions[sid].add("trace_or_join_error")
            continue
        if summary["scope_violation"]:
            exclusions[sid].add("unexpected_stub_or_evict")
            continue
        session_summaries.append(summary)
        pooled_pressure.extend(internal["pressure"])
        pooled_floor_pressure.extend(internal["floor_pressure"])
        pooled_drop_share.extend(internal["drop_share"])
        pooled_churn.extend(internal["selection_churn"])
        pin_events.update(internal["pin_events"])
        for pid, sessions in internal["pin_sessions"].items():
            pin_sessions[pid].update(sessions)
        page_meta.update(internal["page_meta"])

    # Recompute valid count after trace/join failures.
    valid_count = len(session_summaries)
    enough = valid_count >= MIN_VALID_SESSIONS
    # Ratios are descriptive-only and stay internal until the sufficiency gate passes.
    ratio_fields = ("pressure", "floor_pressure", "drop_share", "selection_churn")
    public_sessions = []
    for summary in session_summaries:
        public = dict(summary)
        if not enough:
            for field in ratio_fields:
                public.pop(field, None)
        public_sessions.append(public)

    result: Dict[str, Any] = {
        "schema": "ctxvm-shadow-join-result/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_sha256": _sha256_bytes(raw_shadow),
        "status": "OK" if enough else "INSUFFICIENT_DATA",
        "required_valid_sessions": MIN_VALID_SESSIONS,
        "valid_sessions": valid_count,
        "shadow_records": len(rows),
        "schema_invalid_records": schema_invalid,
        "sessions_seen": len({row.get("session_id") for row in rows if isinstance(row.get("session_id"), str)}),
        "excluded_sessions": [
            {"session_key": _session_key(sid), "reasons": sorted(reasons)}
            for sid, reasons in sorted(exclusions.items()) if reasons
        ],
        "sessions": public_sessions,
        "candidate_pins": [],
    }

    if enough:
        totals = Counter()
        for s in session_summaries:
            for key in ("selections", "dropped_records", "dropped_pages", "page_opportunities",
                        "unmatched_page_ids", "later_tool_recall_opportunities",
                        "later_identifier_scan_opportunities", "never_observed_opportunities",
                        "ambiguous_same_turn_events"):
                totals[key] += s[key]
        opp = totals["page_opportunities"]
        result["counts"] = dict(totals)
        result["metrics"] = {
            "would_drop_rate": totals["dropped_records"] / totals["selections"] if totals["selections"] else None,
            "later_tool_recall_rate": totals["later_tool_recall_opportunities"] / opp if opp else None,
            "later_identifier_scan_rate": totals["later_identifier_scan_opportunities"] / opp if opp else None,
            "never_observed_rate": totals["never_observed_opportunities"] / opp if opp else None,
            "pressure": _summary(pooled_pressure),
            "floor_pressure": _summary(pooled_floor_pressure),
            "drop_share": _summary(pooled_drop_share),
            "selection_churn": _summary(pooled_churn),
        }
        pins = []
        for pid, count in sorted(pin_events.items()):
            if len(pin_sessions[pid]) >= PIN_MIN_SESSIONS and count >= PIN_MIN_EVENTS:
                pins.append({"page_id": pid, "later_tool_recall_events": count,
                             "sessions": len(pin_sessions[pid]), "kind": page_meta.get(pid, {}).get("kind"),
                             "offline_only": True, "activation": "not_authorized"})
        result["candidate_pins"] = pins
    else:
        result["counts"] = {
            "selections": sum(s["selections"] for s in session_summaries),
            "dropped_records": sum(s["dropped_records"] for s in session_summaries),
            "dropped_pages": sum(s["dropped_pages"] for s in session_summaries),
            "page_opportunities": sum(s["page_opportunities"] for s in session_summaries),
            "later_tool_recall_opportunities": sum(s["later_tool_recall_opportunities"] for s in session_summaries),
            "later_identifier_scan_opportunities": sum(s["later_identifier_scan_opportunities"] for s in session_summaries),
            "never_observed_opportunities": sum(s["never_observed_opportunities"] for s in session_summaries),
        }
        result["metrics"] = None
        result["candidate_pin_status"] = "not_evaluated_insufficient_data"

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shadow", required=True, type=Path)
    parser.add_argument("--trace-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repo", type=Path, default=None)
    args = parser.parse_args(argv)
    repo = args.repo.resolve() if args.repo else _repo_root()
    result = run(args.shadow.resolve(), args.trace_dir.resolve(), args.out.resolve(), repo)
    print(json.dumps({
        "status": result["status"],
        "valid_sessions": result["valid_sessions"],
        "required_valid_sessions": result["required_valid_sessions"],
        "shadow_records": result["shadow_records"],
        "counts": result["counts"],
        "candidate_pins": len(result["candidate_pins"]),
    }, sort_keys=True))
    return 0 if result["status"] == "OK" else 3


if __name__ == "__main__":
    sys.exit(main())

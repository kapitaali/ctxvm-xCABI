#!/usr/bin/env python3
"""Synthetic regression tests for research/shadow-analysis/join.py."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("shadow_join", HERE / "join.py")
join = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(join)
REPO = join._repo_root()


def pid(ref: str, digest: str) -> str:
    return "sha256:" + hashlib.sha256((ref + "|" + digest).encode()).hexdigest()


def record(sid: str, call: int, page_id: str, *, turn=0, ts="2026-11-26T19:00:00.000Z") -> dict:
    return {
        "schema": "ctxvm-shadow-selection/v1",
        "session_id": sid,
        "turn": turn,
        "call_index": call,
        "ts": ts,
        "policy": {"name": "keep-law", "version": "test", "mode": "fresh"},
        "budget_tokens": 24000,
        "resident_tokens": 33000,
        "floor_tokens": 17000,
        "dropped_tokens": 15000,
        "dropped_pages": [{"page_id": page_id, "tokens": 15000, "kind": "tool_result"}],
        "repositioned_pages": [],
        "selection_hash": "sha256:" + "a" * 64,
        "prefix_hash": "sha256:" + "b" * 64,
        "trigger": "overflow",
        "request_unchanged": True,
        "policy_applied": False,
    }


def declare(ref: str, digest: str, turn=0, ts="2026-11-26T18:59:00.000Z") -> dict:
    return {"type": "page.declare", "turn": turn, "ts": ts,
            "page": {"id": {"logicalRef": ref, "contentHash": digest},
                     "kind": "tool_result", "tokens": 15000}}


def fault(ref: str, digest: str, source="tool_recall", turn=0,
          ts="2026-11-26T19:00:01.000Z") -> dict:
    return {"type": "page.fault", "turn": turn, "ts": ts, "source": source,
            "page": {"logicalRef": ref, "contentHash": digest}}


def write_session(root: Path, sid: str, rows: list[dict], records: list[dict],
                  version="0.13.37", failures=0) -> None:
    trace_dir = root / "traces"
    trace_dir.mkdir(exist_ok=True)
    trace_name = sid + ".jsonl"
    raw = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows).encode()
    (trace_dir / trace_name).write_bytes(raw)
    coverage = {
        "session": {"sessionID": sid},
        "plugin": {"version": version, "profile": "w8-shadow",
                   "shadowSelection": True, "shadowWriteFailures": failures},
        "traceFile": trace_name,
        "traceDigest": hashlib.sha256(raw).hexdigest(),
    }
    (trace_dir / (sid + ".coverage.json")).write_text(json.dumps(coverage), encoding="utf-8")
    with (root / "selection.jsonl").open("a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")


class JoinTests(unittest.TestCase):
    def test_historical_page_id_not_latest_by_ref(self):
        ref = 'tool:read_file({"path":"same.md"})'
        v1, v2 = "sha256:11111111", "sha256:22222222"
        rows = [declare(ref, v1), declare(ref, v2)]
        events, declared, meta = join._build_event_index(rows)
        self.assertIn(pid(ref, v1), declared)
        self.assertIn(pid(ref, v2), declared)
        self.assertEqual(len(events), 2)
        self.assertEqual(meta[pid(ref, v1)]["kind"], "tool_result")

    def test_same_turn_requires_timestamp(self):
        rec = record("s", 0, pid("r", "sha256:1"))
        self.assertTrue(join._is_later(fault("r", "sha256:1", ts="2026-11-26T19:00:01.000Z"), rec))
        self.assertIsNone(join._is_later(fault("r", "sha256:1", ts="2026-11-26T19:00:00.000Z"), rec))
        self.assertFalse(join._is_later(fault("r", "sha256:1", ts="2026-11-26T18:59:59.000Z"), rec))
        no_ts = fault("r", "sha256:1")
        no_ts.pop("ts")
        self.assertIsNone(join._is_later(no_ts, rec))

    def test_insufficient_data_and_old_version_exclusion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ref = "tool:r"
            digest = "sha256:abcdef01"
            p = pid(ref, digest)
            write_session(root, "new", [declare(ref, digest)], [record("new", 0, p)])
            write_session(root, "old", [declare(ref, digest)], [record("old", 0, p)], version="0.13.36", failures=2)
            result = join.run(root / "selection.jsonl", root / "traces", root / "out", REPO)
            self.assertEqual(result["status"], "INSUFFICIENT_DATA")
            self.assertEqual(result["valid_sessions"], 1)
            self.assertIsNone(result["metrics"])
            self.assertEqual(result["candidate_pins"], [])
            for field in ("pressure", "floor_pressure", "drop_share", "selection_churn"):
                self.assertNotIn(field, result["sessions"][0])
            reasons = {tuple(e["reasons"]) for e in result["excluded_sessions"]}
            self.assertIn(("session_write_failures", "version_too_old"), reasons)

    def test_candidate_pin_requires_two_sessions_three_unique_events(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ref = "tool:r"
            digest = "sha256:abcdef01"
            p = pid(ref, digest)
            for sid in ("s1", "s2", "s3"):
                rows = [declare(ref, digest)]
                if sid == "s1":
                    rows.append(fault(ref, digest, ts="2026-11-26T19:00:01.000Z"))
                if sid == "s2":
                    rows.append(fault(ref, digest, ts="2026-11-26T19:00:01.000Z"))
                    rows.append(fault(ref, digest, ts="2026-11-26T19:00:02.000Z"))
                write_session(root, sid, rows, [record(sid, 0, p)])
            result = join.run(root / "selection.jsonl", root / "traces", root / "out", REPO)
            self.assertEqual(result["status"], "OK")
            self.assertEqual(result["valid_sessions"], 3)
            self.assertEqual(len(result["candidate_pins"]), 1)
            pin = result["candidate_pins"][0]
            self.assertEqual(pin["page_id"], p)
            self.assertEqual(pin["later_tool_recall_events"], 3)
            self.assertEqual(pin["sessions"], 2)
            self.assertIs(pin["offline_only"], True)
            self.assertEqual(pin["activation"], "not_authorized")

    def test_ambiguous_same_turn_is_not_never_observed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ref = "tool:r"
            digest = "sha256:abcdef01"
            p = pid(ref, digest)
            no_ts = fault(ref, digest)
            no_ts.pop("ts")
            write_session(root, "s1", [declare(ref, digest), no_ts], [record("s1", 0, p)])
            result = join.run(root / "selection.jsonl", root / "traces", root / "out", REPO)
            s = result["sessions"][0]
            self.assertEqual(s["ambiguous_opportunities"], 1)
            self.assertEqual(s["never_observed_opportunities"], 0)

    def test_output_contains_no_raw_ref_or_host_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ref = 'tool:read_file({"path":"secret.md"})'
            digest = "sha256:abcdef01"
            p = pid(ref, digest)
            write_session(root, "s1", [declare(ref, digest)], [record("s1", 0, p)])
            result = join.run(root / "selection.jsonl", root / "traces", root / "out", REPO)
            blob = json.dumps(result)
            self.assertNotIn(ref, blob)
            self.assertNotIn("secret.md", blob)
            self.assertNotIn(str(root), blob)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Synthetic adapter-aware coverage checker tests (stdlib only)."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CHECKER = Path(__file__).with_name("coverage_check.py")
REF = "tool:read({\"path\":\"a.ts\"})"
HASH = "sha256:12345678"
TURN = 1
TEXT = "exact stub\n  text"


def base_rows() -> list[dict]:
    return [
        {"type": "session.open", "agentId": "dsh", "model": "m", "provider": "p",
         "budgetTokens": 100, "tokenizerId": "apx4-char", "schemaVersion": "0.1"},
        {"type": "page.declare", "turn": 0,
         "page": {"id": {"logicalRef": REF, "contentHash": HASH}, "kind": "tool_result", "tokens": 10}},
        {"type": "page.evict", "turn": TURN,
         "page": {"logicalRef": REF, "contentHash": HASH}, "stubText": TEXT},
        {"type": "page.render", "turn": TURN,
         "page": {"logicalRef": REF, "contentHash": HASH}, "mode": "stub"},
        {"type": "turn.render", "turn": 0, "residentTokens": 10, "evictedTokens": 0},
        {"type": "turn.render", "turn": 1, "residentTokens": 0, "evictedTokens": 10},
    ]


def base_plugin() -> dict:
    return {
        "version": "0.0.1",
        "harness": "deepseek-harness",
        "adapter": "dsh",
        "capabilities": {"stubWire": 1},
        "stubDropped": "recoverable",
        "evictedTokens": 10,
        "stubCount": 1,
        "stubbedRefs": [{"ref": REF, "contentHash": HASH, "stubText": TEXT, "turn": TURN}],
    }


def manifest_for(rows: list[dict], plugin: dict) -> dict:
    declares = [row for row in rows if row.get("type") == "page.declare"]
    faults = [row for row in rows if row.get("type") == "page.fault"]
    turns = {row["turn"] for row in rows if row.get("type") == "turn.render"}
    pages = {(row["page"]["id"]["logicalRef"], row["page"]["id"]["contentHash"])
             for row in declares}
    return {
        "xcabiCoverage": "0.1",
        "traceFile": "trace.jsonl",
        "traceDigest": "",
        "session": {"sessionID": "s", "model": "m", "provider": "p"},
        "toolTable": {"readOnlyRegistered": [], "default": "MUTATING"},
        "instrumentation": {"ts": False, "toolEffect": False, "identifierScan": True},
        "plugin": plugin,
        "captures": {
            "turns": len(turns),
            "pages": len(pages),
            "declares": len(declares),
            "declaresByClass": {"READ_ONLY": 0, "MUTATING": 0},
            "faults": len(faults),
            "faultsBySource": {"tool_recall": 0, "identifier_scan": 0,
                               "explicit_api": 0, "semantic": 0},
        },
    }


class CoverageStubWireTests(unittest.TestCase):
    def run_checker(self, rows: list[dict], plugin: dict) -> subprocess.CompletedProcess[str]:
        raw = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                      for row in rows).encode("utf-8")
        manifest = manifest_for(rows, plugin)
        manifest["traceDigest"] = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory(prefix="dsh-coverage-test-") as directory:
            trace = Path(directory) / "trace.jsonl"
            sidecar = Path(directory) / "trace.jsonl.coverage.json"
            trace.write_bytes(raw)
            sidecar.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            return subprocess.run([sys.executable, str(CHECKER), str(trace), str(sidecar)],
                                  capture_output=True, text=True, check=False)

    def assert_rc(self, expected: int, rows: list[dict], plugin: dict) -> None:
        result = self.run_checker(rows, plugin)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def test_green_exact_pageid_turn_and_text(self) -> None:
        self.assert_rc(0, base_rows(), base_plugin())

    def test_missing_eviction(self) -> None:
        rows = [row for row in base_rows() if row["type"] != "page.evict"]
        self.assert_rc(1, rows, base_plugin())

    def test_missing_render(self) -> None:
        rows = [row for row in base_rows()
                if not (row["type"] == "page.render" and row.get("mode") == "stub")]
        self.assert_rc(1, rows, base_plugin())

    def test_wrong_eviction_turn(self) -> None:
        rows = copy.deepcopy(base_rows())
        next(row for row in rows if row["type"] == "page.evict")["turn"] = 2
        self.assert_rc(1, rows, base_plugin())

    def test_wrong_render_turn(self) -> None:
        rows = copy.deepcopy(base_rows())
        next(row for row in rows if row["type"] == "page.render")["turn"] = 2
        self.assert_rc(1, rows, base_plugin())

    def test_mismatched_text(self) -> None:
        rows = copy.deepcopy(base_rows())
        next(row for row in rows if row["type"] == "page.evict")["stubText"] = "different"
        self.assert_rc(1, rows, base_plugin())

    def test_mismatched_evicted_tokens(self) -> None:
        plugin = base_plugin()
        plugin["evictedTokens"] = 11
        self.assert_rc(1, base_rows(), plugin)

    def test_wrong_pageid(self) -> None:
        plugin = base_plugin()
        plugin["stubbedRefs"][0]["contentHash"] = "sha256:deadbeef"
        self.assert_rc(1, base_rows(), plugin)

    def test_duplicate_record_cannot_reuse_one_pair(self) -> None:
        plugin = base_plugin()
        plugin["stubCount"] = 2
        plugin["stubbedRefs"].append(copy.deepcopy(plugin["stubbedRefs"][0]))
        self.assert_rc(1, base_rows(), plugin)

    def test_malformed_capability(self) -> None:
        plugin = base_plugin()
        plugin["capabilities"]["stubWire"] = True
        self.assert_rc(1, base_rows(), plugin)

    def test_legacy_dsh_without_capability_is_exempt(self) -> None:
        plugin = base_plugin()
        plugin.pop("capabilities")
        self.assert_rc(0, base_rows(), plugin)

    def test_off_with_empty_records_passes(self) -> None:
        rows = [row for row in base_rows() if row["type"] not in ("page.evict", "page.render")]
        plugin = base_plugin()
        plugin.update({"stubDropped": "off", "evictedTokens": 0, "stubCount": 0, "stubbedRefs": []})
        self.assert_rc(0, rows, plugin)

    def test_non_dsh_adapter_keeps_hermes_semantics(self) -> None:
        plugin = base_plugin()
        plugin["adapter"] = "hermes"
        self.assert_rc(0, base_rows(), plugin)


if __name__ == "__main__":
    unittest.main()

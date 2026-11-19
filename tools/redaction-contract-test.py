#!/usr/bin/env python3
"""G4 redaction-sidecar contract — the gate step (RR-REDACTIMPL-20261119).

Asserts EVERY string and exit of the consumer contract (RR-REDACT-20261118 §4),
the writer's frozen-drop refusal (§5), and the scanner integration (§3), with
the three meta-assertions the card demands:
  1. the absence case prints "redaction: unknown" and never the word "none";
  2. no line contains "verified", and none asserts the artifact IS redacted;
  3. the contradiction case exits non-zero and names both the declared value
     and the observed raw-ref count.

Run: python3 tools/redaction-contract-test.py   (exit 0 = contract holds)
Fixtures: tools/fixtures/redaction/ (synthetic, dq-clean) + corpus/m1 (frozen).
"""

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCK = ROOT / "tools" / "redaction-block.py"
SCAN = ROOT / "tools" / "dq-secret-scan.py"
FX = ROOT / "tools" / "fixtures" / "redaction"
M1 = ROOT / "corpus" / "m1"

_spec = importlib.util.spec_from_file_location("dq_secret_scan", SCAN)
assert _spec is not None and _spec.loader is not None
dq = importlib.util.module_from_spec(_spec)
sys.modules["dq_secret_scan"] = dq
_spec.loader.exec_module(dq)


def run_tool(tool, *args):
    p = subprocess.run([sys.executable, str(tool), *args],
                       capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def consume(path):
    return run_tool(BLOCK, "consume", str(path))


def tmpdrop():
    d = Path(tempfile.mkdtemp(prefix="ctxvm-g4-"))
    (d / "trace.jsonl").write_text(
        '{"type":"page.declare","turn":0,"logicalRef":"tool:read({\\"path\\":\\"data/f1.txt\\"})","ts":"2026-11-19T09:00:00Z"}\n'
        '{"type":"page.declare","turn":1,"logicalRef":"tool:read({\\"path\\":\\"data/f2.txt\\"})","ts":"2026-11-19T09:00:01Z"}\n',
        encoding="utf-8")
    return d


def write_block(d, logical_ref="raw", stages=None):
    stages = stages or [{"stage": "capture", "policyId": "raw-passthrough",
                         "ruleSetVersion": "w8-dq-v1", "replacedFieldCount": 0}]
    (d / "redaction.json").write_text(json.dumps(
        {"stages": stages, "logicalRef": logical_ref,
         "channelsModelled": ["logicalRef"]}, indent=2), encoding="utf-8")


def m1_digests():
    return {str(p.relative_to(M1)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(M1.rglob("*")) if p.is_file()}


class ConsumerContractTests(unittest.TestCase):
    """§4: exact strings, exact exits."""

    def test_absent_is_unknown_exit0_and_never_none(self):
        rc, out, err = consume(FX / "fresh-noblock")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "redaction: unknown\n")
        self.assertEqual(err, "")
        self.assertIsNone(re.search(r"\bnone\b", out, re.I))

    def test_absent_on_every_frozen_corpus_drop(self):
        for drop in sorted((ROOT / "corpus").iterdir()):
            if drop.is_dir():
                rc, out, _ = consume(drop)
                self.assertEqual(rc, 0, drop.name)
                self.assertEqual(out, "redaction: unknown\n", drop.name)

    def test_declared_two_stages_exact_lines(self):
        rc, out, err = consume(FX / "two-stages")
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")
        self.assertEqual(out.splitlines(), [
            "redaction: declared",
            "stage=capture policy=raw-passthrough rules=w8-dq-v1 replaced=0",
            "stage=flush policy=example-flush-rules rules=w8-dq-v1 replaced=2",
            "logicalRef: raw",
            "channels modelled: logicalRef",
        ])

    def test_contradiction_exit1_names_value_and_count(self):
        rc, out, err = consume(FX / "contradiction")
        self.assertEqual(rc, 1)
        self.assertEqual(out,
            "redaction: inconsistent — declared keyed-hashed, 3 raw refs present\n")
        self.assertEqual(err, "")

    def test_dropped_declaration_with_survivors_is_inconsistent(self):
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        write_block(d, logical_ref="dropped")
        rc, out, _ = consume(d)
        self.assertEqual(rc, 1)
        self.assertEqual(out,
            "redaction: inconsistent — declared dropped, 2 raw refs present\n")

    def test_keyed_declaration_with_keyed_refs_is_declared(self):
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "trace.jsonl").write_text(
            '{"type":"page.declare","turn":0,"logicalRef":"tool:sha256:' + "ab" * 32 + '","ts":"2026-11-19T09:00:00Z"}\n',
            encoding="utf-8")
        write_block(d, logical_ref="keyed-hashed",
                    stages=[{"stage": "capture", "policyId": "example-keyed-rules",
                             "ruleSetVersion": "w8-dq-v1", "replacedFieldCount": 1}])
        rc, out, _ = consume(d)
        self.assertEqual(rc, 0)
        self.assertIn("redaction: declared", out)
        self.assertIn("logicalRef: keyed-hashed", out)

    def test_raw_declaration_with_raw_refs_is_declared(self):
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        write_block(d, logical_ref="raw")
        rc, out, _ = consume(d)
        self.assertEqual(rc, 0)
        self.assertIn("redaction: declared", out)

    def test_invalid_cases_exit2_with_reason(self):
        cases = {
            "broken json": "{not json",
            "not an object": "[]",
            "empty stage list": json.dumps({"stages": [], "logicalRef": "raw"}),
            "missing stage field": json.dumps({"stages": [{"stage": "capture"}],
                                               "logicalRef": "raw"}),
            "unknown stage": json.dumps({"stages": [{"stage": "render",
                "policyId": "p", "ruleSetVersion": "v", "replacedFieldCount": 0}],
                "logicalRef": "raw"}),
            "bad enum": json.dumps({"stages": [{"stage": "capture",
                "policyId": "p", "ruleSetVersion": "v", "replacedFieldCount": 0}],
                "logicalRef": "hashed"}),
            "missing enum": json.dumps({"stages": [{"stage": "capture",
                "policyId": "p", "ruleSetVersion": "v", "replacedFieldCount": 0}]}),
            "negative count": json.dumps({"stages": [{"stage": "capture",
                "policyId": "p", "ruleSetVersion": "v", "replacedFieldCount": -1}],
                "logicalRef": "raw"}),
            "float count": json.dumps({"stages": [{"stage": "capture",
                "policyId": "p", "ruleSetVersion": "v", "replacedFieldCount": 1.5}],
                "logicalRef": "raw"}),
        }
        for name, content in cases.items():
            with self.subTest(case=name):
                d = tmpdrop()
                self.addCleanup(shutil.rmtree, d, ignore_errors=True)
                (d / "redaction.json").write_text(content, encoding="utf-8")
                rc, out, _ = consume(d)
                self.assertEqual(rc, 2)
                self.assertTrue(out.startswith("redaction: invalid — "), out)
                self.assertGreater(len(out.split("— ", 1)[1].strip()), 0)

    def test_unreadable_trace_under_nonraw_declaration_is_invalid(self):
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "trace.jsonl").write_text("{bad json\n", encoding="utf-8")
        write_block(d, logical_ref="keyed-hashed")
        rc, out, _ = consume(d)
        self.assertEqual(rc, 2)
        self.assertIn("trace unreadable", out)

    def test_missing_drop_is_invalid(self):
        rc, out, _ = consume(ROOT / "tools" / "fixtures" / "no-such-drop")
        self.assertEqual(rc, 2)
        self.assertTrue(out.startswith("redaction: invalid — "))

    def test_no_output_says_verified_or_claims_redacted(self):
        """Meta-assertion 2: the strongest true sentence stays the lint's."""
        outputs = []
        for fx in ("fresh-noblock", "two-stages", "contradiction"):
            outputs.append(consume(FX / fx)[1])
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "redaction.json").write_text("{bad", encoding="utf-8")
        outputs.append(consume(d)[1])
        for out in outputs:
            self.assertNotIn("verified", out.lower())
            self.assertNotIn("is redacted", out.lower())
            self.assertIsNone(re.search(r"\bnone\b", out, re.I))


class WriterTests(unittest.TestCase):
    """§3/§5: the writer, its append law, and the frozen refusal."""

    def test_write_creates_sidecar_with_four_fields(self):
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        rc, out, err = run_tool(BLOCK, "write", str(d), "--stage", "capture")
        self.assertEqual(rc, 0, err)
        block = json.loads((d / "redaction.json").read_text())
        self.assertEqual(block["logicalRef"], "raw")
        self.assertEqual(block["channelsModelled"], ["logicalRef"])
        self.assertEqual(block["stages"], [{"stage": "capture",
            "policyId": "raw-passthrough", "ruleSetVersion": "w8-dq-v1",
            "replacedFieldCount": 0}])

    def test_append_second_stage_keeps_first_and_counts(self):
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        rc, _, err = run_tool(BLOCK, "write", str(d), "--stage", "capture")
        self.assertEqual(rc, 0, err)
        rc, _, err = run_tool(BLOCK, "write", str(d), "--stage", "flush",
                              "--policy-id", "example-flush-rules", "--replaced", "2")
        self.assertEqual(rc, 0, err)
        block = json.loads((d / "redaction.json").read_text())
        self.assertEqual([s["stage"] for s in block["stages"]], ["capture", "flush"])
        self.assertEqual([s["replacedFieldCount"] for s in block["stages"]], [0, 2])
        rc, out, _ = consume(d)
        self.assertEqual(rc, 0)
        self.assertIn("stage=flush policy=example-flush-rules rules=w8-dq-v1 replaced=2", out)

    def test_frozen_corpus_m1_refused_with_zero_byte_change(self):
        before = m1_digests()
        git_before = subprocess.run(["git", "status", "--short", "corpus/"],
                                    cwd=ROOT, capture_output=True, text=True).stdout
        rc, out, err = run_tool(BLOCK, "write", str(M1), "--stage", "capture")
        self.assertNotEqual(rc, 0)
        self.assertIn("frozen drop (law 5)", err)
        self.assertFalse((M1 / "redaction.json").exists())
        self.assertEqual(m1_digests(), before)
        git_after = subprocess.run(["git", "status", "--short", "corpus/"],
                                   cwd=ROOT, capture_output=True, text=True).stdout
        self.assertEqual(git_after, git_before)
        self.assertEqual(git_after, "")

    def test_invalid_declaration_refused_before_any_write(self):
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        rc, _, err = run_tool(BLOCK, "write", str(d), "--stage", "capture",
                              "--replaced", "-1")
        self.assertNotEqual(rc, 0)
        self.assertFalse((d / "redaction.json").exists())
        rc, _, err = run_tool(BLOCK, "write", str(d), "--stage", "capture",
                              "--logical-ref", "hashed")
        self.assertNotEqual(rc, 0)
        self.assertFalse((d / "redaction.json").exists())

    def test_non_directory_refused(self):
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        rc, _, err = run_tool(BLOCK, "write", str(d / "trace.jsonl"), "--stage", "capture")
        self.assertNotEqual(rc, 0)
        self.assertIn("not a drop directory", err)


class ScannerIntegrationTests(unittest.TestCase):
    """§3: the DQ lint emits the record; verdict + stamp mechanism unchanged."""

    def test_default_scan_writes_no_sidecar_and_keeps_wording(self):
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        rc, out, err = run_tool(SCAN, str(d))
        self.assertEqual(rc, 0, err)
        self.assertIn(f"dq-scan list {dq.SCAN_LIST_VERSION}  "
                      f"patterns={len(dq._PATTERNS)}  files=1", out)
        self.assertIn("verdict: SHIP-UNBLOCKED", out)
        identity = json.loads(out.split("dq_scan=", 1)[1].strip())
        self.assertEqual(identity["scanListVersion"], "w8-dq-v1")
        self.assertEqual(identity["scanToolSha256"],
                         hashlib.sha256(SCAN.read_bytes()).hexdigest())
        self.assertFalse((d / "redaction.json").exists())

    def test_scan_write_redaction_on_fresh_drop(self):
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        rc, out, err = run_tool(SCAN, str(d), "--write-redaction", "--stage", "capture")
        self.assertEqual(rc, 0, err)
        self.assertIn("verdict: SHIP-UNBLOCKED", out)
        block = json.loads((d / "redaction.json").read_text())
        self.assertEqual(block["stages"][0]["stage"], "capture")
        for field in ("policyId", "ruleSetVersion", "replacedFieldCount"):
            self.assertIn(field, block["stages"][0])
        rc, cout, _ = consume(d)
        self.assertEqual(rc, 0)
        self.assertIn("channels modelled: logicalRef", cout)
        # a re-scan classifies the sidecar too (idempotent, still clean)
        rc, out, err = run_tool(SCAN, str(d), "--write-redaction", "--stage", "flush")
        self.assertEqual(rc, 0, err)
        block = json.loads((d / "redaction.json").read_text())
        self.assertEqual([s["stage"] for s in block["stages"]], ["capture", "flush"])

    def test_cannot_ship_writes_no_sidecar(self):
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "trace.jsonl").write_text('{"k":"teppo@example.com"}\n', encoding="utf-8")
        rc, out, err = run_tool(SCAN, str(d), "--write-redaction", "--stage", "capture")
        self.assertEqual(rc, 1)
        self.assertIn("CANNOT-SHIP", out)
        self.assertFalse((d / "redaction.json").exists())

    def test_write_flag_usage_errors_exit2(self):
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        for args in ((str(d), "--write-redaction"),                     # no stage
                     (str(d), "--write-redaction", "--stage", "capture",
                      "--replaced", "-1"),
                     (str(d / "trace.jsonl"), "--write-redaction", "--stage", "capture"),
                     (str(d), str(d), "--write-redaction", "--stage", "capture")):
            rc, _, err = run_tool(SCAN, *args)
            self.assertEqual(rc, 2, args)
            self.assertIn("SCAN-SCOPE-ERROR", err)
        self.assertFalse((d / "redaction.json").exists())

    def test_scanner_frozen_refusal_leaves_m1_unchanged(self):
        before = m1_digests()
        rc, _, err = run_tool(SCAN, str(M1), "--write-redaction", "--stage", "capture")
        self.assertEqual(rc, 2)  # scope refusal (README/provenance) or frozen refusal
        self.assertFalse((M1 / "redaction.json").exists())
        self.assertEqual(m1_digests(), before)

    def test_sidecar_bytes_are_linted(self):
        d = tmpdrop()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        write_block(d)
        (d / "redaction.json").write_text(
            json.dumps({"stages": [{"stage": "capture", "policyId": "p",
                                    "ruleSetVersion": "v", "replacedFieldCount": 0}],
                        "logicalRef": "raw", "leak": "teppo@example.com"}),
            encoding="utf-8")
        rc, out, _ = run_tool(SCAN, str(d))
        self.assertEqual(rc, 1)
        self.assertIn("match email", out)


class KitWiringTests(unittest.TestCase):
    """The shared kit carries the consumer; the gate carries this script."""

    def test_verify_capture_has_the_consumer_step(self):
        kit = (ROOT / "tools" / "verify-capture.sh").read_text()
        self.assertIn("redaction-block.py", kit)
        self.assertIn("consume", kit)

    def test_gate_and_ci_mirror_carry_the_contract_step(self):
        gate = (ROOT / "tools" / "run-ci.sh").read_text()
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
        self.assertIn("redaction-contract-test.py", gate)
        self.assertIn("redaction-contract-test.py", ci)


if __name__ == "__main__":
    unittest.main(verbosity=2)
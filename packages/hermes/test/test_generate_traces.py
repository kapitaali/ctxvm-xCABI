"""W4b B2 — the hermes fixture generator can no longer green a dead surface.

Follows packages/hermes/OBSERVABILITY.md (F1: every m2/m3-era fixture was green
while the LIVE scan was dead — the fixtures only ever fed the block shape), W4b B1
(the parser fix; unit matrix in test_plugin.py), and RR-W5-20261030 (the live
facts: hermes v0.22.5 carries history `content` as PLAIN STRINGS, tool hooks fire
with `tool_name`, and a single-user-turn session is identifier_scan-dead by
construction). B2 is the owner-queued rider (RR-DECISIONS-20261030 rider 5, "B2
queued immediately after W5").

Guards (standing):
1. The generator emits a LIVE-shape session whose history is all plain strings;
   its trace must still show ≥1 identifier_scan fault — so a future parser
   regression of the exact B1 class (strings unread → scan dead) turns the
   suite red instead of greening.
2. The generator's emitter API is shape-auditable: make_live_shape_trace()
   returns the history it fed, and every message must be string-shaped.
3. The frozen m3-source fixtures are byte-identical to their corpus drop
   (packages/hermes/fixtures ↔ corpus/m3, checksums.sha256) — the no-rewrite
   law from the m-series freezes; and the generator refuses to overwrite
   them without force.

Run: python test/test_generate_traces.py   (or: cd packages/hermes && npm test)
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

_TEST_DIR = str(Path(__file__).resolve().parent)
for _p in (_TEST_DIR,):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import generate_traces  # noqa: E402

REPO = Path(__file__).resolve().parents[3]  # .../ctxvm-xCABI
FIXTURES = REPO / "packages" / "hermes" / "fixtures"
M3 = REPO / "corpus" / "m3"

# RR-T17-20261024.md:15 — the numbers the m3 drop shipped with.
M3_NUMBERS = {
    "hermes-echo-synthetic.jsonl": (20, 3, 3, 5),
    "hermes-thrash-synthetic.jsonl": (26, 5, 5, 5),
}


def fault_pairs(jsonl: str):
    """(source, turn) for every page.fault event, in order."""
    out = []
    for line in jsonl.splitlines():
        e = json.loads(line)
        if e["type"] == "page.fault":
            out.append([e["source"], e["turn"]])
    return out


class GenerateTests(unittest.TestCase):
    def test_live_shape_session_exercises_the_scan(self):
        """End-to-end: all-string history → the scan fires (B1-class death guard).

        Every history message the emitter feeds is a plain string, exactly like
        live Hermes v0.22.5 appends them — so if the plugin's transcript parser
        ever loses the string shape again, identifier_scan goes quiet HERE in
        the suite, not silently in the field again (m4/m7: faults 0).
        """
        jsonl, stats, history = generate_traces.make_live_shape_trace()
        self.assertGreaterEqual(
            sum(1 for e in jsonl.splitlines() if '"identifier_scan"' in e and "page.fault" in e),
            1,
            "identifier_scan must fire on the live-shape session",
        )
        # Mirror of the m3 echo structure through live shapes: same beats,
        # so the surface composition must match the frozen echo exactly.
        self.assertEqual(fault_pairs(jsonl), [["identifier_scan", 0], ["tool_recall", 0], ["identifier_scan", 1]])
        self.assertEqual(stats["pages"], 3)
        self.assertEqual(stats["turns"], 5)
        self.assertIn("page.declare", jsonl)

    def test_all_history_messages_are_plain_strings(self):
        """The live emitter's history is auditable: content must be a plain str.

        The emitter returns the history it fed; a regression to block-only
        (`[{"type": "text", ...}]`) lists — the exact blind spot that produced
        F1 — fails here at the generator, not in the field.
        """
        _jsonl, _stats, history = generate_traces.make_live_shape_trace()
        self.assertGreater(len(history), 0)
        for msg in history:
            self.assertIsInstance(msg, dict)
            self.assertIn(msg["role"], ("user", "assistant"))
            self.assertIsInstance(msg["content"], str, "live hermes sends content as a plain string")
            self.assertTrue(msg["content"], "empty content would hide the surface")

    def test_frozen_fixtures_stay_byte_identical_to_m3(self):
        """The m3 corpus drop checksummed these files — nobody regenerates them.

        Byte-parity packages/hermes/fixtures ↔ corpus/m3, and the event counts
        RR-T17 recorded (events, pages, faults, turns).
        """
        for name, (events, pages, faults, turns) in M3_NUMBERS.items():
            repo_bytes = (FIXTURES / name).read_bytes()
            m3_bytes = (M3 / name).read_bytes()
            self.assertEqual(repo_bytes, m3_bytes, f"{name} rewrote a frozen m3 source")
            trace_events = [json.loads(l) for l in repo_bytes.decode("utf-8").splitlines()]
            self.assertEqual(len(trace_events), events)
            self.assertEqual(sum(1 for e in trace_events if e["type"] == "page.declare"), pages)
            self.assertEqual(sum(1 for e in trace_events if e["type"] == "page.fault"), faults)
            self.assertEqual(sum(1 for e in trace_events if e["type"] == "turn.render"), turns)

    def test_frozen_write_guard_refuses_silent_overwrites(self):
        """_write_fixture refuses a frozen target; force overrides; fresh paths fine."""
        with tempfile.TemporaryDirectory() as td:
            frozen = Path(td) / "hermes-echo-synthetic.jsonl"
            frozen.write_text("seed\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                generate_traces._write_fixture(frozen, "new bytes")
            self.assertEqual(frozen.read_text(encoding="utf-8"), "seed\n")
            generate_traces._write_fixture(frozen, "forced bytes", force=True)
            self.assertEqual(frozen.read_text(encoding="utf-8"), "forced bytes")
            fresh = Path(td) / "fresh.jsonl"
            generate_traces._write_fixture(fresh, "fresh bytes")
            self.assertEqual(fresh.read_text(encoding="utf-8"), "fresh bytes")


if __name__ == "__main__":
    unittest.main()

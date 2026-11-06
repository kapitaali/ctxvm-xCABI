"""W8 redaction DQ scan tests — the pre-drop blocking gate's law
(`design/w8-capture-design.md` §10; tool: `tools/dq-secret-scan.py`, list
``w8-dq-v1``).

Run: cd packages/hermes && python -m pytest test/ -q

Pinned tool laws (these are the gate, so the tests are the second gate):
- every pattern family in the scan list fires on its specimen (and, where the
  specimen is crafted alone, ONLY on that family — isolation guards against a
  pattern being so loose it swallows the whole surface);
- exit 0 = zero matches (SHIP-UNBLOCKED), exit 1 = CANNOT-SHIP, exit 2 =
  scan-scope refusal (a non-drop-set file or a missing path; a directory walk
  that meets an unclassifiable file refuses rather than make a blind claim);
- matched BYTES are never printed (positions and pattern names only) — the DQ
  report itself must not leak what it found;
- the identity block (scanListVersion / scanToolSha256 / scanDate /
  filesScanned) rides every verdict and the SHA is the tool's own bytes.
"""

import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TOOL_PATH = _REPO_ROOT / "tools" / "dq-secret-scan.py"

_spec = importlib.util.spec_from_file_location("dq_secret_scan", _TOOL_PATH)
dq = importlib.util.module_from_spec(_spec)
sys.modules["dq_secret_scan"] = dq
_spec.loader.exec_module(dq)


def _run_main(argv):
    """dq.main() with captured stdout/stderr; returns (code, out, err)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = dq.main(argv)
    return code, out.getvalue(), err.getvalue()


def _tmpdir():
    return Path(tempfile.mkdtemp(prefix="ctxvm-dq-"))


def _write(path: Path, *lines: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _row(sample: str) -> str:
    """The specimen wrapped in the drop-set's real shape: one JSONL row."""
    return json.dumps({"k": sample}, ensure_ascii=False)


def _matches_for(report, pattern):
    return [m for m in report["matches"] if m["pattern"] == pattern]


class DQPatternFamilyTests(unittest.TestCase):
    """One specimen per scan-list family: it fires, and fires alone."""

    def _scan_sample(self, *lines):
        tmp = _tmpdir()
        try:
            f = _write(tmp / "sample.jsonl", *lines)
            code, human, _err = _run_main([str(f)])
            code_json, jout, _e = _run_main(["--json", str(f)])
            return code, code_json, json.loads(jout), human
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_each_family_fires_on_its_specimen(self):
        specimens = {
            "openai.sk": "sk-abcdefghijklmnopqrstuvwxyz123456",
            "aws.akia": "AKIAIOSFODNN7EXAMPLE",
            "github.ghp": "ghp_" + "a" * 36,
            "github.gho": "gho_" + "b" * 36,
            "github.pat": "pat_" + "c" * 40,
            "slack.xox": "xoxb-1234-abcdefghij",
            "pem.private_key": "-----BEGIN RSA PRIVATE KEY-----",
            "aws.headers": "AWSAccessKeyId=EXAMPLEACCESSKEYID",
            "generic.api_key": "api_key=Zm9vYmFyYmF6cXV1eA",
            "http.authorization": "Authorization: Basic cmVhbGx5cmVhbHB3",
            "http.bearer": "bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "email": "teppo@example.com",
            "path.abs_home": "/home/devp/notes",
            "ipv4.any": "10.0.0.42",
            "hostname.internal": "printserver.office.local",
        }
        for family, sample in specimens.items():
            with self.subTest(family=family):
                code, code_json, report, human = self._scan_sample(_row(sample))
                self.assertEqual(code, 1, f"{family} must fail the drop")
                self.assertEqual(code_json, 1)
                self.assertEqual(report["verdict"], "CANNOT-SHIP")
                hits = _matches_for(report, family)
                self.assertEqual(len(hits), 1, f"{family} fires exactly once")
                self.assertEqual(hits[0]["line"], 1)
                # isolation: the specimen is crafted to trip ONLY its family
                fired = {m["pattern"] for m in report["matches"]}
                self.assertEqual(fired, {family}, f"{family} must fire alone: {fired}")
                # the bytes stay dark
                self.assertNotIn(sample, human)

    def test_env_form_fires_on_line_start_key(self):
        """`FOO_SECRET=` at line start (the .env form, and the pretty-printed
        JSON key form a .meta.json actually produces); the JSONL-keyed variant
        co-fires here because the specimen line IS a JSON key line."""
        tmp = _tmpdir()
        try:
            f = _write(tmp / "env.meta.json",
                       "{",
                       ' "MY_SERVICE_SECRET": "abc123xyz"',
                       "}")
            code, jout, _e = _run_main(["--json", str(f)])
            report = json.loads(jout)
            self.assertEqual(code, 1)
            families = {m["pattern"] for m in report["matches"]}
            self.assertIn("env.secret_like", families)
            self.assertIn("json.secret_key", families)
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_json_key_form_fires_inside_a_single_line_row(self):
        """A secret-shaped KEY mid-line (the only way a one-line JSONL row can
        carry one) fires exactly the json variant — the env variant anchors at
        line start and must NOT swallow it."""
        tmp = _tmpdir()
        try:
            f = _write(tmp / "row.jsonl", '{"FOO_SECRET":"hunter2xyz"}')
            code, jout, _e = _run_main(["--json", str(f)])
            report = json.loads(jout)
            self.assertEqual(code, 1)
            self.assertEqual({m["pattern"] for m in report["matches"]},
                             {"json.secret_key"})
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_two_families_on_two_lines_report_distinct_lines(self):
        tmp = _tmpdir()
        try:
            f = _write(tmp / "multi.jsonl",
                       _row("sk-abcdefghijklmnopqrstuvwxyz123456"),
                       _row("teppo@example.com"))
            code, jout, _e = _run_main(["--json", str(f)])
            report = json.loads(jout)
            self.assertEqual(code, 1)
            self.assertEqual({m["pattern"] for m in report["matches"]},
                             {"openai.sk", "email"})
            lines = sorted(m["line"] for m in report["matches"])
            self.assertEqual(lines, [1, 2])
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


class DQVerdictTests(unittest.TestCase):
    """THE exit law (§11): 0 = zero matches, 1 = bytes burned, 2 = refuse."""

    def setUp(self):
        self.tmp = _tmpdir()
        self.addCleanup(lambda: __import__("shutil").rmtree(
            self.tmp, ignore_errors=True))

    def test_clean_drop_set_is_exit_zero_and_ship_unblocked(self):
        clean = _write(self.tmp / "clean.jsonl",
                       '{"type": "page.declare", "turn": 0, "residentTokens": 12}',
                       '{"type": "turn.render", "turn": 0, "residentTokens": 12}')
        meta = _write(self.tmp / "clean.meta.json",
                      '{"session": "demo", "harness": "hermes", "hooks": 7}')
        code, jout, _e = _run_main(["--json", str(clean), str(meta)])
        report = json.loads(jout)
        self.assertEqual(code, 0)
        self.assertEqual(report["verdict"], "SHIP-UNBLOCKED")
        self.assertEqual(report["matches"], [])
        self.assertEqual(report["filesScanned"], 2)

    def test_any_match_is_exit_one_and_cannot_ship(self):
        dirty = _write(self.tmp / "dirty.jsonl", _row("AKIAIOSFODNN7EXAMPLE"))
        code, jout, _e = _run_main(["--json", str(dirty)])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(jout)["verdict"], "CANNOT-SHIP")

    def test_explicit_non_drop_file_is_scope_refusal_exit_two(self):
        stray = _write(self.tmp / "notes.txt", "plain prose")
        code, out, err = _run_main([str(stray)])
        self.assertEqual(code, 2)
        self.assertIn("SCAN-SCOPE-ERROR", err)
        self.assertIn("notes.txt", err)
        self.assertNotIn("verdict", out)   # no claim was made

    def test_missing_path_is_scope_refusal_exit_two(self):
        code, _out, err = _run_main([str(self.tmp / "absent.jsonl")])
        self.assertEqual(code, 2)
        self.assertIn("SCAN-SCOPE-ERROR", err)

    def test_directory_walker_recurses_drop_set_shapes(self):
        deep = _write(self.tmp / "a" / "b" / "deep.jsonl",
                      _row("gho_" + "b" * 36))
        _write(self.tmp / "a" / "top.meta.json", '{"session": "demo"}')
        _write(self.tmp / "a" / "run.provenance", '{"tool": "hermes"}')
        code, jout, _e = _run_main(["--json", str(self.tmp)])
        report = json.loads(jout)
        self.assertEqual(code, 1)
        self.assertEqual(report["filesScanned"], 3)
        self.assertEqual(len(_matches_for(report, "github.gho")), 1)
        self.assertIn(str(deep), report["files"])

    def test_directory_walk_with_an_unclassifiable_file_refuses(self):
        """The strict scope law: the scan classifies EVERY byte in the set or
        refuses the claim — a bystander file in the directory makes the verdict
        impossible, so it is a scope error, never a silent skip."""
        _write(self.tmp / "good.jsonl", '{"type": "page.declare"}')
        _write(self.tmp / "stray.txt", "?")
        code, _out, err = _run_main([str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("stray.txt", err)

    def test_provenance_suffixes_are_in_scope(self):
        a = _write(self.tmp / "x.provenance", '{"case": "uc3"}')
        b = _write(self.tmp / "y.provenance.json", '{"case": "uc3"}')
        code, jout, _e = _run_main(["--json", str(a), str(b)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(jout)["filesScanned"], 2)

    def test_rerun_gives_the_same_positions(self):
        """§11 re-run-proof: the same bytes give the same verdict — same file,
        same pattern, same line (the burn decision never flips)."""
        dirty = _write(self.tmp / "again.jsonl",
                       _row("sk-abcdefghijklmnopqrstuvwxyz123456"))
        _r1 = json.loads(_run_main(["--json", str(dirty)])[1])
        _r2 = json.loads(_run_main(["--json", str(dirty)])[1])
        self.assertEqual(_r1["matches"], _r2["matches"])
        self.assertEqual(_r1["verdict"], "CANNOT-SHIP")
        self.assertEqual(_r2["verdict"], "CANNOT-SHIP")


class DQOutputHygieneTests(unittest.TestCase):
    """The report must not leak the bytes it found — and must pin its identity."""

    def setUp(self):
        self.tmp = _tmpdir()
        self.addCleanup(lambda: __import__("shutil").rmtree(
            self.tmp, ignore_errors=True))

    def test_human_mode_never_prints_matched_bytes(self):
        secret_token = "sk-abcdefghijklmnopqrstuvwxyz123456"
        bare_bearer = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9extralong"
        f = _write(self.tmp / "leaky.jsonl",
                   _row(secret_token), _row("bearer " + bare_bearer))
        code, out, err = _run_main([str(f)])
        self.assertEqual(code, 1)
        self.assertNotIn(secret_token, out)
        self.assertNotIn(bare_bearer, out)
        for fragment in ("abcde", "eyJhbGciOi", "123456"):
            self.assertNotIn(fragment, out)
        # pattern names + positions ARE printed (the DQ report needs them)
        self.assertIn("match openai.sk", out)
        self.assertIn("match http.bearer", out)
        self.assertIn("leaky.jsonl:1", out)
        self.assertIn("CANNOT-SHIP", out)
        self.assertEqual(err, "")

    def test_json_matches_carry_no_content_key(self):
        f = _write(self.tmp / "row.jsonl", _row("sk-abcdefghijklmnopqrstuvwxyz123456"))
        _code, jout, _e = _run_main(["--json", str(f)])
        for m in json.loads(jout)["matches"]:
            self.assertEqual(sorted(m.keys()), ["file", "line", "pattern"])

    def test_identity_block_rides_every_verdict(self):
        clean = _write(self.tmp / "c.jsonl", '{}')
        dirty = _write(self.tmp / "d.jsonl", _row("printserver.office.local"))
        for path, expect_code in ((clean, 0), (dirty, 1)):
            _code, jout, _e = _run_main(["--json", str(path)])
            report = json.loads(jout)
            self.assertEqual(report["scanListVersion"], "w8-dq-v1")
            self.assertRegex(report["scanDate"],
                             r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
            self.assertEqual(report["scanToolSha256"],
                             hashlib.sha256(_TOOL_PATH.read_bytes()).hexdigest())
            self.assertEqual(report["patternsChecked"], len(dq._PATTERNS))
        # human mode prints the same identity last
        _code, human, _e = _run_main([str(clean)])
        self.assertIn(f'scanToolSha256": "{hashlib.sha256(_TOOL_PATH.read_bytes()).hexdigest()}"',
                      human)


if __name__ == "__main__":
    unittest.main(verbosity=2)

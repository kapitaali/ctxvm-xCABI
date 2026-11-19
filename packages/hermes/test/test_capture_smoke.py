"""Capture smoke + budget provenance + retention tests (roadmap H16/H18/H17).

H16: one synthetic session through the REAL hook surface, flushed to disk — the
triple (trace + meta + coverage) must exist, tools/coverage_check.py must exit 0,
and the sidecar must carry budgetTokens + budgetSource. The sidecar fields were
new and unpinned by any gate step; this file is that pin (it rides the gated
hermes suite, so the gate derives its count).

H18: the budget tests in test_plugin.py pin `_budget_from_settings`; none of them
flushed. These drive a full flush and assert the sidecar actually carries the
resolved value AND its source (settings / env / default).

H17: retention with suffixed names was implemented and untested. The W21 suffix
is `-<8 hex of the session-id digest>` (NOT `-2`/`-3` — the roadmap's prose was
wrong about the mechanism; the code is the authority). These tests create
suffixed captures, force a prune, and assert the newest survives and the byte
budget rule holds, plus the collision law end-to-end.

Run: cd packages/hermes && python -m pytest test/ -q
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path

# Same self-contained path setup as test_plugin.py — no dependence on test order.
_HERMES_ROOT = str(Path(__file__).resolve().parents[1])
_HERMES_SRC = str(Path(__file__).resolve().parents[1] / "src")
for _p in (_HERMES_ROOT, _HERMES_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)
_LIVE_DIR = str(Path(__file__).resolve().parents[1] / "live")
if _LIVE_DIR not in sys.path:
    sys.path.insert(0, _LIVE_DIR)
if "agent.context_engine" not in sys.modules:
    # This stub must have the SAME structural shape as test_context_engine.py's
    # (its own install uses sys.modules.setdefault). A minimal stub here won the
    # race and broke super().get_status/on_session_reset in the engine law tests
    # when the whole suite ran. Keep the full host-ABC subset.
    import copy as _copy
    import types as _types
    from abc import ABC as _ABC, abstractmethod as _abstractmethod

    _agent_mod = _types.ModuleType("agent")
    _ce_mod = _types.ModuleType("agent.context_engine")

    class _HostContextEngine(_ABC):
        last_prompt_tokens = 0
        last_completion_tokens = 0
        last_total_tokens = 0
        threshold_tokens = 0
        context_length = 0
        compression_count = 0
        threshold_percent = 0.75
        protect_first_n = 3
        protect_last_n = 6
        emit_automatic_compaction_status = True

        @property
        @_abstractmethod
        def name(self) -> str:
            ...

        @_abstractmethod
        def update_from_response(self, usage):
            ...

        @_abstractmethod
        def should_compress(self, prompt_tokens=None):
            ...

        @_abstractmethod
        def compress(self, messages, current_tokens=None, focus_topic=None,
                     force=False, memory_context=""):
            ...

        def clone_for_agent(self):
            return _copy.deepcopy(self)

        def on_session_reset(self):
            self.last_prompt_tokens = 0
            self.compression_count = 0

        def get_status(self) -> dict:
            last_prompt = max(self.last_prompt_tokens, 0)
            return {"last_prompt_tokens": last_prompt,
                    "threshold_tokens": self.threshold_tokens,
                    "context_length": self.context_length,
                    "usage_percent": min(100, last_prompt / self.context_length * 100)
                    if self.context_length else 0,
                    "compression_count": self.compression_count}

        def prune_tool_results_only(self, messages, current_tokens=None):
            return messages, 0

        def select_context(self, request_messages, *, conversation_messages=None,
                           incoming_message=None, budget_tokens=0):
            return None

    _ce_mod.ContextEngine = _HostContextEngine
    _agent_mod.context_engine = _ce_mod
    sys.modules["agent"] = _agent_mod
    sys.modules["agent.context_engine"] = _ce_mod

# test_context_engine.py patches profile_policy.policy globally at import time to
# pin its arm. Save the REAL function by name before that can matter; our drives
# rebind it to the fake home for their own scope and restore on exit.
import profile_policy as _pp  # noqa: E402
_REAL_POLICY = _pp.policy

from live import _clear_env_for_tests, register  # noqa: E402
import live as live_mod  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[3]
_COVERAGE_CHECK = _REPO_ROOT / "tools" / "coverage_check.py"

_SETTINGS_CONFIG = """context:
  engine: compressor
plugins:
  entries:
    ctxvm-tracer:
      settings:
        budgetTokens: 24000
"""
_NO_BUDGET_CONFIG = """context:
  engine: compressor
"""


class _FakeCtx:
    """The host surface the adapter registers against; hooks kept callable."""

    def __init__(self):
        self.hooks = {}
        self.commands = {}
        self.cleanup = None

    def register_hook(self, name, cb):
        self.hooks[name] = cb
        return lambda: None

    def on_unload(self, cb):
        self.cleanup = cb
        return None

    def register_command(self, name, handler, description=""):
        self.commands[name] = handler
        return None

    def get_config(self, key):
        return None


def _fake_home(config_text):
    home = Path(tempfile.mkdtemp(prefix="ctxvm-smoke-home-"))
    (home / "config.yaml").write_text(config_text, encoding="utf-8")
    return home


def _drive_session(trace_dir, home, session_id, env_extra=None):
    """Register against a fake host and fire one real synthetic session."""
    env = {"CTXVM_TRACE_DIR": str(trace_dir), "HERMES_HOME": str(home)}
    with mock.patch.dict(os.environ, env, clear=False):
        os.environ.pop("CTXVM_TRACE_NAME", None)
        os.environ.pop("CTXVM_BUDGET_TOKENS", None)
        if env_extra:
            os.environ.update(env_extra)
        # The engine-law module pins policy() globally to a paged arm; rebind it
        # to the real resolver over OUR fake home so budget provenance is real.
        with mock.patch.object(_pp, "policy",
                               side_effect=lambda *a, **k: dict(
                                   _REAL_POLICY(home=Path(home)))):
            ctx = _FakeCtx()
            register(ctx)
            h = ctx.hooks
            h["on_session_start"](session_id=session_id, model="vendor/model-smoke",
                                  provider="vendor")
            h["pre_tool_call"](session_id=session_id, tool_name="read_file",
                               args={"path": "data/f1.txt"})
            h["post_tool_call"](session_id=session_id, tool_name="read_file",
                                args={"path": "data/f1.txt"}, status="ok",
                                result="alpha line one\nalpha line two\n")
            h["pre_llm_call"](session_id=session_id,
                              conversation_history=[
                                  {"role": "user", "content": "read data/f1.txt"}],
                              latencyMs=5)
            h["on_session_end"](session_id=session_id)
    return ctx


class _SmokeBase(unittest.TestCase):
    def setUp(self):
        _clear_env_for_tests()
        self._old_home = os.environ.get("HERMES_HOME")
        self.addCleanup(self._restore_home)
        self.addCleanup(_clear_env_for_tests)
        self.trace_dir = Path(tempfile.mkdtemp(prefix="ctxvm-smoke-traces-"))

    def _restore_home(self):
        if self._old_home is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self._old_home


class CaptureSmokeTests(_SmokeBase):
    """H16: the gated end-to-end capture smoke."""

    def test_synthetic_session_flushes_a_verifiable_triple(self):
        home = _fake_home(_SETTINGS_CONFIG)
        _drive_session(self.trace_dir, home, "smoke-s1")
        trace = self.trace_dir / "smoke-s1.jsonl"
        meta = self.trace_dir / "smoke-s1.meta.json"
        coverage = self.trace_dir / "smoke-s1.coverage.json"
        for path in (trace, meta, coverage):
            self.assertTrue(path.is_file(), f"missing flush artifact: {path.name}")
        rows = [json.loads(l) for l in trace.read_text().splitlines() if l.strip()]
        self.assertEqual(rows[0]["type"], "session.open")
        self.assertTrue(any(r["type"] == "page.declare" for r in rows))
        self.assertTrue(any(r["type"] == "turn.render" for r in rows))
        check = subprocess.run(
            [sys.executable, str(_COVERAGE_CHECK), str(trace), str(coverage)],
            capture_output=True, text=True)
        self.assertEqual(check.returncode, 0,
                         f"coverage_check failed:\n{check.stdout}\n{check.stderr}")
        coverage_block = json.loads(coverage.read_text())["plugin"]
        self.assertEqual(coverage_block["budgetTokens"], 24000)
        self.assertEqual(coverage_block["budgetSource"], "settings")


class FlushedBudgetProvenanceTests(_SmokeBase):
    """H18: a flushed sidecar carries the resolved budget AND its source."""

    def _flushed_plugin_block(self, home, env_extra=None, session_id="prov-s1"):
        _drive_session(self.trace_dir, home, session_id, env_extra=env_extra)
        # The resolution and its source belong to the COVERAGE sidecar (law 9),
        # not the kit-parity meta.json — both are written on every full flush.
        coverage = json.loads(
            (self.trace_dir / f"{session_id}.coverage.json").read_text())
        return coverage["plugin"]

    def test_flushed_sidecar_names_the_settings_source(self):
        block = self._flushed_plugin_block(_fake_home(_SETTINGS_CONFIG))
        self.assertEqual(block["budgetTokens"], 24000)
        self.assertEqual(block["budgetSource"], "settings")

    def test_flushed_sidecar_names_the_env_source(self):
        block = self._flushed_plugin_block(_fake_home(_NO_BUDGET_CONFIG),
                                           env_extra={"CTXVM_BUDGET_TOKENS": "12000"})
        self.assertEqual(block["budgetTokens"], 12000)
        self.assertEqual(block["budgetSource"], "env")

    def test_flushed_sidecar_names_the_default_source(self):
        block = self._flushed_plugin_block(_fake_home(_NO_BUDGET_CONFIG))
        self.assertEqual(block["budgetTokens"], 200000)
        self.assertEqual(block["budgetSource"], "default")


class RetentionSuffixedTests(unittest.TestCase):
    """H17: retention over W21-suffixed captures — newest survives, budget holds."""

    def setUp(self):
        _clear_env_for_tests()
        self.addCleanup(_clear_env_for_tests)
        self.dir = Path(tempfile.mkdtemp(prefix="ctxvm-retention-"))

    def _capture(self, name, age_s, size):
        """One complete capture triple with a controlled mtime and byte size."""
        now = time.time()
        stamp = now - age_s
        trace = self.dir / f"{name}.jsonl"
        trace.write_text("x" * size + "\n", encoding="utf-8")
        for suffix in (".meta.json", ".coverage.json"):
            (self.dir / f"{name}{suffix}").write_text("{}\n", encoding="utf-8")
        for path in (trace, self.dir / f"{name}.meta.json",
                     self.dir / f"{name}.coverage.json"):
            os.utime(path, (stamp, stamp))
        return trace

    def _names(self):
        return sorted(p.name for p in self.dir.glob("*.jsonl"))

    def test_newest_suffixed_capture_survives_a_forced_prune(self):
        self._capture("base", age_s=300, size=50)
        self._capture("base-a1b2c3d4", age_s=200, size=50)
        keep = self._capture("base-e5f6a7b8", age_s=100, size=50)
        with mock.patch.dict(os.environ, {"CTXVM_TRACE_RETAIN_MAX": "1"}):
            deleted = live_mod._prune_traces(str(self.dir), keep=keep.name)
        self.assertGreater(deleted, 0)
        self.assertEqual(self._names(), ["base-e5f6a7b8.jsonl"])

    def test_byte_budget_keeps_the_newest_that_fit(self):
        self._capture("old", age_s=300, size=300)
        self._capture("mid-a1b2c3d4", age_s=200, size=200)
        keep = self._capture("new-e5f6a7b8", age_s=100, size=100)
        with mock.patch.dict(os.environ, {"CTXVM_TRACE_RETAIN_BYTES": "350"}):
            live_mod._prune_traces(str(self.dir), keep=keep.name)
        survivors = self._names()
        self.assertEqual(survivors, ["mid-a1b2c3d4.jsonl", "new-e5f6a7b8.jsonl"])
        kept_bytes = sum((self.dir / n).stat().st_size for n in survivors)
        self.assertLessEqual(kept_bytes, 350)
        self.assertGreater(kept_bytes + 301, 350)  # the oldest no longer fits

    def test_keep_file_survives_even_when_it_alone_busts_the_budget(self):
        self._capture("old", age_s=300, size=10)
        keep = self._capture("new-a1b2c3d4", age_s=100, size=500)
        with mock.patch.dict(os.environ, {"CTXVM_TRACE_RETAIN_BYTES": "100"}):
            live_mod._prune_traces(str(self.dir), keep=keep.name)
        self.assertEqual(self._names(), ["new-a1b2c3d4.jsonl"])

    def test_pruned_suffixed_capture_takes_its_meta_and_coverage(self):
        keep = self._capture("new-e5f6a7b8", age_s=100, size=50)
        self._capture("old-a1b2c3d4", age_s=300, size=50)
        with mock.patch.dict(os.environ, {"CTXVM_TRACE_RETAIN_MAX": "1"}):
            live_mod._prune_traces(str(self.dir), keep=keep.name)
        self.assertFalse((self.dir / "old-a1b2c3d4.meta.json").exists())
        self.assertFalse((self.dir / "old-a1b2c3d4.coverage.json").exists())
        self.assertTrue((self.dir / "new-e5f6a7b8.meta.json").exists())
        self.assertTrue((self.dir / "new-e5f6a7b8.coverage.json").exists())

    def test_partial_snapshots_are_never_pruned(self):
        partial = self.dir / "stale.partial.jsonl"
        partial.write_text("{}\n", encoding="utf-8")
        old = time.time() - 10 * 86400
        os.utime(partial, (old, old))
        keep = self._capture("new", age_s=100, size=50)
        with mock.patch.dict(os.environ, {"CTXVM_TRACE_RETAIN_MAX": "1",
                                          "CTXVM_TRACE_RETAIN_DAYS": "1"}):
            live_mod._prune_traces(str(self.dir), keep=keep.name)
        self.assertTrue(partial.exists())


class CollisionSuffixLawTests(_SmokeBase):
    """W21 end-to-end: a reused trace name never replaces another session's bytes."""

    def test_second_session_gets_the_digest_suffix_and_first_bytes_stay(self):
        home = _fake_home(_NO_BUDGET_CONFIG)
        name_env = {"CTXVM_TRACE_NAME": "shared-name"}
        _drive_session(self.trace_dir, home, "collide-a", env_extra=name_env)
        first = self.trace_dir / "shared-name.jsonl"
        first_bytes = first.read_bytes()
        _drive_session(self.trace_dir, home, "collide-b", env_extra=name_env)
        suffix = hashlib.sha256(b"collide-b").hexdigest()[:8]
        second = self.trace_dir / f"shared-name-{suffix}.jsonl"
        self.assertTrue(second.is_file(), "second session must get the digest suffix")
        self.assertEqual(first.read_bytes(), first_bytes,
                         "the first session's bytes must not be replaced")
        self.assertEqual(json.loads(first.with_name("shared-name.meta.json")
                                    .read_text())["sessionID"], "collide-a")
        self.assertEqual(json.loads(second.with_name(
            f"shared-name-{suffix}.meta.json").read_text())["sessionID"], "collide-b")


if __name__ == "__main__":
    unittest.main(verbosity=2)
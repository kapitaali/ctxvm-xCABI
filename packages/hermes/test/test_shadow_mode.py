"""Shadow-mode tests — opt-in, content-free, no-perturbation, per-session."""
import json
import os
import stat
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

_HERMES = Path(__file__).resolve().parents[1]
for p in (str(_HERMES), str(_HERMES / "src"), str(_HERMES / "live")):
    if p not in sys.path:
        sys.path.insert(0, p)

import live
if "agent.context_engine" not in sys.modules:
    import copy
    import types
    from abc import ABC, abstractmethod
    agent = types.ModuleType("agent")
    ce_mod = types.ModuleType("agent.context_engine")
    class _Host(ABC):
        last_prompt_tokens = last_completion_tokens = last_total_tokens = 0
        threshold_tokens = context_length = compression_count = 0
        threshold_percent = 0.75
        protect_first_n = 3
        protect_last_n = 6
        emit_automatic_compaction_status = True
        @property
        @abstractmethod
        def name(self): ...
        @abstractmethod
        def update_from_response(self, usage): ...
        @abstractmethod
        def should_compress(self, prompt_tokens=None): ...
        @abstractmethod
        def compress(self, messages, current_tokens=None, focus_topic=None,
                     force=False, memory_context=""): ...
        def clone_for_agent(self): return copy.deepcopy(self)
        def on_session_reset(self): self.last_prompt_tokens = 0; self.compression_count = 0
        def get_status(self): return {}
        def select_context(self, *a, **k): return None
    ce_mod.ContextEngine = _Host
    agent.context_engine = ce_mod
    sys.modules["agent"] = agent
    sys.modules["agent.context_engine"] = ce_mod
import context_engine as ce
import importlib.util
_pp_spec = importlib.util.spec_from_file_location(
    "shadow_profile_policy", _HERMES / "live" / "profile_policy.py")
assert _pp_spec is not None and _pp_spec.loader is not None
profile_policy = importlib.util.module_from_spec(_pp_spec)
_pp_spec.loader.exec_module(profile_policy)
from plugin import Tracer, TraceInit
from shadow_schema import ShadowSchemaError, validate_record


def _tx(n=20, chars=20000):
    out = [{"role": "system", "content": "sys"}, {"role": "user", "content": "go"}]
    for i in range(1, n + 1):
        out.append({"role": "assistant", "content": "", "tool_calls": [{
            "id": f"c{i}", "type": "function",
            "function": {"name": "read_file", "arguments": json.dumps({"path": f"notes/f{i}.md"})}}]})
        out.append({"role": "tool", "content": ("f%d" % i) + "." * chars,
                    "tool_call_id": f"c{i}"})
    return out


class ShadowPolicyTests(unittest.TestCase):
    def test_profile_setting_is_read_and_defaults_false(self):
        d = Path(tempfile.mkdtemp(prefix="ctxvm-shadow-policy-"))
        cfg = d / "config.yaml"
        cfg.write_text("context:\n  engine: compressor\nplugins:\n  entries:\n"
                       "    ctxvm-tracer:\n      settings:\n        shadowSelection: true\n")
        self.assertTrue(profile_policy.read_yaml_subset(cfg)["shadowSelection"])
        cfg.write_text("context:\n  engine: compressor\n")
        pol = profile_policy.policy(d)
        self.assertFalse(pol["shadowSelection"])
        self.assertEqual(pol["shadowSelectionSource"], "default")

    def test_env_cannot_enable_shadow(self):
        e = ce.build_engine(v_budget=30000)
        with mock.patch.dict(os.environ, {"CTXVM_SHADOW_SELECTION": "true"}):
            self.assertFalse(e._shadow_selection)
            self.assertFalse(e._shadow_explicit)


class ShadowPlannerTests(unittest.TestCase):
    def test_control_shadow_plan_does_not_change_request_or_live_state(self):
        home = Path(tempfile.mkdtemp(prefix="ctxvm-shadow-home-"))
        pol = {"engine": "compressor", "budget": 30000, "budgetSource": "settings",
               "profile": "w8-shadow", "arm": "control", "home": str(home),
               "selectionMode": "fresh", "selectionModeSource": "default",
               "stubDropped": "off", "stubDroppedSource": "default",
               "shadowSelection": True, "shadowSelectionSource": "settings"}
        e = ce.build_engine(v_budget=30000)
        plans = []
        e.set_observer(lambda p: None, plans.append)
        tx = _tx()
        before = json.dumps(tx, sort_keys=True)
        pages_before = dict(e._pages)
        pins_before = list(e._pin_order)
        with mock.patch.object(ce, "_POLICY_MOD", types.SimpleNamespace(policy=lambda: dict(pol))):
            out = e.select_context(list(tx))
        self.assertIsNone(out)
        self.assertEqual(json.dumps(tx, sort_keys=True), before)
        self.assertEqual(e._pages, pages_before)
        self.assertEqual(e._pin_order, pins_before)
        self.assertEqual(len(plans), 1)
        self.assertTrue(plans[0]["shadow"])
        self.assertTrue(plans[0]["shadowSelection"])
        self.assertFalse(plans[0]["policyApplied"])
        self.assertTrue(plans[0]["requestUnchanged"])
        self.assertGreater(plans[0]["droppedCount"], 0)

    def test_shadow_off_and_on_return_the_same_control_result(self):
        home = Path(tempfile.mkdtemp(prefix="ctxvm-shadow-home-"))
        pol = {"engine": "compressor", "budget": 30000, "budgetSource": "settings",
               "profile": "w8-shadow", "arm": "control", "home": str(home),
               "selectionMode": "fresh", "selectionModeSource": "default",
               "stubDropped": "off", "stubDroppedSource": "default",
               "shadowSelection": True, "shadowSelectionSource": "settings"}
        results = []
        for shadow in (False, True):
            e = ce.build_engine(v_budget=30000, shadow_selection=shadow)
            with mock.patch.object(ce, "_POLICY_MOD", types.SimpleNamespace(policy=lambda: dict(pol))):
                results.append(e.select_context(list(_tx())))
        self.assertEqual(results[0], results[1])
        self.assertIsNone(results[0])


class ShadowRecordTests(unittest.TestCase):
    def setUp(self):
        live._clear_env_for_tests()
        self.home = Path(tempfile.mkdtemp(prefix="ctxvm-shadow-record-"))
        self.tr = Tracer(TraceInit(agent_id="hermes", model="m", provider="p", budget_tokens=30000))
        self.tr.page({"tool": "read_file", "args": {"path": "notes/f2.md"},
                      "content": "SECRET BODY", "toolEffect": "READ_ONLY"})
        live._state().setdefault("policy_by_session", {})["s1"] = {"home": str(self.home)}

    def test_record_is_hashed_private_and_content_free(self):
        payload = {"budgetTokens": 30000, "residentTokens": 50000, "floorTokens": 10000,
                   "droppedTokens": 20000, "droppedPages": [{"ids": ["notes/f2"],
                   "tokens": 20000, "contentHash": self.tr._declared[
                       self.tr.refs_for_identity_tokens([["notes/f2"]])[0]]["contentHash"]}],
                   "selectionMode": "fresh", "selectionHash": "sha256:" + "a" * 64,
                   "prefixHash": "sha256:" + "b" * 64, "trigger": None,
                   "policyApplied": False}
        live._write_shadow_record("s1", payload, self.tr)
        path = self.home / "ctxvm-shadow" / "selection.jsonl"
        self.assertTrue(path.exists())
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
        rec = json.loads(path.read_text())
        self.assertEqual(rec["schema"], "ctxvm-shadow-selection/v1")
        self.assertTrue(rec["dropped_pages"][0]["page_id"].startswith("sha256:"))
        text = path.read_text()
        for forbidden in ("SECRET BODY", "notes/f2.md", "tool:read_file", "arguments"):
            self.assertNotIn(forbidden, text)
        self.assertTrue(rec["request_unchanged"])

    def test_two_sessions_produce_disjoint_records(self):
        live._state().setdefault("policy_by_session", {})["s2"] = {"home": str(self.home)}
        payload = {"budgetTokens": 30000, "residentTokens": 50000, "floorTokens": 10000,
                   "droppedTokens": 20000, "droppedPages": [{"ids": ["notes/f2"],
                   "tokens": 20000, "contentHash": self.tr._declared[
                       self.tr.refs_for_identity_tokens([["notes/f2"]])[0]]["contentHash"]}],
                   "selectionMode": "fresh", "selectionHash": "sha256:" + "a" * 64,
                   "prefixHash": "sha256:" + "b" * 64, "trigger": None,
                   "policyApplied": False}
        live._write_shadow_record("s1", payload, self.tr)
        live._write_shadow_record("s2", payload, self.tr)
        rows = [json.loads(l) for l in (self.home / "ctxvm-shadow" / "selection.jsonl").read_text().splitlines()]
        self.assertEqual([r["session_id"] for r in rows], ["s1", "s2"])
        self.assertEqual([r["call_index"] for r in rows], [0, 0])

    def test_write_failure_is_visible_and_fail_open(self):
        with mock.patch.object(Path, "mkdir", side_effect=OSError("read-only")):
            live._write_shadow_record("s1", {}, self.tr)
        self.assertEqual(live._state()["shadowWriteFailures"], 1)

    def test_historical_page_id_uses_the_payload_hash_not_latest(self):
        ref = "file:same.md"
        self.tr.page({"ref": ref, "kind": "file", "content": "v1"})
        v1 = self.tr._declared[ref]["contentHash"]
        self.tr.page({"ref": ref, "kind": "file", "content": "v2"})
        v2 = self.tr._declared[ref]["contentHash"]
        payload = {"budgetTokens": 30000, "residentTokens": 50000, "floorTokens": 10000,
                   "droppedTokens": 20000, "droppedPages": [{"ids": ["same.md"],
                   "tokens": 20000, "contentHash": v1}], "selectionMode": "fresh",
                   "selectionHash": "sha256:" + "a" * 64,
                   "prefixHash": "sha256:" + "b" * 64, "trigger": None,
                   "policyApplied": False}
        live._write_shadow_record("s1", payload, self.tr)
        rec = json.loads((self.home / "ctxvm-shadow" / "selection.jsonl").read_text())
        expected = "sha256:" + __import__("hashlib").sha256((ref + "|" + v1).encode()).hexdigest()
        wrong = "sha256:" + __import__("hashlib").sha256((ref + "|" + v2).encode()).hexdigest()
        self.assertEqual(rec["dropped_pages"][0]["page_id"], expected)
        self.assertNotEqual(rec["dropped_pages"][0]["page_id"], wrong)

    def test_invalid_record_is_rejected_before_write(self):
        payload = {"budgetTokens": -1, "residentTokens": 1, "floorTokens": 0,
                   "droppedTokens": 2, "droppedPages": [], "selectionMode": "fresh",
                   "selectionHash": None, "prefixHash": None, "trigger": None,
                   "policyApplied": False}
        live._write_shadow_record("s1", payload, self.tr)
        self.assertFalse((self.home / "ctxvm-shadow" / "selection.jsonl").exists())
        self.assertEqual(live._state()["shadowWriteFailures"], 1)

    def test_repositioned_pages_are_populated_and_hashed(self):
        ref = self.tr.refs_for_identity_tokens([["notes/f2"]])[0]
        ch = self.tr._declared[ref]["contentHash"]
        payload = {"budgetTokens": 30000, "residentTokens": 50000, "floorTokens": 10000,
                   "droppedTokens": 0, "droppedPages": [],
                   "repositionedPages": [{"ids": ["notes/f2"], "tokens": 20000,
                                          "contentHash": ch}],
                   "selectionMode": "fresh", "selectionHash": "sha256:" + "a" * 64,
                   "prefixHash": "sha256:" + "b" * 64, "trigger": None,
                   "policyApplied": False}
        live._write_shadow_record("s1", payload, self.tr)
        rec = json.loads((self.home / "ctxvm-shadow" / "selection.jsonl").read_text())
        self.assertEqual(len(rec["repositioned_pages"]), 1)
        self.assertTrue(rec["repositioned_pages"][0]["page_id"].startswith("sha256:"))

    def test_schema_rejects_invalid_counts_hashes_and_shape(self):
        good = json.loads((Path(__file__).resolve().parents[3] /
                           "tools/fixtures/shadow/valid.jsonl").read_text())
        validate_record(good)
        cases = []
        for field, value in (("budget_tokens", -1), ("dropped_tokens", 999999),
                             ("selection_hash", None), ("prefix_hash", None)):
            bad = json.loads(json.dumps(good)); bad[field] = value; cases.append(bad)
        bad = json.loads(json.dumps(good)); bad["extra"] = 1; cases.append(bad)
        bad = json.loads(json.dumps(good)); bad["dropped_pages"][0]["page_id"] = "raw"; cases.append(bad)
        for bad in cases:
            with self.assertRaises(ShadowSchemaError):
                validate_record(bad)


class ShadowParityTests(unittest.TestCase):
    def test_duplicate_page_control_shadow_matches_real_plan(self):
        home = Path(tempfile.mkdtemp(prefix="ctxvm-shadow-parity-"))
        control = {"engine": "compressor", "budget": 20000, "budgetSource": "settings",
                   "profile": "w8-shadow", "arm": "control", "home": str(home),
                   "selectionMode": "fresh", "selectionModeSource": "default",
                   "stubDropped": "off", "stubDroppedSource": "default",
                   "shadowSelection": True, "shadowSelectionSource": "settings"}
        paged = dict(control, engine="ctxvm", arm="paged")
        msgs = [{"role": "system", "content": "sys"}, {"role": "user", "content": "go"}]
        # Same PageId twice -> second-demand pin/reposition, then pressure.
        for i in range(2):
            msgs.append({"role": "assistant", "content": "", "tool_calls": [{
                "id": f"dup{i}", "type": "function", "function": {
                    "name": "read_file", "arguments": json.dumps({"path": "dup.md"})}}]})
            msgs.append({"role": "tool", "content": "same", "tool_call_id": f"dup{i}"})
        for i in range(10):
            msgs.append({"role": "assistant", "content": "", "tool_calls": [{
                "id": f"u{i}", "type": "function", "function": {
                    "name": "read_file", "arguments": json.dumps({"path": f"u{i}.md"})}}]})
            msgs.append({"role": "tool", "content": ("u%d" % i) + "." * 20000,
                         "tool_call_id": f"u{i}"})
        real = ce.build_engine(v_budget=20000)
        real_plans = []
        real.set_observer(lambda p: None, real_plans.append)
        with mock.patch.object(ce, "_POLICY_MOD", types.SimpleNamespace(policy=lambda: dict(paged))):
            real.select_context(list(msgs))
        shadow_engine = ce.build_engine(v_budget=20000)
        shadow_plans = []
        shadow_engine.set_observer(lambda p: None, shadow_plans.append)
        with mock.patch.object(ce, "_POLICY_MOD", types.SimpleNamespace(policy=lambda: dict(control))):
            shadow_engine.select_context(list(msgs))
        self.assertEqual(real_plans[0]["droppedCount"], shadow_plans[0]["droppedCount"])
        self.assertEqual(real_plans[0]["repositionedCount"], shadow_plans[0]["repositionedCount"])
        self.assertEqual(real_plans[0]["selectionHash"], shadow_plans[0]["selectionHash"])
        self.assertGreater(real_plans[0]["repositionedCount"], 0)


class ShadowLiveIntegrationTests(unittest.TestCase):
    def setUp(self):
        live._clear_env_for_tests()
        self.home = Path(tempfile.mkdtemp(prefix="ctxvm-shadow-live-"))
        self.traces = Path(tempfile.mkdtemp(prefix="ctxvm-shadow-live-traces-"))
        (self.home / "config.yaml").write_text(
            "context:\n  engine: compressor\nplugins:\n  entries:\n"
            "    ctxvm-tracer:\n      settings:\n        budgetTokens: 24000\n"
            "        shadowSelection: true\n")
        self.pol = {"engine": "compressor", "budget": 24000, "budgetSource": "settings",
                    "profile": "w8-shadow", "arm": "control", "home": str(self.home),
                    "selectionMode": "fresh", "selectionModeSource": "default",
                    "stubDropped": "off", "stubDroppedSource": "default",
                    "shadowSelection": True, "shadowSelectionSource": "settings"}

    def test_control_pre_api_request_writes_record_and_attests(self):
        class Ctx:
            def __init__(self): self.hooks = {}; self.commands = {}
            def register_hook(self, n, cb): self.hooks[n] = cb; return lambda: None
            def on_unload(self, cb): return None
            def register_command(self, n, cb, description=""): self.commands[n] = cb; return None
            def get_config(self, key): return None
            def register_context_engine(self, engine): self.engine = engine

        with mock.patch.dict(os.environ, {"CTXVM_TRACE_DIR": str(self.traces),
                                          "HERMES_HOME": str(self.home)}):
            ctx = Ctx()
            live.register(ctx)
            h = ctx.hooks
            h["on_session_start"](session_id="live-s", model="m", provider="p")
            msgs = _tx(n=20, chars=20000)
            tr = live._state()["plugin"].tracer_for("live-s")
            # Declare the exact pages the request carries, so the shadow writer
            # can resolve ids to refs and historical content hashes.
            for m in msgs:
                if m.get("role") != "tool":
                    continue
                cid = m["tool_call_id"]
                call = next(c for x in msgs if x.get("role") == "assistant"
                            for c in (x.get("tool_calls") or []) if c.get("id") == cid)
                args = json.loads(call["function"]["arguments"])
                tr.page({"tool": "read_file", "args": args, "content": m["content"],
                         "toolEffect": "READ_ONLY"})
            h["pre_llm_call"](session_id="live-s", conversation_history=msgs)
            before = json.dumps(msgs, sort_keys=True)
            h["pre_api_request"](session_id="live-s", request_messages=msgs,
                                 conversation_history=msgs, system_prompt="sys")
            self.assertEqual(json.dumps(msgs, sort_keys=True), before)
            record_path = self.home / "ctxvm-shadow" / "selection.jsonl"
            self.assertTrue(record_path.exists())
            records = [json.loads(l) for l in record_path.read_text().splitlines()]
            self.assertGreaterEqual(len(records), 1)
            for rec in records:
                validate_record(rec)
                self.assertFalse(rec["policy_applied"])
                self.assertTrue(rec["request_unchanged"])
            h["on_session_end"](session_id="live-s")
        cov = json.loads((self.traces / "live-s.coverage.json").read_text())["plugin"]
        self.assertTrue(cov["shadowSelection"])
        self.assertEqual(cov["shadowSelectionSource"], "settings")
        self.assertGreater(cov["shadowSelections"], 0)
        self.assertEqual(cov["engineSelections"], 0)
        self.assertEqual(cov["shadowWriteFailures"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

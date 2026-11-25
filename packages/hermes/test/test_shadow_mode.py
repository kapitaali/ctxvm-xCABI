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
                   "droppedTokens": 20000, "droppedPages": [{"ids": ["notes/f2"], "tokens": 20000}],
                   "selectionMode": "fresh", "selectionHash": "sha256:a",
                   "prefixHash": "sha256:b", "trigger": None, "policyApplied": False}
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
                   "droppedTokens": 20000, "droppedPages": [{"ids": ["notes/f2"], "tokens": 20000}],
                   "selectionMode": "fresh", "selectionHash": "sha256:a",
                   "prefixHash": "sha256:b", "trigger": None, "policyApplied": False}
        live._write_shadow_record("s1", payload, self.tr)
        live._write_shadow_record("s2", payload, self.tr)
        rows = [json.loads(l) for l in (self.home / "ctxvm-shadow" / "selection.jsonl").read_text().splitlines()]
        self.assertEqual([r["session_id"] for r in rows], ["s1", "s2"])
        self.assertEqual([r["call_index"] for r in rows], [0, 0])

    def test_write_failure_is_visible_and_fail_open(self):
        with mock.patch.object(Path, "mkdir", side_effect=OSError("read-only")):
            live._write_shadow_record("s1", {}, self.tr)
        self.assertEqual(live._state()["shadowWriteFailures"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

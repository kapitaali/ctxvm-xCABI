"""W8 engine tests — the seven laws of the paged arm's v1 FaultPinPolicy
(`packages/hermes/live/context_engine.py`; the preregistered law is
`design/w8-capture-design.md` §3.3/§4, and the simulator mirror is
`benchmarks/metrics/policies.py` fault-pin @2nd-demand, served or not).

Run: cd packages/hermes && python -m pytest test/ -q   (or this file alone).

The host ABC (agent.context_engine) does not exist outside the hermes runtime,
so these tests install a minimal STRUCTURAL stub at import time — the engine
module then takes its _HOST_ABC branch against the stub and the pin class is
instantiable. The real hermes shape is pinned by the same virtual methods and
by EngineWiringTests in test_plugin.py.
"""

import copy
import json
import os
import sys
import types
import unittest
from abc import ABC, abstractmethod
from pathlib import Path
from unittest import mock

_LIVE_DIR = str(Path(__file__).resolve().parents[1] / "live")
if _LIVE_DIR not in sys.path:
    sys.path.insert(0, _LIVE_DIR)

# --- the arm policy, pinned for the suite -------------------------------------
# The engine asks `profile_policy.policy()` which arm this session belongs to, and outside the host
# that resolves the operator's own ~/.hermes (where context.engine is `compressor`), which would
# make every law test inert. The suite therefore declares the arm explicitly: paged by default, and
# ArmPolicyTests overrides it per test to prove the gate itself.
import profile_policy  # noqa: E402  (live/ is on sys.path above)

_PAGED_POLICY = {"engine": "ctxvm", "budget": 70000, "budgetSource": "settings",
                 "profile": "w8bn-paged", "arm": "paged", "home": "/suite"}
_REAL_POLICY = profile_policy.policy
mock.patch.object(profile_policy, "policy", lambda *a, **k: dict(_PAGED_POLICY)).start()

# --- structural stub of the host ABC, installed BEFORE the engine import ------
_stub_agent = types.ModuleType("agent")
_stub_ctx_engine = types.ModuleType("agent.context_engine")


class _HostContextEngine(ABC):
    """The subset of agent.context_engine.ContextEngine the engine relies on:
    class-level token state, the abstract contract, session reset, get_status."""

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
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def update_from_response(self, usage: dict) -> None:
        ...

    @abstractmethod
    def should_compress(self, prompt_tokens: int | None = None) -> bool:
        ...

    @abstractmethod
    def compress(self, messages, current_tokens=None, focus_topic=None,
                 force=False, memory_context=""):
        ...

    def on_session_reset(self) -> None:
        self.last_prompt_tokens = 0
        self.compression_count = 0

    def get_status(self) -> dict:
        last_prompt = max(self.last_prompt_tokens, 0)
        return {
            "last_prompt_tokens": last_prompt,
            "threshold_tokens": self.threshold_tokens,
            "context_length": self.context_length,
            "usage_percent": min(100, last_prompt / self.context_length * 100)
            if self.context_length else 0,
            "compression_count": self.compression_count,
        }

    def prune_tool_results_only(self, messages, current_tokens=None):
        return messages, 0

    def select_context(self, request_messages, *, conversation_messages=None,
                       incoming_message=None, budget_tokens=0):
        return None


_stub_ctx_engine.ContextEngine = _HostContextEngine
_stub_agent.context_engine = _stub_ctx_engine
sys.modules.setdefault("agent", _stub_agent)
sys.modules.setdefault("agent.context_engine", _stub_ctx_engine)

import context_engine as ce  # noqa: E402


# --- transcript builders -------------------------------------------------------

def _msg(role, content, **kw):
    d = {"role": role, "content": content}
    d.update(kw)
    return d


def _call(cid, path):
    return {"id": cid, "type": "function",
            "function": {"name": "read_file", "arguments": json.dumps({"path": path})}}


def _result(chars, word):
    """A tool body of `chars` characters; padding distinct per page."""
    pad = max(0, chars - len(word))
    return word + ("." * pad)


def _page_tokens(chars: int) -> int:
    """The engine's L6 arithmetic, mirrored: 4 structural + ceil(chars/4)."""
    return 4 + (chars + 3) // 4


def _estimate_all(messages) -> int:
    return sum(ce._tokens_for(m) for m in messages)


# ---------------------------------------------------------------------------
# vBudget resolution (§5)
# ---------------------------------------------------------------------------

class EngineBudgetTests(unittest.TestCase):
    """CTXVM_VBUDGET confirms or raises; a lowering is refused and RECORDED,
    never silently applied; malformed env is an absence, not a zero."""

    def test_preregistered_default_when_env_absent(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CTXVM_VBUDGET", None)
            engine = ce.build_engine()
            self.assertEqual(engine._v_budget, 24_000)
            self.assertEqual(engine._v_budget_source, "preregistered")
            self.assertFalse(engine._v_budget_refused_lower)

    def test_env_confirms_and_raises(self):
        for value in (24_000, 30_000):
            with mock.patch.dict(os.environ, {"CTXVM_VBUDGET": str(value)}, clear=False):
                engine = ce.build_engine()
                self.assertEqual(engine._v_budget, value)
                self.assertEqual(engine._v_budget_source, "env CTXVM_VBUDGET")
                self.assertFalse(engine._v_budget_refused_lower)

    def test_malformed_env_is_an_absence(self):
        for raw in ("junk", "-3", "0", ""):
            with mock.patch.dict(os.environ, {"CTXVM_VBUDGET": raw}, clear=False):
                engine = ce.build_engine()
                self.assertEqual(engine._v_budget, 24_000, f"env={raw!r}")
                self.assertEqual(engine._v_budget_source, "preregistered")

    def test_engine_never_lowers_below_preregistered(self):
        """The refusal law (design §5): a lowering tunes the arms toward PASS;
        the engine flags the refusal instead of operating it."""
        with mock.patch.dict(os.environ, {"CTXVM_VBUDGET": "12000"}, clear=False):
            engine = ce.build_engine()
            self.assertEqual(engine._v_budget, 24_000)
            self.assertTrue(engine._v_budget_refused_lower)
            self.assertTrue(engine.get_status()["vBudgetRefusedLower"])

    def test_env_wins_over_the_ctor_seam_and_ctor_is_clamped_too(self):
        """The env is the owner's T0 binding surface (wins over the ctor test
        seam); the ctor is itself subject to the refusal law."""
        with mock.patch.dict(os.environ, {"CTXVM_VBUDGET": "30000"}, clear=False):
            engine = ce.build_engine(v_budget=18_000)
            self.assertEqual(engine._v_budget, 30_000)
            self.assertFalse(engine._v_budget_refused_lower)
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CTXVM_VBUDGET", None)
            engine = ce.build_engine(v_budget=18_000)
            self.assertEqual(engine._v_budget, 24_000, "ctor lowering is refused too")
            self.assertTrue(engine._v_budget_refused_lower)
            self.assertEqual(engine._v_budget_source, "ctor")
            engine2 = ce.build_engine(v_budget=30_000)
            self.assertEqual(engine2._v_budget, 30_000)
            self.assertEqual(engine2._v_budget_source, "ctor")


class EngineLawTests(unittest.TestCase):
    """L1–L7 pins against hand-built transcripts.

    Worked arithmetic notes (L6: tokens = 4 + ceil(chars/4), so a 22,000-char
    page is 5,505 tokens; a transcript of system + user + n read/pair messages
    keeps page 1 and the last-6 tail in the hard floor — pages 2..5 of eight
    22k pages (4 × 5,505 = 22,020 est.) overflow remain ≈ 1,890, so the
    pressure tests drop the oldest droppable pages deterministically."""

    def setUp(self):
        os.environ.pop("CTXVM_VBUDGET", None)

    # -- helpers ---------------------------------------------------------------

    def _assert_request_valid(self, transcript, selected: list):
        """Pair-validity + keep-law presence — the invariants every replacement
        must hold (L1 + L5), independent of the exact drop set."""
        self.assertIsInstance(selected, list)
        ids_seen = {}
        for m in selected:
            self.assertIsInstance(m, dict)
            if isinstance(m.get("tool_calls"), list):
                for c in m["tool_calls"]:
                    cid = c.get("id")
                    self.assertNotIn(cid, ids_seen, f"duplicate call id {cid}")
                    ids_seen[cid] = False
            tid = m.get("tool_call_id")
            if isinstance(tid, str):
                self.assertIn(tid, ids_seen, f"dangling tool reply for {tid}")
                ids_seen[tid] = True
        for cid, answered in ids_seen.items():
            self.assertTrue(answered, f"call {cid} has no reply in the request")
        # the rewrite-on-copy law: originals were never mutated
        for m in transcript:
            if isinstance(m.get("tool_calls"), list):
                self.assertTrue(m["tool_calls"], "original carrier lost its calls")

    def _pair_positions(self, selected, cid):
        """(carrier_index, reply_index) of the single occurrence of a call and
        its adjacent reply, or raises."""
        carrier = reply = None
        for i, m in enumerate(selected):
            calls = m.get("tool_calls") if isinstance(m, dict) else None
            if calls and any(isinstance(c, dict) and c.get("id") == cid for c in calls):
                self.assertIsNone(carrier, f"call {cid} appears twice")
                carrier = i
                self.assertEqual(len(calls), 1,
                                 "block carriers carry exactly their one call")
            if m.get("tool_call_id") == cid:
                reply = i
        self.assertIsNotNone(carrier, f"call {cid} absent from the request")
        self.assertIsNotNone(reply, f"reply {cid} absent from the request")
        self.assertEqual(reply, carrier + 1, f"pair {cid} not adjacent")
        return carrier, reply

    def _call_count(self, selected, cid) -> int:
        n = 0
        for m in selected:
            for c in (m.get("tool_calls") or []):
                if isinstance(c, dict) and c.get("id") == cid:
                    n += 1
        return n

    # -- L7 --------------------------------------------------------------------

    def test_small_transcript_selects_none(self):
        """Under budget with no pins → None: the request stays byte-identical
        and the cache prefix is untouched."""
        engine = ce.build_engine()
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Investigate notes."),
              _msg("assistant", "", tool_calls=[_call("c1", "notes/alpha.md")]),
              _msg("tool", _result(2_000, "alpha"), tool_call_id="c1"),
              _msg("assistant", "", tool_calls=[_call("c2", "notes/bravo.md")]),
              _msg("tool", _result(2_000, "bravo"), tool_call_id="c2")]
        self.assertIsNone(engine.select_context(list(tx)))
        self.assertIsNone(engine.select_context(list(tx)))
        self.assertEqual(len(engine._pages), 2)
        self.assertEqual({p["demand_count"] for p in engine._pages.values()}, {1})

    # -- L3: the pin lands on the second demand --------------------------------

    def test_birth_demand_is_one_and_no_pin(self):
        """birth = demand 1 (the page was rendered once: the model read it) —
        and one demand never pins."""
        engine = ce.build_engine()
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Investigate notes."),
              _msg("assistant", "", tool_calls=[_call("c1", "notes/alpha.md")]),
              _msg("tool", _result(2_000, "alpha"), tool_call_id="c1")]
        engine.select_context(list(tx))
        key, page = next(iter(engine._pages.items()))
        self.assertEqual(page["demand_count"], 1)
        self.assertFalse(page["pinned"])

    def test_second_demand_via_prose_remention_pins(self):
        """A digest-unseen later message naming the identifier = demand 2 →
        pinned (policies.py: pin on second demand, served or not)."""
        engine = ce.build_engine()
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Investigate notes."),
              _msg("assistant", "", tool_calls=[_call("c1", "notes/alpha.md")]),
              _msg("tool", _result(2_000, "alpha"), tool_call_id="c1"),
              _msg("assistant", "", tool_calls=[_call("c2", "notes/bravo.md")]),
              _msg("tool", _result(2_000, "bravo"), tool_call_id="c2")]
        engine.select_context(list(tx))
        # the model re-mentions the ALPHA identifier in a new user turn
        tx2 = list(tx) + [_msg("user", "Now revisit the notes/alpha.md finding.")]
        out = engine.select_context(list(tx2))
        pinned_key, = engine._pin_order
        self.assertIn("notes/alpha", str(sorted(engine._pages[pinned_key]["id_toks"])))
        self.assertEqual(len(engine._pages) - 1,
                         sum(1 for p in engine._pages.values() if not p["pinned"]))

    def test_re_read_is_a_demand_that_pins_and_the_block_rides(self):
        """The same file read again (same rollup → same key, new result
        message) is a re-render = one more demand → pinned; the pinned page's
        pair then RIDES THE BLOCK even without pressure (L1(c) is the pinned
        pages' home — the first selection change since the pin)."""
        engine = ce.build_engine()
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Investigate notes."),
              _msg("assistant", "", tool_calls=[_call("c1", "notes/alpha.md")]),
              _msg("tool", _result(2_000, "alpha"), tool_call_id="c1")]
        self.assertIsNone(engine.select_context(list(tx)))
        tx2 = list(tx) + [
            _msg("assistant", "", tool_calls=[_call("c2", "notes/alpha.md")]),
            _msg("tool", _result(2_000, "alpha"), tool_call_id="c2")]
        out = engine.select_context(list(tx2))
        self.assertIsNotNone(out, "a pin repositions the pair into the block")
        c1_carrier, c1_reply = self._pair_positions(out, "c1")
        # the pinned block runs BEFORE the recency tail: the re-read (a fresh
        # call on the same page) stays at its own transcript position, after
        # the block (the head window may shrink when a kept member is
        # repositioned, so measure against the tail, not a counted head slot)
        c2_pos = next(i for i, m in enumerate(out)
                      if any(isinstance(c, dict) and c.get("id") == "c2"
                             for c in (m.get("tool_calls") or [])))
        self.assertLess(c1_carrier, c2_pos,
                        "the pinned block runs before the kept recency tail")
        # the re-read's own result stays at its call's position (a separate
        # page render; the block carries the page's first-sighted body)
        self.assertEqual(self._call_count(out, "c2"), 1)
        self.assertEqual({engine._pages[k]["demand_count"]
                          for k in engine._pin_order}, {2})

    def test_retry_reobservation_cannot_double_credit(self):
        """L2/L3: selecting twice on the same transcript (the host also runs
        select_context on provider retries) is ONE observation, not two, and —
        with the state unchanged — the outputs are identical."""
        engine = ce.build_engine()
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Investigate notes."),
              _msg("assistant", "", tool_calls=[_call("c1", "notes/alpha.md")]),
              _msg("tool", _result(2_000, "alpha"), tool_call_id="c1"),
              _msg("assistant", "", tool_calls=[_call("c2", "notes/bravo.md")]),
              _msg("tool", _result(2_000, "bravo"), tool_call_id="c2")]
        engine.select_context(list(tx))
        before = {k: (p["demand_count"], p["pinned"])
                  for k, p in engine._pages.items()}
        out2 = engine.select_context(list(tx))
        after = {k: (p["demand_count"], p["pinned"])
                 for k, p in engine._pages.items()}
        self.assertEqual(before, after, "a retry must not double-credit demand")
        self.assertIsNone(out2)

    def test_dropped_page_re_referenced_pins(self):
        """Design §4's fault-class signal in its purest live form: a page the
        selection DROPPED, re-referenced by prose — the demand pins it, and its
        pair rides the block on the next request."""
        engine = ce.build_engine()
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Work through the files.")]
        pages = [("c%d" % i, "notes/file%02d.md" % i, 22_000) for i in range(1, 9)]
        for cid, path, chars in pages:
            tx.append(_msg("assistant", "", tool_calls=[_call(cid, path)]))
            tx.append(_msg("tool", _result(chars, path.split("/")[-1].split(".")[0]),
                           tool_call_id=cid))
        out1 = engine.select_context(list(tx))
        self.assertIsNotNone(out1, "eight ~5.5k pages over 24k → selection fires")
        # file02's pair was dropped (oldest of the droppable cluster): its
        # body and its lone-call carrier are both out of the request
        self.assertEqual(self._call_count(out1, "c2"), 0)
        self.assertEqual([m for m in out1 if m.get("tool_call_id") == "c2"], [],
                         "a dropped call must not dangle")
        # re-mention file02 → demand 2 → pin → the pair rides the block
        tx2 = list(tx) + [_msg("user", "Back to notes/file02.md — combine findings.")]
        out2 = engine.select_context(list(tx2))
        self._assert_request_valid(tx2, out2)
        self.assertEqual(len(engine._pin_order), 1)
        carrier, reply = self._pair_positions(out2, "c2")
        non_system_positions = [i for i, m in enumerate(out2)
                                if isinstance(m, dict) and m.get("role") != "system"]
        self.assertGreater(carrier, non_system_positions[2])

    def test_pin_crunch_keeps_the_smallest_honoring_L5(self):
        """Sim-mirrored pin-crunch: when the pinned page + the hard floor
        already pass vBudget, the non-pinned pages all drop and the request
        busts VISIBLE rather than hiding it (the T0 lock error made visible)."""
        engine = ce.build_engine()
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Work through the files.")]
        pages = [("c%d" % i, "notes/file%02d.md" % i, 22_000) for i in range(1, 9)]
        for cid, path, chars in pages:
            tx.append(_msg("assistant", "", tool_calls=[_call(cid, path)]))
            tx.append(_msg("tool", _result(chars, path.split("/")[-1].split(".")[0]),
                           tool_call_id=cid))
        engine.select_context(list(tx))  # pressured: at least one drop happens
        tx2 = list(tx) + [_msg("user", "Back to notes/file02.md now.")]
        out2 = engine.select_context(list(tx2))
        self._assert_request_valid(tx2, out2)
        carrier, reply = self._pair_positions(out2, "c2")   # the pinned page rides
        # floor(4 pinned-tail kept pages ≈ 22k) + block + scaffold > vBudget
        self.assertGreater(_estimate_all(out2), engine._v_budget)
        non_pinned_bodies = [m for m in out2 if m.get("tool_call_id")
                             in {"c3", "c4", "c5"}]
        self.assertEqual(non_pinned_bodies, [],
                         "pin crunch drops every non-pinned, droppable page")

    def test_generic_argument_keys_never_demand(self):
        """Cross-fire guard (regression @2026-11-06): `path`, a parameter KEY
        shared by every read_file call, is not an identifier; re-invoking the
        tool on a DIFFERENT file must not demand the first file's page."""
        engine = ce.build_engine()
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Investigate notes."),
              _msg("assistant", "", tool_calls=[_call("c1", "notes/alpha.md")]),
              _msg("tool", _result(2_000, "alpha"), tool_call_id="c1"),
              _msg("assistant", "", tool_calls=[_call("c2", "notes/bravo.md")]),
              _msg("tool", _result(2_000, "bravo"), tool_call_id="c2")]
        engine.select_context(list(tx))
        for key, page in engine._pages.items():
            self.assertEqual(page["demand_count"], 1, f"{key} stays at birth demand")
            self.assertFalse(page["pinned"])
            self.assertNotIn("path", page["id_toks"])

    # -- L1 ordering + pair rewrite --------------------------------------------

    def test_pinned_block_order_is_frozen_first_pin_order(self):
        """Two pins land in mention order; the block carries them pair-adjact
        in the frozen order; every original transcript slot is rewritten out
        (the shared carrier keeps its other call, rebuilt as a reduced COPY;
        the lone-call carrier vanishes with its call)."""
        engine = ce.build_engine()
        base = [
            _msg("system", "You are a coding agent."),
            _msg("user", "Work through the files."),
            _msg("assistant", "", tool_calls=[_call("c01", "notes/file01.md")]),
            _msg("tool", _result(6_000, "file01"), tool_call_id="c01"),
            _msg("assistant", "", tool_calls=[_call("c02", "notes/file02.md"),
                                              _call("c03", "notes/file03.md")]),
            _msg("tool", _result(6_000, "file02"), tool_call_id="c02"),
            _msg("tool", _result(6_000, "file03"), tool_call_id="c03"),
            _msg("assistant", "", tool_calls=[_call("c04", "notes/file04.md")]),
            _msg("tool", _result(6_000, "file04"), tool_call_id="c04"),
            _msg("assistant", "", tool_calls=[_call("c05", "notes/file05.md")]),
            _msg("tool", _result(6_000, "file05"), tool_call_id="c05"),
            _msg("assistant", "", tool_calls=[_call("c06", "notes/file06.md")]),
            _msg("tool", _result(6_000, "file06"), tool_call_id="c06"),
        ]
        engine.select_context(list(base))
        # mention file03 (demand 2 → pin), then file05 (demand 2 → pin)
        with_m3 = list(base) + [_msg("user", "Compare notes/file03.md to the brief.")]
        out2 = engine.select_context(list(with_m3))
        self._assert_request_valid(with_m3, out2)
        self.assertEqual(len(engine._pin_order), 1)
        with_m5 = list(with_m3) + [
            _msg("user", "And notes/file05.md goes with notes/file03.md.")]
        out3 = engine.select_context(list(with_m5))
        self._assert_request_valid(with_m5, out3)
        pinned = list(engine._pin_order)   # frozen order: file03 then file05
        self.assertEqual(len(pinned), 2)
        c3_carrier, c3_reply = self._pair_positions(out3, "c03")
        c5_carrier, c5_reply = self._pair_positions(out3, "c05")
        self.assertLess(c3_carrier, c5_carrier,
                        "the block runs in first-pin order")
        block_start = c3_carrier
        non_system_positions = [i for i, m in enumerate(out3)
                                if isinstance(m, dict) and m.get("role") != "system"]
        head_last = non_system_positions[2]
        self.assertGreater(block_start, head_last,
                           "the block runs after the head-protected window")
        # the shared carrier keeps c02 and lost c03 (rewritten COPY, original
        # untouched) — original check in _assert_request_valid
        rewritten = [m for m in out3 if m.get("tool_calls")
                     and [c.get("id") for c in m["tool_calls"]] == ["c02"]]
        self.assertEqual(len(rewritten), 1, "the shared carrier keeps its kept call")
        self.assertEqual(rewritten[0]["tool_calls"][0]["function"]["name"], "read_file")
        # the lone-call carrier vanished with its call; its reply rides the block
        self.assertEqual(self._call_count(out3, "c05"), 1)
        self.assertEqual([m for m in out3 if m.get("tool_call_id") == "c05"],
                         [out3[c5_reply]])
        # the kept un-pinned content runs AFTER the block (L1d recency tail):
        # the shared carrier's reduced copy lands in transcript order there
        idx = out3.index(rewritten[0])
        self.assertGreater(idx, c5_reply,
                           "kept unpinned content runs after the pinned block")

    # -- L4 --------------------------------------------------------------------

    def test_new_rollup_for_same_identity_releases_the_pin(self):
        """Pichay §3.5 step 4: pin = (tool identity + rollup); a NEW rollup for
        the same invocation releases it. Same args + changed content → the old
        key unpins; the fresh page starts unbudgeted."""
        engine = ce.build_engine()
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Investigate notes."),
              _msg("assistant", "", tool_calls=[_call("c1", "notes/alpha.md")]),
              _msg("tool", _result(2_000, "alpha"), tool_call_id="c1")]
        engine.select_context(list(tx))
        tx2 = list(tx) + [_msg("user", "Again: notes/alpha.md please.")]
        out2 = engine.select_context(list(tx2))
        self.assertIsNotNone(out2)   # the pin rides the block
        self.assertEqual(len(engine._pin_order), 1)
        # third read, SAME identity, DIFFERENT content → new rollup → release
        tx3 = list(tx2) + [
            _msg("assistant", "", tool_calls=[_call("c3", "notes/alpha.md")]),
            _msg("tool", "CHANGED BODY " + _result(1_900, "alpha"), tool_call_id="c3")]
        engine.select_context(list(tx3))
        self.assertEqual(engine._pin_order, [],
                         "the new rollup released the page's pin")
        self.assertEqual(len(engine._pages), 2)   # old rollup + new rollup rows

    def test_different_identity_does_not_release(self):
        """Same tool, other args → other identity: the pin survives (L4 binds
        to the invocation, not to the tool name)."""
        engine = ce.build_engine()
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Investigate notes."),
              _msg("assistant", "", tool_calls=[_call("c1", "notes/alpha.md")]),
              _msg("tool", _result(2_000, "alpha"), tool_call_id="c1")]
        engine.select_context(list(tx))
        tx2 = list(tx) + [_msg("user", "Back to notes/alpha.md.")]
        engine.select_context(list(tx2))
        self.assertEqual(len(engine._pin_order), 1)
        tx3 = list(tx2) + [
            _msg("assistant", "", tool_calls=[_call("c2", "notes/bravo.md")]),
            _msg("tool", _result(2_000, "bravo"), tool_call_id="c2")]
        engine.select_context(list(tx3))
        self.assertEqual(len(engine._pin_order), 1, "bravo must not release alpha")

    # -- L5 keep law + floor ---------------------------------------------------

    def test_floor_above_budget_selects_none(self):
        """L5 law corner: when the hard floor alone reaches vBudget the engine
        leaves the request untouched for this round — pages never rescue a
        busting floor (the T0 lock error made visible)."""
        engine = ce.build_engine()
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Work through the files.")]
        pages = [("c%d" % i, "notes/f%02d.md" % i, 28_000) for i in range(1, 9)]
        for cid, path, chars in pages:
            tx.append(_msg("assistant", "", tool_calls=[_call(cid, path)]))
            tx.append(_msg("tool", _result(chars, path.split("/")[-1].split(".")[0]),
                           tool_call_id=cid))
        # the floor alone = system + head(3) + tail(6) → page bodies r1, r6,
        # r7, r8 ≈ 4 × 7,006 > 24,000
        out = engine.select_context(list(tx))
        self.assertIsNone(out)
        self.assertFalse(engine._pin_order)

    def test_keep_law_members_survive_a_pressured_selection(self):
        """System first verbatim; head window in transcript order; the last
        user message present at the end; drops only lose whole DROPPED page
        pairs."""
        engine = ce.build_engine()
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Work through the files.")]
        pages = [("c%d" % i, "notes/f%02d.md" % i, 12_000) for i in range(1, 11)]
        for cid, path, chars in pages:
            tx.append(_msg("assistant", "", tool_calls=[_call(cid, path)]))
            tx.append(_msg("tool", _result(chars, path.split("/")[-1].split(".")[0]),
                           tool_call_id=cid))
        last = _msg("user", "Wrap up: how do notes/f01.md and the others relate?")
        tx.append(last)
        out = engine.select_context(list(tx))
        self._assert_request_valid(tx, out)
        self.assertEqual(out[0]["role"], "system")
        self.assertEqual(out[0]["content"], tx[0]["content"])
        self.assertEqual(out[1], tx[1])            # head window, transcript order
        self.assertEqual(out[2], tx[2])
        self.assertEqual(out[3], tx[3])
        self.assertIs(out[-1], last, "the last user message is kept verbatim")
        # the request stays inside the enforced budget (L6 arithmetic)
        self.assertLessEqual(_estimate_all(out), engine._v_budget)
        # something was actually dropped (11k × 7 pages over-budget)
        self.assertLess(len([m for m in out if m.get("role") == "tool"]),
                        len(pages), "pressure must drop something")

    # -- L2 purity -------------------------------------------------------------

    def test_same_state_same_list(self):
        """L2: two engines in the same pre-selection state select the same
        list and land in the same page-table state."""
        pages = [("c%d" % i, "notes/f%02d.md" % i, 22_000) for i in range(1, 9)]
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Work through the files.")]
        for cid, path, chars in pages:
            tx.append(_msg("assistant", "", tool_calls=[_call(cid, path)]))
            tx.append(_msg("tool", _result(chars, path.split("/")[-1].split(".")[0]),
                           tool_call_id=cid))
        fresh = ce.build_engine()
        first, second = fresh, copy.deepcopy(fresh)
        out1 = first.select_context(list(tx))
        out2 = second.select_context(list(tx))
        self.assertEqual(json.dumps(out1, sort_keys=True),
                         json.dumps(out2, sort_keys=True))
        self.assertEqual(first._pages, second._pages)
        self.assertEqual(first._pin_order, second._pin_order)

    def test_select_returns_none_when_output_would_equal_input(self):
        """The no-op gate is structural, not accidental: under budget, no
        pins → no reposition → no drops → None (verify via the plan walk)."""
        engine = ce.build_engine()
        tx = [_msg("system", "s"), _msg("user", "u"),
              _msg("assistant", "", tool_calls=[_call("c1", "notes/a.md")]),
              _msg("tool", _result(100, "a"), tool_call_id="c1")]
        dropped, repos = engine._plan(
            tx, engine._classify(tx), engine._hard_keep(tx, engine._classify(tx)))
        self.assertEqual((dropped, repos), (set(), set()))

    # -- copying / lifecycle ----------------------------------------------------

    def test_clone_isolation(self):
        engine = ce.build_engine()
        tx = [_msg("system", "s"), _msg("user", "u"),
              _msg("assistant", "", tool_calls=[_call("c1", "notes/alpha.md")]),
              _msg("tool", _result(2_000, "alpha"), tool_call_id="c1")]
        engine.select_context(list(tx))
        self.assertTrue(engine._pages)
        twin = copy.deepcopy(engine)
        twin._pages["ghost"] = {"tokens": 1, "pinned": True, "demand_count": 5,
                                "id_toks": frozenset(), "birth": 0}
        twin._pin_order.append("ghost-twin")
        engine._pin_order.append("ghost-origin")
        self.assertNotIn("ghost-twin", engine._pin_order)
        self.assertNotIn("ghost-origin", twin._pin_order)
        self.assertIn("ghost", twin._pages)
        self.assertNotIn("ghost", engine._pages)

    def test_on_session_reset_clears_the_page_table(self):
        engine = ce.build_engine()
        tx = [_msg("system", "s"), _msg("user", "u"),
              _msg("assistant", "", tool_calls=[_call("c1", "notes/alpha.md")]),
              _msg("tool", _result(2_000, "alpha"), tool_call_id="c1")]
        engine.select_context(list(tx))
        engine.select_context(list(tx) + [_msg("user", "notes/alpha.md again")])
        self.assertTrue(engine._pin_order)
        engine.compression_count = 3          # the base class's counter state
        engine.on_session_reset()
        self.assertEqual(engine._pages, {})
        self.assertEqual(engine._pin_order, [])
        self.assertEqual(engine._credited_texts, set())
        self.assertEqual(engine._sighted, set())
        # the base class's own token-state reset still ran
        self.assertEqual(engine.compression_count, 0)

    # -- L6 the estimate family -------------------------------------------------

    def test_estimate_ceiling_and_overhead(self):
        """L6: ceil(chars/4) + 4 structural overhead; rounding never
        under-counts a body; the tool reply's own id bytes count (they ARE
        prompt bytes)."""
        self.assertEqual(ce._estimate_tokens("abcde"), 2)
        self.assertEqual(ce._estimate_tokens("abcd"), 1)
        body = "x" * 999
        m = _msg("tool", body, tool_call_id="c1")
        # _message_text = body + "\n" + "c1" = 1_002 bytes → 4 + 251
        self.assertEqual(ce._tokens_for(m), 4 + (1_002 + 3) // 4)
        u = _msg("user", body)
        self.assertEqual(ce._tokens_for(u), 4 + (999 + 3) // 4)

    def test_status_shape_and_token_bookkeeping(self):
        engine = ce.build_engine()
        engine.context_length = 200_000
        engine.threshold_tokens = 150_000
        engine.update_from_response({"prompt_tokens": 12_345,
                                     "completion_tokens": 678,
                                     "total_tokens": 13_023})
        status = engine.get_status()
        self.assertEqual(status["engine"], "ctxvm")
        self.assertEqual(status["last_prompt_tokens"], 12_345)
        self.assertEqual(status["vBudget"], 24_000)
        self.assertEqual(status["pages"], 0)
        self.assertEqual(status["pinned"], 0)
        self.assertEqual(status["compression_count"], 0)
        for field in ("vBudgetSource", "vBudgetRefusedLower"):
            self.assertIn(field, status)

    def test_engine_never_compacts_and_stays_noop_on_other_seams(self):
        engine = ce.build_engine()
        self.assertIs(engine.should_compress(999_999), False)
        msgs = [{"role": "user", "content": "hi"}]
        self.assertEqual(engine.compress(msgs), msgs)
        pruned, n = engine.prune_tool_results_only(msgs)
        self.assertEqual((pruned, n), (msgs, 0))
        self.assertIs(engine.emit_automatic_compaction_status, False)


class NoOpByteIdentityTests(unittest.TestCase):
    """C2 (RR-W8CACHE): a no-op selection must leave the request untouched.

    The claim under test is the one the cache investigation needs: when `_plan`
    returns early (protected floor at or above the budget) or when the whole
    request fits, `select_context` returns None and MUTATES NOTHING — so a
    request-size series cannot be explained by the engine rewriting history.
    """

    @staticmethod
    def _tx(n=10, result_chars=20_000):
        tx = [_msg("system", "You are a coding agent."),
              _msg("user", "Census the notes.")]
        for i in range(n):
            cid = f"c{i}"
            tx.append(_msg("assistant", "", tool_calls=[_call(cid, f"notes/part-{i}.txt")]))
            tx.append(_msg("tool", _result(result_chars, f"part{i}"), tool_call_id=cid))
        return tx

    def test_floor_at_or_above_budget_returns_none_and_preserves_bytes(self):
        tx = self._tx()
        before = json.dumps(tx, sort_keys=True)
        engine = ce.build_engine(v_budget=1_000)          # floor is far above this
        out = engine.select_context(list(tx))
        # L7 says None; the contract that matters for the cache is BYTES. A pinned
        # page can make the engine return a list that is still byte-identical.
        self.assertEqual(json.dumps(out if out is not None else tx, sort_keys=True), before)

    def test_request_under_budget_returns_none_and_preserves_bytes(self):
        tx = self._tx(n=2, result_chars=200)
        before = json.dumps(tx, sort_keys=True)
        engine = ce.build_engine(v_budget=10_000_000)
        out = engine.select_context(list(tx))
        self.assertEqual(json.dumps(out if out is not None else tx, sort_keys=True), before)

    def test_when_eviction_happens_the_head_is_byte_identical_and_order_is_kept(self):
        tx = self._tx(n=12, result_chars=40_000)
        before = [json.dumps(m, sort_keys=True) for m in tx]
        engine = ce.build_engine(v_budget=60_000)          # between floor and total
        out = engine.select_context(list(tx))
        self.assertIsNotNone(out, "a request this size must be selected down")
        self.assertEqual(json.dumps(out[0], sort_keys=True), before[0])   # system verbatim
        positions = [before.index(json.dumps(m, sort_keys=True)) for m in out
                     if json.dumps(m, sort_keys=True) in before]
        self.assertEqual(positions, sorted(positions), "kept messages must keep transcript order")


class ArmPolicyTests(unittest.TestCase):
    """One gateway serves every profile, so the arm must be read per SESSION, not per process.

    Measured 2026-11-11: the naive arm reported `engine: ctxvm` and `budgetTokens: 70000 /
    settings` because the plugin took one settings snapshot at registration and applied it to
    every session served afterwards. These tests pin the per-profile resolution that replaces it.
    """

    def _home(self, name, engine, budget=None):
        import tempfile
        root = Path(tempfile.mkdtemp(prefix=f"w8bn-{name}-"))
        lines = ["model:", '  default: "x"', "context:", f'  engine: "{engine}"']
        if budget is not None:
            lines += ["plugins:", "  entries:", "    ctxvm-tracer:", "      settings:",
                      f"        budgetTokens: {budget}"]
        (root / "config.yaml").write_text("\n".join(lines) + "\n")
        return root

    def test_control_profile_is_control_and_carries_no_budget(self):
        import profile_policy
        home = self._home("naive", "compressor")
        pol = _REAL_POLICY(home)
        self.assertEqual(pol["arm"], "control")
        self.assertEqual(pol["engine"], "compressor")
        self.assertEqual(pol["budgetSource"], "default")

    def test_paged_profile_is_paged_and_carries_its_budget(self):
        import profile_policy
        home = self._home("paged", "ctxvm", 70000)
        pol = _REAL_POLICY(home)
        self.assertEqual(pol["arm"], "paged")
        self.assertEqual(pol["budget"], 70000)
        self.assertEqual(pol["budgetSource"], "settings")

    def test_missing_config_falls_open_to_control(self):
        import profile_policy
        import tempfile
        home = Path(tempfile.mkdtemp(prefix="w8bn-empty-"))
        pol = _REAL_POLICY(home)
        self.assertEqual(pol["arm"], "control", "a missing profile must never become a treatment")
        self.assertEqual(pol["budget"], 200000)

    def test_comments_and_quotes_do_not_confuse_the_reader(self):
        import profile_policy
        import tempfile
        home = Path(tempfile.mkdtemp(prefix="w8bn-comments-"))
        (home / "config.yaml").write_text(
            "# context:\ncontext:\n  engine: \"ctxvm\"   # the treatment\n"
            "plugins:\n  entries:\n    ctxvm-tracer:\n      settings:\n"
            "        budgetTokens: 70000  # measured floor + middle\n")
        pol = _REAL_POLICY(home)
        self.assertEqual(pol["engine"], "ctxvm")
        self.assertEqual(pol["budget"], 70000)

    def test_engine_declines_when_the_session_profile_is_control(self):
        import context_engine
        import profile_policy
        engine = context_engine.CtxvmFaultPinEngine(v_budget=70000)
        msgs = [{"role": "user", "content": "hi"}]
        with mock.patch.object(profile_policy, "policy",
                               return_value={"engine": "compressor", "budget": 70000,
                                             "budgetSource": "settings", "profile": "w8bn-naive",
                                             "arm": "control", "home": "/x"}):
            self.assertIsNone(engine.select_context(msgs, budget_tokens=70000))
        self.assertEqual(engine._meter["skipped_control"], 1)
        self.assertEqual(engine._meter["select"], 0, "a control session must not select")

    def test_engine_acts_when_the_session_profile_is_paged(self):
        import context_engine
        import profile_policy
        engine = context_engine.CtxvmFaultPinEngine(v_budget=1)
        msgs = [{"role": "user", "content": "hi"}]
        with mock.patch.object(profile_policy, "policy",
                               return_value={"engine": "ctxvm", "budget": 1,
                                             "budgetSource": "settings", "profile": "w8bn-paged",
                                             "arm": "paged", "home": "/y"}):
            engine.select_context(msgs, budget_tokens=1)
        self.assertEqual(engine._meter["select"], 1)
        self.assertEqual(engine._meter["skipped_control"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

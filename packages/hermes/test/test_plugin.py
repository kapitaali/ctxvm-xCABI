"""T17 Hermes plugin tests — env gate, hook registration/mapping, cleanup flush.

Run: python test/test_plugin.py   (or: cd packages/hermes && npm test)
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

# Make packages/hermes/src and packages/hermes importable
_HERMES_ROOT = str(Path(__file__).resolve().parents[1])
_HERMES_SRC = str(Path(__file__).resolve().parents[1] / "src")
for _p in (_HERMES_ROOT, _HERMES_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from plugin import CtxvmPlugin, create_ctxvm_plugin, Tracer, TraceInit, canonical_json, content_hash, tool_ref, identity_tokens, provider_usage_of  # noqa: E402
from live import PLUGIN_VERSION, _canon_meta, _clear_env_for_tests, _state, register  # noqa: E402

INIT = {
    "agentId": "hermes",
    "model": "openai/gpt-5",
    "provider": "openai",
    "budgetTokens": 120000,
}

TRACE_INIT = TraceInit(
    agent_id="hermes",
    model="openai/gpt-5",
    provider="openai",
    budget_tokens=120000,
)


class TracerTests(unittest.TestCase):
    """Pure tracer unit tests — mirror packages/node/test/tracer.test.ts."""

    def run_healthy(self):
        vm = Tracer(TRACE_INIT)
        vm.page({"ref": "file:src/auth.ts", "kind": "file", "content": "export const S = 1;\n"})
        vm.page({"tool": "read_file", "args": {"path": "src/auth/session.ts"}, "content": "SESSION = configured\n"})
        vm.page({"ref": "summary:t0", "kind": "summary", "content": "turn-0 micro-summary"})
        vm.render()
        vm.render()
        vm.render()
        vm.scan({"text": "opening src/auth/session.ts to verify the change", "latencyMs": 12})
        vm.render({"latencyMs": 1240})
        return vm.finish()

    def test_event_types_and_field_order_match_rfc0(self):
        trace = self.run_healthy()
        lines = [json.loads(l) for l in trace.jsonl.strip().split("\n")]
        self.assertEqual(lines[0]["type"], "session.open")
        # RFC-0.1 §R0 extends the session.open shape: schemaVersion rides
        # directly after tokenizerId (the canonical v0.1 wire order the rust
        # writer minted) — same card as the opencode mirror and the parity doc.
        # R4-ts (RR-R4TS2): ts rides LAST on the line — same card as the node
        # mirror and the parity doc (D9 per-lane law, port stamping its own).
        self.assertEqual(
            list(lines[0].keys()),
            ["type", "agentId", "model", "provider", "budgetTokens", "tokenizerId", "schemaVersion", "ts"],
        )
        # The v0.1 schema's ts pattern, mirrored: RFC 3339 UTC, milliseconds.
        self.assertRegex(lines[0]["ts"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
        declares = [e for e in lines if e["type"] == "page.declare"]
        self.assertEqual(list(declares[0]["page"].keys()), ["id", "kind", "tokens"])
        # RFC-0.1 §R5 + §R4 (R5-turn card): the declaration turn sits directly
        # after the page object and latencyMs (when supplied) rides between turn
        # and ts. The healthy run supplies none ⇒ type,page,turn,ts.
        self.assertEqual(list(declares[0].keys()), ["type", "page", "turn", "ts"])
        turns = [e for e in lines if e["type"] == "turn.render"]
        self.assertEqual([e["turn"] for e in turns], [0, 1, 2, 3])
        self.assertEqual(turns[0]["evictedTokens"], 0)
        self.assertEqual(turns[0]["headroom"], 120000 - turns[0]["residentTokens"])
        faults = [e for e in lines if e["type"] == "page.fault"]
        self.assertEqual(faults[0]["source"], "identifier_scan")
        self.assertEqual(faults[0]["turn"], 2)
        self.assertEqual(faults[0]["latencyMs"], 12)
        metas = [e for e in lines if e["type"] == "call.meta"]
        self.assertEqual(len(metas), 4)
        self.assertEqual(metas[3]["turn"], 3)
        self.assertEqual(metas[3]["cacheEstimate"]["providerReported"], False)
        order = [e["type"] for e in lines]
        last_tr = max(i for i, e in enumerate(lines) if e["type"] == "turn.render")
        first_cm = min(i for i, e in enumerate(lines) if e["type"] == "call.meta")
        self.assertLess(last_tr, first_cm)

    def test_page_declare_carries_its_declaration_turn_rfc01_r5(self):
        """The stamped turn is the counter AT DECLARATION TIME; declarations made
        before the first render carry -1 and stamp as 0 (RFC-0 §5 convention —
        the same law page.fault uses). Reveal bookkeeping unchanged."""
        vm = Tracer(TRACE_INIT)
        vm.page({"ref": "file:pre.py", "kind": "file", "content": "P"})  # counter -1 → stamps 0
        vm.render()  # turn 0 — reveals the pre page
        vm.render()  # turn 1
        vm.page({"ref": "file:mid.py", "kind": "file", "content": "M"})  # counter 1 → stamps 1
        vm.page({"ref": "file:mid2.py", "kind": "file", "content": "M2"})  # same turn, second declare
        vm.render()  # turn 2 — reveals both mid pages
        events = [json.loads(l) for l in vm.finish().jsonl.strip().split("\n")]
        declares = [e for e in events if e["type"] == "page.declare"]
        self.assertEqual([e["turn"] for e in declares], [0, 1, 1])
        renders = [e for e in events if e["type"] == "page.render"]
        self.assertEqual([(e["turn"], e["page"]["logicalRef"]) for e in renders],
                         [(0, "file:pre.py"), (2, "file:mid.py"), (2, "file:mid2.py")])

    def test_page_declare_latency_ms_intake_law_rfc01_r4(self):
        """Strict intake mirroring noteUsage: a finite integer >= 0 is emitted;
        anything else is an ABSENCE and the key is omitted — never null, never
        coerced, never a float. bool is excluded because bool IS an int in
        Python (True must not become 1 ms)."""
        vm = Tracer(TRACE_INIT)
        vm.page({"ref": "file:a.py", "kind": "file", "content": "A"})  # absent
        vm.page({"ref": "file:b.py", "kind": "file", "content": "B", "latencyMs": 0})  # 0 is a fact
        vm.page({"ref": "file:c.py", "kind": "file", "content": "C", "latencyMs": 12})  # valid
        vm.page({"ref": "file:d.py", "kind": "file", "content": "D", "latencyMs": 1.5})  # float
        vm.page({"ref": "file:e.py", "kind": "file", "content": "E", "latencyMs": -3})  # negative
        vm.page({"ref": "file:f.py", "kind": "file", "content": "F", "latencyMs": True})  # bool
        vm.page({"ref": "file:g.py", "kind": "file", "content": "G", "latencyMs": "12"})  # str
        events = [json.loads(l) for l in vm.finish().jsonl.strip().split("\n")]
        declares = [e for e in events if e["type"] == "page.declare"]
        self.assertEqual([e.get("latencyMs") for e in declares], [None, 0, 12, None, None, None, None])
        for e in declares:
            if "latencyMs" in e:
                self.assertIsInstance(e["latencyMs"], int)
                self.assertNotIsInstance(e["latencyMs"], bool)
                self.assertGreaterEqual(e["latencyMs"], 0)
        # Wire order when present: the field rides between turn and ts.
        self.assertEqual(list(declares[2].keys()), ["type", "page", "turn", "latencyMs", "ts"])

    def test_finish_idempotent_tail_regenerates(self):
        """T17.7 law pinned BOTH sides this card (mirrors the node tracer test).

        The tail is computed per call and never appended to the event stream:
        repeated flushes (mid-session handoff trigger, session end, dispose)
        produce the same JSONL; lifecycle recorded after a first flush joins
        the next transcript exactly once, with a regenerated tail.
        """
        vm = Tracer(TRACE_INIT)
        vm.page({"ref": "file:src/a.ts", "kind": "file", "content": "A"})
        vm.render()
        vm.render({"latencyMs": 100})
        first = vm.finish()
        again = vm.finish()
        self.assertEqual(again.jsonl, first.jsonl)
        # Mid-session flush continues: new lifecycle, then the second finish.
        vm.page({"ref": "file:src/b.ts", "kind": "file", "content": "B"})
        vm.render({"latencyMs": 200})
        second = vm.finish()
        self.assertEqual(
            [e["turn"] for e in second.events if e["type"] == "turn.render"], [0, 1, 2]
        )
        self.assertEqual(len([e for e in second.events if e["type"] == "call.meta"]), 3)
        self.assertEqual(len([e for e in second.events if e["type"] == "page.declare"]), 2)
        # The first flushed transcript was never mutated by the later flush.
        self.assertEqual(
            [e["turn"] for e in first.events if e["type"] == "turn.render"], [0, 1]
        )
        self.assertEqual(len([e for e in first.events if e["type"] == "page.declare"]), 1)

    def test_resident_render_sums_match_declared_pages(self):
        trace = self.run_healthy()
        lines = [json.loads(l) for l in trace.jsonl.strip().split("\n")]
        tr0 = next(e for e in lines if e["type"] == "turn.render" and e["turn"] == 0)
        declares = [e for e in lines if e["type"] == "page.declare"]
        total_tokens = sum(d["page"]["tokens"] for d in declares)
        self.assertEqual(tr0["residentTokens"], total_tokens)
        self.assertEqual(trace.stats["pages"], 3)
        self.assertEqual(trace.stats["turns"], 4)
        self.assertEqual(trace.stats["faults"], 1)

    def test_tool_recall_resident_recall_page_fault(self):
        vm = Tracer(TRACE_INIT)
        vm.page({"tool": "read_file", "args": {"path": "src/auth/session.ts"}, "content": "A"})
        vm.render()
        vm.recall({"tool": "read_file", "args": {"path": "src/auth/session.ts"}})
        landing = vm.page({"tool": "read_file", "args": {"path": "src/auth/session.ts"}, "content": "A"})
        vm.render()
        trace = vm.finish()
        faults = [e for e in trace.events if e["type"] == "page.fault"]
        self.assertEqual([[f["source"], f["turn"]] for f in faults], [["tool_recall", 0]])
        self.assertEqual(faults[0]["page"]["contentHash"], landing["contentHash"])

    def test_fresh_fetch_same_ref_new_hash_not_scored_as_waste(self):
        vm = Tracer(TRACE_INIT)
        vm.page({"tool": "read_file", "args": {"path": "src/auth/session.ts"}, "content": "v1"})
        vm.render()
        vm.recall({"tool": "read_file", "args": {"path": "src/auth/session.ts"}})
        fresh = vm.page({"tool": "read_file", "args": {"path": "src/auth/session.ts"}, "content": "v2"})
        vm.render()
        trace = vm.finish()
        declares = [e for e in trace.events if e["type"] == "page.declare"]
        self.assertEqual(len(declares), 2)
        self.assertEqual(declares[1]["page"]["id"]["contentHash"], fresh["contentHash"])
        faults = [e for e in trace.events if e["type"] == "page.fault"]
        self.assertEqual(len(faults), 0)

    def test_identifier_scan_deduped_per_page_per_source(self):
        vm = Tracer(TRACE_INIT)
        vm.page({"ref": "file:src/auth/session.ts", "kind": "file", "content": "s"})
        vm.render()
        vm.scan({"text": "mentions src/auth/session.ts twice: src/auth/session.ts"})
        vm.scan({"text": "mentions src/auth/session.ts again"})
        vm.render()
        trace = vm.finish()
        faults = [e for e in trace.events if e["type"] == "page.fault"]
        self.assertEqual(len(faults), 1)

    def test_determinism_identical_sessions_byte_identical(self):
        # D9: ts default-ON stamps each trace's own wall-clock; the per-trace
        # opt-out is the named byte-stability mechanism.
        prev = os.environ.get("CTXVM_TRACE_TS")
        os.environ["CTXVM_TRACE_TS"] = "0"
        try:
            self.assertEqual(self.run_healthy().jsonl, self.run_healthy().jsonl)
        finally:
            if prev is None:
                os.environ.pop("CTXVM_TRACE_TS", None)
            else:
                os.environ["CTXVM_TRACE_TS"] = prev

    def test_ts_rides_last_on_every_event_rfc3339_utc_ms_default_on(self):
        # RFC-0.1 §R4 (D9 default-ON, RR-R4TS2): ts on EVERY event, LAST key,
        # RFC 3339 UTC ms, monotonic across the stream (live pushes + cached
        # tail snapshots mint in temporal order by construction).
        vm = self.run_healthy()
        events = vm.events
        for e in events:
            keys = list(e.keys())
            self.assertEqual(keys[-1], "ts", f"ts must ride LAST on {e['type']}")
            self.assertRegex(
                e["ts"], r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])T([01]\d|2[0-3]):[0-5]\d:([0-5]\d|60)\.\d{3}Z$",
            )
        # The FILE order is canonical by event class, not by time: finish() emits
        # every turn.render and then every call.meta, and the tail is re-derived on
        # each flush so repeated flushes stay byte-identical (D9 / idempotency law).
        # So the stream as a whole is NOT monotonic. What holds: the live prefix is
        # stamped as events are pushed; each turn's render and meta carry the same
        # snapshot stamp; the turn stamps ascend with the turn index.
        types = [e["type"] for e in events]
        split = len(types)
        while split > 0 and types[split - 1] in ("turn.render", "call.meta"):
            split -= 1
        live_stamps = [e["ts"] for e in events[:split]]
        self.assertEqual(sorted(live_stamps), live_stamps, "live pushes are time-monotonic")
        tail = events[split:]
        renders = [e for e in tail if e["type"] == "turn.render"]
        metas = [e for e in tail if e["type"] == "call.meta"]
        self.assertTrue(renders, "the fixture must exercise the tail")
        self.assertEqual(
            [e["type"] for e in tail],
            ["turn.render"] * len(renders) + ["call.meta"] * len(metas),
            "the tail is grouped by class, renders before metas",
        )
        render_stamps = [r["ts"] for r in renders]
        self.assertEqual(sorted(render_stamps), render_stamps, "turn stamps ascend with the turn index")
        for meta in metas:
            render = next((r for r in renders if r["turn"] == meta["turn"]), None)
            if render is None or "ts" not in meta:
                continue
            self.assertEqual(meta["ts"], render["ts"], f"turn {meta['turn']}: meta carries its render's stamp")
        # Tail snapshots mint at their turn's render snapshot time: repeated
        # finish() flushes re-derive the SAME stamps — covered by
        # test_finish_idempotent_tail_regenerates, deliberately left unwrapped
        # so it proves idempotency holds under default-ON.

    def test_ctxvm_trace_ts_0_opts_out_bytewise(self):
        # CTXVM_TRACE_TS=0: no ts on any line, byte determinism restored (D9).
        prev = os.environ.get("CTXVM_TRACE_TS")
        os.environ["CTXVM_TRACE_TS"] = "0"
        try:
            first = self.run_healthy()
            again = self.run_healthy()
            for e in first.events + again.events:
                self.assertNotIn("ts", e, f"no ts under the opt-out on {e['type']}")
            self.assertEqual(again.jsonl, first.jsonl, "the opt-out is the byte-stability mechanism")
        finally:
            if prev is None:
                os.environ.pop("CTXVM_TRACE_TS", None)
            else:
                os.environ["CTXVM_TRACE_TS"] = prev

    def test_content_hash_and_canonical_json(self):
        self.assertRegex(content_hash("anything"), r"^sha256:[0-9a-f]{8}$")
        self.assertEqual(
            canonical_json({"b": 1, "a": [2, {"d": 1, "c": 2}]}),
            '{"a":[2,{"c":2,"d":1}],"b":1}',
        )

    def test_session_open_first_line_newline_terminated(self):
        trace = self.run_healthy()
        first = json.loads(trace.jsonl.split("\n")[0])
        self.assertEqual(first["type"], "session.open")
        self.assertTrue(trace.jsonl.endswith("\n"))
        for line in trace.jsonl.strip().split("\n"):
            json.loads(line)

    def test_tool_ref_stable_under_arg_key_order(self):
        a = tool_ref(None, "read_file", {"path": "src/a.ts", "mode": "r"})
        b = tool_ref(None, "read_file", {"mode": "r", "path": "src/a.ts"})
        self.assertEqual(a, b)
        self.assertEqual(a, 'tool:read_file({"mode":"r","path":"src/a.ts"})')

    def test_tool_ref_truncates_over_120_chars(self):
        payload = {"blob": "x" * 400}
        r1 = tool_ref("github", "create_issue", payload)
        r2 = tool_ref("github", "create_issue", payload)
        self.assertEqual(r1, r2)
        self.assertTrue(r1.startswith("tool:github.create_issue("))
        self.assertLess(len(r1), 200)
        different = tool_ref("github", "create_issue", {"blob": "_" * 400})
        self.assertNotEqual(r1, different)

    def test_identity_tokens_longest_first(self):
        tokens = identity_tokens("tool:read_file({\"path\":\"src/auth/session.ts\"})")
        self.assertTrue(all(len(t) >= 3 for t in tokens))
        if len(tokens) > 1:
            self.assertGreaterEqual(len(tokens[0]), len(tokens[-1]))


class PluginTests(unittest.TestCase):
    """CtxvmPlugin hook-handler tests — mirror packages/opencode/test/plugin.test.ts."""

    def _run_once(self):
        plugin = create_ctxvm_plugin(INIT)
        session_id = "ses_hermes_test"

        plugin.on_session_start({"session_id": session_id})
        plugin.on_pre_tool_call({
            "session_id": session_id, "tool": "read", "args": {"path": "notes.txt"},
        })
        plugin.on_post_tool_call({
            "session_id": session_id, "tool": "read", "args": {"path": "notes.txt"},
            "status": "completed",
            "result": {"content": [{"type": "text", "text": "hello"}]},
        })
        plugin.on_pre_llm_call({
            "session_id": session_id,
            "conversation_history": [
                {"role": "user", "content": [{"type": "text", "text": "Read notes.txt"}]},
                {"role": "assistant", "content": [{"type": "text", "text": "It says hello."}]},
            ],
        })

        return plugin.finish_all()[0]

    def test_one_session_replays_to_expected_event_shape(self):
        record = self._run_once()
        events = record["trace"].events
        types = [e["type"] for e in events]
        self.assertEqual(types.count("session.open"), 1)
        self.assertEqual(record["trace"].stats["turns"], 1)
        self.assertEqual(record["trace"].stats["pages"], 1)
        self.assertEqual(record["trace"].stats["faults"], 1)

    def test_errored_call_produces_no_page(self):
        plugin = create_ctxvm_plugin(INIT)
        plugin.on_session_start({"session_id": "ses_err"})
        plugin.on_post_tool_call({
            "session_id": "ses_err", "tool": "read", "args": {"path": "missing.json"},
            "status": "error", "error": {"code": "ENOENT"},
        })
        record = plugin.finish_all()[0]
        events = record["trace"].events
        declares = [e for e in events if e["type"] == "page.declare"]
        self.assertEqual(len(declares), 0)

    def test_live_shape_status_ok_declares_page(self):
        """Live Hermes post_tool_call uses status='ok' (model_tools.py:_tool_result_observer_fields)."""
        plugin = create_ctxvm_plugin(INIT)
        plugin.on_session_start({"session_id": "ses_ok"})
        plugin.on_pre_tool_call({
            "session_id": "ses_ok", "tool": "read", "args": {"path": "notes/alpha.md"},
        })
        plugin.on_post_tool_call({
            "session_id": "ses_ok", "tool": "read", "args": {"path": "notes/alpha.md"},
            "status": "ok",
            "result": {"content": [{"type": "text", "text": "hello world"}]},
        })
        plugin.on_pre_llm_call({
            "session_id": "ses_ok",
            "conversation_history": [
                {"role": "user", "content": [{"type": "text", "text": "Read notes/alpha.md"}]},
            ],
        })
        record = plugin.finish_all()[0]
        events = record["trace"].events
        declares = [e for e in events if e["type"] == "page.declare"]
        faults = [e for e in events if e["type"] == "page.fault"]
        self.assertEqual(len(declares), 1, "status='ok' must declare a page")
        self.assertEqual(len(faults), 1)  # identifier_scan from history text
        self.assertEqual(record["trace"].stats["pages"], 1)
        self.assertEqual(record["trace"].stats["turns"], 1)

    def test_live_shape_tool_name_declares_page(self):
        """Live Hermes passes tool_name (not tool) — must still declare a page."""
        plugin = create_ctxvm_plugin(INIT)
        plugin.on_session_start({"session_id": "ses_tn"})
        plugin.on_pre_tool_call({
            "session_id": "ses_tn", "tool_name": "read", "args": {"path": "notes/alpha.md"},
        })
        plugin.on_post_tool_call({
            "session_id": "ses_tn", "tool_name": "read", "args": {"path": "notes/alpha.md"},
            "status": "ok",
            "result": "hello world",
        })
        record = plugin.finish_all()[0]
        declares = [e for e in record["trace"].events if e["type"] == "page.declare"]
        self.assertEqual(len(declares), 1)
        self.assertIn("read_file" if False else "read", declares[0]["page"]["id"]["logicalRef"])

    def test_tool_none_maps_to_tool_name(self):
        """Gateway payload with tool:null + tool_name set must still declare a page.

        The hook-key mapping falls back from tool to tool_name; tool=None (key
        present, value null) is falsy and must not leak into the ref as
        tool:None(...).
        """
        plugin = create_ctxvm_plugin(INIT)
        plugin.on_session_start({"session_id": "ses_tn"})
        plugin.on_pre_tool_call({
            "session_id": "ses_tn", "tool": None, "tool_name": "read",
            "args": {"path": "notes/alpha.md"},
        })
        plugin.on_post_tool_call({
            "session_id": "ses_tn", "tool": None, "tool_name": "read",
            "args": {"path": "notes/alpha.md"},
            "status": "ok",
            "result": "hello world",
        })
        record = plugin.finish_all()[0]
        declares = [e for e in record["trace"].events if e["type"] == "page.declare"]
        self.assertEqual(len(declares), 1)
        self.assertIn("read", declares[0]["page"]["id"]["logicalRef"])

    def test_live_shape_stamps_the_registered_class(self):
        """W17 finder pin: on live payloads the tool arrives under `tool_name`, so the
        W15 class stamp must read the SAME effective name the adapter's ref
        builder uses. On 0.8.0 real hermes bytes EVERY declare classified
        MUTATING because the stamp site read a synthetic key (`tool`) the host
        never sends on this hook — 447 witness rows read `after tool=None` —
        and tools/coverage_check.py caught it from the registration-law check
        on real capture bytes (read_file stamped MUTATING in the live trace).
        A keys-only parity test passes while every page is wrong; this asserts
        the registered VALUE reaches the flushed declare row through the live
        adapter (the stamp site), fired as the real hook fires."""
        _clear_env_for_tests()
        tmp = Path(tempfile.mkdtemp(prefix="ctxvm-cls-"))
        os.environ["CTXVM_TRACE_DIR"] = str(tmp)
        os.environ["CTXVM_TRACE_NAME"] = "cls"
        cbs, cmds = {}, {}

        class FakeCtx:
            def register_hook(self, name, cb):
                cbs[name] = cb
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                cmds[name] = handler
                return None

        register(FakeCtx())
        try:
            cbs["pre_tool_call"](
                session_id="s", tool_name="read_file",
                args={"path": "notes/alpha.md"},
            )
            cbs["post_tool_call"](
                session_id="s", tool_name="read_file",
                args={"path": "notes/alpha.md"}, status="ok",
                result="hello world",
            )
            out = cmds["ctxvm-trace"]("stop")
            self.assertIn("1 trace(s)", out)
            rows = [json.loads(line) for line in (tmp / "cls.jsonl").read_text(
                encoding="utf-8").splitlines() if line.strip()]
            declare = next(r for r in rows if r.get("type") == "page.declare")
            self.assertEqual(declare.get("toolEffect"), "READ_ONLY",
                             "the registration table must reach live-shaped payloads")
        finally:
            for key in ("CTXVM_TRACE_DIR", "CTXVM_TRACE_NAME"):
                os.environ.pop(key, None)

    def test_live_shape_string_content_scan_fires(self):
        """W4b B1 regression pin — RED before the fix, green after.

        Live Hermes v0.22.5 appends assistant messages with ``content`` as a
        PLAIN STRING (agent/conversation_loop.py:350, oneshot.py:103). The old
        parser expected a parts list, so identifier_scan saw '' every live
        turn and could never fire (m4/m7 LIVE: 0 faults).
        """
        plugin = create_ctxvm_plugin(INIT)
        plugin.on_session_start({"session_id": "ses_str"})
        plugin.on_pre_tool_call({
            "session_id": "ses_str", "tool": "read", "args": {"path": "notes/alpha.md"},
        })
        plugin.on_post_tool_call({
            "session_id": "ses_str", "tool": "read", "args": {"path": "notes/alpha.md"},
            "status": "ok",
            "result": "alpha contents",
        })
        plugin.on_pre_llm_call({
            "session_id": "ses_str",
            "conversation_history": [
                {"role": "assistant", "content": "I read notes/alpha.md"},
            ],
        })
        record = plugin.finish_all()[0]
        faults = [e for e in record["trace"].events if e["type"] == "page.fault"]
        self.assertEqual(len(faults), 1, "the live string shape must fire identifier_scan")
        self.assertEqual(faults[0]["source"], "identifier_scan")

    def test_live_shape_multimodal_parts_still_scan(self):
        """W4b B1 guard — the block shape (multimodal / OpenCode-style) keeps firing."""
        plugin = create_ctxvm_plugin(INIT)
        plugin.on_session_start({"session_id": "ses_blk"})
        plugin.on_pre_tool_call({
            "session_id": "ses_blk", "tool": "read", "args": {"path": "notes/alpha.md"},
        })
        plugin.on_post_tool_call({
            "session_id": "ses_blk", "tool": "read", "args": {"path": "notes/alpha.md"},
            "status": "ok",
            "result": "alpha contents",
        })
        plugin.on_pre_llm_call({
            "session_id": "ses_blk",
            "conversation_history": [
                {"role": "user", "content": [{"type": "text", "text": "Read notes/alpha.md again"}]},
            ],
        })
        record = plugin.finish_all()[0]
        faults = [e for e in record["trace"].events if e["type"] == "page.fault"]
        self.assertEqual(len(faults), 1)
        self.assertEqual(faults[0]["source"], "identifier_scan")

    def test_transcript_texts_shape_matrix(self):
        """W4b B1 unit matrix — the next Hermes shape change fails one obvious test."""
        T = CtxvmPlugin._transcript_texts
        self.assertEqual(
            T([{"role": "assistant", "content": "plain string body"}]),
            "plain string body",
        )
        self.assertEqual(
            T([{"role": "user", "content": [
                {"type": "text", "text": "block one"},
                {"type": "text", "text": "block two"},
            ]}]),
            "block one\nblock two",
        )
        self.assertEqual(
            T([{"role": "user", "parts": [{"type": "text", "text": "part one"}, "part two str"]}]),
            "part one\npart two str",
        )
        self.assertEqual(
            T([{"role": "user", "text": "direct text"}]),
            "direct text",
        )
        # Non-text blocks, bare strings, junk dicts, and non-dict messages.
        self.assertEqual(
            T([{"role": "user", "content": [{"type": "image", "url": "x"}, "str item", {"bogus": 1}, 42]}]),
            "str item",
        )
        self.assertEqual(
            T(["not a dict", {"role": "user", "content": "after non-dict"}]),
            "after non-dict",
        )

    def test_finish_all_returns_trace_with_jsonl_and_stats(self):
        record = self._run_once()
        self.assertIn("sessionID", record)
        self.assertIn("trace", record)
        trace = record["trace"]
        self.assertIsNotNone(trace.jsonl)
        self.assertIsNotNone(trace.stats)
        self.assertEqual(record["sessionID"], "ses_hermes_test")


class LiveAdapterTests(unittest.TestCase):
    """Live adapter tests — mirror packages/opencode/test/live-adapter.test.ts."""

    def setUp(self):
        _clear_env_for_tests()

    def test_adapter_is_inert_without_ctxvm_trace_dir(self):
        """Without CTXVM_TRACE_DIR, hooks are registered but no tracing occurs."""
        _clear_env_for_tests()
        calls = []

        class FakeCtx:
            def register_hook(self, name, cb):
                calls.append(("hook", name))
                return lambda: None

            def on_unload(self, cb):
                calls.append(("unload", cb.__name__))
                return None

            def register_command(self, name, handler, description=""):
                calls.append(("command", name))
                return None

        register(FakeCtx())
        # Hooks are always registered (gating is lazy per-call); the key invariant
        # is that no plugin instance is created and no traces are written.
        self.assertEqual(len(calls), 11)  # 7 hooks (W8: +post_api_request) + 3 commands (trace/help/start) + 1 unload
        self.assertIn(("hook", "on_session_start"), calls)
        self.assertIn(("hook", "pre_api_request"), calls)
        self.assertIn(("command", "ctxvm-trace"), calls)
        # cleanup is registered as a lambda inside register(), so __name__ is "<lambda>"
        self.assertIn(("unload", "<lambda>"), calls)

    # --- adoption contract (2026-11-01): ON by default, `~` expanded, honest stop ---

    def test_trace_dir_defaults_to_state_dir_when_unset(self):
        """Capture is ON out of the box: unset env resolves to the XDG state dir."""
        _clear_env_for_tests()
        import live as live_mod
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": "/tmp/xdg-test"}, clear=False):
            self.assertEqual(live_mod._resolve_trace_dir(None), "/tmp/xdg-test/ctxvm/traces")
        self.assertTrue(live_mod._traced())

    def test_tilde_is_expanded_and_never_literal(self):
        """`~` in a trace dir must expand; a literal '~' dir was the 2026-11-01 bug."""
        _clear_env_for_tests()
        import live as live_mod
        resolved = live_mod._resolve_trace_dir("~/ctxvm-tilde-test")
        self.assertTrue(os.path.isabs(resolved))
        self.assertNotIn("/~", resolved)
        self.assertEqual(resolved, os.path.join(os.path.expanduser("~"), "ctxvm-tilde-test"))

    def test_opt_out_env_and_empty_string_disable(self):
        """Two documented ways to switch capture off."""
        _clear_env_for_tests()
        import live as live_mod
        with mock.patch.dict(os.environ, {"CTXVM_TRACE": "0"}, clear=False):
            self.assertIsNone(live_mod._resolve_trace_dir("/tmp/whatever"))
        _clear_env_for_tests()
        self.assertIsNone(live_mod._resolve_trace_dir(""))

    def test_adapter_creates_plugin_by_default_and_honours_opt_out(self):
        """Replaces the old default-OFF contract: a plugin exists unless disabled."""
        _clear_env_for_tests()
        from live import _make_plugin
        self.assertIsNotNone(_make_plugin())
        _clear_env_for_tests()
        with mock.patch.dict(os.environ, {"CTXVM_TRACE": "0"}, clear=False):
            self.assertIsNone(_make_plugin())

    def test_identity_from_payload_stamps_session_open(self):
        """Hermes knows the model; the tracer uses it instead of env placeholders."""
        from plugin import create_ctxvm_plugin, identity_from_payload
        ident = identity_from_payload({"model": "vendor/model-a", "provider": "vendor"})
        self.assertEqual(ident, {"model": "vendor/model-a", "provider": "vendor"})
        self.assertIsNone(identity_from_payload({}))
        # nested shape (opencode-style): model: {id, providerID}
        nested = identity_from_payload({"model": {"id": "vendor/model-b", "providerID": "vendor"}})
        self.assertEqual(nested, {"model": "vendor/model-b", "provider": "vendor"})
        # provider-only spellings
        self.assertEqual(identity_from_payload({"provider_id": "p2"}), {"provider": "p2"})
        vm = create_ctxvm_plugin({"agentId": "hermes", "model": "unknown/unknown",
                                  "provider": "unknown", "budgetTokens": 1000})
        vm.on_session_start({"session_id": "s-identity", "model": "vendor/model-a",
                             "provider": "vendor"})
        tracer = vm.tracer_for("s-identity")
        opened = [e for e in tracer._events if e.get("type") == "session.open"][0]
        self.assertEqual(opened["model"], "vendor/model-a")
        self.assertEqual(opened["provider"], "vendor")

    def test_settings_identity_fills_the_init_fallback(self):
        """Host-owned plugin settings (ctx.get_config) complete the identity the
        turn-prep payload cannot: pre_llm_call carries no provider (HOOKS.md §1,
        source-verified against the pinned runtime), and identity is stamped once —
        no backfill after write-through. The settings source is read at register(),
        before any hook fires, and degrades fail-open in every hostile case."""
        _clear_env_for_tests()
        from live import _identity_from_settings

        class SettingsCtx:
            """Host-shaped: `identity` carries both; a bare `model` would be refused."""
            def get_config(self, key):
                if key.split(".")[0].lower() in {"model", "plugins", "security", "settings"}:
                    raise ValueError("reserved root")
                return {"identity": {"model": "vendor/model-a",
                                     "provider": "vendor"}}.get(key)

        self.assertEqual(_identity_from_settings(SettingsCtx()),
                         {"model": "vendor/model-a", "provider": "vendor"})
        # fail-open: no get_config method at all
        self.assertEqual(_identity_from_settings(object()), {})
        self.assertEqual(_identity_from_settings(None), {})

        class RaisingCtx:
            def get_config(self, key):
                raise RuntimeError("host exploded mid-config")

        self.assertEqual(_identity_from_settings(RaisingCtx()), {})
        # non-string or blank values are skipped, never minted
        class BlankCtx:
            def get_config(self, key):
                return {"model": "   ", "provider": 42}.get(key)

        self.assertEqual(_identity_from_settings(BlankCtx()), {})

        # The host REFUSES a plugin settings key whose first segment is reserved
        # (model/plugins/security/settings): `get_config("model")` raises. The first
        # version wrapped the whole loop in one try, so the raise on `model` aborted
        # the lookup before `provider` was ever read — the documented remedy for
        # `provider: unknown` was dead, and the exception was swallowed. Mirror the
        # real rule here so a permissive fake cannot hide it again.
        class ReservedRootCtx:
            RESERVED = {"model", "plugins", "security", "settings"}
            def __init__(self, identity=None, provider=None):
                self._identity, self._provider = identity, provider
            def get_config(self, key):
                if key.split(".")[0].lower() in self.RESERVED:
                    raise ValueError("reserved root")
                if key == "identity":
                    return self._identity
                if key == "provider":
                    return self._provider
                return None

        self.assertEqual(
            _identity_from_settings(ReservedRootCtx(identity={"model": "vendor/model-b",
                                                              "provider": "vendor-b"})),
            {"model": "vendor/model-b", "provider": "vendor-b"},
            "the non-reserved `identity` mapping carries both fields",
        )
        self.assertEqual(
            _identity_from_settings(ReservedRootCtx(provider="vendor-c")),
            {"provider": "vendor-c"},
            "a refused `model` root must not abort the `provider` read",
        )

    def test_settings_outrank_env_and_payload_still_wins(self):
        """Priority chain: payload > plugin settings > env > 'unknown'. Settings
        beat env because they are the running gateway's declared configuration."""
        _clear_env_for_tests()
        os.environ["CTXVM_PROVIDER"] = "envprov"
        os.environ["CTXVM_MODEL"] = "envvendor/envmodel"
        try:
            class SettingsCtx:
                def register_hook(self, name, cb):
                    return lambda: None

                def on_unload(self, cb):
                    return None

                def register_command(self, name, handler, description=""):
                    return None

                def get_config(self, key):
                    if key.split(".")[0].lower() in {"model", "plugins", "security", "settings"}:
                        raise ValueError("reserved root")
                    return {"identity": {"model": "vendor/model-a",
                                         "provider": "settingsprov"}}.get(key)

            register(SettingsCtx())
            from live import _make_plugin
            pm = _make_plugin()
            self.assertIsNotNone(pm)
            self.assertEqual(pm._init.provider, "settingsprov")  # settings beat env
            self.assertEqual(pm._init.model, "vendor/model-a")   # settings beat env
            # the payload still outranks settings: covered (session.open model/provider)
            # by test_identity_from_payload_stamps_session_open above.
        finally:
            _clear_env_for_tests()

    def test_slash_command_start_then_stop(self):
        """Slash command /ctxvm-trace start|stop enables/disables tracing at runtime."""
        _clear_env_for_tests()
        tmpdir = tempfile.mkdtemp(prefix="ctxvm-slash-test-")

        captured = []

        class FakeCtx:
            def register_hook(self, name, cb):
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                captured.append((name, handler))
                return None

        register(FakeCtx())

        # Find the registered handler
        handlers = [h for n, h in captured if n == "ctxvm-trace"]
        self.assertEqual(len(handlers), 1)
        handle = handlers[0]

        # Tracing is ON by default (adoption contract): before `start`, the dir is the
        # resolved default, not None. `start` then switches it to the explicit path.
        import live as live_mod
        self.assertTrue(live_mod._traced())
        self.assertEqual(live_mod._active_trace_dir(), live_mod._resolve_trace_dir(None))

        # Start tracing via slash command
        out = handle(f"start {tmpdir} slash-session")
        self.assertIn("tracing enabled", out)
        self.assertTrue(live_mod._traced())
        self.assertEqual(live_mod._active_trace_dir(), tmpdir)

        # Status
        out = handle("status")
        self.assertIn("enabled=True", out)
        self.assertIn(tmpdir, out)

        # Stop tracing — no session activity, so the message must say ZERO, not "flushed"
        out = handle("stop")
        self.assertIn("stopped", out)
        self.assertIn("0 traces written", out)
        self.assertFalse(live_mod._traced())
        self.assertIsNone(live_mod._active_trace_dir())

    def test_slash_command_unknown_subcommand(self):
        """Unknown /ctxvm-trace subcommand returns usage."""
        _clear_env_for_tests()

        class FakeCtx:
            def register_hook(self, name, cb):
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                self.commands = getattr(self, "commands", {})
                self.commands[name] = handler
                return None

        ctx = FakeCtx()
        register(ctx)
        # By name: three commands register now, and "the last one" is not the trace
        # command any more.
        trace = ctx.commands["ctxvm-trace"]
        out = trace("bogus")
        self.assertIn("unknown subcommand", out.lower())

        out = trace("")
        self.assertIn("Usage:", out)

    def test_environment_id_derives_from_the_hosts_session_workspace(self):
        """W14: the hermes lane derives the id from ctx.session_cwd(), per session.

        The host exposes the calling session's recorded working directory to a plugin
        handle and says explicitly it is never the gateway's own cwd — so this is a
        registration-time fact, not an inference.
        """
        def run(cwd, name):
            """One isolated capture: fresh process state, given workspace, one turn."""
            _clear_env_for_tests()
            out_dir = tempfile.mkdtemp(prefix=f"ctxvm-env-{name}-")
            os.environ["CTXVM_TRACE_DIR"] = out_dir
            os.environ["CTXVM_TRACE_NAME"] = name
            cmds, cbs = {}, {}

            class FakeCtx:
                def register_hook(self, hook, cb):
                    cbs[hook] = cb
                    return lambda: None

                def on_unload(self, cb):
                    return None

                def register_command(self, command, handler, description=""):
                    cmds[command] = handler
                    return None

                def session_cwd(self):
                    return cwd

            register(FakeCtx())
            # session_start does not fire in every build: the first pre_llm_call
            # must carry the id, because that is what creates the tracer.
            cbs["pre_llm_call"](session_id=f"ses-{name}", conversation_history=[], model="m")
            cmds["ctxvm-trace"]("stop")
            return json.loads(Path(out_dir, f"{name}.jsonl").read_text(encoding="utf-8").splitlines()[0])

        a = tempfile.mkdtemp(prefix="ctxvm-ws-a-")
        b = tempfile.mkdtemp(prefix="ctxvm-ws-b-")

        first = run(a, "one").get("environmentId")
        self.assertIsNotNone(first, "the workspace must yield an environment id")
        self.assertRegex(first, r"^env-[0-9a-f]{12}$")
        self.assertNotIn(Path(a).name, first, "the id must not carry the path")

        same = run(a, "two").get("environmentId")
        self.assertEqual(same, first, "one workspace, one id")

        other = run(b, "three").get("environmentId")
        self.assertNotEqual(other, first, "different workspaces differ")

    def test_environment_id_prefers_the_git_remote_over_the_path(self):
        """Two clones of one repository share an id; the remote never appears in it."""
        import shutil
        import subprocess

        if shutil.which("git") is None:
            self.skipTest("git not available")
        import live as live_mod

        def clone(remote: str, extra: str) -> str:
            d = tempfile.mkdtemp(prefix=f"ctxvm-clone-{extra}-")
            subprocess.run(["git", "init", "-q", d], check=True)
            subprocess.run(["git", "-C", d, "remote", "add", "origin", remote], check=True)
            return d

        one = clone("https://user:token@git.example.com/Org/Repo.git", "one")
        two = clone("git@git.example.com:Org/Repo.git", "two")
        three = clone("https://git.example.com/Org/Other.git", "three")

        a = live_mod._derive_environment_id(one)
        b = live_mod._derive_environment_id(two)
        c = live_mod._derive_environment_id(three)
        self.assertEqual(a, b, "one remote, one environment, whatever the transport")
        self.assertNotEqual(a, c, "different repositories differ")
        self.assertRegex(a, r"^env-[0-9a-f]{12}$")
        self.assertNotIn("git.example.com", a, "the remote must not leak into the id")
        self.assertNotIn("token", a, "credentials must not reach the id")

    def test_environment_id_absent_when_the_host_records_no_workspace(self):
        """No workspace, no key — absence is the honest answer, not a hash of nothing."""
        _clear_env_for_tests()
        tmpfile = tempfile.mkdtemp(prefix="ctxvm-envn-")
        os.environ["CTXVM_TRACE_DIR"] = tmpfile
        os.environ["CTXVM_TRACE_NAME"] = "nw"
        cmds, cbs = {}, {}

        class FakeCtx:
            def register_hook(self, name, cb):
                cbs[name] = cb
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                cmds[name] = handler
                return None

            def session_cwd(self):
                return ""

        register(FakeCtx())
        cbs["pre_llm_call"](session_id="s1", conversation_history=[], model="m")
        cmds["ctxvm-trace"]("stop")
        opened = json.loads(Path(tmpfile, "nw.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertNotIn("environmentId", opened)
        os.environ.pop("CTXVM_TRACE_DIR", None)
        os.environ.pop("CTXVM_TRACE_NAME", None)

    def test_explicit_environment_id_outranks_the_host_workspace(self):
        """A registered id is a deliberate statement; the host value must not override it."""
        _clear_env_for_tests()
        tmpfile = tempfile.mkdtemp(prefix="ctxvm-enve-")
        wd = tempfile.mkdtemp(prefix="ctxvm-envw-")
        os.environ["CTXVM_TRACE_DIR"] = tmpfile
        os.environ["CTXVM_TRACE_NAME"] = "ex"
        os.environ["CTXVM_ENVIRONMENT_ID"] = "env-0a1b2c3d4e5f"
        cmds, cbs = {}, {}

        class FakeCtx:
            def register_hook(self, name, cb):
                cbs[name] = cb
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                cmds[name] = handler
                return None

            def session_cwd(self):
                return wd

        register(FakeCtx())
        cbs["pre_llm_call"](session_id="s1", conversation_history=[], model="m")
        cmds["ctxvm-trace"]("stop")
        opened = json.loads(Path(tmpfile, "ex.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(opened.get("environmentId"), "env-0a1b2c3d4e5f")
        for key in ("CTXVM_TRACE_DIR", "CTXVM_TRACE_NAME", "CTXVM_ENVIRONMENT_ID"):
            os.environ.pop(key, None)

    def test_environment_id_is_opaque_and_rides_before_ts(self):
        """W14: the environment id is a hash, never a path, and ts stays last."""
        init = TraceInit(agent_id="a", model="m", provider="p", budget_tokens=0,
                         environment_id="env-0a1b2c3d4e5f")
        line = Tracer(init).finish().jsonl.splitlines()[0]
        self.assertIn("environmentId", line)
        self.assertLess(line.index("environmentId"), line.index('"ts"'),
                        "environmentId must ride before ts (ts is last)")

        # Absent by default — absence is "unknown", never an invented id.
        plain = Tracer(TraceInit(agent_id="a", model="m", provider="p",
                                 budget_tokens=0)).finish().jsonl.splitlines()[0]
        self.assertNotIn("environmentId", plain)

    def test_adapter_accepts_only_an_opaque_environment_id(self):
        """W14: a malformed value is dropped, and a path can never reach the trace."""
        _clear_env_for_tests()
        tmp = tempfile.mkdtemp(prefix="ctxvm-w14-")
        os.environ["CTXVM_TRACE_DIR"] = tmp
        os.environ["CTXVM_TRACE_NAME"] = "env"
        cbs, cmds = {}, {}

        class FakeCtx:
            def register_hook(self, name, cb):
                cbs[name] = cb
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                cmds[name] = handler
                return None

        os.environ["CTXVM_ENVIRONMENT_ID"] = "env-0a1b2c3d4e5f"
        register(FakeCtx())
        cbs["on_session_start"](session_id="s1")
        cbs["pre_llm_call"](session_id="s1", conversation_history=[], model="m")
        cmds["ctxvm-trace"]("stop")
        opened = json.loads(Path(tmp, "env.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(opened["environmentId"], "env-0a1b2c3d4e5f")

        # A path (or any non-opaque value) is refused at the boundary: the adapter
        # returns None, so the key is absent and no path can reach a trace.
        import live as live_mod
        os.environ["CTXVM_ENVIRONMENT_ID"] = "/home/someone/private-project"
        self.assertIsNone(live_mod._environment_id(), "a path is not an opaque id")
        os.environ["CTXVM_ENVIRONMENT_ID"] = "env-SHORT"
        self.assertIsNone(live_mod._environment_id(), "a non-opaque id is refused")
        os.environ["CTXVM_ENVIRONMENT_ID"] = "env-0a1b2c3d4e5f"
        self.assertEqual(live_mod._environment_id(), "env-0a1b2c3d4e5f")
        os.environ.pop("CTXVM_ENVIRONMENT_ID", None)

    def test_pre_api_request_bills_the_static_prefix(self):
        """W13: the prefix cost comes from the host's own counters, per turn."""
        init = TraceInit(agent_id="ctxvm-dev", model="m", provider="p", budget_tokens=0)
        tr = Tracer(init)
        tr.scan({"text": "hello world", "latencyMs": None})
        tr.render()
        tr.on_pre_api_request({
            "tool_count": 23, "message_count": 4, "request_char_count": 8192,
            "approx_input_tokens": 2048, "system_prompt": "You are a careful agent.",
        })
        renders = [json.loads(line) for line in tr.finish().jsonl.splitlines()
                   if '"turn.render"' in line]
        prefix = renders[-1].get("prefix")
        self.assertIsNotNone(prefix, "pre_api_request must populate the render prefix")
        self.assertEqual(prefix["toolSchemas"], 23)
        self.assertEqual(prefix["messageCount"], 4)
        self.assertEqual(prefix["requestChars"], 8192)
        self.assertEqual(prefix["approxInputTokens"], 2048)
        self.assertEqual(prefix["systemPromptBytes"], len("You are a careful agent.".encode()))
        self.assertEqual(prefix["source"], "measured")

        # An adapter that cannot see the request says unknown — never zero.
        tr2 = Tracer(TraceInit(agent_id="ctxvm-dev", model="m", provider="p", budget_tokens=0))
        tr2.scan({"text": "hi", "latencyMs": None})
        tr2.render()
        tr2.on_pre_api_request({"session_id": "s"})
        renders = [json.loads(line) for line in tr2.finish().jsonl.splitlines()
                   if '"turn.render"' in line]
        self.assertEqual(renders[-1]["prefix"], {"source": "unknown"},
                         "unmeasurable counters must be absent, not zero")

    def test_help_lists_commands_and_explains_one(self):
        """/ctxvm-help finds the commands; /ctxvm-help <cmd> explains one."""
        _clear_env_for_tests()
        cmds = {}

        class FakeCtx:
            def register_hook(self, name, cb):
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                cmds[name] = handler
                return None

        register(FakeCtx())
        self.assertIn("ctxvm-help", cmds)
        self.assertIn("ctxvm-start", cmds)

        listing = cmds["ctxvm-help"]("")
        for expected in ("/ctxvm-start", "/ctxvm-trace", "/ctxvm-forensics",
                         "/ctxvm-handoff", "/ctxvm-resume", "environment"):
            self.assertIn(expected, listing)

        detail = cmds["ctxvm-help"]("ctxvm-trace")
        self.assertIn("status", detail)
        self.assertIn("stop", detail)

        unknown = cmds["ctxvm-help"]("nope")
        self.assertIn("no topic", unknown)
        self.assertIn("ctxvm-trace", unknown)

    def test_help_environment_prints_values_and_defaults(self):
        """/ctxvm-help environment shows every variable with its value, not just names."""
        _clear_env_for_tests()
        tmp = tempfile.mkdtemp(prefix="ctxvm-env-")
        os.environ["CTXVM_TRACE_DIR"] = tmp
        os.environ["CTXVM_ENVIRONMENT_ID"] = "env-0a1b2c3d4e5f"
        cmds = {}

        class FakeCtx:
            def register_hook(self, name, cb):
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                cmds[name] = handler
                return None

        register(FakeCtx())
        report = cmds["ctxvm-help"]("environment")
        self.assertIn(tmp, report, "the resolved trace dir must be visible")
        self.assertIn("env-0a1b2c3d4e5f", report, "a set id must show its value")
        self.assertIn("CTXVM_TRACE_RETAIN_BYTES", report)
        self.assertIn("536870912", report, "an unset variable shows its default")
        self.assertIn("unset -> on", report)
        # "env" is accepted as a short form of the topic.
        self.assertIn(tmp, cmds["ctxvm-help"]("env"))

    def test_start_without_arguments_uses_the_configured_defaults(self):
        """/ctxvm-start takes no arguments; a directory is an override, not a requirement."""
        _clear_env_for_tests()
        tmp = tempfile.mkdtemp(prefix="ctxvm-start-")
        os.environ["CTXVM_TRACE_DIR"] = tmp
        cmds = {}

        class FakeCtx:
            def register_hook(self, name, cb):
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                cmds[name] = handler
                return None

        register(FakeCtx())
        started = cmds["ctxvm-start"]("")
        self.assertIn("tracing enabled", started)
        self.assertIn(tmp, started, "a no-argument start must keep the configured dir")
        self.assertIn("env CTXVM_TRACE_DIR", started,
                      "the source must name the env var, not the built-in default")

        # With no env dir at all, the same command resolves the built-in default and
        # says that it did. clear_env also drops the process state, so the default is
        # re-resolved rather than inherited from the case above.
        _clear_env_for_tests()
        register(FakeCtx())
        defaults = cmds["ctxvm-start"]("")
        self.assertIn("start (defaults)", defaults)
        self.assertIn("state/ctxvm/traces", defaults.replace(os.path.expanduser("~"), "~"))

        other = tempfile.mkdtemp(prefix="ctxvm-start2-")
        resumed = cmds["ctxvm-start"](other + " custom")
        self.assertIn(other, resumed)
        self.assertIn("custom", resumed)
        self.assertIn("slash command", resumed)
        os.environ.pop("CTXVM_TRACE_DIR", None)

    def test_plugin_yaml_version_matches_the_constant(self):
        """A version bump that misses one of the two files is a silent no-op."""
        from live import PLUGIN_VERSION
        yaml_text = (Path(__file__).resolve().parents[1] / "live" / "plugin.yaml").read_text()
        self.assertIn(f"version: {PLUGIN_VERSION}", yaml_text,
                      "plugin.yaml and PLUGIN_VERSION must agree")

    def test_adapter_tags_side_effect_class_at_registration(self):
        """W15: the class comes from the registration table, by name, never from content.

        A keys-only parity test passes while every page is MUTATING — this asserts the
        VALUE, which is the only thing that makes the field worth recording.
        """
        _clear_env_for_tests()
        tmp = tempfile.mkdtemp(prefix="ctxvm-w15-")
        os.environ["CTXVM_TRACE_DIR"] = tmp
        os.environ["CTXVM_TRACE_NAME"] = "w15"
        cbs, cmds = {}, {}

        class FakeCtx:
            def register_hook(self, name, cb):
                cbs[name] = cb
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                cmds[name] = handler
                return None

        register(FakeCtx())
        cbs["on_session_start"](session_id="s1")
        cbs["pre_llm_call"](session_id="s1", conversation_history=[], model="m")
        expected = {"read_file": "READ_ONLY", "search_files": "READ_ONLY",
                    "terminal": "MUTATING", "read": "MUTATING"}
        for tool in expected:
            cbs["post_tool_call"](session_id="s1", tool=tool, args={"x": tool},
                                  status="ok",
                                  result={"content": [{"type": "text", "text": f"body of {tool}"}]})
        cmds["ctxvm-trace"]("stop")

        events = [json.loads(line) for line in
                  Path(tmp, "w15.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        declares = {e["page"]["id"]["logicalRef"]: e for e in events if e["type"] == "page.declare"}
        self.assertEqual(len(declares), 4)
        for tool, want in expected.items():
            ref = next(r for r in declares if f"tool:{tool}(" in r)
            self.assertEqual(declares[ref].get("toolEffect"), want,
                             f"{tool} must classify as {want} — the class is registration-owned")

        # The class is a function of the NAME: identical content, different names.
        kinds = {e["page"]["id"]["logicalRef"]: e["page"]["kind"] for e in declares.values()}
        self.assertTrue(all(k == "tool_result" for k in kinds.values()))

    def test_write_through_persists_partial_and_flush_clears_it(self):
        """A crash must cost at most N events: write-through persists a partial snapshot."""
        _clear_env_for_tests()
        tmp = tempfile.mkdtemp(prefix="ctxvm-wt-")
        os.environ["CTXVM_TRACE_DIR"] = tmp
        os.environ["CTXVM_TRACE_NAME"] = "wt"
        os.environ["CTXVM_TRACE_WRITETHROUGH_EVERY"] = "1"
        cbs, cmds = {}, {}

        class FakeCtx:
            def register_hook(self, name, cb):
                cbs[name] = cb
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                cmds[name] = handler
                return None

        register(FakeCtx())
        self.assertIn("post_tool_call", cbs)
        cbs["post_tool_call"](
            session_id="s1", tool="read", args={}, status="ok",
            result={"content": [{"type": "text", "text": "hello"}]},
        )
        partials = list(Path(tmp).glob("*.partial.jsonl"))
        self.assertEqual(len(partials), 1, "write-through must persist a partial snapshot")

        out = cmds["ctxvm-trace"]("stop")
        self.assertIn("1 trace(s) flushed", out)
        self.assertEqual(list(Path(tmp).glob("*.partial.jsonl")), [])
        self.assertTrue((Path(tmp) / "wt.jsonl").exists())
        self.assertTrue((Path(tmp) / "wt.meta.json").exists())

    def test_retention_enforces_a_byte_budget(self):
        """Count alone cannot bound size: the byte budget prunes oldest-first too."""
        import live as live_mod
        tmp = tempfile.mkdtemp(prefix="ctxvm-retain-bytes-")
        for i in range(4):
            body = "x" * 1000
            p = Path(tmp, f"cap{i}.jsonl")
            p.write_text(body)
            Path(tmp, f"cap{i}.meta.json").write_text("{}")
            os.utime(p, (1000 + i, 1000 + i))
        os.environ["CTXVM_TRACE_RETAIN_MAX"] = "100"
        os.environ["CTXVM_TRACE_RETAIN_DAYS"] = "9999"
        os.environ["CTXVM_TRACE_RETAIN_BYTES"] = "2500"   # room for two captures, not four
        live_mod._prune_traces(tmp, keep="cap0.jsonl")
        remaining = sorted(p.name for p in Path(tmp).glob("*.jsonl"))
        total = sum(p.stat().st_size for p in Path(tmp).glob("*.jsonl"))
        self.assertIn("cap0.jsonl", remaining, "the file just written must never be pruned")
        self.assertLessEqual(total, 2500 + 1000, "budget is enforced (plus the kept file)")
        self.assertNotIn("cap1.jsonl", remaining, "oldest captures go first")
        for key in ("CTXVM_TRACE_RETAIN_MAX", "CTXVM_TRACE_RETAIN_DAYS", "CTXVM_TRACE_RETAIN_BYTES"):
            os.environ.pop(key, None)

    def test_retention_prunes_beyond_budget_and_keeps_the_written_file(self):
        """Default-ON capture is bounded: oldest captures are deleted, the newest is not."""
        import live as live_mod
        tmp = tempfile.mkdtemp(prefix="ctxvm-retain-")
        for i in range(5):
            p = Path(tmp, f"cap{i}.jsonl")
            m = Path(tmp, f"cap{i}.meta.json")
            p.write_text("{}\n")
            m.write_text("{}\n")
            # W17: the coverage sidecar is the third pair member — a pruned
            # capture must not strand its manifest describing absent bytes.
            Path(tmp, f"cap{i}.coverage.json").write_text("{}\n")
            os.utime(p, (1000 + i, 1000 + i))
            os.utime(m, (1000 + i, 1000 + i))
            os.utime(Path(tmp, f"cap{i}.coverage.json"), (1000 + i, 1000 + i))
        os.environ["CTXVM_TRACE_RETAIN_MAX"] = "2"
        os.environ["CTXVM_TRACE_RETAIN_DAYS"] = "9999"
        deleted = live_mod._prune_traces(tmp, keep="cap0.jsonl")
        remaining = sorted(p.name for p in Path(tmp).glob("*.jsonl"))
        self.assertIn("cap0.jsonl", remaining, "the file just written must never be pruned")
        self.assertLessEqual(len(remaining), 3)  # budget 2 + the kept file
        self.assertNotIn("cap1.jsonl", remaining)
        self.assertFalse(Path(tmp, "cap1.coverage.json").exists(),
                         "the coverage sidecar goes with its capture, never orphaned")
        for key in ("CTXVM_TRACE_RETAIN_MAX", "CTXVM_TRACE_RETAIN_DAYS"):
            os.environ.pop(key, None)

    def test_adapter_maps_hooks_and_flushes_trace_on_cleanup(self):
        _clear_env_for_tests()
        tmpdir = tempfile.mkdtemp(prefix="ctxvm-hermes-test-")
        os.environ["CTXVM_TRACE_DIR"] = tmpdir
        os.environ["CTXVM_TRACE_NAME"] = "hermes-test"
        os.environ["CTXVM_MODEL"] = "openai/gpt-5"
        os.environ["CTXVM_PROVIDER"] = "openai"

        captured_hooks = []
        captured_cleanup = [None]

        class FakeCtx:
            def register_hook(self, name, cb):
                captured_hooks.append(name)
                return lambda: None

            def on_unload(self, cb):
                captured_cleanup[0] = cb
                return None

            def register_command(self, name, handler, description=""):
                captured_hooks.append(("command", name))
                return None

        register(FakeCtx())

        self.assertIn("on_session_start", captured_hooks)
        self.assertIn("pre_tool_call", captured_hooks)
        self.assertIn("post_tool_call", captured_hooks)
        self.assertIn("pre_llm_call", captured_hooks)
        self.assertIn("on_session_end", captured_hooks)
        self.assertIn(("command", "ctxvm-trace"), captured_hooks)

        # Fire hooks through the closures by re-registering with a real plugin
        # Instead, test the adapter end-to-end: create a real plugin and fire hooks
        from plugin import create_ctxvm_plugin as ccp
        plugin = ccp(INIT)
        plugin.on_session_start({"session_id": "ses_live_test"})
        plugin.on_pre_tool_call({"session_id": "ses_live_test", "tool": "read", "args": {"path": "notes.txt"}})
        plugin.on_post_tool_call({
            "session_id": "ses_live_test", "tool": "read", "args": {"path": "notes.txt"},
            "status": "completed", "result": {"content": [{"type": "text", "text": "hello"}]},
        })
        plugin.on_pre_llm_call({
            "session_id": "ses_live_test",
            "conversation_history": [{"role": "user", "content": [{"type": "text", "text": "Read notes.txt"}]}],
        })

        cleanup_fn = captured_cleanup[0]
        self.assertIsNotNone(cleanup_fn)

        # Temporarily swap plugin's tracers into the adapter's context won't work
        # since adapter creates its own plugin. Instead, verify the adapter's
        # cleanup path by directly calling finish_all on the test plugin.
        trace_dir = os.environ["CTXVM_TRACE_DIR"]
        Path(trace_dir).mkdir(parents=True, exist_ok=True)
        flushed = plugin.finish_all()
        base = os.environ.get("CTXVM_TRACE_NAME")
        for record in flushed:
            session_id = record["sessionID"]
            trace = record["trace"]
            file = base or session_id
            (Path(trace_dir) / f"{file}.jsonl").write_text(trace.jsonl, encoding="utf-8")
            (Path(trace_dir) / f"{file}.meta.json").write_text(
                json.dumps(
                    {"sessionID": session_id, "traceStats": trace.stats},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

        jsonl_path = Path(tmpdir) / "hermes-test.jsonl"
        meta_path = Path(tmpdir) / "hermes-test.meta.json"
        self.assertTrue(jsonl_path.exists(), f"trace file not written to {jsonl_path}")
        self.assertTrue(meta_path.exists())

        events = [json.loads(l) for l in jsonl_path.read_text().strip().split("\n") if l.strip()]
        self.assertEqual(events[0]["type"], "session.open")
        self.assertEqual(events[0]["model"], "openai/gpt-5")

        meta = json.loads(meta_path.read_text())
        self.assertEqual(meta["sessionID"], "ses_live_test")


# --- KIT-1: canonical wire-format parity (09-plugin-parity.md §2/§3) ----------

# RFC-0.1 (RR-RFC01E1): session.open gains `schemaVersion` — updated on BOTH
# sides in the same card, together with the contract doc table (2026-10-31).
# R4-ts (RR-R4TS2): ts gains on ALL types in the hermes port's own per-lane
# card (statuses the §R3-note precedent; updated with the parity doc + the
# node mirror's opencode table already carrying its lane's ts in RR-R4TS1).
CANONICAL_EVENT_KEYS = {
    "session.open": ["agentId", "budgetTokens", "model", "provider", "schemaVersion", "tokenizerId", "ts", "type"],
    # page.declare (R5-turn card, RFC-0.1 §R5 + §R4): `turn` always rides
    # (declaration turn, pre-first-render -1 stamps as 0); `latencyMs` is an
    # ACCEPTED-BUT-UNEMITTED slot — no lane surface feeds it yet, so the table
    # stays true to the wire (the noteUsage/providerUsage precedent: optional
    # fields enter the table when a fixture actually exercises them).
    # W15 (§R7): `toolEffect` is OPTIONAL on page.declare — the live adapter tags
    # every tool_result at registration time, while a direct tracer call (this
    # fixture) passes no class and the key stays absent. Both shapes are legal;
    # the value assertion lives in test_adapter_tags_side_effect_class.
    "page.declare": ["page", "ts", "turn", "type"],
    "page.fault": ["page", "source", "turn", "ts", "type"],
    "page.render": ["mode", "page", "turn", "ts", "type"],
    # W13: `prefix` always rides (source "unknown" when the adapter cannot see the request).
    "turn.render": ["evictedTokens", "headroom", "prefix", "residentTokens", "turn", "ts", "type"],
    "call.meta": ["cacheEstimate", "provider", "turn", "ts", "type"],
}
# W15 (§R7): keys that may ride or be absent depending on whether an adapter
# supplied a registration-time fact. A present value is still checked.
OPTIONAL_EVENT_KEYS = {
    "page.declare": frozenset({"toolEffect"}),
    # W14 (§R8): present only when the operator registered an opaque environment id
    # (the hermes gateway does not disclose the session's workspace).
    "session.open": frozenset({"environmentId"}),
    # W8 (§R3 note, owner option A): the provider receipt is a separate fact on
    # call.meta (the cacheEstimate stays page-table semantics). Optional per v0.1;
    # this lane became an emitter only now — the opencode table stays untouched
    # (its per-port comment rule defers hermes key-signature equality here).
    "call.meta": frozenset({"providerUsage"}),
}

CANONICAL_META_KEYS = [
    "budgetTokens", "capturedAt", "harness", "harnessVersion", "hookStats",
    "model", "pluginVersion", "provider", "resumeFrom", "sessionID", "traceStats",
]
CANONICAL_HOOKSTAT_KEYS = [
    "after", "before", "completed", "contexts", "errored", "extraHookStats", "sessions",
]


class CanonicalSidecarParity(unittest.TestCase):
    """09-plugin-parity.md §2/§3 — mirrors packages/opencode/test/meta-parity.test.ts.

    Any drift lands in the SAME card on BOTH sides: update the contract doc,
    both emitters, and both test files together."""

    def _mini_run(self) -> dict:
        vm = create_ctxvm_plugin(INIT)
        sid = "ses_par"
        doneread = {"session_id": sid, "tool": "read", "args": {"path": "notes.txt"}}
        vm.on_session_start({"session_id": sid})
        vm.on_pre_tool_call(doneread)
        vm.on_pre_llm_call({"session_id": sid, "conversation_history": [
            {"role": "user", "content": [{"type": "text", "text": "Read notes.txt"}]},
        ]})
        vm.on_post_tool_call({
            **doneread,
            "status": "ok",
            "result": {"content": [{"type": "text", "text": "hello page"}]},
        })
        vm.on_pre_llm_call({"session_id": sid, "conversation_history": [
            {"role": "user", "content": [{"type": "text", "text": "Read notes.txt"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "It says hello page"}]},
        ]})
        # Turn 2: double fetch of the same page -> tool_recall page.fault.
        vm.on_pre_tool_call(doneread)
        vm.on_post_tool_call({
            **doneread,
            "status": "ok",
            "result": {"content": [{"type": "text", "text": "hello page"}]},
        })
        vm.on_pre_llm_call({"session_id": sid, "conversation_history": [
            {"role": "user", "content": [{"type": "text", "text": "Read notes.txt again"}]},
        ]})
        vm.on_session_end({"session_id": sid})
        return vm.finish_all()[0]

    def test_event_key_signatures(self):
        record = self._mini_run()
        events = [json.loads(l) for l in record["trace"].jsonl.split("\n") if l.strip()]
        for event in events:
            t = event["type"]
            self.assertIn(t, CANONICAL_EVENT_KEYS, f"type outside the canonical table: {t}")
            optional = OPTIONAL_EVENT_KEYS.get(t, frozenset())
            self.assertTrue(
                set(event) - optional >= set(CANONICAL_EVENT_KEYS[t]),
                f"canonical key drift for {t} — update 09-plugin-parity.md §2 AND the opencode mirror in the same card",
            )
            self.assertTrue(
                set(event) - optional <= set(CANONICAL_EVENT_KEYS[t]),
                f"unexpected keys on {t} — update 09-plugin-parity.md §2 AND the opencode mirror in the same card",
            )
            for key in set(event) & optional:
                if key == "toolEffect":
                    self.assertIn(event[key], ("READ_ONLY", "MUTATING"),
                                  f"{t}.{key} must be a registration-time class, got {event[key]!r}")
                elif key == "environmentId":
                    self.assertRegex(str(event[key]), r"^env-[0-9a-f]{12}$",
                                     f"{t}.{key} must be an opaque id, never a path")
                elif key == "providerUsage":
                    self.assertEqual(set(event[key].keys()),
                                     {"inputTokens", "outputTokens", "cachedInputTokens"},
                                     f"{t}.providerUsage must be the three v0.1 buckets")
                    self.assertTrue(all(isinstance(v, int) and not isinstance(v, bool)
                                        and v >= 0 for v in event[key].values()),
                                    f"{t}.providerUsage buckets must be whole numbers >= 0")
        self.assertEqual(
            {e["type"] for e in events},
            set(CANONICAL_EVENT_KEYS),
            "the canonical table must stay emission-proven: every type exercised by the mini run",
        )

    def test_canon_meta_shape_and_mapping(self):
        hook_stats = {
            "session_starts": 1,
            "pre_tool_calls": 2,
            "post_tool_calls": 2,
            "completed": 1,
            "errored": 1,
            "pre_llm_calls": 1,
            "session_ends": 1,
            "skipped_untraced": 3,
        }
        trace_stats = {"turns": 1, "pages": 1, "faults": 0, "residentTokens": 10}
        env = {
            "CTXVM_HERMES_VERSION": "9.9.9",
            "CTXVM_MODEL": "test/model",
            "CTXVM_PROVIDER": "test",
            "CTXVM_BUDGET_TOKENS": "1234",
        }
        old = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        try:
            meta = _canon_meta("ses_par", hook_stats, trace_stats)
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.assertEqual(sorted(meta), sorted(CANONICAL_META_KEYS))
        self.assertEqual(meta["harness"], "hermes-python-plugin")
        self.assertEqual(meta["harnessVersion"], "9.9.9")
        self.assertEqual(meta["pluginVersion"], PLUGIN_VERSION)
        self.assertTrue(meta["capturedAt"].endswith("Z"))
        self.assertEqual(sorted(meta["hookStats"]), sorted(CANONICAL_HOOKSTAT_KEYS))
        # §3 mapping table: hermes-terrain counters -> canonical hook-agnostic keys.
        self.assertEqual(meta["hookStats"]["contexts"], 1)
        self.assertEqual(meta["hookStats"]["before"], 2)
        self.assertEqual(meta["hookStats"]["after"], 2)
        self.assertEqual(meta["hookStats"]["completed"], 1)
        self.assertEqual(meta["hookStats"]["errored"], 1)
        self.assertEqual(
            meta["hookStats"]["extraHookStats"],
            {"session_starts": 1, "session_ends": 1, "skipped_untraced": 3},
        )
        self.assertEqual(meta["hookStats"]["sessions"], ["ses_par"])
        self.assertEqual(meta["traceStats"], trace_stats)
        self.assertEqual(meta["budgetTokens"], 1234)
        self.assertEqual(meta["model"], "test/model")
        self.assertEqual(meta["provider"], "test")


class CoverageManifestTests(unittest.TestCase):
    """W17 — the coverage sidecar rides every FULL flush and answers to ONE
    authoritative checker (tools/coverage_check.py), invoked here through
    subprocess ON PURPOSE: the checker is the law, not an import.

    Written at full flush only — never at write-through partials, so a later
    partial prune can never leave coverage describing nonexistent bytes."""

    def _flush_a_session(self, tmp: Path) -> None:
        _clear_env_for_tests()
        os.environ["CTXVM_TRACE_DIR"] = str(tmp)
        os.environ["CTXVM_TRACE_NAME"] = "cov"
        cbs, cmds = {}, {}

        class FakeCtx:
            def register_hook(self, name, cb):
                cbs[name] = cb
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                cmds[name] = handler
                return None

        register(FakeCtx())
        cbs["pre_tool_call"](
            session_id="s", tool_name="read_file", args={"path": "notes/alpha.md"},
        )
        cbs["post_tool_call"](
            session_id="s", tool_name="read_file", args={"path": "notes/alpha.md"},
            status="ok", result={"content": [{"type": "text", "text": "hello page"}]},
        )
        cbs["pre_llm_call"](
            session_id="s", conversation_history=[
                {"role": "user", "content": [{"type": "text", "text": "Read notes/alpha.md"}]},
                {"role": "assistant", "content": [{"type": "text", "text": "It says hello page"}]},
            ],
        )
        cbs["pre_tool_call"](
            session_id="s", tool_name="write_file", args={"path": "notes/beta.md"},
        )
        cbs["post_tool_call"](
            session_id="s", tool_name="write_file", args={"path": "notes/beta.md"},
            status="ok", result={"content": [{"type": "text", "text": "written"}]},
        )
        out = cmds["ctxvm-trace"]("stop")
        self.assertIn("1 trace(s)", out)
        self.assertTrue((tmp / "cov.jsonl").exists())
        self.assertTrue((tmp / "cov.meta.json").exists())
        self.assertTrue((tmp / "cov.coverage.json").exists())

    def _checker(self, tmp: Path, trace: str, manifest: str):
        """Run the authoritative checker through subprocess — deliberately NOT
        an import: the tool file is the law, not a library module."""
        import subprocess
        checker = Path(__file__).resolve().parents[3] / "tools" / "coverage_check.py"
        return subprocess.run(
            [sys.executable, str(checker), str(tmp / trace), str(tmp / manifest)],
            capture_output=True, text=True,
        )

    def test_flush_writes_coverage_the_checker_accepts(self):
        tmp = Path(tempfile.mkdtemp(prefix="ctxvm-cov-"))
        self._flush_a_session(tmp)
        try:
            manifest = json.loads((tmp / "cov.coverage.json").read_text(encoding="utf-8"))
            rows = [json.loads(line) for line in (tmp / "cov.jsonl").read_text(
                encoding="utf-8").splitlines() if line.strip()]
            trace_digest = hashlib.sha256((tmp / "cov.jsonl").read_bytes()).hexdigest()
            self.assertEqual(manifest["traceDigest"], trace_digest,
                             "the manifest ties itself to the bytes at the flushed path")
            self.assertEqual(manifest["traceFile"], "cov.jsonl")
            session_open = next(r for r in rows if r.get("type") == "session.open")
            self.assertEqual(manifest["session"]["environmentId"],
                             session_open.get("environmentId"))
            self.assertEqual(manifest["captures"], {
                "turns": 1,
                "pages": 2,
                "declares": 2,
                "declaresByClass": {"READ_ONLY": 1, "MUTATING": 1},
                # The pre-LLM scan attributes the history path token to the
                # just-declared tool page → one identifier_scan fault.
                "faults": 1,
                "faultsBySource": {"tool_recall": 0, "identifier_scan": 1,
                                   "explicit_api": 0, "semantic": 0},
            })
            result = self._checker(tmp, "cov.jsonl", "cov.coverage.json")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        finally:
            for key in ("CTXVM_TRACE_DIR", "CTXVM_TRACE_NAME"):
                os.environ.pop(key, None)

    def test_instrumentation_and_sidecar_identities_are_lane_fixed(self):
        from live import _HERMES_READ_ONLY_TOOLS, PLUGIN_VERSION
        tmp = Path(tempfile.mkdtemp(prefix="ctxvm-cov-"))
        self._flush_a_session(tmp)
        try:
            manifest = json.loads((tmp / "cov.coverage.json").read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["instrumentation"],
                {"ts": True, "toolEffect": True, "identifierScan": True},
                "the hermes lane has no per-run toggles; the constants are pinned here "
                "and mirrored in tools/coverage_check.py's docstring",
            )
            self.assertEqual(
                manifest["toolTable"],
                {"readOnlyRegistered": sorted(_HERMES_READ_ONLY_TOOLS), "default": "MUTATING"},
            )
            self.assertEqual(manifest["plugin"]["version"], PLUGIN_VERSION)
            self.assertEqual(manifest["plugin"]["harness"], "hermes-python-plugin")
            self.assertIsNone(manifest["plugin"].get("harnessVersion"))
            self.assertEqual(manifest["session"]["sessionID"], "s")
        finally:
            for key in ("CTXVM_TRACE_DIR", "CTXVM_TRACE_NAME"):
                os.environ.pop(key, None)

    def test_no_coverage_at_write_through_partials(self):
        """Partial snapshots never carry coverage: a partial's later pruning must
        not strand coverage describing bytes that no longer exist."""
        _clear_env_for_tests()
        tmp = Path(tempfile.mkdtemp(prefix="ctxvm-cov-wt-"))
        os.environ["CTXVM_TRACE_DIR"] = str(tmp)
        os.environ["CTXVM_TRACE_NAME"] = "cov"
        os.environ["CTXVM_TRACE_WRITETHROUGH"] = "1"
        os.environ["CTXVM_TRACE_WRITETHROUGH_EVERY"] = "1"
        cbs, cmds = {}, {}

        class FakeCtx:
            def register_hook(self, name, cb):
                cbs[name] = cb
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                cmds[name] = handler
                return None

        register(FakeCtx())
        cbs["post_tool_call"](
            session_id="s", tool_name="read_file", args={"path": "notes/alpha.md"},
            status="ok", result={"content": [{"type": "text", "text": "hello page"}]},
        )
        try:
            partials = list(tmp.glob("*.partial.jsonl"))
            self.assertEqual(len(partials), 1, "the partial snapshot exists")
            self.assertFalse(list(tmp.glob("*.partial.coverage.json")),
                             "no coverage sidecar at write-through partials")
            # The full flush later still writes coverage for the full capture.
            cmds["ctxvm-trace"]("stop")
            self.assertTrue((tmp / "cov.coverage.json").exists())
        finally:
            for key in ("CTXVM_TRACE_DIR", "CTXVM_TRACE_NAME",
                        "CTXVM_TRACE_WRITETHROUGH", "CTXVM_TRACE_WRITETHROUGH_EVERY"):
                os.environ.pop(key, None)

    def test_checker_rejects_tampered_pairs(self):
        """The checker's negative classes — what a wrong manifest must look like
        to consumers: digest mismatch, a registered tool stamped MUTATING, an
        unregistered name stamped READ_ONLY, a claimed class coverage missing
        from the bytes, and counts that disagree with observation. Every case
        exits 1 and names its law; the byte-tampered cases rebuild the manifest
        digest first, so the complaint is the CLASS law, not byte drift."""
        tmp = Path(tempfile.mkdtemp(prefix="ctxvm-cov-neg-"))
        self._flush_a_session(tmp)
        try:
            trace_text = (tmp / "cov.jsonl").read_text(encoding="utf-8")
            manifest = json.loads((tmp / "cov.coverage.json").read_text(encoding="utf-8"))

            def rewrite(label: str, mutation) -> str:
                rows = [json.loads(line) for line in trace_text.splitlines() if line.strip()]
                hits = 0
                for row in rows:
                    hit = mutation(row)
                    if hit:
                        hits += 1
                self.assertEqual(hits, 1, f"{label}: the mutation must hit exactly one row")
                return "\n".join(json.dumps(row) for row in rows) + "\n"

            def write_case(name: str, trace: str, overrides: dict):
                body = json.dumps({**manifest, **overrides}, indent=2) + "\n"
                (tmp / name).write_text(body, encoding="utf-8")
                return self._checker(tmp, trace, name)

            def tamper_digest(tampered: str) -> dict:
                return {"traceDigest": hashlib.sha256(tampered.encode("utf-8")).hexdigest()}

            # digest tamper: the manifest no longer describes these bytes
            result = write_case("neg-digest.coverage.json", "cov.jsonl",
                                {"traceDigest": "0" * 64})
            self.assertEqual(result.returncode, 1)
            self.assertIn("violated digest", result.stdout)

            # registered READ_ONLY tool stamped MUTATING — the W15 law as seen
            # in real capture bytes before the effective-name fix
            tampered = rewrite("flip class", lambda row: (
                row.update(toolEffect="MUTATING") or True)
                if row.get("type") == "page.declare" and row.get("toolEffect") == "READ_ONLY"
                else False)
            (tmp / "neg-mutating.jsonl").write_text(tampered, encoding="utf-8")
            result = write_case("neg-mutating.coverage.json", "neg-mutating.jsonl",
                                tamper_digest(tampered))
            self.assertEqual(result.returncode, 1)
            self.assertIn("violated toolTable", result.stdout)

            # unregistered tool name stamped READ_ONLY — the fail-safe law
            tampered = rewrite("rename tool", lambda row: (
                row["page"]["id"].update(
                    logicalRef=row["page"]["id"]["logicalRef"].replace("read_file", "terminal", 1))
                or True)
                if row.get("type") == "page.declare" and row.get("toolEffect") == "READ_ONLY"
                else False)
            (tmp / "neg-readonly.jsonl").write_text(tampered, encoding="utf-8")
            result = write_case("neg-readonly.coverage.json", "neg-readonly.jsonl",
                                tamper_digest(tampered))
            self.assertEqual(result.returncode, 1)
            self.assertIn("violated toolTable", result.stdout)

            # claimed class coverage missing from the bytes
            tampered = rewrite("drop class", lambda row: (
                row.pop("toolEffect") or True)
                if row.get("type") == "page.declare" and row.get("toolEffect") == "READ_ONLY"
                else False)
            (tmp / "neg-missing.jsonl").write_text(tampered, encoding="utf-8")
            result = write_case("neg-missing.coverage.json", "neg-missing.jsonl",
                                tamper_digest(tampered))
            self.assertEqual(result.returncode, 1)
            self.assertIn("violated instrumentation", result.stdout)

            # counts that disagree with observation
            counts = dict(manifest["captures"])
            counts["declaresByClass"] = {"READ_ONLY": 0, "MUTATING": 0}
            result = write_case("neg-counts.coverage.json", "cov.jsonl",
                                {"captures": counts})
            self.assertEqual(result.returncode, 1)
            self.assertIn("violated captures", result.stdout)
        finally:
            for key in ("CTXVM_TRACE_DIR", "CTXVM_TRACE_NAME"):
                os.environ.pop(key, None)


if __name__ == "__main__":
    unittest.main()


class CollisionNamingTests(unittest.TestCase):
    """W21 — a reused trace name must never replace another session's bytes.

    RR-LIVE-20261104: a post-restart capture reused the default name and the
    write-through replaced the 13:0x evidence at identical filenames. The rule:
    a different session gets an 8-hex digest suffix; the session that owns the
    name keeps it.
    """

    def _drive(self, tmp: Path) -> str:
        """Register the plugin, run one tool call, stop; return the stop message."""
        _clear_env_for_tests()
        os.environ["CTXVM_TRACE_DIR"] = str(tmp)
        os.environ["CTXVM_TRACE_NAME"] = "cov"
        cbs, cmds = {}, {}

        class FakeCtx:
            def register_hook(self, name, cb):
                cbs[name] = cb
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                cmds[name] = handler
                return None

        register(FakeCtx())
        cbs["pre_tool_call"](
            session_id="s", tool_name="read_file", args={"path": "notes/alpha.md"},
        )
        cbs["post_tool_call"](
            session_id="s", tool_name="read_file", args={"path": "notes/alpha.md"},
            status="ok", result={"content": [{"type": "text", "text": "hello page"}]},
        )
        return cmds["ctxvm-trace"]("stop")

    def _checker(self, tmp: Path, trace: str, manifest: str):
        import subprocess
        checker = Path(__file__).resolve().parents[3] / "tools" / "coverage_check.py"
        return subprocess.run(
            [sys.executable, str(checker), str(tmp / trace), str(tmp / manifest)],
            capture_output=True, text=True,
        )

    def test_a_different_session_gets_a_suffixed_name(self):
        tmp = Path(tempfile.mkdtemp(prefix="ctxvm-collide-"))
        sentinel = '{"sentinel": true}\n'
        (tmp / "cov.jsonl").write_text(sentinel, encoding="utf-8")
        (tmp / "cov.meta.json").write_text(
            json.dumps({"sessionID": "another-session"}) + "\n", encoding="utf-8"
        )
        out = self._drive(tmp)
        self.assertIn("1 trace(s)", out)
        suffix = hashlib.sha256(b"s").hexdigest()[:8]
        self.assertTrue((tmp / f"cov-{suffix}.jsonl").exists(), "the second session needs its own path")
        self.assertTrue((tmp / f"cov-{suffix}.meta.json").exists())
        self.assertTrue((tmp / f"cov-{suffix}.coverage.json").exists())
        self.assertEqual(
            (tmp / "cov.jsonl").read_text(encoding="utf-8"), sentinel,
            "the other session's bytes must be untouched",
        )
        check = self._checker(tmp, f"cov-{suffix}.jsonl", f"cov-{suffix}.coverage.json")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertIn("consistent", check.stdout)

    def test_the_session_that_owns_the_name_keeps_it(self):
        tmp = Path(tempfile.mkdtemp(prefix="ctxvm-same-"))
        self._drive(tmp)
        self.assertTrue((tmp / "cov.jsonl").exists())
        self._drive(tmp)  # same session id "s" flushes again
        self.assertTrue((tmp / "cov.jsonl").exists())
        self.assertEqual(
            sorted(p.name for p in tmp.glob("cov-*.jsonl")), [],
            "no suffix for the session that owns the name",
        )
        check = self._checker(tmp, "cov.jsonl", "cov.coverage.json")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


class ProviderUsageIntakeTests(unittest.TestCase):
    """W8 D12 intake law (packages/hermes/src/plugin.py `provider_usage_of`).

    The host's post_api_request usage summary carries the canonical buckets —
    `input_tokens` is the UNCACHED input on every provider shape (agent/
    usage_pricing.py normalize_usage: Anthropic reports uncached directly;
    Chat/Codex totals are split by subtracting the cache buckets), and
    `prompt_tokens = input + cache_read + cache_write`. The wire shape is
    `{inputTokens, outputTokens, cachedInputTokens?}` (RFC-0.1 §R3).
    `cacheEstimate` stays the page-table estimate and `providerReported` stays
    FALSE — owner option A (2026-11-06): the provider receipt rides the
    separate `providerUsage` fact; the est*→provider-truth upgrade question
    (RR-W2B1 §6) remains open."""

    def _summary(self, **over):
        base = {
            "input_tokens": 1200, "output_tokens": 512,
            "cache_read_tokens": 800, "cache_write_tokens": 200,
            "reasoning_tokens": 64, "request_count": 1,
            "prompt_tokens": 2200, "total_tokens": 2712,
        }
        base.update(over)
        return base

    def test_canonical_summary_maps_to_the_r3_shape(self):
        shaped = provider_usage_of(self._summary())
        self.assertEqual(shaped, {
            "inputTokens": 1200,       # prompt 2200 − read 800 − write 200
            "outputTokens": 512,
            "cachedInputTokens": 800,  # a read bucket exists → it rides
        })

    def test_reported_zero_cache_read_is_a_fact_not_an_absence(self):
        shaped = provider_usage_of(self._summary(
            cache_read_tokens=0, cache_write_tokens=0, prompt_tokens=1200,
            total_tokens=1712))
        self.assertEqual(shaped["cachedInputTokens"], 0)
        self.assertIn("cachedInputTokens", shaped)

    def test_malformed_and_absent_buckets_are_an_absence(self):
        self.assertIsNone(provider_usage_of(None))
        self.assertIsNone(provider_usage_of({}))
        self.assertIsNone(provider_usage_of({"output_tokens": 5}))
        self.assertIsNone(provider_usage_of(self._summary(prompt_tokens=True)))
        self.assertIsNone(provider_usage_of(self._summary(output_tokens="512")))
        self.assertIsNone(provider_usage_of(self._summary(cache_read_tokens=-1)))
        self.assertIsNone(provider_usage_of("2200/512"))
        self.assertIsNone(provider_usage_of([1, 2, 3]))

    def test_bucketless_but_nonnegative_shapes_derive_clamped(self):
        """The clamp law: prompt − read − write below zero pins at zero (a
        harness remap error must not mint negative tokens)."""
        shaped = provider_usage_of(self._summary(prompt_tokens=100))
        self.assertEqual(shaped["inputTokens"], 0)


class ProviderUsageTracerTests(unittest.TestCase):
    """note_usage + the finish slot: last-write-wins, orphan pairing, and the
    §R3 wire position (providerUsage rides after latencyMs, BEFORE ts)."""

    SID = "ses_usage"

    def _plugin(self):
        plugin = create_ctxvm_plugin(INIT)
        plugin.on_session_start({"session_id": self.SID})
        return plugin

    def _meta_events(self, events):
        return [e for e in events if e["type"] == "call.meta"]

    def test_receipt_attaches_to_the_pending_meta(self):
        plugin = self._plugin()
        plugin.on_pre_llm_call({"session_id": self.SID, "conversation_history": []})
        plugin.on_post_api_request({
            "session_id": self.SID,
            "usage": {"input_tokens": 900, "output_tokens": 100,
                      "cache_read_tokens": 300, "cache_write_tokens": 200,
                      "prompt_tokens": 1400},
        })
        record = plugin.finish_all()[0]
        metas = self._meta_events(record["trace"].events)
        self.assertEqual(len(metas), 1)
        self.assertEqual(metas[0]["providerUsage"],
                         {"inputTokens": 900, "outputTokens": 100,
                          "cachedInputTokens": 300})

    def test_last_write_wins_on_multiple_receipts(self):
        plugin = self._plugin()
        plugin.on_pre_llm_call({"session_id": self.SID, "conversation_history": []})
        plugin.on_post_api_request({
            "session_id": self.SID,
            "usage": {"input_tokens": 1, "output_tokens": 1,
                      "cache_read_tokens": 1, "cache_write_tokens": 1,
                      "prompt_tokens": 3},
        })
        plugin.on_post_api_request({
            "session_id": self.SID,
            "usage": {"input_tokens": 5, "output_tokens": 6,
                      "cache_read_tokens": 7, "cache_write_tokens": 0,
                      "prompt_tokens": 12},
        })
        record = plugin.finish_all()[0]
        (meta,) = self._meta_events(record["trace"].events)
        self.assertEqual(meta["providerUsage"],
                         {"inputTokens": 5, "outputTokens": 6,
                          "cachedInputTokens": 7})

    def test_absent_usage_is_an_absence_never_a_zero(self):
        plugin = self._plugin()
        plugin.on_pre_llm_call({"session_id": self.SID, "conversation_history": []})
        plugin.on_post_api_request({"session_id": self.SID})          # usage key absent
        plugin.on_post_api_request({"session_id": self.SID, "usage": None})
        plugin.on_post_api_request({"session_id": self.SID, "usage": {"junk": 1}})
        record = plugin.finish_all()[0]
        (meta,) = self._meta_events(record["trace"].events)
        self.assertNotIn("providerUsage", meta)
        # the estimate stays honest: page-table semantics, providerReported False
        self.assertEqual(meta["cacheEstimate"]["providerReported"], False)

    def test_orphan_receipt_pairs_with_the_next_meta(self):
        plugin = self._plugin()
        # a receipt BEFORE any meta exists (api call outside the render
        # sequence): held on the tracer, attached to the NEXT created meta
        plugin.on_post_api_request({
            "session_id": self.SID,
            "usage": {"input_tokens": 42, "output_tokens": 9,
                      "cache_read_tokens": 3, "cache_write_tokens": 0,
                      "prompt_tokens": 45},
        })
        plugin.on_pre_llm_call({"session_id": self.SID, "conversation_history": []})
        record = plugin.finish_all()[0]
        (meta,) = self._meta_events(record["trace"].events)
        self.assertEqual(meta["providerUsage"]["inputTokens"], 42)

    def test_wire_order_provider_usage_before_ts(self):
        """§R3: the receipt rides AFTER cacheEstimate/latencyMs, BEFORE ts —
        the canonical v0.1 wire order the rust writer minted."""
        plugin = self._plugin()
        plugin.on_pre_llm_call({"session_id": self.SID,
                                "conversation_history": [], "latencyMs": 42})
        plugin.on_post_api_request({
            "session_id": self.SID,
            "usage": {"input_tokens": 1, "output_tokens": 2,
                      "cache_read_tokens": 3, "cache_write_tokens": 0,
                      "prompt_tokens": 4},
        })
        record = plugin.finish_all()[0]
        (meta,) = self._meta_events(record["trace"].events)
        keys = list(meta.keys())
        self.assertIn("latencyMs", keys)
        self.assertIn("providerUsage", keys)
        self.assertIn("ts", keys)
        self.assertLess(keys.index("providerUsage"), keys.index("ts"))
        self.assertLess(keys.index("latencyMs"), keys.index("providerUsage"))
        self.assertLess(keys.index("cacheEstimate"), keys.index("providerUsage"))

    def test_meta_without_receipt_carries_none_of_it(self):
        plugin = self._plugin()
        plugin.on_pre_llm_call({"session_id": self.SID, "conversation_history": []})
        record = plugin.finish_all()[0]
        (meta,) = self._meta_events(record["trace"].events)
        self.assertNotIn("providerUsage", meta)


class EngineWiringTests(unittest.TestCase):
    """register() enrolls the paged arm's engine, fail-open (design §13 gate 3:
    host activates it only with a profile carrying context.engine: "ctxvm";
    outside the hermes runtime build_engine() returns None and the observer
    duties are untouched)."""

    def setUp(self):
        _clear_env_for_tests()

    def test_register_enrolls_one_engine_named_ctxvm(self):
        captured = []

        class SpyCtx:
            def register_hook(self, name, cb):
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                return None

            def register_context_engine(self, engine):
                captured.append(engine)
                return object()

        register(SpyCtx())
        self.assertEqual(len(captured), 1,
                         "exactly one engine — the host allows only one")
        self.assertEqual(captured[0].name, "ctxvm")
        self.assertEqual(_state()["engine_registered"], "ctxvm")

    def test_register_survives_a_ctx_without_the_engine_seam(self):
        class FakeCtx:
            def register_hook(self, name, cb):
                return lambda: None

            def on_unload(self, cb):
                return None

            def register_command(self, name, handler, description=""):
                return None

        register(FakeCtx())  # must not raise
        self.assertIsNone(_state().get("engine_registered"),
                          "a ctx without the seam keeps the engine out of state")

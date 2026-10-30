#!/usr/bin/env python3
"""
Generate synthetic Hermes-captured traces for corpus/m3.

Mirrors the beat structure of corpus/m2 (T12):
  (a) echo session — read → re-read → edit → fresh read → missing file
  (b) sustained re-fetch pressure — 5 rounds × 5 files

Uses the Python tracer port (packages/hermes/src/plugin.py) to emit RFC-0
xCABI JSONL, then validates against the schema and replays with the Rust engine.

W4b B2 (2026-10-30, owner rider: "B2 queued immediately after W5"):
  - `make_live_shape_trace()` emits the LIVE Hermes v0.22.5 shapes the m3-era
    generator never exercised — history `content` as PLAIN STRINGS
    (agent/conversation_loop.py:350, oneshot.py:103), tool hooks under
    `tool_name`, `status: "ok"` results as plain strings. Its fixture
    (`hermes-live-echo-synthetic.jsonl`) is the standing proof that the
    identifier_scan surface fires on all-string history — a future parser
    regression of the B1 class (strings unread → scan dead) turns the suite
    red (test/test_generate_traces.py) instead of greening field runs as
    happened in m4/m7 (OBSERVABILITY.md F1).
  - The two LEGACY sessions (`make_echo_trace` / `make_thrash_trace`) keep
    their block-shaped history ON PURPOSE: they are the m3 corpus-drop
    sources (corpus/m3/checksums.sha256) and must stay byte-identical —
    main() refuses to overwrite them without --force, and
    test_generate_traces.py pins the byte parity against the drop.
"""

import argparse
import json
import sys
from pathlib import Path

_HERMES_SRC = str(Path(__file__).resolve().parents[1] / "src")
if _HERMES_SRC not in sys.path:
    sys.path.insert(0, _HERMES_SRC)

from plugin import create_ctxvm_plugin, TraceInit  # noqa: E402

INIT = {
    "agentId": "hermes",
    "model": "nvidia/nemotron-3.5-super-vl-120b-a12b",
    "provider": "nvidia",
    "budgetTokens": 120000,
}

# The W5 hermes capture's emitted session.open (RR-W5-20261030 D7): the CTXVM_*
# env block did not reach the hermes boot, so the live plugin emitted the
# unknown/unknown + default-budget placeholders. The live-shape fixture mirrors
# that reality instead of inventing fields the plugin had no evidence for.
INIT_LIVE = {
    "agentId": "hermes",
    "model": "unknown/unknown",
    "provider": "unknown",
    "budgetTokens": 200000,
}

# m3 drop sources (corpus/m3/checksums.sha256) — byte-frozen, guarded below.
FROZEN_FIXTURES = frozenset({
    "hermes-echo-synthetic.jsonl",
    "hermes-thrash-synthetic.jsonl",
})


def make_echo_trace() -> str:
    """Echo session: read → re-read → edit → fresh read → missing file."""
    plugin = create_ctxvm_plugin(INIT)
    sid = "ses_hermes_echo_synth"

    plugin.on_session_start({"session_id": sid})

    # Turn 0: first read of alpha.md
    plugin.on_pre_tool_call({"session_id": sid, "tool": "read_file", "args": {"path": "notes/alpha.md"}})
    plugin.on_post_tool_call({
        "session_id": sid, "tool": "read_file", "args": {"path": "notes/alpha.md"},
        "status": "completed",
        "result": {"content": [{"type": "text", "text": "test file for ctxvm capture"}]},
    })
    plugin.on_pre_llm_call({
        "session_id": sid,
        "conversation_history": [
            {"role": "user", "content": [{"type": "text", "text": "Read notes/alpha.md"}]},
        ],
    })

    # Turn 1: re-read alpha.md (double fetch → tool_recall)
    plugin.on_pre_tool_call({"session_id": sid, "tool": "read_file", "args": {"path": "notes/alpha.md"}})
    plugin.on_post_tool_call({
        "session_id": sid, "tool": "read_file", "args": {"path": "notes/alpha.md"},
        "status": "completed",
        "result": {"content": [{"type": "text", "text": "test file for ctxvm capture"}]},
    })
    plugin.on_pre_llm_call({
        "session_id": sid,
        "conversation_history": [
            {"role": "user", "content": [{"type": "text", "text": "Read notes/alpha.md again"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "It says test file for ctxvm capture"}]},
        ],
    })

    # Turn 2: edit alpha.md
    plugin.on_pre_tool_call({"session_id": sid, "tool": "edit", "args": {
        "path": "notes/alpha.md", "oldString": "capture", "newString": "capture echo-round-2"}})
    plugin.on_post_tool_call({
        "session_id": sid, "tool": "edit", "args": {
            "path": "notes/alpha.md", "oldString": "capture", "newString": "capture echo-round-2"},
        "status": "completed",
        "result": {"content": [{"type": "text", "text": "Edited"}]},
    })
    plugin.on_pre_llm_call({
        "session_id": sid,
        "conversation_history": [
            {"role": "user", "content": [{"type": "text", "text": "Edit notes/alpha.md"}]},
        ],
    })

    # Turn 3: fresh read (new contentHash → new declare, no fault)
    plugin.on_pre_tool_call({"session_id": sid, "tool": "read_file", "args": {"path": "notes/alpha.md"}})
    plugin.on_post_tool_call({
        "session_id": sid, "tool": "read_file", "args": {"path": "notes/alpha.md"},
        "status": "completed",
        "result": {"content": [{"type": "text", "text": "test file for ctxvm capture echo-round-2"}]},
    })
    plugin.on_pre_llm_call({
        "session_id": sid,
        "conversation_history": [
            {"role": "user", "content": [{"type": "text", "text": "Read notes/alpha.md after edit"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "Edited alpha.md"}]},
        ],
    })

    # Turn 4: missing file (error → no page)
    plugin.on_pre_tool_call({"session_id": sid, "tool": "read_file", "args": {"path": "notes/missing.md"}})
    plugin.on_post_tool_call({
        "session_id": sid, "tool": "read_file", "args": {"path": "notes/missing.md"},
        "status": "error", "error": {"code": "ENOENT"},
    })
    plugin.on_pre_llm_call({
        "session_id": sid,
        "conversation_history": [
            {"role": "user", "content": [{"type": "text", "text": "Read notes/missing.md"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "File not found"}]},
        ],
    })

    record = plugin.finish_all()[0]
    return record["trace"].jsonl, record["trace"].stats


def make_thrash_trace() -> str:
    """Thrash session: 5 rounds × 5 files re-read (sustained re-fetch pressure)."""
    plugin = create_ctxvm_plugin(INIT)
    sid = "ses_hermes_thrash_synth"

    plugin.on_session_start({"session_id": sid})

    files = ["data/f1.txt", "data/f2.txt", "data/f3.txt", "data/f4.txt", "data/f5.txt"]
    contents = ["alpha content one", "beta content two", "gamma content three",
                "delta content four", "epsilon content five"]

    for round_num in range(5):
        for i, path in enumerate(files):
            plugin.on_pre_tool_call({"session_id": sid, "tool": "read_file", "args": {"path": path}})
            plugin.on_post_tool_call({
                "session_id": sid, "tool": "read_file", "args": {"path": path},
                "status": "completed",
                "result": {"content": [{"type": "text", "text": contents[i]}]},
            })
        plugin.on_pre_llm_call({
            "session_id": sid,
            "conversation_history": [
                {"role": "user", "content": [{"type": "text", "text": f"Round {round_num + 1}: re-read all files"}]},
                {"role": "assistant", "content": [{"type": "text", "text": f"Round {round_num + 1} complete"}]},
            ],
        })

    record = plugin.finish_all()[0]
    return record["trace"].jsonl, record["trace"].stats


def live_message(role: str, text: str) -> dict:
    """One LIVE Hermes message: `content` is a PLAIN STRING.

    Hermes v0.22.5 appends assistant/user messages with string content
    (agent/conversation_loop.py:350, oneshot.py:103) — the exact shape the
    m3-era generator never produced, which is why every fixture was green
    while the live scan was dead (OBSERVABILITY.md F1 → W4b B1/B2).
    """
    return {"role": role, "content": text}


def make_live_shape_trace():
    """The m3 echo beats, through the LIVE shapes (all-string content,
    `tool_name` hooks, `"ok"` status results as plain strings — the W5-observed
    reality, RR-W5-20261030 §5 D4/D7).

    Returns (jsonl, stats, history): the history is returned precisely so
    test_generate_traces.py can audit the SHAPES the emitter feeds — a drop of
    that audit is how the B1-class defect escaped the m2/m3 suite.
    """
    plugin = create_ctxvm_plugin(INIT_LIVE)
    sid = "ses_hermes_live_synth"

    history = []
    plugin.on_session_start({"session_id": sid})

    def beat(history_lines, tool_payloads=()):
        """One user turn: tool pair(s) first, then the boundary pre_llm.

        Mirrors live ordering (RR-W5 hooks-witness: tools run inside the user
        turn; `pre_llm_call` is the turn boundary that carries the history).
        """
        for payload_type, payload in tool_payloads:
            if payload_type == "pre":
                plugin.on_pre_tool_call(payload)
            else:
                plugin.on_post_tool_call(payload)
        turn_history = [live_message(role, text) for role, text in history_lines]
        history.extend(turn_history)
        plugin.on_pre_llm_call({"session_id": sid, "conversation_history": turn_history})

    # Turn 0: first read of alpha.md (scan fires: the user text names the file
    # and the page is newly declared — same as frozen echo's turn 0).
    beat(
        [("user", "Read notes/alpha.md")],
        [
            ("pre", {"session_id": sid, "tool_name": "read_file", "args": {"path": "notes/alpha.md"}}),
            ("post", {"session_id": sid, "tool_name": "read_file", "args": {"path": "notes/alpha.md"},
                      "status": "ok", "result": "test file for ctxvm capture"}),
        ],
    )

    # Turn 1: re-read (double fetch → tool_recall) + history mentions the file
    # again → second identifier_scan, exactly the frozen echo composition.
    beat(
        [("user", "Read notes/alpha.md again"),
         ("assistant", "It says test file for ctxvm capture")],
        [
            ("pre", {"session_id": sid, "tool_name": "read_file", "args": {"path": "notes/alpha.md"}}),
            ("post", {"session_id": sid, "tool_name": "read_file", "args": {"path": "notes/alpha.md"},
                      "status": "ok", "result": "test file for ctxvm capture"}),
        ],
    )

    # Turn 2: edit alpha.md
    beat(
        [("user", "Edit notes/alpha.md")],
        [
            ("pre", {"session_id": sid, "tool_name": "edit",
                     "args": {"path": "notes/alpha.md", "oldString": "capture", "newString": "capture echo-round-2"}}),
            ("post", {"session_id": sid, "tool_name": "edit",
                      "args": {"path": "notes/alpha.md", "oldString": "capture", "newString": "capture echo-round-2"},
                      "status": "ok", "result": "Edited"}),
        ],
    )

    # Turn 3: fresh read after edit (new contentHash → new declare, no fault)
    beat(
        [("user", "Read notes/alpha.md after edit"),
         ("assistant", "Edited alpha.md")],
        [
            ("pre", {"session_id": sid, "tool_name": "read_file", "args": {"path": "notes/alpha.md"}}),
            ("post", {"session_id": sid, "tool_name": "read_file", "args": {"path": "notes/alpha.md"},
                      "status": "ok", "result": "test file for ctxvm capture echo-round-2"}),
        ],
    )

    # Turn 4: missing file (error → no page)
    beat(
        [("user", "Read notes/missing.md"),
         ("assistant", "File not found")],
        [
            ("pre", {"session_id": sid, "tool_name": "read_file", "args": {"path": "notes/missing.md"}}),
            ("post", {"session_id": sid, "tool_name": "read_file", "args": {"path": "notes/missing.md"},
                      "status": "error", "error": {"code": "ENOENT"}}),
        ],
    )

    # Live-shape self-checks BEFORE returning: a generator run must not be
    # able to emit a trace that would green a dead scan.
    finished = plugin.finish_all()[0]
    jsonl, stats = finished["trace"].jsonl, finished["trace"].stats
    assert all(msg["content"] and isinstance(msg["content"], str) for msg in history), \
        "live-shape generator regression: history lost the plain-string shape"
    scans = sum(1 for line in jsonl.splitlines()
                if json.loads(line).get("type") == "page.fault"
                and json.loads(line).get("source") == "identifier_scan")
    assert scans >= 1, "live-shape generator regression: identifier_scan silent on string history (B1-class death)"
    if stats["turns"] != 5 or stats["pages"] != 3:
        raise RuntimeError(f"live-shape echo beat structure drifted: {stats}")
    return jsonl, stats, history


def _write_fixture(path: Path, content: str, force: bool = False) -> bool:
    """Write a fixture file — refusing frozen m3 drop sources without force.

    corpus/m3/checksums.sha256 pinned these bytes at the drop; regenerating
    them would orphan the checksums while the repo still claims parity.
    """
    if path.exists() and path.name in FROZEN_FIXTURES and not force:
        raise RuntimeError(
            f"{path.name} is an m3 drop source (corpus/m3/checksums.sha256) — "
            f"regenerating would break frozen provenance; pass force to override"
        )
    path.write_text(content, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting the frozen m3 drop sources")
    args = parser.parse_args()

    out_dir = Path(__file__).resolve().parents[1] / "fixtures"
    out_dir.mkdir(parents=True, exist_ok=True)

    echo_jsonl, echo_stats = make_echo_trace()
    echo_path = out_dir / "hermes-echo-synthetic.jsonl"
    try:
        _write_fixture(echo_path, echo_jsonl, force=args.force)
    except RuntimeError as exc:
        print(f"echo: SKIPPED ({exc})")
    else:
        print(f"echo: {echo_path} — {echo_stats['turns']} turns, {echo_stats['pages']} pages, {echo_stats['faults']} faults")

    thrash_jsonl, thrash_stats = make_thrash_trace()
    thrash_path = out_dir / "hermes-thrash-synthetic.jsonl"
    try:
        _write_fixture(thrash_path, thrash_jsonl, force=args.force)
    except RuntimeError as exc:
        print(f"thrash: SKIPPED ({exc})")
    else:
        print(f"thrash: {thrash_path} — {thrash_stats['turns']} turns, {thrash_stats['pages']} pages, {thrash_stats['faults']} faults")

    live_jsonl, live_stats, _history = make_live_shape_trace()
    live_path = out_dir / "hermes-live-echo-synthetic.jsonl"
    _write_fixture(live_path, live_jsonl)
    print(f"live-echo: {live_path} — {live_stats['turns']} turns, {live_stats['pages']} pages, {live_stats['faults']} faults")


if __name__ == "__main__":
    main()

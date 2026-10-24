#!/usr/bin/env python3
"""
Generate synthetic Hermes-captured traces for corpus/m3.

Mirrors the beat structure of corpus/m2 (T12):
  (a) echo session — read → re-read → edit → fresh read → missing file
  (b) sustained re-fetch pressure — 5 rounds × 5 files

Uses the Python tracer port (packages/hermes/src/plugin.py) to emit RFC-0
xCABI JSONL, then validates against the schema and replays with the Rust engine.
"""

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


def main():
    out_dir = Path(__file__).resolve().parents[1] / "fixtures"
    out_dir.mkdir(parents=True, exist_ok=True)

    echo_jsonl, echo_stats = make_echo_trace()
    echo_path = out_dir / "hermes-echo-synthetic.jsonl"
    echo_path.write_text(echo_jsonl, encoding="utf-8")
    print(f"echo: {echo_path} — {echo_stats['turns']} turns, {echo_stats['pages']} pages, {echo_stats['faults']} faults")

    thrash_jsonl, thrash_stats = make_thrash_trace()
    thrash_path = out_dir / "hermes-thrash-synthetic.jsonl"
    thrash_path.write_text(thrash_jsonl, encoding="utf-8")
    print(f"thrash: {thrash_path} — {thrash_stats['turns']} turns, {thrash_stats['pages']} pages, {thrash_stats['faults']} faults")


if __name__ == "__main__":
    main()

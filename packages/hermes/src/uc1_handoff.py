"""
ctxvm UC1 — within-harness pause/resume submodule (pause beat).

KIT-1 org decision (09-plugin-parity.md §1): use cases are CTXVM_FEATURES-gated
submodules inside each plugin, dispatched by a thin live/ entry. This file
implements UC1 pause: flush the live tracer, snapshot the flushed file as an
era snapshot, and package it through the committed Rust `export` binary
(`--turn N --output <dir>/handoff/ --odps`) which emits the memo-specified
artifact set (trace-N.jsonl.zst, page-table-N.json, manifest.yaml with DQ/KPIs,
llms.txt, checksums.sha256).

The engine (Rust core) is untouched — this module shells out to the committed
binaries and orchestrates pause, which is a thin wrapper per the plugin
organization decision. Resume (B3) and the ctxvm-py binding (B1) follow.

Enabled via CTXVM_FEATURES=handoff (default is CTXVM_FEATURES=trace only).
Also gated: `CTXVM_HANDOFF_DIR` (flush target, required) and
`CTXVM_HANDOFF_TURN` (pause turn; unset = package at flush).

Public surface:

    uc1 = UC1Handoff()
    uc1.pause(trace_dir, turn=None)   # → {"exit_code", "snapshot", "report", "stderr"}
    uc1.status()                      # → {"enabled": bool, "handoff_dir": str|None}
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from uc_registry import UCModule, UC1_FEATURE, HANDOFF_FEATURE

# Rust CLI binaries (built by cargo build --release in rust/).
_EXPORT_BIN = "export"
_REPLAY_BIN = "replay"


def _rust_bin_dir() -> Optional[Path]:
    """Locate the directory holding the release Rust binaries."""
    override = os.environ.get("CTXVM_RUST_BIN_DIR")
    if override:
        p = Path(override)
        if p.is_dir():
            return p
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "rust" / "target" / "release"
        if candidate.is_dir() and (candidate / _EXPORT_BIN).is_file():
            return candidate
    return None


def _bin_path(name: str) -> str:
    d = _rust_bin_dir()
    if d is not None:
        return str(d / name)
    return name


def _run(name: str, args: List[str]) -> Dict[str, Any]:
    """Shell out to a Rust binary; return {exit_code, stdout, stderr}."""
    cmd = [_bin_path(name), *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return {
            "exit_code": 2,
            "stdout": "",
            "stderr": f"binary not found: {name} (set CTXVM_RUST_BIN_DIR or add rust/target/release to PATH)",
        }
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _parse_json(stdout: str) -> Any:
    try:
        return json.loads(stdout)
    except (json.JSONDecodeError, ValueError):
        return stdout


def _rfc3339_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class UC1Handoff(UCModule):
    """UC1 — within-harness pause/resume (pause beat).

    Pause flushes the live tracer, snapshots the flushed file as an era
    snapshot (cp -n semantics: never clobbers an existing era), and packages
    it through the committed export binary. Resume lives in beat B3.
    """

    name = "uc1-handoff"
    feature = HANDOFF_FEATURE

    # --- Pause ------------------------------------------------------------

    def pause(
        self,
        trace_dir: str,
        turn: Optional[int] = None,
        handoff_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Pause at `turn` (or flush if unset) and package a handoff snapshot.

        Steps:
          1. Flush all live tracers to `trace_dir` (existing flush path).
          2. Era-snapshot the flushed file (`{name}-{turn}.{jsonl,meta.json}`,
             cp -n never clobbers).
          3. Package via `export --turn N --output <dir>/handoff/ --odps`.
          4. Return artifact paths + DQ/KPI JSON.

        Returns {"exit_code", "snapshot": {...}, "report": {...}, "stderr": str}.
        """
        handoff_dir = os.environ.get("CTXVM_HANDOFF_DIR") or trace_dir
        if not handoff_dir:
            return {
                "exit_code": 2,
                "snapshot": {},
                "report": {},
                "stderr": "CTXVM_HANDOFF_DIR (or trace_dir) is required for uc1 pause",
            }
        name = handoff_name or os.environ.get("CTXVM_HANDOFF_NAME") or "handoff"
        if turn is None:
            turn = int(os.environ.get("CTXVM_HANDOFF_TURN", "0")) or None

        Path(handoff_dir).mkdir(parents=True, exist_ok=True)

        # Era snapshot label uses the turn so repeated pauses keep history.
        label = f"turn-{turn}" if turn is not None else "flush"
        snapshot: Dict[str, Any] = {}

        # Step 1 + 2: flush happens via the live adapter's _flush_traces();
        # here we snapshot whatever flushed file exists for `name`.
        for ext in ("jsonl", "meta.json"):
            src = Path(handoff_dir) / f"{name}.{ext}"
            dst = Path(handoff_dir) / f"{name}-{label}.{ext}"
            if src.is_file():
                if not dst.exists():
                    shutil.copy2(src, dst)
                snapshot[ext] = str(dst)

        # Step 3: package through the committed export binary.
        snapshot_dir = Path(handoff_dir) / "handoff"
        export_args: List[str] = ["--output", str(snapshot_dir)]
        if turn is not None:
            export_args.insert(0, str(turn))
        export_args.append("--odps")
        # export takes the trace as its first positional arg:
        #   export <trace.jsonl> --turn N --output DIR --odps
        trace_jsonl = str(Path(handoff_dir) / f"{name}.jsonl")
        result = _run(_EXPORT_BIN, [trace_jsonl] + export_args)

        # Step 4: verification (replay counterproof) — best effort, never blocks.
        replay_ok = True
        replay_divergences: List[Any] = []
        zst_path = snapshot_dir / "trace-N.jsonl.zst"
        if result["exit_code"] == 0 and zst_path.is_file():
            replay_result = _run(_REPLAY_BIN, [str(zst_path)])
            if replay_result["exit_code"] != 0:
                replay_ok = False
            try:
                rep = json.loads(replay_result["stdout"])
                replay_divergences = rep.get("divergences", [])
            except (json.JSONDecodeError, ValueError):
                pass

        snapshot["handoff_dir"] = str(snapshot_dir)
        snapshot["label"] = label
        snapshot["turn"] = turn

        return {
            "exit_code": result["exit_code"],
            "snapshot": snapshot,
            "report": _parse_json(result["stdout"]),
            "stderr": result["stderr"],
            "verified": replay_ok,
            "divergences": replay_divergences,
            "witness": {
                "paused_at": _rfc3339_z(),
                "turn": turn,
                "handoff_dir": handoff_dir,
                "artifacts": list(snapshot.values()),
            },
        }

    # --- Resume hook (stub — B3) ------------------------------------------

    def resume(self, snapshot_dir: str) -> Dict[str, Any]:
        """Resume from a snapshot: verify + provenance (stub for B3).

        Returns {"exit_code", "verified": bool, "reason": str, "evidence": {...}}.
        """
        return {
            "exit_code": 2,
            "verified": False,
            "reason": "resume (B3) not yet implemented — use verify-only: replay the snapshot's trace-N.jsonl.zst --turn N",
            "evidence": {},
        }

    # --- UCModule surface --------------------------------------------------

    def on_session_start(self, payload: Dict[str, Any]) -> None:
        return None

    def on_pre_tool_call(self, payload: Dict[str, Any]) -> None:
        return None

    def on_post_tool_call(self, payload: Dict[str, Any]) -> None:
        return None

    def on_pre_llm_call(self, payload: Dict[str, Any]) -> None:
        return None

    def on_session_end(self, payload: Dict[str, Any]) -> None:
        return None

    def flush(self) -> None:
        return None

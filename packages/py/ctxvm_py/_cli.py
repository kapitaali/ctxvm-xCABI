"""ctxvm-py internal CLI wrapper — subprocess calls to the Rust binaries."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


def _rust_bin_dir() -> Optional[Path]:
    """Locate the directory holding the release Rust binaries.

    Order:
      1. CTXVM_RUST_BIN_DIR env override
      2. rust/target/release/ relative to the repo root (found by walking up
         from this file: packages/py/ctxvm_py/_cli.py → repo root)
      3. None → fall back to PATH
    """
    override = os.environ.get("CTXVM_RUST_BIN_DIR")
    if override:
        p = Path(override)
        if p.is_dir():
            return p
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "rust" / "target" / "release"
        if candidate.is_dir() and (candidate / "replay").is_file():
            return candidate
    return None


def _bin_path(name: str) -> str:
    """Return the path (or bare name, for PATH lookup) of a Rust binary."""
    d = _rust_bin_dir()
    if d is not None:
        return str(d / name)
    return name


def _run(name: str, args: List[str]) -> Dict[str, Any]:
    """Shell out to a Rust binary and return its parsed stdout JSON.

    Raises RuntimeError on non-zero exit (with stderr attached).
    """
    cmd = [_bin_path(name), *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        raise RuntimeError(
            f"ctxvm {name} binary not found "
            f"(set CTXVM_RUST_BIN_DIR or add rust/target/release to PATH)"
        )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ctxvm {name} failed (exit {proc.returncode}): "
            f"{proc.stderr.strip()}"
        )
    try:
        return json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        return {"raw": proc.stdout}


def replay(
    trace: str,
    turn: Optional[int] = None,
    pins: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Run `ctxvm replay <trace> [--turn N] [--pin ...]`.

    Returns the parsed JSON report (or a ``{"raw": ...}`` dict when the binary
    emitted non-JSON).
    """
    args: List[str] = [trace]
    if turn is not None:
        args.extend(["--turn", str(turn)])
    for pin in pins or []:
        args.extend(["--pin", pin])
    return _run("replay", args)


def profile(
    trace: str,
    events: Optional[List[str]] = None,
    turns: Optional[str] = None,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """Run `ctxvm profile <trace> [--event <type>]... [--turns spec] [--source <src>]`.

    Returns the parsed JSON report.
    """
    args: List[str] = [trace]
    for event in events or []:
        args.extend(["--event", event])
    if turns:
        args.extend(["--turns", turns])
    if source:
        args.extend(["--source", source])
    return _run("profile", args)


def diff(a: str, b: str) -> Dict[str, Any]:
    """Run `ctxvm diff <a.jsonl> <b.jsonl>`.

    Returns the parsed JSON report.
    """
    return _run("diff", [a, b])


def export(
    trace: str,
    turn: Optional[int] = None,
    output_dir: Optional[str] = None,
    odps: bool = False,
) -> Dict[str, Any]:
    """Run `ctxvm export <trace> [--turn N] [--output DIR] [--odps]`.

    Returns the parsed JSON report (the `--output DIR` artifacts are written
    to output_dir).
    """
    args: List[str] = [trace]
    if turn is not None:
        args.extend(["--turn", str(turn)])
    if output_dir:
        args.extend(["--output", output_dir])
    if odps:
        args.append("--odps")
    return _run("export", args)


def build_handoff_snapshot(trace: str, turn: int, output_dir: str) -> Dict[str, Any]:
    """Package a turn-N handoff snapshot via `export --turn N --output DIR --odps`.

    Writes artifacts under ``output_dir`` and returns the parsed export report.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    args = [trace, "--turn", str(turn), "--output", output_dir, "--odps"]
    return _run("export", args)

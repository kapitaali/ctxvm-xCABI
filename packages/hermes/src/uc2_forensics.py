"""
ctxvm UC2 — in-harness forensics surface (memo-UC2).

KIT-1 org decision (09-plugin-parity.md §1): use cases are CTXVM_FEATURES-gated
submodules inside each plugin, dispatched by a thin live/ entry. This file
implements UC2 forensics — thin per-port wrappers around the committed Rust CLI
binaries (`replay`, `profile`, `diff`, `export`) plus the verdict decomposition
that separates context-management faults from model reasoning faults.

The engine (Rust core) is untouched. This module only shells out to the
already-built binaries and interprets their JSON output for the harness user.

Enabled via CTXVM_FEATURES=uc2-forensics (default is CTXVM_FEATURES=trace only).

Public surface:

    uc2 = UC2Forensics()
    uc2.replay(trace, turn=N, pins=[...], output=FILE)   # → parsed JSON report
    uc2.profile(trace, event="page.fault", source="tool_recall")  # → parsed JSON
    uc2.diff(a, b, output=FILE)                               # → parsed JSON
    uc2.export(trace, turn=N, output=DIR, odps=True)         # → {"snapshot": ...}
    uc2.diagnose(trace, fault_turn)                           # → verdict dict

Verdict decomposition (UC2 §3 Phase 3–4):

    context-management fault   — a page the model needed was evicted before
                                 the fault turn (replay proves visibility loss)
    model reasoning fault      — the page was resident at the fault turn;
                                 the pager is not at fault
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from uc_registry import UCModule, UC2_FEATURE

# Binary names as built by `cargo build --release` in rust/.
_BINARIES = ("replay", "profile", "diff", "export")


def _rust_bin_dir() -> Optional[Path]:
    """Locate the directory holding the release Rust binaries.

    Order:
      1. CTXVM_RUST_BIN_DIR env override
      2. rust/target/release/ relative to the repo root (found by walking up
         from this file: packages/hermes/src/ → repo root)
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


def _run(name: str, args: Sequence[str]) -> Dict[str, Any]:
    """Shell out to a Rust binary and return {exit_code, stdout, stderr}."""
    cmd = [_bin_path(name), *args]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
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
    """Best-effort JSON parse of stdout; returns raw string on failure."""
    try:
        return json.loads(stdout)
    except (json.JSONDecodeError, ValueError):
        return stdout


class UC2Forensics(UCModule):
    """UC2 — in-harness forensics surface.

    Thin wrapper around the committed Rust CLI binaries plus verdict
    decomposition. All methods return dicts parsed from the binary's JSON
    output (or the raw string if the binary emitted non-JSON).
    """

    name = "uc2-forensics"
    feature = UC2_FEATURE

    # --- CLI wrappers -----------------------------------------------------

    def replay(
        self,
        trace: str,
        turn: Optional[int] = None,
        pins: Optional[List[str]] = None,
        output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run `ctxvm replay <trace> [--turn N] [--pin ...] [--output FILE]`.

        Returns {"exit_code": int, "report": <parsed JSON | str>, "stderr": str}.
        """
        args: List[str] = [trace]
        if turn is not None:
            args.extend(["--turn", str(turn)])
        if pins:
            for pin in pins:
                args.extend(["--pin", pin])
        if output:
            args.extend(["--output", output])
        result = _run("replay", args)
        return {
            "exit_code": result["exit_code"],
            "report": _parse_json(result["stdout"]),
            "stderr": result["stderr"],
        }

    def profile(
        self,
        trace: str,
        events: Optional[List[str]] = None,
        turns: Optional[str] = None,
        source: Optional[str] = None,
        output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run `ctxvm profile <trace> [--event <type>]... [--turns spec] [--source <src>] [--output FILE]`.

        Returns {"exit_code": int, "report": <parsed JSON | str>, "stderr": str}.
        """
        args: List[str] = [trace]
        if events:
            for event in events:
                args.extend(["--event", event])
        if turns:
            args.extend(["--turns", turns])
        if source:
            args.extend(["--source", source])
        if output:
            args.extend(["--output", output])
        result = _run("profile", args)
        return {
            "exit_code": result["exit_code"],
            "report": _parse_json(result["stdout"]),
            "stderr": result["stderr"],
        }

    def diff(self, a: str, b: str, output: Optional[str] = None) -> Dict[str, Any]:
        """Run `ctxvm diff <a.jsonl> <b.jsonl> [--output FILE]`.

        Returns {"exit_code": int, "report": <parsed JSON | str>, "stderr": str}.
        """
        args: List[str] = [a, b]
        if output:
            args.extend(["--output", output])
        result = _run("diff", args)
        return {
            "exit_code": result["exit_code"],
            "report": _parse_json(result["stdout"]),
            "stderr": result["stderr"],
        }

    def export(
        self,
        trace: str,
        turn: Optional[int] = None,
        output: Optional[str] = None,
        odps: bool = False,
    ) -> Dict[str, Any]:
        """Run `ctxvm export <trace> [--turn N] [--output DIR] [--odps]`.

        Returns {"exit_code": int, "report": <parsed JSON | str>, "stderr": str}.
        """
        args: List[str] = [trace]
        if turn is not None:
            args.extend(["--turn", str(turn)])
        if output:
            args.extend(["--output", output])
        if odps:
            args.append("--odps")
        result = _run("export", args)
        return {
            "exit_code": result["exit_code"],
            "report": _parse_json(result["stdout"]),
            "stderr": result["stderr"],
        }

    # --- Verdict decomposition (UC2 §3 Phase 3–4) -----------------------

    def diagnose(self, trace: str, fault_turn: int) -> Dict[str, Any]:
        """Diagnose whether a fault at *fault_turn* is context-management or
        model reasoning.

        Method:
          1. Profile all faults in the trace; confirm one exists at *fault_turn*.
          2. Profile all evictions before *fault_turn*.
          3. For each fault at *fault_turn*, check whether its page was evicted
             in an earlier turn (context-management fault) or was resident
             (model reasoning fault).
          4. Run `replay --turn fault_turn` to confirm byte-identical render
             (fact gate).

        Returns:
            {
              "fault_turn": int,
              "verdict": "context-management" | "model-reasoning" | "inconclusive",
              "evidence": {
                "faults_at_turn": [fault rows ...],
                "evictions_before": [evict rows ...],
                "replay_exit_code": int,
                "replay_divergences": [],
              },
            }
        """
        # Fact gate: replay must be divergence-free at the fault turn.
        replay_result = self.replay(trace, turn=fault_turn)
        replay_report = replay_result.get("report", {})
        divergences = replay_report.get("divergences", []) if isinstance(replay_report, dict) else []

        # Faults at the fault turn.
        profile_result = self.profile(trace, events=["page.fault"])
        profile_report = profile_result.get("report", {})
        faults = profile_report.get("faults", []) if isinstance(profile_report, dict) else []
        faults_at_turn = [f for f in faults if f.get("turn") == fault_turn]

        # Evictions before the fault turn.
        if fault_turn > 0:
            evict_result = self.profile(trace, events=["page.evict"], turns=f"0-{fault_turn - 1}")
        else:
            evict_result = self.profile(trace, events=["page.evict"], turns="0-0")
        evict_report = evict_result.get("report", {})
        evictions_before = evict_report.get("evictions", []) if isinstance(evict_report, dict) else []
        evicted_refs_before = {
            e.get("page", {}).get("logicalRef") for e in evictions_before if isinstance(e, dict)
        }

        # Determine verdict.
        if not faults_at_turn:
            verdict = "inconclusive"
            reason = f"no page.fault at turn {fault_turn}"
        elif replay_result["exit_code"] != 0 or divergences:
            verdict = "inconclusive"
            reason = f"replay at turn {fault_turn} not divergence-free (exit {replay_result['exit_code']})"
        else:
            # A fault is context-management if its page was evicted before the
            # fault turn (the pager dropped it). Otherwise it's model reasoning
            # (the page was resident — visibility was not the issue).
            context_management = any(
                f.get("page", {}).get("logicalRef") in evicted_refs_before
                for f in faults_at_turn
                if isinstance(f, dict)
            )
            verdict = "context-management" if context_management else "model-reasoning"
            reason = (
                "page evicted before fault turn — pager dropped needed content"
                if context_management
                else "page resident at fault turn — pager not at fault"
            )

        return {
            "fault_turn": fault_turn,
            "verdict": verdict,
            "reason": reason,
            "evidence": {
                "faults_at_turn": faults_at_turn,
                "evictions_before": evictions_before,
                "replay_exit_code": replay_result["exit_code"],
                "replay_divergences": divergences,
            },
        }

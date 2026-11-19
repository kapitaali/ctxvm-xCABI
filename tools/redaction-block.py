#!/usr/bin/env python3
"""G4 redaction sidecar — writer + consumer (implementation card RR-REDACTIMPL-20261119).

A sidecar ASSERTION record beside a drop's provenance.json / checksums.sha256
(design/redaction-block.md, heading "Required properties"). It is a claim by its
writer, never a verifier: no tamper evidence, no canary, no keyed-hash emission.
Scope authority: reports/RR-G4GO-20261118.md (owner GO, narrow) and
reports/RR-REDACT-20261118.md (revised implementation card).

Record shape (redaction.json):
  stages            LIST of {stage, policyId, ruleSetVersion, replacedFieldCount}
                    (capture / flush / export; one artifact may be redacted more
                    than once, so entries accumulate — never a single flag)
  logicalRef        declaration-only enum raw | keyed-hashed | dropped; raw ships
  channelsModelled  ["logicalRef"] — stubText/reason are DEFERRED (card §6), so
                    replacedFieldCount is never "all leak channels handled"

Consumer contract — exact strings, asserted by the gate (card §4):
  block absent                  "redaction: unknown"                     exit 0
  block present, consistent     "redaction: declared"
                                stage=<s> policy=<id> rules=<v> replaced=<n>  (per stage)
                                "logicalRef: <enum>"
                                "channels modelled: logicalRef"          exit 0
  declaration contradicts bytes "redaction: inconsistent — declared <value>, <n> raw refs present"
                                                                         exit 1
  block unreadable / invalid    "redaction: invalid — <reason>"          exit 2

Absence means UNKNOWN, never "none": the v0-era corpus predates any block, so
absence is provably not evidence of no redaction.

The raw-ref count is a LINT-level shape check, not a verifier: a ref is keyed
only if it matches scheme:(sha256:)?<hex of >= 32 chars>; anything else present
is raw. For a "dropped" declaration any surviving ref counts (it was not
dropped). A "raw" declaration needs no count — it matches the shipped value.

Writer law: new drops only. Any directory under <repo>/corpus/ is frozen
(AGENTS.md law 5) and is refused BEFORE any byte is written. Existing sidecar
entries are appended, never rewritten.

Usage:
  python3 tools/redaction-block.py write DROP --stage capture|flush|export
      [--policy-id ID] [--rules VERSION] [--replaced N]
      [--logical-ref raw|keyed-hashed|dropped]
  python3 tools/redaction-block.py consume DROP_DIR_OR_TRACE_JSONL
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SIDECAR_NAME = "redaction.json"
STAGES = ("capture", "flush", "export")
ENUM = ("raw", "keyed-hashed", "dropped")
STAGE_FIELDS = ("stage", "policyId", "ruleSetVersion", "replacedFieldCount")
DEFAULT_POLICY_ID = "raw-passthrough"
DEFAULT_RULES = "w8-dq-v1"

# Lint-level keyed shape: a scheme followed by a hex digest only. Everything
# else present (arguments, paths, parentheses, spaces) is raw. This is a shape
# check on the declaration's consistency with the bytes — not a verifier.
_KEYED_REF = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:(?:sha256:)?[0-9a-f]{32,}$")

_REPO_ROOT = Path(__file__).resolve().parents[1]


class RedactionRefused(Exception):
    """The writer refuses the drop (frozen, invalid shape, bad declaration)."""


def _frozen_reason(drop: Path) -> Optional[str]:
    """Law 5: every corpus drop is byte-pinned; the writer never touches one."""
    try:
        rel = drop.resolve().relative_to(_REPO_ROOT / "corpus")
    except ValueError:
        return None
    return f"frozen drop (law 5): corpus/{rel}"


def _validate_stage(entry: Dict[str, Any]) -> None:
    for field in STAGE_FIELDS:
        if field not in entry:
            raise RedactionRefused(f"stage entry missing field: {field}")
    if entry["stage"] not in STAGES:
        raise RedactionRefused(f"unknown stage: {entry['stage']!r}")
    for field in ("policyId", "ruleSetVersion"):
        v = entry[field]
        if not isinstance(v, str) or not v:
            raise RedactionRefused(f"{field} must be a non-empty string")
    n = entry["replacedFieldCount"]
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise RedactionRefused("replacedFieldCount must be an integer >= 0")


def write_sidecar(drop: Path, stages: List[Dict[str, Any]],
                  logical_ref: str) -> Path:
    """Write/append <drop>/redaction.json. Refuses frozen drops and invalid
    declarations BEFORE any byte is written. Returns the sidecar path."""
    drop = Path(drop)
    if not drop.is_dir():
        raise RedactionRefused(f"not a drop directory: {drop}")
    reason = _frozen_reason(drop)
    if reason:
        raise RedactionRefused(reason)
    if not stages:
        raise RedactionRefused("at least one stage entry is required")
    if logical_ref not in ENUM:
        raise RedactionRefused(f"logicalRef not in enum: {logical_ref!r}")
    for entry in stages:
        _validate_stage(entry)
    sidecar = drop / SIDECAR_NAME
    existing: Dict[str, Any] = {"stages": []}
    if sidecar.exists():
        try:
            existing = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RedactionRefused(f"existing sidecar unreadable: {exc}")
        if not isinstance(existing.get("stages"), list):
            raise RedactionRefused("existing sidecar has no stage list")
    record = {
        "stages": list(existing["stages"]) + [dict(e) for e in stages],
        "logicalRef": logical_ref,
        "channelsModelled": ["logicalRef"],
    }
    sidecar.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
    return sidecar


def _block_errors(block: Any) -> Optional[str]:
    """Required-field validation of a parsed block; None when valid."""
    if not isinstance(block, dict):
        return "block is not a JSON object"
    stages = block.get("stages")
    if not isinstance(stages, list) or not stages:
        return "missing or empty stage list"
    for i, entry in enumerate(stages):
        if not isinstance(entry, dict):
            return f"stage entry {i} is not an object"
        for field in STAGE_FIELDS:
            if field not in entry:
                return f"stage entry {i} missing field: {field}"
        if entry["stage"] not in STAGES:
            return f"stage entry {i} unknown stage: {entry['stage']!r}"
        for field in ("policyId", "ruleSetVersion"):
            v = entry[field]
            if not isinstance(v, str) or not v:
                return f"stage entry {i} {field} must be a non-empty string"
        n = entry["replacedFieldCount"]
        if not isinstance(n, int) or isinstance(n, bool) or n < 0:
            return f"stage entry {i} replacedFieldCount must be an integer >= 0"
    if block.get("logicalRef") not in ENUM:
        return "logicalRef missing or not in enum raw|keyed-hashed|dropped"
    return None


def _logical_refs(obj: Any, out: List[str]) -> None:
    """Collect every logicalRef string value anywhere in an event."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "logicalRef" and isinstance(v, str):
                out.append(v)
            else:
                _logical_refs(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _logical_refs(v, out)


def _raw_ref_count(drop: Path, declared: str) -> Tuple[int, Optional[str]]:
    """Lint-level count of refs contradicting a non-raw declaration.
    Returns (count, error); error means the trace bytes are unreadable."""
    refs: List[str] = []
    for trace in sorted(drop.rglob("*.jsonl")):
        try:
            text = trace.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            return 0, f"trace unreadable: {trace.name} ({exc})"
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except ValueError:
                return 0, f"trace unreadable: {trace.name} line {line_no} (bad JSON)"
            _logical_refs(event, refs)
    if declared == "dropped":
        # a dropped ref does not survive; any survivor is raw by definition
        return len(refs), None
    return sum(1 for r in refs if not _KEYED_REF.match(r)), None


def consume(path: Path) -> int:
    """The §4 consumer. Prints the contract strings; exit 0 / 1 / 2."""
    path = Path(path)
    if path.is_file():
        drop = path.parent
    elif path.is_dir():
        drop = path
    else:
        print(f"redaction: invalid — drop does not exist: {path}")
        return 2
    sidecar = drop / SIDECAR_NAME
    if not sidecar.exists():
        print("redaction: unknown")
        return 0
    try:
        block = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"redaction: invalid — sidecar unreadable ({exc})")
        return 2
    err = _block_errors(block)
    if err:
        print(f"redaction: invalid — {err}")
        return 2
    declared = block["logicalRef"]
    if declared != "raw":
        count, err = _raw_ref_count(drop, declared)
        if err:
            print(f"redaction: invalid — {err}")
            return 2
        if count > 0:
            print(f"redaction: inconsistent — declared {declared}, "
                  f"{count} raw refs present")
            return 1
    print("redaction: declared")
    for entry in block["stages"]:
        print(f"stage={entry['stage']} policy={entry['policyId']} "
              f"rules={entry['ruleSetVersion']} "
              f"replaced={entry['replacedFieldCount']}")
    print(f"logicalRef: {declared}")
    print("channels modelled: logicalRef")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="G4 redaction sidecar: writer + consumer (assertion, not verifier).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write", help="write/append the sidecar (new drops only)")
    w.add_argument("drop", help="drop directory")
    w.add_argument("--stage", required=True, choices=STAGES)
    w.add_argument("--policy-id", default=DEFAULT_POLICY_ID)
    w.add_argument("--rules", default=DEFAULT_RULES)
    w.add_argument("--replaced", type=int, default=0)
    w.add_argument("--logical-ref", default="raw", choices=ENUM)
    c = sub.add_parser("consume", help="print the redaction contract for a drop")
    c.add_argument("path", help="drop directory or a trace .jsonl inside it")
    ns = parser.parse_args(argv)
    if ns.cmd == "write":
        entry = {"stage": ns.stage, "policyId": ns.policy_id,
                 "ruleSetVersion": ns.rules, "replacedFieldCount": ns.replaced}
        try:
            sidecar = write_sidecar(Path(ns.drop), [entry], ns.logical_ref)
        except RedactionRefused as exc:
            print(f"write refused: {exc}", file=sys.stderr)
            return 2
        print(f"redaction sidecar written: {sidecar}")
        return 0
    return consume(Path(ns.path))


if __name__ == "__main__":
    sys.exit(main())
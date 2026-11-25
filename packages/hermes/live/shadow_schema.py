"""Schema + validator for ctxvm-shadow-selection/v1 records.

The shadow sidecar is an offline analysis artefact, not a wire surface. Records
are content-free: hashed page ids, token counts, policy facts. Validation is
fail-closed at write time and available as an offline CLI through
tools/shadow-selection-validate.py.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

SCHEMA = "ctxvm-shadow-selection/v1"
_TOP = {"schema", "session_id", "turn", "call_index", "ts", "policy",
        "budget_tokens", "resident_tokens", "floor_tokens", "dropped_tokens",
        "dropped_pages", "repositioned_pages", "selection_hash", "prefix_hash",
        "trigger", "request_unchanged", "policy_applied"}
_POLICY = {"name", "version", "mode"}
_PAGE = {"page_id", "tokens", "kind"}
_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
_TRIGGERS = {None, "new-page", "overflow", "every-B", "held"}


class ShadowSchemaError(ValueError):
    pass


def _int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ShadowSchemaError(f"{field} must be a non-negative integer")
    return value


def _pages(value: Any, field: str) -> None:
    if not isinstance(value, list):
        raise ShadowSchemaError(f"{field} must be a list")
    for i, page in enumerate(value):
        if not isinstance(page, dict) or set(page) != _PAGE:
            raise ShadowSchemaError(f"{field}[{i}] must have exactly {sorted(_PAGE)}")
        if not isinstance(page.get("page_id"), str) or not _HASH.match(page["page_id"]):
            raise ShadowSchemaError(f"{field}[{i}].page_id must be sha256:<64 hex>")
        _int(page.get("tokens"), f"{field}[{i}].tokens")
        if not isinstance(page.get("kind"), str) or not page["kind"]:
            raise ShadowSchemaError(f"{field}[{i}].kind must be a non-empty string")


def validate_record(record: Any) -> Dict[str, Any]:
    """Raise ShadowSchemaError on any invalid record; return the record."""
    if not isinstance(record, dict) or set(record) != _TOP:
        raise ShadowSchemaError(f"record must have exactly {sorted(_TOP)}")
    if record.get("schema") != SCHEMA:
        raise ShadowSchemaError(f"schema must be {SCHEMA}")
    if not isinstance(record.get("session_id"), str) or not record["session_id"]:
        raise ShadowSchemaError("session_id must be a non-empty string")
    _int(record.get("turn"), "turn")
    _int(record.get("call_index"), "call_index")
    if not isinstance(record.get("ts"), str) or not record["ts"]:
        raise ShadowSchemaError("ts must be a non-empty string")
    policy = record.get("policy")
    if not isinstance(policy, dict) or set(policy) != _POLICY:
        raise ShadowSchemaError(f"policy must have exactly {sorted(_POLICY)}")
    if policy.get("name") != "keep-law":
        raise ShadowSchemaError("policy.name must be keep-law")
    if not isinstance(policy.get("version"), str) or not policy["version"]:
        raise ShadowSchemaError("policy.version must be a non-empty string")
    if policy.get("mode") not in ("fresh", "stable"):
        raise ShadowSchemaError("policy.mode must be fresh or stable")
    budget = _int(record.get("budget_tokens"), "budget_tokens")
    resident = _int(record.get("resident_tokens"), "resident_tokens")
    floor = _int(record.get("floor_tokens"), "floor_tokens")
    dropped = _int(record.get("dropped_tokens"), "dropped_tokens")
    if dropped > resident:
        raise ShadowSchemaError("dropped_tokens must be <= resident_tokens")
    if floor > resident:
        raise ShadowSchemaError("floor_tokens must be <= resident_tokens")
    if budget <= 0:
        raise ShadowSchemaError("budget_tokens must be positive")
    _pages(record.get("dropped_pages"), "dropped_pages")
    _pages(record.get("repositioned_pages"), "repositioned_pages")
    for field in ("selection_hash", "prefix_hash"):
        value = record.get(field)
        if not isinstance(value, str) or not value.startswith("sha256:"):
            raise ShadowSchemaError(f"{field} must be a sha256: hash string")
    if record.get("trigger") not in _TRIGGERS:
        raise ShadowSchemaError("trigger is not in the frozen enum")
    if record.get("request_unchanged") is not True:
        raise ShadowSchemaError("request_unchanged must be true")
    if not isinstance(record.get("policy_applied"), bool):
        raise ShadowSchemaError("policy_applied must be a boolean")
    return record

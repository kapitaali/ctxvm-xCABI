"""
ctxvm UC2 — in-harness forensics surface submodule (stub).

KIT-1 org decision (09-plugin-parity.md §1): use cases are CTXVM_FEATURES-gated
submodules inside each plugin, dispatched by a thin live/ entry. This file is
the UC2 skeleton — a no-op placeholder until UC2 forensics commands land
(ORG-1 / UC2-PLUGIN). It never mutates messages, never evicts, never throws.

Enabled via CTXVM_FEATURES=uc2-forensics (default is CTXVM_FEATURES=trace only).
"""

from __future__ import annotations

from typing import Any, Dict

from uc_registry import UCModule, UC2_FEATURE


class UC2Forensics(UCModule):
    """UC2 — in-harness forensics surface (stub). No behavior yet."""

    name = "uc2-forensics"
    feature = UC2_FEATURE

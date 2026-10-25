"""
ctxvm UC3 — capacity-planning policy hooks submodule (stub).

KIT-1 org decision (09-plugin-parity.md §1): use cases are CTXVM_FEATURES-gated
submodules inside each plugin, dispatched by a thin live/ entry. This file is
the UC3 skeleton — a no-op placeholder until UC3 policy-simulation hooks land.
It never mutates messages, never evicts, never throws.

Enabled via CTXVM_FEATURES=uc3-planner (default is CTXVM_FEATURES=trace only).
"""

from __future__ import annotations

from typing import Any, Dict

from uc_registry import UCModule, UC3_FEATURE


class UC3Planner(UCModule):
    """UC3 — capacity-planning policy hooks (stub). No behavior yet."""

    name = "uc3-planner"
    feature = UC3_FEATURE

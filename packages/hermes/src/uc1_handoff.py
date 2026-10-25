"""
ctxvm UC1 — within-harness pause/resume submodule (stub).

KIT-1 org decision (09-plugin-parity.md §1): use cases are CTXVM_FEATURES-gated
submodules inside each plugin, dispatched by a thin live/ entry. This file is
the UC1 skeleton — a no-op placeholder until UC1 pause/resume logic lands
(ORG-1 / UC1-PLUGIN). It never mutates messages, never evicts, never throws.

Enabled via CTXVM_FEATURES=uc1-handoff (default is CTXVM_FEATURES=trace only).
"""

from __future__ import annotations

from typing import Any, Dict

from uc_registry import UCModule, UC1_FEATURE


class UC1Handoff(UCModule):
    """UC1 — within-harness pause/resume (stub). No behavior yet."""

    name = "uc1-handoff"
    feature = UC1_FEATURE

# ctxvm-py

Python bindings for the ctxvm Rust engine — `replay`, `profile`, `diff`, and
`export` — exposed as a thin subprocess wrapper around the committed Rust CLI
binaries in `rust/target/release/`.

This is the **fallback binding** referenced by `design/uc1-plugin.md` §5:
"until the binding lands, the modules shell the committed rust binaries;
swapping the call site is the binding card's entire integration step." When a
real PyO3/maturin binding lands, this package's Python API stays the same and
the shell-out is replaced by native FFI calls.

## Install

```bash
pip install packages/py/
# or, for editable development:
pip install -e packages/py/
```

## Usage

```python
from ctxvm_py import replay, profile, diff, export

# Point-in-time replay + counterfactual force-resident overlay
report = replay("session.jsonl", turn=37, pins=["page:tool:read_file(src/auth/session.ts)"])

# Forensic aggregation
report = profile("session.jsonl", events=["page.fault"], source="tool_recall")

# Two-trace comparison
report = diff("a.jsonl", "b.jsonl")

# Handoff snapshot builder (ODPS package)
report = export("trace.jsonl", turn=142, odps=True)
```

All functions return the parsed JSON report dict from the corresponding Rust
CLI binary and raise `RuntimeError` on non-zero exit.
"""

from ctxvm_py._cli import (
    _bin_path,
    _run,
    diff,
    export,
    profile,
    replay,
)

__all__ = [
    "diff",
    "export",
    "profile",
    "replay",
]

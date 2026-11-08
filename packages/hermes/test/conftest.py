"""Test-session hygiene: every temporary directory the suite creates is removed at the end.

Why this exists: the suite calls `tempfile.mkdtemp` about ninety times per run and never
removes what it makes. Four gate runs on 2026-11-08 left **364 `/tmp/ctxvm-*` directories
(7.9 MB)** behind, and the count grows with every run. Those directories are regenerable
scratch — the same suite recreates them byte-identically from its own seeds — so the right
answer is to delete them, not to archive them.

The patch is applied to `tempfile.mkdtemp` rather than to each test, so a test written next
month is cleaned up without its author knowing this file exists.
"""
import atexit
import shutil
import tempfile

_CREATED: list[str] = []
_REAL_MKDTEMP = tempfile.mkdtemp


def _tracked_mkdtemp(*args, **kwargs):
    path = _REAL_MKDTEMP(*args, **kwargs)
    _CREATED.append(path)
    return path


tempfile.mkdtemp = _tracked_mkdtemp


def _cleanup() -> None:
    for path in _CREATED:
        shutil.rmtree(path, ignore_errors=True)
    _CREATED.clear()


atexit.register(_cleanup)

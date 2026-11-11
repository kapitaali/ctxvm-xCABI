"""Per-session profile policy — which arm is this turn, and what budget does it carry?

**Why this module exists.** One gateway process holds ONE plugin instance, and the plugin used to
read its settings once, at registration. Measured 2026-11-11: the naive arm and the paged arm both
reported `engine: ctxvm` and `budgetTokens: 70000 / settings`, because the settings snapshot taken in
the host process was the paged profile's and was applied to every session served afterwards. An
experiment whose control arm runs the treatment is not an experiment.

**How the host scopes a turn.** The gateway sets a contextvar per turn
(`gateway/run.py::_profile_runtime_scope` → `set_hermes_home_override`, which "reaches the agent
worker via copy_context()"), and `hermes_constants.get_hermes_home()` reads that override first.
So the profile IS knowable at hook time — just not at registration time, which is when the plugin
used to ask.

**What this module does.** It resolves the home at call time and reads the two values the experiment
depends on from that home's `config.yaml`:

    context.engine                                   -> "ctxvm" (treatment) or "compressor" (control)
    plugins.entries.<id>.settings.budgetTokens       -> the vBudget for this arm

No third-party YAML parser: the gateway's interpreter has no PyYAML, and these two keys live in a
hand-written file. The scanner is deliberately narrow — a block key at indent 0, then a child key.

Outside the Hermes runtime (the plugin's own test suite) everything fails open to the control arm,
which is the safe direction: a missing profile must never silently produce a treatment.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

PLUGIN_ID = "ctxvm-tracer"


def current_home() -> Path:
    """The profile home serving THIS turn: contextvar override → HERMES_HOME → ~/.hermes."""
    try:
        from hermes_constants import get_hermes_home  # type: ignore

        return Path(get_hermes_home())
    except Exception:  # noqa: BLE001 - outside the host
        env = os.environ.get("HERMES_HOME", "").strip()
        return Path(env) if env else Path.home() / ".hermes"


def profile_name(home: Path) -> str:
    """`default` for the root home, otherwise the directory name."""
    try:
        if Path(home).resolve() == (Path.home() / ".hermes").resolve():
            return "default"
    except Exception:  # noqa: BLE001
        pass
    name = Path(home).name or "default"
    return "default" if name == ".hermes" else name


def _strip(value: str) -> str:
    value = value.split("#", 1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value.strip()


def read_yaml_subset(path: Path) -> Dict[str, Any]:
    """Read the two keys this plugin needs from a Hermes config.yaml.

    Returns `{"engine": str | None, "budgetTokens": int | None}`. Narrow on purpose: a full YAML
    implementation here would be a second source of truth about a file the host owns.
    """
    out: Dict[str, Any] = {"engine": None, "budgetTokens": None}
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    block = None          # current indent-0 block
    in_plugin_entry = False
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        key, sep, rest = raw.strip().partition(":")
        if not sep:
            continue
        if indent == 0:
            block = key
            in_plugin_entry = False
            continue
        if block == "context" and indent > 0 and key == "engine":
            val = _strip(rest)
            if val:
                out["engine"] = val
        elif block == "plugins" and key == PLUGIN_ID:
            in_plugin_entry = True
        elif block == "plugins" and key == "budgetTokens" and in_plugin_entry:
            try:
                out["budgetTokens"] = int(_strip(rest))
            except (TypeError, ValueError):
                pass
    return out


def policy(home: Optional[Path] = None) -> Dict[str, Any]:
    """Resolve the arm for the current turn. Never raises."""
    try:
        h = Path(home) if home else current_home()
    except Exception:  # noqa: BLE001
        h = Path.home() / ".hermes"
    try:
        cfg = read_yaml_subset(h / "config.yaml")
    except Exception:  # noqa: BLE001
        cfg = {"engine": None, "budgetTokens": None}

    engine = cfg.get("engine") or "compressor"
    budget: Optional[int] = cfg.get("budgetTokens")
    source = "settings" if isinstance(budget, int) and budget > 0 else "default"
    if source == "default":
        env = os.environ.get("CTXVM_BUDGET_TOKENS", "").strip()
        if env:
            try:
                value = int(env)
                if value > 0:
                    budget, source = value, "env"
            except ValueError:
                pass
    if not isinstance(budget, int) or budget <= 0:
        budget, source = 200000, "default"

    return {
        "home": str(h),
        "profile": profile_name(h),
        "engine": engine,
        "budget": int(budget),
        "budgetSource": source,
        # The arm is decided by the profile's own setting, never by what the process happens to hold.
        "arm": "paged" if engine == "ctxvm" else "control",
    }

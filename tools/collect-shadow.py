#!/usr/bin/env python3
"""Collect a bounded, preregistered control-shadow corpus.

The collector is instrumentation. It never changes profile/gateway/model configuration,
never applies candidate pins, and never treats descriptive reuse as causal importance.

Live execution is conditional on owner authorization and review acceptance. All tests for
this module use fake runners and make no model calls.

Fixture manifest shape (research-owned, SHA-256 pinned)::

    {"schema": "ctxvm-shadow-fixtures/v1",
     "shapes": {"read-once-pressure": {
       "workspace": "relative/path",
       "prompt": "frozen prompt",
       "files": [{"path": "relative/file", "sha256": "<64 lowercase hex>"}]},
       ...}}

Exit codes: 0 target met; 2 preflight failed; 3 attempt cap or underpowered;
4 auth/model/provider failure stopped collection.

Use --preflight-only to prove every live prerequisite without running a model session.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import stat
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
MIN_PLUGIN_VERSION = (0, 13, 37)
FROZEN_MODEL = "tencent/hy4-flash:free"
FROZEN_PROVIDER = "nous"
MAX_TARGET_INFORMATIVE = 12
MAX_ATTEMPTS = 18
MAX_ATTEMPTS_PER_SHAPE = 6
SHAPES = ("read-once-pressure", "deliberate-later-reread", "dependency-chain")
FIXTURE_SCHEMA = "ctxvm-shadow-fixtures/v1"


class PreflightError(RuntimeError):
    """A required instrument, profile, privacy, or fixture fact is not proven."""


@dataclass(frozen=True)
class Config:
    repo: Path
    shadow: Path
    trace_dir: Path
    fixture_manifest: Path
    out: Path
    target_informative: int = 12
    max_attempts: int = 18
    max_attempts_per_shape: int = 6
    model: str = FROZEN_MODEL
    provider: str = FROZEN_PROVIDER
    hermes_home: Optional[Path] = None
    profile_home: Optional[Path] = None
    test_mode: bool = False


Runner = Callable[..., subprocess.CompletedProcess[str]]


def _read_gateway_env(hermes_home: Path) -> Dict[str, str]:
    lock_path = hermes_home / "gateway.lock"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        pid = int(lock["pid"])
        raw = Path(f"/proc/{pid}/environ").read_bytes()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise PreflightError(f"cannot read gateway environment: {exc}") from exc
    env: Dict[str, str] = {}
    for item in raw.split(b"\0"):
        if b"=" in item:
            key, value = item.split(b"=", 1)
            env[key.decode(errors="replace")] = value.decode(errors="replace")
    if not env:
        raise PreflightError("gateway environment is empty")
    return env


def _gateway_trace_dir(env: Dict[str, str]) -> Optional[Path]:
    if env.get("CTXVM_TRACE", "").strip().lower() in {"0", "off", "false", "no"}:
        return None
    raw = env.get("CTXVM_TRACE_DIR")
    if raw is None:
        state_home = env.get("XDG_STATE_HOME", "").strip()
        home = env.get("HOME", "").strip() or str(Path.home())
        base = Path(state_home) if state_home else Path(home) / ".local" / "state"
        return (base / "ctxvm" / "traces").resolve()
    raw = raw.strip()
    if not raw:
        return None
    home = env.get("HOME", "").strip() or str(Path.home())
    if raw == "~":
        raw = home
    elif raw.startswith("~/"):
        raw = home + raw[1:]
    def expand(match: re.Match[str]) -> str:
        name = match.group(1)
        if name.startswith("{") and name.endswith("}"):
            name = name[1:-1]
        return env.get(name, match.group(0))
    raw = re.sub(r"\$(\w+|\{[^}]*\})", expand, raw)
    return Path(raw).resolve()


def _parse_trace_status(output: str) -> Dict[str, Any]:
    if not isinstance(output, str):
        raise PreflightError("gateway trace status was not text")
    enabled = re.search(r"\benabled=(True|False)\b", output)
    directory = re.search(r"\bdir=(.*?) \(source: (.*?)\), name=", output)
    version = re.search(r"\bversion=([^, ]+)", output)
    if not enabled or not directory or not version:
        raise PreflightError("gateway trace status was incomplete")
    raw_dir = directory.group(1).strip()
    return {
        "enabled": enabled.group(1) == "True",
        "trace_dir": None if raw_dir == "<none>" else Path(raw_dir).resolve(),
        "source": directory.group(2).strip(),
        "version": version.group(1),
    }


def _query_gateway_trace_status(hermes_home: Path, profile_home: Path,
                                session_ids: Sequence[str]) -> Dict[str, Any]:
    if not session_ids:
        raise PreflightError("no baseline session id is available for the read-only gateway status query")
    env = {key: value for key, value in os.environ.items() if not key.startswith("CTXVM_")}
    env["HERMES_HOME"] = str(hermes_home)
    attach = subprocess.run(
        ["hermes", "-p", profile_home.name, "gateway", "attach", "--json"],
        capture_output=True, text=True, check=False, env=env, timeout=30,
    )
    if attach.returncode != 0:
        raise PreflightError(f"gateway attach failed with exit {attach.returncode}")
    try:
        target = json.loads(attach.stdout)
        url = target["url"]
        protocols = target["protocols"]
    except (ValueError, KeyError, TypeError) as exc:
        raise PreflightError("gateway attach returned an invalid target") from exc
    try:
        import websocket
    except ImportError as exc:
        raise PreflightError("websocket-client is required for active gateway status proof") from exc
    ws = None
    try:
        ws = websocket.create_connection(url, subprotocols=protocols, timeout=10,
                                         suppress_origin=True)
        if protocols and ws.getsubprotocol() != protocols[0]:
            raise PreflightError("gateway WebSocket protocol mismatch")
        for sid in session_ids:
            ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "command.dispatch",
                                "params": {"name": "ctxvm-trace", "arg": "status",
                                           "session_id": sid}}))
            for _ in range(100):
                frame = json.loads(ws.recv())
                if frame.get("id") != 1:
                    continue
                error = frame.get("error")
                if error:
                    reason = (error.get("data") or {}).get("reason") if isinstance(error, dict) else None
                    if reason == "not_found":
                        break
                    raise PreflightError("gateway refused the read-only trace status query")
                result = frame.get("result") or {}
                output = result.get("output")
                if not isinstance(output, str):
                    raise PreflightError("gateway trace status was not text")
                return _parse_trace_status(output)
            else:
                raise PreflightError("gateway trace status query did not answer")
        raise PreflightError("no baseline session could query the active trace status")
    except PreflightError:
        raise
    except Exception as exc:  # noqa: BLE001 - never echo a ticket-bearing attach target
        raise PreflightError(f"active gateway status query failed: {type(exc).__name__}") from exc
    finally:
        if ws is not None:
            ws.close()


def _subprocess_env(hermes_home: Path, trace_dir: Path) -> Dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("CTXVM_")}
    env["HERMES_HOME"] = str(hermes_home)
    env["CTXVM_TRACE_DIR"] = str(trace_dir)
    return env


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _version(value: str) -> Tuple[int, int, int]:
    if not isinstance(value, str):
        raise PreflightError(f"invalid plugin version: {value!r}")
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", value.strip())
    if not match:
        raise PreflightError(f"invalid plugin version: {value!r}")
    return tuple(map(int, match.groups()))  # type: ignore[return-value]


def _read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PreflightError(f"cannot read {label}: {exc}") from exc


def _repo_version(repo: Path) -> str:
    path = repo / "packages" / "hermes" / "live" / "__init__.py"
    match = re.search(r'^PLUGIN_VERSION\s*=\s*"([^"]+)"', _read_text(path, "repo PLUGIN_VERSION"), re.M)
    if not match:
        raise PreflightError("repo PLUGIN_VERSION not found")
    return match.group(1)


def _installed_version(hermes_home: Path) -> str:
    path = hermes_home / "plugins" / "ctxvm-tracer" / "__init__.py"
    match = re.search(r'^PLUGIN_VERSION\s*=\s*"([^"]+)"', _read_text(path, "installed PLUGIN_VERSION"), re.M)
    if not match:
        raise PreflightError("installed PLUGIN_VERSION not found")
    return match.group(1)


def _manifest_version(hermes_home: Path) -> str:
    path = hermes_home / "plugins" / "ctxvm-tracer" / "plugin.yaml"
    match = re.search(r"^version:\s*(\S+)\s*$", _read_text(path, "installed plugin.yaml"), re.M)
    if not match:
        raise PreflightError("installed plugin.yaml version not found")
    return match.group(1)


def _private_dir(path: Path, *, create: bool = False) -> None:
    if create and not path.exists():
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not path.is_dir():
        raise PreflightError(f"not a directory: {path}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise PreflightError(f"directory is not private (0700): {path}")
    if not os.access(path, os.W_OK | os.X_OK):
        raise PreflightError(f"directory is not writable: {path}")


def _safe_relative(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise PreflightError(f"{label} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise PreflightError(f"{label} must be a safe relative path")
    return path


def load_fixtures(path: Path) -> Dict[str, Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise PreflightError(f"cannot read fixture manifest: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != FIXTURE_SCHEMA:
        raise PreflightError(f"fixture manifest schema must be {FIXTURE_SCHEMA}")
    shapes = data.get("shapes")
    if not isinstance(shapes, dict) or set(shapes) != set(SHAPES):
        raise PreflightError(f"fixture manifest must contain exactly: {', '.join(SHAPES)}")
    base = path.parent
    normalized: Dict[str, Dict[str, Any]] = {}
    for shape in SHAPES:
        item = shapes[shape]
        if not isinstance(item, dict):
            raise PreflightError(f"fixture shape {shape} must be an object")
        workspace_rel = _safe_relative(item.get("workspace", ""), f"{shape}.workspace")
        prompt = item.get("prompt")
        files = item.get("files")
        if not isinstance(prompt, str) or not prompt.strip():
            raise PreflightError(f"{shape}.prompt must be a non-empty string")
        if not isinstance(files, list) or not files:
            raise PreflightError(f"{shape}.files must be a non-empty list")
        workspace = (base / workspace_rel).resolve()
        try:
            workspace.relative_to(base.resolve())
        except ValueError as exc:
            raise PreflightError(f"{shape}.workspace escapes manifest directory") from exc
        if not workspace.is_dir():
            raise PreflightError(f"{shape}.workspace does not exist")
        checked: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for entry in files:
            if not isinstance(entry, dict):
                raise PreflightError(f"{shape}.files entries must be objects")
            rel = _safe_relative(entry.get("path", ""), f"{shape}.files.path")
            key = rel.as_posix()
            if key in seen:
                raise PreflightError(f"{shape} has duplicate fixture path {key}")
            seen.add(key)
            expected = entry.get("sha256")
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                raise PreflightError(f"{shape}.{key} needs a lowercase sha256")
            file_path = (workspace / rel).resolve()
            try:
                file_path.relative_to(workspace)
            except ValueError as exc:
                raise PreflightError(f"{shape}.{key} escapes workspace") from exc
            if not file_path.is_file():
                raise PreflightError(f"{shape}.{key} does not exist")
            actual = hashlib.sha256(file_path.read_bytes()).hexdigest()
            if actual != expected:
                raise PreflightError(f"{shape}.{key} sha256 mismatch")
            checked.append({"path": key, "sha256": actual})
        normalized[shape] = {"workspace": workspace, "prompt": prompt, "files": checked}
    return normalized


def _load_policy(repo: Path):
    path = repo / "packages" / "hermes" / "live" / "profile_policy.py"
    spec = importlib.util.spec_from_file_location("ctxvm_collect_profile_policy", path)
    if spec is None or spec.loader is None:
        raise PreflightError("cannot load profile_policy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_join(repo: Path):
    path = repo / "research" / "shadow-analysis" / "join.py"
    spec = importlib.util.spec_from_file_location("ctxvm_collect_shadow_join", path)
    if spec is None or spec.loader is None:
        raise PreflightError("cannot load research/shadow-analysis/join.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_private(path: Path, text: str) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o600)


def _write_private_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(0o600)


def _jsonl(rows: List[Dict[str, Any]]) -> str:
    return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:
            raise ValueError(f"invalid JSON at line {line_no}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"non-object at line {line_no}")
        rows.append(row)
    return rows


def _auth_model_failure(rc: int, stdout: str, stderr: str) -> bool:
    if rc == 0:
        return False
    text = re.sub(r"[_-]+", " ", (stdout + "\n" + stderr).lower())
    patterns = (
        r"\b401\b", r"\b402\b", r"\b403\b", r"\b404\b", r"\b429\b",
        r"no api key found", r"missing api key", r"api key not provided", r"api key is missing",
        r"invalid[_ -]?api[_ -]?key", r"invalid token", r"token expired",
        r"access denied", r"unauthori[sz]ed", r"authentication",
        r"auth(?:entication)? (?:failed|error)",
        r"model[_ ]not[_ ]found", r"model not found", r"model unavailable", r"no such model",
        r"is not a valid model", r"unknown model", r"unsupported model", r"is no longer free",
        r"does not exist", r"provider.*unavailable", r"insufficient quota", r"quota exceeded",
        r"payment required", r"rate limit exceeded", r"model overloaded",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _summary(values: List[float]) -> Optional[Dict[str, float]]:
    if not values:
        return None
    return {"mean": sum(values) / len(values), "min": min(values), "max": max(values)}


class Collector:
    def __init__(self, config: Config, *, sync_runner: Optional[Runner] = None,
                 session_runner: Optional[Runner] = None,
                 gate_runner: Optional[Runner] = None,
                 join_runner: Optional[Runner] = None,
                 gateway_env_reader: Optional[Callable[[Path], Dict[str, str]]] = None,
                 gateway_status_runner: Optional[Callable[[Path, Path, Sequence[str]], Dict[str, Any]]] = None) -> None:
        self.config = config
        self.sync_runner = sync_runner or self._default_runner
        self.session_runner = session_runner or self._default_runner
        self.gate_runner = gate_runner or self._default_runner
        self.join_runner = join_runner or self._default_runner
        self.gateway_env_reader = gateway_env_reader or _read_gateway_env
        self.gateway_status_runner = gateway_status_runner or _query_gateway_trace_status
        self.fixtures: Dict[str, Dict[str, Any]] = {}
        self.preflight_facts: Dict[str, Any] = {}
        self.join: Any = None
        self.subprocess_env: Optional[Dict[str, str]] = None
        self.profile_home: Optional[Path] = None
        self.baseline_session_ids: set[str] = set()

    def _default_runner(self, cmd: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if kwargs.get("env") is None:
            kwargs["env"] = self.subprocess_env or _subprocess_env(
                self.config.hermes_home or Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes"),
                self.config.trace_dir)
        return subprocess.run(list(cmd), capture_output=True, text=True, check=False, **kwargs)

    def _gate(self, name: str, cmd: List[str]) -> Dict[str, Any]:
        try:
            result = self.gate_runner(cmd, cwd=str(self.config.repo), timeout=180,
                                      env=self.subprocess_env)
            receipt = {"name": name, "rc": result.returncode,
                       "stdout": result.stdout or "", "stderr": result.stderr or ""}
        except Exception as exc:  # noqa: BLE001 - a gate failure excludes the attempt
            receipt = {"name": name, "rc": 127, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}
        if name == "replay" and receipt["rc"] == 0:
            try:
                report = json.loads(receipt["stdout"])
                if report.get("divergences") != [] or report.get("violations") != []:
                    receipt["rc"] = 1
                    receipt["stderr"] = "replay reported divergences or violations"
            except Exception as exc:  # noqa: BLE001
                receipt["rc"] = 1
                receipt["stderr"] = f"invalid replay JSON: {exc}"
        return receipt

    @staticmethod
    def _session_id(stdout: str, stderr: str = "") -> Optional[str]:
        text = stdout + "\n" + stderr
        matches = re.findall(r"(?mi)^\s*(?:Session|session_id)\s*:\s*(\S+)\s*$", text)
        matches.extend(re.findall(r"hermes\s+--resume\s+(\S+)", text))
        unique = sorted(set(matches))
        return unique[0] if len(unique) == 1 else None

    def _coverage_for(self, sid: Optional[str]) -> Tuple[Optional[Path], Optional[Dict[str, Any]], List[str]]:
        if not sid:
            return None, None, ["session_id"]
        matches = []
        errors = []
        for path in sorted(self.config.trace_dir.glob("*.coverage.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001 - unrelated malformed sidecars are not this session's proof
                continue
            if not isinstance(data, dict):
                continue
            session = data.get("session")
            if not isinstance(session, dict):
                continue
            if session.get("sessionID") == sid:
                matches.append((path, data))
        if len(matches) != 1:
            errors.append("coverage_missing" if not matches else "coverage_multiple")
            return None, None, errors
        return matches[0][0], matches[0][1], []

    def _summarize(self, records: List[Dict[str, Any]], coverage: Dict[str, Any],
                   sid: str, snapshot_dir: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        if self.join is None:
            raise PreflightError("join module was not loaded")
        return self.join._session_result(sid, records, coverage, snapshot_dir)

    def _session_store_route(self, sid: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        if self.profile_home is None:
            return None, "profile_unbound"
        path = self.profile_home / "state.db"
        con = None
        try:
            con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            row = con.execute(
                "SELECT model, billing_provider, model_config FROM sessions WHERE id = ?",
                (sid,),
            ).fetchone()
        except (OSError, sqlite3.Error) as exc:
            return None, f"session_store:{type(exc).__name__}"
        finally:
            if con is not None:
                con.close()
        if row is None:
            return None, "session_not_found"
        model, billing_provider, raw_config = row
        try:
            config = json.loads(raw_config) if isinstance(raw_config, str) else {}
        except ValueError as exc:
            return None, f"model_config:{type(exc).__name__}"
        runtime = config.get("gateway_runtime") if isinstance(config, dict) else None
        if not isinstance(runtime, dict):
            runtime = {}
        runtime_model = runtime.get("model")
        runtime_provider = runtime.get("provider")
        fallback_active = runtime.get("fallback_active")
        errors = []
        if model != self.config.model:
            errors.append("column_model")
        if billing_provider and billing_provider != self.config.provider:
            errors.append("billing_provider")
        if not runtime_model:
            errors.append("missing_runtime_model")
        elif runtime_model != self.config.model:
            errors.append("runtime_model")
        if not runtime_provider:
            errors.append("missing_runtime_provider")
        elif runtime_provider != self.config.provider:
            errors.append("runtime_provider")
        if fallback_active is not False:
            errors.append("fallback_active")
        provider = runtime_provider or billing_provider
        return {
            "model": model,
            "provider": provider,
            "billing_provider": billing_provider,
            "runtime_model": runtime_model,
            "runtime_provider": runtime_provider,
            "fallback_active": fallback_active,
            "source": "session_store",
            "consistent": not errors,
            "errors": errors,
        }, None

    @staticmethod
    def _empty_summary(sid: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        return ({"session_key": "sha256:" + hashlib.sha256(sid.encode()).hexdigest()[:16]},
                {"pressure": [], "floor_pressure": [], "drop_share": [],
                 "selection_churn": [], "pin_events": Counter(),
                 "pin_sessions": defaultdict(set)})

    def _attempt(self, shape: str, attempt_no: int, seen_sessions: set[str]) -> Dict[str, Any]:
        cfg = self.config
        fixture = self.fixtures[shape]
        directory = cfg.out / "attempts" / f"{attempt_no:04d}-{shape}"
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        directory.chmod(0o700)
        workspace = directory / shape
        workspace.mkdir(mode=0o700)
        workspace.chmod(0o700)
        for entry in fixture["files"]:
            rel = Path(entry["path"])
            source = fixture["workspace"] / rel
            try:
                data = source.read_bytes()
            except OSError as exc:
                raise PreflightError(f"cannot read frozen fixture {shape}/{rel}: {exc}") from exc
            actual = hashlib.sha256(data).hexdigest()
            if actual != entry["sha256"]:
                raise PreflightError(f"frozen fixture changed before attempt: {shape}/{rel}")
            target = workspace / rel
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            _write_private_bytes(target, data)
            if hashlib.sha256(target.read_bytes()).hexdigest() != entry["sha256"]:
                raise PreflightError(f"fixture snapshot hash mismatch: {shape}/{rel}")
        started_at = _utc()
        started_mono = datetime.now(timezone.utc)
        input_shadow_digest = hashlib.sha256(cfg.shadow.read_bytes()).hexdigest()
        cmd = ["hermes", "-p", "w8-shadow", "chat", "-q", fixture["prompt"], "--oneshot",
               "--max-turns", "20", "--provider", cfg.provider, "--model", cfg.model,
               "--in", str(workspace)]
        try:
            result = self.session_runner(cmd, cwd=str(cfg.repo), timeout=600,
                                         env=self.subprocess_env)
            rc, stdout, stderr = result.returncode, result.stdout or "", result.stderr or ""
        except subprocess.TimeoutExpired as exc:
            rc = 124
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes): stdout = stdout.decode(errors="replace")
            if isinstance(stderr, bytes): stderr = stderr.decode(errors="replace")
            stderr += "\ncollect-shadow: session timed out"
        except Exception as exc:  # noqa: BLE001 - record and exclude, never hide a failed attempt
            rc, stdout, stderr = 127, "", f"{type(exc).__name__}: {exc}"
        ended_at = _utc()
        duration_ms = int((datetime.now(timezone.utc) - started_mono).total_seconds() * 1000)
        _write_private(directory / "stdout.txt", stdout)
        _write_private(directory / "stderr.txt", stderr)
        sid = self._session_id(stdout, stderr)
        duplicate_session = bool(sid and sid in seen_sessions)
        if sid and not duplicate_session:
            seen_sessions.add(sid)
        auth_failure = _auth_model_failure(rc, stdout, stderr)
        output_shadow_digest = hashlib.sha256(cfg.shadow.read_bytes()).hexdigest()

        records: List[Dict[str, Any]] = []
        shadow_error = None
        try:
            records = [row for row in _read_jsonl(cfg.shadow)
                       if sid and row.get("session_id") == sid]
        except Exception as exc:  # noqa: BLE001
            shadow_error = f"{type(exc).__name__}: {exc}"
        _write_private(directory / "shadow-delta.jsonl", _jsonl(records))

        cov_path, coverage, evidence_errors = self._coverage_for(sid)
        coverage_obj = coverage if isinstance(coverage, dict) else {}
        session_obj = coverage_obj.get("session")
        if not isinstance(session_obj, dict):
            evidence_errors.append("coverage_session")
            session_obj = {}
        plugin_obj = coverage_obj.get("plugin")
        if not isinstance(plugin_obj, dict):
            evidence_errors.append("coverage_plugin")
            plugin_obj = {}
        trace_bytes = b""
        trace_digest = None
        trace_rows: List[Dict[str, Any]] = []
        if cov_path and coverage_obj:
            trace_name = coverage_obj.get("traceFile")
            if not isinstance(trace_name, str) or Path(trace_name).name != trace_name:
                evidence_errors.append("trace_name")
            else:
                try:
                    trace_bytes = (cfg.trace_dir / trace_name).read_bytes()
                    trace_digest = hashlib.sha256(trace_bytes).hexdigest()
                    if trace_digest != coverage_obj.get("traceDigest"):
                        evidence_errors.append("trace_digest")
                    trace_rows: List[Dict[str, Any]] = []
                    for line_no, line in enumerate(trace_bytes.decode("utf-8").splitlines(), 1):
                        if line.strip():
                            row = json.loads(line)
                            if not isinstance(row, dict):
                                raise ValueError(f"non-object at line {line_no}")
                            trace_rows.append(row)
                except Exception as exc:  # noqa: BLE001
                    evidence_errors.append(f"trace_read:{type(exc).__name__}")
        _write_private_bytes(directory / "trace.jsonl", trace_bytes)
        snapshot_coverage = dict(coverage_obj)
        snapshot_coverage["traceFile"] = "trace.jsonl"
        _write_private(directory / "coverage.json", json.dumps(snapshot_coverage, indent=2, sort_keys=True) + "\n")

        gates = [
            self._gate("shadow_schema", [sys.executable, str(cfg.repo / "tools/shadow-selection-validate.py"),
                                         str(directory / "shadow-delta.jsonl")]),
            self._gate("coverage_check", [sys.executable, str(cfg.repo / "tools/coverage_check.py"),
                                          str(directory / "trace.jsonl"), str(directory / "coverage.json")]),
            self._gate("v01_schema", [sys.executable, str(cfg.repo / "spec/rfc-0.1/validate_schema_v0_1.py"),
                                      str(directory / "trace.jsonl")]),
            self._gate("replay", [str(cfg.repo / "rust/target/release/replay"),
                                  str(directory / "trace.jsonl")]),
        ]
        failed = [gate["name"] for gate in gates if gate["rc"] != 0]
        if duplicate_session:
            failed.append("duplicate_session")
        if rc != 0:
            failed.append("session_rc")
        failed.extend(evidence_errors)
        if shadow_error:
            failed.append("shadow_read")

        plugin = plugin_obj
        try:
            version_ok = _version(plugin.get("version", "")) >= MIN_PLUGIN_VERSION
        except PreflightError:
            version_ok = False
        observed_model = session_obj.get("model")
        observed_provider = session_obj.get("provider")
        sidecar_required = {
            "version": version_ok,
            "profile": plugin.get("profile") == "w8-shadow",
            "arm": plugin.get("arm") == "control",
            "engine": plugin.get("engineSetting") == "compressor",
            "budget": plugin.get("budgetTokens") == 24000 and plugin.get("budgetSource") == "settings",
            "shadow": plugin.get("shadowSelection") is True and plugin.get("shadowSelectionSource") == "settings",
            "selections": plugin.get("shadowSelections") == len(records),
            "engineSelections": plugin.get("engineSelections") == 0,
            "stub": plugin.get("stubDropped") == "off",
            "failures": plugin.get("shadowWriteFailures") == 0,
        }
        for name, ok in sidecar_required.items():
            if not ok:
                failed.append(f"sidecar_{name}")
        if not records:
            failed.append("shadow_records")
        declared = {self.join._event_page_id(row) for row in trace_rows
                    if self.join._event_page_id(row) is not None}
        drop_records: List[Dict[str, Any]] = []
        page_errors = []
        for record in records:
            if record.get("budget_tokens") != 24000:
                failed.append("record_budget")
            policy = record.get("policy")
            if not isinstance(policy, dict):
                failed.append("record_policy")
            elif policy.get("mode") != "fresh":
                failed.append("not_fresh")
            if record.get("policy_applied") is not False:
                failed.append("policy_applied")
            if record.get("request_unchanged") is not True:
                failed.append("request_changed")
            dropped = record.get("dropped_pages", [])
            repositioned = record.get("repositioned_pages", [])
            if (not isinstance(dropped, list) or not isinstance(repositioned, list)
                    or any(not isinstance(page, dict) for page in dropped + repositioned)):
                failed.append("record_pages")
                continue
            if (dropped and isinstance(record.get("floor_tokens"), int)
                    and isinstance(record.get("budget_tokens"), int)
                    and isinstance(record.get("resident_tokens"), int)
                    and record["floor_tokens"] < record["budget_tokens"] < record["resident_tokens"]):
                drop_records.append(record)
            for page in dropped + repositioned:
                page_id = page.get("page_id")
                if not isinstance(page_id, str) or page_id not in declared:
                    page_errors.append("unmatched_page_id")
        if page_errors:
            failed.append("page_identity")

        if coverage_obj and records and not shadow_error:
            try:
                summary, internal = self._summarize(records, snapshot_coverage, sid or "missing-session",
                                                    directory)
            except Exception as exc:  # noqa: BLE001 - join/summary failure excludes the attempt
                failed.append("summary_error")
                summary, internal = self._empty_summary(sid or "missing-session")
        else:
            summary, internal = self._empty_summary(sid or "missing-session")
        if summary.get("scope_violation"):
            failed.append("unexpected_stub_or_evict")
        labels = {
            "later_tool_recall_opportunities": summary.get("later_tool_recall_opportunities", 0),
            "later_identifier_scan_opportunities": summary.get("later_identifier_scan_opportunities", 0),
            "never_observed_opportunities": summary.get("never_observed_opportunities", 0),
            "ambiguous_opportunities": summary.get("ambiguous_opportunities", 0),
        }
        sid_present = isinstance(sid, str) and bool(sid)
        if not sid_present:
            store_route, route_error = None, "missing_sid"
        else:
            store_route, route_error = self._session_store_route(sid or "")
        store_ok = bool(
            store_route
            and store_route.get("consistent") is True
            and store_route.get("model") == cfg.model
            and store_route.get("provider") == cfg.provider
            and store_route.get("fallback_active") is False
        )
        if store_route and not store_route.get("consistent"):
            route_error = "route_contradiction"
        unknown_model = observed_model in (None, "", "unknown", "unknown/unknown")
        unknown_provider = observed_provider in (None, "", "unknown")
        coverage_known_drift = not (
            (unknown_model or observed_model == cfg.model)
            and (unknown_provider or observed_provider == cfg.provider)
        )
        route_ok = store_ok and not coverage_known_drift
        if sid_present and not route_ok:
            if not unknown_model and observed_model != cfg.model:
                failed.append("sidecar_model")
            if not unknown_provider and observed_provider != cfg.provider:
                failed.append("sidecar_provider")
            failed.append("route_unproven")
        model_provider_failure = sid_present and not route_ok
        valid = not failed and not auth_failure and not model_provider_failure
        if shape == "read-once-pressure":
            informative = valid and bool(drop_records)
        elif shape == "deliberate-later-reread":
            informative = valid and bool(drop_records) and labels["later_tool_recall_opportunities"] > 0
        else:
            informative = valid and bool(drop_records) and labels["later_identifier_scan_opportunities"] > 0

        join_receipt = None
        if valid:
            join_dir = directory / "join"
            join_dir.mkdir(mode=0o700, exist_ok=True)
            join_cmd = [sys.executable, str(cfg.repo / "research/shadow-analysis/join.py"),
                        "--shadow", str(cfg.shadow), "--trace-dir", str(cfg.trace_dir),
                        "--out", str(join_dir), "--repo", str(cfg.repo)]
            try:
                joined = self.join_runner(join_cmd, cwd=str(cfg.repo), timeout=180,
                                          env=self.subprocess_env)
                join_receipt = {"rc": joined.returncode, "stdout": joined.stdout or "",
                                "stderr": joined.stderr or ""}
            except Exception as exc:  # noqa: BLE001
                join_receipt = {"rc": 127, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}
            _write_private(directory / "join.stdout.txt", join_receipt["stdout"])
            _write_private(directory / "join.stderr.txt", join_receipt["stderr"])
            if join_receipt["rc"] not in (0, 3):
                failed.append("join_contract")
                valid = False
                informative = False

        receipt = {
            "schema": "ctxvm-shadow-attempt/v1",
            "attempt": attempt_no,
            "shape": shape,
            "session_id": sid,
            "requested_model": cfg.model,
            "requested_provider": cfg.provider,
            "observed_model": observed_model,
            "observed_provider": observed_provider,
            "route_model": (store_route or {}).get("model"),
            "route_provider": (store_route or {}).get("provider"),
            "route_proof_source": (store_route or {}).get("source"),
            "route_fallback_active": (store_route or {}).get("fallback_active"),
            "route_consistency_errors": (store_route or {}).get("errors", []),
            "route_error": route_error,
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_ms": duration_ms,
            "rc": rc,
            "auth_model_failure": auth_failure,
            "model_provider_failure": model_provider_failure,
            "input_shadow_sha256": input_shadow_digest,
            "output_shadow_sha256": output_shadow_digest,
            "trace_digest": trace_digest,
            "gates": gates,
            "failed_gates": sorted(set(failed)),
            "drop_shape": bool(drop_records),
            "shape_labels": labels,
            "valid": valid,
            "informative": informative,
            "join": join_receipt,
            "summary": summary,
        }
        _write_private(directory / "receipt.json", json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        receipt["_internal"] = internal
        return receipt

    @staticmethod
    def _public_attempt(entry: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "attempt": entry["attempt"],
            "shape": entry["shape"],
            "session_key": entry["summary"]["session_key"],
            "rc": entry["rc"],
            "auth_model_failure": entry["auth_model_failure"],
            "model_provider_failure": entry["model_provider_failure"],
            "valid": entry["valid"],
            "informative": entry["informative"],
            "failed_gates": entry["failed_gates"],
            "drop_shape": entry["drop_shape"],
            "shape_labels": entry["shape_labels"],
            "trace_digest": entry["trace_digest"],
            "input_shadow_sha256": entry["input_shadow_sha256"],
            "output_shadow_sha256": entry["output_shadow_sha256"],
            "counts": {key: entry["summary"].get(key, 0) for key in
                       ("selections", "dropped_records", "dropped_pages", "page_opportunities",
                        "later_tool_recall_opportunities", "later_identifier_scan_opportunities",
                        "never_observed_opportunities", "ambiguous_opportunities")},
        }

    def _view(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        totals = Counter()
        pressure: List[float] = []
        floor_pressure: List[float] = []
        drop_share: List[float] = []
        churn: List[float] = []
        pin_events: Counter[str] = Counter()
        pin_sessions: Dict[str, set[str]] = defaultdict(set)
        for entry in entries:
            summary = entry["summary"]
            for key in ("selections", "dropped_records", "dropped_pages", "page_opportunities",
                        "unmatched_page_ids", "later_tool_recall_opportunities",
                        "later_identifier_scan_opportunities", "never_observed_opportunities",
                        "ambiguous_opportunities", "ambiguous_same_turn_events"):
                totals[key] += summary.get(key, 0)
            internal = entry["_internal"]
            pressure.extend(internal["pressure"])
            floor_pressure.extend(internal["floor_pressure"])
            drop_share.extend(internal["drop_share"])
            churn.extend(internal["selection_churn"])
            pin_events.update(internal["pin_events"])
            for pid, sessions in internal["pin_sessions"].items():
                pin_sessions[pid].update(sessions)
        opp = totals["page_opportunities"]
        enough = len(entries) >= 3
        metrics = None
        pins = []
        if enough:
            metrics = {
                "would_drop_rate": totals["dropped_records"] / totals["selections"] if totals["selections"] else None,
                "later_tool_recall_rate": totals["later_tool_recall_opportunities"] / opp if opp else None,
                "later_identifier_scan_rate": totals["later_identifier_scan_opportunities"] / opp if opp else None,
                "never_observed_rate": totals["never_observed_opportunities"] / opp if opp else None,
                "pressure": _summary(pressure), "floor_pressure": _summary(floor_pressure),
                "drop_share": _summary(drop_share), "selection_churn": _summary(churn),
            }
            for pid, count in sorted(pin_events.items()):
                if len(pin_sessions[pid]) >= 2 and count >= 3:
                    pins.append({"page_id": pid, "later_tool_recall_events": count,
                                 "sessions": len(pin_sessions[pid]), "offline_only": True,
                                 "activation": "not_authorized"})
        return {"sessions": len(entries), "counts": dict(totals), "metrics": metrics,
                "candidate_pins": pins,
                "session_keys": sorted(entry["summary"]["session_key"] for entry in entries)}

    def run(self) -> Dict[str, Any]:
        if not self.preflight_facts:
            self.preflight()
        cfg = self.config
        per_shape_target = cfg.target_informative // len(SHAPES)
        stats = {shape: {"attempts": 0, "valid": 0, "informative": 0,
                         "target": per_shape_target, "status": "PENDING"} for shape in SHAPES}
        attempts: List[Dict[str, Any]] = []
        seen_sessions: set[str] = set(self.baseline_session_ids)
        valid_entries: List[Dict[str, Any]] = []
        informative_entries: List[Dict[str, Any]] = []
        informative_count = 0
        auth_failure = False
        route_failure = False
        while len(attempts) < cfg.max_attempts and informative_count < cfg.target_informative:
            progressed = False
            for shape in SHAPES:
                if len(attempts) >= cfg.max_attempts or informative_count >= cfg.target_informative:
                    break
                if (stats[shape]["attempts"] >= cfg.max_attempts_per_shape
                        or stats[shape]["informative"] >= per_shape_target):
                    continue
                progressed = True
                entry = self._attempt(shape, len(attempts) + 1, seen_sessions)
                attempts.append(entry)
                stats[shape]["attempts"] += 1
                if entry["valid"]:
                    stats[shape]["valid"] += 1
                    valid_entries.append(entry)
                if entry["informative"]:
                    stats[shape]["informative"] += 1
                    informative_entries.append(entry)
                    informative_count += 1
                if entry["auth_model_failure"]:
                    auth_failure = True
                    break
                if entry["model_provider_failure"]:
                    route_failure = True
                    break
            if auth_failure or route_failure or not progressed:
                break
        for shape in SHAPES:
            if stats[shape]["informative"] >= per_shape_target:
                stats[shape]["status"] = "TARGET_MET"
            elif stats[shape]["attempts"] >= cfg.max_attempts_per_shape:
                stats[shape]["status"] = "UNDERPOWERED"
            elif auth_failure:
                stats[shape]["status"] = "STOPPED_AUTH_MODEL"
            elif route_failure:
                stats[shape]["status"] = "STOPPED_MODEL_PROVIDER"
            else:
                stats[shape]["status"] = "PENDING"
        if auth_failure:
            status = "STOPPED_AUTH_MODEL"
        elif route_failure:
            status = "STOPPED_MODEL_PROVIDER"
        elif informative_count >= cfg.target_informative:
            status = "TARGET_MET"
        elif all(row["status"] in ("TARGET_MET", "UNDERPOWERED") for row in stats.values()):
            status = "UNDERPOWERED"
        elif len(attempts) >= cfg.max_attempts:
            status = "ATTEMPT_CAP"
        else:
            status = "UNDERPOWERED"
        public_attempts = [self._public_attempt(entry) for entry in attempts]
        all_valid_view = {
            "pooled": self._view(valid_entries),
            "by_shape": {shape: self._view([entry for entry in valid_entries if entry["shape"] == shape])
                         for shape in SHAPES},
        }
        informative_view = {
            "pooled": self._view(informative_entries),
            "by_shape": {shape: self._view([entry for entry in informative_entries if entry["shape"] == shape])
                         for shape in SHAPES},
        }
        aggregate = {
            "schema": "ctxvm-shadow-batch-result/v1",
            "status": status,
            "target_informative": cfg.target_informative,
            "max_attempts": cfg.max_attempts,
            "max_attempts_per_shape": cfg.max_attempts_per_shape,
            "attempts": len(attempts),
            "all_valid_sessions": len(valid_entries),
            "informative_sessions": informative_count,
            "valid_without_shape_label": len(valid_entries) - informative_count,
            "shapes": stats,
            "denominator_views": {
                "all_valid": all_valid_view,
                "informative_only": informative_view,
            },
            "candidate_pins": all_valid_view["pooled"]["candidate_pins"],
            "attempt_receipts": public_attempts,
        }
        _write_private(cfg.out / "aggregate.json", json.dumps(aggregate, indent=2, sort_keys=True) + "\n")
        lines = ["# Shadow batch aggregate", "", f"Status: **{status}**", "",
                 f"Attempts: {len(attempts)}; all-valid: {len(valid_entries)}; informative: {informative_count}.",
                 "", "| shape | attempts | valid | informative | target | status |",
                 "|---|---:|---:|---:|---:|---|"]
        for shape in SHAPES:
            row = stats[shape]
            lines.append(f"| {shape} | {row['attempts']} | {row['valid']} | {row['informative']} | {row['target']} | {row['status']} |")
        lines.extend(["", "Candidate pins are offline-only and not authorized for activation.", ""])
        _write_private(cfg.out / "aggregate.md", "\n".join(lines))
        return aggregate

    def _prove_fallback_disabled(self) -> None:
        for key in ("fallback_providers", "fallback_model"):
            cmd = ["hermes", "config", "get", key, "-p", "w8-shadow", "--json"]
            try:
                result = self.sync_runner(cmd, cwd=str(self.config.repo), timeout=60,
                                          env=self.subprocess_env)
            except Exception as exc:  # noqa: BLE001 - unproven fallback state is fail-closed
                raise PreflightError(f"cannot read {key}: {type(exc).__name__}: {exc}") from exc
            text = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
            if result.returncode == 1 and "not set" in text.lower():
                continue
            if result.returncode != 0:
                raise PreflightError(f"cannot prove {key} is empty: {text}")
            try:
                value = json.loads(result.stdout or "null")
            except ValueError as exc:
                raise PreflightError(f"invalid {key} JSON: {exc}") from exc
            if value not in (None, [], {}):
                raise PreflightError(f"{key} must be empty; fallback is not authorized")

    def preflight(self) -> Dict[str, Any]:
        cfg = self.config
        if cfg.model != FROZEN_MODEL or cfg.provider != FROZEN_PROVIDER:
            raise PreflightError(f"model/provider are frozen to {FROZEN_MODEL} / {FROZEN_PROVIDER}")
        if cfg.target_informative <= 0 or cfg.target_informative % len(SHAPES):
            raise PreflightError("target-informative must be positive and divisible by three")
        if not cfg.test_mode and cfg.target_informative != MAX_TARGET_INFORMATIVE:
            raise PreflightError(
                f"live target-informative is frozen to {MAX_TARGET_INFORMATIVE}; reduced targets are test-only")
        if cfg.target_informative > MAX_TARGET_INFORMATIVE:
            raise PreflightError(f"target-informative exceeds the authorized cap of {MAX_TARGET_INFORMATIVE}")
        if cfg.max_attempts <= 0 or cfg.max_attempts_per_shape <= 0:
            raise PreflightError("attempt caps must be positive")
        if cfg.max_attempts > MAX_ATTEMPTS:
            raise PreflightError(f"max-attempts exceeds the authorized cap of {MAX_ATTEMPTS}")
        if cfg.max_attempts_per_shape > MAX_ATTEMPTS_PER_SHAPE:
            raise PreflightError(
                f"max-attempts-per-shape exceeds the authorized cap of {MAX_ATTEMPTS_PER_SHAPE}")

        hermes_home = (cfg.hermes_home or Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")).resolve()
        if not cfg.shadow.is_file() or stat.S_IMODE(cfg.shadow.stat().st_mode) != 0o600:
            raise PreflightError("shadow records must be a private 0600 file")
        if not os.access(cfg.shadow, os.R_OK):
            raise PreflightError("shadow records are not readable")
        try:
            baseline_rows = _read_jsonl(cfg.shadow)
        except (OSError, UnicodeError, ValueError) as exc:
            raise PreflightError(f"cannot parse shadow baseline: {exc}") from exc
        baseline_ids: set[str] = set()
        for row in baseline_rows:
            sid = row.get("session_id")
            if not isinstance(sid, str) or not sid:
                raise PreflightError("shadow baseline contains a record without a non-empty session_id")
            baseline_ids.add(sid)
        self.baseline_session_ids = baseline_ids
        profile_home = (cfg.profile_home or hermes_home / "profiles" / "w8-shadow").resolve()
        try:
            gateway_env = self.gateway_env_reader(hermes_home)
        except PreflightError:
            raise
        except Exception as exc:  # noqa: BLE001 - unproven gateway environment is fail-closed
            raise PreflightError(f"cannot read gateway environment: {type(exc).__name__}: {exc}") from exc
        if not isinstance(gateway_env, dict):
            raise PreflightError("gateway environment reader did not return an object")
        gateway_trace_dir = _gateway_trace_dir(gateway_env)
        if gateway_trace_dir is None or cfg.trace_dir.resolve() != gateway_trace_dir:
            raise PreflightError(
                f"requested trace-dir {cfg.trace_dir} does not match gateway trace-dir {gateway_trace_dir}")
        expected_profile = (hermes_home / "profiles" / "w8-shadow").resolve()
        if profile_home != expected_profile:
            raise PreflightError("profile-home must be the w8-shadow profile inside the validated HERMES_HOME")
        try:
            active_status = self.gateway_status_runner(
                hermes_home, profile_home, sorted(baseline_ids) or ["test-session"])
        except PreflightError:
            raise
        except Exception as exc:  # noqa: BLE001 - unproven active state is fail-closed
            raise PreflightError(f"cannot query active gateway trace status: {type(exc).__name__}") from exc
        if not isinstance(active_status, dict):
            raise PreflightError("active gateway trace status was not an object")
        active_dir = active_status.get("trace_dir")
        if isinstance(active_dir, str):
            active_dir = Path(active_dir).resolve()
        allowed_sources = {"start (defaults)", "env CTXVM_TRACE_DIR",
                           "default (set CTXVM_TRACE=0 to disable)"}
        if active_status.get("enabled") is not True or active_dir != cfg.trace_dir.resolve():
            raise PreflightError("active gateway trace directory is disabled or differs from the requested path")
        if active_status.get("source") not in allowed_sources:
            raise PreflightError("active gateway trace directory has an unapproved override")
        if active_status.get("version") != _repo_version(cfg.repo):
            raise PreflightError("active gateway trace status reports a different plugin version")
        gateway_trace_source = active_status["source"]
        self.profile_home = profile_home
        store_path = profile_home / "state.db"
        if not store_path.is_file() or not os.access(store_path, os.R_OK):
            raise PreflightError("profile session store is missing or unreadable")
        store_con = None
        try:
            store_con = sqlite3.connect(f"file:{store_path}?mode=ro", uri=True)
            store_con.execute("SELECT model, billing_provider, model_config FROM sessions LIMIT 0")
        except sqlite3.Error as exc:
            raise PreflightError(f"profile session store is not readable: {exc}") from exc
        finally:
            if store_con is not None:
                store_con.close()
        self.subprocess_env = _subprocess_env(hermes_home, cfg.trace_dir)
        versions = {
            "repo": _repo_version(cfg.repo),
            "installed": _installed_version(hermes_home),
            "manifest": _manifest_version(hermes_home),
        }
        if len(set(versions.values())) != 1:
            raise PreflightError(f"plugin versions disagree: {versions}")
        if _version(versions["repo"]) < MIN_PLUGIN_VERSION:
            raise PreflightError(f"plugin {versions['repo']} is older than 0.13.37")

        try:
            sync = self.sync_runner(["bash", str(cfg.repo / "tools" / "sync-plugin.sh"), "--check"],
                                    cwd=str(cfg.repo), timeout=120, env=self.subprocess_env)
        except Exception as exc:  # noqa: BLE001 - any preflight runner failure is fail-closed
            raise PreflightError(f"sync-plugin --check failed: {type(exc).__name__}: {exc}") from exc
        sync_text = (sync.stdout or "") + (sync.stderr or "")
        if sync.returncode != 0 or "GATEWAY STALE" in sync_text or "holds this build" not in sync_text:
            raise PreflightError("sync-plugin --check did not prove the live gateway holds this build")
        self._prove_fallback_disabled()

        policy = _load_policy(cfg.repo).policy(profile_home)
        required = {
            "profile": "w8-shadow",
            "engine": "compressor",
            "budget": 24000,
            "budgetSource": "settings",
            "shadowSelection": True,
            "shadowSelectionSource": "settings",
            "selectionMode": "fresh",
            "stubDropped": "off",
            "arm": "control",
        }
        for key, expected in required.items():
            if policy.get(key) != expected:
                raise PreflightError(f"profile policy {key}={policy.get(key)!r}, expected {expected!r}")

        _private_dir(cfg.trace_dir)
        if cfg.out.exists() and not cfg.out.is_dir():
            raise PreflightError("output path is not a directory")
        if cfg.out.exists() and any(cfg.out.iterdir()):
            raise PreflightError("output directory must be absent or empty")
        _private_dir(cfg.out, create=True)
        required_files = [
            cfg.repo / "tools/shadow-selection-validate.py",
            cfg.repo / "tools/coverage_check.py",
            cfg.repo / "spec/rfc-0.1/validate_schema_v0_1.py",
            cfg.repo / "rust/target/release/replay",
            cfg.repo / "research/shadow-analysis/join.py",
        ]
        missing = [str(path) for path in required_files if not path.is_file()]
        if missing:
            raise PreflightError("required gate files are missing: " + ", ".join(missing))
        replay = cfg.repo / "rust/target/release/replay"
        if not os.access(replay, os.X_OK):
            raise PreflightError("Rust replay binary is not executable")
        self.join = _load_join(cfg.repo)
        self.fixtures = load_fixtures(cfg.fixture_manifest)
        self.preflight_facts = {
            "plugin_version": versions["repo"],
            "model": cfg.model,
            "provider": cfg.provider,
            "profile": profile_home.name,
            "budgetTokens": policy["budget"],
            "shadowSelection": True,
            "selectionMode": policy["selectionMode"],
            "stubDropped": policy["stubDropped"],
            "fallbackDisabled": True,
            "sessionStoreReady": True,
            "gatewayTraceDir": str(gateway_trace_dir),
            "gatewayTraceSource": gateway_trace_source,
            "fixture_manifest_sha256": hashlib.sha256(cfg.fixture_manifest.read_bytes()).hexdigest(),
            "target_informative": cfg.target_informative,
            "max_attempts": cfg.max_attempts,
            "max_attempts_per_shape": cfg.max_attempts_per_shape,
            "baseline_sessions": len(self.baseline_session_ids),
        }
        return self.preflight_facts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--shadow", required=True, type=Path)
    parser.add_argument("--trace-dir", required=True, type=Path)
    parser.add_argument("--fixture-manifest", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--target-informative", type=int, default=12)
    parser.add_argument("--max-attempts", type=int, default=18)
    parser.add_argument("--max-attempts-per-shape", type=int, default=6)
    parser.add_argument("--model", default=FROZEN_MODEL)
    parser.add_argument("--provider", default=FROZEN_PROVIDER)
    parser.add_argument("--hermes-home", type=Path, default=None)
    parser.add_argument("--profile-home", type=Path, default=None)
    parser.add_argument("--preflight-only", action="store_true",
                        help="prove every preflight fact and exit without running a model session")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = Config(
        repo=args.repo.resolve(), shadow=args.shadow.resolve(), trace_dir=args.trace_dir.resolve(),
        fixture_manifest=args.fixture_manifest.resolve(), out=args.out.resolve(),
        target_informative=args.target_informative, max_attempts=args.max_attempts,
        max_attempts_per_shape=args.max_attempts_per_shape, model=args.model, provider=args.provider,
        hermes_home=args.hermes_home.resolve() if args.hermes_home else None,
        profile_home=args.profile_home.resolve() if args.profile_home else None,
    )
    try:
        collector = Collector(cfg)
        if args.preflight_only:
            facts = collector.preflight()
            print(json.dumps(facts, sort_keys=True))
            return 0
        result = collector.run()
    except PreflightError as exc:
        print(f"collect-shadow: preflight failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "status": result["status"],
        "attempts": result["attempts"],
        "all_valid_sessions": result["all_valid_sessions"],
        "informative_sessions": result["informative_sessions"],
        "candidate_pins": len(result["candidate_pins"]),
    }, sort_keys=True))
    if result["status"] == "TARGET_MET":
        return 0
    if result["status"] in ("STOPPED_AUTH_MODEL", "STOPPED_MODEL_PROVIDER"):
        return 4
    return 3


if __name__ == "__main__":
    sys.exit(main())

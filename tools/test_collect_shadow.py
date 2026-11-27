#!/usr/bin/env python3
"""No-model tests for tools/collect-shadow.py."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("collect_shadow", ROOT / "tools" / "collect-shadow.py")
assert SPEC is not None and SPEC.loader is not None
collect = importlib.util.module_from_spec(SPEC)
sys.modules["collect_shadow"] = collect
SPEC.loader.exec_module(collect)

VERSION = "0.13.37"
MODEL = "tencent/hy4-flash:free"
PROVIDER = "nous"
SHAPES = ("read-once-pressure", "deliberate-later-reread", "dependency-chain")


def write_plugin(home: Path, version: str = VERSION) -> None:
    live = home / "packages" / "hermes" / "live"
    live.mkdir(parents=True, exist_ok=True)
    (live / "__init__.py").write_text(f'PLUGIN_VERSION = "{version}"\n')
    (live / "plugin.yaml").write_text(f"version: {version}\n")
    shutil.copy2(ROOT / "packages" / "hermes" / "live" / "profile_policy.py", live / "profile_policy.py")


def write_installed(hermes_home: Path, version: str = VERSION) -> None:
    dest = hermes_home / "plugins" / "ctxvm-tracer"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "__init__.py").write_text(f'PLUGIN_VERSION = "{version}"\n')
    (dest / "plugin.yaml").write_text(f"version: {version}\n")


def write_sync_script(repo: Path, text: str) -> None:
    path = repo / "tools" / "sync-plugin.sh"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\n" + text + "\n")
    path.chmod(0o700)


def write_profile(profile_home: Path, *, engine="compressor", budget=24000,
                  shadow=True, mode="fresh", stub="off") -> None:
    profile_home.mkdir(parents=True, exist_ok=True)
    (profile_home / "config.yaml").write_text(
        "context:\n"
        f"  engine: {engine}\n"
        "plugins:\n"
        "  entries:\n"
        "    ctxvm-tracer:\n"
        "      settings:\n"
        f"        budgetTokens: {budget}\n"
        f"        shadowSelection: {str(shadow).lower()}\n"
        f"        selectionMode: {mode}\n"
        f"        stubDropped: {stub}\n"
    )


def write_manifest(path: Path) -> dict:
    shapes = {}
    for shape in SHAPES:
        workspace = path.parent / shape
        workspace.mkdir(parents=True, exist_ok=True)
        file = workspace / "fixture.txt"
        file.write_text(f"fixture for {shape}\n")
        shapes[shape] = {
            "workspace": shape,
            "prompt": f"frozen prompt for {shape}",
            "files": [{"path": "fixture.txt", "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}],
        }
    data = {"schema": "ctxvm-shadow-fixtures/v1", "shapes": shapes}
    path.write_text(json.dumps(data, indent=2) + "\n")
    return data


def write_required_gates(repo: Path) -> None:
    for rel in ("tools/shadow-selection-validate.py", "tools/coverage_check.py",
                "spec/rfc-0.1/validate_schema_v0_1.py", "research/shadow-analysis/join.py"):
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel == "research/shadow-analysis/join.py":
            shutil.copy2(ROOT / rel, path)
        else:
            path.write_text("# fake gate for no-model collector tests\n")
    replay = repo / "rust/target/release/replay"
    replay.parent.mkdir(parents=True, exist_ok=True)
    replay.write_text("#!/usr/bin/env bash\nexit 0\n")
    replay.chmod(0o700)


def make_config(root: Path, **overrides) -> Any:
    repo = root / "repo"
    hermes_home = root / "hermes"
    profile_home = hermes_home / "profiles" / "w8-shadow"
    trace_dir = root / "traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_dir.chmod(0o700)
    shadow = root / "selection.jsonl"
    shadow.write_text("")
    shadow.chmod(0o600)
    manifest = root / "fixtures.json"
    write_plugin(repo)
    write_installed(hermes_home)
    write_sync_script(repo, "echo 'gateway: pid 123 started after these files were written; it holds this build.'")
    write_required_gates(repo)
    write_profile(profile_home)
    write_manifest(manifest)
    values = dict(
        repo=repo,
        shadow=shadow,
        trace_dir=trace_dir,
        fixture_manifest=manifest,
        out=root / "out",
        target_informative=12,
        max_attempts=18,
        max_attempts_per_shape=6,
        model=MODEL,
        provider=PROVIDER,
        hermes_home=hermes_home,
        profile_home=profile_home,
    )
    values.update(overrides)
    return collect.Config(**values)


class PreflightTests(unittest.TestCase):
    def test_accepts_frozen_profile_private_paths_and_manifest(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
            cfg = make_config(Path(td))
            facts = collect.Collector(cfg, sync_runner=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "gateway: pid 123 started after these files were written; it holds this build.\n", "")).preflight()
            self.assertEqual(facts["plugin_version"], VERSION)
            self.assertEqual(facts["model"], MODEL)
            self.assertEqual(facts["provider"], PROVIDER)
            self.assertEqual(stat.S_IMODE(cfg.out.stat().st_mode), 0o700)

    def test_rejects_stale_plugin_version(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
            cfg = make_config(Path(td))
            write_plugin(cfg.repo, "0.13.36")
            write_installed(cfg.hermes_home, "0.13.36")
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "gateway: pid 123 holds this build.\n", "")).preflight()

    def test_missing_version_files_are_preflight_errors(self):
        paths = (
            "packages/hermes/live/__init__.py",
            "plugins/ctxvm-tracer/__init__.py",
            "plugins/ctxvm-tracer/plugin.yaml",
        )
        for rel in paths:
            with self.subTest(path=rel), tempfile.TemporaryDirectory(prefix="collect-shadow-missing-version-") as td:
                cfg = make_config(Path(td))
                root = cfg.repo if rel.startswith("packages/") else cfg.hermes_home
                (root / rel).unlink()
                with self.assertRaises(collect.PreflightError):
                    collect.Collector(cfg, sync_runner=sync_ok).preflight()

    def test_rejects_stale_gateway_even_when_sync_exits_zero(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
            cfg = make_config(Path(td))
            runner = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "GATEWAY STALE: pid 123\nsync-plugin: OK\n", "")
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=runner).preflight()

    def test_sync_runner_exception_is_a_preflight_error(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-sync-error-") as td:
            cfg = make_config(Path(td))
            def broken_sync(cmd, **kw):
                raise subprocess.TimeoutExpired(cmd, kw.get("timeout", 120))
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=broken_sync).preflight()

    def test_rejects_wrong_profile_budget_shadow_mode_and_stub(self):
        cases = [
            {"engine": "ctxvm"},
            {"budget": 200000},
            {"shadow": False},
            {"mode": "stable"},
            {"stub": "recoverable"},
        ]
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
                cfg = make_config(Path(td))
                write_profile(cfg.profile_home, **case)
                with self.assertRaises(collect.PreflightError):
                    collect.Collector(cfg, sync_runner=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "gateway: pid 123 holds this build.\n", "")).preflight()

    def test_rejects_wrong_model_or_provider(self):
        for overrides in ({"model": "paid/model"}, {"provider": "openrouter"}):
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
                cfg = make_config(Path(td), **overrides)
                with self.assertRaises(collect.PreflightError):
                    collect.Collector(cfg, sync_runner=sync_ok).preflight()

    def test_rejects_owner_caps_missing_gates_and_reused_output(self):
        cases = [
            {"target_informative": 15},
            {"max_attempts": 19},
            {"max_attempts_per_shape": 7},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
                cfg = make_config(Path(td), **overrides)
                with self.assertRaises(collect.PreflightError):
                    collect.Collector(cfg, sync_runner=sync_ok).preflight()
        with tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
            cfg = make_config(Path(td))
            (cfg.repo / "rust/target/release/replay").unlink()
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=sync_ok).preflight()
        with tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
            cfg = make_config(Path(td))
            cfg.out.mkdir(mode=0o700)
            (cfg.out / "old.txt").write_text("old")
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=sync_ok).preflight()

    def test_rejects_version_disagreement_unsafe_fixtures_and_bad_private_files(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
            cfg = make_config(Path(td))
            write_installed(cfg.hermes_home, "0.13.38")
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=sync_ok).preflight()
        for field, value in (("workspace", None), ("workspace", "/absolute"),
                             ("files", "not-a-list")):
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
                cfg = make_config(Path(td))
                data = json.loads(cfg.fixture_manifest.read_text())
                data["shapes"][SHAPES[0]][field] = value
                cfg.fixture_manifest.write_text(json.dumps(data))
                with self.assertRaises(collect.PreflightError):
                    collect.Collector(cfg, sync_runner=sync_ok).preflight()
        with tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
            cfg = make_config(Path(td))
            cfg.shadow.chmod(0o644)
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=sync_ok).preflight()
        with tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
            cfg = make_config(Path(td))
            (cfg.repo / "rust/target/release/replay").chmod(0o600)
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=sync_ok).preflight()

    def test_rejects_unsafe_fixture_paths_and_bad_private_files(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
            cfg = make_config(Path(td))
            data = json.loads(cfg.fixture_manifest.read_text())
            data["shapes"][SHAPES[0]]["workspace"] = None
            cfg.fixture_manifest.write_text(json.dumps(data))
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=sync_ok).preflight()
        with tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
            cfg = make_config(Path(td))
            cfg.out.write_text("not a directory")
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=sync_ok).preflight()
        with tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
            cfg = make_config(Path(td))
            cfg.shadow.chmod(0o644)
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=sync_ok).preflight()
        with tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
            cfg = make_config(Path(td))
            (cfg.repo / "rust/target/release/replay").chmod(0o600)
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=sync_ok).preflight()

    def test_rejects_fixture_hash_mismatch_and_nonprivate_trace_dir(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-preflight-") as td:
            root = Path(td)
            cfg = make_config(root)
            fixture = cfg.fixture_manifest.parent / SHAPES[0] / "fixture.txt"
            fixture.write_text("tampered\n")
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "gateway: pid 123 holds this build.\n", "")).preflight()
            write_manifest(cfg.fixture_manifest)
            cfg.trace_dir.chmod(0o755)
            with self.assertRaises(collect.PreflightError):
                collect.Collector(cfg, sync_runner=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "gateway: pid 123 holds this build.\n", "")).preflight()


def page_id(ref: str, digest: str) -> str:
    return "sha256:" + hashlib.sha256((ref + "|" + digest).encode()).hexdigest()


def shadow_record(sid: str, pid: str, *, call=0, turn=0,
                  ts="2026-11-27T10:00:00.000Z", floor=17000,
                  resident=33000, dropped=15000, budget=24000) -> dict:
    return {
        "schema": "ctxvm-shadow-selection/v1",
        "session_id": sid,
        "turn": turn,
        "call_index": call,
        "ts": ts,
        "policy": {"name": "keep-law", "version": "test", "mode": "fresh"},
        "budget_tokens": budget,
        "resident_tokens": resident,
        "floor_tokens": floor,
        "dropped_tokens": dropped,
        "dropped_pages": [{"page_id": pid, "tokens": dropped, "kind": "tool_result"}],
        "repositioned_pages": [],
        "selection_hash": "sha256:" + "a" * 64,
        "prefix_hash": "sha256:" + "b" * 64,
        "trigger": "overflow",
        "request_unchanged": True,
        "policy_applied": False,
    }


def write_fake_session(cfg: Any, sid: str, *, label: Optional[str] = None,
                       floor=17000, resident=33000, dropped=15000, budget=24000,
                       model=MODEL, provider=PROVIDER, selections=1,
                       process_failures=0, arm="control",
                       ref='tool:read_file({"path":"private/secret.md"})') -> None:
    digest = "sha256:abcdef01"
    pid = page_id(ref, digest)
    rows = [
        {"type": "session.open", "agentId": "hermes", "model": model,
         "provider": provider, "budgetTokens": 24000, "tokenizerId": "apx4-char",
         "schemaVersion": "0.1", "environmentId": "env-123456789abc",
         "ts": "2026-11-27T09:59:00.000Z"},
        {"type": "page.declare", "turn": 0,
         "page": {"id": {"logicalRef": ref, "contentHash": digest},
                  "kind": "tool_result", "tokens": dropped},
         "toolEffect": "READ_ONLY", "ts": "2026-11-27T09:59:01.000Z"},
        {"type": "turn.render", "turn": 0, "residentTokens": resident,
         "evictedTokens": 0, "headroom": 24000 - resident,
         "ts": "2026-11-27T09:59:02.000Z"},
        {"type": "call.meta", "turn": 0, "provider": provider,
         "cacheEstimate": {"estHitTokens": 0, "estMissTokens": 0,
                           "providerReported": False},
         "ts": "2026-11-27T09:59:03.000Z"},
    ]
    if label:
        rows.append({"type": "page.fault", "turn": 1, "source": label,
                     "page": {"logicalRef": ref, "contentHash": digest},
                     "ts": "2026-11-27T10:00:01.000Z"})
    raw = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows).encode()
    trace = cfg.trace_dir / f"{sid}.jsonl"
    trace.write_bytes(raw)
    trace.chmod(0o600)
    coverage = {
        "xcabiCoverage": "0.1",
        "traceFile": trace.name,
        "traceDigest": hashlib.sha256(raw).hexdigest(),
        "session": {"sessionID": sid, "model": model, "provider": provider,
                    "environmentId": "env-123456789abc"},
        "plugin": {"version": VERSION, "profile": "w8-shadow", "arm": arm,
                   "engineSetting": "compressor", "engineSelections": 0,
                   "budgetTokens": 24000, "budgetSource": "settings",
                   "shadowSelection": True, "shadowSelectionSource": "settings",
                   "shadowSelections": selections, "shadowWriteFailures": 0,
                   "shadowWriteFailuresProcess": process_failures, "stubDropped": "off"},
    }
    cov = cfg.trace_dir / f"{sid}.coverage.json"
    cov.write_text(json.dumps(coverage, indent=2) + "\n")
    cov.chmod(0o600)
    with cfg.shadow.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(shadow_record(sid, pid, floor=floor, resident=resident,
                                          dropped=dropped, budget=budget), sort_keys=True) + "\n")
    cfg.shadow.chmod(0o600)


class FakeSessionRunner:
    def __init__(self, cfg: Any, plans: Dict[str, List[dict]],
                 gate_runner: Optional[Callable[..., subprocess.CompletedProcess[str]]] = None,
                 join_runner: Optional[Callable[..., subprocess.CompletedProcess[str]]] = None):
        self.cfg = cfg
        self.plans = {shape: list(items) for shape, items in plans.items()}
        self.calls: List[List[str]] = []
        self.observed_fixtures: List[bytes] = []
        self.gate_runner = gate_runner or (lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "", ""))
        self._join_impl = join_runner or (lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, '{"status":"OK"}', ""))
        self.join_calls: List[List[str]] = []
        self.join_runner = self._record_join

    def _record_join(self, cmd: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.join_calls.append(list(cmd))
        return self._join_impl(cmd, **kwargs)

    def __call__(self, cmd: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        args = list(cmd)
        self.calls.append(args)
        workspace = Path(args[args.index("--in") + 1])
        shape = workspace.name
        fixture_file = workspace / "fixture.txt"
        self.observed_fixtures.append(fixture_file.read_bytes())
        fixture_file.write_text("model changed this workspace\n")
        plan = self.plans[shape].pop(0)
        if plan.get("auth_failure"):
            return subprocess.CompletedProcess(args, 1, "", "401 Unauthorized: model unavailable")
        sid = plan.get("sid", f"local-{shape}-{len(self.calls):04d}")
        write_fake_session(self.cfg, sid, label=plan.get("label"),
                           floor=plan.get("floor", 17000),
                           resident=plan.get("resident", 33000),
                           dropped=plan.get("dropped", 15000),
                           budget=plan.get("budget", 24000),
                           model=plan.get("model", MODEL),
                           provider=plan.get("provider", PROVIDER),
                           selections=plan.get("selections", 1),
                           process_failures=plan.get("process_failures", 0),
                           arm=plan.get("arm", "control"),
                           ref=plan.get("ref", 'tool:read_file({"path":"private/secret.md"})'))
        stdout = f"Session: {sid}\nanswer body must stay private\nsk-abcdefghijklmnop\n/home/private/workspace\n"
        return subprocess.CompletedProcess(args, plan.get("rc", 0), stdout, plan.get("stderr", ""))


def green_gates(cmd: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    args = list(cmd)
    if args and Path(args[0]).name == "replay":
        return subprocess.CompletedProcess(args, 0, '{"events":5,"divergences":[],"violations":[]}', "")
    return subprocess.CompletedProcess(args, 0, "OK", "")


def green_join(cmd: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(list(cmd), 0, '{"status":"OK"}', "")


def sync_ok(cmd: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(list(cmd), 0,
                                       "gateway: pid 123 started after these files were written; it holds this build.\n", "")


class ExecutionTests(unittest.TestCase):
    def test_fake_runner_creates_private_snapshots_and_dual_denominators(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-run-") as td:
            cfg = make_config(Path(td), target_informative=3, max_attempts=3,
                              max_attempts_per_shape=1)
            plans = {
                "read-once-pressure": [{}],
                "deliberate-later-reread": [{"label": "tool_recall"}],
                "dependency-chain": [{"label": "identifier_scan"}],
            }
            session = FakeSessionRunner(cfg, plans, gate_runner=green_gates, join_runner=green_join)
            collector = collect.Collector(cfg, sync_runner=sync_ok, session_runner=session,
                                           gate_runner=green_gates, join_runner=session.join_runner)
            config_before = (cfg.profile_home / "config.yaml").read_bytes()
            result = collector.run()
            self.assertEqual((cfg.profile_home / "config.yaml").read_bytes(), config_before)
            for call in session.calls:
                self.assertIn("--oneshot", call)
                self.assertEqual(call[call.index("--max-turns") + 1], "20")
                self.assertEqual(call[call.index("--model") + 1], MODEL)
                self.assertEqual(call[call.index("--provider") + 1], PROVIDER)
                self.assertEqual(call[call.index("-p") + 1], "w8-shadow")
                for forbidden in ("--create-if-missing", "--continue", "--resume"):
                    self.assertNotIn(forbidden, call)
            self.assertEqual(result["status"], "TARGET_MET")
            self.assertEqual(result["attempts"], 3)
            self.assertEqual(result["all_valid_sessions"], 3)
            self.assertEqual(result["informative_sessions"], 3)
            self.assertEqual(result["denominator_views"]["all_valid"]["sessions"], 3)
            self.assertEqual(result["denominator_views"]["informative_only"]["sessions"], 3)
            self.assertEqual(len(session.join_calls), 3)
            for call in session.join_calls:
                self.assertIn(str(cfg.shadow), call)
                self.assertIn(str(cfg.trace_dir), call)
            attempt_dirs = sorted((cfg.out / "attempts").iterdir())
            self.assertEqual(len(attempt_dirs), 3)
            for directory in attempt_dirs:
                self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
                for name in ("stdout.txt", "stderr.txt", "receipt.json", "trace.jsonl",
                             "coverage.json", "shadow-delta.jsonl"):
                    path = directory / name
                    self.assertTrue(path.exists(), (directory, name))
                    self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
                receipt = json.loads((directory / "receipt.json").read_text())
                self.assertEqual(receipt["requested_model"], MODEL)
                self.assertEqual(receipt["requested_provider"], PROVIDER)
                self.assertEqual(receipt["observed_model"], MODEL)
                self.assertEqual(receipt["observed_provider"], PROVIDER)
                self.assertEqual(len(receipt["input_shadow_sha256"]), 64)
                self.assertEqual(len(receipt["output_shadow_sha256"]), 64)
                self.assertEqual(len(receipt["trace_digest"]), 64)
                self.assertEqual([gate["name"] for gate in receipt["gates"]],
                                 ["shadow_schema", "coverage_check", "v01_schema", "replay"])
                self.assertEqual(receipt["join"]["rc"], 0)
            aggregate = (cfg.out / "aggregate.json").read_text()
            for forbidden in ("private/secret.md", "answer body must stay private", str(cfg.repo),
                              "sk-abcdefghijklmnop", "/home/private/workspace",
                              "local-read-once-pressure-0001",
                              "frozen prompt for read-once-pressure", str(cfg.fixture_manifest.parent)):
                self.assertNotIn(forbidden, aggregate)
            self.assertTrue((cfg.out / "aggregate.md").exists())

    def test_each_attempt_uses_a_fresh_private_fixture_snapshot(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-fixture-copy-") as td:
            cfg = make_config(Path(td), target_informative=6, max_attempts=6,
                              max_attempts_per_shape=2)
            plans = {
                "read-once-pressure": [{}, {}],
                "deliberate-later-reread": [{"label": "tool_recall"}, {"label": "tool_recall"}],
                "dependency-chain": [{"label": "identifier_scan"}, {"label": "identifier_scan"}],
            }
            source = {shape: (cfg.fixture_manifest.parent / shape / "fixture.txt").read_bytes()
                      for shape in SHAPES}
            session = FakeSessionRunner(cfg, plans, gate_runner=green_gates, join_runner=green_join)
            result = collect.Collector(cfg, sync_runner=sync_ok, session_runner=session,
                                       gate_runner=green_gates, join_runner=session.join_runner).run()
            self.assertEqual(result["status"], "TARGET_MET")
            self.assertEqual(session.observed_fixtures,
                             [source[Path(call[call.index("--in") + 1]).name] for call in session.calls])
            workspaces = [Path(call[call.index("--in") + 1]) for call in session.calls]
            self.assertEqual(len(set(workspaces)), 6)
            for workspace in workspaces:
                self.assertEqual(stat.S_IMODE(workspace.stat().st_mode), 0o700)
                self.assertEqual(stat.S_IMODE((workspace / "fixture.txt").stat().st_mode), 0o600)
            for shape, expected in source.items():
                self.assertEqual((cfg.fixture_manifest.parent / shape / "fixture.txt").read_bytes(), expected)

    def test_gate_failure_excludes_attempt_and_auth_failure_stops_all(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-run-") as td:
            cfg = make_config(Path(td), target_informative=3, max_attempts=5,
                              max_attempts_per_shape=2)
            plans = {
                "read-once-pressure": [{}, {}],
                "deliberate-later-reread": [{"auth_failure": True}],
                "dependency-chain": [{}],
            }
            session = FakeSessionRunner(cfg, plans)
            failed_once = {"done": False}
            def gates(cmd, **kw):
                if not failed_once["done"] and any("coverage_check.py" in str(part) for part in cmd):
                    failed_once["done"] = True
                    return subprocess.CompletedProcess(list(cmd), 1, "bad coverage", "")
                return green_gates(cmd, **kw)
            collector = collect.Collector(cfg, sync_runner=sync_ok, session_runner=session,
                                           gate_runner=gates, join_runner=session.join_runner)
            result = collector.run()
            self.assertEqual(result["status"], "STOPPED_AUTH_MODEL")
            self.assertEqual(result["attempts"], 2)
            self.assertEqual(result["all_valid_sessions"], 0)
            self.assertEqual(result["informative_sessions"], 0)
            receipts = [json.loads(p.read_text()) for p in sorted((cfg.out / "attempts").glob("*/receipt.json"))]
            self.assertEqual(receipts[0]["valid"], False)
            self.assertIn("coverage_check", receipts[0]["failed_gates"])
            self.assertTrue(receipts[1]["auth_model_failure"])

    def test_drop_shape_and_shape_label_control_informativeness(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-run-") as td:
            cfg = make_config(Path(td), target_informative=3, max_attempts=3,
                              max_attempts_per_shape=1)
            plans = {
                "read-once-pressure": [{}],
                "deliberate-later-reread": [{}],
                "dependency-chain": [{"label": "identifier_scan"}],
            }
            session = FakeSessionRunner(cfg, plans, gate_runner=green_gates, join_runner=green_join)
            result = collect.Collector(cfg, sync_runner=sync_ok, session_runner=session,
                                       gate_runner=green_gates, join_runner=session.join_runner).run()
            self.assertEqual(result["status"], "UNDERPOWERED")
            self.assertEqual(result["all_valid_sessions"], 3)
            self.assertEqual(result["informative_sessions"], 2)
            self.assertEqual(result["valid_without_shape_label"], 1)
            self.assertEqual(result["denominator_views"]["all_valid"]["sessions"], 3)
            self.assertEqual(result["denominator_views"]["informative_only"]["sessions"], 2)

    def test_schema_checker_replay_and_drop_shape_failures_exclude_attempt(self):
        cases = ("shadow_schema", "coverage_check", "v01_schema", "replay", "drop_shape")
        for failed in cases:
            with self.subTest(failed=failed), tempfile.TemporaryDirectory(prefix="collect-shadow-gates-") as td:
                cfg = make_config(Path(td), target_informative=3, max_attempts=3,
                                  max_attempts_per_shape=1)
                plans = {
                    "read-once-pressure": [{"floor": 24000} if failed == "drop_shape" else {}],
                    "deliberate-later-reread": [{}],
                    "dependency-chain": [{"label": "identifier_scan"}],
                }
                session = FakeSessionRunner(cfg, plans)
                failed_once = {"done": False}
                def gates(cmd, **kw):
                    if failed == "replay":
                        if not failed_once["done"] and Path(str(cmd[0])).name == "replay":
                            failed_once["done"] = True
                            return subprocess.CompletedProcess(
                                list(cmd), 0,
                                '{"events":5,"divergences":[{"seq":2,"kind":"faultOfResidentPage"}],"violations":[]}',
                                "")
                        return green_gates(cmd, **kw)
                    if failed in ("shadow_schema", "coverage_check", "v01_schema"):
                        script = {"shadow_schema": "shadow-selection-validate.py",
                                  "coverage_check": "coverage_check.py",
                                  "v01_schema": "validate_schema_v0_1.py"}[failed]
                        if (not failed_once["done"]
                                and any(script in str(part) for part in cmd)):
                            failed_once["done"] = True
                            return subprocess.CompletedProcess(list(cmd), 1, "engineered failure", "")
                    return green_gates(cmd, **kw)
                result = collect.Collector(cfg, sync_runner=sync_ok, session_runner=session,
                                           gate_runner=gates, join_runner=session.join_runner).run()
                receipt = json.loads(sorted((cfg.out / "attempts").glob("*/receipt.json"))[0].read_text())
                self.assertFalse(receipt["valid"])
                self.assertIn(failed, receipt["failed_gates"])
                self.assertEqual(result["all_valid_sessions"], 2)

    def test_join_exit_three_is_accepted_and_other_exit_excludes(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-join-") as td:
            cfg = make_config(Path(td), target_informative=3, max_attempts=3,
                              max_attempts_per_shape=1)
            plans = {shape: [{}] for shape in SHAPES}
            session = FakeSessionRunner(cfg, plans)
            join_calls = {"n": 0}
            def join(cmd, **kw):
                join_calls["n"] += 1
                rc = 3 if join_calls["n"] == 1 else 0
                return subprocess.CompletedProcess(list(cmd), rc, '{"status":"INSUFFICIENT_DATA"}', "")
            result = collect.Collector(cfg, sync_runner=sync_ok, session_runner=session,
                                       gate_runner=green_gates, join_runner=join).run()
            self.assertEqual(result["all_valid_sessions"], 3)
            receipts = [json.loads(p.read_text()) for p in sorted((cfg.out / "attempts").glob("*/receipt.json"))]
            self.assertEqual(receipts[0]["join"]["rc"], 3)
            self.assertTrue(receipts[0]["valid"])

        with tempfile.TemporaryDirectory(prefix="collect-shadow-join-") as td:
            cfg = make_config(Path(td), target_informative=3, max_attempts=3,
                              max_attempts_per_shape=1)
            plans = {shape: [{}] for shape in SHAPES}
            session = FakeSessionRunner(cfg, plans)
            bad_join = lambda cmd, **kw: subprocess.CompletedProcess(list(cmd), 2, "", "join failed")
            result = collect.Collector(cfg, sync_runner=sync_ok, session_runner=session,
                                       gate_runner=green_gates, join_runner=bad_join).run()
            receipt = json.loads(sorted((cfg.out / "attempts").glob("*/receipt.json"))[0].read_text())
            self.assertFalse(receipt["valid"])
            self.assertIn("join_contract", receipt["failed_gates"])
            self.assertEqual(result["all_valid_sessions"], 0)

    def test_provider_unknown_is_recorded_but_known_drift_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-provider-") as td:
            cfg = make_config(Path(td), target_informative=3, max_attempts=3,
                              max_attempts_per_shape=1)
            plans = {
                "read-once-pressure": [{"provider": "unknown"}],
                "deliberate-later-reread": [{"label": "tool_recall", "provider": "unknown"}],
                "dependency-chain": [{"label": "identifier_scan", "provider": "unknown"}],
            }
            session = FakeSessionRunner(cfg, plans)
            result = collect.Collector(cfg, sync_runner=sync_ok, session_runner=session,
                                       gate_runner=green_gates, join_runner=session.join_runner).run()
            self.assertEqual(result["all_valid_sessions"], 3)
            receipt = json.loads(sorted((cfg.out / "attempts").glob("*/receipt.json"))[0].read_text())
            self.assertEqual(receipt["requested_provider"], PROVIDER)
            self.assertEqual(receipt["observed_provider"], "unknown")

    def test_identity_budget_and_selection_count_drift_exclude_attempt(self):
        cases = [
            ({"model": "other/model"}, "sidecar_model"),
            ({"provider": "other"}, "sidecar_provider"),
            ({"budget": 20000}, "record_budget"),
            ({"selections": 2}, "sidecar_selections"),
            ({"process_failures": 1}, "sidecar_process_failures"),
            ({"arm": "paged"}, "sidecar_arm"),
        ]
        for plan, reason in cases:
            with self.subTest(plan=plan), tempfile.TemporaryDirectory(prefix="collect-shadow-identity-") as td:
                cfg = make_config(Path(td), target_informative=3, max_attempts=3,
                                  max_attempts_per_shape=1)
                plans = {
                    "read-once-pressure": [plan],
                    "deliberate-later-reread": [{"label": "tool_recall"}],
                    "dependency-chain": [{"label": "identifier_scan"}],
                }
                session = FakeSessionRunner(cfg, plans)
                result = collect.Collector(cfg, sync_runner=sync_ok, session_runner=session,
                                           gate_runner=green_gates, join_runner=session.join_runner).run()
                receipt = json.loads(sorted((cfg.out / "attempts").glob("*/receipt.json"))[0].read_text())
                self.assertFalse(receipt["valid"])
                self.assertIn(reason, receipt["failed_gates"])
                self.assertEqual(result["all_valid_sessions"], 2)

    def test_candidate_pins_are_hashed_offline_only_and_not_authorized(self):
        pid = "sha256:" + "a" * 64
        entries = []
        for sid, events in (("s1", 2), ("s2", 1), ("s3", 0)):
            entries.append({
                "summary": {"session_key": "sha256:" + hashlib.sha256(sid.encode()).hexdigest()[:16],
                            "selections": 1, "dropped_records": 1, "dropped_pages": 1,
                            "page_opportunities": 1},
                "_internal": {"pressure": [], "floor_pressure": [], "drop_share": [],
                              "selection_churn": [], "pin_events": Counter({pid: events}),
                              "pin_sessions": {pid: {sid}}},
            })
        view = collect.Collector._view(None, entries)
        self.assertEqual(len(view["candidate_pins"]), 1)
        pin = view["candidate_pins"][0]
        self.assertEqual(pin["page_id"], pid)
        self.assertIs(pin["offline_only"], True)
        self.assertEqual(pin["activation"], "not_authorized")

    def test_cli_preflight_only_never_runs_a_session(self):
        args = ["--repo", "/repo", "--shadow", "/shadow", "--trace-dir", "/traces",
                "--fixture-manifest", "/fixtures.json", "--out", "/out", "--preflight-only"]
        facts = {"plugin_version": VERSION, "model": MODEL, "provider": PROVIDER}
        with mock.patch.object(collect, "Collector") as cls:
            cls.return_value.preflight.return_value = facts
            with mock.patch("sys.stdout"), mock.patch("sys.stderr"):
                self.assertEqual(collect.main(args), 0)
            cls.return_value.preflight.assert_called_once_with()
            cls.return_value.run.assert_not_called()

    def test_cli_exit_contract_without_model_calls(self):
        args = ["--repo", "/repo", "--shadow", "/shadow", "--trace-dir", "/traces",
                "--fixture-manifest", "/fixtures.json", "--out", "/out"]
        base = {"status": "TARGET_MET", "attempts": 12, "all_valid_sessions": 12,
                "informative_sessions": 12, "candidate_pins": []}
        for status, expected in (("TARGET_MET", 0), ("UNDERPOWERED", 3),
                                 ("ATTEMPT_CAP", 3), ("STOPPED_AUTH_MODEL", 4)):
            with self.subTest(status=status), mock.patch.object(collect, "Collector") as cls:
                cls.return_value.run.return_value = dict(base, status=status)
                with mock.patch("sys.stdout"), mock.patch("sys.stderr"):
                    self.assertEqual(collect.main(args), expected)
        with mock.patch.object(collect, "Collector") as cls:
            cls.return_value.run.side_effect = collect.PreflightError("blocked")
            with mock.patch("sys.stdout"), mock.patch("sys.stderr"):
                self.assertEqual(collect.main(args), 2)

    def test_aggregate_omits_private_run_metadata(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-privacy-") as td:
            cfg = make_config(Path(td), target_informative=3, max_attempts=3,
                              max_attempts_per_shape=1)
            plans = {
                "read-once-pressure": [{}],
                "deliberate-later-reread": [{"label": "tool_recall"}],
                "dependency-chain": [{"label": "identifier_scan"}],
            }
            session = FakeSessionRunner(cfg, plans)
            result = collect.Collector(cfg, sync_runner=sync_ok, session_runner=session,
                                       gate_runner=green_gates, join_runner=session.join_runner).run()
            aggregate = json.dumps(result)
            for forbidden in (str(cfg.repo), str(cfg.out), str(cfg.fixture_manifest.parent),
                              "tencent/hy4-flash:free", "nous", "0.13.37"):
                self.assertNotIn(forbidden, aggregate)

    def test_total_cap_and_per_shape_cap_stop_without_broadening(self):
        with tempfile.TemporaryDirectory(prefix="collect-shadow-run-") as td:
            cfg = make_config(Path(td), target_informative=6, max_attempts=4,
                              max_attempts_per_shape=2)
            plans = {shape: [{}, {}] for shape in SHAPES}
            session = FakeSessionRunner(cfg, plans, gate_runner=green_gates, join_runner=green_join)
            result = collect.Collector(cfg, sync_runner=sync_ok, session_runner=session,
                                       gate_runner=green_gates, join_runner=session.join_runner).run()
            self.assertEqual(result["status"], "ATTEMPT_CAP")
            self.assertEqual(result["attempts"], 4)
            self.assertEqual(result["shapes"]["read-once-pressure"]["attempts"], 2)
            self.assertEqual(result["shapes"]["deliberate-later-reread"]["attempts"], 1)
            self.assertEqual(result["shapes"]["dependency-chain"]["attempts"], 1)


if __name__ == "__main__":
    unittest.main()

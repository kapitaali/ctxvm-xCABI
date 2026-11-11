#!/usr/bin/env python3
"""W8B end-to-end run: both arms, then verification, then a record. No spend (free tier).

One command runs the experiment and refuses to run it wrong. Every check in `preflight` exists
because one of them was missing at some point in this card:

  * profile must carry `toolsets: [file]`      (the H6 run shelled out 16 times without it)
  * paged profile must declare 70000           (a budget default is not a treatment)
  * model and provider must be the W8B pair    (a run on gpt-6-luna would silently cost money)
  * no stale artefact.json                     (a PASS on yesterday's file is not a measurement)
  * fixture must be 20 parts                   (a sealed prompt 12 needs the parts to exist)
  * gateway must be newer than the installed plugin file
  * a session that never flushes is NO RECORD, not a failed cell

It does not edit the repo. It writes a bundle under the state dir and prints the rows to paste.

Usage:
  python3 tools/w8b-run.py --dry-run                 # preflight + the exact commands, no calls
  python3 tools/w8b-run.py                           # both arms, 120 s per prompt
  python3 tools/w8b-run.py --arms paged              # one arm
  python3 tools/w8b-run.py --timeout 180 --record    # append the chunklog rows too
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import re
import subprocess
import urllib.error
import urllib.request
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "tools/w8-driver.py"
CHECKER = ROOT / "tools/w8-checker-ta-v2.py"   # T-A v2: tool-reported values only
PROFILES = Path.home() / ".hermes" / "profiles"
TRACES = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "ctxvm" / "traces"
BUDGET = 70000
PARTS = 20

# Two ways to run the same experiment on someone else's free tier. The provider is not a detail:
# it decides the model id, the profile pair (model/provider are PROFILE settings because the CLI
# refuses creation overrides on resume), and which API key must exist.
PROVIDERS = {
    "nvidia": {
        "model": "nvidia/nemotron-3.5-super-vl-120b-a12b",
        "provider": "nvidia",
        "prefix": "w8b",
        "key": "NVIDIA_API_KEY",
        "auth": "env",
        "note": "the run of 2026-11-10: tool-calling works, $0.00, naive arm completed",
    },
    "openrouter": {
        "model": "nvidia/nemotron-3.5-lightning:free",
        "provider": "openrouter",
        "prefix": "w8bo",
        "key": "OPENROUTER_API_KEY",
        "auth": "env",
        "note": "free tier via OpenRouter; capability unproven, prompt 1 decides",
    },
    "nous": {
        "model": "meituan/longcat-2.5:free",
        "provider": "nous",
        "prefix": "w8bn",
        "key": None,
        "auth": "oauth",
        "note": "Nous Portal free models (stepfun/step-3.7-flash:free, meituan/longcat-2.5:free); --model picks",
    },
}


def sh(cmd: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)


def cfg(key: str, arm: str, prefix: str) -> str:
    r = sh(["hermes", "config", "get", key, "-p", f"{prefix}-{arm}"])
    return (r.stdout if r.returncode == 0 else r.stderr).strip()


KEY_PROBES = {
    "nvidia": "https://integrate.api.nvidia.com/v1/models",
    "openrouter": "https://openrouter.ai/api/v1/key",
}


def _env_key_from(path: Path, name: str) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text(errors="ignore").splitlines():
        if line.strip().startswith(f"{name}="):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            if val:
                return val
    return None


def _env_key(name: str) -> str | None:
    return _env_key_from(Path.home() / ".hermes" / ".env", name)


def sync_profile_keys(spec: dict) -> None:
    """Copy the root key into each arm profile's .env when they differ.

    A profile is its own HERMES_HOME, and the loader reads `<home>/.env`
    (hermes_cli/env_loader.py:216). So a profile created by copying another one carries a
    SNAPSHOT of the key: updating ~/.hermes/.env alone leaves the run using the old key, and the
    failure surfaces as an auth error at prompt 1. Measured 2026-11-10.
    """
    root = _env_key_from(Path.home() / ".hermes" / ".env", spec["key"])
    if not root:
        return
    for arm in ("naive", "paged"):
        f = PROFILES / f"{spec['prefix']}-{arm}" / ".env"
        if not f.exists():
            continue
        lines = f.read_text().splitlines()
        cur = next((l.split("=", 1)[1].strip() for l in lines if l.startswith(spec["key"] + "=")), None)
        if cur == root:
            continue
        out, replaced = [], False
        for line in lines:
            if line.startswith(spec["key"] + "=") and not replaced:
                out.append(f"{spec['key']}={root}")
                replaced = True
            else:
                out.append(line)
        if not replaced:
            out.append(f"{spec['key']}={root}")
        f.write_text("\n".join(out) + "\n")
        print(f"synced {spec['key']} into {f} (a profile .env shadows the root .env)")


def check_key(spec: dict) -> str | None:
    if spec.get("auth") == "oauth":
        auth = Path.home() / ".hermes" / "auth.json"
        try:
            d = json.loads(auth.read_text())
            tok = (d.get("providers", {}).get(spec["provider"]) or {}).get("access_token")
        except Exception:
            tok = None
        if not tok:
            return f"no OAuth access token for {spec['provider']} in ~/.hermes/auth.json (run hermes auth add {spec['provider']})"
        return None
    """Presence is not validity. A 401 from the provider costs one free request; discovering it at
    prompt 1 of a 20-prompt session costs the session (measured 2026-11-10: OPENROUTER_API_KEY was
    set and dead — 401 "User not found")."""
    key = _env_key(spec["key"])
    if not key:
        return f"{spec['key']} is not set in ~/.hermes/.env"
    url = KEY_PROBES.get(spec["provider"])
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=15) as r:
            if 200 <= r.status < 300:
                return None
            return f"{spec['provider']} returned HTTP {r.status} for the key"
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read()[:120].decode("utf-8", "replace")
        except Exception:
            pass
        return f"{spec['provider']} rejected the key: HTTP {exc.code} {body}"
    except Exception as exc:
        return f"key check could not reach {url}: {type(exc).__name__} (use --skip-key-check offline)"


def _set_model_provider(cfgp: Path, model: str, provider: str) -> bool:
    """Rewrite the model.default / model.provider lines, line-wise.

    String replacement failed the first time a third model id appeared (it only knew the ids
    hard-coded in the loop). Reading the two lines under `model:` is stable regardless of which
    model the profile currently carries.
    """
    lines = cfgp.read_text().splitlines()
    changed = False
    in_model = False
    for i, line in enumerate(lines):
        if line.startswith("model:"):
            in_model = True
            continue
        if in_model and line.startswith("  default:"):
            new = f'  default: "{model}"'
            changed |= lines[i] != new
            lines[i] = new
        elif in_model and line.startswith("  provider:"):
            new = f'  provider: "{provider}"'
            changed |= lines[i] != new
            lines[i] = new
            in_model = False
    if changed:
        cfgp.write_text("\n".join(lines) + "\n")
    return changed


PROFILE_COUNT = 2   # one pair: naive + paged. Not one per provider, not one per model.


def profiles_for(prefix: str) -> list[Path]:
    return sorted(p for p in PROFILES.glob(f"{prefix}-*") if p.is_dir())


def ensure_profiles(spec: dict) -> None:
    """Never create a profile. Refuse and say what is missing.

    An earlier version provisioned a missing pair by copying another one, which is how eight
    profiles (368 MB, ~170 sessions) appeared in the owner's Hermes install. The owner does not want
    the experiment to add profiles. A missing pair is now a refusal that names the two paths, and
    preflight reports it too, so nothing is created even by accident.
    """
    missing = []
    for arm in ("naive", "paged"):
        dst = PROFILES / f"{spec['prefix']}-{arm}"
        if not dst.exists():
            missing.append(str(dst))
            continue
        if _set_model_provider(dst / "config.yaml", spec["model"], spec["provider"]):
            print(f"updated {dst} -> model={spec['model']} provider={spec['provider']}")
    if missing:
        print("refusing to create profiles (the owner's rule): " + ", ".join(missing))
    found = profiles_for(spec["prefix"])
    if len(found) > PROFILE_COUNT:
        print(f"note: {len(found)} profiles match {spec['prefix']}-* — only {PROFILE_COUNT} are wanted "
              f"({', '.join(p.name for p in found)})")


def preflight(arms: list[str], spec: dict) -> list[str]:
    # The owner's rule: exactly one pair. A third profile under this prefix means something
    # provisioned one; refuse rather than run against an ambiguous arm.
    found = profiles_for(spec["prefix"])
    if len(found) != PROFILE_COUNT:
        return [f"expected exactly {PROFILE_COUNT} profiles matching {spec['prefix']}-*, "
                f"found {len(found)}: {', '.join(p.name for p in found) or 'none'}"]
    errs: list[str] = []
    plugin = Path.home() / ".hermes" / "plugins" / "ctxvm-tracer" / "__init__.py"
    if not plugin.exists():
        errs.append(f"installed plugin missing: {plugin}")
    else:
        gw = sh(["pgrep", "-af", "hermes.*gateway"])
        pid = next((line.split()[0] for line in gw.stdout.splitlines() if "gateway" in line), None)
        if pid:
            st = sh(["ps", "-o", "lstart=", "-p", pid]).stdout.strip()
            try:
                started = time.mktime(time.strptime(" ".join(st.split()), "%a %b %d %H:%M:%S %Y"))
                if started < plugin.stat().st_mtime:
                    errs.append(f"gateway PID {pid} started before the plugin file; restart before running")
            except Exception:
                pass
        else:
            errs.append("no hermes gateway process found")
    if not (len(sys.argv) > 1 and "--skip-key-check" in sys.argv):
        key_err = check_key(spec)
        if key_err:
            errs.append(key_err)
    for arm in arms:
        prof = PROFILES / f"{spec['prefix']}-{arm}"
        if not prof.is_dir():
            errs.append(f"profile missing: {prof}")
            continue
        ts = cfg("toolsets", arm, spec["prefix"])
        if "file" not in ts:
            errs.append(f"w8b-{arm} toolsets is {ts!r}; expected [file]")
        model = cfg("model.default", arm, spec["prefix"])
        prov = cfg("model.provider", arm, spec["prefix"])
        if spec["model"] not in model:
            errs.append(f"{spec['prefix']}-{arm} model is {model!r}; expected {spec['model']}")
        if spec["provider"] not in prov:
            errs.append(f"{spec['prefix']}-{arm} provider is {prov!r}; expected {spec['provider']}")
        if arm == "paged":
            b = cfg("plugins.entries.ctxvm-tracer.settings.budgetTokens", arm, spec["prefix"])
            if str(BUDGET) not in b:
                errs.append(f"w8b-paged budget is {b!r}; expected {BUDGET}")
        ws = ROOT / "experiments" / "w8b" / f"ws-{arm}"
        fixture = ws / "fixture"
        if not fixture.is_dir():
            errs.append(f"workspace fixture missing: {fixture}")
        else:
            n = len(list(fixture.glob("part-*.txt")))
            if n != PARTS:
                errs.append(f"{fixture} has {n} parts; expected {PARTS}")
        # A stale artefact is archived, not deleted: the previous run's output is evidence.
        # It just must not be in place when the next run starts.archived in main().
    if not DRIVER.exists():
        errs.append(f"driver missing: {DRIVER}")
    return errs


def session_id(arm: str, title: str, prefix: str) -> str | None:
    db = PROFILES / f"{prefix}-{arm}" / "state.db"
    if not db.exists():
        return None
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    row = c.execute("select id from sessions where title=? order by rowid desc limit 1", (title,)).fetchone()
    return row[0] if row else None


def capture_for(sid: str) -> Path | None:
    p = TRACES / f"{sid}.jsonl"
    return p if p.exists() else None


def run_arm(arm: str, run_id: str, timeout: int, spec: dict) -> dict:
    title = f"{run_id}-{arm}"
    run_dir = Path.home() / ".local" / "state" / "ctxvm" / "w8-runs" / run_id / arm
    run_dir.mkdir(parents=True, exist_ok=True)
    ws = ROOT / "experiments" / "w8b" / f"ws-{arm}"
    env = dict(os.environ)
    env["HERMES_HOME"] = str(PROFILES / f"{spec['prefix']}-{arm}")
    started = time.time()
    print(f"\n[{arm}] driver -> {run_dir}")
    r = subprocess.run([sys.executable, str(DRIVER), "--arm", arm, "--session-name", title,
                        "--workspace", str(ws), "--run-dir", str(run_dir),
                        "--profile-prefix", spec["prefix"], "--expect-budget", str(BUDGET),
                        "--timeout", str(timeout)],
                       text=True, capture_output=True, env=env, timeout=PARTS * timeout + 300)
    (run_dir / "driver.out").write_text(r.stdout, encoding="utf-8")
    (run_dir / "driver.err").write_text(r.stderr, encoding="utf-8")
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "(no driver output)")
    out = {"arm": arm, "title": title, "driver_rc": r.returncode,
           "wall_s": round(time.time() - started, 1), "verdict": None, "checks": [],
           "capture": None, "cost_usd": None, "calls": None}
    if r.returncode != 0:
        out["verdict"] = "DATA-INVALID" if "TIMEOUT" not in r.stderr else "NO RECORD"
        print(f"[{arm}] driver stopped: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'rc=' + str(r.returncode)}")
        return out

    # Prefer the id the CLI printed ("Session: local-…"); it equals the capture filename. The DB row
    # id is not always the same value, and the "newest sidecar" fallback is polluted by any other
    # session writing at the same time — including the operator's own chat.
    m = re.search(r"^Session:\s+(local-[0-9a-f]{64})", r.stdout or "", re.M)
    printed_sid = m.group(1) if m else None
    sid = printed_sid or session_id(arm, title, spec["prefix"])
    cap = capture_for(sid) if sid else None
    out["session_id"] = sid
    out["capture"] = str(cap) if cap else None
    if not cap:
        out["verdict"] = "NO RECORD"
        print(f"[{arm}] NO RECORD — session {sid} never flushed")
        return out

    v = sh([sys.executable, str(DRIVER), "--capture", str(cap), "--expect-budget",
            str(BUDGET) if arm == "paged" else "any"])
    (run_dir / "verify.txt").write_text(v.stdout + v.stderr, encoding="utf-8")
    for line in v.stdout.splitlines():
        if line.strip().startswith("["):
            out["checks"].append(line.strip())
        if line.startswith("verify: verdict"):
            out["verdict"] = line.split()[-1]
    print(v.stdout.strip())

    if arm == "paged":
        art = ws / "artefact.json"
        if art.exists():
            c = sh([sys.executable, str(CHECKER), str(ws / "fixture"), str(art)])
            (run_dir / "checker.txt").write_text(c.stdout + c.stderr, encoding="utf-8")
            print(f"[{arm}] checker exit {c.returncode}: {c.stdout.strip().splitlines()[-1] if c.stdout.strip() else ''}")
            out["checker_rc"] = c.returncode

    db = PROFILES / f"{spec['prefix']}-{arm}" / "state.db"
    if sid and db.exists():
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        row = c.execute("select api_call_count, estimated_cost_usd, input_tokens, output_tokens "
                        "from sessions where id=?", (sid,)).fetchone()
        if row:
            out["calls"], out["cost_usd"] = row[0], row[1]
            out["in"], out["out"] = row[2], row[3]
    return out



PROBE_PROMPT = ("Use the read_file tool to read fixture/part-01.txt and reply with its byte count. "
                "You have exactly three tools: read_file, search_files, write_file. "
                "Do not ask for any other tool.")


def probe(spec: dict, run_id: str, arm: str = "paged") -> dict:
    """One prompt: can this model drive the read_file surface? Nothing else is measured."""
    title = f"{run_id}-probe-{arm}"
    ws = ROOT / "experiments" / "w8b" / f"ws-{arm}"
    env = dict(os.environ)
    env["HERMES_HOME"] = str(PROFILES / f"{spec['prefix']}-{arm}")
    started = time.time()
    cmd = ["hermes", "chat", "-q", PROBE_PROMPT, "--oneshot", "-c", title,
           "--create-if-missing", "--in", str(ws)]
    r = subprocess.run(cmd, text=True, capture_output=True, env=env, timeout=300)
    out = {"probe": True, "model": spec["model"], "provider": spec["provider"],
           "rc": r.returncode, "wall_s": round(time.time() - started, 1), "tool_calls": 0,
           "tools": {}, "reply": "", "cost": None, "verdict": "NO TOOL CALLS"}
    sid = session_id(arm, title, spec["prefix"])
    if sid:
        db = PROFILES / f"{spec['prefix']}-{arm}" / "state.db"
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        for role, content, tool in c.execute(
                "select role,content,tool_name from messages where session_id=? order by rowid", (sid,)):
            if tool or role == "tool":
                out["tools"][tool or "?"] = out["tools"].get(tool or "?", 0) + 1
                out["tool_calls"] += 1
            if role == "assistant" and content:
                out["reply"] = content.strip()[:200]
        row = c.execute("select estimated_cost_usd from sessions where id=?", (sid,)).fetchone()
        out["cost"] = row[0] if row else None
        # The precondition the prediction block demands: did the host ever SELECT with the engine?
        # The capture name is not guaranteed to equal the DB session id, so look for the newest
        # sidecar written during this probe rather than deriving a path that may not exist.
        traces = Path.home() / ".local" / "state" / "ctxvm" / "traces"
        plug = {}
        out["sidecar"] = None
        candidates = ([traces / f"{sid}.coverage.json"] if sid else []) +                      sorted((f for f in traces.glob("*.coverage.json")
                             if f.stat().st_mtime >= started - 2), key=lambda f: f.stat().st_mtime)
        for cand in candidates:
            try:
                plug = json.loads(cand.read_text()).get("plugin", {})
                out["sidecar"] = cand.name
                break
            except Exception:
                continue
        out["engine"] = plug.get("engine")
        out["engineSelections"] = plug.get("engineSelections")
        out["profile"] = plug.get("profile")
        out["budget"] = f"{plug.get('budgetTokens')}/{plug.get('budgetSource')}"
        out["precondition"] = ("READY" if (plug.get("engineSelections") or 0) > 0
                               else "NOT READY — engine never selected; a pair cannot start")
    if out["tool_calls"] and any(t in ("read_file", "search_files", "write_file") for t in out["tools"]):
        out["verdict"] = "TOOL CALLS OK"
    if out.get("precondition", "").startswith("NOT READY"):
        out["verdict"] = f"{out['verdict']} / {out['precondition']}"
    print(json.dumps(out, indent=2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None, help="override the provider's default model id")
    ap.add_argument("--arm", choices=["naive", "paged", "both"], default="paged",
                    help="which arm the probe uses (both = the contrast check)")
    ap.add_argument("--probe", action="store_true",
                    help="one capability prompt on the paged arm, then stop (no cells)")
    ap.add_argument("--provider", choices=sorted(PROVIDERS), default="nvidia",
                    help="nvidia = nemotron-3.5-super-vl-120b-a12b via NIM; "
                         "openrouter = nemotron-3.5-lightning:free via OpenRouter")
    ap.add_argument("--arms", default="naive,paged")
    ap.add_argument("--timeout", type=int, default=120, help="seconds per prompt (naive averages 4-7)")
    ap.add_argument("--run-id", default=time.strftime("w8b-%Y%m%d-%H%M%S"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--record", action="store_true", help="append the chunklog rows (repo edit)")
    ap.add_argument("--skip-key-check", action="store_true",
                    help="do not call the provider's free key endpoint (offline use only)")
    args = ap.parse_args()
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    spec = dict(PROVIDERS[args.provider])
    if args.model:
        spec["model"] = args.model
    print(f"provider {args.provider}: model {spec['model']} ({spec['note']})")
    # A dry run must not write anything, including a model/provider rewrite of a live profile.
    if not args.dry_run:
        ensure_profiles(spec)
        sync_profile_keys(spec)

    errs = preflight(arms, spec)
    if errs:
        print("PREFLIGHT FAILED — nothing ran:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 2

    bundle0 = Path.home() / ".local" / "state" / "ctxvm" / "w8-runs" / args.run_id / "stale"
    for arm in arms:
        ws = ROOT / "experiments" / "w8b" / f"ws-{arm}"
        art = ws / "artefact.json"
        if art.exists():
            bundle0.mkdir(parents=True, exist_ok=True)
            dst = bundle0 / f"{arm}-artefact.json"
            shutil.move(str(art), str(dst))
            print(f"archived stale artefact: {art} -> {dst}")

    if args.probe:
        arms = ["naive", "paged"] if args.arm == "both" else [args.arm]
        results = [probe(spec, args.run_id, a) for a in arms]
        if len(results) == 2:
            same = (results[0].get("engine"), results[0].get("engineSelections") is not None and
                    (results[0].get("engineSelections") or 0) > 0) ==                    (results[1].get("engine"), (results[1].get("engineSelections") or 0) > 0)
            print(json.dumps({"contrast": "NO CONTRAST — both arms look identical" if same
                              else "CONTRAST OK", "arms": [{k: r.get(k) for k in
                              ("model", "engine", "engineSelections", "profile", "budget", "precondition")}
                              for r in results]}, indent=2))
        return 0

    if args.dry_run:
        for arm in arms:
            print(f"[{arm}] python3 tools/w8-driver.py --arm {arm} --session-name {args.run_id}-{arm} "
                  f"--workspace experiments/w8b/ws-{arm} --run-dir <state>/w8-runs/{args.run_id}/{arm} "
                  f"--profile-prefix {spec['prefix']} --expect-budget {BUDGET} --timeout {args.timeout}")
        print(f"dry-run OK — provider {args.provider}, {len(arms)} arm(s), {PARTS} prompts each, "
              f"{args.timeout}s cap, model {spec['model']}")
        return 0

    results = [run_arm(a, args.run_id, args.timeout, spec) for a in arms]
    for r in results:
        r["provider"] = args.provider
        r["model"] = spec["model"]

    bundle = Path.home() / ".local" / "state" / "ctxvm" / "w8-runs" / args.run_id
    (bundle / "summary.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    rows = []
    for r in results:
        rows.append(f"| {r['title']} | {r.get('calls')} | {r.get('in')} | {r.get('out')} | "
                    f"${r.get('cost_usd') or 0:.4f} | {r['verdict']} | {r.get('wall_s')}s |")
    md = ("| session | calls | in | out | cost | verdict | wall |\n|---|---|---|---|---|---|---|\n"
          + "\n".join(rows) + "\n")
    (bundle / "summary.md").write_text(md, encoding="utf-8")
    print("\n" + md)
    if args.record:
        log = ROOT / "reports" / "W8B-CHUNKLOG.md"
        with log.open("a", encoding="utf-8") as fh:
            for r in results:
                fh.write(f"| {time.strftime('%Y-%m-%dT%H:%M')} | {r['arm']} | {r.get('calls')} | "
                         f"${r.get('cost_usd') or 0:.4f} | {r['verdict']} | {r.get('capture') or 'none'} |\n")
        print(f"recorded -> {log}")
    bad = [r for r in results if r["verdict"] in (None, "DATA-INVALID", "NO RECORD")]
    print(f"bundle: {bundle}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

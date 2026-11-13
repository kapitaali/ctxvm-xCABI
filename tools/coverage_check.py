#!/usr/bin/env python3
"""coverage_check.py — the authoritative validator of xCABI coverage manifests (W17).

usage:
    python tools/coverage_check.py TRACE.jsonl TRACE.coverage.json

Exit codes: 0 = manifest consistent with the trace bytes it covers; 1 = law
violation (every violated check printed, one per line); 2 = usage / IO / JSON
error — nothing was verified. Stdlib only, no repo imports: this file IS the
law, so it must run on any python and is invoked through subprocess on purpose.

W17 (08.1-UPDATE-PROMPT.md): a coverage manifest is a sidecar
`<file>.coverage.json` written by a flush lane at FULL FLUSH only — never at
write-through partials (partial pruning would leave coverage describing bytes
that no longer exist) — and NOT a tenth trace event: the sealed nine-verb
envelope is untouched; the manifest describes a run's instrumentation, it does
not report a harness observation.

Shape v0.1 and what this checker proves for each claim:

  xcabiCoverage      "0.1" — this checker's manifest shape version.
  traceFile          basename of the trace the manifest covers.
  traceDigest        sha256 of the trace bytes — a manifest only ever describes
                     the bytes physically present at the flushed path
                     (RR-LIVE-20261104: trace names can be reused by a later
                     session, so the digest is what ties the pair).
  session{}          identity facts. sessionID is carried for meta pairing and
                     is NOT byte-verifiable; environmentId, model and provider
                     must agree with the trace's single `session.open` row.
  toolTable{}        {readOnlyRegistered: [...], default: "MUTATING"} — the W15
                     registration + fail-safe law; unregistered tools are NOT
                     enumerated. `default` other than "MUTATING" is a law
                     violation, never an extension.
  instrumentation{}  {ts, toolEffect, identifierScan} — REAL lane toggles.
                     ts: true means ts on 100% of events; toolEffect: true
                     means every tool_result declare carries READ_ONLY or
                     MUTATING; identifierScan has no byte shadow yet — the
                     field documents that the scan instrumentation ran. All
                     three are lane-fixed constants for the hermes lane.
  plugin{}           {version, harness, harnessVersion, engine, profile} — descriptive
                     pairing. `engine` is the registered engine name or null, `profile`
                     is the serving profile directory. Both are OPTIONAL in 0.1 so an
                     older sidecar still validates, but a W8 cell REQUIRES them: without
                     them a capture cannot be attributed to an arm after the fact.
                     facts, asserted present and typed only.
  captures{}         counts that must match observation exactly: turns
                     (distinct turn.render boundaries), pages (distinct
                     declared logicalRef+contentHash pairs), declares (rows),
                     declaresByClass (READ_ONLY/MUTATING stamps on tool_result
                     declares), faults (rows), faultsBySource (the four codec
                     sources, all keys always present, exact equality).

The registration law runs on what the trace MUST already carry: for every
tool_result declare that stamps a toolEffect, the tool name (text between
`tool:` and the first `(` in the logicalRef, matched by full name and by leaf —
the segment after the last dot) must be consistent with the table: registered
READ_ONLY tools never carry MUTATING; unregistered names never carry READ_ONLY.

Violations to be exact: checksums prove only what the white paper at
research/white-paper/white-paper.md:258 says they prove; this file makes that
pair-verifiable, which is a different claim from tamper evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

COVERAGE_VERSION = "0.1"
TOOL_EFFECTS = ("READ_ONLY", "MUTATING")
FAULT_SOURCES = ("tool_recall", "identifier_scan", "explicit_api", "semantic")
SESSION_AGREED = ("environmentId", "model", "provider")

USAGE = "usage: coverage_check.py TRACE.jsonl MANIFEST.coverage.json"


def _leaf(tool: str) -> str:
    """A tool name matches its table entry by full string or last dot segment."""
    return tool.rsplit(".", 1)[-1]


def _tool_of(logical_ref: str) -> str | None:
    """The W15 name law: the text between `tool:` and the first `(`."""
    if not logical_ref.startswith("tool:"):
        return None
    return logical_ref[len("tool:"):].split("(", 1)[0] or None


def _registered(tool: str, table) -> bool:
    return tool in table or _leaf(tool) in table


def _int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _fail(violations: list, check: str, detail: str) -> None:
    violations.append(f"{check}: {detail}")


def main(argv: list) -> int:
    if len(argv) != 2:
        print(USAGE, file=sys.stderr)
        return 2
    trace_path, manifest_path = argv
    try:
        with open(trace_path, "rb") as fh:
            trace_bytes = fh.read()
        rows = [json.loads(text) for text in trace_bytes.decode("utf-8").splitlines() if text.strip()]
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"coverage_check: {exc}", file=sys.stderr)
        return 2

    violations: list = []

    # ---- shape: every required key present and typed (the law is self-noted) ----
    if not isinstance(manifest, dict):
        print("coverage_check: manifest is not a JSON object", file=sys.stderr)
        return 2
    for key in ("xcabiCoverage", "traceFile", "traceDigest", "session",
                "toolTable", "instrumentation", "plugin", "captures"):
        if key not in manifest:
            _fail(violations, "shape", f"missing required key `{key}`")
    if manifest.get("xcabiCoverage") != COVERAGE_VERSION:
        _fail(violations, "shape",
              f"xcabiCoverage must be {COVERAGE_VERSION!r}, got {manifest.get('xcabiCoverage')!r}")
    if manifest.get("traceFile") != os.path.basename(trace_path):
        _fail(violations, "digest",
              f"traceFile {manifest.get('traceFile')!r} != coverable file {os.path.basename(trace_path)!r}")
    digest = hashlib.sha256(trace_bytes).hexdigest()
    if manifest.get("traceDigest") != digest:
        _fail(violations, "digest",
              f"traceDigest {manifest.get('traceDigest')!r} != sha256(bytes) {digest!r}")

    session_block = manifest.get("session") if isinstance(manifest.get("session"), dict) else None
    tool_table = manifest.get("toolTable") if isinstance(manifest.get("toolTable"), dict) else None
    instrument = manifest.get("instrumentation") if isinstance(manifest.get("instrumentation"), dict) else None
    plugin = manifest.get("plugin") if isinstance(manifest.get("plugin"), dict) else None
    captures = manifest.get("captures") if isinstance(manifest.get("captures"), dict) else None

    # ---- the trace's single session.open row is the byte truth for identity ----
    opens = [r for r in rows if r.get("type") == "session.open"]
    open_row = None
    if len(opens) != 1:
        detail = f"trace has {len(opens)} session.open rows; the manifest claims one session"
        _fail(violations, "session", detail)
    else:
        open_row = opens[0]
    if session_block is not None and not isinstance(session_block.get("sessionID"), str):
        _fail(violations, "session", "session.sessionID must be a string (pairing fact, not byte-verified)")
    if session_block is not None and open_row is not None:
        for key in SESSION_AGREED:
            if session_block.get(key) != open_row.get(key):
                _fail(violations, "session",
                      f"session.{key} {session_block.get(key)!r} disagrees with session.open {open_row.get(key)!r}")

    # ---- instrumentation.ts: the claim is 100% coverage, so it is checkable ----
    if instrument is not None and instrument.get("ts") is True:
        missing = [i for i, r in enumerate(rows) if not (isinstance(r.get("ts"), str) and r["ts"].strip())]
        if missing:
            shown = ", ".join(f"row {i} ({rows[i].get('type')})" for i in missing[:3])
            _fail(violations, "instrumentation",
                  f"ts: true claimed but {len(missing)} row(s) have no ts — {shown}")

    # ---- toolEffect: claim + enum lint (the enum lint runs on stamps that exist) ----
    declares = [r for r in rows if r.get("type") == "page.declare"]
    tool_results = [r for r in declares if isinstance(r.get("page"), dict)
                    and r["page"].get("kind") == "tool_result"]
    if instrument is not None and instrument.get("toolEffect") is True:
        untagged = [r for r in tool_results if r.get("toolEffect") not in TOOL_EFFECTS]
        if untagged:
            shown = ", ".join(f"row {rows.index(r)}" for r in untagged[:3])
            _fail(violations, "instrumentation",
                  f"toolEffect: true claimed but {len(untagged)} tool_result declare(s) "
                  f"carry no READ_ONLY/MUTATING class — {shown}")
    for row in rows:
        effect = row.get("toolEffect")
        if effect is not None and effect not in TOOL_EFFECTS:
            _fail(violations, "instrumentation",
                  f"stamped toolEffect {effect!r} is outside the READ_ONLY/MUTATING enum")

    # ---- the W15 registration law, checked against the stamps that exist ----
    if tool_table is not None:
        if tool_table.get("default") != "MUTATING":
            _fail(violations, "toolTable",
                  f"default must be the MUTATING fail-safe, got {tool_table.get('default')!r}")
        registered = tool_table.get("readOnlyRegistered")
        if not isinstance(registered, list) or any(not isinstance(t, str) for t in registered):
            _fail(violations, "toolTable", "readOnlyRegistered must be a list of strings")
        elif isinstance(instrument, dict) and instrument.get("toolEffect") is True:
            for row in tool_results:
                page = row.get("page") or {}
                ref = (page.get("id") or {}).get("logicalRef", "")
                tool = _tool_of(ref)
                if tool is None:
                    _fail(violations, "toolTable",
                          f"tool_result declare does not name its tool: {ref[:60]!r}")
                    continue
                stamped = row.get("toolEffect")
                if stamped == "READ_ONLY" and not _registered(tool, registered):
                    _fail(violations, "toolTable",
                          f"{tool!r} carries READ_ONLY but is not in the registration table")
                if stamped == "MUTATING" and _registered(tool, registered):
                    _fail(violations, "toolTable",
                          f"registered READ_ONLY tool {tool!r} carries MUTATING")

    # ---- captures: every count must match observation exactly ----
    if captures is not None:
        turns = {r["turn"] for r in rows if r.get("type") == "turn.render" and _int(r.get("turn"))}
        pages = {(r["page"]["id"]["logicalRef"], r["page"]["id"]["contentHash"])
                 for r in declares if isinstance(r.get("page"), dict)
                 and isinstance(r["page"].get("id"), dict)}
        by_class = {e: 0 for e in TOOL_EFFECTS}
        for row in tool_results:
            if row.get("toolEffect") in by_class:
                by_class[row["toolEffect"]] += 1
        faults = [r for r in rows if r.get("type") == "page.fault"]
        by_source = {s: 0 for s in FAULT_SOURCES}
        for row in faults:
            if row.get("source") in by_source:
                by_source[row["source"]] += 1
        # W8C: the observer's prose-mention counts. They cannot be derived from the trace — prose is
        # telemetry, not an event — so the checker validates shape, that every key names a page the
        # trace declared, and that the total agrees. This is what lets a diagnostic prove the scan
        # still SEES prose while pinning nothing.
        pm = captures.get("proseMentions")
        if pm is not None:
            if not isinstance(pm, dict) or not all(
                    isinstance(k, str) and _int(v) for k, v in pm.items()):
                _fail(violations, "captures", "proseMentions must map logicalRef -> integer")
            else:
                declared_refs = {r["page"]["id"]["logicalRef"] for r in declares
                                 if isinstance(r.get("page"), dict)
                                 and isinstance(r["page"].get("id"), dict)}
                unknown = sorted(set(pm) - declared_refs)
                if unknown:
                    _fail(violations, "captures",
                          f"proseMentions names pages the trace never declared: {unknown[:3]}")
                if captures.get("proseMentionsTotal") != sum(pm.values()):
                    _fail(violations, "captures",
                          f"proseMentionsTotal {captures.get('proseMentionsTotal')!r} "
                          f"!= sum(proseMentions) {sum(pm.values())!r}")

        expected = {
            "turns": len(turns),
            "pages": len(pages),
            "declares": len(declares),
            "declaresByClass": by_class,
            "faults": len(faults),
            "faultsBySource": by_source,
        }
        if not _int(captures.get("turns")) or not _int(captures.get("pages")) \
                or not _int(captures.get("declares")) or not _int(captures.get("faults")):
            _fail(violations, "captures", "turns/pages/declares/faults must be integers")
        if captures.get("turns") != expected["turns"]:
            _fail(violations, "captures",
                  f"turns {captures.get('turns')!r} != observed {expected['turns']!r} "
                  f"(distinct turn.render boundaries)")
        if captures.get("pages") != expected["pages"]:
            _fail(violations, "captures",
                  f"pages {captures.get('pages')!r} != observed {expected['pages']!r}")
        if captures.get("declares") != expected["declares"]:
            _fail(violations, "captures",
                  f"declares {captures.get('declares')!r} != observed {expected['declares']!r}")
        if captures.get("faults") != expected["faults"]:
            _fail(violations, "captures",
                  f"faults {captures.get('faults')!r} != observed {expected['faults']!r}")
        if captures.get("declaresByClass") != expected["declaresByClass"]:
            _fail(violations, "captures",
                  f"declaresByClass {captures.get('declaresByClass')!r} != observed "
                  f"{expected['declaresByClass']!r}")
        if captures.get("faultsBySource") != expected["faultsBySource"]:
            _fail(violations, "captures",
                  f"faultsBySource {captures.get('faultsBySource')!r} != observed "
                  f"{expected['faultsBySource']!r}")

    # ---- perCall: the per-turn resident series, byte-true against the trace ----
    # ADDITIVE, OPTIONAL (shape 0.1 stays valid without it). The manifest may carry one
    # sample per turn.render, in trace order: turn, residentTokens, and — when the row has
    # a measured prefix — requestChars / approxInputTokens. A flat series is the failure
    # this field exists to expose: before 2026-11-07 the emitter stamped every render with
    # the flush-time total, so a long session's pages looked constant.
    series = manifest.get("perCall")
    if series is not None:
        renders = [r for r in rows if r.get("type") == "turn.render"]
        if not isinstance(series, list):
            _fail(violations, "perCall", "must be a list of per-turn samples")
        elif len(series) != len(renders):
            _fail(violations, "perCall",
                  f"{len(series)} samples != {len(renders)} turn.render rows in the trace")
        else:
            for k, (claim, row) in enumerate(zip(series, renders)):
                if not isinstance(claim, dict):
                    _fail(violations, "perCall", f"sample {k} is not an object")
                    continue
                if claim.get("turn") != row.get("turn"):
                    _fail(violations, "perCall",
                          f"sample {k} turn {claim.get('turn')!r} != {row.get('turn')!r}")
                if claim.get("residentTokens") != row.get("residentTokens"):
                    _fail(violations, "perCall",
                          f"sample {k} residentTokens {claim.get('residentTokens')!r} != "
                          f"{row.get('residentTokens')!r}")
                prefix = row.get("prefix") if isinstance(row.get("prefix"), dict) else {}
                for key in ("requestChars", "approxInputTokens"):
                    if key in claim and claim[key] != prefix.get(key):
                        _fail(violations, "perCall",
                              f"sample {k} {key} {claim[key]!r} != trace {prefix.get(key)!r}")

    # ---- perApiRequest: the per-request series (ADDITIVE, OPTIONAL) ----
    # The wire cannot carry one row per API call (a five-call task is one user turn), so
    # the request-size series lives here. It is not byte-derivable from the trace — the
    # checker verifies shape and order instead of claiming a byte identity it does not have.
    calls = manifest.get("perApiRequest")
    if calls is not None:
        if not isinstance(calls, list):
            _fail(violations, "perApiRequest", "must be a list of per-request samples")
        else:
            seen: dict = {}
            for k, sample in enumerate(calls):
                if not isinstance(sample, dict):
                    _fail(violations, "perApiRequest", f"sample {k} is not an object")
                    continue
                turn, call = sample.get("turn"), sample.get("call")
                if not (_int(turn) and _int(call) and isinstance(call, int) and call >= 1):
                    _fail(violations, "perApiRequest",
                          f"sample {k} needs an integer turn and a 1-based call index")
                    continue
                expected_call = seen.get(turn, 0) + 1
                if call != expected_call:
                    _fail(violations, "perApiRequest",
                          f"sample {k}: turn {turn} call {call}, expected {expected_call}")
                seen[turn] = call
                for key in ("requestChars", "approxInputTokens", "toolSchemas", "messageCount"):
                    if key in sample and not _int(sample[key]):
                        _fail(violations, "perApiRequest",
                              f"sample {k} {key} must be a non-negative integer")

    # ---- plugin: present and typed; a pairing fact, not a byte claim ----
    if plugin is not None:
        if not (isinstance(plugin.get("version"), str) and plugin["version"].strip()):
            _fail(violations, "plugin", "plugin.version must be a non-empty string")
        if not (isinstance(plugin.get("harness"), str) and plugin["harness"].strip()):
            _fail(violations, "plugin", "plugin.harness must be a non-empty string")
        for key in ("engine", "profile"):
            if key in plugin:
                value = plugin[key]
                if value is not None and not (isinstance(value, str) and value.strip()):
                    _fail(violations, "plugin", f"plugin.{key} must be a name or null")
        hv = plugin.get("harnessVersion")
        if hv is not None and not isinstance(hv, str):
            _fail(violations, "plugin", "plugin.harnessVersion must be a string or null")

        # Fail-closed per-call rule (P12 ruling, 2026-11-13): every call the policy had to drop on
        # must name what it removed, and the named tokens must account for the size change. A capture
        # with removals and no list is a violation, not a gap.
        def _v23(v):        # local: the older `_v` is defined further down the function
            try:
                return tuple(int(x) for x in str(v).split(".")[:3])
            except Exception:
                return (0,)
        calls = plugin.get("callSizes")
        budget = plugin.get("budgetTokens")
        if _v23(plugin.get("version")) >= (0, 13, 23) and isinstance(calls, list) and calls:
            for c in calls:
                if not isinstance(c, dict):
                    _fail(violations, "plugin", "callSizes entries must be objects")
                    continue
                before, after = c.get("before"), c.get("after")
                if not (isinstance(before, int) and isinstance(after, int)):
                    _fail(violations, "plugin", f"call {c.get('i')}: before/after must be integers")
                    continue
                removed = c.get("removed") or []
                if after < before and not removed:
                    _fail(violations, "plugin",
                          f"call {c.get('i')}: {before - after} tokens left the request but no "
                          f"removed pages are named")
                    continue
                if after < before and isinstance(budget, int) and before > budget:
                    named = sum(int(r.get("tokens") or 0) for r in removed if isinstance(r, dict))
                    actual = before - after
                    if actual and abs(named - actual) / actual > 0.10:
                        _fail(violations, "plugin",
                              f"call {c.get('i')}: removed pages name {named} tokens against an "
                              f"actual drop of {actual} (tolerance 10 %)")

        # A treatment that reports evictions must say WHICH pages left the request. A token count
        # alone cannot distinguish "the engine dropped the middle" from "something else changed the
        # prefix" — measured 2026-11-12, before the engine reported identities.
        def _v(v):
            try:
                return tuple(int(x) for x in str(v).split(".")[:3])
            except Exception:
                return (0,)
        if isinstance(plugin.get("evictedTokens"), int) and plugin["evictedTokens"] > 0 \
                and plugin.get("arm") != "control" and _v(plugin.get("version")) >= (0, 13, 2):
            n = plugin.get("evictedPagesCount")
            if not isinstance(n, int) or n <= 0:
                _fail(violations, "plugin",
                      "evictedTokens > 0 but no per-page detail: plugin.evictedPagesCount must be a "
                      "positive integer once the engine reports identities")

    if violations:
        for line in violations:
            print(f"coverage_check: violated {line}")
        return 1
    print(f"coverage_check: consistent ({os.path.basename(trace_path)}, "
          f"{len(rows)} events, digest ok)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

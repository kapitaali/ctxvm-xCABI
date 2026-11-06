#!/usr/bin/env python3
"""W8 redaction DQ — the pre-drop blocking gate (design/w8-capture-design.md §10).

The law: no trace rope byte leaves the owner's machine or enters a corpus
drop without this scan's ZERO-match verdict. Every `.jsonl`, `.meta.json` and
`.provenance` in the declared drop set is scanned for credential-key
patterns (`sk-` prefixes, `AKIA`, `ghp_`, `gho_`, `pat_`, `xox[bp]`,
`BEGIN ... PRIVATE KEY`, AWS-style key headers, generic `api_key=`,
`Authorization:` headers, long bearer-shaped tokens), `.env`-style secret
assignments, EMAILS, absolute `/home/` paths, IPv4 addresses (private ranges
included), and bare hostnames (mDNS/internal-TLD forms).

Exit 0 = zero matches (ship-unblocked). Exit 1 = CANNOT-SHIP: the drop burns
(those bytes are never retried; the owner rebuilds them by re-run).
Exit 2 = usage/scan-scope error (the scan refuses to make a claim about bytes
it was not asked to or cannot classify).

The tool NEVER prints matched bytes — positions and pattern names only, so
the DQ report itself cannot leak what it found. The scan's own identity
(SHA-256 of this file + scan list version + UTC date) prints on every verdict
so `provenance.json` can carry it verbatim (the m8 extension).

Usage:
  python3 tools/dq-secret-scan.py PATH [PATH ...]            # files or dirs
  python3 tools/dq-secret-scan.py --json PATH [PATH ...]     # machine verdict
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Pattern, Sequence, Tuple

SCAN_LIST_VERSION = "w8-dq-v1"
_DROP_SUFFIXES = (".jsonl", ".meta.json", ".provenance", ".provenance.json")

# Pattern set per design §10. Compiled once; flags: classic ignore-case where
# the credential surface is conventionally case-insensitive.
_PATTERNS: Tuple[Tuple[str, Pattern[str]], ...] = tuple(
    (name, re.compile(body, flags)) for name, body, flags in [
        ("openai.sk",         r"\bsk-[A-Za-z0-9_-]{20,}",                 0),
        ("aws.akia",          r"\bAKIA[0-9A-Z]{16}\b",                    0),
        ("github.ghp",        r"\bghp_[A-Za-z0-9]{20,}",                  0),
        ("github.gho",        r"\bgho_[A-Za-z0-9]{20,}",                  0),
        ("github.pat",        r"\bpat_[A-Za-z0-9_-]{20,}",                0),
        ("slack.xox",         r"\bxox[bp]-[A-Za-z0-9-]{10,}",             0),
        ("pem.private_key",   r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----",   0),
        ("aws.headers",       (r"AWSAccessKeyId|(?i:aws4[_-]?hmac)"
                               r"|x-amz-credential|(?i:aws_secret[_-]?"
                               r"access[_-]?key)"),                      0),
        ("generic.api_key",   (r"(?i)\bapi[_-]?key(\s*[=:]\s*|\b)\s*"
                               r"[A-Za-z0-9_\-.]{8,}"),                  0),
        ("http.authorization", r"(?i)\bauthorization\b\s*:\s*\S",         0),
        ("http.bearer",        (r"(?i)\bbearer\s+[A-Za-z0-9_\-\.]{24,}"), 0),
        # .env style: the line STARTS with the secret-shaped key (plain env
        # form `FOO_SECRET=...` and pretty-printed JSON form `"FOO_SECRET":`
        # both qualify; a key buried mid-line is the json variant below).
        ("env.secret_like",    (r"(?im)^[ \t]*(?:export[ \t]+)?[\"']?"
                               r"[A-Z][A-Z0-9_]*(?:_KEY|_SECRET|_TOKEN"
                               r"|PASSWORD|PASSWD|_PASSPHRASE)[\"']?"
                               r"\s*[:=]\s*"),                            0),
        ("json.secret_key",    (r"(?i)[\"'][A-Z][A-Z0-9_]*"
                               r"(?:_KEY|_SECRET|_TOKEN|PASSWORD|PASSWD"
                               r"|_PASSPHRASE)[\"']\s*:\s*[\"']\S"),      0),
        ("email",              (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+"
                               r"(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b"), 0),
        ("path.abs_home",      (r"\B/home/[A-Za-z0-9._\-/]*"),           0),
        ("ipv4.any",           (r"\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|"
                               r"[1-9]?[0-9])\.){3}"
                               r"(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|"
                               r"[1-9]?[0-9])\b"),                       0),
        ("hostname.internal",  (r"(?i)\b[a-z0-9][a-z0-9-]{0,62}"
                               r"(?:\.[a-z0-9-]{1,62}){0,4}"
                               r"\.(?:local|lan|internal|home|arpa)\b"), 0),
    ]
)


class ScanScopeError(Exception):
    """Exit 2: the scan was asked for bytes outside the drop-set shape."""


def _drop_files(arg: Path) -> Iterator[Path]:
    """The drop-set shape: .jsonl / .meta.json / .provenance(.json) files,
    recursed for directories; anything else refuses with scope error."""
    if arg.is_dir():
        for f in sorted(arg.rglob("*")):
            if f.is_file():
                yield from _drop_files(f)
    elif arg.is_file():
        if arg.name.endswith(_DROP_SUFFIXES):
            yield arg
        else:
            raise ScanScopeError(
                f"not a drop-set shape: {arg.name} (expected "
                "*.jsonl / *.meta.json / *.provenance)")
    else:
        raise ScanScopeError(f"path does not exist: {arg}")


def scan_text_for_line(text: str) -> List[Tuple[str, int]]:
    """One line against every pattern; returns [(pattern, line_no)] matches.
    Pure over (text, patterns) — the same bytes give the same verdict (the
    re-run-proof law §11)."""
    out: List[Tuple[str, int]] = []
    lines = text.splitlines()
    for line_no, line in enumerate(lines, start=1):
        for name, pattern in _PATTERNS:
            if pattern.search(line):
                out.append((name, line_no))
    return out


def scan_path(path: Path) -> List[Dict[str, Any]]:
    """Scan one file; returns per-file match records WITHOUT the matched
    bytes (the DQ report must not leak them)."""
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    hits = scan_text_for_line(text)
    return [{
        "file": str(path),
        "pattern": name,
        "line": line_no,
    } for name, line_no in hits]


def scan_all(args: Sequence[str]) -> Dict[str, Any]:
    files: List[Path] = []
    for a in args:
        files.extend(_drop_files(Path(a)))
    matches: List[Dict[str, Any]] = []
    for f in files:
        matches.extend(scan_path(f))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    verdict = "SHIP-UNBLOCKED" if not matches else "CANNOT-SHIP"
    return {
        "scanListVersion": SCAN_LIST_VERSION,
        "scanToolSha256": hashlib.sha256(
            Path(__file__).read_bytes()).hexdigest(),
        "scanDate": now,
        "filesScanned": len(files),
        "files": [str(f) for f in files],
        "patternsChecked": len(_PATTERNS),
        "matches": matches,
        "verdict": verdict,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="W8 redaction DQ scan (design §10): zero matches or CANNOT-SHIP.")
    parser.add_argument("paths", nargs="+", help="drop-set files or directories")
    parser.add_argument("--json", action="store_true",
                        help="machine verdict (stdout JSON) only")
    ns = parser.parse_args(argv)
    try:
        report = scan_all(ns.paths)
    except ScanScopeError as exc:
        print(f"SCAN-SCOPE-ERROR: {exc}", file=sys.stderr)
        return 2
    if ns.json:
        print(json.dumps(report, indent=1))
    else:
        print(f"dq-scan list {report['scanListVersion']}  "
              f"patterns={report['patternsChecked']}  "
              f"files={report['filesScanned']}")
        for m in report["matches"]:
            # the bytes stay dark: pattern + position only
            print(f"  match {m['pattern']}  {m['file']}:{m['line']}")
        print(f"verdict: {report['verdict']}")
        identity = {"scanListVersion": report["scanListVersion"],
                    "scanToolSha256": report["scanToolSha256"],
                    "scanDate": report["scanDate"],
                    "filesScanned": report["filesScanned"]}
        print("dq_scan=" + json.dumps(identity, sort_keys=True))
    return 0 if report["verdict"] == "SHIP-UNBLOCKED" else 1


if __name__ == "__main__":
    sys.exit(main())

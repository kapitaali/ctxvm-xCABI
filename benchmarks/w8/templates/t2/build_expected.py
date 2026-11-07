#!/usr/bin/env python3
"""T2 expected-artefact builder — the MECHANICAL RULE, executable.

Rule (also stated in task.md; frozen with the checker):

  drop          every directory corpus/m1..m8, in name order. The drop id is the
                directory name.
  files[]       every *.jsonl in that directory, in name order. sha256 is the full
                lowercase hex digest of the file's bytes. checksumStatus compares it to
                that directory's checksums.sha256 row for the SAME file name:
                  "verified"  the row exists and its digest equals the computed one
                  "mismatch"  the row exists and differs
                  "unlisted"  the file has no row in checksums.sha256
  eventsByType  counts of `type` over every line of every trace in the drop, keys sorted.
  totalEvents   the number of parsed lines across the drop.
  pages         the number of `page.declare` events in the drop.
  faultsBySource counts of `source` over every `page.fault` event, keys sorted.
  sessions      the number of distinct `sessionID` values across the drop's *.meta.json
                sidecars; null when the drop has no sidecar. It is NEVER derived from
                event rows: only a sidecar carries a session identity.
  sessionsSource for a count: the sidecar file names, sorted, joined by ", ";
                for null: "no .meta.json sidecar (checked: <names>)".

Usage: python3 build_expected.py <repo-root> <out.json>
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def drop_ids(root: Path):
    return sorted(p.name for p in (root / "corpus").glob("m*") if p.is_dir())


def checksums(path: Path) -> dict:
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2:
            out[parts[1].lstrip("*")] = parts[0].lower()
    return out


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    out = {"drops": []}
    for did in drop_ids(root):
        d = root / "corpus" / did
        sums = checksums(d / "checksums.sha256")
        files, ev, pages, faults = [], Counter(), 0, Counter()
        for trace in sorted(d.glob("*.jsonl")):
            raw = trace.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            want = sums.get(trace.name)
            status = "unlisted" if want is None else ("verified" if want == digest else "mismatch")
            files.append({"name": trace.name, "sha256": digest, "checksumStatus": status})
            for line in raw.decode("utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                ev[row.get("type", "")] += 1
                if row.get("type") == "page.declare":
                    pages += 1
                elif row.get("type") == "page.fault":
                    faults[row.get("source", "")] += 1
        metas = sorted(d.glob("*.meta.json"))
        sessions, source = None, ""
        if metas:
            ids = set()
            for m in metas:
                try:
                    sid = json.loads(m.read_text(encoding="utf-8")).get("sessionID")
                except (OSError, ValueError):
                    sid = None
                if sid:
                    ids.add(sid)
            sessions = len(ids)
            source = ", ".join(m.name for m in metas)
        else:
            checked = ", ".join(f.name for f in sorted(d.iterdir()) if f.is_file())
            source = f"no .meta.json sidecar (checked: {checked})"
        out["drops"].append({
            "drop": did,
            "files": files,
            "eventsByType": dict(sorted(ev.items())),
            "totalEvents": sum(ev.values()),
            "pages": pages,
            "faultsBySource": dict(sorted(faults.items())),
            "sessions": sessions,
            "sessionsSource": source,
        })
    Path(sys.argv[2]).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("drops=%d files=%d events=%d" % (len(out["drops"]),
          sum(len(d["files"]) for d in out["drops"]),
          sum(d["totalEvents"] for d in out["drops"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

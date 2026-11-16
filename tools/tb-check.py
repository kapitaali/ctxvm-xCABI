#!/usr/bin/env python3
"""tb-check.py — the T-B checker: recompute from the fixture, never from a stored expectation.

Three modes, all of them fail-closed on arguments:

  tb-check.py <fixture-dir> <artefact.json>          score the reconciliation artefact
  tb-check.py <fixture-dir> --per-reply <replies>    score each per-file reply (H4's measurement)
  tb-check.py <fixture-dir> --prove                  prove the checker can fail (six perturbations)
  tb-check.py --lookups <lookups.json> <reply-file>  score the three revisit lookups (P16/P17)

Why recompute: an expected artefact shipped beside the fixture, or a checker that compares a
reference copy against a reference copy, is a tautology. This reads the CSV bytes and derives the
answer with the same rule the task states.

What the gate is: **parsed equality** (the 2026-11-09 ruling). Canonical bytes are reported as an
observation and never fail a call — a cell must not be voided for indentation.

Replies file for --per-reply: JSONL, one object per line, {"file": "data-NN.csv", "reply": "..."}.
A reply is one `<category> <count> <sum> <min_id> <max_id>` line per category; other lines are
reported as `extra` and do not rescue a missing category.

Exit: 0 pass, 1 mismatch/red-before, 2 usage/IO/parse.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

CATEGORIES = ("alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta")
HEADER = "id,category,value"


# ---------------------------------------------------------------- recomputation

def read_fixture(fixture: Path) -> dict[str, list[tuple[int, str, int]]]:
    """Returns {basename: [(id, category, value), ...]} for every data-*.csv, sorted by name."""
    files = sorted(fixture.glob("data-*.csv"))
    if not files:
        raise SystemExit(f"tb-check: no data-*.csv under {fixture}")
    rows: dict[str, list[tuple[int, str, int]]] = {}
    for path in files:
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0].strip() != HEADER:
            raise SystemExit(f"tb-check: {path.name}: header is {lines[0]!r}, expected {HEADER!r}")
        parsed = []
        for n, line in enumerate(lines[1:], start=2):
            parts = line.split(",")
            if len(parts) != 3:
                raise SystemExit(f"tb-check: {path.name}:{n}: {line!r} is not id,category,value")
            row_id, category, value = int(parts[0]), parts[1], int(parts[2])
            if category not in CATEGORIES:
                raise SystemExit(f"tb-check: {path.name}:{n}: unknown category {category!r}")
            parsed.append((row_id, category, value))
        rows[path.name] = parsed
    return rows


def aggregates(rows: list[tuple[int, str, int]]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for row_id, category, value in rows:
        slot = out.setdefault(category, {"count": 0, "sum": 0, "min_id": row_id, "max_id": row_id})
        slot["count"] += 1
        slot["sum"] += value
        slot["min_id"] = min(slot["min_id"], row_id)
        slot["max_id"] = max(slot["max_id"], row_id)
    return out


def expected_artefact(rows: dict[str, list[tuple[int, str, int]]]) -> dict:
    categories: dict[str, dict[str, int]] = {}
    per_file: dict[str, dict[str, dict[str, int]]] = {}
    for name in sorted(rows):
        file_agg = aggregates(rows[name])
        per_file[name] = file_agg
        for category, slot in file_agg.items():
            total = categories.setdefault(category,
                                          {"count": 0, "sum": 0, "min_id": slot["min_id"],
                                           "max_id": slot["max_id"]})
            total["count"] += slot["count"]
            total["sum"] += slot["sum"]
            total["min_id"] = min(total["min_id"], slot["min_id"])
            total["max_id"] = max(total["max_id"], slot["max_id"])
    # top_category: largest sum, tie-break category name ascending
    top_category = sorted(categories, key=lambda c: (-categories[c]["sum"], c))[0]
    # top_file: most rows in top_category, tie-break basename ascending
    counts = {name: per_file[name].get(top_category, {}).get("count", 0) for name in per_file}
    top_file = sorted(counts, key=lambda name: (-counts[name], name))[0]
    grand_total = sum(slot["sum"] for slot in categories.values())
    return {
        "categories": {c: categories[c] for c in sorted(categories)},
        "top_category": top_category,
        "top_file": top_file,
        "grand_total": grand_total,
    }


def canonical_bytes(obj: dict) -> str:
    """The task's stated shape: categories sorted, 2-space indent, single trailing newline."""
    return json.dumps(obj, indent=2) + "\n"


# ---------------------------------------------------------------- scoring

def compare(actual: object, expected: dict) -> list[str]:
    """Parsed-equality gate. Returns the list of differences, empty means pass."""
    problems: list[str] = []
    if not isinstance(actual, dict):
        return [f"artefact is {type(actual).__name__}, expected an object"]
    got_cats = actual.get("categories")
    if not isinstance(got_cats, dict):
        return ["categories is missing or not an object"]
    if set(got_cats) != set(expected["categories"]):
        missing = sorted(set(expected["categories"]) - set(got_cats))
        extra = sorted(set(got_cats) - set(expected["categories"]))
        problems.append(f"category set differs: missing {missing}, extra {extra}")
    for category in sorted(set(got_cats) & set(expected["categories"])):
        want, got = expected["categories"][category], got_cats[category]
        if not isinstance(got, dict):
            problems.append(f"{category}: not an object")
            continue
        for key in ("count", "sum", "min_id", "max_id"):
            if got.get(key) != want[key]:
                problems.append(f"{category}.{key}: got {got.get(key)!r}, want {want[key]}")
    for key in ("top_category", "top_file", "grand_total"):
        if actual.get(key) != expected[key]:
            problems.append(f"{key}: got {actual.get(key)!r}, want {expected[key]!r}")
    return problems


def parse_reply(text: str) -> tuple[dict[str, tuple[int, int, int, int]], list[str]]:
    """One `<category> <count> <sum> <min_id> <max_id>` per category; other lines are `extra`."""
    tuples: dict[str, tuple[int, int, int, int]] = {}
    extra: list[str] = []
    for line in text.splitlines():
        stripped = line.strip().strip("|").strip()
        if not stripped:
            continue
        parts = stripped.replace("|", " ").split()
        if len(parts) == 5 and parts[0] in CATEGORIES:
            try:
                tuples[parts[0]] = (int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]))
                continue
            except ValueError:
                pass
        extra.append(stripped)
    return tuples, extra


def score_reply(reply: str, expected: dict[str, dict[str, int]]) -> tuple[bool, str]:
    tuples, extra = parse_reply(reply)
    want = {c: (v["count"], v["sum"], v["min_id"], v["max_id"]) for c, v in expected.items()}
    if tuples == want:
        return True, "ok" if not extra else f"ok ({len(extra)} extra line(s) ignored)"
    missing = sorted(set(want) - set(tuples))
    wrong = sorted(c for c in set(want) & set(tuples) if want[c] != tuples[c])
    surplus = sorted(set(tuples) - set(want))
    return False, (f"missing {missing}, wrong {wrong}, unexpected {surplus}, "
                   f"extra lines {len(extra)}")


# ---------------------------------------------------------------- modes

def mode_artefact(fixture: Path, artefact: Path) -> int:
    rows = read_fixture(fixture)
    expected = expected_artefact(rows)
    try:
        raw = artefact.read_text(encoding="utf-8")
        actual = json.loads(raw)
    except FileNotFoundError:
        print(f"tb-check: artefact not found: {artefact}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"tb-check: artefact is not JSON: {exc}", file=sys.stderr)
        return 2
    problems = compare(actual, expected)
    if problems:
        print(f"FAIL: fixture={fixture} artefact={artefact}")
        for problem in problems[:20]:
            print(f"  - {problem}")
        if len(problems) > 20:
            print(f"  … {len(problems) - 20} more")
        return 1
    # bytes are an observation, never the gate (2026-11-09 ruling)
    byte_note = "canonical" if raw == canonical_bytes(expected) else "differs from canonical form"
    print(f"PASS: fixture={fixture} artefact={artefact} (bytes: {byte_note})")
    return 0


def mode_per_reply(fixture: Path, replies_path: Path) -> int:
    rows = read_fixture(fixture)
    expected_by_file = {name: aggregates(rows[name]) for name in rows}
    try:
        lines = replies_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        print(f"tb-check: replies not found: {replies_path}", file=sys.stderr)
        return 2
    seen: dict[str, str] = {}
    for n, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            name, reply = obj["file"], obj["reply"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            print(f"tb-check: replies line {n}: {exc}", file=sys.stderr)
            return 2
        seen[name] = reply
    passed = 0
    for name in sorted(expected_by_file):
        if name not in seen:
            print(f"  {name}: MISSING (no reply recorded)")
            continue
        ok, detail = score_reply(seen[name], expected_by_file[name])
        passed += ok
        print(f"  {name}: {'PASS' if ok else 'FAIL'} — {detail}")
    total = len(expected_by_file)
    print(f"per-reply accuracy: {passed}/{total} = {passed / total:.1%}")
    return 0 if passed == total else 1


def parse_lookup_answers(text: str) -> list[tuple[str, int]]:
    """Pull `<category> <value>` answers out of a reply, in the order they appear.

    Two accepted shapes, because a model may answer either way: a bare/‑numbered token pair
    (`1) epsilon -327`, `epsilon -327`) or a prose clause (`the row ... is epsilon, -327`). The
    artefact JSON in the same reply cannot be mistaken for an answer: a JSON key is quoted
    (`"epsilon":`), and the numeric keys there (`"sum":`) never start with a category name.
    """
    found: list[tuple[str, int]] = []
    for line in text.splitlines():
        stripped = line.strip().strip("|").strip()
        if not stripped:
            continue
        tokens = re.sub(r"^[\s*(\[]*\d+[).:\]]\s*", "", stripped).split()
        if len(tokens) >= 2 and tokens[0].strip("*,:;") in CATEGORIES:
            tail = tokens[1].strip("*,:;")
            if re.fullmatch(r"-?\d+", tail):
                found.append((tokens[0].strip("*,:;"), int(tail)))
    if found:
        return found
    # prose fallback: `<category>` then a signed integer within a few characters
    for match in re.finditer(
            r"\b(" + "|".join(CATEGORIES) + r")\b[^\n\d-]{0,12}(-?\d+)", text):
        found.append((match.group(1), int(match.group(2))))
    return found


def mode_lookups(lookups_path: Path, reply_path: Path) -> int:
    """Score the reconciliation's three exact-row answers against the key written at prompt time.

    The rows are the only part of T-B that paging can actually damage (assistant prose is never
    dropped), so this is the accuracy surface H3 is judged on, with the refetch count beside it.
    """
    try:
        key = json.loads(lookups_path.read_text(encoding="utf-8"))
        reply = reply_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        print(f"tb-check: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"tb-check: lookups key is not JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(key, list) or not key:
        print("tb-check: lookups key is empty", file=sys.stderr)
        return 2
    answers = parse_lookup_answers(reply)
    passed = 0
    for i, item in enumerate(key):
        want = (item.get("category"), item.get("value"))
        got = answers[i] if i < len(answers) else None
        ok = got == want
        passed += ok
        print(f"  lookup {i + 1} ({item.get('file')} id {item.get('id')}): "
              f"{'PASS' if ok else 'FAIL'} — want {want}, got {got}")
    if len(answers) > len(key):
        print(f"  note: {len(answers) - len(key)} extra answer(s) parsed and ignored")
    print(f"lookup accuracy: {passed}/{len(key)} = {passed / len(key):.1%}")
    return 0 if passed == len(key) else 1


def mode_prove(fixture: Path) -> int:
    """Prove the checker can fail: one correct artefact, then six deliberate perturbations."""
    rows = read_fixture(fixture)
    expected = expected_artefact(rows)

    def run(obj: dict) -> int:
        with tempfile.TemporaryDirectory(prefix="tb-prove-") as tmp:
            path = Path(tmp) / "artefact.json"
            path.write_text(canonical_bytes(obj), encoding="utf-8")
            return mode_artefact(fixture, path)

    print("prove: a correct artefact must PASS")
    if run(json.loads(json.dumps(expected))) != 0:
        print("prove: FAILED — the checker rejects a correct artefact", file=sys.stderr)
        return 1
    print("prove: PASS\n")

    def mutate(label: str, fn) -> int:
        obj = json.loads(json.dumps(expected))
        fn(obj)
        print(f"prove: {label} must FAIL")
        rc = run(obj)
        print(f"prove: {'PASS (rejected)' if rc == 1 else 'FAILED — accepted a wrong artefact'}\n")
        return 0 if rc == 1 else 1

    def bump_count(obj):
        first = sorted(obj["categories"])[0]
        obj["categories"][first]["count"] += 1

    def bump_sum(obj):
        first = sorted(obj["categories"])[0]
        obj["categories"][first]["sum"] += 1

    def swap_top_category(obj):
        obj["top_category"] = "theta" if obj["top_category"] != "theta" else "alpha"

    def swap_keys(obj):
        cats = obj["categories"]
        a, b = sorted(cats)[0], sorted(cats)[1]
        cats[a], cats[b] = cats[b], cats[a]

    def shift_min_id(obj):
        first = sorted(obj["categories"])[0]
        obj["categories"][first]["min_id"] += 1

    def drop_key(obj):
        trims = sorted(obj["categories"])
        del obj["categories"][trims[-1]]

    failures = 0
    for label, fn in (("count +1", bump_count), ("sum +1", bump_sum),
                      ("top_category altered", swap_top_category),
                      ("two category keys swapped", swap_keys),
                      ("min_id off by one", shift_min_id),
                      ("a category removed", drop_key)):
        failures += mutate(label, fn)

    # the trailing-newline case is a BYTE observation, not a gate: state it, do not fail a cell on it
    with tempfile.TemporaryDirectory(prefix="tb-prove-") as tmp:
        path = Path(tmp) / "artefact.json"
        path.write_text(json.dumps(json.loads(json.dumps(expected)), indent=2), encoding="utf-8")
        rc = mode_artefact(fixture, path)
    print(f"prove: no trailing newline -> exit {rc} (0 expected: parsed equality is the gate; "
          f"the byte note reports the difference)")
    if rc != 0:
        failures += 1

    print(f"\nprove: {'ALL SEVEN BEHAVED' if failures == 0 else f'{failures} PROBE(S) WRONG'}")
    return 0 if failures == 0 else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="T-B checker (recompute, never a stored expectation)")
    ap.add_argument("fixture", help="directory holding data-*.csv")
    ap.add_argument("artefact", nargs="?", help="artefact.json to score")
    ap.add_argument("--per-reply", metavar="REPLIES", help="JSONL of {file, reply} rows")
    ap.add_argument("--lookups", metavar="LOOKUPS", help="score a reconciliation reply against lookups.json")
    ap.add_argument("--prove", action="store_true", help="prove the checker can fail (six perturbations)")
    args = ap.parse_args(argv)

    if args.lookups:
        # argv is `--lookups <key> <reply-file>`, so the reply arrives in the `fixture` positional.
        reply = args.artefact or args.fixture
        if not reply:
            print("tb-check: --lookups needs a reply file", file=sys.stderr)
            return 2
        return mode_lookups(Path(args.lookups).expanduser(), Path(reply).expanduser())

    fixture = Path(args.fixture).expanduser()
    if not fixture.is_dir():
        print(f"tb-check: fixture directory not found: {fixture}", file=sys.stderr)
        return 2
    if sum((args.prove, bool(args.per_reply), bool(args.artefact))) != 1:
        print("tb-check: give exactly one of <artefact>, --per-reply, --prove", file=sys.stderr)
        return 2
    if args.prove:
        return mode_prove(fixture)
    if args.per_reply:
        return mode_per_reply(fixture, Path(args.per_reply).expanduser())
    return mode_artefact(fixture, Path(args.artefact).expanduser())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

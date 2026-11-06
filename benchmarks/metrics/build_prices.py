#!/usr/bin/env python3
"""Build prices.json from the owner's provider-catalogue export.

The catalogue is a CSV the owner supplied on 2026-11-06 (six columns, no header):

    index, "Vendor: Model", modality, current price, list price, discount

Examples:
    #2,DeepSeek: DeepSeek V4.1 Flash 1017,Text,in $0.15/1M / out $0.60/1M,—,—
    ,Thenlper: GTE-Base,Embeddings,$0.01/1M input,—,—
    ,Z.ai: GLM 5.3 Flash,Text,in $0.12/1M / out $0.40/1M,in $0.15/1M / out $0.50/1M,20%

Law: this script never invents a number. "FREE" is 0.0 (an observed price), a dash is
null (unknown), and an unparseable cell aborts the build rather than guessing. The
catalogue carries NO cache-read price, so `usdPer1mCachedRead` stays null for every
catalogue entry — a W8 ledger that needs cache pricing must say which assumption it used.

The v1 `providers` block is preserved verbatim so existing consumers keep working; the
catalogue is additive and `priceModelVersion` moves to 2.

Usage:
    python3 benchmarks/metrics/build_prices.py            # rebuild prices.json
    python3 benchmarks/metrics/build_prices.py --check    # exit 1 if prices.json is stale
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOGUE = HERE / "catalogue-2026-11-06.csv"
MODEL_LIST = HERE / "model-list-2026-11-06.txt"
PRICES = HERE / "prices.json"
ACCESSED = "2026-11-06"

V2_NOTE = (
    "v2 (2026-11-06): the owner's catalogue export is added under `catalogue`; the v1 "
    "`providers` block is unchanged. The export carries no cache-read price, so "
    "`usdPer1mCachedRead` is null for every catalogue entry — unknown, never substituted. "
    "Prices are owner-supplied, not web-verified here."
)

FREE = "FREE"
DASH = "\u2014"
PRICE_RE = re.compile(r"^in \$([0-9.]+)/1M / out \$([0-9.]+)/1M$")
INPUT_ONLY_RE = re.compile(r"^\$([0-9.]+)/1M input$")
SINGLE_RE = re.compile(r"^\$([0-9.]+)/1M$")


def parse_price(cell: str, row: int) -> tuple[float | None, float | None, str]:
    """Return (input, output, basis) per 1M tokens; None where the cell says unknown.

    `basis` records the shape the export used, so a consumer can tell a two-sided
    price from a single figure that names no direction:
      "in-out"     -> both sides stated
      "input-only" -> "$X/1M input" (embeddings), no output price
      "single"     -> "$X/1M" with no direction stated: recorded as input, output null
      "free"       -> FREE, both sides 0.0
      "unknown"    -> a dash
    """
    cell = cell.strip()
    if cell == DASH or cell == "":
        return None, None, "unknown"
    if cell.upper() == FREE:
        return 0.0, 0.0, "free"
    m = PRICE_RE.match(cell)
    if m:
        return float(m.group(1)), float(m.group(2)), "in-out"
    m = INPUT_ONLY_RE.match(cell)
    if m:
        return float(m.group(1)), None, "input-only"
    m = SINGLE_RE.match(cell)
    if m:
        return float(m.group(1)), None, "single"
    raise SystemExit(f"build_prices: row {row}: unparseable price cell {cell!r}")


def parse_row(line: str, row: int) -> dict:
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 6:
        raise SystemExit(f"build_prices: row {row}: expected 6 columns, got {len(parts)}")
    _index, name, modality, current, listed, discount = parts
    vendor, sep, model = name.partition(": ")
    if not sep:
        # A listing without a vendor prefix is still data: record the absence rather
        # than invent a vendor or drop the row.
        vendor, model = None, name
    cur_in, cur_out, basis = parse_price(current, row)
    list_in, list_out, _ = parse_price(listed, row)
    return {
        "id": f"row-{row:03d}",
        "vendor": vendor,
        "model": model,
        "modality": modality,
        "usdPer1mInput": cur_in,
        "usdPer1mOutput": cur_out,
        "priceBasis": basis,
        "listUsdPer1mInput": list_in,
        "listUsdPer1mOutput": list_out,
        "discount": None if discount == DASH else discount,
        "usdPer1mCachedRead": None,  # not present in this export — unknown, never guessed
    }


LIST_RE = re.compile(
    r"^\s*\((?:●|○)\)\s+(?:★\s+)?(?P<model>\S+)\s+\$?(?P<inp>[0-9.]+|free)\s+"
    r"\$?(?P<out>[0-9.]+|free)\s*(?P<third>\$?[0-9.]+|-?[0-9.]+%|-)?\s*(?:<-.*)?$"
)


def _num(token: str) -> float | None:
    token = token.strip().lstrip("$")
    if token.lower() == "free":
        return 0.0
    try:
        return float(token)
    except ValueError:
        return None


def parse_model_list() -> list[dict]:
    """Parse the provider's `hermes model list` output the owner pasted.

    Columns are: marker, model id, input, output, and an optional third figure. For paid
    rows that figure is a price and it tracks the cached-input rate (10% of input on Luna
    and Haiku, 5% on Sonnet/Opus); for the free row it is a discount percentage. The third
    column is therefore recorded as `cachedReadCandidate` with its basis named, never
    silently promoted to a verified cache price — the list has no header.
    """
    rows: list[dict] = []
    for n, line in enumerate(MODEL_LIST.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        m = LIST_RE.match(line)
        if m is None:
            raise SystemExit(f"build_prices: model list row {n}: unparseable {line!r}")
        third = (m.group("third") or "").strip()
        cached = None
        basis = None
        if third.endswith("%"):
            basis = "discount-percent"
        elif third:
            cached = _num(third)
            basis = "model-list third column; read as cached-input rate"
        rows.append({
            "model": m.group("model"),
            "usdPer1mInput": _num(m.group("inp")),
            "usdPer1mOutput": _num(m.group("out")),
            "cachedReadCandidate": cached,
            "thirdColumnBasis": basis,
        })
    return rows


def _norm(vendor: str | None, model: str) -> str:
    return re.sub(r"[^a-z0-9]", "", f"{vendor or ''}{model}".lower())


def build() -> dict:
    rows = [ln for ln in CATALOGUE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    entries = [parse_row(ln, i) for i, ln in enumerate(rows, start=1)]

    # Duplicate "Vendor: Model" names are real (two listings at different prices).
    # Keep every row; mark the repeats so nothing is silently merged.
    seen: dict[tuple[str, str], str] = {}
    for e in entries:
        key = (e["vendor"], e["model"])
        if key in seen:
            e["duplicateOf"] = seen[key]
        else:
            seen[key] = e["id"]
            e["duplicateOf"] = None

    listed = parse_model_list()
    by_key = {_norm(None, r["model"]): r for r in listed}
    # Cross-check every catalogue row that the provider list also carries, and fill the
    # cache-read candidate where the catalogue had no such column.
    matched = 0
    for e in entries:
        key = _norm(e["vendor"], e["model"])
        hit = by_key.get(key)
        if hit is None:
            e["crossCheck"] = None
            continue
        matched += 1
        same = (e["usdPer1mInput"] == hit["usdPer1mInput"]
                and e["usdPer1mOutput"] == hit["usdPer1mOutput"])
        e["crossCheck"] = "matches model list" if same else (
            f"DIFFERS: model list {hit['usdPer1mInput']}/{hit['usdPer1mOutput']}")
        if e["usdPer1mCachedRead"] is None and hit["cachedReadCandidate"] is not None:
            e["usdPer1mCachedRead"] = hit["cachedReadCandidate"]
            e["cachedReadSource"] = hit["thirdColumnBasis"]

    raw = json.loads(PRICES.read_text(encoding="utf-8"))
    out = dict(raw)
    out["priceModelVersion"] = 2
    out["updated"] = ACCESSED
    # Idempotence: the note is rebuilt from its v1 base each run, never appended to itself.
    base_note = raw["note"].split(" v2 (2026-11-06):")[0]
    out["note"] = base_note + " " + V2_NOTE
    out["providerList"] = {
        "source": MODEL_LIST.name,
        "sourceKind": "owner-pasted `hermes model list` output",
        "accessed": ACCESSED,
        "verified": "owner-supplied; the list carries no column header",
        "rows": len(listed),
        "matchedCatalogueRows": matched,
        "entries": listed,
    }
    out["catalogue"] = {
        "source": CATALOGUE.name,
        "sourceKind": "owner-supplied provider catalogue export (CSV, six columns, no header)",
        "accessed": ACCESSED,
        "verified": "owner-supplied; not web-verified by this repository",
        "rows": len(entries),
        "entries": entries,
    }
    return out


def dumps(doc: dict) -> str:
    return json.dumps(doc, indent=1, sort_keys=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build prices.json from the catalogue CSV.")
    ap.add_argument("--check", action="store_true", help="exit 1 if prices.json is stale")
    args = ap.parse_args(argv)
    text = dumps(build())
    if args.check:
        if PRICES.read_text(encoding="utf-8") != text:
            print("build_prices: stale — rerun without --check", file=sys.stderr)
            return 1
        print("build_prices: OK — prices.json matches the catalogue")
        return 0
    PRICES.write_text(text, encoding="utf-8")
    doc = json.loads(text)
    print(f"build_prices: wrote {PRICES.name} — version {doc['priceModelVersion']}, "
          f"{doc['catalogue']['rows']} catalogue rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

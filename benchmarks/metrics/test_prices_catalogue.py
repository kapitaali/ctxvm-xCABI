"""The price catalogue: every row parsed, nothing invented.

The catalogue is the owner's export (2026-11-06). These tests pin the parse law: FREE is
an observed 0.0, a dash is unknown, a single figure with no direction is recorded as input
with output null, duplicate listings are preserved rather than merged, and no cache-read
price appears anywhere because the export does not carry one.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PRICES = HERE / "prices.json"
CATALOGUE = HERE / "catalogue-2026-11-06.csv"
BUILDER = HERE / "build_prices.py"


@pytest.fixture(scope="module")
def doc() -> dict:
    return json.loads(PRICES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def entries(doc: dict) -> list[dict]:
    return doc["catalogue"]["entries"]


def test_version_and_row_count(doc: dict) -> None:
    assert doc["priceModelVersion"] == 2
    csv_rows = [ln for ln in CATALOGUE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert doc["catalogue"]["rows"] == len(csv_rows) == len(doc["catalogue"]["entries"])


def test_v1_providers_block_survives(doc: dict) -> None:
    # Existing consumers read `providers`; the catalogue is additive.
    assert {"nvidia", "opencode", "openai"} <= set(doc["providers"])
    assert doc["providers"]["nvidia"]["usdPer1mInput"] == 0.0


def test_free_is_zero_and_dash_is_null(entries: list[dict]) -> None:
    free = [e for e in entries if e["priceBasis"] == "free"]
    assert free and all(e["usdPer1mInput"] == 0.0 and e["usdPer1mOutput"] == 0.0 for e in free)
    unknown = [e for e in entries if e["priceBasis"] == "unknown"]
    assert all(e["usdPer1mInput"] is None and e["usdPer1mOutput"] is None for e in unknown)


def test_single_figure_is_input_with_null_output(entries: list[dict]) -> None:
    single = [e for e in entries if e["priceBasis"] == "single"]
    assert single, "the export carries single-figure rows; they must not be dropped"
    assert all(e["usdPer1mInput"] is not None and e["usdPer1mOutput"] is None for e in single)


def test_embeddings_have_no_output_price(entries: list[dict]) -> None:
    emb = [e for e in entries if e["modality"] == "Embeddings"]
    assert emb
    assert all(e["usdPer1mOutput"] is None and e["priceBasis"] == "input-only" for e in emb)


def test_cache_read_is_never_invented(entries: list[dict]) -> None:
    # The export has no cache-read column; a price here would be fabricated.
    assert all(e["usdPer1mCachedRead"] is None for e in entries)


def test_duplicate_listings_are_preserved_and_marked(entries: list[dict]) -> None:
    names = [(e["vendor"], e["model"]) for e in entries]
    assert len(names) != len(set(names)), "the export contains repeats; the test data should show it"
    marked = [e for e in entries if e["duplicateOf"]]
    assert marked, "a repeat must carry duplicateOf instead of being merged"
    by_id = {e["id"]: e for e in entries}
    for e in marked:
        assert e["duplicateOf"] in by_id


def test_the_w8_candidate_row_is_present(entries: list[dict]) -> None:
    row = next(e for e in entries if e["model"] == "DeepSeek V4.1 Flash 1017")
    assert (row["vendor"], row["usdPer1mInput"], row["usdPer1mOutput"]) == ("DeepSeek", 0.15, 0.60)


def test_builder_check_is_clean() -> None:
    res = subprocess.run([sys.executable, str(BUILDER), "--check"], capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "matches the catalogue" in res.stdout

import json
from datetime import date

import pandas as pd

from equity_research.merge import (
    apply_performance,
    performance_from_ohlc,
    update_dataset_prices,
)
from equity_research.returns import UNAVAILABLE


def test_performance_from_fixture():
    df = pd.read_csv("tests/fixtures/ohlc_reliance.csv", parse_dates=["date"])

    perf = performance_from_ohlc(
        df, price_date=pd.Timestamp("2026-10-03"), listing_date=None
    )

    assert "1D" in perf
    assert perf["1D"] != UNAVAILABLE


def test_performance_from_empty_ohlc_is_unavailable():
    perf = performance_from_ohlc(
        pd.DataFrame(columns=["date", "close"]),
        price_date=pd.Timestamp("2026-10-03"),
        listing_date=None,
    )

    assert all(value == UNAVAILABLE for value in perf.values())


def test_performance_respects_listing_date():
    df = pd.read_csv("tests/fixtures/ohlc_reliance.csv", parse_dates=["date"])

    perf = performance_from_ohlc(
        df,
        price_date=pd.Timestamp("2026-10-03"),
        listing_date=date(2025, 6, 1),
    )

    assert perf["5Y_cagr"] == "N/A — listed 2025-06-01"


def test_apply_performance_sets_fields():
    entity = {"ticker": "RELIANCE.NS", "name": "Reliance Industries"}

    result = apply_performance(
        entity,
        {"1D": 0.5},
        price=150.0,
        price_date="2026-10-03",
        source="Yahoo Finance (NSE)",
    )

    assert result is entity
    assert entity["price"] == 150.0
    assert entity["price_date"] == "2026-10-03"
    assert entity["source"] == "Yahoo Finance (NSE)"
    assert entity["performance"]["1D"] == 0.5


def test_update_dataset_prices_updates_all_entity_groups(tmp_path):
    data_dir = tmp_path / "data"
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True)
    (data_dir / "sectors.json").write_text(
        json.dumps(
            {
                "sectors": [
                    {
                        "id": "energy",
                        "representative_index": "^CNXENERGY",
                        "performance": {},
                    }
                ]
            }
        )
    )
    (data_dir / "companies.json").write_text(
        json.dumps(
            {
                "benchmarks": [{"ticker": "^NSEI", "performance": {}}],
                "by_sector": {
                    "energy": [{"ticker": "RELIANCE.NS", "performance": {}}]
                },
            }
        )
    )
    (data_dir / "new_age.json").write_text(
        json.dumps({"companies": [{"ticker": "ETERNAL.NS", "performance": {}}]})
    )
    fixture = pd.read_csv("tests/fixtures/ohlc_reliance.csv")
    for symbol in ("^CNXENERGY", "^NSEI", "RELIANCE.NS"):
        fixture.to_csv(raw_dir / f"{symbol}.csv", index=False)

    summary = update_dataset_prices(data_dir, raw_dir, "2026-10-03")

    companies = json.loads((data_dir / "companies.json").read_text())
    new_age = json.loads((data_dir / "new_age.json").read_text())
    assert companies["by_sector"]["energy"][0]["price"] == 150.0
    assert companies["benchmarks"][0]["performance"]["1D"] != UNAVAILABLE
    assert new_age["companies"][0]["performance"]["1D"] == UNAVAILABLE
    assert summary == {"ok": 3, "fail": 1}

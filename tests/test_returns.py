from datetime import date
import pandas as pd
from equity_research.returns import compute_horizon_returns, UNAVAILABLE, na_listed


def _series():
    df = pd.read_csv("tests/fixtures/sample_prices.csv", parse_dates=["date"])
    return df["date"].list if False else list(df["date"]), list(df["close"])


def test_na_listed_format():
    assert na_listed(date(2024, 5, 1)) == "N/A — listed 2024-05-01"


def test_1d_and_1y_absolute_returns():
    dates, closes = [], []
    df = pd.read_csv("tests/fixtures/sample_prices.csv", parse_dates=["date"])
    dates, closes = list(df["date"]), list(df["close"])
    out = compute_horizon_returns(dates, closes, price_date=pd.Timestamp("2026-10-03"), listing_date=date(2020, 1, 1))
    assert round(out["1D"], 4) == round((150 / 149 - 1) * 100, 4)
    assert round(out["1Y"], 2) == round((150 / 140 - 1) * 100, 2)


def test_3y_cagr_not_absolute():
    df = pd.read_csv("tests/fixtures/sample_prices.csv", parse_dates=["date"])
    out = compute_horizon_returns(list(df["date"]), list(df["close"]), price_date=pd.Timestamp("2026-10-03"), listing_date=date(2020, 1, 1))
    # 2023-10-04 close 121 → 150 over ~3y
    assert isinstance(out["3Y_cagr"], float)
    assert out["3Y_cagr"] != round((150 / 121 - 1) * 100, 4)


def test_short_listing_returns_na_string():
    df = pd.read_csv("tests/fixtures/sample_prices.csv", parse_dates=["date"])
    out = compute_horizon_returns(list(df["date"]), list(df["close"]), price_date=pd.Timestamp("2026-10-03"), listing_date=date(2025, 6, 1))
    assert out["5Y_cagr"] == "N/A — listed 2025-06-01"


def test_empty_series_unavailable():
    out = compute_horizon_returns([], [], price_date=pd.Timestamp("2026-10-03"), listing_date=None)
    assert out["1D"] == UNAVAILABLE

from __future__ import annotations

from equity_research.quant import (
    attractiveness_score,
    breadth_pct,
    build_quant_signals,
    momentum_label,
    price_momentum_factor,
    relative_return,
)


def test_relative_return():
    assert relative_return(5.0, 2.0) == 3.0
    assert relative_return(None, 2.0) is None
    assert relative_return(1.0, None) is None


def test_momentum_label_rules():
    assert momentum_label(1.0, 2.0) == "outperforming"
    assert momentum_label(-1.0, -2.0) == "underperforming"
    assert momentum_label(1.0, -2.0) == "mixed"
    assert momentum_label(None, 1.0) == "unavailable"


def test_price_momentum_factor_map():
    assert price_momentum_factor(10.0, 10.0) == 9
    assert price_momentum_factor(1.0, 1.0) == 6
    assert price_momentum_factor(-5.0, -5.0) == 3
    assert price_momentum_factor(None, 1.0) is None


def test_attractiveness_score_matches_banks_formula():
    factors = {
        "demand": 8,
        "earnings_growth": 8,
        "earnings_revision": 5,
        "margins": 7,
        "balance_sheet": 8,
        "valuation": 7,
        "policy": 7,
        "competitive_structure": 7,
        "capital_cycle": 7,
        "price_momentum": 4,
        "macro_sensitivity": 7,
        "downside_risk": 7,
    }
    weights = {
        "demand": 12,
        "earnings_growth": 12,
        "earnings_revision": 7,
        "margins": 8,
        "balance_sheet": 10,
        "valuation": 10,
        "policy": 8,
        "competitive_structure": 7,
        "capital_cycle": 7,
        "price_momentum": 7,
        "macro_sensitivity": 6,
        "downside_risk": 6,
    }
    assert attractiveness_score(factors, weights) == 69.9


def test_breadth_pct():
    assert breadth_pct([1.0, -1.0, 2.0, None]) == 66.7
    assert breadth_pct([None, None]) is None


def test_build_quant_signals_patches_only_price_momentum():
    meta = {"price_date": "2026-10-16"}
    sectors = {
        "sectors": [
            {
                "id": "banks",
                "name": "Banks",
                "stance": "OW",
                "attractiveness_score": 69.9,
                "factor_scores": {
                    "demand": 8,
                    "earnings_growth": 8,
                    "earnings_revision": 5,
                    "margins": 7,
                    "balance_sheet": 8,
                    "valuation": 7,
                    "policy": 7,
                    "competitive_structure": 7,
                    "capital_cycle": 7,
                    "price_momentum": 4,
                    "macro_sensitivity": 7,
                    "downside_risk": 7,
                },
                "weights": {
                    "demand": 12,
                    "earnings_growth": 12,
                    "earnings_revision": 7,
                    "margins": 8,
                    "balance_sheet": 10,
                    "valuation": 10,
                    "policy": 8,
                    "competitive_structure": 7,
                    "capital_cycle": 7,
                    "price_momentum": 7,
                    "macro_sensitivity": 6,
                    "downside_risk": 6,
                },
                "performance": {
                    "1M": 5.0,
                    "3M": 5.0,
                    "YTD": 1.0,
                    "1Y": 2.0,
                },
            }
        ]
    }
    companies = {
        "benchmarks": [
            {
                "name": "Nifty 50",
                "ticker": "^NSEI",
                "performance": {"1M": 0.0, "3M": 0.0, "YTD": 0.0, "1Y": 0.0},
            },
            {
                "name": "Nifty 500",
                "ticker": "^CRSLDX",
                "performance": {"1M": 0.0, "3M": 0.0, "YTD": 0.0, "1Y": 0.0},
            },
        ],
        "by_sector": {
            "banks": [
                {
                    "ticker": "HDFCBANK.NS",
                    "name": "HDFC Bank",
                    "performance": {"1M": 2.0, "3M": 3.0, "YTD": 1.0, "1Y": 1.0},
                },
                {
                    "ticker": "ICICIBANK.NS",
                    "name": "ICICI Bank",
                    "performance": {"1M": -1.0, "3M": -1.0, "YTD": 0.0, "1Y": 0.0},
                },
            ]
        },
    }
    new_age = {"companies": []}
    quant, patched = build_quant_signals(
        meta=meta,
        sectors=sectors,
        companies=companies,
        new_age=new_age,
        patch_sectors=True,
    )
    bank = patched["sectors"][0]
    assert bank["stance"] == "OW"
    assert bank["factor_scores"]["demand"] == 8
    assert bank["factor_scores"]["price_momentum"] == 8  # avg rel +5 → 8
    assert bank["attractiveness_score"] == attractiveness_score(
        bank["factor_scores"], bank["weights"]
    )
    assert quant["companies"]["HDFCBANK.NS"]["momentum_label"] == "outperforming"
    assert quant["sectors"]["banks"]["breadth_1m"] == 50.0

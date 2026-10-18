from copy import deepcopy
from pathlib import Path

import pytest

from equity_research.schemas import load_all_data, validate_macro_deep

ROOT = Path(__file__).resolve().parents[1]

_MIN = {
    "as_of": "2026-10-18",
    "headline": "Test headline",
    "base_case": ["a"],
    "upside": ["b"],
    "downside": ["c"],
    "transmission_map": ["d"],
    "portfolio_implications": ["e"],
    "risk_watchlist": [
        {"id": "x", "title": "Risk", "severity": "high", "note": "note"}
    ],
    "open_questions": ["q"],
    "methodology_notes": ["m"],
    "sources": [
        {
            "title": "t",
            "url_or_publisher": "u",
            "as_of": "2026-10-18",
            "notes": "n",
        }
    ],
}


def test_validate_macro_deep_ok():
    validate_macro_deep(_MIN)


def test_validate_macro_deep_rejects_bad_severity():
    payload = deepcopy(_MIN)
    payload["risk_watchlist"][0]["severity"] = "critical"
    with pytest.raises(ValueError, match="severity"):
        validate_macro_deep(payload)


def test_load_all_data_includes_macro_deep():
    data = load_all_data(ROOT / "data")
    assert "macro_deep" in data
    assert data["macro_deep"]["headline"]
    assert data["macro_deep"]["risk_watchlist"]

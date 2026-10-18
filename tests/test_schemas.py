from pathlib import Path

import pytest

from equity_research.schemas import load_all_data, validate_meta, validate_new_age

ROOT = Path(__file__).resolve().parents[1]


def test_load_all_data_from_repo():
    data = load_all_data(ROOT / "data")
    assert set(data) >= {
        "meta",
        "macro",
        "market_regime",
        "sectors",
        "companies",
        "new_age",
        "sources",
        "deep_dives",
        "macro_deep",
    }


def test_meta_requires_dates():
    validate_meta(
        {
            "analysis_date": "2026-10-04",
            "data_cutoff_date": "2026-10-03",
            "price_date": "2026-10-03",
            "return_type": "price_return_split_bonus_adjusted_dividends_excluded",
        }
    )


def test_validate_new_age_skeleton_empty_companies_ok():
    validate_new_age({"status": "skeleton", "companies": []})


def test_validate_new_age_no_status_empty_companies_ok():
    validate_new_age({"companies": []})


def test_validate_new_age_final_wrong_length_fails():
    with pytest.raises(ValueError, match="exactly 25"):
        validate_new_age({"status": "final", "companies": [{}]})


def test_validate_new_age_final_twenty_five_companies_ok():
    validate_new_age({"status": "final", "companies": [{}] * 25})

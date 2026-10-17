import json
from pathlib import Path

import pytest

from equity_research.schemas import (
    validate_companies,
    validate_deep_dive_index,
    validate_deep_dive_pack,
)

ROOT = Path(__file__).resolve().parents[1]

_MIN_PACK = {
    "sector_id": "pharma",
    "name": "Pharmaceuticals and Healthcare",
    "as_of": "2026-10-18",
    "stance_summary": "OW — defensive growth with company-specific regulatory risk.",
    "overview": ["Domestic demand and exports support growth."],
    "sub_themes": [{"id": "domestic", "title": "Domestic brands", "summary": "Franchise strength."}],
    "drivers": ["Specialty mix"],
    "risks": ["US FDA / pricing"],
    "expectation_gaps": {"positive": ["Hospital structural growth"], "negative": ["US pricing pressure"]},
    "shortlist": [
        {
            "ticker": "SUNPHARMA.NS",
            "name": "Sun Pharmaceutical Industries",
            "priority": 1,
            "role_in_sector": "Diversified specialty leader",
            "thesis": ["Specialty and chronic franchise."],
            "why_now": ["Relative defensive growth."],
            "key_risks": ["Concentration and regulatory inspection risk."],
            "classification": "Sector Leader",
            "open_questions": ["Data unavailable from reliable sources."],
        }
    ],
    "methodology_notes": ["No sell-side target prices verified for this pack."],
    "sources": [
        {
            "title": "Stage 1 sector thesis (internal)",
            "url_or_publisher": "data/sectors.json",
            "as_of": "2026-10-04",
            "notes": "Baseline stance and thesis carried into Stage 2.",
        }
    ],
}


def test_validate_index_ok():
    validate_deep_dive_index(
        {
            "entries": [
                {
                    "sector_id": "pharma",
                    "name": "Pharmaceuticals and Healthcare",
                    "status": "published",
                    "as_of": "2026-10-18",
                },
                {
                    "sector_id": "banks",
                    "name": "Banks",
                    "status": "coming_next",
                    "as_of": None,
                },
            ]
        }
    )


def test_validate_pack_rejects_unknown_ticker():
    companies = {"by_sector": {"pharma": [{"ticker": "OTHER.NS", "name": "X", "classification": "Y", "performance": {}}]}}
    with pytest.raises(ValueError, match="SUNPHARMA"):
        validate_deep_dive_pack(_MIN_PACK, companies["by_sector"])


def test_validate_pack_ok_against_repo_universe():
    companies = json.loads((ROOT / "data" / "companies.json").read_text())
    validate_companies(companies)
    validate_deep_dive_pack(_MIN_PACK, companies["by_sector"])

from copy import deepcopy
import json
from pathlib import Path

import pytest

from equity_research.schemas import (
    load_all_data,
    validate_companies,
    validate_deep_dive_index,
    validate_deep_dive_pack,
    validate_shortlist_kpis,
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


_COMPANIES_BY_SECTOR = {
    "pharma": [
        {
            "ticker": "SUNPHARMA.NS",
            "name": "Sun Pharmaceutical Industries",
            "classification": "Sector Leader",
            "performance": {},
        }
    ]
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


@pytest.mark.parametrize("key", tuple(_MIN_PACK))
def test_validate_pack_rejects_missing_required_pack_key(key):
    pack = deepcopy(_MIN_PACK)
    del pack[key]

    with pytest.raises(ValueError, match="missing required keys"):
        validate_deep_dive_pack(pack, _COMPANIES_BY_SECTOR)


@pytest.mark.parametrize("key", tuple(_MIN_PACK["shortlist"][0]))
def test_validate_pack_rejects_missing_required_shortlist_key(key):
    pack = deepcopy(_MIN_PACK)
    del pack["shortlist"][0][key]

    with pytest.raises(ValueError, match="missing required keys"):
        validate_deep_dive_pack(pack, _COMPANIES_BY_SECTOR)


@pytest.mark.parametrize("key", ("positive", "negative"))
def test_validate_pack_rejects_missing_expectation_gap_key(key):
    pack = deepcopy(_MIN_PACK)
    del pack["expectation_gaps"][key]

    with pytest.raises(ValueError, match="missing required keys"):
        validate_deep_dive_pack(pack, _COMPANIES_BY_SECTOR)


@pytest.mark.parametrize(
    ("path", "invalid_value"),
    [
        (("overview",), "not-a-list"),
        (("drivers",), [1]),
        (("risks",), None),
        (("methodology_notes",), {}),
        (("expectation_gaps", "positive"), "not-a-list"),
        (("expectation_gaps", "negative"), [False]),
        (("shortlist", 0, "thesis"), "not-a-list"),
        (("shortlist", 0, "why_now"), [1]),
        (("shortlist", 0, "key_risks"), None),
        (("shortlist", 0, "open_questions"), {}),
    ],
)
def test_validate_pack_rejects_non_string_lists(path, invalid_value):
    pack = deepcopy(_MIN_PACK)
    target = pack
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = invalid_value

    with pytest.raises(ValueError, match="must be a list of strings"):
        validate_deep_dive_pack(pack, _COMPANIES_BY_SECTOR)


def test_validate_pack_ok_against_repo_universe():
    companies = json.loads((ROOT / "data" / "companies.json").read_text())
    validate_companies(companies)
    validate_deep_dive_pack(_MIN_PACK, companies["by_sector"])


def test_load_all_data_includes_pharma_pack():
    data = load_all_data(ROOT / "data")
    assert "deep_dives" in data
    assert data["deep_dives"]["packs"]["pharma"]["sector_id"] == "pharma"
    assert 4 <= len(data["deep_dives"]["packs"]["pharma"]["shortlist"]) <= 10


def test_load_all_data_includes_banks_pack():
    data = load_all_data(ROOT / "data")
    banks_pack = data["deep_dives"]["packs"]["banks"]
    assert banks_pack["sector_id"] == "banks"
    assert len(banks_pack["shortlist"]) == 10
    assert any(item.get("kpis") for item in banks_pack["shortlist"])
    entry = next(e for e in data["deep_dives"]["index"] if e["sector_id"] == "banks")
    assert entry["status"] == "published"
    assert entry["as_of"]
    assert len(data["companies"]["by_sector"]["banks"]) == 18


_BASE_KPI_ITEM = {
    "ticker": "HDFCBANK.NS",
    "name": "HDFC Bank",
    "priority": 1,
    "role_in_sector": "Large private franchise",
    "thesis": ["x"],
    "why_now": ["y"],
    "key_risks": ["z"],
    "classification": "Sector Leader",
    "open_questions": ["Data unavailable from reliable sources."],
}


def test_kpis_qualitative_only_ok():
    item = dict(_BASE_KPI_ITEM)
    item["kpis"] = [
        {
            "id": "nim",
            "label": "NIM",
            "qualitative": "adequate",
            "value": None,
            "note": "Data unavailable from reliable sources.",
        }
    ]
    validate_shortlist_kpis(item, "shortlist[0]")


def test_kpis_numeric_requires_as_of_and_source():
    item = dict(_BASE_KPI_ITEM)
    item["kpis"] = [
        {
            "id": "nim",
            "label": "NIM",
            "qualitative": "strong",
            "value": 3.5,
            "unit": "pct",
        }
    ]
    with pytest.raises(ValueError, match="as_of"):
        validate_shortlist_kpis(item, "shortlist[0]")


def test_kpis_invalid_qualitative_fails():
    item = dict(_BASE_KPI_ITEM)
    item["kpis"] = [{"id": "nim", "label": "NIM", "qualitative": "great"}]
    with pytest.raises(ValueError, match="qualitative"):
        validate_shortlist_kpis(item, "shortlist[0]")


def test_kpis_duplicate_id_fails():
    item = dict(_BASE_KPI_ITEM)
    item["kpis"] = [
        {"id": "nim", "label": "NIM", "qualitative": "adequate"},
        {"id": "nim", "label": "NIM", "qualitative": "strong"},
    ]
    with pytest.raises(ValueError, match="duplicate"):
        validate_shortlist_kpis(item, "shortlist[0]")

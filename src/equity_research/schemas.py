from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "meta",
    "macro",
    "market_regime",
    "sectors",
    "companies",
    "new_age",
    "sources",
]

_META_KEYS = ("analysis_date", "data_cutoff_date", "price_date", "return_type")
_SECTOR_ITEM_KEYS = (
    "id",
    "name",
    "stance",
    "attractiveness_score",
    "factor_scores",
    "representative_index",
    "performance",
    "thesis",
    "expectation_gaps",
)
_COMPANY_KEYS = ("ticker", "name", "classification", "performance")
_MACRO_VAR_KEYS = (
    "name",
    "current",
    "direction",
    "outlook_6_12m",
    "earnings_impact",
    "sector_market_impact",
    "source",
    "as_of",
)
_REGIME_KEYS = ("label", "evidence", "earnings", "valuation", "flows")
_SOURCE_ITEM_KEYS = ("title", "url_or_publisher", "as_of", "notes")


def _require_keys(obj: dict[str, Any], keys: tuple[str, ...], label: str) -> None:
    if not isinstance(obj, dict):
        raise ValueError(f"{label} must be a JSON object")
    missing = [k for k in keys if k not in obj]
    if missing:
        raise ValueError(f"{label} missing required keys: {', '.join(missing)}")


def validate_meta(meta: dict[str, Any]) -> None:
    _require_keys(meta, _META_KEYS, "meta")


def validate_macro(data: dict[str, Any]) -> None:
    _require_keys(data, ("variables",), "macro")
    if not isinstance(data["variables"], list):
        raise ValueError("macro.variables must be a list")
    for i, row in enumerate(data["variables"]):
        _require_keys(row, _MACRO_VAR_KEYS, f"macro.variables[{i}]")


def validate_market_regime(data: dict[str, Any]) -> None:
    _require_keys(data, _REGIME_KEYS, "market_regime")


def validate_sectors(data: dict[str, Any]) -> None:
    _require_keys(data, ("sectors",), "sectors")
    if not isinstance(data["sectors"], list):
        raise ValueError("sectors.sectors must be a list")
    for i, sector in enumerate(data["sectors"]):
        _require_keys(sector, _SECTOR_ITEM_KEYS, f"sectors.sectors[{i}]")


def validate_companies(data: dict[str, Any]) -> None:
    _require_keys(data, ("benchmarks", "by_sector"), "companies")
    if not isinstance(data["benchmarks"], list):
        raise ValueError("companies.benchmarks must be a list")
    if not isinstance(data["by_sector"], dict):
        raise ValueError("companies.by_sector must be an object")
    for sector_id, rows in data["by_sector"].items():
        if not isinstance(rows, list):
            raise ValueError(f"companies.by_sector[{sector_id!r}] must be a list")
        for j, company in enumerate(rows):
            _require_keys(
                company,
                _COMPANY_KEYS,
                f"companies.by_sector[{sector_id}][{j}]",
            )


def validate_new_age(data: dict[str, Any]) -> None:
    _require_keys(data, ("companies",), "new_age")
    if not isinstance(data["companies"], list):
        raise ValueError("new_age.companies must be a list")
    status = data.get("status")
    if status == "final" and len(data["companies"]) != 25:
        raise ValueError("new_age.companies must contain exactly 25 entries")


def validate_sources(data: dict[str, Any]) -> None:
    _require_keys(data, ("items",), "sources")
    if not isinstance(data["items"], list):
        raise ValueError("sources.items must be a list")
    for i, item in enumerate(data["items"]):
        _require_keys(item, _SOURCE_ITEM_KEYS, f"sources.items[{i}]")


_DEEP_DIVE_INDEX_ENTRY_KEYS = ("sector_id", "name", "status", "as_of")
_DEEP_DIVE_PACK_KEYS = (
    "sector_id",
    "name",
    "as_of",
    "stance_summary",
    "overview",
    "sub_themes",
    "drivers",
    "risks",
    "expectation_gaps",
    "shortlist",
    "methodology_notes",
    "sources",
)
_DEEP_DIVE_SHORTLIST_KEYS = (
    "ticker",
    "name",
    "priority",
    "role_in_sector",
    "thesis",
    "why_now",
    "key_risks",
    "classification",
    "open_questions",
)
_DEEP_DIVE_SUBTHEME_KEYS = ("id", "title", "summary")
_PUBLISHED = "published"
_COMING_NEXT = "coming_next"


def validate_deep_dive_index(data: dict[str, Any]) -> None:
    _require_keys(data, ("entries",), "deep_dives.index")
    if not isinstance(data["entries"], list) or not data["entries"]:
        raise ValueError("deep_dives.index.entries must be a non-empty list")
    for i, entry in enumerate(data["entries"]):
        _require_keys(entry, _DEEP_DIVE_INDEX_ENTRY_KEYS, f"deep_dives.index.entries[{i}]")
        if entry["status"] not in (_PUBLISHED, _COMING_NEXT):
            raise ValueError(
                f"deep_dives.index.entries[{i}].status must be '{_PUBLISHED}' or '{_COMING_NEXT}'"
            )


def validate_deep_dive_pack(pack: dict[str, Any], companies_by_sector: dict[str, Any]) -> None:
    _require_keys(pack, _DEEP_DIVE_PACK_KEYS, "deep_dive.pack")
    sector_id = pack["sector_id"]
    universe = companies_by_sector.get(sector_id)
    if not isinstance(universe, list):
        raise ValueError(f"no companies.by_sector[{sector_id!r}] for deep-dive pack")
    tickers = {row.get("ticker") for row in universe}
    shortlist = pack["shortlist"]
    if not isinstance(shortlist, list) or not (1 <= len(shortlist) <= 6):
        raise ValueError("deep_dive.pack.shortlist must contain 1–6 names")
    for j, item in enumerate(shortlist):
        _require_keys(item, _DEEP_DIVE_SHORTLIST_KEYS, f"deep_dive.pack.shortlist[{j}]")
        if item["ticker"] not in tickers:
            raise ValueError(
                f"deep_dive.pack.shortlist[{j}] ticker {item['ticker']} "
                f"not in companies.by_sector[{sector_id}]"
            )
    gaps = pack["expectation_gaps"]
    _require_keys(gaps, ("positive", "negative"), "deep_dive.pack.expectation_gaps")
    sub_themes = pack["sub_themes"]
    if not isinstance(sub_themes, list):
        raise ValueError("deep_dive.pack.sub_themes must be a list")
    for i, theme in enumerate(sub_themes):
        _require_keys(theme, _DEEP_DIVE_SUBTHEME_KEYS, f"deep_dive.pack.sub_themes[{i}]")
    sources = pack["sources"]
    if not isinstance(sources, list):
        raise ValueError("deep_dive.pack.sources must be a list")
    for i, src in enumerate(sources):
        _require_keys(src, _SOURCE_ITEM_KEYS, f"deep_dive.pack.sources[{i}]")


_VALIDATORS = {
    "meta": validate_meta,
    "macro": validate_macro,
    "market_regime": validate_market_regime,
    "sectors": validate_sectors,
    "companies": validate_companies,
    "new_age": validate_new_age,
    "sources": validate_sources,
}


def load_deep_dives(data_dir: Path, companies: dict[str, Any]) -> dict[str, Any]:
    index_path = data_dir / "deep_dives" / "index.json"
    if not index_path.is_file():
        raise ValueError("missing required data file: deep_dives/index.json")
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    validate_deep_dive_index(index_payload)
    packs: dict[str, Any] = {}
    by_sector = companies["by_sector"]
    for entry in index_payload["entries"]:
        if entry["status"] != _PUBLISHED:
            continue
        sector_id = entry["sector_id"]
        pack_path = data_dir / "deep_dives" / f"{sector_id}.json"
        if not pack_path.is_file():
            raise ValueError(f"missing published deep-dive pack: {pack_path.name}")
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        if pack.get("sector_id") != sector_id:
            raise ValueError(f"pack sector_id mismatch for {pack_path.name}")
        validate_deep_dive_pack(pack, by_sector)
        if not (4 <= len(pack["shortlist"]) <= 6):
            raise ValueError(
                f"published pack {sector_id} shortlist must contain 4–6 names"
            )
        packs[sector_id] = pack
    return {"index": index_payload["entries"], "packs": packs}


def load_all_data(data_dir: Path) -> dict[str, Any]:
    if not data_dir.is_dir():
        raise ValueError(f"data directory not found: {data_dir}")

    loaded: dict[str, Any] = {}
    for name in REQUIRED_FILES:
        path = data_dir / f"{name}.json"
        if not path.is_file():
            raise ValueError(f"missing required data file: {path.name}")
        with path.open(encoding="utf-8") as f:
            payload = json.load(f)
        _VALIDATORS[name](payload)
        loaded[name] = payload

    missing = [k for k in REQUIRED_FILES if k not in loaded]
    if missing:
        raise ValueError(f"loaded data missing required keys: {', '.join(missing)}")

    loaded["deep_dives"] = load_deep_dives(data_dir, loaded["companies"])
    return loaded

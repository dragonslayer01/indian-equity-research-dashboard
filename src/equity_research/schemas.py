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


_VALIDATORS = {
    "meta": validate_meta,
    "macro": validate_macro,
    "market_regime": validate_market_regime,
    "sectors": validate_sectors,
    "companies": validate_companies,
    "new_age": validate_new_age,
    "sources": validate_sources,
}


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

    return loaded

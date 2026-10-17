from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from .returns import compute_horizon_returns


def performance_from_ohlc(
    df: pd.DataFrame,
    price_date: pd.Timestamp,
    listing_date: date | None,
) -> dict[str, float | str]:
    if df.empty or not {"date", "close"}.issubset(df.columns):
        return compute_horizon_returns([], [], price_date, listing_date)
    clean = df.loc[:, ["date", "close"]].copy()
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce")
    clean["close"] = pd.to_numeric(clean["close"], errors="coerce")
    clean = clean.dropna().sort_values("date")
    return compute_horizon_returns(
        clean["date"].tolist(),
        clean["close"].tolist(),
        price_date,
        listing_date,
    )


def apply_performance(
    entity: dict,
    performance: dict,
    price: float | None,
    price_date: str,
    source: str,
) -> dict:
    entity["performance"] = performance
    entity["price"] = price
    entity["price_date"] = price_date
    entity["source"] = source
    return entity


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _symbol(entity: dict, key: str) -> str | None:
    value = entity.get(key)
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("ticker") or value.get("symbol")
    return None


def _listing_date(entity: dict) -> date | None:
    value = entity.get("listing_date")
    if not value:
        return None
    try:
        return pd.Timestamp(value).date()
    except (TypeError, ValueError):
        return None


def _merge_entity(entity: dict, symbol: str | None, raw_dir: Path, price_date: str) -> bool:
    source = "Yahoo Finance (index)" if symbol and symbol.startswith("^") else "Yahoo Finance (NSE)"
    frame = pd.DataFrame(columns=["date", "close"])
    if symbol:
        path = raw_dir / f"{symbol}.csv"
        if path.is_file():
            try:
                frame = pd.read_csv(path)
            except (OSError, pd.errors.ParserError):
                frame = pd.DataFrame(columns=["date", "close"])

    performance = performance_from_ohlc(
        frame,
        price_date=pd.Timestamp(price_date),
        listing_date=_listing_date(entity),
    )
    eligible = pd.DataFrame()
    if not frame.empty and {"date", "close"}.issubset(frame.columns):
        eligible = frame.copy()
        eligible["date"] = pd.to_datetime(eligible["date"], errors="coerce")
        eligible["close"] = pd.to_numeric(eligible["close"], errors="coerce")
        eligible = eligible.dropna()
        eligible = eligible.loc[eligible["date"] <= pd.Timestamp(price_date)]
    price = None if eligible.empty else float(eligible.sort_values("date").iloc[-1]["close"])
    apply_performance(entity, performance, price, price_date, source)
    return price is not None


def update_dataset_prices(
    data_dir: str | Path,
    raw_dir: str | Path,
    price_date: str,
) -> dict[str, int]:
    data_path = Path(data_dir)
    raw_path = Path(raw_dir)
    sectors = _load_json(data_path / "sectors.json")
    companies = _load_json(data_path / "companies.json")
    new_age = _load_json(data_path / "new_age.json")
    ok = fail = 0

    groups: list[tuple[list[dict], str]] = [
        (sectors.get("sectors", []), "representative_index"),
        (companies.get("benchmarks", []), "ticker"),
        (new_age.get("companies", []), "ticker"),
    ]
    groups.extend(
        (rows, "ticker") for rows in companies.get("by_sector", {}).values()
    )

    for entities, symbol_key in groups:
        for entity in entities:
            success = _merge_entity(
                entity, _symbol(entity, symbol_key), raw_path, price_date
            )
            ok += int(success)
            fail += int(not success)

    _write_json(data_path / "sectors.json", sectors)
    _write_json(data_path / "companies.json", companies)
    _write_json(data_path / "new_age.json", new_age)
    return {"ok": ok, "fail": fail}

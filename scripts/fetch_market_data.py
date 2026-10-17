#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from equity_research.fetch import fetch_ohlc
from equity_research.merge import update_dataset_prices


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _symbols(data_dir: Path) -> list[str]:
    sectors = _read(data_dir / "sectors.json")
    companies = _read(data_dir / "companies.json")
    new_age = _read(data_dir / "new_age.json")
    symbols = {
        sector["representative_index"]
        for sector in sectors["sectors"]
        if isinstance(sector.get("representative_index"), str)
    }
    symbols.update(
        row["ticker"] for row in companies["benchmarks"] if row.get("ticker")
    )
    for rows in companies["by_sector"].values():
        symbols.update(row["ticker"] for row in rows if row.get("ticker"))
    symbols.update(
        row["ticker"] for row in new_age["companies"] if row.get("ticker")
    )
    return sorted(symbols)


def _record_source(data_dir: Path, price_date: str, failures: list[str]) -> None:
    path = data_dir / "sources.json"
    sources = _read(path)
    item = {
        "title": "Yahoo Finance market prices",
        "url_or_publisher": "https://finance.yahoo.com/",
        "as_of": price_date,
        "notes": (
            "Close-price history fetched by yfinance. "
            + (
                f"Unavailable symbols: {', '.join(failures)}."
                if failures
                else "All requested symbols returned data."
            )
        ),
    }
    sources["items"] = [
        existing
        for existing in sources.get("items", [])
        if existing.get("title") != item["title"]
    ]
    sources["items"].append(item)
    _write(path, sources)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and merge market prices.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--price-date", help="Shared price date (YYYY-MM-DD)")
    args = parser.parse_args()

    meta_path = args.data_dir / "meta.json"
    meta = _read(meta_path)
    price_date = args.price_date or meta.get("price_date") or (
        date.today() - timedelta(days=1)
    ).isoformat()
    end = (pd.Timestamp(price_date) + pd.Timedelta(days=1)).date().isoformat()
    start = (pd.Timestamp(price_date) - pd.DateOffset(years=5) - pd.Timedelta(days=14))
    args.raw_dir.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    symbols = _symbols(args.data_dir)
    for symbol in symbols:
        frame = fetch_ohlc(symbol, start.date().isoformat(), end)
        frame.to_csv(args.raw_dir / f"{symbol}.csv", index=False)
        if frame.empty:
            failures.append(symbol)

    update_dataset_prices(args.data_dir, args.raw_dir, price_date)
    meta["price_date"] = price_date
    meta["data_cutoff_date"] = price_date
    _write(meta_path, meta)
    _record_source(args.data_dir, price_date, failures)
    print(f"ok={len(symbols) - len(failures)} fail={len(failures)}")
    if failures:
        print("failed_symbols=" + ",".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

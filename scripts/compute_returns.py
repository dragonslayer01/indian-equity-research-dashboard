#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from equity_research.merge import update_dataset_prices


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge cached prices into JSON.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--price-date", help="Shared price date (YYYY-MM-DD)")
    args = parser.parse_args()

    meta_path = args.data_dir / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    price_date = args.price_date or meta["price_date"]
    summary = update_dataset_prices(args.data_dir, args.raw_dir, price_date)
    meta["price_date"] = price_date
    meta["data_cutoff_date"] = price_date
    meta_path.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"ok={summary['ok']} fail={summary['fail']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

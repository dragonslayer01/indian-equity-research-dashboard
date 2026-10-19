#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from equity_research.quant import build_quant_signals


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute price-derived quant overlays and patch sector momentum."
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--no-patch-sectors",
        action="store_true",
        help="Write quant_signals.json only; leave sectors.json unchanged.",
    )
    args = parser.parse_args()
    data_dir = args.data_dir

    meta = _read(data_dir / "meta.json")
    sectors = _read(data_dir / "sectors.json")
    companies = _read(data_dir / "companies.json")
    new_age = _read(data_dir / "new_age.json")

    quant, sectors_out = build_quant_signals(
        meta=meta,
        sectors=sectors,
        companies=companies,
        new_age=new_age,
        patch_sectors=not args.no_patch_sectors,
    )
    _write(data_dir / "quant_signals.json", quant)
    if not args.no_patch_sectors:
        _write(data_dir / "sectors.json", sectors_out)

    n_co = len(quant["companies"])
    n_na = len(quant["new_age"])
    n_sec = len(quant["sectors"])
    print(f"as_of={quant['as_of']} sectors={n_sec} companies={n_co} new_age={n_na}")
    for sector_id, row in quant["sectors"].items():
        print(
            f"  {sector_id}: momentum={row['momentum_label']} "
            f"pm={row['price_momentum_factor']} "
            f"score {row['attractiveness_score_before']}→{row['attractiveness_score_after']} "
            f"breadth_1m={row['breadth_1m']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

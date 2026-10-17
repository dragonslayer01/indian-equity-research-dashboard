#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from equity_research.build import build_dashboard


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build offline Indian equity research dashboard HTML.",
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--src-dir", type=Path, default=Path("src/dashboard"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("dist/index.html"),
        help="Primary output path (default: dist/index.html for Netlify / local open).",
    )
    args = parser.parse_args()
    out = build_dashboard(args.data_dir, args.src_dir, args.out)
    print(f"Wrote {out}")
    # Keep legacy filename for local sharing / older docs.
    if out.name != "indian_equity_strategy_dashboard.html":
        legacy = out.parent / "indian_equity_strategy_dashboard.html"
        legacy.write_text(out.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Wrote {legacy}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

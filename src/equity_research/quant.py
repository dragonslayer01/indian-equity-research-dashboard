"""Price-derived quantitative overlays (no authored judgment rewrite)."""

from __future__ import annotations

from typing import Any

REL_HORIZONS = ("1M", "3M", "YTD", "1Y")
MOMENTUM_LABELS = frozenset(
    {"outperforming", "underperforming", "mixed", "unavailable"}
)

METHODOLOGY_NOTES = [
    "Relative return = entity absolute return minus benchmark return for the same horizon.",
    "Momentum labels are rule-based from 1M and 3M relative returns vs Nifty 50.",
    "Sector price_momentum factor is mapped from sector-index relative returns; other factors remain authored.",
    "Stance (OW/Neutral/UW) is not changed by this job.",
]


def relative_return(entity: float | None, benchmark: float | None) -> float | None:
    if entity is None or benchmark is None:
        return None
    if not isinstance(entity, (int, float)) or isinstance(entity, bool):
        return None
    if not isinstance(benchmark, (int, float)) or isinstance(benchmark, bool):
        return None
    return round(float(entity) - float(benchmark), 4)


def relative_block(
    performance: dict[str, Any] | None,
    benchmark_performance: dict[str, Any] | None,
    horizons: tuple[str, ...] = REL_HORIZONS,
) -> dict[str, float | None]:
    perf = performance or {}
    bench = benchmark_performance or {}
    return {
        horizon: relative_return(
            perf.get(horizon) if isinstance(perf.get(horizon), (int, float)) else None,
            bench.get(horizon) if isinstance(bench.get(horizon), (int, float)) else None,
        )
        for horizon in horizons
    }


def momentum_label(rel_1m: float | None, rel_3m: float | None) -> str:
    if rel_1m is None or rel_3m is None:
        return "unavailable"
    if rel_1m > 0 and rel_3m > 0:
        return "outperforming"
    if rel_1m < 0 and rel_3m < 0:
        return "underperforming"
    return "mixed"


def price_momentum_factor(rel_1m: float | None, rel_3m: float | None) -> int | None:
    """Map average of 1M/3M relative returns vs Nifty 50 into a 1–10 factor."""
    if rel_1m is None or rel_3m is None:
        return None
    avg = (rel_1m + rel_3m) / 2.0
    if avg >= 8:
        return 9
    if avg >= 4:
        return 8
    if avg >= 2:
        return 7
    if avg >= 0:
        return 6
    if avg >= -2:
        return 5
    if avg >= -4:
        return 4
    if avg >= -8:
        return 3
    return 2


def attractiveness_score(
    factor_scores: dict[str, Any], weights: dict[str, Any]
) -> float:
    total = 0.0
    for key, weight in weights.items():
        score = factor_scores.get(key)
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise ValueError(f"missing numeric factor_scores[{key!r}]")
        if not isinstance(weight, (int, float)) or isinstance(weight, bool):
            raise ValueError(f"missing numeric weights[{key!r}]")
        total += float(score) * float(weight)
    return round(total / 10.0, 1)


def breadth_pct(rel_values: list[float | None], horizon: str = "1M") -> float | None:
    del horizon  # callers pass list already sliced to a horizon
    usable = [v for v in rel_values if isinstance(v, (int, float))]
    if not usable:
        return None
    winners = sum(1 for v in usable if v > 0)
    return round(100.0 * winners / len(usable), 1)


def _benchmark_by_name(companies: dict[str, Any], name: str) -> dict[str, Any] | None:
    for row in companies.get("benchmarks") or []:
        if row.get("name") == name:
            return row
    return None


def build_quant_signals(
    *,
    meta: dict[str, Any],
    sectors: dict[str, Any],
    companies: dict[str, Any],
    new_age: dict[str, Any],
    patch_sectors: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Build quant_signals payload and optionally patch sectors in-memory.

    Returns (quant_signals, sectors_payload). sectors_payload is a deep-ish
    copy of sectors with price_momentum + attractiveness updated when patching.
    """
    import copy

    sectors_out = copy.deepcopy(sectors)
    nifty50 = _benchmark_by_name(companies, "Nifty 50")
    nifty500 = _benchmark_by_name(companies, "Nifty 500")
    nifty50_perf = (nifty50 or {}).get("performance") or {}
    nifty500_perf = (nifty500 or {}).get("performance") or {}

    company_signals: dict[str, Any] = {}
    by_sector_rel_1m: dict[str, list[float | None]] = {}
    by_sector_rel_3m: dict[str, list[float | None]] = {}

    for sector_id, rows in (companies.get("by_sector") or {}).items():
        by_sector_rel_1m.setdefault(sector_id, [])
        by_sector_rel_3m.setdefault(sector_id, [])
        for row in rows or []:
            ticker = row.get("ticker")
            if not ticker:
                continue
            rel50 = relative_block(row.get("performance"), nifty50_perf)
            rel500 = relative_block(row.get("performance"), nifty500_perf)
            label = momentum_label(rel50.get("1M"), rel50.get("3M"))
            company_signals[ticker] = {
                "sector_id": sector_id,
                "name": row.get("name"),
                "rel_nifty50": rel50,
                "rel_nifty500": rel500,
                "momentum_label": label,
            }
            by_sector_rel_1m[sector_id].append(rel50.get("1M"))
            by_sector_rel_3m[sector_id].append(rel50.get("3M"))

    new_age_signals: dict[str, Any] = {}
    for row in new_age.get("companies") or []:
        ticker = row.get("ticker")
        if not ticker:
            continue
        rel50 = relative_block(row.get("performance"), nifty50_perf)
        rel500 = relative_block(row.get("performance"), nifty500_perf)
        new_age_signals[ticker] = {
            "name": row.get("name"),
            "rel_nifty50": rel50,
            "rel_nifty500": rel500,
            "momentum_label": momentum_label(rel50.get("1M"), rel50.get("3M")),
        }

    sector_signals: dict[str, Any] = {}
    for sector in sectors_out.get("sectors") or []:
        sector_id = sector["id"]
        rel50 = relative_block(sector.get("performance"), nifty50_perf)
        rel500 = relative_block(sector.get("performance"), nifty500_perf)
        factor = price_momentum_factor(rel50.get("1M"), rel50.get("3M"))
        before = sector.get("attractiveness_score")
        after = before
        if patch_sectors and factor is not None:
            sector.setdefault("factor_scores", {})["price_momentum"] = factor
            weights = sector.get("weights") or {}
            if weights:
                after = attractiveness_score(sector["factor_scores"], weights)
                sector["attractiveness_score"] = after
        sector_signals[sector_id] = {
            "name": sector.get("name"),
            "rel_nifty50": rel50,
            "rel_nifty500": rel500,
            "momentum_label": momentum_label(rel50.get("1M"), rel50.get("3M")),
            "breadth_1m": breadth_pct(by_sector_rel_1m.get(sector_id, [])),
            "breadth_3m": breadth_pct(by_sector_rel_3m.get(sector_id, [])),
            "price_momentum_factor": factor,
            "attractiveness_score_before": before,
            "attractiveness_score_after": after if factor is not None else before,
        }

    quant = {
        "as_of": meta.get("price_date"),
        "benchmark": "Nifty 50",
        "methodology_notes": list(METHODOLOGY_NOTES),
        "benchmarks": {
            "Nifty 50": {
                "ticker": (nifty50 or {}).get("ticker"),
                "performance": nifty50_perf,
            },
            "Nifty 500": {
                "ticker": (nifty500 or {}).get("ticker"),
                "performance": nifty500_perf,
            },
        },
        "sectors": sector_signals,
        "companies": company_signals,
        "new_age": new_age_signals,
    }
    return quant, sectors_out

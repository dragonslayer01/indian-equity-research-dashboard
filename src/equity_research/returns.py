from __future__ import annotations
from datetime import date, datetime
from typing import Sequence
import numpy as np
import pandas as pd

UNAVAILABLE = "Data unavailable from reliable sources."

_HORIZONS_CALENDAR_DAYS = {
    "1D": 1,
    "1W": 7,
    "1M": 30,
    "3M": 91,
    "6M": 182,
    "1Y": 365,
    "3Y_cagr": 365 * 3,
    "5Y_cagr": 365 * 5,
}


def na_listed(listing_date: date) -> str:
    return f"N/A — listed {listing_date.isoformat()}"


def _as_ts(d) -> pd.Timestamp:
    return pd.Timestamp(d).normalize()


def compute_horizon_returns(
    dates: Sequence,
    closes: Sequence[float],
    price_date: pd.Timestamp,
    listing_date: date | None,
) -> dict[str, float | str]:
    keys = ["1D", "1W", "1M", "3M", "6M", "YTD", "1Y", "3Y_cagr", "5Y_cagr"]
    if not dates or not closes or len(dates) != len(closes):
        return {k: UNAVAILABLE for k in keys}

    s = pd.Series(closes, index=pd.to_datetime(dates)).sort_index()
    s = s[~s.index.duplicated(keep="last")]
    price_date = _as_ts(price_date)
    if price_date not in s.index:
        # use last available on/before price_date
        eligible = s.loc[:price_date]
        if eligible.empty:
            return {k: UNAVAILABLE for k in keys}
        price_date = eligible.index[-1]
    end = float(s.loc[price_date])

    def prior_close(target: pd.Timestamp):
        hist = s.loc[:target]
        if hist.empty:
            return None
        return float(hist.iloc[-1]), hist.index[-1]

    out: dict[str, float | str] = {}

    # calendar lookbacks for absolute horizons
    for key, days in [("1D", 1), ("1W", 7), ("1M", 30), ("3M", 91), ("6M", 182), ("1Y", 365)]:
        if listing_date and (price_date.date() - listing_date).days < days:
            out[key] = na_listed(listing_date)
            continue
        target = price_date - pd.Timedelta(days=days)
        # for 1D use previous trading session before price_date
        if key == "1D":
            hist = s.loc[:price_date]
            if len(hist) < 2:
                out[key] = UNAVAILABLE
                continue
            prev = float(hist.iloc[-2])
            out[key] = round((end / prev - 1) * 100, 4)
            continue
        got = prior_close(target)
        if got is None:
            out[key] = UNAVAILABLE
            continue
        start_px, start_dt = got
        if listing_date and start_dt.date() < listing_date:
            out[key] = na_listed(listing_date)
            continue
        out[key] = round((end / start_px - 1) * 100, 4)

    # YTD
    ytd_target = pd.Timestamp(year=price_date.year, month=1, day=1)
    if listing_date and listing_date > ytd_target.date():
        out["YTD"] = na_listed(listing_date)
    else:
        got = prior_close(ytd_target)
        out["YTD"] = UNAVAILABLE if got is None else round((end / got[0] - 1) * 100, 4)

    for key, years in [("3Y_cagr", 3), ("5Y_cagr", 5)]:
        need_days = 365 * years
        if listing_date and (price_date.date() - listing_date).days < need_days:
            out[key] = na_listed(listing_date) if listing_date else UNAVAILABLE
            continue
        target = price_date - pd.DateOffset(years=years)
        got = prior_close(pd.Timestamp(target))
        if got is None:
            out[key] = UNAVAILABLE
            continue
        start_px, start_dt = got
        year_frac = max((price_date - start_dt).days / 365.25, 1e-9)
        cagr = ((end / start_px) ** (1 / year_frac) - 1) * 100
        out[key] = round(float(cagr), 4)

    return out

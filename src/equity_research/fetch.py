from __future__ import annotations

import pandas as pd
import yfinance as yf


def fetch_ohlc(symbol: str, start: str, end: str) -> pd.DataFrame:
    empty = pd.DataFrame(columns=["date", "close"])
    try:
        downloaded = yf.download(
            symbol,
            start=start,
            end=end,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception:
        return empty
    if downloaded.empty:
        return empty

    try:
        close = downloaded["Close"]
        if isinstance(close, pd.DataFrame):
            if symbol in close.columns:
                close = close[symbol]
            else:
                close = close.iloc[:, 0]
        result = close.rename("close").rename_axis("date").reset_index()
        result["date"] = pd.to_datetime(result["date"], errors="coerce")
        if result["date"].dt.tz is not None:
            result["date"] = result["date"].dt.tz_localize(None)
        result["close"] = pd.to_numeric(result["close"], errors="coerce")
        return result.loc[:, ["date", "close"]].dropna().sort_values("date")
    except (KeyError, TypeError, ValueError):
        return empty

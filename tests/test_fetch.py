import pandas as pd

from equity_research import fetch


def test_fetch_ohlc_returns_normalized_date_close(monkeypatch):
    index = pd.to_datetime(["2026-10-01", "2026-10-02"])
    downloaded = pd.DataFrame({"Close": [149.0, 150.0]}, index=index)
    monkeypatch.setattr(fetch.yf, "download", lambda *args, **kwargs: downloaded)

    result = fetch.fetch_ohlc("RELIANCE.NS", "2026-10-01", "2026-10-03")

    assert list(result.columns) == ["date", "close"]
    assert result["close"].tolist() == [149.0, 150.0]


def test_fetch_ohlc_returns_empty_frame_on_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("network unavailable")

    monkeypatch.setattr(fetch.yf, "download", fail)

    result = fetch.fetch_ohlc("RELIANCE.NS", "2026-10-01", "2026-10-03")

    assert result.empty
    assert list(result.columns) == ["date", "close"]

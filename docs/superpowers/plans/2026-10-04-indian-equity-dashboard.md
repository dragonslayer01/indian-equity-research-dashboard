# Indian Equity Research Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a Stage 1 offline multi-page HTML Indian equity research dashboard with real prices/returns/macros and authored sector/universe research, built from versioned JSON.

**Architecture:** Python scripts fetch market history and compute PDF-standard returns into `data/*.json`; Stage 1 research judgment is authored into the same JSON files; `build_dashboard.py` inlines CSS/JS/data into one self-contained `dist/indian_equity_strategy_dashboard.html` with hash-routed pages and dropdowns. No PDF.

**Tech Stack:** Python 3.11+, pytest, yfinance, pandas, numpy; vanilla HTML/CSS/JS (no React); Chart.js inlined or vendored for ranking/heatmap charts; optional Alpha Vantage only as fallback for FX/commodities.

**Spec:** `docs/superpowers/specs/2026-10-04-indian-equity-dashboard-design.md`

## Global Constraints

- Never invent financial/market/consensus/analyst data; missing → exact string `Data unavailable from reliable sources.`
- One shared `price_date` across all performance tables in a build
- Returns: 1D/1W/1M/3M/6M/YTD/1Y = absolute price return %; 3Y/5Y = CAGR %; short history → `N/A — listed [listing date]`
- Price returns split/bonus adjusted; dividends excluded unless labelled total return
- Include Nifty 50 and Nifty 500 benchmark rows on every performance table
- HTML only — no PDF generation
- Multi-page + dropdown navigation (not tabs-only)
- Offline single-file deliverable under `dist/`
- No live browser market fetch; refresh = re-run scripts + rebuild
- Commits only when the user explicitly asks (skip commit steps during execution unless requested)

---

## File Structure

| Path | Responsibility |
|------|----------------|
| `requirements.txt` | Python deps |
| `README.md` | How to fetch, build, open |
| `src/equity_research/__init__.py` | Package marker |
| `src/equity_research/returns.py` | Pure return math from price series |
| `src/equity_research/fetch.py` | Download OHLC / macro series |
| `src/equity_research/schemas.py` | Load/validate JSON shapes |
| `src/equity_research/merge.py` | Merge fetched returns into research JSON |
| `scripts/fetch_market_data.py` | CLI entry: fetch → write raw cache + update data JSON |
| `scripts/compute_returns.py` | CLI entry: recompute returns from cached OHLC |
| `scripts/build_dashboard.py` | Embed data into HTML |
| `data/meta.json` | Dates, methodology flags |
| `data/macro.json` | Macro scorecard + numeric series |
| `data/market_regime.json` | Regime analysis |
| `data/sectors.json` | Scores, theses, index performance |
| `data/companies.json` | Universes + stock performance |
| `data/new_age.json` | Top 25 + performance |
| `data/sources.json` | Bibliography |
| `data/raw/` | Cached OHLC parquet/CSV (gitignored optional) |
| `src/dashboard/index.template.html` | HTML shell with `{{EMBEDDED_DATA}}` |
| `src/dashboard/styles.css` | Layout, tables, print |
| `src/dashboard/app.js` | Router, dropdowns, tables, heatmaps |
| `dist/indian_equity_strategy_dashboard.html` | Built artifact |
| `tests/test_returns.py` | Return math |
| `tests/test_schemas.py` | JSON schema validation |
| `tests/test_build_dashboard.py` | Builder produces embed + offline markers |
| `tests/fixtures/` | Tiny OHLC + sample JSON |

---

### Task 1: Project scaffold + return math (TDD)

**Files:**
- Create: `requirements.txt`
- Create: `README.md`
- Create: `src/equity_research/__init__.py`
- Create: `src/equity_research/returns.py`
- Create: `tests/test_returns.py`
- Create: `tests/fixtures/sample_prices.csv`
- Create: `.gitignore`

**Interfaces:**
- Consumes: none
- Produces:
  - `compute_horizon_returns(dates: list[pd.Timestamp], closes: list[float], price_date: pd.Timestamp, listing_date: pd.Timestamp | None) -> dict[str, float | str]`
  - Keys: `1D`,`1W`,`1M`,`3M`,`6M`,`YTD`,`1Y`,`3Y_cagr`,`5Y_cagr`
  - `UNAVAILABLE = "Data unavailable from reliable sources."`
  - `na_listed(listing_date) -> str` format `N/A — listed YYYY-MM-DD`

- [ ] **Step 1: Write failing tests for return math**

Create `tests/fixtures/sample_prices.csv`:

```csv
date,close
2021-10-04,100
2022-10-04,110
2023-10-04,121
2024-10-04,133.1
2025-10-03,140
2026-09-04,145
2026-09-26,148
2026-10-02,149
2026-10-03,150
```

Create `tests/test_returns.py`:

```python
from datetime import date
import pandas as pd
from equity_research.returns import compute_horizon_returns, UNAVAILABLE, na_listed


def _series():
    df = pd.read_csv("tests/fixtures/sample_prices.csv", parse_dates=["date"])
    return df["date"].list if False else list(df["date"]), list(df["close"])


def test_na_listed_format():
    assert na_listed(date(2024, 5, 1)) == "N/A — listed 2024-05-01"


def test_1d_and_1y_absolute_returns():
    dates, closes = [], []
    df = pd.read_csv("tests/fixtures/sample_prices.csv", parse_dates=["date"])
    dates, closes = list(df["date"]), list(df["close"])
    out = compute_horizon_returns(dates, closes, price_date=pd.Timestamp("2026-10-03"), listing_date=date(2020, 1, 1))
    assert round(out["1D"], 4) == round((150 / 149 - 1) * 100, 4)
    assert round(out["1Y"], 2) == round((150 / 140 - 1) * 100, 2)


def test_3y_cagr_not_absolute():
    df = pd.read_csv("tests/fixtures/sample_prices.csv", parse_dates=["date"])
    out = compute_horizon_returns(list(df["date"]), list(df["close"]), price_date=pd.Timestamp("2026-10-03"), listing_date=date(2020, 1, 1))
    # 2023-10-04 close 121 → 150 over ~3y
    assert isinstance(out["3Y_cagr"], float)
    assert out["3Y_cagr"] != round((150 / 121 - 1) * 100, 4)


def test_short_listing_returns_na_string():
    df = pd.read_csv("tests/fixtures/sample_prices.csv", parse_dates=["date"])
    out = compute_horizon_returns(list(df["date"]), list(df["close"]), price_date=pd.Timestamp("2026-10-03"), listing_date=date(2025, 6, 1))
    assert out["5Y_cagr"] == "N/A — listed 2025-06-01"


def test_empty_series_unavailable():
    out = compute_horizon_returns([], [], price_date=pd.Timestamp("2026-10-03"), listing_date=None)
    assert out["1D"] == UNAVAILABLE
```

- [ ] **Step 2: Run tests — expect fail**

Run: `cd personal_projects/indian-equity-research-dashboard && python3 -m pip install pytest pandas numpy -q && PYTHONPATH=src pytest tests/test_returns.py -v`

Expected: FAIL (`ModuleNotFoundError` or import error for `equity_research.returns`)

- [ ] **Step 3: Implement `returns.py`**

```python
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
```

- [ ] **Step 4: Add packaging files and re-run tests**

`requirements.txt`:

```
pytest>=8.0
pandas>=2.0
numpy>=1.26
yfinance>=0.2.40
```

`.gitignore`:

```
__pycache__/
.pytest_cache/
.venv/
data/raw/
dist/*.html
.DS_Store
```

`README.md`: document `PYTHONPATH=src`, fetch, build, open `dist/...html`.

`src/equity_research/__init__.py`: empty.

Run: `PYTHONPATH=src pytest tests/test_returns.py -v`  
Expected: PASS

---

### Task 2: JSON schemas + skeleton data files

**Files:**
- Create: `src/equity_research/schemas.py`
- Create: `tests/test_schemas.py`
- Create: `data/meta.json`, `macro.json`, `market_regime.json`, `sectors.json`, `companies.json`, `new_age.json`, `sources.json`

**Interfaces:**
- Consumes: none
- Produces: `load_all_data(data_dir: Path) -> dict[str, Any]` raising `ValueError` if required keys missing; `REQUIRED_FILES = ["meta","macro","market_regime","sectors","companies","new_age","sources"]`

- [ ] **Step 1: Write schema tests**

```python
from pathlib import Path
from equity_research.schemas import load_all_data, validate_meta

ROOT = Path(__file__).resolve().parents[1]


def test_load_all_data_from_repo():
    data = load_all_data(ROOT / "data")
    assert set(data) >= {"meta", "macro", "market_regime", "sectors", "companies", "new_age", "sources"}


def test_meta_requires_dates():
    validate_meta({"analysis_date": "2026-10-04", "data_cutoff_date": "2026-10-03", "price_date": "2026-10-03", "return_type": "price_return_split_bonus_adjusted_dividends_excluded"})
```

- [ ] **Step 2: Run — expect fail**

Run: `PYTHONPATH=src pytest tests/test_schemas.py -v`  
Expected: FAIL import or missing files

- [ ] **Step 3: Implement schemas + skeleton JSON**

`schemas.py` must require:

- `meta`: `analysis_date`, `data_cutoff_date`, `price_date`, `return_type`
- `sectors`: `sectors` list; each item has `id`, `name`, `stance`, `attractiveness_score`, `factor_scores`, `representative_index`, `performance`, `thesis`, `expectation_gaps`
- `companies`: `benchmarks` + `by_sector` map of lists with `ticker`,`name`,`classification`,`performance`
- `new_age`: `companies` list length intended 25 (validate `len == 25` once populated; skeleton may use `status: "skeleton"` and skip length until Task 5)
- `macro`: `variables` list with `name`,`current`,`direction`,`outlook_6_12m`,`earnings_impact`,`sector_market_impact`,`source`,`as_of`
- `market_regime`: `label`,`evidence`,`earnings`,`valuation`,`flows`
- `sources`: `items` list of `{title,url_or_publisher,as_of,notes}`

Skeleton `meta.json`:

```json
{
  "analysis_date": "2026-10-04",
  "data_cutoff_date": "2026-10-03",
  "price_date": "2026-10-03",
  "return_type": "price_return_split_bonus_adjusted_dividends_excluded",
  "currency": "INR",
  "benchmarks": ["Nifty 50", "Nifty 500"]
}
```

Create minimal valid skeletons for other files (empty arrays allowed except meta). For `new_age.json` use `"status": "skeleton"` and `companies: []` until Task 5; schema skips length check when status is skeleton.

- [ ] **Step 4: Tests pass**

Run: `PYTHONPATH=src pytest tests/test_schemas.py -v`  
Expected: PASS

---

### Task 3: Market fetch + merge returns into JSON

**Files:**
- Create: `src/equity_research/fetch.py`
- Create: `src/equity_research/merge.py`
- Create: `scripts/fetch_market_data.py`
- Create: `scripts/compute_returns.py`
- Create: `tests/test_merge.py`
- Create: `tests/fixtures/ohlc_reliance.csv`

**Interfaces:**
- Consumes: `compute_horizon_returns`
- Produces:
  - `fetch_ohlc(symbol: str, start: str, end: str) -> pd.DataFrame` columns `date,close` (wrap yfinance; on failure return empty DataFrame)
  - `performance_from_ohlc(df, price_date, listing_date) -> dict`
  - `apply_performance(entity: dict, performance: dict, source: str) -> dict` sets `entity["performance"]`, `entity["price"]`, `entity["price_date"]`, `entity["source"]`
  - CLI `python scripts/fetch_market_data.py --data-dir data --raw-dir data/raw`

**Universe symbols (initial Stage 1 fetch list — adjust if delisted):**

Benchmarks: `^NSEI` (Nifty 50), `^CRSLDX` or `^NSEI` fallback notes — if Nifty 500 symbol fails, store unavailable and document in sources.

Sector indices (yfinance symbols to try):  
`^CNXAUTO`,`^CNXBANK`,`^CNXIT`,`^CNXFMCG`,`^CNXPHARMA`,`^CNXMETAL`,`^CNXREALTY`,`^CNXENERGY`,`^CNXFIN`,`^CNXINFRA` (record actual symbol used per sector).

Conventional sectors (~10) and illustrative tickers (`.NS`):

1. banks — HDFCBANK, ICICIBANK, SBIN, KOTAKBANK, AXISBANK, INDUSINDBK, BANDHANBNK, FEDERALBNK, IDFCFIRSTB, AUBANK  
2. it — TCS, INFY, HCLTECH, WIPRO, TECHM, LTIM, PERSISTENT, COFORGE, MPHASIS, TATAELXSI  
3. auto — MARUTI, M&M, TATAMOTORS, BAJAJ-AUTO, HEROMOTOCO, EICHERMOT, TVSMOTOR, ASHOKLEY, BHARATFORG, MOTHERSON  
4. fmcg — HINDUNILVR, ITC, NESTLEIND, BRITANNIA, TATACONSUM, DABUR, MARICO, GODREJCP, COLPAL, UNITDSPR  
5. pharma — SUNPHARMA, DRREDDY, CIPLA, DIVISLAB, APOLLOHOSP, MAXHEALTH, TORNTPHARM, LUPIN, AUROPHARMA, BIOCON  
6. metals — TATASTEEL, JSWSTEEL, HINDALCO, VEDL, NMDC, COALINDIA, NATIONALUM, SAIL, JINDALSTEL, HINDZINC  
7. energy — RELIANCE, ONGC, BPCL, IOC, GAIL, POWERGRID, NTPC, ADANIGREEN, TATAPOWER, ADANIPOWER  
8. financials_nbfc — BAJFINANCE, BAJAJFINSV, HDFCLIFE, SBILIFE, PFC, RECLTD, CHOLAFIN, MUTHOOTFIN, SHRIRAMFIN, LICI  
9. capital_goods_infra — LT, SIEMENS, ABB, BEL, HAL, BHEL, THERMAX, CUMMINSIND, POLYCAB, KEI  
10. realty_consumer_disc — DLF, GODREJPROP, OBEROIRLTY, PRESTIGE, BRIGADE, TITAN, TRENT, PAGEIND, INDIGO, KALYANKJIL

New-Age 25 (verify listing; drop/replace if needed):  
ZOMATO (Eternal), SWIGGY, NYKAA, DELHIVERY, PAYTM, POLICYBZR, NAUKRI, INDIAMART, CARTRADE, FIRSTCRY, OLAELEC, ATHERENERG, HONASA, IXIGO, BLACKBUCK, GODIGIT, MOBIKWIK, AFFLE, EASEMYTRIP, YATRA, MAPMYINDIA, TANLA, ROUTE, PB FINTECH already POLICYBZR, DMART is not new-age — prefer pure new-age; fill to 25 with currently listed relevant names after fetch validation.

- [ ] **Step 1: Write merge tests with fixture OHLC (no network)**

```python
import pandas as pd
from equity_research.merge import performance_from_ohlc, apply_performance
from equity_research.returns import UNAVAILABLE

def test_performance_from_fixture():
    df = pd.read_csv("tests/fixtures/ohlc_reliance.csv", parse_dates=["date"])
    perf = performance_from_ohlc(df, price_date=pd.Timestamp("2026-10-03"), listing_date=None)
    assert "1D" in perf and perf["1D"] != UNAVAILABLE

def test_apply_performance_sets_fields():
    entity = {"ticker": "RELIANCE.NS", "name": "Reliance Industries"}
    apply_performance(entity, {"1D": 0.5}, price=150.0, price_date="2026-10-03", source="Yahoo Finance (NSE)")
    assert entity["price"] == 150.0
    assert entity["performance"]["1D"] == 0.5
```

Copy/adapt `sample_prices.csv` to `ohlc_reliance.csv`.

- [ ] **Step 2: Implement fetch/merge + CLIs**

`fetch.py`: use `yfinance.download` or `Ticker.history`; never invent rows; write CSV under `data/raw/{symbol}.csv`.

`merge.py`: `performance_from_ohlc` → calls `compute_horizon_returns`; `update_dataset_prices(data_dir, raw_dir, price_date)` walks sectors/companies/new_age/benchmarks and fills performance.

CLI `fetch_market_data.py`:

```python
# argparse: --data-dir, --raw-dir, --price-date YYYY-MM-DD
# 1) load tickers from companies.json + new_age.json + sectors.json indices + benchmarks
# 2) fetch each symbol to raw CSV
# 3) call update_dataset_prices
# 4) set meta.price_date and meta.data_cutoff_date
```

- [ ] **Step 3: Run unit tests (offline)**

Run: `PYTHONPATH=src pytest tests/test_merge.py tests/test_returns.py -v`  
Expected: PASS

- [ ] **Step 4: Live fetch smoke (network)**

Run: `PYTHONPATH=src python scripts/fetch_market_data.py --data-dir data --raw-dir data/raw`  
Expected: CSVs created; JSON performance fields populated for majority of `.NS` tickers; failures marked unavailable; console summary `ok=X fail=Y`

---

### Task 4: Author Stage 1 research JSON (substantive content)

**Files:**
- Modify: `data/macro.json`, `market_regime.json`, `sectors.json`, `companies.json`, `new_age.json`, `sources.json`, `meta.json`
- Create: `research/stage1_notes.md` (working notes; optional)

**Interfaces:**
- Consumes: performance fields already on entities from Task 3
- Produces: fully populated research judgment fields; `new_age.status = "final"` and `len(companies)==25`; schema length check enabled

- [ ] **Step 1: Fill macro + regime from sourced public info**

For each macro variable row include `source` and `as_of`. Prefer RBI MPC statements, MOSPI CPI releases, Budget docs, NSE market reports. Numeric API fields (USDINR, Brent) come from fetch where possible.

Regime JSON must set `label` to one of the prompt examples (e.g. `Mid Cycle / Valuation Compression`) and `evidence` as bullet list strings.

- [ ] **Step 2: Score all major sectors; select ~10 for deep thesis**

Each selected sector needs factor_scores 1–10 for: demand, earnings_growth, earnings_revision, margins, balance_sheet, valuation, policy, competitive_structure, capital_cycle, price_momentum, macro_sensitivity, downside_risk; documented `weights`; `attractiveness_score` /100; `stance`; thesis bullets; `expectation_gaps.positive` / `.negative`.

- [ ] **Step 3: Company universes + classifications**

For each selected sector, 12–20 institutional-quality names with classification enum:

`Sector Leader | High-Quality Compounder | Growth Challenger | Cyclical Opportunity | Turnaround | Value Opportunity | High-Risk`

- [ ] **Step 4: New-Age Top 25**

Set sub_sector, listing_date, brief `profitability_cycle_stage` (Stage 1–5 per prompt), and performance from fetch. Include benchmarks Nifty 50, Nifty 500, Nifty India Digital (or note proxy).

- [ ] **Step 5: Sources page data**

Every material series cited with publisher and as_of.

- [ ] **Step 6: Validate**

Run: `PYTHONPATH=src python -c "from pathlib import Path; from equity_research.schemas import load_all_data; load_all_data(Path('data')); print('ok')"`  
Expected: `ok` and new_age count 25

---

### Task 5: Dashboard front-end (multi-page + dropdowns)

**Files:**
- Create: `src/dashboard/styles.css`
- Create: `src/dashboard/app.js`
- Create: `src/dashboard/index.template.html`
- Create: `tests/test_dashboard_js_smoke.py` (checks template markers only; optional node-free)

**Interfaces:**
- Consumes: global `window.RESEARCH_DATA` object with keys matching JSON files
- Produces: hash routes `#/overview|#/macro|#/regime|#/sector-rankings|#/sector-performance|#/companies|#/new-age|#/portfolio-stance|#/sources|#/deep-dives|#/analyst|#/valuation|#/portfolio`
- Dropdown `#sector-select` filters company tables
- Functions: `renderRoute()`, `renderReturnsTable(rows)`, `renderHeatmap(rows, periods)`, `filterEntities(q)`

- [ ] **Step 1: HTML template shell**

`index.template.html` structure:

- Sidebar nav links for pages above  
- Header with `data-bind` ids for analysis/cutoff/price dates  
- KPI strip containers  
- `<main id="page-root">`  
- Placeholder `/*__RESEARCH_DATA__*/` script slot replaced by builder  
- Script tag loading inlined CSS/JS (builder inlines file contents)

- [ ] **Step 2: Implement `app.js` router + pages**

Minimum behavior:

```javascript
const ROUTES = {
  overview: renderOverview,
  macro: renderMacro,
  regime: renderRegime,
  "sector-rankings": renderSectorRankings,
  "sector-performance": renderSectorPerformance,
  companies: renderCompanies,
  "new-age": renderNewAge,
  "portfolio-stance": renderPortfolioStance,
  sources: renderSources,
  "deep-dives": () => renderGate("Sector Deep Dives", "Stage 2"),
  analyst: () => renderGate("Analyst & Street View", "Stage 2"),
  valuation: () => renderGate("Valuation & Scenarios", "Stage 2"),
  portfolio: () => renderGate("Full Portfolio", "Stage 4"),
};

function parseRoute() {
  const h = (location.hash || "#/overview").replace(/^#\/?/, "");
  return h.split("?")[0];
}
```

`renderReturnsTable`: build `<table>` with columns Company/Index, Ticker, Price, Price Date, 1D…5Y; color positive/negative; support click-to-sort.

`renderCompanies`: sector `<select>` populated from `RESEARCH_DATA.sectors.sectors`; on change rebuild table from `companies.by_sector[id]` plus benchmark rows.

Heatmap: HTML grid or canvas; green–red scale by return value; ignore string N/A cells.

Search box filters visible table rows by name/ticker.

- [ ] **Step 3: CSS**

- CSS variables for institutional palette (avoid purple-gradient cliché; use navy/slate/off-white)
- Sidebar layout desktop; collapsible on mobile  
- Print: hide sidebar, show all relevant tables  

- [ ] **Step 4: Marker test**

```python
from pathlib import Path

def test_template_has_embed_marker_and_routes():
    html = Path("src/dashboard/index.template.html").read_text()
    assert "__RESEARCH_DATA__" in html
    assert "#/macro" in html or "macro" in html
```

Run: `pytest tests/test_dashboard_js_smoke.py -v`  
Expected: PASS

---

### Task 6: HTML builder + end-to-end artifact

**Files:**
- Create: `scripts/build_dashboard.py`
- Create: `tests/test_build_dashboard.py`
- Create: `dist/.gitkeep`

**Interfaces:**
- Consumes: `load_all_data`, template + css + js files
- Produces: `build_dashboard(data_dir: Path, src_dir: Path, out_path: Path) -> Path`  
  Output HTML contains inlined CSS, inlined JS, and `window.RESEARCH_DATA = {...}`; no external network URLs required for core function (Chart.js: either skip and use CSS heatmap only, or inline a minimal chart helper — **do not depend on CDN at runtime**)

- [ ] **Step 1: Failing builder test**

```python
from pathlib import Path
from equity_research.build import build_dashboard

def test_build_embeds_data(tmp_path):
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "dash.html"
    build_dashboard(root / "data", root / "src" / "dashboard", out)
    text = out.read_text()
    assert "window.RESEARCH_DATA" in text
    assert "Data unavailable from reliable sources." in text or "analysis_date" in text
    assert "cdn.jsdelivr" not in text
```

Move builder core to `src/equity_research/build.py`; CLI wraps it.

- [ ] **Step 2: Implement builder**

```python
def build_dashboard(data_dir, src_dir, out_path):
    data = load_all_data(data_dir)
    html = (src_dir / "index.template.html").read_text()
    css = (src_dir / "styles.css").read_text()
    js = (src_dir / "app.js").read_text()
    payload = json.dumps(data, ensure_ascii=False)
    html = html.replace("/*__INLINE_CSS__*/", css)
    html = html.replace("/*__INLINE_JS__*/", js)
    html = html.replace("/*__RESEARCH_DATA__*/", f"window.RESEARCH_DATA = {payload};")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path
```

Template must contain those three markers inside `<style>`, `<script>`, and data `<script>`.

- [ ] **Step 3: Build dist artifact**

Run:

```bash
PYTHONPATH=src python scripts/build_dashboard.py \
  --data-dir data \
  --src-dir src/dashboard \
  --out dist/indian_equity_strategy_dashboard.html
```

Expected: file exists; open in browser shows Overview KPIs and navigable pages.

- [ ] **Step 4: Acceptance checklist (manual)**

Walk spec §8 acceptance criteria; fix gaps before calling Stage 1 complete.

---

### Task 7: README polish + refresh workflow

**Files:**
- Modify: `README.md`
- Modify: `data/sources.json` if fetch symbols documentation needed

- [ ] **Step 1: Document exact commands**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python scripts/fetch_market_data.py --data-dir data --raw-dir data/raw
PYTHONPATH=src python scripts/build_dashboard.py --data-dir data --src-dir src/dashboard --out dist/indian_equity_strategy_dashboard.html
open dist/indian_equity_strategy_dashboard.html
PYTHONPATH=src pytest -v
```

- [ ] **Step 2: Note Stage 1 stop line for later research**

Include in README: after Stage 1, next user action is picking a sector for Stage 2 deep dive (HTML gate pages already present).

---

## Spec coverage self-review

| Spec requirement | Task |
|------------------|------|
| Stage 1 macro/regime/sectors/universes/New-Age | Task 4 |
| Real prices/returns | Tasks 1, 3 |
| Shared price date + return rules | Tasks 1, 3, meta |
| Multi-page + dropdowns | Task 5 |
| No PDF | Global + Task 6 |
| Single offline HTML | Task 6 |
| Stage 2+ gates | Task 5 |
| Sources/cutoffs | Tasks 2, 4, 5 header |
| Heatmaps/sortable tables/search | Task 5 |
| Benchmarks on tables | Tasks 3–5 |
| Refresh = scripts | Task 7 |

## Placeholder / consistency notes

- Builder module path locked as `src/equity_research/build.py` + `scripts/build_dashboard.py`
- `UNAVAILABLE` string identical everywhere
- Charting: CSS/HTML heatmaps only (no CDN) to satisfy offline constraint
- New-age length validation only when `status == "final"`

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-10-04-indian-equity-dashboard.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute tasks in this session with checkpoints  

Which approach?

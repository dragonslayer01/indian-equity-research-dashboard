# Indian Equity Research Dashboard

Stage 1 institutional Indian equity research as a **single self-contained offline HTML** file. Market prices and returns are loaded from versioned JSON (Yahoo Finance via `yfinance`); macro, regime, sector, and universe views are authored in the same `data/` files and inlined at build time.

Design spec: [`docs/superpowers/specs/2026-10-04-indian-equity-dashboard-design.md`](docs/superpowers/specs/2026-10-04-indian-equity-dashboard-design.md)

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Use `PYTHONPATH=src` when running scripts or tests from the repo root (the package is not installed as a wheel).

## Refresh workflow (data → HTML)

Re-fetch market history, merge returns into `data/*.json`, rebuild the dashboard, and open it locally:

```bash
PYTHONPATH=src python scripts/fetch_market_data.py --data-dir data --raw-dir data/raw
PYTHONPATH=src python scripts/build_dashboard.py --data-dir data --src-dir src/dashboard --out dist/index.html
open dist/index.html
```

- **Fetch** reads tickers from `data/sectors.json` (sector indices), `data/companies.json` (benchmarks + universe), and `data/new_age.json`; writes OHLC CSVs under `data/raw/` and updates shared `price_date` / performance fields. It also refreshes the Yahoo Finance line in `data/sources.json`.
- **Build** produces `dist/index.html` (and a legacy copy `dist/indian_equity_strategy_dashboard.html`) with inlined CSS, JS, and `window.RESEARCH_DATA` — no CDN or server required to view.
- To recompute returns from cached CSVs **without** network access, use `PYTHONPATH=src python scripts/compute_returns.py --data-dir data --raw-dir data/raw`.

## Deploy to Netlify

Site is configured via `netlify.toml`: Netlify rebuilds `dist/index.html` from `data/` + `src/dashboard/` on each deploy (no extra Node build).

1. Push this repo to GitHub/GitLab.
2. In Netlify: **Add new site → Import an existing project** → select the repo.
3. Leave build settings as detected from `netlify.toml` (`publish = dist`).
4. Deploy. The site root serves the Stage 1 dashboard.

**Drag-and-drop alternative:** run the build locally, then drop the `dist/` folder on [Netlify Drop](https://app.netlify.com/drop).

## Tests

```bash
PYTHONPATH=src pytest -v
```

If `pytest` is not on your PATH, use `PYTHONPATH=src python3 -m pytest -v` instead.

## Stage 1 scope and what comes next

**Stage 1 (shipped)** covers overview KPIs, macro, market regime, sector rankings and performance, conventional and New-Age universes, portfolio stance, and sources — all navigable via hash routes in the built HTML.

**Stop line for research:** Stage 1 is complete and the Stage 2 **Pharmaceuticals and Healthcare** deep dive is now published, with additional sector packs added as they are authored. *Analyst & Street View* and *Valuation & Scenarios* remain gated until their research inputs and validation requirements are complete.

## Stage 2 (in progress)

- **Pharmaceuticals and Healthcare** and **Banks** deep dives + shortlists are live at `#/deep-dives` (Banks: 18-name universe, 10-name shortlist, hybrid KPI badges).
- **Next:** Macro deepen, then New-Age deepen.
- Analyst View, Valuation, and Full Portfolio remain gated.

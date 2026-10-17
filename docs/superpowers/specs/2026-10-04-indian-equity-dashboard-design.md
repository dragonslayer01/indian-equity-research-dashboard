# Indian Equity Research Dashboard — Design Spec

**Date:** 2026-10-04  
**Location:** `personal_projects/indian-equity-research-dashboard/`  
**Source prompt:** Master Prompt — Indian Equity Market, Sector & Company Research (30 pages)  
**Status:** Draft for user review (pre-implementation)

---

## 1. Goal

Build a Stage 1 institutional Indian equity research product as an interactive, offline HTML application with real market prices, returns, and macro inputs, plus authored research judgment (regime, sector scores, universes, New-Age Top 25).

Central question the product must help answer:

> Where should capital be allocated today to maximize forward risk-adjusted returns?

**Horizon:** 6–24 months primary; also flag long-term compounders.

## 2. Scope

### In scope (v1 / Stage 1)

- India macro framework and equity market regime
- Sector attractiveness scoring and OW / Moderate OW / Neutral / UW / Avoid
- ~10 selected conventional sectors with short theses and expectation gaps
- Investable company universes (up to 15–20 per selected sector) with classifications
- India New-Age / Digital Economy Top 25 with sub-sector grouping
- Stock and sector price & performance tables: 1D, 1W, 1M, 3M, 6M, YTD, 1Y, 3Y (CAGR), 5Y (CAGR)
- Nifty 50 and Nifty 500 benchmark rows on every performance table
- Multi-page HTML UI with dropdowns, search, filters, heatmaps, KPI strip
- Sources, data-cutoff dates, and methodology notes
- Data-driven JSON → single offline HTML build

### Out of scope (v1)

- PDF generation or PDF build step (explicit product decision)
- Individual company deep dives (financial bridges, peer scorecards, QoQ/YoY deep analysis)
- Sell-side / brokerage digests (last 30–60 days)
- Full scenario valuation (Bear/Base/Bull) and probability-weighted expected returns
- Final 15–25 stock institutional portfolio (Stage 4)
- Live in-browser auto-refresh of market data

### Deferred pages (present as Stage 2+ gates)

- Sector Deep Dives
- Analyst & Street View
- Valuation & Scenarios
- Full stock-level Portfolio Construction

## 3. Architecture

### Approach

**Data-driven builder (Approach B):** versioned JSON research + market datasets, plus Python scripts that fetch/compute market fields and embed everything into one self-contained HTML file.

### Project layout

```
indian-equity-research-dashboard/
├── README.md
├── docs/superpowers/specs/2026-10-04-indian-equity-dashboard-design.md
├── requirements.txt
├── scripts/
│   ├── fetch_market_data.py
│   ├── compute_returns.py
│   └── build_dashboard.py
├── data/
│   ├── meta.json
│   ├── macro.json
│   ├── market_regime.json
│   ├── sectors.json
│   ├── companies.json
│   ├── new_age.json
│   └── sources.json
├── research/                 # optional narrative drafts before JSON merge
├── src/dashboard/            # HTML/CSS/JS templates used by builder
└── dist/
    └── indian_equity_strategy_dashboard.html
```

### Data flow

```
Public APIs / official publications
        → fetch_market_data.py
        → compute_returns.py
        → data/*.json (market fields)

Authored Stage 1 research (sourced)
        → data/*.json (judgment fields)

build_dashboard.py
        → dist/indian_equity_strategy_dashboard.html (offline)
```

### Principles

- Never invent financial, market, consensus, technical, or analyst data
- Missing verified data → exact string: `Data unavailable from reliable sources.`
- Every market-sensitive field carries source + as-of (or inherits from `meta.json`)
- Distinguish fact vs guidance vs consensus vs external view vs our analysis vs assumption in research text
- One shared **price date** for all companies/sectors within a build’s performance tables
- Returns: 1D–1Y absolute price returns (%); 3Y/5Y annualized CAGR (%), clearly labelled
- Price returns adjusted for splits/bonuses; dividends excluded unless explicitly labelled total return
- Listing too short for a period → `N/A — listed [listing date]`

## 4. Data → JSON strategy

### Market / quantitative feed (automated)

| Series | Intended source priority | Output |
|--------|--------------------------|--------|
| NSE equity OHLC history | yfinance (`.NS`), Alpha Vantage if resolved | prices + returns in `companies.json` / `new_age.json` |
| Sectoral / thematic indices | yfinance / index providers as available | `sectors.json` performance block |
| Nifty 50 / Nifty 500 | same | benchmark rows |
| USDINR, Brent/WTI, US yields | Alpha Vantage / public series | `macro.json` quantitative fields |
| India CPI, GDP, fiscal, RBI stance | RBI / MOSPI / Budget / official releases (manual entry if no API) | `macro.json` with source + as_of |

Scripts must not interpolate missing prices. Failed fetches leave the unavailable string and log the attempted source.

### Research / judgment feed (authored)

Populated into structured JSON (not free-form HTML):

- Macro condition / direction / 6–12M outlook / earnings & sector impact
- Market regime label + evidence bullets
- Sector factor scores (1–10), weights, attractiveness /100, stance
- Sector thesis bullets and positive/negative expectation gaps
- Company classification labels
- New-Age Top 25 selection and brief profitability-cycle assessment
- Sector portfolio stance (overweight map only in Stage 1)

### Example company performance object

```json
{
  "ticker": "RELIANCE.NS",
  "nse_symbol": "RELIANCE",
  "name": "Reliance Industries",
  "sector_id": "energy",
  "classification": "Sector Leader",
  "price": 2950.25,
  "price_date": "2026-10-03",
  "currency": "INR",
  "returns": {
    "1D": 0.4,
    "1W": -1.2,
    "1M": 3.1,
    "3M": 8.4,
    "6M": 12.0,
    "YTD": 15.2,
    "1Y": 18.7,
    "3Y_cagr": 11.2,
    "5Y_cagr": 14.5
  },
  "source": "Yahoo Finance (NSE)",
  "return_type": "price_return_split_bonus_adjusted_dividends_excluded"
}
```

### Refresh model

Browser does not live-fetch. Refresh = re-run fetch/compute scripts, update research JSON if needed, rebuild HTML.

## 5. UI / UX

### Product decision vs master prompt

| Master prompt | This product |
|---------------|--------------|
| Interactive HTML + PDF | HTML only |
| Navigation tabs | Multi-page app + dropdowns |
| Single self-contained HTML | Keep: one offline HTML deliverable |

### Navigation

- Primary **pages** via sidebar/top nav with hash routing (`#/macro`, `#/sectors/banks`, etc.)
- Browser back/forward and bookmarkable routes
- **Dropdowns** for sector, sub-sector, classification, time-period heatmap focus
- Search typeahead for companies

### Page map (Stage 1)

1. **Overview** — KPI strip, regime one-liner, entry points
2. **Macro** — variable scorecard (current / direction / outlook / impacts)
3. **Market Regime** — earnings, valuation, flows, regime conclusion
4. **Sector Rankings** — scorecard, stance, thesis panel via sector dropdown
5. **Sector Performance** — index return table + heatmap; Nifty benchmarks
6. **Company Universe** — sector dropdown → 15–20 names + returns + benchmarks
7. **New-Age Top 25** — sub-sector dropdown + returns + IPO vs issue where available
8. **Portfolio Stance** — sector overweight map only
9. **Sources** — methodology, cutoffs, bibliography
10. **Deep Dive / Analyst / Valuation / Full Portfolio** — Stage 2+ gate screens

### Header (global)

- Analysis date, data-cutoff date, price date
- Return methodology note

### Visual / interaction requirements

- Sortable, filterable tables
- Conditional color: green positive / red negative returns
- Returns heatmaps (sectors × periods; companies × periods within selected sector)
- Responsive desktop + mobile; print-friendly CSS
- Data source / cutoff note visible on every page
- Institutional research aesthetic; clear hierarchy; not a dense “dashboard of widgets” on first view of Overview

## 6. Stage 1 research content requirements

Follow master-prompt analytical sequence through company universe + New-Age list, then stop before company deep dives.

Must include:

- Macro transmission narrative (macro → demand/costs/liquidity → earnings → sectors → valuation)
- Explicit current Indian equity market regime label with evidence
- Sector attractiveness scores with documented weights
- ~10 conventional sectors selected for detailed thesis + universe (do not force exactly ten if relevance differs)
- New-Age Top 25 determined from current listing relevance (examples in prompt are not mandatory)
- Major risks and key expectation gaps at market/sector level
- Honest gaps where sell-side consensus or India-specific macros cannot be verified

After Stage 1 HTML is complete, conversational stop line (for later research sessions):

> Market and sector framework complete. Share the sector you would like me to analyze first.

## 7. Build sequence

1. Scaffold project + dependencies
2. Define JSON schemas / sample empty structures
3. Implement fetch + returns computation
4. Populate Stage 1 research JSON with sourced content
5. Implement multi-page HTML app (routing, dropdowns, tables, heatmaps, KPIs)
6. Build script → `dist/indian_equity_strategy_dashboard.html`
7. Verification pass against acceptance criteria

## 8. Acceptance criteria

- [ ] Opens offline in a modern browser; no login or server required to view
- [ ] No PDF artifacts or PDF build step
- [ ] Shared price date across performance tables; header shows analysis + cutoff + price dates
- [ ] Real prices/returns/macros populated where sources resolve; otherwise explicit unavailable wording
- [ ] Macro, regime, sector rankings, company universes, and New-Age Top 25 are substantive (not placeholder lorem)
- [ ] Multi-page navigation + dropdowns + search/filter work; back/forward works
- [ ] Deep-dive / analyst / valuation / full portfolio routes show Stage 2+ gates only
- [ ] Sources page lists material series with source + as-of
- [ ] Return conventions match section 3 Principles (absolute vs CAGR; N/A listing rule; benchmarks present)

## 9. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Spotty India index/equity coverage from free APIs | Prefer yfinance `.NS`; fall back per ticker; mark unavailable rather than invent |
| Macro India series not API-friendly | Manual entry from RBI/MOSPI/Budget with citations |
| Scope creep into Stage 2 deep dives | Hard gates on deferred pages; Stage 1 stop rule |
| Stale data after build | Document refresh commands; show cutoff prominently |
| Huge company universe slowing UI | Virtualize or paginate tables if needed; sector dropdown limits DOM |

## 10. Next steps after spec approval

1. User reviews and approves this design doc
2. Write implementation plan (`writing-plans` skill)
3. Execute Stage 1 build in `personal_projects/indian-equity-research-dashboard/`

---

## Decision log

| Decision | Choice |
|----------|--------|
| v1 research depth | Stage 1 full research + real prices/returns/macros (Option B) |
| Architecture | JSON + Python builder → single offline HTML |
| PDF | Not in product |
| Navigation | Multi-page + dropdowns (not flat tabs-only) |
| Live browser data fetch | No; rebuild to refresh |
| Repo path | `personal_projects/indian-equity-research-dashboard/` |

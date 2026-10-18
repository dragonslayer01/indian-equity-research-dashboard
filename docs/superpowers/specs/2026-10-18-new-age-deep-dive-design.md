# Stage 2 — New-Age Deep Dive Pack on `#/deep-dives`

**Date:** 2026-10-18  
**Status:** Approved (implementing)  
**Delivery:** Push to `main`

## Goal

Publish a New-Age / digital-economy deep-dive pack with a 10-name shortlist and hybrid digital KPIs on `#/deep-dives`. Keep `#/new-age` Top 25 monitor unchanged.

## Decisions

| Item | Choice |
|------|--------|
| Placement | Full deep-dive pack (option C) |
| KPIs | `unit_economics`, `competitive_moat`, `profitability_path`, `governance_risk` |
| Shortlist (10) | Eternal, Nykaa, Info Edge, IndiaMART, Affle, MapmyIndia, Go Digit, Intellect, Latent View, ixigo |
| Universe join | `new_age.companies` tickers/performance |
| Schema | Expand allowed KPI ids to Banks ∪ digital sets |

## File / loader

- `data/deep_dives/new_age.json`
- `index.json` entry `published`
- `load_deep_dives(..., new_age)` injects `by_sector["new_age"] = new_age["companies"]` for ticker checks
- UI joins returns from `DATA.new_age.companies` when `pack.sector_id === "new_age"`

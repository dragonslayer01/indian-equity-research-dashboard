# Stage 2 — Macro Deepen Pack on `#/macro`

**Date:** 2026-10-18  
**Status:** Approved design (implementing)  
**Delivery:** Push to `main`  
**Next after this:** New-Age deepen

## Goal

Add a versioned **macro deep pack** (`data/macro_deep.json`) and append its research panels under the existing Macro scorecard on `#/macro`.

## Decisions locked

| Decision | Choice |
|----------|--------|
| Depth | New pack module (option C) |
| UI | Enhance `#/macro` — scorecard first, pack below (option A) |
| File split | Separate `macro_deep.json` from Stage 1 `macro.json` |
| Crude / INR | Keep unavailable unless cited |
| Analyst / Valuation | Remain gated |

## Data shape (`macro_deep.json`)

Required keys:

- `as_of` (YYYY-MM-DD)
- `headline` (string)
- `base_case`, `upside`, `downside` (string lists)
- `transmission_map` (string list) — ordered macro → earnings → sectors
- `portfolio_implications` (string list) — ties to Banks / Pharma / Capital Goods OW leans
- `risk_watchlist` — list of `{ id, title, severity, note }` with `severity` ∈ {`high`,`medium`,`low`}
- `open_questions`, `methodology_notes` (string lists)
- `sources` — same shape as other source items

Honesty: never invent levels; use `Data unavailable from reliable sources.` where needed.

## Loader / UI

- `load_all_data` loads and validates `macro_deep.json` → `RESEARCH_DATA.macro_deep`
- `renderMacro` keeps variable cards + Stage 1 transmission; appends pack sections
- Sources page: optional subsection for macro-deep sources (or fold into deep-dive sources pattern)

## Acceptance

- Tests load pack; invalid severity fails
- Build embeds pack headline
- `#/macro` shows scenarios + risk watchlist
- Push to `main`

# Stage 2 — Banks Sector Deep Dive + Expanded Universe + Hybrid KPIs

**Date:** 2026-10-18  
**Status:** Approved (amended: larger universe + 10-name shortlist)  
**Location:** `personal_projects/indian-equity-research-dashboard/`  
**Prior art:**
- Stage 1: `docs/superpowers/specs/2026-10-04-indian-equity-dashboard-design.md`
- Pharma deep dive: `docs/superpowers/specs/2026-10-18-stage2-pharma-deep-dive-design.md`

**Delivery:** Implement and push directly to `main`.

**Roadmap (separate specs after this ships):** Macro deepen → New-Age deepen.

---

## 1. Goal

Publish a **Banks** Stage 2 deep dive on `#/deep-dives`: sector narrative, **10-name shortlist** with **hybrid banking KPIs**, and an **expanded Stage 1 banks universe** (~18 names) for the Companies monitor.

Reuse the Pharma pack/UI path; extend shortlist schema with optional `kpis`. Raise published shortlist length to **4–10** (Pharma remains at 5).

**Central question:** Within Indian banks, where should capital lean on a 6–24 month horizon, with liability, asset-quality, and margin risks stated honestly.

---

## 2. Scope

### In scope

- Expand `companies.by_sector.banks` from 12 → 18 names (add PNB, Union Bank, Indian Bank, Yes Bank, RBL Bank, Karur Vysya); fetch/merge Yahoo performance
- Create `data/deep_dives/banks.json` with **10** shortlist names + hybrid KPIs
- Update `data/deep_dives/index.json`: Banks `published` + `as_of`
- Schema: optional shortlist `kpis`; published shortlist length **4–10** (validator max 10)
- UI: KPI strip on shortlist cards; Banks pack `as_of`
- Join returns from `companies.by_sector.banks` by ticker
- Tests + README; push to `main`
- Keep `#/analyst`, `#/valuation`, `#/portfolio` gated

### Out of scope

- Macro deepen / New-Age deepen
- Sell-side scrapes; full valuation scenarios
- Inventing NIM / GNPA / credit-cost % without cited `as_of` + `source`
- Authored deep-dive notes for every universe name (shortlist only)

### Honesty rule (inherited)

Missing → exact string: `Data unavailable from reliable sources.`

---

## 3. Architecture

```
data/companies.json                 # banks universe 18 names + fetch
data/deep_dives/index.json          # banks → published
data/deep_dives/banks.json          # narrative + 10 shortlist + kpis
src/equity_research/schemas.py      # kpis + shortlist length 4–10
src/dashboard/app.js                # KPI strip
```

### Expanded universe (18)

**Existing (12):** HDFCBANK, ICICIBANK, SBIN, KOTAKBANK, AXISBANK, INDUSINDBK, BANDHANBNK, FEDERALBNK, IDFCFIRSTB, AUBANK, BANKBARODA, CANBK  

**Add (6):**

| Ticker | Name | Classification |
|--------|------|----------------|
| PNB.NS | Punjab National Bank | Cyclical Opportunity |
| UNIONBANK.NS | Union Bank of India | Cyclical Opportunity |
| INDIANB.NS | Indian Bank | Value Opportunity |
| YESBANK.NS | Yes Bank | Turnaround |
| RBLBANK.NS | RBL Bank | High-Risk |
| KARURVYSYA.NS | Karur Vysya Bank | Growth Challenger |

### Shortlist (10) — locked

| # | Ticker | Name |
|---|--------|------|
| 1 | HDFCBANK.NS | HDFC Bank |
| 2 | ICICIBANK.NS | ICICI Bank |
| 3 | SBIN.NS | State Bank of India |
| 4 | KOTAKBANK.NS | Kotak Mahindra Bank |
| 5 | AXISBANK.NS | Axis Bank |
| 6 | BANKBARODA.NS | Bank of Baroda |
| 7 | FEDERALBNK.NS | Federal Bank |
| 8 | IDFCFIRSTB.NS | IDFC First Bank |
| 9 | AUBANK.NS | AU Small Finance Bank |
| 10 | INDUSINDBK.NS | IndusInd Bank |

Universe-only (not shortlist): BANDHANBNK, CANBK, PNB, UNIONBANK, INDIANB, YESBANK, RBLBANK, KARURVYSYA.

### Hybrid KPI schema

Same as prior approval: optional `kpis` with `id` ∈ {`nim`,`asset_quality`,`liability_franchise`,`credit_cost`}, `qualitative` ∈ {`strong`,`adequate`,`watch`,`weak`}, numeric `value` only with `as_of` + `source`.

### Shortlist length rules

- `validate_deep_dive_pack`: shortlist length **1–10**
- `load_deep_dives` for published packs: **4–10**
- Pharma pack (5 names) unchanged and still valid

---

## 4. Content guidelines

- Prefer franchise quality; shortlist mixes leaders, PSU scale, and selected challengers — not every cyclical PSU.
- KPI numerics null + honesty notes unless cited.
- Show pack `as_of` and `meta.price_date`.

---

## 5. Testing & acceptance

- `companies.by_sector.banks` has 18 tickers including the six adds
- `deep_dives.packs.banks` shortlist length 10; all tickers in universe
- Pharma still loads
- Build embeds Banks stance string + a KPI label
- Deep Dives Banks shows 10 cards + KPI strips; no coming_next
- Analyst/valuation gated

---

## 6. Decisions locked

| Decision | Choice |
|----------|--------|
| Expansion | Universe + shortlist (option C) |
| Universe size | 18 (12 + 6) |
| Shortlist size | 10 |
| Published shortlist cap | 4–10 |
| KPIs | Hybrid qualitative + optional cited numeric |
| Delivery | Push to `main` |
| Next after Banks | Macro → New-Age |

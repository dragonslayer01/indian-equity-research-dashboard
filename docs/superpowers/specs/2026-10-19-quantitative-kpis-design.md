# Quantitative KPIs — inventory, computation, and automation

**Date:** 2026-10-19  
**Status:** Phase 1 shipped (price overlays + auto `price_momentum`; judgment factors stay authored)  
**Product rule:** Never invent fundamentals, consensus, or analyst data. Missing → `Data unavailable from reliable sources.`  
**Prior:** Weekly price refresh Action; GitHub Pages deploy; option A (numbers only, no LLM research rewrite).

---

## 1. Goal

Define **every quantitative KPI** in the product, mark which ones we can **compute from market prices**, build code to refresh those on a schedule, and keep **authored judgment** (theses, qualitative deep-dive KPIs, most sector factors) human-owned.

Central question stays the same: where capital should lean — but weekly auto-updates must be **transparent number overlays + one price-driven sector factor**, not silent stance changes.

---

## 2. KPI inventory (complete list)

### A. Already live — price / return KPIs (auto today via fetch)

| KPI | Entity | Source | Unit | Horizon |
|-----|--------|--------|------|---------|
| Absolute price return | Company, New-Age, Sector index, Benchmarks | Yahoo OHLC | % | 1D, 1W, 1M, 3M, 6M, YTD, 1Y |
| CAGR | Same | Yahoo OHLC | % ann. | 3Y, 5Y |
| Last close | Same | Yahoo | INR (or index pts) | as-of `price_date` |
| Shared `price_date` | Global `meta` | Fetch | date | weekly |

**Status:** Shipped. Weekly Action already refreshes these.

---

### B. Price-derived overlay KPIs (Phase 1 — **build next**)

Computed from existing `performance` fields + Nifty 50 / Nifty 500 benchmarks. No new market APIs.

| ID | KPI | Entity | Formula (simple) | Output |
|----|-----|--------|------------------|--------|
| `rel_nifty50` | Relative return vs Nifty 50 | Company, New-Age, Sector | `entity_return − nifty50_return` | % for 1M, 3M, YTD, 1Y |
| `rel_nifty500` | Relative return vs Nifty 500 | Same | same vs Nifty 500 | % for 1M, 3M, YTD, 1Y |
| `momentum_label` | Momentum vs Nifty 50 | Same | Rule: both 1M & 3M rel > 0 → `outperforming`; both < 0 → `underperforming`; else `mixed`; missing → `unavailable` | enum |
| `breadth_1m` | Sector universe breadth | Sector (conventional) | % of names in sector with `rel_nifty50.1M` > 0 | % |
| `breadth_3m` | Sector universe breadth | Sector | same for 3M | % |
| `price_momentum_factor` | Sector factor 1–10 | Sector | Map avg of sector-index `rel_nifty50` 1M & 3M into 1–10 (table below) | int 1–10 |
| `attractiveness_score_recalc` | Sector score 0–100 | Sector | Weighted sum of factors / 10 (existing formula); **only `price_momentum` factor overwritten** by auto map | float |

**`price_momentum` mapping (sector index vs Nifty 50, average of 1M and 3M relative returns):**

| Avg relative return | Factor score |
|---------------------|--------------|
| ≥ +8% | 9 |
| ≥ +4% | 8 |
| ≥ +2% | 7 |
| ≥ 0% | 6 |
| ≥ −2% | 5 |
| ≥ −4% | 4 |
| ≥ −8% | 3 |
| < −8% | 2 |
| unavailable | keep prior authored value; do not invent |

**Stance rule (Phase 1):** Do **not** auto-change `stance` (OW / Neutral / …). Only refresh `factor_scores.price_momentum` + recompute `attractiveness_score`. Log old vs new score in Action summary.

---

### C. Sector factor scores — authored vs auto (clarity)

Current 12 factors (weights sum to 100; score = Σ(factor × weight) / 10):

| Factor | Auto in Phase 1? | Why |
|--------|------------------|-----|
| `demand` | No | Judgment / fundamentals |
| `earnings_growth` | No | Needs earnings series |
| `earnings_revision` | No | Needs sell-side / revision data |
| `margins` | No | Fundamentals |
| `balance_sheet` | No | Fundamentals |
| `valuation` | No | Needs PE/PB or fair-value inputs |
| `policy` | No | Macro / regulatory judgment |
| `competitive_structure` | No | Industry structure judgment |
| `capital_cycle` | No | Cycle judgment |
| `price_momentum` | **Yes** | Purely from index returns |
| `macro_sensitivity` | No | Judgment |
| `downside_risk` | No* | *Optional Phase 2 from drawdowns — see §4 |

Authored fields that stay human: `thesis`, `expectation_gaps`, `stance`, all factors except `price_momentum`.

---

### D. Deep-dive qualitative KPIs (exist today — **not auto** in Phase 1)

**Banks shortlist:** `nim`, `asset_quality`, `liability_franchise`, `credit_cost`  
**New-Age shortlist:** `unit_economics`, `competitive_moat`, `profitability_path`, `governance_risk`  

Schema allows optional numeric `value` + `as_of` + `source`. Today values are mostly null + qualitative badges.

| Auto Phase 1? | Reason |
|---------------|--------|
| No | Require filings / RBI / company disclosures; Yahoo alone cannot fill NIM, GNPA, unit economics honestly |

**Phase 2+ (out of scope now):** ingest cited series when a source is wired; never invent.

---

### E. Macro quantitative fields (exist / gaps)

| Series | Status | Auto Phase 1? |
|--------|--------|---------------|
| GDP, CPI, MPC/repo, liquidity notes | Authored in `macro.json` | No (official releases, not Yahoo equity) |
| Crude / INR / global yields | Often unavailable | No until a cited series is wired |

---

### F. Market-regime quantitative evidence (authored)

Regime label + evidence bullets are research judgment. Phase 1 may **append** a small evidence line from index returns (e.g. “Nifty 50 3M/1Y relative path”) into `quant_signals.json` for UI, **without** rewriting `market_regime.json`.

---

## 3. Architecture (Phase 1)

### Files

```
data/quant_signals.json          # NEW — full overlay; safe to overwrite weekly
data/sectors.json                # UPDATE — only price_momentum + attractiveness_score
scripts/compute_quant_signals.py # NEW
src/equity_research/quant.py     # NEW — pure functions + mapping tables
src/equity_research/schemas.py   # validate quant_signals
src/dashboard/app.js             # show rel returns + momentum + breadth
.github/workflows/weekly-price-refresh.yml  # fetch → quant → commit
```

### `quant_signals.json` shape (sketch)

```json
{
  "as_of": "YYYY-MM-DD",
  "benchmark": "Nifty 50",
  "methodology_notes": [
    "Relative return = entity absolute return minus benchmark return for the same horizon.",
    "Momentum labels are rule-based from 1M and 3M relative returns vs Nifty 50.",
    "Sector price_momentum factor is mapped from sector-index relative returns; other factors remain authored."
  ],
  "benchmarks": {
    "Nifty 50": { "ticker": "...", "performance": {} },
    "Nifty 500": { "ticker": "...", "performance": {} }
  },
  "sectors": {
    "banks": {
      "rel_nifty50": { "1M": 0.0, "3M": 0.0, "YTD": 0.0, "1Y": 0.0 },
      "rel_nifty500": {},
      "momentum_label": "mixed",
      "breadth_1m": 55.0,
      "breadth_3m": 40.0,
      "price_momentum_factor": 4,
      "attractiveness_score_before": 69.9,
      "attractiveness_score_after": 68.5
    }
  },
  "companies": {
    "HDFCBANK.NS": {
      "sector_id": "banks",
      "rel_nifty50": {},
      "rel_nifty500": {},
      "momentum_label": "outperforming"
    }
  },
  "new_age": {
    "ETERNAL.NS": { "rel_nifty50": {}, "momentum_label": "mixed" }
  }
}
```

Unavailable cells use `null` in JSON; UI shows the honesty string.

### UI (minimal)

- Sector Performance + Rankings: show rel 1M/3M and momentum badge; show breadth on sector detail
- Company / New-Age tables: add Rel 1M, Rel 3M, Momentum columns (vs Nifty 50)
- Overview KPI strip (optional): count of sectors with momentum `outperforming`

No new nav page required in Phase 1.

### Weekly automation

```
schedule / manual
  → fetch_market_data.py
  → compute_quant_signals.py   # writes quant_signals.json + patches sectors.json momentum/score
  → commit data/*.json changes
  → Pages deploy (existing)
```

---

## 4. Phase 2 candidates (listed, not building now)

| KPI | Needs |
|-----|-------|
| Realized vol / max drawdown | OHLC history in CI (`data/raw` ephemeral) |
| Auto `downside_risk` factor from drawdown | Same + mapping table |
| Valuation multiples (PE, PB) | Cited fundamental source |
| Earnings revision breadth | Sell-side / revision vendor |
| Bank numeric NIM / GNPA / credit cost | Filings / RBI |
| New-Age unit economics numerics | Filings / IR |
| Macro oil / INR / yields | Cited series API |
| Auto stance from score bands | Product decision (easy to abuse) |

---

## 5. Testing & acceptance (Phase 1)

- Unit tests: relative return math; momentum label rules; momentum→factor map; attractiveness recalc with only `price_momentum` changed
- Schema test: `quant_signals.json` validates; missing benchmark → nulls, no crash
- Build embeds `quant_signals`; UI smoke shows a Rel / Momentum column
- Weekly workflow runs `compute_quant_signals` after fetch
- Deep-dive qualitative KPIs and theses unchanged by the job

---

## 6. Decisions to confirm

| # | Decision | Proposed default |
|---|----------|------------------|
| 1 | Primary benchmark for momentum / rel display | Nifty 50 (also store Nifty 500) |
| 2 | Auto-update `sectors.json` `price_momentum` + score | Yes |
| 3 | Auto-change sector `stance` | **No** (Phase 1) |
| 4 | Touch deep-dive / macro authored JSON | **No** |
| 5 | New UI page vs columns on existing pages | Columns on existing pages |

---

## 7. Implementation order (after approval)

1. Spec approved (this doc).  
2. `quant.py` + `compute_quant_signals.py` + tests.  
3. Wire loader + UI columns.  
4. Extend weekly Action.  
5. Push to `main`; run workflow once; verify Pages.

---

## 8. Out of scope (this project slice)

- LLM rewriting of theses / shortlists  
- Inventing fundamental KPIs  
- Changing OW/Neutral automatically  
- Netlify  

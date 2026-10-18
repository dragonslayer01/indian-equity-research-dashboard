# Stage 2 — Banks Sector Deep Dive + Shortlist + Hybrid KPIs

**Date:** 2026-10-18  
**Status:** Approved design (awaiting user review of this written spec)  
**Location:** `personal_projects/indian-equity-research-dashboard/`  
**Prior art:**
- Stage 1: `docs/superpowers/specs/2026-10-04-indian-equity-dashboard-design.md`
- Pharma deep dive: `docs/superpowers/specs/2026-10-18-stage2-pharma-deep-dive-design.md`

**Delivery:** Implement and push directly to `main` (no long-lived feature branch required).

**Roadmap (separate specs after this ships):** Macro deepen → New-Age deepen.

---

## 1. Goal

Publish a **Banks** Stage 2 deep dive on `#/deep-dives`: sector narrative, **~5-name shortlist**, and **hybrid banking KPIs** on shortlist cards (qualitative badge + optional cited numeric).

Reuse the Pharma pack/UI path; extend the shortlist schema with optional `kpis` so Pharma packs remain valid without KPIs.

**Central question:** Within Indian banks, where should capital lean on a 6–24 month horizon, with liability, asset-quality, and margin risks stated honestly.

---

## 2. Scope

### In scope

- Create `data/deep_dives/banks.json` (full pack content)
- Update `data/deep_dives/index.json`: Banks `status: published`, set `as_of`
- Extend schema for optional shortlist `kpis` (hybrid qualitative + optional numeric)
- UI: render KPI strip on shortlist cards when `kpis` present; show Banks pack `as_of` like Pharma
- Join returns/price from `companies.by_sector.banks` by ticker (do not duplicate returns in the pack)
- Tests: pack load, ticker cross-check, KPI validation, build embed, smoke that Banks is published
- README: Banks live; next = Macro / New-Age
- Keep `#/analyst`, `#/valuation`, `#/portfolio` gated

### Out of scope

- Macro deepen / New-Age deepen (next roadmap slices)
- Sell-side consensus scrapes; full valuation scenarios
- Inventing NIM / GNPA / credit-cost percentages without a cited source + `as_of`
- Full 12-name bank deep dives (shortlist only)
- Changing Pharma pack content except ensuring optional `kpis` does not break validation

### Honesty rule (inherited)

Never invent financial, market, consensus, technical, or analyst data. Missing → exact string:

`Data unavailable from reliable sources.`

If a KPI has no reliable numeric, set `value` to `null` and put the unavailable string (or a short qualitative-only rationale) in `note`.

---

## 3. Architecture

### Approach

**Extend pack schema with banking KPIs (Approach 2)** + **hybrid KPI presentation (option C)** from brainstorming.

```
data/deep_dives/index.json          # banks → published
data/deep_dives/banks.json          # narrative + shortlist + kpis
src/equity_research/schemas.py      # optional kpis validation
src/dashboard/app.js                # KPI strip on shortlist cards
```

No new hash routes. Pharma continues to load without `kpis`.

### Index

```json
{
  "sector_id": "banks",
  "name": "Banks",
  "status": "published",
  "as_of": "YYYY-MM-DD"
}
```

Pharma entry remains `published`. No `coming_next` Banks row after this ships (unless a third sector is added later).

### Banks pack core

Same required top-level keys as Pharma:

`sector_id`, `name`, `as_of`, `stance_summary`, `overview`, `sub_themes`, `drivers`, `risks`, `expectation_gaps`, `shortlist` (4–6), `methodology_notes`, `sources`

- `sector_id` must be `banks` and match `companies.by_sector.banks`
- Align stance with Stage 1 (`OW`, attractiveness ~69.9) unless the pack explicitly documents a change

Suggested sub-themes:
- Large private franchise
- PSU franchise / liability scale
- Deposit competition & margins
- Asset quality / unsecured watchpoints

### Shortlist (locked default)

| Priority | Ticker | Name |
|----------|--------|------|
| 1 | HDFCBANK.NS | HDFC Bank |
| 2 | ICICIBANK.NS | ICICI Bank |
| 3 | SBIN.NS | State Bank of India |
| 4 | KOTAKBANK.NS | Kotak Mahindra Bank |
| 5 | AXISBANK.NS | Axis Bank |

Swaps require an explicit plan amendment. All tickers must exist in `companies.by_sector.banks`.

### Hybrid KPI schema

Optional on each shortlist item: `kpis` — array of KPI objects.

| Field | Required | Notes |
|-------|----------|--------|
| `id` | yes | One of: `nim`, `asset_quality`, `liability_franchise`, `credit_cost` |
| `label` | yes | Display label (e.g. `"NIM"`) |
| `qualitative` | yes | Exactly one of: `strong`, `adequate`, `watch`, `weak` |
| `value` | no | number or `null` |
| `unit` | no | e.g. `pct`; ignored if `value` is null |
| `as_of` | no | `YYYY-MM-DD` when `value` is a number |
| `source` | no | publisher or URL string when `value` is a number |
| `note` | no | rationale or `Data unavailable from reliable sources.` |

**Validation rules:**
- If `kpis` is present, it must be a list (may be empty only if omitted entirely — prefer omit vs empty).
- Each item must include `id`, `label`, `qualitative`.
- `qualitative` ∈ {`strong`,`adequate`,`watch`,`weak`}.
- `id` ∈ the Banks standard set above (packs in other sectors may later define their own sets; for this slice only Banks uses KPIs).
- If `value` is not `null`, it must be a number, and both `as_of` and `source` are required (reject otherwise).
- Duplicate `id` within one shortlist item’s `kpis` → `ValueError`.
- Pharma shortlist without `kpis` remains valid.

**UI rules:**
- Render a compact KPI strip under open questions / above the returns strip.
- Show qualitative as a badge; if `value` is a number, show formatted value + unit + `as_of`.
- If `value` is null, show qualitative + `note` (or unavailable string).
- Do not invent colours beyond existing stance/badge patterns; reuse muted panel styling.

### Loader / schema touchpoints

- Reuse `load_deep_dives` / `validate_deep_dive_pack`.
- Add `validate_shortlist_kpis(item)` called from pack validation when `kpis` key exists.
- Published Banks pack must have 4–6 shortlist names (existing rule).

### Sources

Pack-local `sources` appear under Sources → “Deep-dive sources” (existing subsection). Include Stage 1 banks thesis/universe and any numeric KPI citations with `as_of`.

---

## 4. Content guidelines

- Prefer liability franchise quality and diversified large banks over pure cyclical PSU beta unless thesis justifies it.
- Call out deposit competition, unsecured stress, and margin discipline (Stage 1 gaps).
- Numerics only when cited; otherwise qualitative + unavailable string.
- Research `as_of` and `meta.price_date` both shown on the deep-dive page.

---

## 5. Testing & acceptance

- Load `load_all_data` includes `deep_dives.packs.banks`.
- Unknown shortlist ticker fails; invalid qualitative / numeric without `as_of` fails.
- Pharma pack still loads (no `kpis`).
- Build HTML contains Banks stance_summary (or unique pack string) and at least one KPI label from the pack.
- `#/deep-dives` Banks selection shows shortlist + KPI strip; no “coming next” for Banks.
- Analyst/valuation still show gate copy.
- Offline: no CDN.

---

## 6. Delivery sequence

1. This spec approved by user.
2. Implementation plan (`writing-plans`).
3. Schema + tests for KPIs → banks.json + index flip → UI strip → README.
4. Push commits to `main`; Netlify rebuilds.

---

## 7. Decisions locked

| Decision | Choice |
|----------|--------|
| Roadmap order | Banks → Macro → New-Age |
| Banks depth | Deep dive + ~5 shortlist |
| Approach | Extend schema with banking KPIs |
| KPI presentation | Hybrid (qualitative + optional cited numeric) |
| Shortlist | HDFC, ICICI, SBI, Kotak, Axis |
| Standard KPI ids | `nim`, `asset_quality`, `liability_franchise`, `credit_cost` |
| Git delivery | Push directly to `main` |
| Analyst / Valuation | Remain gated |

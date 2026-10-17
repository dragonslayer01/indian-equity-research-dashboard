# Stage 2 — Pharma Sector Deep Dive + Shortlist

**Date:** 2026-10-18  
**Status:** Approved approach (design for user review)  
**Location:** `personal_projects/indian-equity-research-dashboard/`  
**Prior art:** Stage 1 design `docs/superpowers/specs/2026-10-04-indian-equity-dashboard-design.md`

---

## 1. Goal

Unlock **Sector Deep Dives** for **Pharmaceuticals and Healthcare** with a substantive sector narrative plus an authored **~5-name shortlist**, shipped through the existing JSON → single offline HTML pipeline.

**Sequencing:** Pharma first (this spec). **Banks** follows as a second deep-dive pack using the same schema/UI — out of scope for this implementation plan except for a explicit “coming next” placeholder in the sector picker.

**Central question unchanged:** Where should capital be allocated (within Pharma) on a 6–24 month horizon, with risks and gaps stated honestly.

---

## 2. Scope

### In scope

- New versioned JSON pack: `data/deep_dives/pharma.json`
- Schema validation + build embed into `window.RESEARCH_DATA.deep_dives`
- Replace `#/deep-dives` gate with a real **Sector Deep Dives** page:
  - Sector dropdown listing packs (Pharma = published; Banks = “Coming next” / not selectable or selectable with empty state)
  - Sector overview: stance linkage, drivers, risks, expectation gaps, sub-themes
  - Shortlist cards (~5 names): thesis bullets, why-now, key risks, classification; performance strip joined from existing `companies.by_sector.pharma` by ticker
- Sources note for deep-dive authorship / limitations
- Tests for schema load and deep-dive page smoke (no invented financials)
- Keep Analyst (`#/analyst`), Valuation (`#/valuation`), Full Portfolio (`#/portfolio`) **gated**

### Out of scope (this slice)

- Banks deep-dive content (pack file deferred; UI may show “Coming next”)
- Sell-side consensus digests, broker notes scraping
- Bear/Base/Bull valuation models or probability-weighted returns
- Full 12-name company deep dives (only shortlist gets authored notes)
- Live in-browser data refresh
- Changing Stage 1 pages beyond nav label / gate removal for deep-dives

### Honesty rule (inherited)

Never invent financial, market, consensus, technical, or analyst data. Missing → exact string:

`Data unavailable from reliable sources.`

---

## 3. Architecture

### Approach

**JSON deep-dive pack + unlock `#/deep-dives`** (Approach 1 from brainstorming).

```
data/deep_dives/pharma.json  ──┐
data/*.json (Stage 1)          ├──► load_all_data() ──► build_dashboard()
src/dashboard/app.js           ──┘         │
                                           ▼
                              dist/index.html (RESEARCH_DATA.deep_dives)
```

### Why not inline into `sectors.json`

Stage 1 sector objects stay lean for rankings/heatmaps. Deep-dive narrative is long-form and sector-gated; separate packs keep Banks addition a drop-in file.

### Data model

`RESEARCH_DATA.deep_dives` shape:

```json
{
  "packs": {
    "pharma": { "...pack fields..." }
  },
  "index": [
    {
      "sector_id": "pharma",
      "name": "Pharmaceuticals and Healthcare",
      "status": "published",
      "as_of": "YYYY-MM-DD"
    },
    {
      "sector_id": "banks",
      "name": "Banks",
      "status": "coming_next",
      "as_of": null
    }
  ]
}
```

- **`index`:** drives the UI dropdown (published vs coming_next). Authored only in `data/deep_dives/index.json` (includes Banks as `coming_next` without a banks pack file).
- **`packs[sector_id]`:** loaded from `data/deep_dives/{sector_id}.json` when that index entry has `status == published`.

### Pharma pack schema (`data/deep_dives/pharma.json`)

Required top-level keys:

| Key | Type | Notes |
|-----|------|--------|
| `sector_id` | string | Must be `pharma` (matches `sectors.sectors[].id`) |
| `name` | string | Display name |
| `as_of` | string | Research as-of date (YYYY-MM-DD) |
| `stance_summary` | string | One-line stance vs Stage 1 scorecard |
| `overview` | string[] | 3–6 bullets: demand, regulation, export/domestic mix |
| `sub_themes` | object[] | `{ "id", "title", "summary" }` — e.g. domestic brands, US generics, hospitals/API |
| `drivers` | string[] | Positive catalysts |
| `risks` | string[] | Sector risks |
| `expectation_gaps` | object | `{ "positive": string[], "negative": string[] }` |
| `shortlist` | object[] | Exactly 4–6 names (target 5) |
| `methodology_notes` | string[] | Limitations; what was not verified |
| `sources` | object[] | `{ "title", "url_or_publisher", "as_of", "notes" }` — pack-local; also mirrored or linked on Sources page optionally |

**Shortlist item keys:**

| Key | Type | Notes |
|-----|------|--------|
| `ticker` | string | Must exist in `companies.by_sector.pharma` |
| `name` | string | Display; should match universe name |
| `priority` | number | 1 = highest conviction in shortlist order |
| `role_in_sector` | string | e.g. domestic franchise / specialty / hospital |
| `thesis` | string[] | 2–4 bullets |
| `why_now` | string[] | 1–3 bullets (6–24M) |
| `key_risks` | string[] | 2–4 bullets |
| `classification` | string | Prefer same label as Stage 1 company row |
| `open_questions` | string[] | Honest unknowns; may include unavailable string |

UI **joins** `performance` / `price` / `price_date` from `companies.by_sector.pharma` by `ticker` at render time — do **not** duplicate return series inside the pack.

### Loader changes

- Extend `load_all_data` to read `data/deep_dives/index.json` and each published pack.
- Validate packs with `validate_deep_dive_pack`.
- Cross-check: every shortlist `ticker` ∈ `companies.by_sector[sector_id]`; fail build/tests if missing.
- Stage 1 `REQUIRED_FILES` stay as-is; deep dives are **additive** (if `deep_dives/` missing, either fail closed for Stage 2 branch or treat as empty packs — **this project will require `index.json` once Stage 2 lands** so the Deep Dives page never silently regresses to a blank gate).

### UI (`#/deep-dives`)

1. Page header: “Sector Deep Dives” / Stage 2.
2. Toolbar: sector `<select>` from `deep_dives.index`.
3. If selected status is `coming_next`: empty-state panel (“Banks deep dive is next after Pharma.”) + link back to overview or companies.
4. If `published`:
   - Stance summary + overview list
   - Sub-themes as compact sections (not card chrome overload)
   - Drivers / risks / expectation gaps panels
   - Shortlist: ordered cards; each shows thesis/why_now/risks + mini returns row (1M, 3M, 1Y, YTD) from joined company data
5. Footer cutoff uses global `meta.price_date` / pack `as_of`.
6. Sidebar: remove Stage “2” badge visual treatment that implies fully locked, or keep badge but page is live — **remove the gate-only render**; optional small “Stage 2” eyebrow is fine.

Analyst / Valuation / Portfolio routes unchanged gates.

### Sources page

Append pack `sources` into the Sources view **or** add a subsection “Deep-dive sources” listing published packs’ source rows. Prefer subsection to avoid mixing with Yahoo/macro register without attribution.

---

## 4. Content guidelines (Pharma)

- Align stance with Stage 1 (`OW`, score ~71) unless pack explicitly documents a change and `as_of`.
- Shortlist drawn from existing 12-name Pharma universe; do not add tickers not already in `companies.json` without a Stage 1 universe update first.
- Prefer specialty / domestic brand / hospital-quality names consistent with Stage 1 sector thesis; exclude undifferentiated filler.
- No fabricated EPS, PE, or street target prices — use unavailable string if not sourced.
- Research `as_of` may differ from `meta.price_date`; both shown.

---

## 5. Testing & acceptance

- Schema unit tests: valid Pharma pack loads; missing shortlist ticker raises; invalid keys raise.
- Build test: `window.RESEARCH_DATA.deep_dives` present; Pharma pack embedded.
- JS smoke: deep-dives route renders without throwing; gate string “Not yet published” **absent** on deep-dives when Pharma pack present; still present on analyst/valuation.
- Manual: open `dist/index.html` → Deep Dives → Pharma shortlist visible; Banks coming_next message works.
- Offline: no CDN.

---

## 6. Delivery sequence

1. Spec (this doc) approved.
2. Implementation plan (writing-plans).
3. Implement schema + loader + UI shell with fixture pack if needed.
4. Author real Pharma pack content.
5. Rebuild HTML; run tests.
6. Commit: include Oct-16 (or later) price refresh + Stage 2 Pharma; push for Netlify.
7. Later: Banks pack (`status: published`) using same schema — separate small plan.

---

## 7. Non-goals / risks

| Risk | Mitigation |
|------|------------|
| Scope creep into valuation/analyst | Keep those routes gated |
| Invented numbers in shortlist | Unavailable string + methodology_notes |
| Shortlist tickers drift from universe | Schema cross-check |
| Banks half-built | `coming_next` in index only |

---

## 8. Decisions locked

| Decision | Choice |
|----------|--------|
| Approach | JSON pack + unlock `#/deep-dives` |
| First sector | Pharma |
| Second sector | Banks (after Pharma ships) |
| Depth | Sector deep dive + ~5 shortlist |
| Valuation / Analyst | Remain gated |

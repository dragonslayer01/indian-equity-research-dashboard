# Stage 2 Pharma Deep Dive + Shortlist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unlock `#/deep-dives` with a Pharma sector deep-dive pack and ~5-name shortlist, via versioned JSON embedded in the offline HTML build.

**Architecture:** Add `data/deep_dives/index.json` plus `data/deep_dives/pharma.json`. Extend `load_all_data` to validate and embed `deep_dives` into `window.RESEARCH_DATA`. Replace the Deep Dives gate in `app.js` with a real page that joins shortlist tickers to Stage 1 company performance. Banks appears in the index as `coming_next` only.

**Tech Stack:** Python 3 / pytest (schemas + build), vanilla JS + CSS (dashboard), existing Netlify/`build_dashboard.py` pipeline.

**Spec:** `docs/superpowers/specs/2026-10-18-stage2-pharma-deep-dive-design.md`

## Global Constraints

- Never invent financial/market/consensus/analyst data; missing → exact string `Data unavailable from reliable sources.`
- Shortlist tickers must already exist in `companies.by_sector.pharma`.
- `#/analyst`, `#/valuation`, `#/portfolio` remain gated.
- Keep Stage 1 JSON files’ market fields untouched except when running the existing fetch/merge scripts.
- Run tests with `PYTHONPATH=src python3 -m pytest …` from repo root.
- Prefer `git add` of explicit paths; do not commit `data/raw/` or `dist/*.html` (gitignored).

## File structure

| File | Responsibility |
|------|----------------|
| `data/deep_dives/index.json` | Dropdown catalog: Pharma published, Banks coming_next |
| `data/deep_dives/pharma.json` | Pharma narrative + shortlist + pack sources |
| `src/equity_research/schemas.py` | Validate index/packs; load into `deep_dives` |
| `tests/test_deep_dives.py` | Schema + cross-ticker + load tests |
| `src/dashboard/app.js` | `renderDeepDives`, Sources subsection, ROUTES wire |
| `src/dashboard/styles.css` | Deep-dive layout (reuse panel/card patterns) |
| `src/dashboard/index.template.html` | Optional nav label tweak (remove hard “locked” implication) |
| `tests/test_build_dashboard.py` | Assert `deep_dives` embedded |
| `tests/test_dashboard_js_smoke.py` | Assert `renderDeepDives` exists; deep-dives not permanent gate |
| `README.md` | Stage 2 Pharma note + refresh reminder |

---

### Task 1: Deep-dive schema validation (TDD)

**Files:**
- Modify: `src/equity_research/schemas.py`
- Create: `tests/test_deep_dives.py`
- Test: `tests/test_deep_dives.py`

**Interfaces:**
- Consumes: existing `_require_keys`, `_SOURCE_ITEM_KEYS`
- Produces:
  - `validate_deep_dive_index(data: dict) -> None`
  - `validate_deep_dive_pack(pack: dict, companies_by_sector: dict) -> None`
  - `load_deep_dives(data_dir: Path, companies: dict) -> dict` returning `{"index": list, "packs": dict}`
  - `load_all_data` includes key `"deep_dives"`

- [ ] **Step 1: Write failing tests**

Create `tests/test_deep_dives.py`:

```python
from pathlib import Path

import pytest

from equity_research.schemas import (
    load_all_data,
    validate_deep_dive_index,
    validate_deep_dive_pack,
)

ROOT = Path(__file__).resolve().parents[1]

_MIN_PACK = {
    "sector_id": "pharma",
    "name": "Pharmaceuticals and Healthcare",
    "as_of": "2026-10-18",
    "stance_summary": "OW — defensive growth with company-specific regulatory risk.",
    "overview": ["Domestic demand and exports support growth."],
    "sub_themes": [{"id": "domestic", "title": "Domestic brands", "summary": "Franchise strength."}],
    "drivers": ["Specialty mix"],
    "risks": ["US FDA / pricing"],
    "expectation_gaps": {"positive": ["Hospital structural growth"], "negative": ["US pricing pressure"]},
    "shortlist": [
        {
            "ticker": "SUNPHARMA.NS",
            "name": "Sun Pharmaceutical Industries",
            "priority": 1,
            "role_in_sector": "Diversified specialty leader",
            "thesis": ["Specialty and chronic franchise."],
            "why_now": ["Relative defensive growth."],
            "key_risks": ["Concentration and regulatory inspection risk."],
            "classification": "Sector Leader",
            "open_questions": ["Data unavailable from reliable sources."],
        }
    ],
    "methodology_notes": ["No sell-side target prices verified for this pack."],
    "sources": [
        {
            "title": "Stage 1 sector thesis (internal)",
            "url_or_publisher": "data/sectors.json",
            "as_of": "2026-10-04",
            "notes": "Baseline stance and thesis carried into Stage 2.",
        }
    ],
}


def test_validate_index_ok():
    validate_deep_dive_index(
        {
            "entries": [
                {
                    "sector_id": "pharma",
                    "name": "Pharmaceuticals and Healthcare",
                    "status": "published",
                    "as_of": "2026-10-18",
                },
                {
                    "sector_id": "banks",
                    "name": "Banks",
                    "status": "coming_next",
                    "as_of": None,
                },
            ]
        }
    )


def test_validate_pack_rejects_unknown_ticker():
    companies = {"by_sector": {"pharma": [{"ticker": "OTHER.NS", "name": "X", "classification": "Y", "performance": {}}]}}
    with pytest.raises(ValueError, match="SUNPHARMA"):
        validate_deep_dive_pack(_MIN_PACK, companies["by_sector"])


def test_validate_pack_ok_against_repo_universe():
    companies = load_all_data(ROOT / "data")["companies"]
    # Until Task 2 adds files, this may fail on load_all_data deep_dives —
    # use companies only:
    from equity_research.schemas import validate_companies
    import json
    companies = json.loads((ROOT / "data" / "companies.json").read_text())
    validate_companies(companies)
    validate_deep_dive_pack(_MIN_PACK, companies["by_sector"])
```

Note: In Step 1, **do not** call full `load_all_data` for pack-ok until Task 2 lands files. Prefer reading `companies.json` only as above.

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src python3 -m pytest tests/test_deep_dives.py -v`  
Expected: FAIL with `ImportError` or `AttributeError` for missing validators.

- [ ] **Step 3: Implement validators (not yet wired into `load_all_data`)**

Append to `src/equity_research/schemas.py`:

```python
_DEEP_DIVE_INDEX_ENTRY_KEYS = ("sector_id", "name", "status", "as_of")
_DEEP_DIVE_PACK_KEYS = (
    "sector_id",
    "name",
    "as_of",
    "stance_summary",
    "overview",
    "sub_themes",
    "drivers",
    "risks",
    "expectation_gaps",
    "shortlist",
    "methodology_notes",
    "sources",
)
_DEEP_DIVE_SHORTLIST_KEYS = (
    "ticker",
    "name",
    "priority",
    "role_in_sector",
    "thesis",
    "why_now",
    "key_risks",
    "classification",
    "open_questions",
)
_DEEP_DIVE_SUBTHEME_KEYS = ("id", "title", "summary")
_PUBLISHED = "published"
_COMING_NEXT = "coming_next"


def validate_deep_dive_index(data: dict[str, Any]) -> None:
    _require_keys(data, ("entries",), "deep_dives.index")
    if not isinstance(data["entries"], list) or not data["entries"]:
        raise ValueError("deep_dives.index.entries must be a non-empty list")
    for i, entry in enumerate(data["entries"]):
        _require_keys(entry, _DEEP_DIVE_INDEX_ENTRY_KEYS, f"deep_dives.index.entries[{i}]")
        if entry["status"] not in (_PUBLISHED, _COMING_NEXT):
            raise ValueError(
                f"deep_dives.index.entries[{i}].status must be '{_PUBLISHED}' or '{_COMING_NEXT}'"
            )


def validate_deep_dive_pack(pack: dict[str, Any], companies_by_sector: dict[str, Any]) -> None:
    _require_keys(pack, _DEEP_DIVE_PACK_KEYS, "deep_dive.pack")
    sector_id = pack["sector_id"]
    universe = companies_by_sector.get(sector_id)
    if not isinstance(universe, list):
        raise ValueError(f"no companies.by_sector[{sector_id!r}] for deep-dive pack")
    tickers = {row.get("ticker") for row in universe}
    shortlist = pack["shortlist"]
    if not isinstance(shortlist, list) or not (4 <= len(shortlist) <= 6):
        raise ValueError("deep_dive.pack.shortlist must contain 4–6 names")
    # Allow Task 1 unit pack with 1 name only in tests by using a separate
    # internal helper OR relax to >=1 in validate and enforce 4–6 only in
    # load_deep_dives for published repo packs.
```

**Lock this decision in implementation:** `validate_deep_dive_pack` requires **1–6** shortlist items; `load_deep_dives` additionally requires **4–6** for any `published` pack loaded from disk. Update `_MIN_PACK` test accordingly (1 item OK for unit validate; repo pack must be 4–6).

Replace the shortlist length check with:

```python
    if not isinstance(shortlist, list) or not (1 <= len(shortlist) <= 6):
        raise ValueError("deep_dive.pack.shortlist must contain 1–6 names")
    for j, item in enumerate(shortlist):
        _require_keys(item, _DEEP_DIVE_SHORTLIST_KEYS, f"deep_dive.pack.shortlist[{j}]")
        if item["ticker"] not in tickers:
            raise ValueError(
                f"deep_dive.pack.shortlist[{j}] ticker {item['ticker']} "
                f"not in companies.by_sector[{sector_id}]"
            )
    gaps = pack["expectation_gaps"]
    _require_keys(gaps, ("positive", "negative"), "deep_dive.pack.expectation_gaps")
    for i, theme in enumerate(pack["sub_themes"]):
        _require_keys(theme, _DEEP_DIVE_SUBTHEME_KEYS, f"deep_dive.pack.sub_themes[{i}]")
    for i, src in enumerate(pack["sources"]):
        _require_keys(src, _SOURCE_ITEM_KEYS, f"deep_dive.pack.sources[{i}]")
```

- [ ] **Step 4: Run unit validate tests**

Run: `PYTHONPATH=src python3 -m pytest tests/test_deep_dives.py::test_validate_index_ok tests/test_deep_dives.py::test_validate_pack_rejects_unknown_ticker tests/test_deep_dives.py::test_validate_pack_ok_against_repo_universe -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/equity_research/schemas.py tests/test_deep_dives.py
git commit -m "$(cat <<'EOF'
Add deep-dive pack schema validators for Stage 2.

EOF
)"
```

---

### Task 2: Load `deep_dives` from disk + index/pharma files

**Files:**
- Create: `data/deep_dives/index.json`
- Create: `data/deep_dives/pharma.json` (full authored pack — see content below)
- Modify: `src/equity_research/schemas.py` (`load_deep_dives`, `load_all_data`)
- Modify: `tests/test_deep_dives.py`
- Modify: `tests/test_schemas.py` (assert `deep_dives` in `load_all_data`)

**Interfaces:**
- Consumes: `validate_deep_dive_index`, `validate_deep_dive_pack`
- Produces: `load_all_data(...)["deep_dives"] == {"index": [...], "packs": {"pharma": {...}}}`

- [ ] **Step 1: Write failing load test**

Add to `tests/test_deep_dives.py`:

```python
def test_load_all_data_includes_pharma_pack():
    data = load_all_data(ROOT / "data")
    assert "deep_dives" in data
    assert data["deep_dives"]["packs"]["pharma"]["sector_id"] == "pharma"
    assert 4 <= len(data["deep_dives"]["packs"]["pharma"]["shortlist"]) <= 6
    banks = next(e for e in data["deep_dives"]["index"] if e["sector_id"] == "banks")
    assert banks["status"] == "coming_next"
```

Update `tests/test_schemas.py` `test_load_all_data_from_repo` to include `"deep_dives"` in the expected set.

- [ ] **Step 2: Run test — expect FAIL** (missing files / key)

Run: `PYTHONPATH=src python3 -m pytest tests/test_deep_dives.py::test_load_all_data_includes_pharma_pack -v`  
Expected: FAIL

- [ ] **Step 3: Write `data/deep_dives/index.json`**

```json
{
  "entries": [
    {
      "sector_id": "pharma",
      "name": "Pharmaceuticals and Healthcare",
      "status": "published",
      "as_of": "2026-10-18"
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

- [ ] **Step 4: Write `data/deep_dives/pharma.json`**

Use this pack (honest gaps; no invented multiples). Shortlist: SUNPHARMA, DRREDDY, CIPLA, APOLLOHOSP, TORNTPHARM.

```json
{
  "sector_id": "pharma",
  "name": "Pharmaceuticals and Healthcare",
  "as_of": "2026-10-18",
  "stance_summary": "Maintain Stage 1 OW: diversified healthcare demand and exporter characteristics support defensive growth; prefer specialty, domestic brand, and hospital execution over undifferentiated US generics exposure.",
  "overview": [
    "India healthcare combines structural domestic demand (chronic therapies, hospitals) with export earnings that diversify currency and cycle exposure.",
    "Company outcomes remain highly idiosyncratic: US FDA inspection outcomes, product concentration, and pricing can dominate sector beta.",
    "Stage 1 scorecard rated the sector OW (attractiveness ~71); this pack does not change stance—it sharpens implementation via a five-name shortlist.",
    "Capital allocation within the sector should favour franchise quality and visible domestic/hospital growth over pure commodity generics."
  ],
  "sub_themes": [
    {
      "id": "specialty_chronic",
      "title": "Specialty and chronic franchises",
      "summary": "Leaders with specialty pipelines and chronic brand strength tend to show more durable mix than pure acute/generics books."
    },
    {
      "id": "hospitals",
      "title": "Hospital delivery",
      "summary": "Organised hospital platforms monetise rising procedure volumes and payor mix; execution and capital intensity differ by chain."
    },
    {
      "id": "exports_api",
      "title": "Exports and complex manufacturing",
      "summary": "US/EU exposure and complex chemistry can add growth but raise regulatory and pricing risk—stock selection matters more than sector beta."
    }
  ],
  "drivers": [
    "Domestic chronic and specialty volume growth",
    "Hospital capacity and occupancy recovery / expansion",
    "INR earnings diversification from export-oriented businesses where compliance is strong"
  ],
  "risks": [
    "US FDA warning letters, import alerts, and remediation costs",
    "US generics price erosion and channel inventory swings",
    "Input-cost and API supply shocks for manufacturing-heavy names",
    "Hospital regulatory, land, and doctor-engagement execution risk"
  ],
  "expectation_gaps": {
    "positive": [
      "Street may under-appreciate durability of domestic brand franchises versus headline US generics noise",
      "Hospital structural growth can compound longer than cyclical pharma sentiment implies"
    ],
    "negative": [
      "Consensus may be slow to price inspection or product-concentration setbacks",
      "Undifferentiated generics exposure can look cheap on earnings that are not high quality"
    ]
  },
  "shortlist": [
    {
      "ticker": "SUNPHARMA.NS",
      "name": "Sun Pharmaceutical Industries",
      "priority": 1,
      "role_in_sector": "Diversified specialty / chronic leader",
      "thesis": [
        "Broad specialty and chronic franchise with scale advantages versus mid-tier peers.",
        "Diversified geography reduces single-market binary outcomes relative to pure US generics names."
      ],
      "why_now": [
        "Fits Stage 1 preference for specialty/domestic-quality over undifferentiated exposure.",
        "OW sector stance is best expressed through leaders with multiple earnings engines."
      ],
      "key_risks": [
        "Any major US regulatory setback can re-rate the whole complex.",
        "Specialty concentration in key products remains a company-specific watchpoint."
      ],
      "classification": "Sector Leader",
      "open_questions": [
        "Data unavailable from reliable sources."
      ]
    },
    {
      "ticker": "DRREDDY.NS",
      "name": "Dr. Reddy's Laboratories",
      "priority": 2,
      "role_in_sector": "High-quality compounder with US/complex generics capability",
      "thesis": [
        "Quality compounder profile with mix of complex generics and branded businesses.",
        "Balance-sheet and execution culture historically support navigating regulatory cycles better than weaker peers."
      ],
      "why_now": [
        "Useful core holding when expressing Pharma OW without relying only on hospital names."
      ],
      "key_risks": [
        "US pricing and approval timing can swing near-term earnings.",
        "Pipeline concentration risk on key launches."
      ],
      "classification": "High-Quality Compounder",
      "open_questions": [
        "Data unavailable from reliable sources."
      ]
    },
    {
      "ticker": "CIPLA.NS",
      "name": "Cipla",
      "priority": 3,
      "role_in_sector": "Domestic brand strength with respiratory franchise",
      "thesis": [
        "Strong domestic branded franchise, notably respiratory, aligns with defensive India demand.",
        "Mix improvement narrative is more domestic-led than pure exporter beta."
      ],
      "why_now": [
        "Domestic brand quality matches the Stage 1 sector thesis preference."
      ],
      "key_risks": [
        "South Africa / US pockets still matter for consolidated growth.",
        "Competitive intensity in key domestic therapies."
      ],
      "classification": "High-Quality Compounder",
      "open_questions": [
        "Data unavailable from reliable sources."
      ]
    },
    {
      "ticker": "APOLLOHOSP.NS",
      "name": "Apollo Hospitals Enterprise",
      "priority": 4,
      "role_in_sector": "Hospital platform sector leader",
      "thesis": [
        "Organised hospital delivery captures structural procedure and diagnostics demand.",
        "Pharmacy and digital adjacencies diversify the hospital earnings story when executed well."
      ],
      "why_now": [
        "Hospital theme is under-served if Pharma OW is implemented only via drug manufacturers."
      ],
      "key_risks": [
        "Capital intensity and occupancy/ARPOB execution risk.",
        "Regulatory and competitive intensity in metro markets."
      ],
      "classification": "Sector Leader",
      "open_questions": [
        "Data unavailable from reliable sources."
      ]
    },
    {
      "ticker": "TORNTPHARM.NS",
      "name": "Torrent Pharmaceuticals",
      "priority": 5,
      "role_in_sector": "Domestic-focused compounder",
      "thesis": [
        "Domestic-heavy branded business fits the preference for India franchise quality.",
        "More focused profile than the largest diversified majors—useful satellite to core holdings."
      ],
      "why_now": [
        "Complements leaders with a cleaner domestic compounder expression."
      ],
      "key_risks": [
        "Brazil / other international pockets can add volatility.",
        "Scale disadvantage versus the largest Indian majors on specialty BD."
      ],
      "classification": "High-Quality Compounder",
      "open_questions": [
        "Data unavailable from reliable sources."
      ]
    }
  ],
  "methodology_notes": [
    "No sell-side EPS, target prices, or PE multiples were verified for this pack; numerical valuation fields are omitted by design.",
    "Shortlist is a research preference ranking within the existing Stage 1 Pharma universe—not a portfolio weight recommendation.",
    "Price and return figures must be read from companies.by_sector.pharma at render time, not copied into this pack."
  ],
  "sources": [
    {
      "title": "Stage 1 Pharmaceuticals sector thesis and scorecard",
      "url_or_publisher": "data/sectors.json",
      "as_of": "2026-10-04",
      "notes": "Stance, factor scores, and thesis bullets used as baseline."
    },
    {
      "title": "Stage 1 Pharma company universe",
      "url_or_publisher": "data/companies.json",
      "as_of": "2026-10-04",
      "notes": "Classification labels and ticker list for shortlist eligibility."
    },
    {
      "title": "Yahoo Finance NSE prices",
      "url_or_publisher": "https://finance.yahoo.com/",
      "as_of": "2026-10-16",
      "notes": "Performance joined at dashboard build/render from refreshed company rows."
    }
  ]
}
```

- [ ] **Step 5: Implement `load_deep_dives` and wire `load_all_data`**

```python
def load_deep_dives(data_dir: Path, companies: dict[str, Any]) -> dict[str, Any]:
    index_path = data_dir / "deep_dives" / "index.json"
    if not index_path.is_file():
        raise ValueError("missing required data file: deep_dives/index.json")
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    validate_deep_dive_index(index_payload)
    packs: dict[str, Any] = {}
    by_sector = companies["by_sector"]
    for entry in index_payload["entries"]:
        if entry["status"] != _PUBLISHED:
            continue
        sector_id = entry["sector_id"]
        pack_path = data_dir / "deep_dives" / f"{sector_id}.json"
        if not pack_path.is_file():
            raise ValueError(f"missing published deep-dive pack: {pack_path.name}")
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        if pack.get("sector_id") != sector_id:
            raise ValueError(f"pack sector_id mismatch for {pack_path.name}")
        validate_deep_dive_pack(pack, by_sector)
        if not (4 <= len(pack["shortlist"]) <= 6):
            raise ValueError(
                f"published pack {sector_id} shortlist must contain 4–6 names"
            )
        packs[sector_id] = pack
    return {"index": index_payload["entries"], "packs": packs}


def load_all_data(data_dir: Path) -> dict[str, Any]:
    # ... existing REQUIRED_FILES loop ...
    loaded["deep_dives"] = load_deep_dives(data_dir, loaded["companies"])
    return loaded
```

- [ ] **Step 6: Run tests**

Run: `PYTHONPATH=src python3 -m pytest tests/test_deep_dives.py tests/test_schemas.py -v`  
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add data/deep_dives/index.json data/deep_dives/pharma.json \
  src/equity_research/schemas.py tests/test_deep_dives.py tests/test_schemas.py
git commit -m "$(cat <<'EOF'
Load Pharma deep-dive pack into research data.

EOF
)"
```

---

### Task 3: Deep Dives UI + Sources subsection

**Files:**
- Modify: `src/dashboard/app.js`
- Modify: `src/dashboard/styles.css`
- Modify: `src/dashboard/index.template.html` (nav: change Deep Dives badge from locked Stage 2 chip to live, keep Analyst/Valuation badges)
- Modify: `tests/test_dashboard_js_smoke.py`
- Modify: `tests/test_build_dashboard.py`

**Interfaces:**
- Consumes: `DATA.deep_dives.index`, `DATA.deep_dives.packs[sectorId]`, `DATA.companies.by_sector[sectorId]`
- Produces: `function renderDeepDives(selectedSectorId)` wired in `ROUTES["deep-dives"]`

- [ ] **Step 1: Extend smoke/build tests (fail first)**

In `tests/test_dashboard_js_smoke.py`, assert:

```python
assert "function renderDeepDives(" in javascript
assert 'ROUTES' in javascript
# deep-dives should not be a permanent one-liner gate:
assert 'renderDeepDives' in javascript
assert javascript.count('return renderGate("Sector Deep Dives"') == 0
```

In `tests/test_build_dashboard.py`, after build:

```python
assert '"deep_dives"' in text or "deep_dives" in text
assert "SUNPHARMA.NS" in text
```

- [ ] **Step 2: Run smoke test — expect FAIL**

Run: `PYTHONPATH=src python3 -m pytest tests/test_dashboard_js_smoke.py tests/test_build_dashboard.py -v`  
Expected: FAIL on `renderDeepDives`

- [ ] **Step 3: Implement `renderDeepDives` in `app.js`**

Replace deep-dives route:

```javascript
"deep-dives": function () { return renderDeepDives(); },
```

Add (place near other renderers; reuse `panel`, `list`, `pageHeader`, `escapeHtml`, `formatNumber`, `formatDate`, `bindSectorSelect`-style listener):

```javascript
function renderDeepDives(selectedSectorId) {
  const index = valueAt(DATA, "deep_dives.index", []);
  if (!index.length) {
    return pageHeader("Stage 2", "Sector Deep Dives", "No deep-dive index is available.") +
      emptyState("Deep-dive catalog is empty.");
  }
  const published = index.filter(function (e) { return e.status === "published"; });
  const defaultId = selectedSectorId || (published[0] && published[0].sector_id) || index[0].sector_id;
  const entry = index.find(function (e) { return e.sector_id === defaultId; }) || index[0];
  const options = index.map(function (e) {
    const label = e.status === "coming_next" ? e.name + " (coming next)" : e.name;
    return '<option value="' + escapeHtml(e.sector_id) + '"' +
      (e.sector_id === entry.sector_id ? " selected" : "") + ">" +
      escapeHtml(label) + "</option>";
  }).join("");
  const toolbar = '<div class="toolbar"><label>Sector<select id="deep-dive-select">' +
    options + "</select></label></div>";

  if (entry.status === "coming_next") {
    return pageHeader("Stage 2", "Sector Deep Dives",
      "Published packs unlock here; remaining sectors stay gated until authored.") +
      toolbar +
      '<section class="gate coming-next"><p class="eyebrow">Coming next</p><h2>' +
      escapeHtml(entry.name) +
      "</h2><p>Banks deep dive is scheduled after Pharmaceuticals and Healthcare ships.</p>" +
      '<a class="button-link" href="#/companies">View company universe</a></section>' +
      renderPageCutoff();
  }

  const pack = valueAt(DATA, "deep_dives.packs." + entry.sector_id, null);
  if (!pack) {
    return pageHeader("Stage 2", "Sector Deep Dives", "") + toolbar +
      emptyState("Published pack file is missing for " + entry.sector_id + ".");
  }

  const universe = valueAt(DATA, "companies.by_sector." + pack.sector_id, []);
  const byTicker = {};
  universe.forEach(function (row) { byTicker[row.ticker] = row; });

  const shortlist = (pack.shortlist || []).slice().sort(function (a, b) {
    return (a.priority || 99) - (b.priority || 99);
  });

  const cards = shortlist.map(function (item) {
    const market = byTicker[item.ticker] || {};
    const perf = market.performance || {};
    const strip = ["1M", "3M", "YTD", "1Y"].map(function (p) {
      return "<span><em>" + p + "</em><strong>" + formatNumber(perf[p], 2) + "%</strong></span>";
    }).join("");
    return '<article class="deep-dive-card">' +
      '<div class="card-head"><div><span class="ticker">' + escapeHtml(item.ticker) +
      "</span><h3>" + escapeHtml(item.name) + "</h3><p class=\"muted\">" +
      escapeHtml(item.role_in_sector) + " · " + escapeHtml(item.classification) +
      "</p></div><span class=\"priority\">#" + escapeHtml(item.priority) +
      "</span></div>" +
      "<h4>Thesis</h4>" + list(item.thesis) +
      "<h4>Why now</h4>" + list(item.why_now) +
      "<h4>Key risks</h4>" + list(item.key_risks) +
      "<h4>Open questions</h4>" + list(item.open_questions) +
      '<div class="perf-strip" aria-label="Selected returns">' + strip + "</div>" +
      '<p class="muted">Price as of ' + formatDate(market.price_date) +
      (market.price != null ? " · " + formatNumber(market.price, 2) : "") +
      "</p></article>";
  }).join("");

  const themes = (pack.sub_themes || []).map(function (t) {
    return "<article><h3>" + escapeHtml(t.title) + "</h3><p>" +
      escapeHtml(t.summary) + "</p></article>";
  }).join("");

  return pageHeader("Stage 2", pack.name + " deep dive",
      escapeHtml(pack.stance_summary)) +
    toolbar +
    panel("Overview", list(pack.overview)) +
    '<section class="subtheme-grid">' + themes + "</section>" +
    panel("Drivers", list(pack.drivers)) +
    panel("Risks", list(pack.risks)) +
    panel("Expectation gaps — positive", list(pack.expectation_gaps.positive)) +
    panel("Expectation gaps — negative", list(pack.expectation_gaps.negative)) +
    '<section class="panel"><h3>Shortlist</h3><div class="deep-dive-grid">' +
    cards + "</div></section>" +
    panel("Methodology", list(pack.methodology_notes)) +
    renderPageCutoff();
}

function bindDeepDiveSelect() {
  const select = document.getElementById("deep-dive-select");
  if (!select) return;
  select.addEventListener("change", function () {
    document.getElementById("page-root").innerHTML = renderDeepDives(select.value);
    bindDeepDiveSelect();
  });
}
```

Call `bindDeepDiveSelect()` from `renderRoute` after setting `page-root` innerHTML (same pattern as sector-select).

Update `renderSources` to append:

```javascript
const diveSources = [];
valueAt(DATA, "deep_dives.index", []).forEach(function (entry) {
  if (entry.status !== "published") return;
  const pack = valueAt(DATA, "deep_dives.packs." + entry.sector_id, null);
  (pack && pack.sources || []).forEach(function (source) {
    diveSources.push(Object.assign({ pack: pack.name }, source));
  });
});
// render diveSources in a second panel "Deep-dive sources" with an extra Pack column
```

- [ ] **Step 4: Add CSS**

Append to `styles.css`:

```css
.subtheme-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin: 16px 0 24px;
}
.subtheme-grid article {
  padding: 16px;
  background: var(--white);
  border: 1px solid var(--slate-200);
  border-top: 3px solid var(--navy-800);
}
.deep-dive-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}
.deep-dive-card {
  padding: 18px;
  background: var(--white);
  border: 1px solid var(--slate-200);
}
.deep-dive-card h4 { margin: 14px 0 6px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--slate-600); }
.deep-dive-card .priority { font-family: Georgia, serif; font-size: 22px; color: var(--navy-800); }
.perf-strip { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--slate-200); }
.perf-strip span { display: flex; flex-direction: column; gap: 2px; font-size: 12px; }
.perf-strip em { font-style: normal; color: var(--slate-600); }
.coming-next { text-align: center; }
.muted { color: var(--slate-600); font-size: 13px; }
```

- [ ] **Step 5: Template nav**

In `index.template.html`, change Deep Dives link from `Sector Deep Dives <span>2</span>` to `Sector Deep Dives` (live). Leave Analyst/Valuation/Portfolio badges.

- [ ] **Step 6: Wire `bindDeepDiveSelect` in `renderRoute`**

After existing select binders, call `bindDeepDiveSelect()`.

- [ ] **Step 7: Run tests + local build**

```bash
PYTHONPATH=src python3 -m pytest -v
PYTHONPATH=src python scripts/build_dashboard.py --out dist/index.html
```

Expected: all tests PASS; open `dist/index.html#/deep-dives` shows Pharma shortlist.

- [ ] **Step 8: Commit**

```bash
git add src/dashboard/app.js src/dashboard/styles.css src/dashboard/index.template.html \
  tests/test_dashboard_js_smoke.py tests/test_build_dashboard.py
git commit -m "$(cat <<'EOF'
Unlock Sector Deep Dives UI for Pharma shortlist.

EOF
)"
```

---

### Task 4: Docs, price-refresh commit, push

**Files:**
- Modify: `README.md`
- Stage refreshed market JSON + fetch default fix from the data refresh session:
  - `data/meta.json`, `data/companies.json`, `data/sectors.json`, `data/new_age.json`, `data/sources.json`
  - `scripts/fetch_market_data.py`

- [ ] **Step 1: README**

Add under Stage 1 scope:

```markdown
## Stage 2 (in progress)

- **Pharmaceuticals and Healthcare** deep dive + shortlist is live at `#/deep-dives`.
- **Banks** is next (`coming_next` in `data/deep_dives/index.json`).
- Analyst View, Valuation, and Full Portfolio remain gated.
```

- [ ] **Step 2: Full test + rebuild**

```bash
PYTHONPATH=src python3 -m pytest -v
PYTHONPATH=src python scripts/build_dashboard.py --out dist/index.html
```

Expected: PASS

- [ ] **Step 3: Commit refresh + README**

```bash
git add README.md data/meta.json data/companies.json data/sectors.json \
  data/new_age.json data/sources.json scripts/fetch_market_data.py
git commit -m "$(cat <<'EOF'
Refresh market prices to 2026-10-16 and document Stage 2 Pharma.

EOF
)"
```

- [ ] **Step 4: Push**

```bash
git push origin main
```

Expected: Netlify rebuild serves Deep Dives with Pharma content.

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| `data/deep_dives/pharma.json` + index | Task 2 |
| Schema + ticker cross-check | Task 1–2 |
| Embed in `RESEARCH_DATA` | Task 2 (via `load_all_data` / build) |
| Unlock `#/deep-dives` UI + shortlist join | Task 3 |
| Banks `coming_next` | Task 2 index + Task 3 UI |
| Sources “Deep-dive sources” | Task 3 |
| Analyst/Valuation stay gated | Task 3 (untouched routes) |
| Honesty / unavailable string | Task 2 pack content |
| Tests | Tasks 1–3 |
| Price refresh + push | Task 4 |

## Placeholder scan

No TBD/TODO left in steps; Pharma shortlist tickers and JSON are fully specified.

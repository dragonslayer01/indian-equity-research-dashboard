# Stage 2 Banks Deep Dive + Hybrid KPIs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish Banks on `#/deep-dives` with a five-name shortlist and hybrid KPI strips, pushing commits directly to `main`.

**Architecture:** Reuse Pharma deep-dive loader/UI. Extend shortlist validation with optional `kpis`. Add `data/deep_dives/banks.json`, flip Banks to `published` in `index.json`, render a KPI strip when present.

**Tech Stack:** Python 3 / pytest, vanilla JS/CSS, existing `build_dashboard.py` / Netlify pipeline.

**Spec:** `docs/superpowers/specs/2026-10-18-stage2-banks-deep-dive-design.md`

## Global Constraints

- Never invent financial/market/consensus/analyst data; missing → exact string `Data unavailable from reliable sources.`
- Shortlist tickers must exist in `companies.by_sector.banks`.
- KPI `qualitative` ∈ {`strong`,`adequate`,`watch`,`weak`}; `id` ∈ {`nim`,`asset_quality`,`liability_franchise`,`credit_cost`}.
- If KPI `value` is not null, it must be a number and both `as_of` and `source` are required.
- Pharma packs without `kpis` must keep passing validation.
- `#/analyst`, `#/valuation`, `#/portfolio` remain gated.
- Run tests with `PYTHONPATH=src python3 -m pytest …` from repo root.
- Prefer explicit `git add` paths; do not commit `data/raw/` or `dist/*.html`.
- **Push each successful task commit to `origin/main`** (user delivery rule).

## File structure

| File | Responsibility |
|------|----------------|
| `src/equity_research/schemas.py` | `validate_shortlist_kpis`; hook from `validate_deep_dive_pack` |
| `tests/test_deep_dives.py` | KPI unit tests + Banks load assertions |
| `data/deep_dives/banks.json` | Banks narrative + shortlist + kpis |
| `data/deep_dives/index.json` | Banks → published |
| `src/dashboard/app.js` | KPI strip in shortlist cards |
| `src/dashboard/styles.css` | `.kpi-strip` / badge styles |
| `tests/test_build_dashboard.py` | Assert Banks pack embed string |
| `README.md` | Banks live; Macro/New-Age next |

---

### Task 1: Optional shortlist KPI validation (TDD)

**Files:**
- Modify: `src/equity_research/schemas.py`
- Modify: `tests/test_deep_dives.py`

**Interfaces:**
- Consumes: `_require_keys`, existing shortlist loop in `validate_deep_dive_pack`
- Produces: `validate_shortlist_kpis(item: dict, label: str) -> None` called when `"kpis" in item`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_deep_dives.py`:

```python
from equity_research.schemas import validate_shortlist_kpis

_BASE_ITEM = {
    "ticker": "HDFCBANK.NS",
    "name": "HDFC Bank",
    "priority": 1,
    "role_in_sector": "Large private franchise",
    "thesis": ["x"],
    "why_now": ["y"],
    "key_risks": ["z"],
    "classification": "Sector Leader",
    "open_questions": ["Data unavailable from reliable sources."],
}


def test_kpis_qualitative_only_ok():
    item = dict(_BASE_ITEM)
    item["kpis"] = [
        {
            "id": "nim",
            "label": "NIM",
            "qualitative": "adequate",
            "value": None,
            "note": "Data unavailable from reliable sources.",
        }
    ]
    validate_shortlist_kpis(item, "shortlist[0]")


def test_kpis_numeric_requires_as_of_and_source():
    item = dict(_BASE_ITEM)
    item["kpis"] = [
        {
            "id": "nim",
            "label": "NIM",
            "qualitative": "strong",
            "value": 3.5,
            "unit": "pct",
        }
    ]
    with pytest.raises(ValueError, match="as_of"):
        validate_shortlist_kpis(item, "shortlist[0]")


def test_kpis_invalid_qualitative_fails():
    item = dict(_BASE_ITEM)
    item["kpis"] = [{"id": "nim", "label": "NIM", "qualitative": "great"}]
    with pytest.raises(ValueError, match="qualitative"):
        validate_shortlist_kpis(item, "shortlist[0]")


def test_kpis_duplicate_id_fails():
    item = dict(_BASE_ITEM)
    item["kpis"] = [
        {"id": "nim", "label": "NIM", "qualitative": "adequate"},
        {"id": "nim", "label": "NIM", "qualitative": "strong"},
    ]
    with pytest.raises(ValueError, match="duplicate"):
        validate_shortlist_kpis(item, "shortlist[0]")
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
PYTHONPATH=src python3 -m pytest tests/test_deep_dives.py::test_kpis_qualitative_only_ok tests/test_deep_dives.py::test_kpis_numeric_requires_as_of_and_source tests/test_deep_dives.py::test_kpis_invalid_qualitative_fails tests/test_deep_dives.py::test_kpis_duplicate_id_fails -v
```

Expected: `ImportError` or `AttributeError` for `validate_shortlist_kpis`.

- [ ] **Step 3: Implement validator**

In `schemas.py`:

```python
_KPI_QUALITATIVE = frozenset({"strong", "adequate", "watch", "weak"})
_KPI_IDS = frozenset({"nim", "asset_quality", "liability_franchise", "credit_cost"})
_KPI_REQUIRED = ("id", "label", "qualitative")


def validate_shortlist_kpis(item: dict[str, Any], label: str) -> None:
    if "kpis" not in item:
        return
    kpis = item["kpis"]
    if not isinstance(kpis, list):
        raise ValueError(f"{label}.kpis must be a list")
    seen: set[str] = set()
    for i, kpi in enumerate(kpis):
        kpi_label = f"{label}.kpis[{i}]"
        _require_keys(kpi, _KPI_REQUIRED, kpi_label)
        if kpi["id"] not in _KPI_IDS:
            raise ValueError(f"{kpi_label}.id must be one of {sorted(_KPI_IDS)}")
        if kpi["id"] in seen:
            raise ValueError(f"{kpi_label} duplicate kpi id {kpi['id']}")
        seen.add(kpi["id"])
        if kpi["qualitative"] not in _KPI_QUALITATIVE:
            raise ValueError(
                f"{kpi_label}.qualitative must be one of {sorted(_KPI_QUALITATIVE)}"
            )
        value = kpi.get("value", None)
        if value is not None:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"{kpi_label}.value must be a number or null")
            if not kpi.get("as_of"):
                raise ValueError(f"{kpi_label}.as_of required when value is set")
            if not kpi.get("source"):
                raise ValueError(f"{kpi_label}.source required when value is set")
```

Inside `validate_deep_dive_pack` shortlist loop, after ticker check:

```python
        validate_shortlist_kpis(item, f"deep_dive.pack.shortlist[{j}]")
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
PYTHONPATH=src python3 -m pytest tests/test_deep_dives.py -v
```

- [ ] **Step 5: Commit and push main**

```bash
git add src/equity_research/schemas.py tests/test_deep_dives.py
git commit -m "$(cat <<'EOF'
Add optional hybrid KPI validation for deep-dive shortlists.

EOF
)"
git push origin main
```

---

### Task 2: Banks pack JSON + index publish

**Files:**
- Create: `data/deep_dives/banks.json`
- Modify: `data/deep_dives/index.json`
- Modify: `tests/test_deep_dives.py`

**Interfaces:**
- Consumes: existing `load_deep_dives` / `validate_deep_dive_pack` (+ KPI validation)
- Produces: `load_all_data(...)["deep_dives"]["packs"]["banks"]`

- [ ] **Step 1: Failing load test**

```python
def test_load_all_data_includes_banks_pack():
    data = load_all_data(ROOT / "data")
    banks = data["deep_dives"]["packs"]["banks"]
    assert banks["sector_id"] == "banks"
    assert 4 <= len(banks["shortlist"]) <= 6
    assert any(item.get("kpis") for item in banks["shortlist"])
    entry = next(e for e in data["deep_dives"]["index"] if e["sector_id"] == "banks")
    assert entry["status"] == "published"
    assert entry["as_of"]
```

- [ ] **Step 2: Run — expect FAIL** (banks not published / missing file)

```bash
PYTHONPATH=src python3 -m pytest tests/test_deep_dives.py::test_load_all_data_includes_banks_pack -v
```

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
      "status": "published",
      "as_of": "2026-10-18"
    }
  ]
}
```

- [ ] **Step 4: Write `data/deep_dives/banks.json`**

Use this full pack (qualitative KPIs; numerics null + honesty notes — do not invent %).

```json
{
  "sector_id": "banks",
  "name": "Banks",
  "as_of": "2026-10-18",
  "stance_summary": "Maintain Stage 1 OW (~69.9): credit demand supported by domestic activity; prefer scaled franchises with funding and risk-management advantages over homogeneous lender beta.",
  "overview": [
    "Large diversified banks retain liability and distribution advantages that matter more when policy is neutral and deposit pricing is competitive.",
    "Asset quality and unsecured books are stock-specific; treat sector OW as a franchise-quality call, not a blanket financials long.",
    "PSU scale (notably SBI) can complement private leaders when liability franchise and capital are intact, but cyclical PSU beta is not the core expression.",
    "Stage 1 thesis stands: deposit pricing, asset quality and margin discipline dominate a simple rate-cut narrative."
  ],
  "sub_themes": [
    {
      "id": "large_private",
      "title": "Large private franchises",
      "summary": "HDFC Bank and ICICI Bank anchor private-sector quality via funding mix, distribution and risk systems."
    },
    {
      "id": "psu_scale",
      "title": "PSU liability scale",
      "summary": "SBI's deposit franchise and balance-sheet scale remain distinctive; execution and credit-mix quality still drive outcomes."
    },
    {
      "id": "deposit_margins",
      "title": "Deposit competition and margins",
      "summary": "Neutral policy raises the importance of CASA quality and pricing discipline versus wholesale-funded growth."
    },
    {
      "id": "asset_quality_watch",
      "title": "Asset quality and unsecured watchpoints",
      "summary": "Unsecured or concentrated stress can re-rate names quickly even when sector NPAs look benign in aggregate."
    }
  ],
  "drivers": [
    "Broad-based credit demand from domestic activity",
    "Franchise advantages in deposits and distribution for scaled leaders",
    "Improving mid-tier challengers where liability and underwriting are visibly strengthening"
  ],
  "risks": [
    "Deposit competition compressing NIMs",
    "Unsecured or SME stress lifting credit costs",
    "Governance or underwriting setbacks at individual banks",
    "Policy or liquidity surprises that reprice funding costs"
  ],
  "expectation_gaps": {
    "positive": [
      "Credit costs stay benign while growth remains broad-based",
      "Street may under-differentiate franchise quality within the sector"
    ],
    "negative": [
      "Deposit competition or unsecured stress weakens margins and asset quality faster than consensus models",
      "Homogeneous 'banks OW' ignores stock-specific liability and risk books"
    ]
  },
  "shortlist": [
    {
      "ticker": "HDFCBANK.NS",
      "name": "HDFC Bank",
      "priority": 1,
      "role_in_sector": "Large private franchise leader",
      "thesis": [
        "Core private-sector expression of scaled funding, distribution and risk architecture.",
        "Best used as the primary OW vehicle when deposit competition is elevated."
      ],
      "why_now": [
        "Stage 1 prefers scaled franchises over undifferentiated lender beta."
      ],
      "key_risks": [
        "Margin pressure from deposit repricing",
        "Integration and growth-mix execution remain watchpoints"
      ],
      "classification": "Sector Leader",
      "open_questions": ["Data unavailable from reliable sources."],
      "kpis": [
        {"id": "nim", "label": "NIM", "qualitative": "adequate", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "asset_quality", "label": "Asset quality", "qualitative": "strong", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "liability_franchise", "label": "Liability franchise", "qualitative": "strong", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "credit_cost", "label": "Credit cost", "qualitative": "adequate", "value": null, "note": "Data unavailable from reliable sources."}
      ]
    },
    {
      "ticker": "ICICIBANK.NS",
      "name": "ICICI Bank",
      "priority": 2,
      "role_in_sector": "Large private franchise / risk culture compounder",
      "thesis": [
        "Second core private holding with strong retail/SME franchise and improved risk culture versus prior cycles.",
        "Complements HDFC Bank without relying on PSU beta."
      ],
      "why_now": [
        "Useful co-leader when expressing Banks OW through private quality."
      ],
      "key_risks": [
        "Competitive intensity in retail unsecured",
        "Market-sensitive fee and treasury income swings"
      ],
      "classification": "Sector Leader",
      "open_questions": ["Data unavailable from reliable sources."],
      "kpis": [
        {"id": "nim", "label": "NIM", "qualitative": "adequate", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "asset_quality", "label": "Asset quality", "qualitative": "strong", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "liability_franchise", "label": "Liability franchise", "qualitative": "strong", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "credit_cost", "label": "Credit cost", "qualitative": "adequate", "value": null, "note": "Data unavailable from reliable sources."}
      ]
    },
    {
      "ticker": "SBIN.NS",
      "name": "State Bank of India",
      "priority": 3,
      "role_in_sector": "PSU liability-scale franchise",
      "thesis": [
        "Distinctive deposit franchise and balance-sheet scale among Indian banks.",
        "Complements private leaders when capital and credit mix remain constructive."
      ],
      "why_now": [
        "Provides PSU scale exposure without making cyclical mid-tier PSUs the core OW expression."
      ],
      "key_risks": [
        "Policy and credit-mix interventions",
        "Operating leverage and cost ratios versus private peers"
      ],
      "classification": "Sector Leader",
      "open_questions": ["Data unavailable from reliable sources."],
      "kpis": [
        {"id": "nim", "label": "NIM", "qualitative": "adequate", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "asset_quality", "label": "Asset quality", "qualitative": "adequate", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "liability_franchise", "label": "Liability franchise", "qualitative": "strong", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "credit_cost", "label": "Credit cost", "qualitative": "watch", "value": null, "note": "Data unavailable from reliable sources."}
      ]
    },
    {
      "ticker": "KOTAKBANK.NS",
      "name": "Kotak Mahindra Bank",
      "priority": 4,
      "role_in_sector": "High-quality compounder / conservative franchise",
      "thesis": [
        "Quality compounder profile with historically conservative underwriting culture.",
        "Useful satellite to the two large private leaders."
      ],
      "why_now": [
        "Fits preference for franchise quality when deposit competition is elevated."
      ],
      "key_risks": [
        "Growth versus peer share-of-wallet",
        "Leadership and strategy continuity perceptions"
      ],
      "classification": "High-Quality Compounder",
      "open_questions": ["Data unavailable from reliable sources."],
      "kpis": [
        {"id": "nim", "label": "NIM", "qualitative": "strong", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "asset_quality", "label": "Asset quality", "qualitative": "strong", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "liability_franchise", "label": "Liability franchise", "qualitative": "adequate", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "credit_cost", "label": "Credit cost", "qualitative": "strong", "value": null, "note": "Data unavailable from reliable sources."}
      ]
    },
    {
      "ticker": "AXISBANK.NS",
      "name": "Axis Bank",
      "priority": 5,
      "role_in_sector": "Growth challenger among large privates",
      "thesis": [
        "Large private challenger with improving franchise trajectory versus prior cycles.",
        "Offers incremental upside versus leaders if liability and credit outcomes continue to stabilize."
      ],
      "why_now": [
        "Diversifies the shortlist beyond the top-two private names without moving into high-risk mid-tiers."
      ],
      "key_risks": [
        "Still more sensitive to credit and liability setbacks than the top franchises",
        "Competitive intensity in retail and corporate books"
      ],
      "classification": "Growth Challenger",
      "open_questions": ["Data unavailable from reliable sources."],
      "kpis": [
        {"id": "nim", "label": "NIM", "qualitative": "adequate", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "asset_quality", "label": "Asset quality", "qualitative": "watch", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "liability_franchise", "label": "Liability franchise", "qualitative": "adequate", "value": null, "note": "Data unavailable from reliable sources."},
        {"id": "credit_cost", "label": "Credit cost", "qualitative": "watch", "value": null, "note": "Data unavailable from reliable sources."}
      ]
    }
  ],
  "methodology_notes": [
    "KPI values are intentionally null in this pack; qualitative badges are research judgment, not audited financial metrics.",
    "No NIM, GNPA or credit-cost percentages were verified from filings for this release — use Data unavailable from reliable sources. until cited.",
    "Shortlist is a preference ranking within the Stage 1 Banks universe, not portfolio weights.",
    "Returns and prices are joined from companies.by_sector.banks at render time."
  ],
  "sources": [
    {
      "title": "Stage 1 Banks sector thesis and scorecard",
      "url_or_publisher": "data/sectors.json",
      "as_of": "2026-10-04",
      "notes": "Stance, thesis and expectation gaps used as baseline."
    },
    {
      "title": "Stage 1 Banks company universe",
      "url_or_publisher": "data/companies.json",
      "as_of": "2026-10-04",
      "notes": "Classification labels and ticker eligibility for shortlist."
    },
    {
      "title": "Yahoo Finance NSE prices",
      "url_or_publisher": "https://finance.yahoo.com/",
      "as_of": "2026-10-16",
      "notes": "Performance joined at dashboard render from company rows."
    }
  ]
}
```

- [ ] **Step 5: Run tests**

```bash
PYTHONPATH=src python3 -m pytest tests/test_deep_dives.py tests/test_schemas.py -v
```

Expected: PASS (including Pharma still loads).

- [ ] **Step 6: Commit and push main**

```bash
git add data/deep_dives/banks.json data/deep_dives/index.json tests/test_deep_dives.py
git commit -m "$(cat <<'EOF'
Publish Banks deep-dive pack with hybrid KPI shortlist.

EOF
)"
git push origin main
```

---

### Task 3: KPI strip UI + build assertion + README

**Files:**
- Modify: `src/dashboard/app.js`
- Modify: `src/dashboard/styles.css`
- Modify: `tests/test_build_dashboard.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `item.kpis` on shortlist cards inside `renderDeepDives`
- Produces: visible KPI strip; build assert on Banks `stance_summary` fragment

- [ ] **Step 1: Failing build assert**

In `tests/test_build_dashboard.py`, after existing Pharma assert, add:

```python
assert "Maintain Stage 1 OW (~69.9)" in text
assert "Liability franchise" in text or "liability_franchise" in text
```

- [ ] **Step 2: Run build test — may FAIL on Banks string until rebuild uses new data (data already on disk after Task 2)**

```bash
PYTHONPATH=src python3 -m pytest tests/test_build_dashboard.py -v
```

If data is present, assert may already pass for stance string once build runs — if UI lacks KPI label text in HTML, `"Liability franchise"` comes from pack JSON embed either way. Prefer asserting `"Maintain Stage 1 OW (~69.9)"` for pack embed and separately ensure UI renders KPI labels via a smoke string check in app.js presence of `kpi-strip` class after Step 3.

Add to `tests/test_dashboard_js_smoke.py`:

```python
assert "kpi-strip" in javascript or "renderKpiStrip" in javascript
```

- [ ] **Step 3: Implement `renderKpiStrip` in `app.js`**

```javascript
function renderKpiStrip(kpis) {
  if (!kpis || !kpis.length) return "";
  const cells = kpis.map(function (kpi) {
    const badge = '<span class="kpi-badge kpi-' + escapeHtml(kpi.qualitative) + '">' +
      escapeHtml(kpi.qualitative) + "</span>";
    let detail;
    if (kpi.value != null && kpi.value !== "") {
      detail = "<strong>" + formatNumber(kpi.value, 2) +
        (kpi.unit === "pct" ? "%" : "") + "</strong>" +
        '<em class="muted">' + formatDate(kpi.as_of) + "</em>";
    } else {
      detail = '<span class="muted">' + escapeHtml(kpi.note || "Data unavailable from reliable sources.") + "</span>";
    }
    return '<div class="kpi-cell"><span class="kpi-label">' + escapeHtml(kpi.label) +
      "</span>" + badge + detail + "</div>";
  }).join("");
  return '<div class="kpi-strip" aria-label="Banking KPIs">' + cells + "</div>";
}
```

In shortlist card HTML, after open questions and before perf-strip:

```javascript
renderKpiStrip(item.kpis) +
```

- [ ] **Step 4: CSS**

```css
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--slate-200);
}
.kpi-cell { display: flex; flex-direction: column; gap: 4px; font-size: 12px; }
.kpi-label { color: var(--slate-600); text-transform: uppercase; letter-spacing: 0.04em; }
.kpi-badge {
  display: inline-block;
  width: fit-content;
  padding: 2px 8px;
  border: 1px solid var(--slate-200);
  text-transform: capitalize;
}
.kpi-strong { border-color: #2f6b4f; color: #2f6b4f; }
.kpi-adequate { border-color: var(--navy-800); color: var(--navy-800); }
.kpi-watch { border-color: #b28a2f; color: #8a6a20; }
.kpi-weak { border-color: #8b3a3a; color: #8b3a3a; }
```

- [ ] **Step 5: README**

Update Stage 2 section:

```markdown
## Stage 2 (in progress)

- **Pharmaceuticals and Healthcare** and **Banks** deep dives + shortlists are live at `#/deep-dives` (Banks includes hybrid KPI badges).
- **Next:** Macro deepen, then New-Age deepen.
- Analyst View, Valuation, and Full Portfolio remain gated.
```

- [ ] **Step 6: Full test + build**

```bash
PYTHONPATH=src python3 -m pytest -v
PYTHONPATH=src python scripts/build_dashboard.py --out dist/index.html
```

Expected: all PASS.

- [ ] **Step 7: Commit and push main**

```bash
git add src/dashboard/app.js src/dashboard/styles.css \
  tests/test_build_dashboard.py tests/test_dashboard_js_smoke.py README.md
git commit -m "$(cat <<'EOF'
Render Banks hybrid KPI strip on Deep Dives shortlist cards.

EOF
)"
git push origin main
```

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| Optional KPI schema + validation | Task 1 |
| `banks.json` + index published | Task 2 |
| Shortlist HDFC/ICICI/SBI/Kotak/Axis | Task 2 |
| Hybrid KPI UI strip | Task 3 |
| Pharma still valid without kpis | Task 1–2 |
| Sources via existing deep-dive subsection | automatic via pack.sources |
| Analyst/Valuation gated | untouched |
| Push to main | each task Step commit |

## Placeholder scan

No TBD. Banks pack JSON fully specified with null numerics + honesty notes.

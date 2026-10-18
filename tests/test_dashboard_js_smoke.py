from pathlib import Path


DASHBOARD_DIR = Path("src/dashboard")


def test_template_has_builder_markers_and_shell():
    html = (DASHBOARD_DIR / "index.template.html").read_text()

    assert "<style>/*__INLINE_CSS__*/</style>" in html
    assert "<script>/*__RESEARCH_DATA__*/</script>" in html
    assert "<script>/*__INLINE_JS__*/</script>" in html
    assert html.index("/*__RESEARCH_DATA__*/") < html.index("/*__INLINE_JS__*/")
    assert 'id="page-root"' in html
    assert 'id="analysis-date"' in html
    assert 'id="data-cutoff-date"' in html
    assert 'id="price-date"' in html


def test_template_exposes_all_hash_routes():
    html = (DASHBOARD_DIR / "index.template.html").read_text()
    routes = (
        "overview",
        "macro",
        "regime",
        "sector-rankings",
        "sector-performance",
        "companies",
        "new-age",
        "portfolio-stance",
        "sources",
        "deep-dives",
        "analyst",
        "valuation",
        "portfolio",
    )

    for route in routes:
        assert f'href="#/{route}"' in html


def test_javascript_defines_public_dashboard_functions():
    javascript = (DASHBOARD_DIR / "app.js").read_text()

    for function_name in (
        "renderRoute",
        "renderReturnsTable",
        "renderHeatmap",
        "filterEntities",
    ):
        assert f"function {function_name}(" in javascript

    assert "const ROUTES" in javascript
    assert '"sector-select"' in javascript
    assert "function renderDeepDives(" in javascript
    assert "ROUTES" in javascript
    assert "renderDeepDives" in javascript
    assert "function renderKpiStrip(" in javascript
    assert "kpi-strip" in javascript
    assert javascript.count('return renderGate("Sector Deep Dives"') == 0

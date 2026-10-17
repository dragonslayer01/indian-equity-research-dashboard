from pathlib import Path

from equity_research.build import build_dashboard


def test_build_embeds_data(tmp_path):
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "dash.html"
    build_dashboard(root / "data", root / "src" / "dashboard", out)
    text = out.read_text(encoding="utf-8")
    assert "window.RESEARCH_DATA" in text
    assert "Data unavailable from reliable sources." in text or "analysis_date" in text
    assert "cdn.jsdelivr" not in text

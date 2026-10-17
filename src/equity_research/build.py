from __future__ import annotations

import json
from pathlib import Path

from equity_research.schemas import load_all_data


def build_dashboard(data_dir: Path, src_dir: Path, out_path: Path) -> Path:
    data = load_all_data(data_dir)
    html = (src_dir / "index.template.html").read_text(encoding="utf-8")
    css = (src_dir / "styles.css").read_text(encoding="utf-8")
    js = (src_dir / "app.js").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False)
    html = html.replace("/*__INLINE_CSS__*/", css)
    html = html.replace("/*__INLINE_JS__*/", js)
    html = html.replace(
        "/*__RESEARCH_DATA__*/",
        f"window.RESEARCH_DATA = {payload};",
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path

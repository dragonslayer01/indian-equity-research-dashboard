(function () {
  "use strict";

  const DATA = window.RESEARCH_DATA || {};
  const PERIODS = ["1D", "1W", "1M", "3M", "6M", "YTD", "1Y", "3Y_cagr", "5Y_cagr"];
  const ROUTES = {
    overview: renderOverview,
    macro: renderMacro,
    regime: renderRegime,
    "sector-rankings": renderSectorRankings,
    "sector-performance": renderSectorPerformance,
    companies: renderCompanies,
    "new-age": renderNewAge,
    "portfolio-stance": renderPortfolioStance,
    sources: renderSources,
    "deep-dives": function () { return renderGate("Sector Deep Dives", "Stage 2"); },
    analyst: function () { return renderGate("Analyst & Street View", "Stage 2"); },
    valuation: function () { return renderGate("Valuation & Scenarios", "Stage 2"); },
    portfolio: function () { return renderGate("Full Portfolio", "Stage 4"); },
  };

  function valueAt(object, path, fallback) {
    return path.split(".").reduce(function (value, key) {
      return value && value[key] !== undefined ? value[key] : undefined;
    }, object) ?? fallback;
  }

  function escapeHtml(value) {
    return String(value ?? "—")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function titleCase(value) {
    return String(value).replace(/_/g, " ").replace(/\b\w/g, function (letter) {
      return letter.toUpperCase();
    });
  }

  function formatDate(value) {
    if (!value) return "Unavailable";
    const date = new Date(value + "T00:00:00");
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  }

  function formatNumber(value, digits) {
    if (typeof value !== "number" || !Number.isFinite(value)) return escapeHtml(value || "N/A");
    return value.toLocaleString("en-IN", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }

  function formatReturn(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return "N/A";
    return (value > 0 ? "+" : "") + value.toFixed(1) + "%";
  }

  function returnClass(value) {
    return typeof value === "number" ? (value > 0 ? "positive" : value < 0 ? "negative" : "flat") : "unavailable";
  }

  function stanceClass(stance) {
    return stance === "OW" ? "overweight" : stance === "UW" ? "underweight" : "neutral";
  }

  function pageHeader(kicker, title, description) {
    return '<div class="page-heading"><div><p class="eyebrow">' + escapeHtml(kicker) +
      "</p><h2>" + escapeHtml(title) + "</h2></div><p>" + escapeHtml(description) + "</p></div>";
  }

  function panel(title, body, className) {
    return '<section class="panel ' + (className || "") + '"><h3>' + escapeHtml(title) +
      "</h3>" + body + "</section>";
  }

  function emptyState(message) {
    return '<div class="empty-state"><strong>Data unavailable</strong><p>' + escapeHtml(message) + "</p></div>";
  }

  function list(items) {
    if (!items || !items.length) return emptyState("No supporting observations are available.");
    return '<ul class="evidence-list">' + items.map(function (item) {
      return "<li>" + escapeHtml(item) + "</li>";
    }).join("") + "</ul>";
  }

  function parseRoute() {
    const hash = (location.hash || "#/overview").replace(/^#\/?/, "");
    return hash.split("?")[0];
  }

  function bindMeta() {
    const meta = DATA.meta || {};
    ["analysis_date", "data_cutoff_date", "price_date"].forEach(function (key) {
      const node = document.querySelector('[data-bind="' + key + '"]');
      if (node) node.textContent = formatDate(meta[key]);
    });
    const note = document.getElementById("cutoff-note");
    if (note) note.textContent = "Data cutoff: " + formatDate(meta.data_cutoff_date) + ". Later events are excluded.";
  }

  function renderKpis() {
    const sectors = valueAt(DATA, "sectors.sectors", []);
    const newAge = valueAt(DATA, "new_age.companies", []);
    const regime = valueAt(DATA, "market_regime.label", "Unavailable");
    const overweights = sectors.filter(function (sector) { return sector.stance === "OW"; }).length;
    const items = [
      ["Market regime", regime],
      ["Sectors covered", sectors.length],
      ["Overweight sectors", overweights],
      ["New-age universe", newAge.length],
    ];
    document.getElementById("kpi-strip").innerHTML = items.map(function (item) {
      return '<div class="kpi"><span>' + escapeHtml(item[0]) + "</span><strong>" + escapeHtml(item[1]) + "</strong></div>";
    }).join("");
  }

  function renderRoute() {
    const requestedRoute = parseRoute();
    const route = ROUTES[requestedRoute] ? requestedRoute : "overview";
    const root = document.getElementById("page-root");
    root.innerHTML = ROUTES[route]();
    document.getElementById("page-title").textContent = route.split("-").map(titleCase).join(" ");
    document.querySelectorAll(".sidebar a").forEach(function (link) {
      const active = link.getAttribute("href") === "#/" + route;
      link.classList.toggle("active", active);
      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    document.body.classList.remove("nav-open");
    bindPageEvents(route);
    root.focus({ preventScroll: true });
  }

  function renderOverview() {
    const sectors = valueAt(DATA, "sectors.sectors", []);
    const topSectors = sectors.slice().sort(function (a, b) {
      return (b.attractiveness_score || 0) - (a.attractiveness_score || 0);
    }).slice(0, 5);
    const macro = valueAt(DATA, "macro.variables", []);
    const regime = DATA.market_regime || {};
    const sectorRows = topSectors.map(function (sector, index) {
      return '<tr><td class="rank">' + (index + 1) + "</td><td><strong>" + escapeHtml(sector.name) +
        '</strong></td><td><span class="stance ' + stanceClass(sector.stance) + '">' +
        escapeHtml(sector.stance) + "</span></td><td>" + formatNumber(sector.attractiveness_score, 1) + "</td></tr>";
    }).join("");
    const macroRows = macro.slice(0, 5).map(function (row) {
      return "<tr><td><strong>" + escapeHtml(row.name) + "</strong></td><td>" +
        escapeHtml(row.direction) + "</td><td>" + escapeHtml(row.current) + "</td></tr>";
    }).join("");

    return pageHeader("Investment dashboard", "India equity research at a glance",
      "A data-led view of the macro backdrop, market regime and relative sector opportunity.") +
      '<div class="dashboard-grid">' +
      panel("Regime assessment", '<div class="regime-callout"><span>Current classification</span><strong>' +
        escapeHtml(regime.label || "Unavailable") + "</strong><p>" + escapeHtml(regime.valuation || "") +
        "</p></div>", "span-2") +
      panel("Top sector rankings", '<div class="table-wrap"><table><thead><tr><th>#</th><th>Sector</th><th>Stance</th><th>Score</th></tr></thead><tbody>' +
        sectorRows + "</tbody></table></div>") +
      panel("Macro pulse", '<div class="table-wrap"><table><thead><tr><th>Variable</th><th>Direction</th><th>Latest reading</th></tr></thead><tbody>' +
        macroRows + "</tbody></table></div>") +
      "</div>" + renderPageCutoff();
  }

  function renderMacro() {
    const variables = valueAt(DATA, "macro.variables", []);
    const cards = variables.map(function (row) {
      return '<article class="macro-card"><div class="card-head"><h3>' + escapeHtml(row.name) +
        '</h3><span class="direction">' + escapeHtml(row.direction) + "</span></div>" +
        '<p class="current-reading">' + escapeHtml(row.current) + "</p>" +
        '<dl><dt>6–12 month view</dt><dd>' + escapeHtml(row.outlook_6_12m) +
        "</dd><dt>Earnings transmission</dt><dd>" + escapeHtml(row.earnings_impact) +
        "</dd><dt>Sector impact</dt><dd>" + escapeHtml(row.sector_market_impact) +
        '</dd></dl><p class="source-line">' + escapeHtml(row.source) + " · " + formatDate(row.as_of) + "</p></article>";
    }).join("");
    return pageHeader("Macro framework", "Macro scorecard",
      "Reported facts are separated from analytical interpretation and market transmission.") +
      '<div class="macro-grid">' + cards + "</div>" +
      panel("Transmission narrative", list(valueAt(DATA, "macro.transmission_narrative", []))) +
      renderPageCutoff();
  }

  function renderRegime() {
    const regime = DATA.market_regime || {};
    const gaps = regime.market_expectation_gaps || {};
    return pageHeader("Market framework", regime.label || "Market regime",
      "The classification combines observed macro conditions and market behavior without unsupported forward estimates.") +
      '<div class="regime-hero"><span>Current regime</span><strong>' + escapeHtml(regime.label || "Unavailable") + "</strong></div>" +
      '<div class="dashboard-grid">' +
      panel("Evidence", list(regime.evidence), "span-2") +
      panel("Earnings", "<p>" + escapeHtml(regime.earnings) + "</p>") +
      panel("Valuation", "<p>" + escapeHtml(regime.valuation) + "</p>") +
      panel("Flows", "<p>" + escapeHtml(regime.flows) + "</p>") +
      panel("Major risks", list(regime.major_risks)) +
      panel("Positive expectation gaps", list(gaps.positive)) +
      panel("Negative expectation gaps", list(gaps.negative)) +
      "</div>" + renderPageCutoff();
  }

  function renderSectorRankings() {
    const sectors = valueAt(DATA, "sectors.sectors", []).slice().sort(function (a, b) {
      return (b.attractiveness_score || 0) - (a.attractiveness_score || 0);
    });
    const factorNames = sectors.length ? Object.keys(sectors[0].factor_scores || {}) : [];
    const rows = sectors.map(function (sector, index) {
      const factorCells = factorNames.map(function (factor) {
        const score = sector.factor_scores[factor];
        return '<td><span class="score-cell score-' + Math.round(score || 0) + '">' + escapeHtml(score) + "</span></td>";
      }).join("");
      return "<tr><td class=\"rank\">" + (index + 1) + "</td><td><strong>" + escapeHtml(sector.name) +
        '</strong></td><td><span class="stance ' + stanceClass(sector.stance) + '">' + escapeHtml(sector.stance) +
        "</span></td><td><strong>" + formatNumber(sector.attractiveness_score, 1) + "</strong></td>" + factorCells + "</tr>";
    }).join("");
    const factors = factorNames.map(function (factor) { return "<th>" + escapeHtml(titleCase(factor)) + "</th>"; }).join("");
    return pageHeader("Relative allocation", "Sector rankings",
      "Weighted factor scores are analytical assessments on a 1–10 scale; overall attractiveness is shown on a 0–100 scale.") +
      '<section class="panel"><div class="table-wrap"><table class="ranking-table"><thead><tr><th>#</th><th>Sector</th><th>Stance</th><th>Score</th>' +
      factors + "</tr></thead><tbody>" + rows + "</tbody></table></div></section>" + renderPageCutoff();
  }

  function renderSectorPerformance() {
    const sectors = valueAt(DATA, "sectors.sectors", []).map(function (sector) {
      return {
        name: sector.name,
        ticker: sector.representative_index,
        price: sector.price,
        price_date: sector.price_date,
        performance: sector.performance,
      };
    });
    return pageHeader("Market monitor", "Sector performance",
      "Cross-period price returns for representative sector indices.") +
      panel("Returns heatmap", renderHeatmap(sectors, PERIODS), "heatmap-panel") +
      panel("Sortable return table", renderReturnsTable(sectors)) + renderPageCutoff();
  }

  function renderCompanies(selectedSector) {
    const sectors = valueAt(DATA, "sectors.sectors", []);
    if (!sectors.length) return pageHeader("Company monitor", "Companies", "No sector data is available.") + emptyState("Sector universe is empty.");
    const sectorId = selectedSector || sectors[0].id;
    const options = sectors.map(function (sector) {
      return '<option value="' + escapeHtml(sector.id) + '"' + (sector.id === sectorId ? " selected" : "") + ">" +
        escapeHtml(sector.name) + "</option>";
    }).join("");
    const companies = valueAt(DATA, "companies.by_sector." + sectorId, []);
    const benchmarks = valueAt(DATA, "companies.benchmarks", []);
    return pageHeader("Company monitor", "Company performance",
      "Select a sector, sort any return column, or filter by company name and ticker.") +
      '<div class="toolbar"><label>Sector<select id="sector-select">' + options +
      '</select></label><label class="search-label">Search<input id="entity-search" type="search" placeholder="Name or ticker…" autocomplete="off"></label></div>' +
      panel("Companies and benchmarks", renderReturnsTable(companies.concat(benchmarks))) + renderPageCutoff();
  }

  function renderNewAge(selectedSubSector) {
    const companies = valueAt(DATA, "new_age.companies", []);
    const subSectors = Array.from(new Set(companies.map(function (company) { return company.sub_sector; }).filter(Boolean))).sort();
    const active = selectedSubSector || "all";
    const filtered = active === "all" ? companies : companies.filter(function (company) { return company.sub_sector === active; });
    const options = ['<option value="all">All sub-sectors</option>'].concat(subSectors.map(function (subSector) {
      return '<option value="' + escapeHtml(subSector) + '"' + (subSector === active ? " selected" : "") + ">" +
        escapeHtml(subSector) + "</option>";
    })).join("");
    const stages = filtered.map(function (company) {
      return '<article class="company-card searchable-row" data-search="' +
        escapeHtml((company.name + " " + company.ticker + " " + company.sub_sector).toLowerCase()) + '"><div class="card-head"><div><span class="ticker">' +
        escapeHtml(company.ticker) + "</span><h3>" + escapeHtml(company.name) +
        '</h3></div><span class="cycle-stage">Stage ' + escapeHtml(company.profitability_cycle_stage) +
        "</span></div><p>" + escapeHtml(company.sub_sector) + "</p><p>" +
        escapeHtml(company.profitability_cycle_rationale) + "</p></article>";
    }).join("");
    return pageHeader("Emerging universe", "New-age companies",
      "Performance and qualitative profitability-cycle staging for recently listed and digital-first businesses.") +
      '<div class="toolbar"><label>Sub-sector<select id="sub-sector-select">' + options +
      '</select></label><label class="search-label">Search<input id="entity-search" type="search" placeholder="Name or ticker…" autocomplete="off"></label></div>' +
      panel("Returns", renderReturnsTable(filtered.concat(valueAt(DATA, "new_age.benchmarks", [])))) +
      '<div class="company-grid">' + stages + "</div>" + renderPageCutoff();
  }

  function renderPortfolioStance() {
    const groups = { OW: [], Neutral: [], UW: [] };
    valueAt(DATA, "sectors.sectors", []).forEach(function (sector) {
      (groups[sector.stance] || groups.Neutral).push(sector);
    });
    const columns = Object.keys(groups).map(function (stance) {
      return '<section class="stance-column"><div class="stance-heading"><span class="stance ' +
        stanceClass(stance) + '">' + escapeHtml(stance) + "</span><strong>" + groups[stance].length +
        " sectors</strong></div>" + groups[stance].map(function (sector) {
          return '<article><div><h3>' + escapeHtml(sector.name) + "</h3><strong>" +
            formatNumber(sector.attractiveness_score, 1) + '</strong></div><p>' +
            escapeHtml((sector.thesis || [])[0] || "No thesis available.") + "</p></article>";
        }).join("") + "</section>";
    }).join("");
    return pageHeader("Allocation framework", "Portfolio stance",
      "Sector positioning reflects relative attractiveness, not security-level recommendations or portfolio weights.") +
      '<div class="stance-board">' + columns + "</div>" +
      '<div class="disclosure"><strong>Stage gate</strong><p>Position sizing, security selection and full portfolio construction are reserved for Stage 4.</p></div>' +
      renderPageCutoff();
  }

  function renderSources() {
    const sources = valueAt(DATA, "sources.items", []);
    const rows = sources.map(function (source) {
      const isUrl = /^https?:\/\//.test(source.url_or_publisher || "");
      const publisher = isUrl ? '<a href="' + escapeHtml(source.url_or_publisher) +
        '" target="_blank" rel="noopener noreferrer">Open source ↗</a>' : escapeHtml(source.url_or_publisher);
      return "<tr><td><strong>" + escapeHtml(source.title) + "</strong></td><td>" + publisher +
        "</td><td>" + formatDate(source.as_of) + "</td><td>" + escapeHtml(source.notes) + "</td></tr>";
    }).join("");
    return pageHeader("Audit trail", "Sources and methodology",
      "Primary sources, market-data references and explicit methodology limitations.") +
      panel("Source register", '<div class="table-wrap"><table><thead><tr><th>Source</th><th>Link / publisher</th><th>As of</th><th>Usage note</th></tr></thead><tbody>' +
        rows + "</tbody></table></div>") +
      panel("Methodology notes", list(valueAt(DATA, "sources.methodology_notes", []))) + renderPageCutoff();
  }

  function renderGate(title, stage) {
    return '<section class="gate"><div class="gate-icon" aria-hidden="true">◇</div><p class="eyebrow">' +
      escapeHtml(stage) + '</p><h2>' + escapeHtml(title) + '</h2><p>This module is intentionally gated until its research inputs and validation requirements are complete.</p>' +
      '<div class="gate-status"><span>Current status</span><strong>Not yet published</strong></div><a class="button-link" href="#/overview">Return to overview</a></section>';
  }

  function renderReturnsTable(rows) {
    if (!rows || !rows.length) return emptyState("No return series are available for this selection.");
    const headerPeriods = PERIODS.map(function (period) {
      return '<th class="sortable numeric" data-sort="' + period + '" tabindex="0" role="button" aria-label="Sort by ' +
        escapeHtml(period.replace("_cagr", " CAGR")) + '">' + escapeHtml(period.replace("_cagr", " CAGR")) + "</th>";
    }).join("");
    const body = rows.map(function (row) {
      const performance = row.performance || {};
      const periodCells = PERIODS.map(function (period) {
        const value = performance[period];
        return '<td class="numeric return-value ' + returnClass(value) + '" data-value="' +
          (typeof value === "number" ? value : "") + '">' + formatReturn(value) + "</td>";
      }).join("");
      const search = ((row.name || "") + " " + (row.ticker || "")).toLowerCase();
      return '<tr class="searchable-row" data-search="' + escapeHtml(search) + '"><td><strong>' +
        escapeHtml(row.name || "Unnamed") + '</strong><small>' + escapeHtml(row.classification || "") +
        '</small></td><td class="ticker">' + escapeHtml(row.ticker || "—") +
        '</td><td class="numeric">₹' + formatNumber(row.price, 2) + "</td><td>" +
        escapeHtml(row.price_date || "N/A") + "</td>" + periodCells + "</tr>";
    }).join("");
    return '<div class="table-wrap"><table class="returns-table"><thead><tr><th class="sortable" data-sort="name" tabindex="0" role="button">Company / Index</th>' +
      '<th class="sortable" data-sort="ticker" tabindex="0" role="button">Ticker</th><th class="sortable numeric" data-sort="price" tabindex="0" role="button">Price</th>' +
      '<th class="sortable" data-sort="price_date" tabindex="0" role="button">Price Date</th>' + headerPeriods +
      "</tr></thead><tbody>" + body + "</tbody></table></div>";
  }

  function renderHeatmap(rows, periods) {
    if (!rows || !rows.length) return emptyState("No performance observations are available.");
    const headers = periods.map(function (period) { return "<span>" + escapeHtml(period.replace("_cagr", " CAGR")) + "</span>"; }).join("");
    const grid = rows.map(function (row) {
      const cells = periods.map(function (period) {
        const value = valueAt(row, "performance." + period, null);
        const intensity = typeof value === "number" ? Math.min(Math.abs(value) / 25, 1) : 0;
        const background = typeof value !== "number" ? "var(--heat-na)" :
          value >= 0 ? "rgba(22, 129, 94, " + (0.14 + intensity * 0.72) + ")" :
            "rgba(190, 55, 64, " + (0.14 + intensity * 0.72) + ")";
        return '<span class="heat-cell ' + returnClass(value) + '" style="background:' + background +
          '" title="' + escapeHtml(row.name + " · " + period + ": " + formatReturn(value)) + '">' +
          formatReturn(value) + "</span>";
      }).join("");
      return '<div class="heat-row"><strong>' + escapeHtml(row.name) + "</strong>" + cells + "</div>";
    }).join("");
    return '<div class="heatmap"><div class="heat-header"><span>Sector</span>' + headers + "</div>" + grid + "</div>";
  }

  function filterEntities(q) {
    const query = String(q || "").trim().toLowerCase();
    document.querySelectorAll(".searchable-row").forEach(function (row) {
      row.hidden = query !== "" && !String(row.dataset.search || "").includes(query);
    });
  }

  function sortTable(table, columnIndex, key) {
    const body = table.tBodies[0];
    if (!body) return;
    const header = table.tHead.rows[0].cells[columnIndex];
    const direction = header.dataset.direction === "asc" ? "desc" : "asc";
    table.querySelectorAll("th").forEach(function (cell) {
      cell.removeAttribute("data-direction");
      cell.removeAttribute("aria-sort");
    });
    header.dataset.direction = direction;
    header.setAttribute("aria-sort", direction === "asc" ? "ascending" : "descending");
    const rows = Array.from(body.rows);
    rows.sort(function (a, b) {
      let left;
      let right;
      if (PERIODS.includes(key)) {
        left = Number(a.cells[columnIndex].dataset.value);
        right = Number(b.cells[columnIndex].dataset.value);
        if (a.cells[columnIndex].dataset.value === "") left = -Infinity;
        if (b.cells[columnIndex].dataset.value === "") right = -Infinity;
      } else if (key === "price") {
        left = Number(a.cells[columnIndex].textContent.replace(/[₹,]/g, "")) || -Infinity;
        right = Number(b.cells[columnIndex].textContent.replace(/[₹,]/g, "")) || -Infinity;
      } else {
        left = a.cells[columnIndex].textContent.trim().toLowerCase();
        right = b.cells[columnIndex].textContent.trim().toLowerCase();
      }
      if (left < right) return direction === "asc" ? -1 : 1;
      if (left > right) return direction === "asc" ? 1 : -1;
      return 0;
    });
    rows.forEach(function (row) { body.appendChild(row); });
  }

  function bindPageEvents(route) {
    const sectorSelect = document.getElementById("sector-select");
    if (sectorSelect) {
      sectorSelect.addEventListener("change", function () {
        document.getElementById("page-root").innerHTML = renderCompanies(sectorSelect.value);
        bindPageEvents("companies");
      });
    }
    const subSectorSelect = document.getElementById("sub-sector-select");
    if (subSectorSelect) {
      subSectorSelect.addEventListener("change", function () {
        document.getElementById("page-root").innerHTML = renderNewAge(subSectorSelect.value);
        bindPageEvents("new-age");
      });
    }
    const search = document.getElementById("entity-search");
    if (search) search.addEventListener("input", function () { filterEntities(search.value); });
    document.querySelectorAll(".returns-table th.sortable").forEach(function (header, columnIndex) {
      const activate = function () { sortTable(header.closest("table"), columnIndex, header.dataset.sort); };
      header.addEventListener("click", activate);
      header.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          activate();
        }
      });
    });
  }

  function renderPageCutoff() {
    return '<p class="page-cutoff">Data cutoff: ' + escapeHtml(valueAt(DATA, "meta.data_cutoff_date", "Unavailable")) +
      ". Prices as of " + escapeHtml(valueAt(DATA, "meta.price_date", "Unavailable")) + ".</p>";
  }

  function initialize() {
    bindMeta();
    renderKpis();
    document.getElementById("menu-button").addEventListener("click", function (event) {
      const open = document.body.classList.toggle("nav-open");
      event.currentTarget.setAttribute("aria-expanded", String(open));
    });
    window.addEventListener("hashchange", renderRoute);
    if (!location.hash) location.replace("#/overview");
    else renderRoute();
  }

  window.renderRoute = renderRoute;
  window.renderReturnsTable = renderReturnsTable;
  window.renderHeatmap = renderHeatmap;
  window.filterEntities = filterEntities;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize);
  else initialize();
}());

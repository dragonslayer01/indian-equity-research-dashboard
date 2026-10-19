# Weekly automated price refresh (GitHub Actions)

**Date:** 2026-10-19  
**Status:** Approved (implementing)  
**Depends on:** GitHub Pages deploy workflow

## Goal

Every week, refresh Yahoo prices/returns into `data/*.json` without manual local runs, then update the live Pages site.

## Decisions

| Item | Choice |
|------|--------|
| Trigger | Cron Saturdays 02:30 UTC (~08:00 IST) + `workflow_dispatch` |
| What runs | `scripts/fetch_market_data.py` only (no research edits) |
| Commit | Push updated JSON under `data/` (not `data/raw/`, still gitignored) |
| Site update | Existing Pages workflow on the commit to `main` |
| Authored research | Untouched (`analysis_date`, deep dives, macro narrative stay as last authored) |
| Partial Yahoo failures | Same as local: log failures, still commit successful symbols |

## Flow

```
schedule / manual
  → checkout main
  → pip install + fetch_market_data.py
  → if data JSON changed: commit + push
  → Deploy to GitHub Pages (existing on push)
```

## Out of scope

- Auto-rewriting sector theses / deep dives / macro judgment
- Opening a PR instead of committing to `main` (can revisit if commits are noisy)

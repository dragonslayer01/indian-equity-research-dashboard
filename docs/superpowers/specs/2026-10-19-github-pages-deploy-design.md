# GitHub Pages deploy (replace Netlify for free hosting)

**Date:** 2026-10-19  
**Status:** Approved (implementing)  
**Live URL:** https://dragonslayer01.github.io/indian-equity-research-dashboard/

## Goal

Host the built dashboard on GitHub Pages (free for this public repo) instead of Netlify, which burns credits.

## Decisions

| Item | Choice |
|------|--------|
| Host | GitHub Pages project site |
| Build | GitHub Actions on push to `main` + manual `workflow_dispatch` |
| Artifact | `dist/` from existing `scripts/build_dashboard.py` (no fetch in CI) |
| Netlify | Leave `netlify.toml` for now; stop using Netlify UI / disconnect site after Pages is verified |
| Custom domain | Out of scope |

## How it works

1. Push to `main` (or Run workflow).
2. Action installs Python deps, runs the same build as Netlify.
3. Uploads `dist/` as a Pages artifact and deploys.
4. Site serves `index.html` at the project URL above; hash routes unchanged.

## Out of scope

- Fetching Yahoo prices in CI (local/manual refresh still updates `data/`, then push rebuilds HTML)
- Custom domain
- Deleting Netlify account/site automatically

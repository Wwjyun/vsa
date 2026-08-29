# Changelog

## Unreleased

- Gave every defect type a stable color derived from its name, so the same defect keeps
  one color across lots, stages, and sessions.
- Replaced the per-page inline Plotly bundle with one offline `plotly.min.js` written per
  window and referenced relatively, shrinking each generated page.
- Wired the Map width, Map height, and Point size fields into the loss map and custom map
  instead of validating values that were never used, and rejected out-of-range sizes in the
  figure builders.
- Replaced fixed window geometry and pinned widget pixel sizes with minimum sizes and size
  policies so the windows scale with display size and DPI.
- Fixed the PyInstaller spec, which relied on `collect_*` hooks that import the package at
  build time and therefore shipped a bundle without `vsa.resources` when the package was not
  installed.

## 0.2.0 - 2026-08-29

- Reorganized the application as an installable `src/vsa` package with one entry point.
- Added validated package resources, data models, safe paths, and CSV/image/file services.
- Added deterministic synthetic demo data, CI, GUI smoke tests, and edge-case coverage.
- Stopped background servers and temporary-file leaks, and fixed ROI/loss-map/export defects.
- Added bounded-memory image composition, background Qt workers, diagnostics, and a PyInstaller build.

## 0.1.0

- Original legacy desktop application baseline.

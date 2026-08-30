# Changelog

## Unreleased

## 0.4.1 - 2026-08-30

- Renamed the `RDL break` defect type in `resources/rule.json` to `trace break`, the last
  process term carried over from the internal tool. Classification behavior is unchanged;
  a data root using the old label must rename it in its CSVs.

## 0.4.0 - 2026-08-30

- Renamed the process stages to `STAGE1`-`STAGE8` for both products, replacing the stage
  codes carried over from the internal tool. The six adjacent-stage comparisons stay
  `LOSS1`-`LOSS6`, and `LOSS1` now compares `STAGE1` with `STAGE2`.
- Raised the data-format contract to 2.0: stage identity changed, so a 1.0 data root is read
  only after its stage folders are renamed. The directory layout and CSV columns are unchanged.
- Made **Search** open the first stage of `STAGE_SEQUENCE` instead of a hard-coded stage name.

## 0.3.0 - 2026-08-30

- Redesigned the interface: one stylesheet and token set in `vsa/ui/theme.py`, reusable
  widgets in `vsa/ui/widgets.py`, and no colors hard-coded in the windows.
- Rebuilt the main window around a process-pipeline stage rail, a zoomable preview pane
  with Fit / -/+ controls, and a side panel that groups Inspect, Export, and session state.
- Gave the loss map a summary panel (loss rate, lost and kept counts) fed by the merged
  frame the plot controller now keeps, and a PKG NO readout wired to the plot selection.
- Gave the custom map a clickable defect-type legend with counts and a persistent red-point
  ratio, replacing the readout that only existed inside the generated page.
- Replaced the diagnostics `QMessageBox` with a panel that lists each value and can copy the
  summary to the clipboard.
- Showed map paths relative to `VSA_DATA_ROOT`, so the preview never exposes machine paths.

- Restored `main.py` at the repository root as a launcher for `python main.py`, which the
  package move had removed.
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

# VSA — Visual Stage Analysis

[![CI](https://github.com/Wwjyun/vsa/actions/workflows/ci.yml/badge.svg)](https://github.com/Wwjyun/vsa/actions/workflows/ci.yml)

VSA is a Windows desktop application for inspecting manufacturing defect maps across process stages. It combines a PySide6 operator interface with pandas-based CSV processing, Plotly/Dash visualizations, ROI image lookup, loss-map comparison, and image export tools.

This repository is a modernized portfolio version of an internal legacy project. It contains no production images, CSV records, credentials, or customer identifiers.

## Highlights

- Browse map images by product, Lot ID, Component ID, and process stage.
- Inspect defect points interactively (**ROI**) and open their TIFF ROI images.
- Compare adjacent stages with operator-selected good/bad classifications (**Loss Map**).
- Export original images, single maps, stage and lot comparisons, and yield summaries.
- Keep production data outside the repository through `VSA_DATA_ROOT`.
- Run deterministic unit and GUI smoke tests without accessing production data.
- Report a non-sensitive environment summary from the UI (**Diagnostics**).

## Architecture

The application is an installable package under `src/vsa` with a single entry point
(`vsa.app:main`). Qt code orchestrates; the computational layer has no Qt dependency and is
tested without constructing a window.

| Area | Main files | Responsibility |
| --- | --- | --- |
| Entry point | `app.py`, `__main__.py` | Logging setup, `QApplication` lifecycle, `--smoke-test` |
| Qt interface | `views/main_window.py`, `views/loss_map_window.py`, `views/custom_map_window.py`, `views/diagnostics_dialog.py` | User input, dialogs, previews, and window lifecycle |
| Presentation layer | `ui/theme.py`, `ui/widgets.py` | Design tokens, the single stylesheet, and the reusable widgets the windows compose |
| Interactive plots | `views/roi_plot.py`, `views/loss_map_plot.py`, `views/custom_map_plot.py` | Plotly/Dash charts, WebChannel events, temporary HTML and server cleanup |
| Data logic | `services/data.py` | CSV schema validation, defect classification, loss-map merge |
| Image and file services | `services/images.py`, `services/files.py`, `services/system.py` | Bounded-memory grids, copy operations, OS integration |
| Plot assets | `services/colors.py`, `services/plotly_assets.py` | Stable defect colors and one shared offline Plotly bundle per window |
| Paths and configuration | `paths.py`, `config.py`, `models.py` | Data-root configuration, safe path construction, canonical stage names |
| Background work | `workers.py` | `QThreadPool` worker that keeps exports off the UI thread |

## Requirements

- Windows 10/11
- Python 3.13 (developed on 3.13.0; CI runs the 3.13 line on `windows-latest`)
- Access to a VSA data directory matching the structure below

## Setup

```powershell
py -3.13 -m venv env
.\env\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Configure the data location for the current PowerShell session:

```powershell
$env:VSA_DATA_ROOT = "D:\path\to\sample-or-production-data"
```

Optional: change log verbosity for the session.

```powershell
$env:VSA_LOG_LEVEL = "DEBUG"
```

`env/` is the Python virtual environment. `.env.example` only documents the supported environment variables; the application does not automatically load `.env` files.

### Quick portfolio demo

Generate a deterministic synthetic dataset and launch the app without production data:

```powershell
.\env\Scripts\python.exe -m scripts.create_demo_data
$env:VSA_DATA_ROOT = (Resolve-Path .\demo_data).Path
.\env\Scripts\python.exe -m vsa
```

Use these values in the UI:

- Product: `Product A`
- Lot ID: `DEMO-LOT`
- Component ID: `DEMO-CMP`

## Run

```powershell
.\env\Scripts\python.exe -m vsa
```

`main.py` in the repository root is an equivalent launcher, kept so an existing shortcut or
`python main.py` habit still works:

```powershell
.\env\Scripts\python.exe main.py
```

Typical workflow:

1. Select a product.
2. Enter a Lot ID and Component ID, then press **Search**.
3. Select a process stage button to preview its map.
4. Use **ROI** for interactive defect-point inspection. Double-click a point to send its
   number to the **PKG NO** field; **Search** then opens that ROI image.
5. Select a `LOSS1`–`LOSS6` stage before opening **Loss Map**.
6. **Map width**, **Map height**, and **Point size** are optional. They apply to **Loss Map**
   and **Customize Map**, and default to 1000 x 800 with point size 2 when left empty.

Verify that the application starts without opening a window (this is what CI runs against
the packaged build):

```powershell
.\env\Scripts\python.exe -m vsa --smoke-test
```

## Expected data layout

```text
VSA_DATA_ROOT/
└── <product>/
    ├── csv/<lot>/<stage>/<component>.csv
    ├── map/<lot>/<stage>/<component>.<image extension>
    ├── roi/<lot>/<stage>/<component>/<package-no>.tiff
    ├── org/<lot>/<stage>/<component>/...
    ├── bar/<lot>/<stage>/<stage>.png
    └── example/<stage>/ok.tiff
```

CSV files used by interactive plots require these columns:

| Column | Meaning |
| --- | --- |
| `No` | Package or ROI image identifier |
| `Row` | Map row coordinate |
| `Col` | Map column coordinate |
| `DefectType` | Defect classification label |

The full directory and CSV contract, including the compatibility policy, is documented in
[docs/DATA_FORMAT.md](docs/DATA_FORMAT.md).

## Quality checks

```powershell
.\env\Scripts
uff.exe check .
.\env\Scripts
uff.exe format --check .
.\env\Scripts\pytest.exe
.\env\Scripts\python.exe -m pip check
```

These are the same four checks CI runs, invoked the same way. Run `pytest` directly rather
than through `python -m pytest`: the two put different entries on `sys.path`, so a suite that
passes only under `python -m pytest` will fail in CI.

Tests use temporary synthetic data and must not point at production `VSA_DATA_ROOT`.

## Packaging

```powershell
.\env\Scripts\pyinstaller.exe vsa.spec --noconfirm --clean
```

The build produces a one-folder Windows bundle in `dist/VSA/`. Verify it the way a reviewer
would receive it:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\dist\VSA\VSA.exe --smoke-test
```

`vsa.spec` resolves sources and resources from the spec directory rather than through the
PyInstaller `collect_*` hooks, because those hooks import the package at build time and
collect nothing when it is not installed. To reproduce that condition, uninstall the editable
install (`pip uninstall vsa-portfolio`) before building.

## Security and data handling

- Production data is treated as read-only.
- User-provided path fields reject separators and traversal components.
- Local virtual environments, `.env` files, caches, generated HTML, and build artifacts are ignored by Git.
- Do not add real manufacturing data or identifiers to issues, screenshots, fixtures, or commits.

## Project history

- [Todo.md](Todo.md) — the improvement audit of the legacy version, with the acceptance
  condition and verification recorded for each item.
- [CHANGELOG.md](CHANGELOG.md) — released and unreleased changes.
- [LICENSE.md](LICENSE.md) — portfolio-use notice and data-handling terms.

# VSA — Visual Stage Analysis

VSA is a Windows desktop application for inspecting manufacturing defect maps across process stages. It combines a PySide6 operator interface with pandas-based CSV processing, Plotly/Dash visualizations, ROI image lookup, loss-map comparison, and image export tools.

This repository is a modernized portfolio version of an internal legacy project. It contains no production images, CSV records, credentials, or customer identifiers.

## Highlights

- Browse map images by product, Lot ID, Component ID, and process stage.
- Inspect defect points interactively and open their TIFF ROI images.
- Compare adjacent stages with configurable good/bad defect classifications.
- Export source images, maps, vertical stage comparisons, and yield summaries.
- Keep production data outside the repository through `VSA_DATA_ROOT`.
- Run deterministic unit and GUI smoke tests without accessing production data.

## Architecture

The application is an installable package under `src/vsa` with a single entry point
(`vsa.app:main`). Qt code orchestrates; the computational layer has no Qt dependency and is
tested without constructing a window.

| Area | Main files | Responsibility |
| --- | --- | --- |
| Entry point | `app.py`, `__main__.py` | Logging setup, `QApplication` lifecycle, `--smoke-test` |
| Qt interface | `views/main_window.py`, `views/loss_map_window.py`, `views/custom_map_window.py` | User input, dialogs, previews, and window lifecycle |
| Interactive plots | `views/roi_plot.py`, `views/loss_map_plot.py`, `views/custom_map_plot.py` | Plotly/Dash charts, WebChannel events, temporary HTML and server cleanup |
| Data logic | `services/data.py` | CSV schema validation, defect classification, loss-map merge |
| Image and file services | `services/images.py`, `services/files.py`, `services/system.py` | Bounded-memory grids, copy operations, OS integration |
| Plot assets | `services/colors.py`, `services/plotly_assets.py` | Stable defect colors and one shared offline Plotly bundle per window |
| Paths and configuration | `paths.py`, `config.py`, `models.py` | Data-root configuration, safe path construction, canonical stage names |
| Background work | `workers.py` | `QThreadPool` worker that keeps exports off the UI thread |

## Requirements

- Windows 10/11
- Python 3.13 (the tested development version is 3.13.0)
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

`env/` is the Python virtual environment. `.env.example` only documents the supported environment variable; the application does not automatically load `.env` files.

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

Typical workflow:

1. Select a product.
2. Enter a Lot ID and Component ID.
3. Select a process stage to preview its map.
4. Use **ROI** for interactive defect-point inspection.
5. Select a `LOSS1`–`LOSS6` stage before opening **Loss Customized**.

## Expected data layout

```text
VSA_DATA_ROOT/
└── <product>/
    ├── csv/<lot>/<stage>/<component>.csv
    ├── map/<lot>/<stage>/<component>.png
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

## Quality checks

```powershell
.\env\Scripts\python.exe -m pytest
.\env\Scripts\ruff.exe check .
.\env\Scripts\ruff.exe format --check .
.\env\Scripts\python.exe -m pip check
```

Tests use temporary synthetic data and must not point at production `VSA_DATA_ROOT`.

## Security and data handling

- Production data is treated as read-only.
- User-provided path fields reject separators and traversal components.
- Local virtual environments, `.env` files, caches, generated HTML, and build artifacts are ignored by Git.
- Do not add real manufacturing data or identifiers to issues, screenshots, fixtures, or commits.

## Roadmap

See [Todo.md](Todo.md) for prioritized correctness, testing, performance, packaging, and UI improvements.

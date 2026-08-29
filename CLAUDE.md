# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this project is

VSA (Visual Stage Analysis) is a Windows **PySide6 desktop application** for inspecting
manufacturing defect maps across process stages. It is a modernized, sanitized **portfolio
version** of an internal legacy tool: it must stay demoable to a reviewer who has no
production data, credentials, or Windows share access.

Stack: PySide6 6.11 (incl. QtWebEngine/QWebChannel), pandas 3, Plotly 7, Dash 4 / Flask,
Pillow. Python **3.13 only** (`requires-python = ">=3.13,<3.14"`).

## Repository layout

```text
src/vsa/
  app.py              # main(): QApplication bootstrap, supports --smoke-test
  __main__.py         # python -m vsa
  config.py           # VSA_DATA_ROOT, STAGE_SEQUENCE, LOSS_STAGE_PAIRS, validated resources
  paths.py            # validate_component() + every data-root path builder
  models.py           # InspectionSelection value object
  workers.py          # FunctionWorker (QRunnable) for background work
  logging_config.py   # configure_logging(), VSA_LOG_LEVEL
  diagnostics.py      # non-sensitive runtime summary for issue reports
  resources/          # button_names.json (product -> stages), rule.json (good/bad defects)
  services/           # non-Qt, unit-testable logic
    data.py           #   CSV validation, classification, conversion, loss merge, yield change
    files.py          #   copy_file / copy_folder_contents
    images.py         #   bounded-memory image grid composition
    system.py         #   open_local_file (os.startfile / open / xdg-open)
  views/              # Qt + Plotly/Dash layer
    main_window.py    #   MainWindow: search, stage buttons, exports, ROI launch
    roi_plot.py       #   ROI Dash server + WebChannel point selection
    loss_map_plot.py  #   loss-map figure, defect selection dialog, WebChannel
    loss_map_window.py, custom_map_window.py, custom_map_plot.py
    actions.py        #   vertical/horizontal comparison + yield exports
scripts/create_demo_data.py   # deterministic synthetic dataset
tests/                        # pytest + pytest-qt, offscreen Qt via conftest.py
docs/DATA_FORMAT.md           # versioned directory + CSV contract
```

The old flat modules (`main.py`, `ui.py`, `plot.py`, `data_processing.py`, `vsa_paths.py`, …)
were moved into `src/vsa/` in 0.2.0. If a doc or issue references them, it is stale —
`README.md`'s architecture table and its `python main.py` commands are known to be stale.

## Commands

Always use the repo virtual environment; do not touch the global interpreter.

```bash
env/Scripts/python.exe -m pytest
```

```bash
env/Scripts/ruff.exe check . && env/Scripts/ruff.exe format --check .
```

```bash
env/Scripts/python.exe -m pip check
```

Run the app (needs `VSA_DATA_ROOT`; PowerShell):

```bash
env/Scripts/python.exe -m vsa
```

Generate demo data and launch without production data (PowerShell):

```bash
env/Scripts/python.exe -m scripts.create_demo_data
```

Then `$env:VSA_DATA_ROOT = (Resolve-Path .\demo_data).Path` and run the app. Demo values:
product `Product A`, Lot ID `DEMO-LOT`, Component ID `DEMO-CMP`.

Headless GUI smoke test:

```bash
env/Scripts/python.exe -m vsa --smoke-test
```

CI (`.github/workflows/ci.yml`, windows-latest) runs ruff check, ruff format --check, pytest
with `QT_QPA_PLATFORM=offscreen`, and `pip check`. Match CI locally before declaring done.

## Conventions

- **One source of truth for paths.** Never build a data path by string concatenation. Use
  `vsa.paths` helpers; every user-supplied component goes through `validate_component()`,
  which rejects separators, `..`, control characters, and Windows-reserved names, and the
  resolved path must stay under the data root.
- **One source of truth for stages.** `config.STAGE_SEQUENCE` / `DYNAMIC_STAGES` /
  `LOSS_STAGE_PAIRS`. Do not introduce spelling variants (`INNER1`, never `INN1`).
- **Keep Qt out of logic.** CSV, image, file, and server logic lives in `services/` and is
  tested without constructing a widget. Views orchestrate; they do not compute.
- **Validate external data.** CSVs must pass `validate_defect_frame`; loss stages reject
  duplicate `(Row, Col)`. Surface an actionable `QMessageBox` and log the traceback.
- **Resources over literals.** Product/stage buttons come from `resources/button_names.json`,
  defect classification from `resources/rule.json`, both validated in `config.py`.
- **Clean up.** Context managers for files, Pillow images, temp dirs, and servers. Dash
  servers get an OS-assigned port and are shut down in `closeEvent`; temporary HTML/CSV must
  not survive window close or an exception.
- **Background work** goes through `FunctionWorker` on `QThreadPool`; keep a reference in
  `active_workers` so it is not garbage collected mid-flight.
- Typing: `from __future__ import annotations`, module docstrings, ruff line length 100,
  double quotes, import sorting (`E4,E7,E9,F,I`).
- No broad `except Exception` unless it logs a traceback and shows a useful UI error.

## Data safety (non-negotiable)

- `D:/Database-PC` (the default root) and any configured `VSA_DATA_ROOT` are **read-only
  production data**. Never write to them, and never point tests at them.
- Tests use `tmp_path` and synthetic fixtures only.
- Never commit or print real Lot IDs, Component IDs, PKG numbers, CSV rows, images,
  credentials, or machine-specific paths — including in fixtures, logs, and screenshots.
- `env/` is a virtual environment, not a config file. `.env` is never read, staged, or
  printed; only the sanitized `.env.example` is committed.

## Working agreements

- Check `git status` first and preserve unrelated changes; the tree often carries in-progress
  refactor work.
- Make the smallest coherent change; update tests and `docs/DATA_FORMAT.md` when behavior,
  schema, configuration, or the operator workflow changes.
- Keep `Todo.md` (Traditional Chinese) and `CHANGELOG.md` current; mark a Todo item done only
  after its stated acceptance condition is verified.
- Commit/push only when repository delivery was requested. Never force-push or rewrite
  published history.
- `AGENTS.md` holds the same rules for other agent runtimes; keep the two consistent.

---
name: vsa-interview-demo
description: Prepare or run an interview walkthrough of the VSA portfolio project — set up the live demo with synthetic data, rehearse the architecture story, or draft answers to likely interviewer questions about design decisions, testing, and data safety. Use when the user mentions an interview, portfolio review, demo, presentation, or "how do I explain this project".
---

# VSA Interview Demo

This repository exists to be shown to a reviewer who has no production data. Optimize for
"a stranger can run it and understand it in ten minutes."

## Getting the demo running (do this first, every time)

The demo must never depend on production data. From a clean PowerShell session:

```bash
env/Scripts/python.exe -m scripts.create_demo_data
```

```powershell
$env:VSA_DATA_ROOT = (Resolve-Path .\demo_data).Path
```

```bash
env/Scripts/python.exe -m vsa
```

Demo inputs: product `Product A`, Lot ID `DEMO-LOT`, Component ID `DEMO-CMP`.

Verify before presenting — a failed demo costs more than a missing one:

```bash
env/Scripts/python.exe -m pytest
```

```bash
env/Scripts/python.exe -m vsa --smoke-test
```

## Demo sequence

Drive the UI in this order; each step sets up the next talking point.

1. **Search** a product / Lot ID / Component ID → map preview. *Point:* every field is a
   validated single path component (`paths.validate_component`), so `..` or a separator is
   rejected before it touches the filesystem.
2. **Stage buttons** → stage map. *Point:* stages come from a validated packaged resource
   (`resources/button_names.json`), with one canonical stage vocabulary in `config.py`.
3. **ROI** → interactive Plotly/Dash scatter; double-click a defect point. *Point:* Qt
   WebChannel bridges the browser event back into the Qt window, and the Dash server takes an
   OS-assigned port and is shut down on window close.
4. **Loss Customized** on a `LOSS1`–`LOSS6` stage. *Point:* an adjacent-stage merge keyed on
   `(Row, Col)` that rejects duplicate coordinates rather than silently fanning out rows.
5. **Exports** — map, original images, vertical comparison, yield. *Point:* image composition
   estimates canvas bytes first so a large lot cannot exhaust memory; the work runs on a
   `QThreadPool` worker so the UI stays responsive.

## The architecture story

Lead with the problem, not the file list: a legacy single-folder script set was reorganized
into an installable `src/vsa` package with a testable core.

- **Layering** — `views/` (Qt + Plotly) orchestrates; `services/` (pandas, Pillow, shutil, OS)
  computes. Nothing in `services/` needs a widget, which is why 37 tests run headless in CI.
- **One source of truth** — data root, stage vocabulary, and path construction each live in
  exactly one module. The legacy bug where `INN1` and `INNER1` disagreed across modules is the
  concrete motivation.
- **Safety at the boundary** — external CSVs are schema- and type-validated; user input is
  validated as path components and confined below the data root.
- **Resource lifetime** — the legacy version leaked Dash servers, temp HTML, and threads. Now
  every one has an owner and a `closeEvent`/`try-finally`.
- **Reproducibility** — pinned dependencies, Python 3.13, GitHub Actions on windows-latest
  running ruff + offscreen pytest + `pip check`, PyInstaller spec for a distributable build.

Use `Todo.md` and `CHANGELOG.md` as evidence: they record the audit, the specific defects
found (ROI argument mismatch, Export Map creating a folder instead of a file, dead
`customdata` on a WebGL trace, the un-shutdown Dash server), and their acceptance criteria.

## Likely questions — have an answer ready

- *Why PySide6 + an embedded web view instead of one or the other?* Operators need a native
  Windows app and file dialogs; the plots need Plotly interactivity. WebChannel is the seam.
- *How do you test a GUI?* Keep logic out of the GUI, then use `pytest-qt` with
  `QT_QPA_PLATFORM=offscreen` for the thin remainder — including a real WebChannel round-trip
  test and a server-shutdown test.
- *How is customer data protected?* No production images, CSVs, identifiers, or credentials in
  the repo; the data root is environment-configured and treated as read-only; diagnostics
  deliberately report only versions and platform.
- *What would you do next?* Answer from the open items in `Todo.md`, not from invention.

## When helping the user prepare

- Verify claims against the code before putting them in a script or slide — never invent a
  feature, benchmark, or metric.
- Keep every example on synthetic demo data; no real Lot IDs or component names.
- If the user asks for slides, a one-pager, or a README-style summary, offer to publish it as
  an artifact so they can share the link.

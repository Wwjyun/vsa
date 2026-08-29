---
name: vsa-development
description: Implement or maintain the VSA PySide6 defect-map desktop app — application code, CSV/image services, paths and configuration, tests, packaging, and docs. Use for any change inside this repository; read-only reviews do not authorize commits or pushes.
---

# VSA Development

Read `CLAUDE.md` for layout and conventions. This skill is the working procedure.

## 1. Orient before editing

- `git status` first; the tree often carries in-progress refactor work. Preserve anything
  unrelated to the request.
- Decide whether the request is implementation or read-only analysis. Analysis never commits.
- Check `Todo.md` for whether the item is already tracked, and `docs/DATA_FORMAT.md` if the
  change touches the directory or CSV contract.

## 2. Place the change correctly

Ask where the change belongs *before* writing it:

| Kind of change | Goes in |
| --- | --- |
| CSV parsing, classification, merge, yield math | `src/vsa/services/data.py` |
| Image composition / export | `src/vsa/services/images.py` |
| File or folder copying | `src/vsa/services/files.py` |
| Path construction, input validation | `src/vsa/paths.py` |
| Stage names, data root, packaged JSON | `src/vsa/config.py` |
| Widgets, dialogs, window lifecycle, Plotly/Dash wiring | `src/vsa/views/` |
| Anything long-running triggered from the UI | `FunctionWorker` in `src/vsa/workers.py` |

Rules that are load-bearing here:

- Every user-supplied path component goes through `validate_component()`; never concatenate a
  data path by hand.
- Stage identity comes from `config.STAGE_SEQUENCE` / `LOSS_STAGE_PAIRS` only — no new
  spelling variants.
- New logic must be reachable in a test without constructing a Qt window. If it is not,
  it is in the wrong layer.
- Servers, temp files, Pillow images, and threads are released in `closeEvent` or a
  `try/finally`, including on the exception path.

## 3. Test with synthetic data only

Never point a test, script, or manual run at `D:/Database-PC` or a real `VSA_DATA_ROOT`.
Build fixtures with `tmp_path`, or regenerate the demo dataset:

```bash
env/Scripts/python.exe -m scripts.create_demo_data
```

Existing tests show the patterns: `tests/test_data_processing.py` (frames), `tests/test_vsa_paths.py`
(traversal rejection), `tests/test_ui_smoke.py` and `tests/test_lossmap_interaction.py` (offscreen Qt),
`tests/test_plot_server.py` (server shutdown).

## 4. Validate

Run everything CI runs, with the repo environment, before reporting completion:

```bash
env/Scripts/python.exe -m pytest
```

```bash
env/Scripts/ruff.exe check . && env/Scripts/ruff.exe format --check .
```

```bash
env/Scripts/python.exe -m pip check
```

For GUI-affecting changes, add the headless launch check:

```bash
env/Scripts/python.exe -m vsa --smoke-test
```

If a check cannot run, name the exact missing prerequisite. Never present an unrun check as
passing.

## 5. Keep the record straight

- Update `tests/` alongside behavior changes, and `docs/DATA_FORMAT.md` on schema changes.
- Update `CHANGELOG.md` for user-visible changes and tick `Todo.md` only when the item's
  acceptance condition is actually verified.
- Keep `CLAUDE.md` and `AGENTS.md` consistent when conventions change.

## 6. Delivery

Commit and push only when the user asked for repository delivery, and only for the scoped
work. Review the staged diff for production identifiers, `.env`, `env/`, caches, generated
HTML/CSV, and build output before committing. Never force-push, rewrite published history,
or bypass a failing check. If a push is blocked, keep the commit and report the hash and the
exact blocker.

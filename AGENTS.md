# VSA Repository Instructions

## Scope

These instructions apply to the entire repository. This project is a Windows desktop application that uses PySide6, pandas, Plotly/Dash, Flask, and Pillow to inspect production image and CSV data.

## Environment

- Use the repository virtual environment for Python commands: `env\Scripts\python.exe`.
- Do not use or modify the global Python installation when the repository environment can perform the task.
- `env/` is a disposable virtual environment, not an environment-variable file. Never commit it.
- A future `.env` file may contain local paths or secrets. Never read, print, stage, or commit its values. Commit only a sanitized `.env.example` when configuration documentation needs one.
- Do not install, upgrade, or remove production dependencies unless the task requires it. Record required dependencies in the repository dependency manifest.

## Production Data Safety

- Treat `D:/Database-PC` and any configured replacement data root as production data.
- Production data is read-only unless the user explicitly authorizes a specific write operation.
- Never run tests against production data. Use temporary directories and synthetic CSV/image fixtures.
- Validate user-derived path components and keep resolved paths within the configured data root.
- Do not include real Lot IDs, Component IDs, PKG numbers, CSV contents, images, credentials, secrets, or machine-specific paths beyond the documented data-root default in commits, logs, fixtures, screenshots, or documentation.

## Implementation Guidelines

- Preserve existing behavior unless the requested change intentionally alters it.
- Prefer `pathlib.Path` and a centralized path/configuration layer over repeated hard-coded path strings.
- Keep Qt UI code separate from CSV calculations, image processing, file operations, and server lifecycle management so non-UI logic can be unit tested.
- Keep product and stage names in one canonical mapping. Do not introduce another spelling variant such as `INN1` versus `INNER1`.
- Validate external CSV schemas and numeric types before processing. Report actionable errors in the UI and retain detailed tracebacks in non-sensitive logs.
- Use context managers for files, Pillow images, temporary directories, and servers. Clean up temporary HTML/CSV files and background threads when their window closes.
- Avoid broad `except Exception` handlers unless they re-raise or log a traceback and present a useful UI error.
- Do not add generated artifacts such as `output_plot.html`, caches, build directories, packaged binaries, or virtual environments to Git.
- Keep `Todo.md` current when completing or discovering material repository work. Mark an item complete only after its acceptance conditions are verified.

## Validation

Run checks with `env\Scripts\python.exe`. Match validation depth to the change and run every applicable check before declaring completion.

Baseline checks available in the current repository:

```powershell
env\Scripts\python.exe -m compileall -q -f . -x "[\\/](env|\.git)[\\/]"
git diff --check
```

When editing a repository skill, also run the validator bundled with the Codex `skill-creator`. When tests and tooling exist, run the targeted tests plus the repository-wide suite, lint/format checks, and `env\Scripts\python.exe -m pip check`. For GUI changes, perform an offscreen or manual smoke test with synthetic data when the installed dependencies allow it. If a check cannot run, state the exact missing prerequisite; do not present an unrun check as passing.

## Git Delivery

- Inspect `git status` before editing and preserve unrelated user changes.
- Stage only intentional files and review the staged diff for secrets, production data, generated files, and accidental edits.
- For a completed implementation task, commit and push the current branch when the user has requested GitHub delivery. Pure reviews, investigations, or reports do not create commits unless explicitly requested.
- Use a concise commit message describing the delivered outcome.
- Push the current branch to its configured upstream. Never force-push, rewrite published history, change remotes, or bypass failed checks unless the user explicitly authorizes that exact action.
- If authentication or branch protection blocks the push, leave the verified commit intact and report the blocker and commit hash.

---
name: vsa-development
description: Work on the VSA PySide6 desktop inspection repository, including application code, CSV and image processing, configuration, tests, documentation, packaging, and GitHub delivery. Use for implementation or maintenance work in this repository; read-only review requests do not authorize commits or pushes.
---

# VSA Development

Follow the repository `AGENTS.md` and preserve the user's stated scope.

## Workflow

1. Inspect `git status`, the relevant code, and `Todo.md` before editing. Preserve unrelated work and identify whether the request is implementation or read-only analysis.
2. Use `env\Scripts\python.exe` for Python commands. Do not treat the `env/` virtual environment as a `.env` configuration file, and never stage either environment contents or secrets.
3. Treat `D:/Database-PC` and the configured data root as read-only production data. Reproduce behavior with temporary synthetic CSV/image fixtures; never mutate production data during development or validation.
4. Make the smallest coherent change. Centralize data-root and stage-name decisions instead of adding more hard-coded paths or spelling variants. Keep file/CSV/image logic testable without constructing a Qt window.
5. Update tests and documentation when behavior, configuration, dependencies, data schema, or operator workflow changes. Keep `Todo.md` aligned with verified progress and newly discovered material work.

## Validation

Run every check applicable to the changed files. At minimum:

```powershell
env\Scripts\python.exe -m compileall -q -f . -x "[\\/](env|\.git)[\\/]"
git diff --check
```

When this skill changes, run the validator bundled with `skill-creator`. Also run targeted and full tests, lint/format checks, `env\Scripts\python.exe -m pip check`, and a synthetic-data GUI smoke test when those checks exist and the environment has their dependencies. Report skipped checks with the precise prerequisite that is missing.

Before delivery, inspect the full diff and staged diff. Exclude virtual environments, `.env`, credentials, production identifiers/data, caches, temporary HTML/CSV, build output, and unrelated user changes.

## Commit and Push

Commit and push only when the user has requested repository delivery. That authorization applies to the current scoped work, not to unrelated changes or history rewriting.

- Stage only the verified files for the task.
- Commit with a concise outcome-focused message.
- Push the current branch to its configured upstream with a normal `git push`.
- Never force-push, change the remote, discard user changes, or bypass failing validation.
- If authentication, permissions, or branch protection blocks delivery, keep the local commit and report the commit hash plus the exact blocker.

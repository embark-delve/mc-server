# Development conventions

Use Python 3.13+, `pyproject.toml`, and the committed `uv.lock`.

- Install: `make bootstrap` (requires uv and Gitleaks; installs Node and both Git hooks)
- Commit gate: `uv run --locked pre-commit run --all-files`
- Push gate: `uv run --locked pre-commit run --all-files --hook-stage pre-push`
- All checks: `make check`
- Tests: `uv run --locked pytest`
- Format: `make format`
- Audit: `make security`
- Package: `uv build`

The supported backend is local Docker. Do not reactivate cloud, legacy shell,
background metrics or auto-shutdown without a separate security review and tests.
Never test restores on real worlds. Use disposable profile directories and
mock Docker for unit tests. Live game tests require a working Docker engine,
explicit EULA agreement, exact mod artifacts, and isolated ports/storage.

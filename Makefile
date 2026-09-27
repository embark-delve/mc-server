.PHONY: bootstrap check test lint type-check format security build
bootstrap:
	uv sync --locked
	uv run --locked nodeenv --node=$$(cat .node-version) .tools/node
	uv run --locked python scripts/node_tools.py ci
	uv run --locked pre-commit install --install-hooks
check: lint type-check test
lint:
	uv run --locked ruff check .
	uv run --locked ruff format --check .
	uv run --locked bandit -c pyproject.toml -r src scripts -q
	uv run --locked python scripts/node_tools.py lint
	uv run --locked python scripts/node_tools.py format-check
type-check:
	uv run --locked mypy src scripts
test:
	uv run --locked pytest
format:
	uv run --locked ruff check --fix .
	uv run --locked ruff format .
	uv run --locked python scripts/node_tools.py format
security:
	uv run --locked pip-audit --skip-editable
	uv run --locked python scripts/node_tools.py audit
	gitleaks git --redact --no-banner
build:
	uv build

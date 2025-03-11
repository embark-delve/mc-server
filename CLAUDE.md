# Minecraft Server Manager Development Guidelines

## Build/Test/Lint Commands
- Run all checks: `make check`
- Run tests: `make test`
- Run single test: `pytest tests/path/to/test_file.py::TestClass::test_function -v`
- Run lint: `make lint`
- Run type checker: `make type-check`
- Format code: `make format`
- Setup dev environment: `make dev-setup`

## Code Style Guidelines
- Line length: 88 characters (Black formatting)
- Python: 3.8+ with type annotations (mypy strict mode)
- Imports: sorted with isort, use absolute imports from `src`
- Class naming: PascalCase
- Function/variable naming: snake_case
- Constants: UPPER_SNAKE_CASE
- Comprehensive docstrings with Args/Returns sections
- Proper error handling with specific exception types and logging
- Configuration via config.yml, env vars, and CLI in order of precedence
- Testing: pytest with high coverage, mock external dependencies
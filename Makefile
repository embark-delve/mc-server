.PHONY: help check test lint type-check format clean install dev-setup docs-build docs-serve run-docker run-aws security

PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy
BLACK := $(VENV)/bin/black
PRE_COMMIT := $(VENV)/bin/pre-commit
MKDOCS := $(VENV)/bin/mkdocs

# Default target
help:
	@echo "Minecraft Server Manager - Development Commands"
	@echo "=============================================="
	@echo ""
	@echo "Development workflow:"
	@echo "  dev-setup   - Set up development environment (venv, deps, pre-commit)"
	@echo "  check       - Run all checks (lint, type-check, test)"
	@echo "  format      - Format code using black and isort"
	@echo "  lint        - Run linter (ruff)"
	@echo "  type-check  - Run type checker (mypy)"
	@echo "  test        - Run tests with coverage"
	@echo "  security    - Run security checks"
	@echo ""
	@echo "Documentation:"
	@echo "  docs-build  - Build documentation"
	@echo "  docs-serve  - Serve documentation locally"
	@echo ""
	@echo "Deployment:"
	@echo "  run-docker  - Run a local Docker Minecraft server"
	@echo "  run-aws     - Run a Minecraft server on AWS"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean       - Remove build artifacts and cache directories"
	@echo "  clean-all   - Clean, plus remove virtual environment"
	@echo ""
	@echo "Installation:"
	@echo "  install     - Install dependencies"

# Check target - runs all checks
check: lint type-check test

# Test target
test:
	@echo "Running tests..."
	$(PYTEST) --cov=src tests/

# Lint target
lint:
	@echo "Running linter..."
	$(RUFF) check .

# Type-check target
type-check:
	@echo "Running type checker..."
	$(MYPY) src

# Format target
format:
	@echo "Formatting code..."
	$(BLACK) .
	$(RUFF) check --fix .

# Security check target
security:
	@echo "Running security checks..."
	$(PIP) install bandit safety
	$(VENV)/bin/bandit -r src/
	$(VENV)/bin/safety check

# Clean target
clean:
	@echo "Cleaning up build artifacts and caches..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Clean all target (includes venv)
clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf $(VENV)

# Install target
install:
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt

# Dev setup target
dev-setup: $(VENV)
	@echo "Setting up development environment..."
	$(PIP) install -e .
	$(PIP) install -r requirements-dev.txt
	$(PRE_COMMIT) install

# Docs build target
docs-build:
	@echo "Building documentation..."
	cd docs && $(MKDOCS) build

# Docs serve target
docs-serve:
	@echo "Serving documentation locally..."
	cd docs && $(MKDOCS) serve

# Run docker target
run-docker:
	@echo "Starting a local Docker Minecraft server..."
	$(PYTHON_VENV) minecraft-server.py --type docker start

# Run AWS target
run-aws:
	@echo "Starting an AWS Minecraft server..."
	@echo "Usage: make run-aws INSTANCE_ID=i-xxxx REGION=us-east-1"
	$(PYTHON_VENV) minecraft-server.py --type aws --instance-id $(INSTANCE_ID) --region $(REGION) start

# Create virtual environment
$(VENV):
	$(PYTHON) -m venv $(VENV) 
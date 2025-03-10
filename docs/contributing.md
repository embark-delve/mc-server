# Contributing Guidelines

Thank you for your interest in contributing to the Minecraft Server Manager project! This document outlines the process for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Requests](#pull-requests)
- [Documentation](#documentation)

## Code of Conduct

This project is governed by our [Code of Conduct](./CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.6+
- Docker (for local testing)
- Git

### Setup

1. Fork the repository on GitHub
2. Clone your fork locally:

   ```bash
   git clone https://github.com/yourusername/minecraft-server.git
   cd minecraft-server
   ```

3. Set up a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Install development dependencies
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

1. Create a branch for your changes:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes
3. Run tests to ensure your changes don't break existing functionality:

   ```bash
   pytest
   ```

4. Commit your changes with a descriptive commit message:

   ```bash
   git commit -m "Add feature: your feature description"
   ```

5. Push your branch to GitHub:

   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a Pull Request on GitHub

## Coding Standards

We use several tools to maintain code quality:

- **Ruff**: For linting
- **Black**: For code formatting
- **MyPy**: For type checking

These are all configured in our pre-commit hooks, which will automatically check your code before committing.

### Python Style Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) conventions
- Use type hints for all function parameters and return values
- Write docstrings for all classes, methods, and functions
- Keep functions small and focused (fewer than 50 lines if possible)
- Use descriptive variable names

## Testing

We use pytest for testing. All new features should include tests.

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=src tests/

# Run a specific test
pytest tests/test_file.py::TestClass::test_function
```

### Writing Tests

- Test files should be named `test_*.py`
- Test classes should be named `Test*`
- Test methods should be named `test_*`
- Use descriptive test names that explain what is being tested
- Each test should focus on testing a single behavior
- Use mocks where appropriate to isolate dependencies

## Pull Requests

### PR Guidelines

1. Keep PRs focused on a single change
2. Update documentation as needed
3. Add tests for new features
4. Ensure all tests pass
5. Update the [CHANGELOG.md](../CHANGELOG.md) file

### PR Template

Your PR description should include:

- A summary of the changes
- Why the changes are necessary
- How you tested the changes
- Any notes on implementation decisions

## Documentation

Documentation is a crucial part of the project. When adding or modifying features:

1. Update docstrings for any changed code
2. Update README.md if user-facing functionality changes
3. Add or update documentation in the docs/ directory

## Adding New Server Implementations

To add a new server implementation:

1. Create a new class in `src/implementations/` that inherits from `MinecraftServer`
2. Implement all required abstract methods
3. Register the implementation in `MinecraftManager._register_server_types()`
4. Add tests for the new implementation
5. Add documentation for the new implementation

## Terraform Contributions

For Terraform-related changes:

1. Format code with `terraform fmt`
2. Validate with `terraform validate`
3. Run terraform security checks with `tfsec`
4. Run cost estimation with `infracost`
5. Document any new variables or outputs

Thank you for contributing to the Minecraft Server Manager project!

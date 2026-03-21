# Contributing to HireKit

Thank you for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/ziho/hirekit.git
cd hirekit

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/ tests/
```

## Adding a Data Source Plugin

1. Create a new file in `src/hirekit/sources/{region}/`
2. Implement the `BaseSource` protocol
3. Register with `@SourceRegistry.register`
4. Add entry point in `pyproject.toml`
5. Write tests in `tests/test_sources/`

See `src/hirekit/sources/base.py` for the full protocol documentation.

## Code Style

- We use `ruff` for linting and formatting
- Type hints are required for all public functions
- Tests are required for new features

## Pull Request Process

1. Fork the repo and create your branch from `main`
2. Add tests for any new functionality
3. Ensure all tests pass (`pytest`)
4. Ensure linting passes (`ruff check`)
5. Update documentation if needed
6. Submit a PR with a clear description

## Reporting Issues

Use GitHub Issues with the provided templates (bug report or feature request).

# Justfile for docio development

# List available commands
default:
    @just --list

# Install dependencies
install:
    uv add --dev pytest pytest-cov ruff mypy

# Run tests
test:
    pytest -v

# Run tests with coverage report
test-cov:
    pytest -v --cov=docio --cov-report=html --cov-report=term

# Run linting
lint:
    ruff check src/ tests/ examples/

# Fix linting issues
lint-fix:
    ruff check --fix src/ tests/ examples/

# Run type checking
typecheck:
    mypy src/docio

# Run all checks (lint + typecheck + test)
check: lint typecheck test

# Format code
format:
    ruff format src/ tests/ examples/

# Build package
build:
    python -m build

# Clean build artifacts
clean:
    rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov/
    find . -type d -name __pycache__ -exec rm -rf {} +

# Run demo (docio documenting itself)
demo:
    python examples/demo.py

# Install package in editable mode
dev-install:
    uv pip install -e ".[dev]"

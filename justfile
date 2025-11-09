set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

default:
    @just --list

install:
    uv sync

test:
    uv run pytest -v

testc:
    uv run pytest -v --cov=docio --cov-report=html --cov-report=term

lint:
    uv run ruff check src/ tests/ examples/

lint-fix:
    uv run ruff check --fix src/ tests/ examples/

typecheck:
    uv run mypy src/docio

check: lint typecheck test

format:
    uv run ruff format src/ tests/ examples/

build:
    uv build

clean:
    uv run python -c "import shutil; import pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', 'htmlcov', '.pytest_cache', '.mypy_cache', '.ruff_cache'] if pathlib.Path(p).exists()]; [p.unlink() for p in pathlib.Path('.').glob('*.egg-info') if p.exists()]"

demo:
    uv run python examples/demo.py

dev-install:
    uv sync --all-extras --dev
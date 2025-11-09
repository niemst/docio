"""
Unit tests for CLI functionality.
"""

import pytest
import tempfile
import sys
from pathlib import Path
from io import StringIO
from unittest.mock import patch
from docio.cli import (
    load_config,
    cmd_generate,
    cmd_scan,
    cmd_validate,
    main,
)
import argparse


def test_load_config_no_file():
    """Test load_config when no pyproject.toml exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            config = load_config()
            assert config == {}
        finally:
            os.chdir(original_cwd)


def test_load_config_with_docio_config():
    """Test load_config reads docio configuration from pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        pyproject = tmpdir / "pyproject.toml"
        pyproject.write_text("""
[tool.docio]
exclude = ["*/migrations/*"]
include = ["src/**/*.py"]
template_dir = "custom/templates"
""")

        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            config = load_config()
            assert config.get("exclude") == ["*/migrations/*"]
            assert config.get("include") == ["src/**/*.py"]
            assert config.get("template_dir") == "custom/templates"
        finally:
            os.chdir(original_cwd)


def test_cmd_generate_no_files():
    """Test cmd_generate when no Python files are found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        args = argparse.Namespace(
            paths=[str(tmpdir)],
            dry_run=False,
            exclude=None,
            include=None,
            template_dir=None
        )

        # Redirect stderr to capture output
        with patch('sys.stderr', new=StringIO()) as mock_stderr:
            result = cmd_generate(args)
            assert result == 1
            assert "No Python files found" in mock_stderr.getvalue()


def test_cmd_generate_nonexistent_path():
    """Test cmd_generate with nonexistent path."""
    args = argparse.Namespace(
        paths=["/nonexistent/path"],
        dry_run=False,
        exclude=None,
        include=None,
        template_dir=None
    )

    with patch('sys.stderr', new=StringIO()) as mock_stderr:
        result = cmd_generate(args)
        assert result == 1
        assert "Path does not exist" in mock_stderr.getvalue()


def test_cmd_generate_with_python_file():
    """Test cmd_generate with a Python file containing @docio."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create source file
        src_file = tmpdir / "test.py"
        src_file.write_text("""
from docio import docio

@docio
class MyClass:
    pass
""")

        # Create necessary template
        template_dir = tmpdir / "templates"
        template_dir.mkdir()
        (template_dir / "class.md").write_text("# {name}")

        args = argparse.Namespace(
            paths=[str(src_file)],
            dry_run=False,
            exclude=None,
            include=None,
            template_dir=str(template_dir)
        )

        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            with patch('docio.core._get_package_root', return_value=tmpdir):
                result = cmd_generate(args)
                assert result == 0
                output = mock_stdout.getvalue()
                assert "Created:" in output or "Would create:" in output


def test_cmd_generate_dry_run():
    """Test cmd_generate in dry-run mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create source file
        src_file = tmpdir / "test.py"
        src_file.write_text("""
from docio import docio

@docio
def my_func():
    pass
""")

        args = argparse.Namespace(
            paths=[str(src_file)],
            dry_run=True,
            exclude=None,
            include=None,
            template_dir=None
        )

        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            with patch('docio.core._get_package_root', return_value=tmpdir):
                result = cmd_generate(args)
                assert result == 0
                output = mock_stdout.getvalue()
                assert "Would create:" in output or "No new documentation stubs needed" in output


def test_cmd_scan_no_files():
    """Test cmd_scan when no Python files are found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        args = argparse.Namespace(paths=[str(tmpdir)])

        with patch('sys.stderr', new=StringIO()) as mock_stderr:
            result = cmd_scan(args)
            assert result == 1
            assert "No Python files found" in mock_stderr.getvalue()


def test_cmd_scan_with_decorators():
    """Test cmd_scan finds @docio decorators."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create source file with @docio decorators
        src_file = tmpdir / "test.py"
        src_file.write_text("""
from docio import docio

@docio
class MyClass:
    pass

@docio(filename="custom.md")
def my_func():
    pass
""")

        args = argparse.Namespace(paths=[str(src_file)])

        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            result = cmd_scan(args)
            assert result == 0
            output = mock_stdout.getvalue()
            assert "MyClass" in output
            assert "my_func" in output
            assert "filename=custom.md" in output


def test_cmd_scan_nonexistent_path():
    """Test cmd_scan with nonexistent path."""
    args = argparse.Namespace(paths=["/nonexistent/path"])

    with patch('sys.stderr', new=StringIO()) as mock_stderr:
        result = cmd_scan(args)
        assert result == 1
        assert "Path does not exist" in mock_stderr.getvalue()


def test_cmd_validate_with_missing_docs():
    """Test cmd_validate detects missing documentation."""
    # Register a fake object with missing docs
    from docio.core import _DOCIO_REGISTRY

    original_registry = _DOCIO_REGISTRY.copy()
    _DOCIO_REGISTRY.clear()

    try:
        def fake_function():
            pass

        _DOCIO_REGISTRY.append((fake_function, None))

        args = argparse.Namespace(strict=False)

        with patch('sys.stderr', new=StringIO()) as mock_stderr:
            result = cmd_validate(args)
            # Should exit with 0 when strict=False
            assert result == 0
            output = mock_stderr.getvalue()
            assert "Missing documentation files" in output

    finally:
        _DOCIO_REGISTRY.clear()
        _DOCIO_REGISTRY.extend(original_registry)


def test_cmd_validate_strict_mode():
    """Test cmd_validate in strict mode fails on missing docs."""
    from docio.core import _DOCIO_REGISTRY

    original_registry = _DOCIO_REGISTRY.copy()
    _DOCIO_REGISTRY.clear()

    try:
        def fake_function():
            pass

        _DOCIO_REGISTRY.append((fake_function, None))

        args = argparse.Namespace(strict=True)

        with patch('sys.stderr', new=StringIO()):
            result = cmd_validate(args)
            # Should exit with 1 when strict=True and docs missing
            assert result == 1

    finally:
        _DOCIO_REGISTRY.clear()
        _DOCIO_REGISTRY.extend(original_registry)


def test_cmd_validate_all_docs_present():
    """Test cmd_validate succeeds when all docs are present."""
    from docio.core import _DOCIO_REGISTRY

    original_registry = _DOCIO_REGISTRY.copy()
    _DOCIO_REGISTRY.clear()

    try:
        # Don't add any fake missing docs
        args = argparse.Namespace(strict=True)

        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            result = cmd_validate(args)
            assert result == 0
            output = mock_stdout.getvalue()
            assert "All @docio decorated objects have documentation" in output

    finally:
        _DOCIO_REGISTRY.clear()
        _DOCIO_REGISTRY.extend(original_registry)


def test_main_no_command():
    """Test main function with no command shows help."""
    with patch('sys.argv', ['docio']):
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            result = main()
            assert result == 0
            # Should print help
            output = mock_stdout.getvalue()
            assert "usage:" in output.lower() or "docio" in output


def test_main_generate_command():
    """Test main function with generate command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        src_file = tmpdir / "test.py"
        src_file.write_text("# empty file")

        with patch('sys.argv', ['docio', 'generate', str(src_file), '--dry-run']):
            with patch('sys.stdout', new=StringIO()):
                with patch('docio.core._get_package_root', return_value=tmpdir):
                    result = main()
                    assert result == 0


def test_main_scan_command():
    """Test main function with scan command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        src_file = tmpdir / "test.py"
        src_file.write_text("""
from docio import docio

@docio
def test_func():
    pass
""")

        with patch('sys.argv', ['docio', 'scan', str(src_file)]):
            with patch('sys.stdout', new=StringIO()):
                result = main()
                assert result == 0


def test_main_validate_command():
    """Test main function with validate command."""
    with patch('sys.argv', ['docio', 'validate']):
        with patch('sys.stdout', new=StringIO()):
            result = main()
            # Result depends on current registry state
            assert result in [0, 1]


def test_cmd_generate_with_exclude_patterns():
    """Test cmd_generate respects exclude patterns from CLI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create a file that should be excluded (use pattern that matches)
        src_dir = tmpdir / "src" / "migrations"
        src_dir.mkdir(parents=True)
        src_file = src_dir / "test.py"
        src_file.write_text("""
from docio import docio

@docio
class Migration:
    pass
""")

        args = argparse.Namespace(
            paths=[str(src_file)],
            dry_run=False,
            exclude=["*/migrations/*"],
            include=None,
            template_dir=None
        )

        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            with patch('docio.core._get_package_root', return_value=tmpdir):
                result = cmd_generate(args)
                assert result == 0
                output = mock_stdout.getvalue()
                # When file is excluded, no docs should be created
                assert "No new documentation stubs needed" in output


def test_cmd_generate_error_handling():
    """Test cmd_generate handles errors gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        src_file = tmpdir / "test.py"
        src_file.write_text("""
from docio import docio

@docio
class MyClass:
    pass
""")

        args = argparse.Namespace(
            paths=[str(src_file)],
            dry_run=False,
            exclude=None,
            include=None,
            template_dir="/nonexistent/template/dir"
        )

        with patch('sys.stderr', new=StringIO()) as mock_stderr:
            result = cmd_generate(args)
            # Should handle error and print message
            output = mock_stderr.getvalue()
            assert "Error processing" in output or "Template directory not found" in output

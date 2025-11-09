"""
Extended unit tests for core docio functionality to improve coverage.
"""

import pytest
import tempfile
from pathlib import Path
from docio import docio
from docio.core import (
    scan_file_for_docio,
    _should_process_file,
    auto_generate_stubs,
)


def test_docio_strips_yaml_frontmatter():
    """Test that YAML frontmatter is stripped from documentation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        docs_dir = tmpdir / "docs"
        docs_dir.mkdir(parents=True)

        doc_file = docs_dir / "TestClass.md"
        doc_file.write_text("---\ntitle: Test\nauthor: Me\n---\n\n# Test\n\nActual content here.")

        from docio import core
        original_get_root = core._get_package_root

        def mock_get_root():
            return tmpdir

        core._get_package_root = mock_get_root

        try:
            @docio(filename="TestClass.md")
            class TestClass:
                pass

            # Should have stripped frontmatter
            assert "Actual content here." in TestClass.__doc__
            assert "---" not in TestClass.__doc__
            assert "title: Test" not in TestClass.__doc__

        finally:
            core._get_package_root = original_get_root


def test_scan_file_for_docio():
    """Test scanning a Python file for @docio decorators."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        test_file = tmpdir / "test.py"
        test_file.write_text("""
from docio import docio

@docio
class MyClass:
    pass

@docio(filename="custom.md")
def my_function():
    pass

def no_decorator():
    pass
""")

        results = scan_file_for_docio(test_file)
        assert len(results) == 2

        # Check class
        names = [r[0] for r in results]
        assert "MyClass" in names
        assert "my_function" in names

        # Check filename override
        for name, filename, lineno, obj_type in results:
            if name == "my_function":
                assert filename == "custom.md"
            if name == "MyClass":
                assert filename is None


def test_scan_file_for_docio_nonexistent():
    """Test scanning a nonexistent file returns empty list."""
    results = scan_file_for_docio(Path("/nonexistent/file.py"))
    assert results == []


def test_scan_file_for_docio_invalid_syntax():
    """Test scanning a file with invalid Python syntax."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        test_file = tmpdir / "invalid.py"
        test_file.write_text("this is not valid python {{{")

        results = scan_file_for_docio(test_file)
        assert results == []


def test_should_process_file_with_exclude():
    """Test _should_process_file with exclude patterns."""
    root = Path("/project")
    file_path = Path("/project/src/migrations/test.py")

    # Should exclude migrations
    assert not _should_process_file(
        file_path, root, exclude_patterns=["*/migrations/*"]
    )

    # Should include without exclude pattern
    assert _should_process_file(file_path, root)


def test_should_process_file_with_include():
    """Test _should_process_file with include patterns."""
    root = Path("/project")
    file_path = Path("/project/src/mymodule/test.py")

    # Should include when matching pattern
    assert _should_process_file(
        file_path, root, include_patterns=["*/mymodule/*"]
    )

    # Should exclude when not matching pattern
    assert not _should_process_file(
        file_path, root, include_patterns=["*/other/*"]
    )


def test_auto_generate_stubs():
    """Test auto-generating documentation stub files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create source file with @docio decorator
        src_dir = tmpdir / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        test_file = src_dir / "module.py"
        test_file.write_text("""
from docio import docio

@docio
class MyClass:
    pass
""")

        # Create template directory
        template_dir = tmpdir / "templates"
        template_dir.mkdir()
        class_template = template_dir / "class.md"
        class_template.write_text("# {name}\n\nClass documentation for {name}.")

        # Mock _get_package_root
        from docio import core
        original_get_root = core._get_package_root

        def mock_get_root():
            return tmpdir

        core._get_package_root = mock_get_root

        try:
            # Generate stubs
            created = auto_generate_stubs(test_file, template_dir=template_dir)

            assert len(created) == 1
            assert created[0].exists()
            assert "MyClass" in created[0].name
            content = created[0].read_text()
            assert "MyClass" in content

        finally:
            core._get_package_root = original_get_root


def test_auto_generate_stubs_dry_run():
    """Test auto-generate stubs in dry-run mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        src_dir = tmpdir / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        test_file = src_dir / "module.py"
        test_file.write_text("""
from docio import docio

@docio
def my_function():
    pass
""")

        from docio import core
        original_get_root = core._get_package_root

        def mock_get_root():
            return tmpdir

        core._get_package_root = mock_get_root

        try:
            # Dry run should return paths but not create files
            created = auto_generate_stubs(test_file, dry_run=True)

            assert len(created) == 1
            assert not created[0].exists()  # File should not exist in dry-run

        finally:
            core._get_package_root = original_get_root


def test_auto_generate_stubs_with_exclude_patterns():
    """Test auto-generate stubs respects exclude patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        migrations_dir = tmpdir / "src" / "migrations"
        migrations_dir.mkdir(parents=True)
        test_file = migrations_dir / "migration.py"
        test_file.write_text("""
from docio import docio

@docio
class Migration:
    pass
""")

        from docio import core
        original_get_root = core._get_package_root

        def mock_get_root():
            return tmpdir

        core._get_package_root = mock_get_root

        try:
            # Should exclude migrations directory
            created = auto_generate_stubs(
                test_file, exclude_patterns=["*/migrations/*"]
            )

            assert len(created) == 0

        finally:
            core._get_package_root = original_get_root


def test_auto_generate_stubs_skip_existing():
    """Test that auto_generate_stubs skips existing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        src_dir = tmpdir / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        test_file = src_dir / "module.py"
        test_file.write_text("""
from docio import docio

@docio
class MyClass:
    pass
""")

        # Create docs directory and existing file
        docs_dir = tmpdir / "docs" / "src" / "mypackage" / "module"
        docs_dir.mkdir(parents=True)
        existing_file = docs_dir / "MyClass.md"
        existing_content = "# Existing Content\n\nDo not overwrite!"
        existing_file.write_text(existing_content)

        from docio import core
        original_get_root = core._get_package_root

        def mock_get_root():
            return tmpdir

        core._get_package_root = mock_get_root

        try:
            # Generate stubs - should skip existing file
            created = auto_generate_stubs(test_file)

            assert len(created) == 0
            # Verify existing file was not modified
            assert existing_file.read_text() == existing_content

        finally:
            core._get_package_root = original_get_root


def test_docio_decorator_handles_long_paragraph():
    """Test that docio decorator truncates long paragraphs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        docs_dir = tmpdir / "docs"
        docs_dir.mkdir(parents=True)

        # Create a very long paragraph
        long_text = "A" * 250
        doc_file = docs_dir / "TestClass.md"
        doc_file.write_text(f"# Test\n\n{long_text}")

        from docio import core
        original_get_root = core._get_package_root

        def mock_get_root():
            return tmpdir

        core._get_package_root = mock_get_root

        try:
            @docio(filename="TestClass.md")
            class TestClass:
                pass

            # Should be truncated with ellipsis
            assert len(TestClass.__doc__) <= 203  # 200 + "..."
            assert TestClass.__doc__.endswith("...")

        finally:
            core._get_package_root = original_get_root


def test_scan_file_detects_test_files():
    """Test that scan_file_for_docio detects test files correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create a test file
        tests_dir = tmpdir / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_foo.py"
        test_file.write_text("""
from docio import docio

@docio
def test_something():
    pass
""")

        results = scan_file_for_docio(test_file)
        assert len(results) == 1
        name, filename, lineno, obj_type = results[0]
        assert obj_type == "test"


def test_scan_file_detects_async_functions():
    """Test scanning async functions with @docio decorator."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Use filename without "test" to avoid being classified as test file
        test_file = tmpdir / "async_module.py"
        test_file.write_text("""
from docio import docio

@docio
async def async_function():
    pass
""")

        results = scan_file_for_docio(test_file)
        assert len(results) == 1
        name, filename, lineno, obj_type = results[0]
        assert name == "async_function"
        assert obj_type == "function"


def test_auto_generate_stubs_with_nonexistent_template_dir():
    """Test that auto_generate_stubs raises error for nonexistent template dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        src_dir = tmpdir / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        test_file = src_dir / "module.py"
        test_file.write_text("""
from docio import docio

@docio
class MyClass:
    pass
""")

        with pytest.raises(FileNotFoundError, match="Template directory not found"):
            auto_generate_stubs(test_file, template_dir="/nonexistent/path")


def test_auto_generate_stubs_nonexistent_file():
    """Test that auto_generate_stubs handles nonexistent files gracefully."""
    result = auto_generate_stubs(Path("/nonexistent/file.py"))
    assert result == []


def test_docio_decorator_with_only_headings():
    """Test docio decorator when doc only contains headings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        docs_dir = tmpdir / "docs"
        docs_dir.mkdir(parents=True)

        doc_file = docs_dir / "TestClass.md"
        doc_file.write_text("# Heading 1\n\n## Heading 2\n\n### Heading 3")

        from docio import core
        original_get_root = core._get_package_root

        def mock_get_root():
            return tmpdir

        core._get_package_root = mock_get_root

        try:
            @docio(filename="TestClass.md")
            class TestClass:
                pass

            # Should use first heading when no paragraph found
            assert "Heading 1" in TestClass.__doc__ or "Heading 2" in TestClass.__doc__

        finally:
            core._get_package_root = original_get_root

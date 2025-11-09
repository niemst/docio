"""
Unit tests for core docio functionality.
"""

import pytest
from pathlib import Path
from docio import docio, get_doc, show_doc
from docio.exceptions import DocNotFoundError


def test_docio_decorator_without_args():
    """Test @docio decorator without arguments."""
    @docio
    class TestClass:
        pass

    # Should have a docstring set
    assert TestClass.__doc__ is not None


def test_docio_decorator_with_filename():
    """Test @docio decorator with explicit filename."""
    @docio(filename="custom/test.md")
    class TestClass:
        pass

    # Should be registered
    from docio.core import _DOCIO_REGISTRY
    assert any(obj is TestClass for obj, _ in _DOCIO_REGISTRY)


def test_docio_decorator_extracts_first_paragraph():
    """Test @docio decorator extracts first paragraph as short doc."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create source structure
        src_dir = tmpdir / "src" / "testpkg"
        src_dir.mkdir(parents=True)
        test_file = src_dir / "test.py"
        test_file.write_text("# test file")

        # Create docs structure mirroring src
        docs_dir = tmpdir / "docs" / "src" / "testpkg" / "test"
        docs_dir.mkdir(parents=True)

        doc_file = docs_dir / "TestClass.md"
        doc_file.write_text("# Test\n\nFirst paragraph here.\n\nSecond paragraph.")

        # Mock the _get_package_root and module file location
        from docio import core
        original_get_root = core._get_package_root

        def mock_get_root():
            return tmpdir

        core._get_package_root = mock_get_root

        try:
            # Use explicit filename to bypass source file detection issues
            @docio(filename="src/testpkg/test/TestClass.md")
            class TestClass:
                pass

            assert "First paragraph here." in TestClass.__doc__

        finally:
            core._get_package_root = original_get_root


def test_get_doc_raises_on_missing():
    """Test that get_doc raises DocNotFoundError for missing files."""
    class NoDocClass:
        pass

    with pytest.raises(DocNotFoundError):
        get_doc(NoDocClass)


def test_get_doc_falls_back_to_original_docstring():
    """Test that get_doc returns original docstring if no file found."""
    class WithDocstring:
        """Original docstring"""
        pass

    doc = get_doc(WithDocstring)
    assert doc == "Original docstring"


def test_show_doc_uses_cached_full_doc():
    """Test that show_doc uses cached __docio_full__ if available."""
    class TestClass:
        pass

    full_doc = "This is the full documentation"
    TestClass.__docio_full__ = full_doc

    assert show_doc(TestClass) == full_doc


def test_docio_caches_full_doc():
    """Test that decorator caches full documentation."""
    # Create a temporary doc file
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create docs structure with new mapping
        docs_dir = tmpdir / "docs" / "src" / "testpkg"
        docs_dir.mkdir(parents=True)

        doc_file = docs_dir / "TestClass.md"
        doc_file.write_text("# Test Documentation\n\nFull content here.")

        # Mock the _get_package_root to return our temp dir
        from docio import core
        original_get_root = core._get_package_root

        def mock_get_root():
            return tmpdir

        core._get_package_root = mock_get_root

        try:
            # Use explicit filename
            @docio(filename="src/testpkg/TestClass.md")
            class TestClass:
                pass

            # Should have cached full doc
            assert hasattr(TestClass, '__docio_full__')
            assert "Full content here" in TestClass.__docio_full__

        finally:
            core._get_package_root = original_get_root

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


def test_docio_creates_rst_link():
    """Test that decorator creates reStructuredText link to .md file."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create source file structure
        src_dir = tmpdir / "src" / "myapp"
        src_dir.mkdir(parents=True)
        module_file = src_dir / "module.py"
        module_file.write_text("# module")

        # Create docs structure
        docs_dir = tmpdir / "docs" / "src" / "myapp" / "module"
        docs_dir.mkdir(parents=True)
        doc_file = docs_dir / "MyClass.md"
        doc_file.write_text("# MyClass\n\nA test class for RST linking.")

        # Mock package root and module file
        from docio import core
        original_get_root = core._get_package_root

        def mock_get_root():
            return tmpdir

        core._get_package_root = mock_get_root

        try:
            # Create a class in the module context
            import types
            test_module = types.ModuleType('test_module')
            test_module.__file__ = str(module_file)

            @docio(filename="src/myapp/module/MyClass.md")
            class MyClass:
                pass

            # Inject module manually
            MyClass.__module__ = test_module.__name__
            import sys
            sys.modules[test_module.__name__] = test_module

            # Apply decorator again with proper module context
            from docio.core import docio as docio_dec
            MyClass = docio_dec(filename="src/myapp/module/MyClass.md")(MyClass)

            # Check that docstring contains RST link format
            assert MyClass.__doc__ is not None
            # RST link format: `text <path>`_
            assert "<" in MyClass.__doc__ and ">`_" in MyClass.__doc__
            # Should contain path to .md file
            assert ".md" in MyClass.__doc__
            # Should contain the description text
            assert "test class" in MyClass.__doc__.lower()

        finally:
            core._get_package_root = original_get_root

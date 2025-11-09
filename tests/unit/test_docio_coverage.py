"""
Test that all @docio decorated objects have documentation files.

This test ensures that the library itself is properly documented.
"""

import pytest
from docio import validate_docs


def test_all_docio_have_docs():
    """
    Validate that all @docio decorated objects in the codebase have documentation.

    This test will fail if:
    - A @docio decorator is used without a corresponding .md file
    - The documentation file path is incorrect
    - The file cannot be read
    """
    # Import all modules to register @docio decorated objects
    import docio
    import docio.core
    import docio.exceptions

    # This will raise AssertionError if any docs are missing
    validate_docs(strict=True)


def test_validate_docs_returns_missing():
    """Test that validate_docs returns list of missing docs when strict=False."""
    from docio.core import _DOCIO_REGISTRY

    # Clear registry and add a fake entry
    original_registry = _DOCIO_REGISTRY.copy()
    _DOCIO_REGISTRY.clear()

    try:
        def fake_function():
            pass

        _DOCIO_REGISTRY.append((fake_function, "nonexistent.md"))

        # Should return the missing item without raising
        missing = validate_docs(strict=False)
        assert len(missing) == 1
        assert missing[0][0] == fake_function

        # Should raise when strict
        with pytest.raises(AssertionError, match="Missing docio documentation files"):
            validate_docs(strict=True)

    finally:
        # Restore original registry
        _DOCIO_REGISTRY.clear()
        _DOCIO_REGISTRY.extend(original_registry)

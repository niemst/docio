"""
Demo showing docio documenting itself.

This example demonstrates the real-world usage of docio by showing how
the library documents its own functions and classes.
"""

import sys
from docio import docio, get_doc, show_doc, validate_docs

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main():
    print("=" * 70)
    print("docio - Documentation Demo")
    print("=" * 70)
    print()

    # Show how help() displays short docstrings
    print("1. Using help() - shows short docstring:")
    print("-" * 70)
    help(docio)
    print()

    # Show the full Markdown documentation
    print("2. Using show_doc() - shows full Markdown documentation:")
    print("-" * 70)
    full_doc = show_doc(docio)
    print(full_doc[:500] + "..." if len(full_doc) > 500 else full_doc)
    print()

    # Demonstrate get_doc()
    print("3. Documentation for get_doc():")
    print("-" * 70)
    get_doc_content = show_doc(get_doc)
    print(get_doc_content[:400] + "..." if len(get_doc_content) > 400 else get_doc_content)
    print()

    # Show validation
    print("4. Validating documentation coverage:")
    print("-" * 70)
    try:
        missing = validate_docs(strict=False)
        if missing:
            print(f"Found {len(missing)} objects without documentation:")
            for obj, fname in missing:
                print(f"  - {obj.__module__}.{obj.__qualname__} -> {fname or '(auto)'}")
        else:
            print("✓ All @docio decorated objects have documentation!")
    except Exception as e:
        print(f"Validation error: {e}")
    print()

    # Show the registry
    print("5. Registered @docio objects:")
    print("-" * 70)
    from docio.core import _DOCIO_REGISTRY
    print(f"Total registered: {len(_DOCIO_REGISTRY)}")
    for obj, fname in _DOCIO_REGISTRY:
        obj_name = getattr(obj, "__qualname__", getattr(obj, "__name__", str(obj)))
        print(f"  - {obj_name} {f'(custom: {fname})' if fname else '(auto)'}")
    print()

    print("=" * 70)
    print("This demo shows docio documenting itself!")
    print("Check docs/docio/core/*.md to see the documentation source.")
    print("=" * 70)


if __name__ == "__main__":
    main()

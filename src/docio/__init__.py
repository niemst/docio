"""docio - External Markdown Documentation for Python Codebase"""

from .core import docio, get_doc, validate_docs, show_doc, scan_file_for_docio, auto_generate_stubs
from .exceptions import DocioError, DocNotFoundError

__version__ = "0.1.0"
__all__ = [
    "docio",
    "get_doc",
    "validate_docs",
    "show_doc",
    "scan_file_for_docio",
    "auto_generate_stubs",
    "DocioError",
    "DocNotFoundError",
]
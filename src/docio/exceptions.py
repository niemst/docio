"""
Exceptions for docio library.
"""


class DocioError(Exception):
    """Base exception for all docio-related errors."""
    pass


class DocNotFoundError(DocioError):
    """Raised when a documentation file cannot be found."""
    pass

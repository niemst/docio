"""Pytest configuration for docio tests."""

import logging
import sys


def pytest_configure(config):
    """Configure logging for tests."""
    # Enable docio logging during tests
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )

    # Set docio logger to DEBUG level
    docio_logger = logging.getLogger('docio')
    docio_logger.setLevel(logging.DEBUG)

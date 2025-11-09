"""Test file to check docio experience with IDE hover."""

import logging
import sys

# Enable logging for docio in this test file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logging.getLogger('docio').setLevel(logging.DEBUG)

from docio import docio


@docio
def calculate_sum(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    # Test the function
    result = calculate_sum(5, 3)
    print(f"Result: {result}")

    # Check the short docstring (what IDE hover shows)
    print(f"\nShort docstring (__doc__): {calculate_sum.__doc__}")

    # Show the full documentation
    from docio import show_doc
    print("\n" + "="*60)
    print("Full documentation (show_doc):")
    print("="*60)
    print(show_doc(calculate_sum))

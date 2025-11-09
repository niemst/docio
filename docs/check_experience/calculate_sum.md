---
source_file: check_experience.py
type: function
object_name: calculate_sum
---

# calculate_sum

A simple demonstration function that adds two integers together.

## Purpose

This function demonstrates the docio documentation system. When you hover over `calculate_sum` in your IDE, you should see the short description. When you call `show_doc(calculate_sum)`, you see this full Markdown documentation.

## Usage Examples

```python
# Basic usage
result = calculate_sum(5, 3)
print(result)  # Output: 8

# With variables
a = 10
b = 20
total = calculate_sum(a, b)  # Returns: 30
```

## When

**When to use:**
- When you need to add two integers
- When testing docio IDE integration

**When NOT to use:**
- For floating-point addition (use `float` types instead)
- For complex calculations (this is just a demo function)

## Details

The function simply returns the sum of two integers using the `+` operator. This is a trivial example to demonstrate how docio works:

1. The inline docstring is minimal (just the first paragraph)
2. The full documentation lives in this Markdown file
3. IDE hover shows the short version
4. `show_doc()` shows this complete documentation

## Examples

```python
from docio import show_doc

# Calculate sum
result = calculate_sum(100, 200)
assert result == 300

# View full documentation
print(show_doc(calculate_sum))
```

## Related Functions

- **Python built-in `sum()`**: For summing iterables
- **operator.add()**: For generic addition

## Notes

- This is a demonstration function, not for production use
- Check IDE hover to verify docio integration works
- The first paragraph of this file becomes the `__doc__` attribute

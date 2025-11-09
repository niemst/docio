# get_doc

Retrieve the documentation content for a Python object.

## Signature

```python
def get_doc(obj: Any, filename: Optional[str] = None) -> str
```

## Description

`get_doc()` retrieves the full Markdown documentation for any Python object,
regardless of whether it was decorated with `@docio`. It searches for
documentation files following the same discovery rules as the decorator.

## Parameters

- **obj** (Any): The Python object to get documentation for (class, function, method, etc.)
- **filename** (str, optional): Override the default file discovery with an explicit path

## Returns

- **str**: The full content of the documentation file

## Raises

- **DocNotFoundError**: If no documentation file can be found and the object has no docstring

## Behavior

1. **File Search**: Uses `_find_doc_file()` to locate the documentation
2. **Fallback**: If no file found, returns the original `__doc__` if available
3. **Reading**: Reads the file with UTF-8 encoding
4. **Caching**: Note that the `@docio` decorator caches this in `__docio_full__`,
   but calling `get_doc()` directly always reads from disk

## Examples

### Get Documentation for a Class

```python
from docio import get_doc

class MyClass:
    pass

doc = get_doc(MyClass)
print(doc)  # Prints full Markdown content
```

### Use Explicit Filename

```python
doc = get_doc(my_function, filename="custom/docs.md")
```

### Handle Missing Documentation

```python
from docio import DocNotFoundError

try:
    doc = get_doc(SomeClass)
except DocNotFoundError as e:
    print(f"No docs found: {e}")
```

## Use Cases

- Dynamically retrieve documentation at runtime
- Build documentation viewers or REPLs
- Generate combined documentation from multiple sources
- Inspect docs without using the decorator

## See Also

- `show_doc()` - User-friendly wrapper that checks cache first
- `docio()` - Decorator that uses this function internally
- `_find_doc_file()` - Internal function for file discovery

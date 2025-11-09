# show_doc

Display the full Markdown documentation for an object.

## Signature

```python
def show_doc(obj: Any) -> str
```

## Description

`show_doc()` is the user-facing function to display full documentation.
Unlike `get_doc()`, it first checks if the object has cached documentation
(from `@docio` decorator) before reading from disk.

## Parameters

- **obj** (Any): The object to show documentation for

## Returns

- **str**: Full Markdown documentation content

## How It Works

1. **Check cache**: If `obj.__docio_full__` exists, return it immediately
2. **Fallback**: Otherwise, call `get_doc(obj)` to read from file

This two-step approach is efficient for decorated objects (no disk I/O)
while still working for non-decorated objects.

## Examples

### Display Full Documentation

```python
from docio import docio, show_doc

@docio
class Calculator:
    pass

# Print the full Markdown docs
print(show_doc(Calculator))
```

### In a Jupyter Notebook

```python
from IPython.display import Markdown, display

display(Markdown(show_doc(Calculator)))
```

### Compare with help()

```python
# Short docstring (first paragraph)
help(Calculator)

# Full Markdown documentation
print(show_doc(Calculator))
```

## Use Cases

- **Interactive exploration**: Use in REPL or Jupyter notebooks
- **Documentation browsers**: Build tools that display rich docs
- **CLI tools**: Create `--help` flags that show full documentation
- **Debugging**: Quickly check what docs are loaded

## Best Practices

1. **Markdown rendering**: Pipe output to a Markdown viewer for formatted display
2. **Caching**: For decorated objects, this is very fast (no file I/O)
3. **Error handling**: Wrap in try/except to handle missing docs gracefully

## See Also

- `get_doc()` - Lower-level function that always reads from disk
- `docio()` - Decorator that caches docs in `__docio_full__`

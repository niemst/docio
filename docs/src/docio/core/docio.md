# @docio

Decorator to replace Python docstrings with external Markdown documentation.

## Overview

The `@docio` decorator is the core of the library. It allows you to write documentation
in separate Markdown files while keeping your Python code clean and focused.

## Syntax

```python
# Simple usage
@docio
class MyClass:
    pass

# With explicit filename
@docio(filename="custom/path.md")
def my_function():
    pass
```

## Parameters

- **obj** (optional): The object to decorate. When using `@docio` without parentheses,
  this is filled automatically.

- **filename** (str, optional): Explicit path to the documentation file, relative to
  the docs root (`docs/{package}/` or `src/{package}/_docs/`). If not provided, the file
  is auto-discovered based on module structure and object name.

## How It Works

1. **Registration**: When applied, the decorator registers the object in a global registry
2. **File Discovery**: Attempts to find the corresponding `.md` file
3. **Content Loading**: Reads and caches the full Markdown content
4. **Injection**: Sets both a short docstring (for `help()`) and caches full content

## File Discovery Rules

The decorator searches for documentation files:

1. **Explicit filename** (if provided via `filename` parameter)
2. **Auto-discovery** based on module structure:
   - `docs/{package_name}/{module_path}/{QualifiedName}.md`

**Philosophy**: Documentation lives in `docs/` only. No mixing with code in `src/`.

### Example Paths

For a class `Calculator` in package `myapp`, module `myapp.utils`:

```
docs/myapp/utils/Calculator.md
```

For docio itself (`docio.core.docio` function):

```
docs/docio/core/docio.md
```

For a method `Calculator.add`:

```
docs/myapp/utils/Calculator.add.md
docs/myapp/utils/add.md
```

## Behavior

### When Documentation File Exists

- Full Markdown content is cached in `obj.__docio_full__`
- Short docstring is extracted from first paragraph (max 200 chars) for `help()` output
- Object is added to validation registry

### When Documentation File Missing

- If original docstring exists: keeps it
- Otherwise: sets a placeholder "Documentation pending for ..."
- Object still added to registry (will fail validation in tests)

## Examples

### Basic Class Documentation

```python
from docio import docio

@docio
class DataProcessor:

    def process(self, data):
        return data.upper()
```

Create `docs/myapp/mymodule/DataProcessor.md`:

```markdown
# DataProcessor

A comprehensive data processor with full Markdown documentation.

## Methods

### process(data)
...
```

### Function with Custom Path

```python
@docio(filename="tutorials/my_function.md")
def complex_operation(x, y, z):
    pass
```

### Method Decoration

```python
class Pipeline:
    @docio(filename="Pipeline.run.md")
    def run(self, input_data):
        pass
```

## Best Practices

1. **First paragraph matters**: The first paragraph of your Markdown becomes the short docstring for `help()`, so make it concise and informative
2. **Consistent naming**: Follow `{QualifiedName}.md` convention for predictability
3. **Module organization**: Mirror your code structure in `docs/{package}/`
4. **Validation**: Use `validate_docs()` in tests to ensure coverage
5. **No code in docs**: Keep documentation purely in `.md` files - no inline docstrings needed

## See Also

- `get_doc()` - Retrieve documentation content
- `show_doc()` - Display full Markdown documentation
- `validate_docs()` - Ensure all decorated objects have docs

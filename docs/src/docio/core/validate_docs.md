# validate_docs

Validate that all `@docio` decorated objects have documentation files.

## Signature

```python
def validate_docs(strict: bool = True) -> list[tuple[Any, Optional[str]]]
```

## Description

`validate_docs()` is a testing utility that ensures all objects decorated with
`@docio` have corresponding documentation files. This is essential for maintaining
documentation coverage in CI/CD pipelines.

## Parameters

- **strict** (bool, default=True): If True, raises `AssertionError` when any docs are missing.
  If False, returns the list of missing docs without raising.

## Returns

- **list[tuple[Any, Optional[str]]]**: List of `(object, filename)` tuples for objects
  that are missing documentation. Empty list if all docs exist.

## Raises

- **AssertionError**: When `strict=True` and any decorated object is missing documentation.
  The error message lists all missing docs with their module paths and expected filenames.

## How It Works

1. **Iterate registry**: Loops through all objects in `_DOCIO_REGISTRY`
2. **Check each**: Attempts to call `get_doc()` for each object
3. **Collect failures**: Records any object that raises `DocNotFoundError`
4. **Report or raise**: Returns the list, or raises with a formatted error message

## Examples

### In Tests (Strict Mode)

```python
# tests/test_docio_coverage.py
from docio import validate_docs

def test_all_docs_exist():
    # Import all modules to register decorated objects
    import mypackage
    import mypackage.core
    import mypackage.utils

    # This will raise if any docs are missing
    validate_docs(strict=True)
```

### Non-Strict Check

```python
from docio import validate_docs

# Check but don't fail
missing = validate_docs(strict=False)

if missing:
    for obj, filename in missing:
        print(f"Missing docs for {obj.__name__}: {filename or '(auto)'}")
```

### In CI/CD

```yaml
# .github/workflows/ci.yml
- name: Check documentation coverage
  run: pytest tests/test_docio_coverage.py
```

## Error Message Format

When validation fails, you get a clear error message:

```
AssertionError: Missing docio documentation files:
  mypackage.core.DataProcessor -> (auto)
  mypackage.utils.helper_function -> custom/helper.md
  mypackage.models.User -> (auto)
```

## Best Practices

1. **Run in tests**: Always have a dedicated test that calls `validate_docs(strict=True)`
2. **Import all modules**: Make sure to import all modules before validation
3. **Pre-commit hook**: Add as a pre-commit hook to catch missing docs early
4. **Non-strict in scripts**: Use `strict=False` in utility scripts or  for reporting

## Use Cases

- **CI/CD enforcement**: Prevent merges when documentation is missing
- **Documentation audits**: Generate reports of documentation coverage
- **Pre-commit checks**: Validate docs before allowing commits
- **Development feedback**: Help developers know when docs are needed

## Integration Examples

### pytest

```python
def test_docio_coverage():
    import myapp
    validate_docs(strict=True)
```

### Pre-commit

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: docio-coverage
      name: Validate docio coverage
      entry: pytest tests/test_docio_coverage.py
      language: system
      pass_filenames: false
```

### Reporting Script

```python
# scripts/check_docs.py
from docio import validate_docs
import sys

missing = validate_docs(strict=False)

if missing:
    print(f"Found {len(missing)} objects without documentation:")
    for obj, fname in missing:
        print(f"  - {obj.__module__}.{obj.__qualname__}")
    sys.exit(1)
else:
    print("All documented! ✓")
```

## See Also

- `docio()` - Decorator that registers objects for validation
- `_DOCIO_REGISTRY` - Global registry of decorated objects
- `get_doc()` - Function used to check if docs exist

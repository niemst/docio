# docio

**Keep Your Code Clean. When Documentation is Worth Writing, Write it Well.**

Stop polluting your codebase with boilerplate docstrings. When something truly deserves documentation, use external Markdown files to do it properly.

## Why docio?

### The Problem with Docstrings

Look at typical Python code:

```python
def calculate_total(items: list[Item], tax_rate: float) -> Decimal:
    """Calculate the total price including tax.

    Args:
        items: List of items to calculate total for
        tax_rate: Tax rate as a decimal (e.g., 0.07 for 7%)

    Returns:
        Total price including tax

    Raises:
        ValueError: If tax_rate is negative
    """
    if tax_rate < 0:
        raise ValueError("Tax rate cannot be negative")
    subtotal = sum(item.price for item in items)
    return subtotal * (1 + tax_rate)
```

**What's wrong here?**

1. **Restates the obvious**: Function name and types already tell us everything
2. **More docs than code**: 10 lines of docstring, 4 lines of actual code
3. **Violates clean code**: The function signature IS the documentation
4. **Maintenance burden**: Change parameter name? Update docstring too
5. **Wastes LLM tokens**: If you are using LLM to read this, many tokens are used due to redundant text



### The docio Solution

**Step 1: Stop writing boilerplate docstrings**

```python
def calculate_total(items: list[Item], tax_rate: float) -> Decimal:
    if tax_rate < 0:
        raise ValueError("Tax rate cannot be negative")
    subtotal = sum(item.price for item in items)
    return subtotal * (1 + tax_rate)
```

Clean. Readable. Self-documenting through good names and types.

**Step 2: Add real documentation ONLY when it adds value**

For complex functionality, create `docs/src/myapp/billing.md`:

```markdown
# Billing System

## Tax Calculation Rules

Our tax system handles complex scenarios:

1. **Multi-jurisdiction**: Different rates for different regions
2. **Item-specific exemptions**: Food vs. luxury goods
3. **Business vs. consumer**: B2B transactions are tax-exempt

## Example: Complex Tax Scenario

\`\`\`python
# Restaurant order in California with mixed items
items = [
    Item("burger", 10.00, tax_exempt=False),
    Item("beer", 5.00, tax_exempt=False, alcohol_tax=0.05),
    Item("to_go_container", 0.50, tax_exempt=True)
]

total = calculate_total(items, region="CA")
# Applies: 7.25% sales tax + 5% alcohol tax + environmental fees
\`\`\`

See [CA Tax Board Guidelines](https://example.com) for details.
```

**This is valuable documentation.** It explains WHY, provides context, includes examples. Could even include diagrams/pictures etc.

**Benefits**:
- ✅ **Clean code**: Python files contain only code
- ✅ **Real docs when needed**: Rich Markdown for complex cases
- ✅ **Separate concerns**: Doc changes don't clutter code diffs
- ✅ **Still works with help()**: First paragraph auto-extracted

## Features

- **Auto-discovery**: Documentation files automatically matched to code structure
- **Dual visibility**: Concise `help()` output, full docs via `show_doc()`
- **Validation**: Ensure docs exist where they should with built-in testing
- **Production-ready**: Works in both development and installed packages
- **Type-safe**: Full type hints support (types in code, not docs)

## Installation

```bash
# From PyPI (when published)
pip install docio

# From source (development)
pip install -e .

# With dev dependencies
pip install -e ".[dev]"
```

## Quick Start

```python
from docio import docio

@docio
class DataProcessor:

    def __init__(self, config: dict, mode: str):
        self.config = config
        self.mode = mode
```

Create `docs/src/myapp/DataProcessor.md`:

```markdown
# DataProcessor

A data processor with comprehensive documentation.

## Quick Start
\`\`\`python
processor = DataProcessor(config={}, mode='fast')
result = processor.process(data)
\`\`\`

## Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| mode   | str  | 'fast' or 'thorough' |
| config | dict | Custom settings |

## Architecture Diagrams
[Include images, links, detailed examples...]
```

Now `help()` shows the first paragraph, `show_doc()` shows the full Markdown.

## Usage Patterns

### Basic decorator

```python
@docio
class MyClass:
    pass
```

Auto-discovers: `docs/src/{package_name}/{module_path}/MyClass.md`

The first paragraph of the Markdown file automatically becomes the short docstring for `help()`.

### Custom filename

```python
@docio(filename="custom/path/docs.md")
def my_function():
    pass
```

### Method decoration

```python
class Pipeline:
    @docio(filename="Pipeline.run.md")
    def run(self, data):
        pass
```

## Documentation Structure

Documentation mirrors your source code structure:

```
your-project/
├── src/
│   └── your_package/
│       ├── __init__.py
│       └── core.py           # Clean code, no docs clutter
├── tests/
│   └── test_core.py
├── docs/
│   ├── src/
│   │   └── your_package/
│   │       └── core/
│   │           └── MyClass.md
│   └── tests/
│       └── test_core/
│           └── TestClass.md
└── pyproject.toml
```

**Philosophy**: Documentation mirrors code structure. `src/pkg/module.py` → `docs/src/pkg/module/Class.md`

### File Discovery

For a class in `src/myapp/processor.py`:
```
docs/src/myapp/processor/DataProcessor.md
```

For a test in `tests/test_processor.py`:
```
docs/tests/test_processor/TestDataProcessor.md
```

**No package name prefix needed** - the structure directly mirrors your project layout.

### Auto-Generation

Don't create docs manually! Use the CLI:

```bash
# Generate stubs for missing docs
docio generate src/myapp/

# Scan to see what would be generated
docio scan src/

# Validate coverage
docio validate
```

### What about help()?

The first paragraph of your Markdown is automatically extracted and set as `__doc__`, so `help()` works even after installation.

## CLI Commands

### `docio generate`

Auto-generate documentation stubs for `@docio` decorated objects:

```bash
# Generate stubs for a file
docio generate src/myapp/processor.py

# Generate for entire directory
docio generate src/

# Dry-run (see what would be created)
docio generate --dry-run src/

# Use custom template directory
docio generate --template-dir=my_templates/ src/

# Exclude specific files or directories
docio generate --exclude "*/migrations/*" --exclude "*/generated/*" src/

# Include only specific patterns
docio generate --include "src/**/*.py" --include "tests/**/*.py" .
```

**Integration**: Add to IDE save hooks, pre-commit, or CI/CD.

#### Filtering Files with Exclude/Include Patterns

Control which files are processed using glob patterns:

**Exclude patterns** - Skip files matching these patterns:
```bash
# Exclude migrations and generated code
docio generate --exclude "*/migrations/*" --exclude "*_pb2.py" src/

# Multiple patterns can be specified
docio generate \
  --exclude "*/migrations/*" \
  --exclude "*/generated/*" \
  --exclude "*_pb2.py" \
  src/
```

**Include patterns** - Process only files matching these patterns:
```bash
# Only process files in src/ and tests/
docio generate --include "src/**/*.py" --include "tests/**/*.py" .
```

**Configuration file** - Set patterns in `pyproject.toml`:
```toml
[tool.docio]
exclude = [
    "*/migrations/*",
    "*/generated/*",
    "*_pb2.py",
    "*_pb2_grpc.py",
]

# Optional: only process specific patterns
include = [
    "src/**/*.py",
    "tests/**/*.py",
]
```

**Pattern matching rules:**
- Patterns use glob syntax (`*` matches any characters, `**` matches directories recursively)
- Paths are matched relative to project root
- Exclude patterns are checked first
- If include patterns are specified, files must match at least one include pattern
- Common patterns:
  - `*/migrations/*` - Exclude all migration directories
  - `*_pb2.py` - Exclude protobuf generated files
  - `src/**/*.py` - Include all Python files under src/

#### Documentation Templates

docio includes built-in templates for different object types:

- **`class.md`** - For classes
- **`function.md`** - For standalone functions
- **`method.md`** - For class methods
- **`test.md`** - For test classes/functions
- **`__init__.md`** - For `__init__.py` files (package documentation)
- **`module.md`** - For regular Python modules

Templates are automatically selected based on the decorated object type and file location. The built-in templates are located in `src/docio/stubs/` and provide comprehensive structure for real documentation.

**Custom Templates:**

To use your own templates, create a directory with template files:

```bash
my_templates/
├── class.md
├── function.md
├── method.md
├── test.md
├── __init__.md
└── module.md
```

Each template can use these placeholders:
- `{name}` - The name of the class/function/method
- `{method_name}` - The method name (for method templates)
- `{module_path}` - The module path (for module templates)
- `{source_file}` - Relative path to the source file
- `{obj_type}` - The object type (class/function/method/etc.)

**Use custom templates via CLI:**

```bash
docio generate --template-dir=my_templates/ src/
```

**Or configure in `pyproject.toml`:**

```toml
[tool.docio]
template_dir = "my_templates"

# CLI arguments take precedence over config file
```

### `docio scan`

Scan files for `@docio` decorators:

```bash
# Scan a file
docio scan src/myapp/processor.py

# Scan directory
docio scan src/

# Output shows decorator locations and custom filenames
```

### `docio validate`

Validate documentation coverage:

```bash
# Check coverage (non-strict)
docio validate

# Fail if docs missing (for CI)
docio validate --strict
```

Use in tests and CI to ensure all decorated objects have documentation.

## IDE Integration

Auto-generate stubs when saving Python files.

### Quick Setup

**VSCode** - Install [Run on Save](https://marketplace.visualstudio.com/items?itemName=emeraldwalk.RunOnSave):
```json
{
  "emeraldwalk.runonsave": {
    "commands": [{"match": "\\.py$", "cmd": "docio generate ${file}"}]
  }
}
```

**PyCharm** - File Watchers:
- Settings → Tools → File Watchers → Add
- Program: `docio`, Arguments: `generate $FilePath$`

**Pre-commit** - Example `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: docio-generate
        name: Generate docio stubs
        entry: docio generate
        language: system
        pass_filenames: true
        types: [python]

# Usage:
# git commit -m "Add feature"  # Generates stubs automatically
# SKIP=docio-generate git commit -m "message"  # Skip if needed
```

See [docs/ide-integration.md](docs/ide-integration.md) for complete setup guides (Vim, Emacs, Sublime, etc.).

## Testing & Validation

### Ensure all docs exist

```python
# tests/test_docio_coverage.py
from docio import validate_docs

def test_all_docio_have_docs():
    import your_package  # Import to register @docio decorators
    validate_docs(strict=True)  # Fails if any docs missing
```

### Run tests

```bash
pytest tests/
```

## API Reference

### `@docio`

Decorator to inject external documentation.

```python
def docio(
    obj=None,
    *,
    filename: Optional[str] = None
)
```

**Parameters:**
- `obj`: The object to decorate (auto when used without parens)
- `filename`: Optional custom documentation file path

The first paragraph of the Markdown file automatically becomes the short docstring.

### `get_doc(obj, filename=None)`

Get documentation content for an object.

**Returns:** String content of documentation file

**Raises:** `DocNotFoundError` if file not found

### `show_doc(obj)`

Display full Markdown documentation.

**Returns:** Full documentation content

### `validate_docs(strict=True)`

Validate all registered `@docio` objects have documentation.

**Parameters:**
- `strict`: If True, raises `AssertionError` on missing docs

**Returns:** List of `(object, filename)` tuples for missing docs

## Development

### Setup

```bash
# Clone repo
git clone https://github.com/yourusername/docio.git
cd docio

# Install with dev dependencies
pip install -e ".[dev]"
```

### Run tests

```bash
pytest -v
```

### Run linting

```bash
ruff check src/
mypy src/
```

### Run example

```bash
python examples/basic_usage.py
```

## Design Philosophy

### Documentation Should Not Be Mandatory Noise

Most codebases are filled with docstrings like:

```python
def get_user(user_id: int) -> User:
    """Get a user by ID.

    Args:
        user_id: The user ID

    Returns:
        The user object
    """
    return db.query(User).get(user_id)
```

**This is boilerplate.** The function signature already says everything. The docstring adds zero value while:
- Making code harder to scan
- Creating maintenance burden
- Violating clean code principles

### With docio: Clean Code First

```python
@docio  # Only if you need external docs
def get_user(user_id: int) -> User:
    return db.query(User).get(user_id)
```

**Or even better - no decorator at all if no docs are needed!**

### Real Documentation When It Matters

When you DO need documentation (complex algorithms, architectural decisions, API contracts), put it in Markdown:

```markdown
# User Authentication System

## Architecture

[Diagram showing auth flow]

## Security Considerations

- Passwords hashed with Argon2
- Session tokens expire after 24h
- Rate limiting: 5 attempts per minute

## Examples

\`\`\`python
# Complex usage scenario with full context
\`\`\`
```

This is **real documentation** that helps developers. Not boilerplate that restates the obvious.

## Examples

### Demo: docio Documents Itself

See [`examples/demo.py`](examples/demo.py) - the library uses `@docio` to document its own functions.

```bash
python examples/demo.py
```

This shows:
- `docs/src/docio/core/docio.md` - Full documentation for the `@docio` decorator
- `docs/src/docio/core/get_doc.md` - Documentation for `get_doc()`
- Auto-generated short docstrings for `help()`
- Full Markdown docs via `show_doc()`
- Validation ensuring all docs exist

Real-world usage, not artificial examples.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Custom License – Based on Creative Commons BY-NC-ND 4.0](LICENSE)

## Philosophy in Practice

### When to use docio

✅ **Use `@docio` when**:
- You have complex functionality requiring detailed explanation
- You need rich formatting (tables, diagrams, extensive examples)
- Documentation is significant and would clutter code
- You want to keep code changes separate from doc changes

❌ **Don't use `@docio` when**:
- The code is self-explanatory (most of the time!)
- A simple one-liner docstring would suffice
- You're just restating the function signature

### The goal

**Most code doesn't need documentation - it needs better names and clearer structure.**

For the parts that DO deserve documentation - make it excellent. Use rich Markdown. Include examples, diagrams, architectural context, and the WHY behind decisions.

If documentation is worth writing, it's worth writing well.

## FAQ

### Q: Isn't this just moving boilerplate to .md files?

No! The point is to **stop writing boilerplate entirely**. Only create `.md` files when you have real information to convey. Most functions don't need documentation - they need better names.

### Q: What about IDEs showing docstrings?

The first paragraph of your Markdown automatically becomes the docstring, so IDEs show it. But more importantly: if your function needs an IDE tooltip to be understood, maybe it needs a better name or simpler design.

### Q: Does this work with type checkers?

Yes! Type hints stay in code where they belong. Types are part of the contract, not documentation.

### Q: Performance impact?

Negligible. Docs are loaded once at import time and cached. Your code runs at a normal speed.

## Changelog

### 0.1.0 (Initial Release)

- Core `@docio` decorator
- Auto-discovery of documentation files
- Registry and validation system
- Dev and production mode support
- Comprehensive test suite

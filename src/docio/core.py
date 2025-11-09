"""
Core functionality for docio - decorator, registry, and documentation resolution.
"""

import ast
import inspect
import logging
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Callable, TypeVar, Union, Optional, List, Tuple
from functools import wraps

from .exceptions import DocNotFoundError

# Create logger for this module
logger = logging.getLogger(__name__)

# Type variable for generic decorator
F = TypeVar('F', bound=Callable[..., Any])

# Global registry of all decorated objects
_DOCIO_REGISTRY: list[tuple[Any, Optional[str]]] = []


def _get_package_root() -> Optional[Path]:
    """
    Find the package root directory.
    Returns the directory containing 'src/docio'.
    """
    try:
        # Get the directory where this module is located
        current_file = Path(__file__).resolve()
        # Go up to find the package root (src/docio -> src -> root)
        pkg_dir = current_file.parent  # docio
        src_dir = pkg_dir.parent  # src
        root_dir = src_dir.parent  # project root
        logger.debug(f"Package root: {root_dir}")
        return root_dir
    except Exception as e:
        logger.error(f"Failed to determine package root: {e}", exc_info=True)
        return None


def _find_doc_file(obj: Any, filename: Optional[str] = None) -> Optional[Path]:
    """
    Find the Markdown documentation file for an object.

    Documentation structure mirrors source structure:
    - src/mypackage/module.py -> docs/src/mypackage/module/ClassName.md
    - tests/test_foo.py -> docs/tests/test_foo/ClassName.md

    Args:
        obj: The object to find documentation for
        filename: Optional explicit filename override

    Returns:
        Path to the doc file if found, None otherwise
    """
    # Get object metadata
    module = inspect.getmodule(obj)
    if not module:
        logger.debug(f"Could not get module for {obj}")
        return None

    module_name = module.__name__
    qualname = getattr(obj, "__qualname__", getattr(obj, "__name__", None))

    if not qualname:
        logger.debug(f"No qualname found for {obj}")
        return None

    logger.debug(f"Looking for docs: module={module_name}, qualname={qualname}")

    root = _get_package_root()
    if not root:
        logger.debug("Could not determine package root")
        return None

    # If explicit filename provided, use it directly under docs/
    if filename:
        # Explicit filename is relative to docs/
        candidate = root / "docs" / filename
        logger.debug(f"Checking explicit filename: {candidate}")
        if candidate.exists():
            logger.info(f"Found doc file via explicit filename: {candidate}")
            return candidate
        logger.debug(f"Explicit filename not found: {candidate}")
        return None

    # Determine source location to mirror in docs/
    try:
        # Special handling for __main__ module
        if module.__name__ == '__main__':
            # Try to get the actual file path
            if hasattr(module, '__file__') and module.__file__:
                source_file = Path(module.__file__).resolve()
            else:
                return None
        else:
            source_file = Path(inspect.getfile(module))
        source_relative = source_file.relative_to(root)

        # Check if file is under src/, tests/, or examples/
        if source_relative.parts[0] in ('src', 'tests', 'examples'):
            base_dir = source_relative.parts[0]
            # Get the module path relative to src/tests/examples
            module_parts = source_relative.parts[1:]  # Skip 'src'/'tests'/'examples'
            # Remove .py extension and build module path
            if module_parts:
                module_parts = list(module_parts[:-1]) + [module_parts[-1].replace('.py', '')]
                module_path = "/".join(module_parts)
            else:
                module_path = ""
        else:
            # Fallback for files not in src/tests/examples
            base_dir = ""
            # For __main__ module, use the source file name instead of module name
            if module_name == '__main__':
                module_path = source_relative.stem
            else:
                module_path = module_name.replace(".", "/")
    except (ValueError, OSError):
        # If we can't determine source location, fall back to module name
        base_dir = ""
        module_path = module_name.replace(".", "/")

    # Try different naming conventions
    doc_filename_candidates = [
        f"{qualname}.md",  # ClassName.method.md or function.md
        f"{qualname.split('.')[-1]}.md",  # method.md (just the last part)
    ]

    # Build search paths
    docs_base = root / "docs"
    if base_dir:
        search_base = docs_base / base_dir
    else:
        search_base = docs_base

    if not search_base.exists():
        return None

    # Try with module path
    if module_path:
        for fname in doc_filename_candidates:
            candidate = search_base / module_path / fname
            logger.debug(f"Checking candidate: {candidate}")
            if candidate.exists():
                logger.info(f"Found doc file: {candidate}")
                return candidate

    # Try without module path (flat structure under base_dir)
    for fname in doc_filename_candidates:
        candidate = search_base / fname
        logger.debug(f"Checking flat candidate: {candidate}")
        if candidate.exists():
            logger.info(f"Found doc file: {candidate}")
            return candidate

    logger.debug(f"No doc file found for {qualname}")
    return None


def get_doc(obj: Any, filename: Optional[str] = None) -> str:
    """Retrieve the documentation content for a Python object.

    Args:
        obj: The object to get documentation for
        filename: Optional explicit filename override

    Returns:
        Documentation content as a string

    Raises:
        DocNotFoundError: If documentation file cannot be found
    """
    doc_path = _find_doc_file(obj, filename)

    if doc_path is None:
        # Return original docstring if available
        original_doc = inspect.getdoc(obj)
        if original_doc:
            logger.debug(f"Using original docstring for {obj}")
            return original_doc
        logger.warning(f"No documentation file found for {obj!r}")
        raise DocNotFoundError(
            f"No documentation file found for {obj!r}"
        )

    try:
        content = doc_path.read_text(encoding="utf-8")
        logger.debug(f"Successfully read doc file: {doc_path}")
        return content
    except Exception as e:
        logger.error(f"Failed to read documentation file {doc_path}: {e}")
        raise DocNotFoundError(
            f"Failed to read documentation file {doc_path}: {e}"
        )


def docio(
    obj: Optional[F] = None,
    *,
    filename: Optional[str] = None,
) -> Union[F, Callable[[F], F]]:
    """Decorator to replace Python docstrings with external Markdown documentation."""
    def decorator(o: F) -> F:
        obj_name = getattr(o, "__qualname__", getattr(o, "__name__", str(o)))
        logger.debug(f"Applying @docio to {obj_name}")

        # Register the object
        _DOCIO_REGISTRY.append((o, filename))

        # Try to load and inject documentation
        try:
            doc_content = get_doc(o, filename)
            # Set the full doc (for show_doc)
            o.__docio_full__ = doc_content
            logger.debug(f"Successfully loaded documentation for {obj_name}")

            # Strip YAML frontmatter if present (content between --- markers)
            content_for_extraction = doc_content
            if content_for_extraction.startswith('---'):
                # Find the closing --- marker
                parts = content_for_extraction.split('---', 2)
                if len(parts) >= 3:
                    # Skip the frontmatter and use the rest
                    content_for_extraction = parts[2].strip()

            # Extract first meaningful paragraph for help()
            # Skip title/heading lines and get the first real paragraph
            paragraphs = [p.strip() for p in content_for_extraction.split('\n\n') if p.strip()]
            first_para = ""
            for para in paragraphs:
                # Skip markdown headings
                if not para.startswith('#'):
                    first_para = para.replace('\n', ' ').strip()
                    break
            # If we only found headings, use the first one
            if not first_para and paragraphs:
                first_para = paragraphs[0].replace('\n', ' ').strip()
            # Limit length
            if len(first_para) > 200:
                first_para = first_para[:197] + "..."
            o.__doc__ = first_para if first_para else f"See documentation for {getattr(o, '__qualname__', o.__name__)}"
        except DocNotFoundError as e:
            # Keep original docstring or set minimal one
            logger.warning(f"Documentation not found for {obj_name}: {e}")
            if not o.__doc__:
                o.__doc__ = f"Documentation pending for {getattr(o, '__qualname__', o.__name__)}"
        except Exception as e:
            # Log any unexpected errors
            logger.error(f"Unexpected error loading documentation for {obj_name}: {e}", exc_info=True)
            if not o.__doc__:
                o.__doc__ = f"Documentation pending for {getattr(o, '__qualname__', o.__name__)}"

        return o

    # Handle both @docio and @docio(...) syntax
    if obj is None:
        return decorator
    else:
        return decorator(obj)


def validate_docs(strict: bool = True) -> list[tuple[Any, Optional[str]]]:
    """Validate that all `@docio` decorated objects have documentation files.

    Args:
        strict: If True, raise AssertionError on missing docs

    Returns:
        List of (object, filename) tuples for objects missing docs

    Raises:
        AssertionError: If strict=True and any docs are missing
    """
    missing = []

    for obj, fname in _DOCIO_REGISTRY:
        try:
            get_doc(obj, filename=fname)
        except DocNotFoundError:
            missing.append((obj, fname))

    if strict and missing:
        msgs = []
        for obj, fname in missing:
            mod = inspect.getmodule(obj)
            mod_name = mod.__name__ if mod else "unknown"
            obj_name = getattr(obj, "__qualname__", getattr(obj, "__name__", str(obj)))
            msgs.append(f"  {mod_name}.{obj_name} -> {fname or '(auto)'}")

        raise AssertionError(
            f"Missing docio documentation files:\n" + "\n".join(msgs)
        )

    return missing

def show_doc(obj: Any) -> str:
    # Try to get from cached full doc first
    if hasattr(obj, '__docio_full__'):
        return obj.__docio_full__

    # Otherwise fetch it
    return get_doc(obj)


def scan_file_for_docio(file_path: Union[str, Path]) -> List[Tuple[str, Optional[str], int, str]]:
    """
    Scan a Python file for @docio decorated classes and functions.

    Args:
        file_path: Path to Python file to scan

    Returns:
        List of tuples: (qualified_name, filename_override, line_number, object_type)
        where object_type is one of: 'class', 'function', 'method', 'test'
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logger.debug(f"File does not exist: {file_path}")
        return []

    try:
        content = file_path.read_text(encoding='utf-8')
        tree = ast.parse(content, filename=str(file_path))
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}", exc_info=True)
        return []

    # Check if this is a test file
    is_test_file = 'test' in file_path.stem.lower() or 'tests' in file_path.parts

    # Check if this is an __init__.py file
    is_init_file = file_path.name == '__init__.py'

    results = []

    def has_docio_decorator(node: Union[ast.ClassDef, ast.FunctionDef]) -> Tuple[bool, Optional[str]]:
        """Check if node has @docio decorator and extract filename if present."""
        for decorator in node.decorator_list:
            # Simple @docio
            if isinstance(decorator, ast.Name) and decorator.id == 'docio':
                return True, None
            # @docio(...) with possible filename argument
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id == 'docio':
                    # Check for filename keyword argument
                    for keyword in decorator.keywords:
                        if keyword.arg == 'filename' and isinstance(keyword.value, ast.Constant):
                            return True, keyword.value.value
                    return True, None
        return False, None

    def determine_object_type(node: Union[ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef],
                               parent: Optional[ast.AST]) -> str:
        """Determine the type of the decorated object."""
        # Special handling for __init__.py files
        if is_init_file:
            return '__init__'

        if is_test_file:
            return 'test'

        if isinstance(node, ast.ClassDef):
            return 'class'

        # Check if function is inside a class (method)
        if isinstance(parent, ast.ClassDef):
            return 'method'

        return 'function'

    # Walk through the tree with parent tracking
    for parent in ast.walk(tree):
        for node in ast.iter_child_nodes(parent):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                has_decorator, filename = has_docio_decorator(node)
                if has_decorator:
                    obj_type = determine_object_type(node, parent)
                    results.append((node.name, filename, node.lineno, obj_type))

    return results


def _should_process_file(
    file_path: Path,
    root: Path,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> bool:
    """
    Check if a file should be processed based on include/exclude patterns.

    Args:
        file_path: Path to the file to check
        root: Project root directory
        include_patterns: List of glob patterns to include (None means include all)
        exclude_patterns: List of glob patterns to exclude

    Returns:
        True if file should be processed, False otherwise
    """
    try:
        # Get path relative to root for pattern matching
        rel_path = file_path.relative_to(root)
        rel_path_str = str(rel_path).replace('\\', '/')
    except (ValueError, OSError):
        # If we can't get relative path, use the file path as-is
        rel_path_str = str(file_path).replace('\\', '/')

    # Check exclude patterns first
    if exclude_patterns:
        for pattern in exclude_patterns:
            if fnmatch(rel_path_str, pattern):
                return False

    # Check include patterns
    if include_patterns:
        for pattern in include_patterns:
            if fnmatch(rel_path_str, pattern):
                return True
        # If include patterns are specified but none matched, exclude the file
        return False

    # Default: include the file
    return True


def auto_generate_stubs(
    file_path: Union[str, Path],
    template_dir: Optional[Union[str, Path]] = None,
    exclude_patterns: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
    dry_run: bool = False
) -> List[Path]:
    """
    Auto-generate documentation stub files for @docio decorated objects in a file.

    Args:
        file_path: Path to Python file to scan
        template_dir: Directory containing template .md files (class.md, function.md, etc.).
                     If None, uses built-in templates from src/docio/stubs/
        exclude_patterns: List of glob patterns for files to exclude (e.g., ["*/migrations/*", "*/generated/*"])
        include_patterns: List of glob patterns for files to include (None means include all)
        dry_run: If True, return what would be created without actually creating files

    Returns:
        List of Path objects for created (or would-be-created) stub files
    """
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        return []

    # Get the package root
    root = _get_package_root()
    if not root:
        root = file_path.parent

    # Check if file should be processed
    if not _should_process_file(file_path, root, include_patterns, exclude_patterns):
        return []

    # Determine template directory
    if template_dir is None:
        # Use built-in templates
        template_dir = Path(__file__).parent / "stubs"
    else:
        template_dir = Path(template_dir)

    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory not found: {template_dir}")

    # Determine documentation structure mirroring source
    try:
        source_relative = file_path.relative_to(root)

        # Check if file is under src/, tests/, or examples/
        if source_relative.parts[0] in ('src', 'tests', 'examples'):
            base_dir = source_relative.parts[0]
            # Get the module path relative to src/tests/examples
            module_parts = source_relative.parts[1:]  # Skip 'src'/'tests'/'examples'
            # Remove .py extension and build module path
            if module_parts:
                module_parts = list(module_parts[:-1]) + [module_parts[-1].replace('.py', '')]
                module_path = "/".join(module_parts)
            else:
                module_path = ""
        else:
            # Fallback for files not in standard structure
            base_dir = ""
            module_path = file_path.stem  # Just the filename without extension
    except (ValueError, OSError):
        # If we can't determine relative path, use fallback
        base_dir = ""
        module_path = file_path.stem

    # Scan file for @docio decorators
    decorated_items = scan_file_for_docio(file_path)

    if not decorated_items:
        return []

    created_files = []

    # Build docs directory path mirroring source structure
    docs_base = root / "docs"
    if base_dir:
        docs_dir = docs_base / base_dir / module_path if module_path else docs_base / base_dir
    else:
        docs_dir = docs_base / module_path if module_path else docs_base

    for name, filename_override, lineno, obj_type in decorated_items:
        # Load appropriate template based on object type
        template_file = template_dir / f"{obj_type}.md"
        if not template_file.exists():
            # Fallback to function template
            template_file = template_dir / "function.md"

        if template_file.exists():
            template_content = template_file.read_text(encoding='utf-8')
        else:
            # Create minimal stub with just metadata if no template found
            template_content = """---
source_file: {source_file}
type: {obj_type}
object_name: {name}
---

# {name}
"""

        # Determine target file path
        if filename_override:
            # Use explicit filename relative to docs/
            target_path = docs_base / filename_override
        else:
            # Auto-discover based on name under appropriate docs directory
            target_path = docs_dir / f"{name}.md"

        # Check if file already exists
        if target_path.exists():
            continue

        # Get source file path relative to root for portability
        try:
            source_file_rel = file_path.relative_to(root)
        except (ValueError, OSError):
            source_file_rel = file_path

        # Generate stub content with available placeholders
        stub_content = template_content.format(
            name=name,
            obj_type=obj_type,
            method_name=name,  # For method templates
            module_path=module_path.replace('/', '.'),  # For module templates
            source_file=str(source_file_rel).replace('\\', '/')  # Normalize path separators
        )

        if not dry_run:
            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            # Write stub file
            target_path.write_text(stub_content, encoding='utf-8')

        created_files.append(target_path)

    return created_files


# Apply @docio decorators to our own functions
# (must be done after all functions are defined to avoid circular dependencies)
docio = docio(docio)
get_doc = docio(get_doc)
show_doc = docio(show_doc)
validate_docs = docio(validate_docs)

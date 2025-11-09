"""Command-line interface for docio."""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from .core import auto_generate_stubs, validate_docs, scan_file_for_docio


def load_config() -> Dict[str, Any]:
    """
    Load docio configuration from pyproject.toml if it exists.

    Returns:
        Dictionary with configuration values (empty if no config found)
    """
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # fallback for Python < 3.11
        except ImportError:
            return {}

    config_path = Path("pyproject.toml")
    if not config_path.exists():
        return {}

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
            return data.get("tool", {}).get("docio", {})
    except Exception:
        return {}


def cmd_generate(args: argparse.Namespace) -> int:
    # Load configuration from pyproject.toml
    config = load_config()

    files_to_process: List[Path] = []

    for path_str in args.paths:
        path = Path(path_str)

        if not path.exists():
            print(f"Error: Path does not exist: {path}", file=sys.stderr)
            return 1

        if path.is_file() and path.suffix == '.py':
            files_to_process.append(path)
        elif path.is_dir():
            # Recursively find all .py files
            files_to_process.extend(path.rglob('*.py'))
        else:
            print(f"Skipping non-Python file: {path}", file=sys.stderr)

    if not files_to_process:
        print("No Python files found to process.", file=sys.stderr)
        return 1

    # Parse exclude and include patterns (CLI args take precedence over config)
    exclude_patterns = args.exclude if hasattr(args, 'exclude') and args.exclude else config.get('exclude')
    include_patterns = args.include if hasattr(args, 'include') and args.include else config.get('include')

    # Get template directory (CLI arg takes precedence over config)
    template_dir = args.template_dir if hasattr(args, 'template_dir') and args.template_dir else config.get('template_dir')

    total_created = 0
    total_skipped = 0

    for file_path in files_to_process:
        try:
            created = auto_generate_stubs(
                file_path,
                template_dir=template_dir,
                exclude_patterns=exclude_patterns,
                include_patterns=include_patterns,
                dry_run=args.dry_run
            )

            if created:
                action = "Would create" if args.dry_run else "Created"
                for stub_path in created:
                    print(f"{action}: {stub_path}")
                    total_created += 1
            elif exclude_patterns or include_patterns:
                # File was skipped due to patterns
                total_skipped += 1

        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)

    if total_created == 0:
        print("No new documentation stubs needed.")
    else:
        action = "would be created" if args.dry_run else "created"
        print(f"\nTotal: {total_created} stub(s) {action}.")

    if total_skipped > 0:
        print(f"Skipped: {total_skipped} file(s) due to exclude/include patterns.")

    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    """Scan files for @docio decorators."""
    files_to_scan: List[Path] = []

    for path_str in args.paths:
        path = Path(path_str)

        if not path.exists():
            print(f"Error: Path does not exist: {path}", file=sys.stderr)
            return 1

        if path.is_file() and path.suffix == '.py':
            files_to_scan.append(path)
        elif path.is_dir():
            files_to_scan.extend(path.rglob('*.py'))

    if not files_to_scan:
        print("No Python files found.", file=sys.stderr)
        return 1

    total_found = 0

    for file_path in files_to_scan:
        try:
            items = scan_file_for_docio(file_path)
            if items:
                print(f"\n{file_path}:")
                for name, filename, lineno, obj_type in items:
                    filename_info = f" (filename={filename})" if filename else ""
                    print(f"  Line {lineno}: {name} [{obj_type}]{filename_info}")
                    total_found += 1
        except Exception as e:
            print(f"Error scanning {file_path}: {e}", file=sys.stderr)

    print(f"\nTotal: {total_found} @docio decorator(s) found.")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate documentation coverage."""
    # Import all modules to register decorators
    # User should run this from their project root
    try:
        missing = validate_docs(strict=False)

        if missing:
            print("Missing documentation files:", file=sys.stderr)
            for obj, filename in missing:
                obj_name = getattr(obj, "__qualname__", getattr(obj, "__name__", str(obj)))
                filename_info = f" (expected: {filename})" if filename else ""
                print(f"  - {obj_name}{filename_info}", file=sys.stderr)
            print(f"\nTotal: {len(missing)} object(s) missing documentation.", file=sys.stderr)
            return 1 if args.strict else 0
        else:
            print("✓ All @docio decorated objects have documentation!")
            return 0

    except Exception as e:
        print(f"Error during validation: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='docio',
        description='Documentation management tool for Python'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Generate command
    generate_parser = subparsers.add_parser(
        'generate',
        help='Generate documentation stub files for @docio decorators'
    )
    generate_parser.add_argument(
        'paths',
        nargs='+',
        help='Python file(s) or director(ies) to process'
    )
    generate_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without creating files'
    )
    generate_parser.add_argument(
        '--template-dir',
        type=str,
        help='Directory containing custom template .md files (class.md, function.md, etc.)'
    )
    generate_parser.add_argument(
        '--exclude',
        action='append',
        help='Glob pattern for files to exclude (can be specified multiple times, e.g., --exclude "*/migrations/*" --exclude "*/generated/*")'
    )
    generate_parser.add_argument(
        '--include',
        action='append',
        help='Glob pattern for files to include (can be specified multiple times). If specified, only matching files are processed.'
    )

    # Scan command
    scan_parser = subparsers.add_parser(
        'scan',
        help='Scan files for @docio decorators'
    )
    scan_parser.add_argument(
        'paths',
        nargs='+',
        help='Python file(s) or director(ies) to scan'
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate documentation coverage'
    )
    validate_parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit with error code if docs are missing'
    )

    args = parser.parse_args()

    if args.command == 'generate':
        return cmd_generate(args)
    elif args.command == 'scan':
        return cmd_scan(args)
    elif args.command == 'validate':
        return cmd_validate(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())

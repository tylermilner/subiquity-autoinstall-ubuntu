#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import pathlib
import sys

import yaml


DEFAULT_PATTERNS = (
    "**/user-data.yml",
    "**/user-data.yaml",
    "**/autoinstall*.yml",
    "**/autoinstall*.yaml",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate YAML syntax for Ubuntu autoinstall template files."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Optional explicit YAML files to validate. If omitted, default autoinstall patterns are used.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to search when no files are provided (default: current directory).",
    )
    return parser.parse_args()


def discover_template_files(root: pathlib.Path) -> list[pathlib.Path]:
    unique_paths: dict[str, pathlib.Path] = {}

    for pattern in DEFAULT_PATTERNS:
        for path in root.glob(pattern):
            if path.is_file():
                unique_paths[str(path.resolve())] = path

    return sorted(unique_paths.values(), key=lambda file_path: file_path.as_posix())


def format_error(path: pathlib.Path, error: Exception) -> str:
    if "GITHUB_ACTIONS" in os.environ:
        return f"::error file={path.as_posix()}::Invalid YAML syntax: {error}"
    return f"Invalid YAML syntax in {path.as_posix()}: {error}"


def main() -> int:
    args = parse_args()
    root = pathlib.Path(args.root).resolve()

    if args.files:
        files = [pathlib.Path(file_path) for file_path in args.files]
    else:
        files = discover_template_files(root)

    if not files:
        print("No autoinstall template YAML files found.")
        return 0

    print(f"Validating {len(files)} file(s):")
    for path in files:
        print(f" - {path.as_posix()}")

    has_errors = False

    for path in files:
        try:
            with path.open("r", encoding="utf-8") as handle:
                list(yaml.safe_load_all(handle))
        except (yaml.YAMLError, OSError) as error:
            has_errors = True
            print(format_error(path, error))

    if has_errors:
        return 1

    print("All autoinstall template YAML files are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys


DEFAULT_PATTERNS = (
    "**/user-data.yml",
    "**/user-data.yaml",
    "**/autoinstall*.yml",
    "**/autoinstall*.yaml",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate autoinstall templates using Subiquity's official "
            "validate-autoinstall-user-data.py script."
        )
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
    parser.add_argument(
        "--subiquity-dir",
        default="subiquity",
        help="Path to a local Subiquity checkout with dependencies installed.",
    )
    parser.add_argument(
        "--no-expect-cloudconfig",
        action="store_true",
        help="Pass through to Subiquity validator for non-cloud-config delivery format.",
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        action="count",
        default=0,
        help="Increase Subiquity validator verbosity (-v, -vv, -vvv).",
    )
    return parser.parse_args()


def discover_template_files(root: pathlib.Path) -> list[pathlib.Path]:
    unique_paths: dict[str, pathlib.Path] = {}
    for pattern in DEFAULT_PATTERNS:
        for path in root.glob(pattern):
            if path.is_file():
                unique_paths[str(path.resolve())] = path.resolve()
    return sorted(unique_paths.values(), key=lambda file_path: file_path.as_posix())


def validate_files(
    files: list[pathlib.Path],
    validator_path: pathlib.Path,
    no_expect_cloudconfig: bool,
    verbosity: int,
) -> int:
    has_errors = False

    for file_path in files:
        command = [sys.executable, str(validator_path)]
        if no_expect_cloudconfig:
            command.append("--no-expect-cloudconfig")
        command.extend(["-v"] * verbosity)
        command.append(str(file_path))

        print(f"Running Subiquity validator for: {file_path.as_posix()}")
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            has_errors = True
            if "GITHUB_ACTIONS" in os.environ:
                print(
                    f"::error file={file_path.as_posix()}::Subiquity autoinstall validation failed"
                )

    return 1 if has_errors else 0


def main() -> int:
    args = parse_args()
    root = pathlib.Path(args.root).resolve()
    subiquity_dir = pathlib.Path(args.subiquity_dir).resolve()
    validator_path = subiquity_dir / "scripts" / "validate-autoinstall-user-data.py"

    if not validator_path.is_file():
        print(
            "Subiquity validator script not found at "
            f"{validator_path.as_posix()}. "
            "Check --subiquity-dir and ensure Subiquity is checked out."
        )
        return 1

    if args.files:
        files = [pathlib.Path(file_path).resolve() for file_path in args.files]
    else:
        files = discover_template_files(root)

    if not files:
        print("No autoinstall template YAML files found.")
        return 0

    print(f"Validating {len(files)} file(s) with Subiquity official validator:")
    for path in files:
        print(f" - {path.as_posix()}")

    exit_code = validate_files(
        files=files,
        validator_path=validator_path,
        no_expect_cloudconfig=args.no_expect_cloudconfig,
        verbosity=args.verbosity,
    )

    if exit_code == 0:
        print("All autoinstall template YAML files passed Subiquity validation.")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

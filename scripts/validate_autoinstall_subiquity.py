#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
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


def is_within(path: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_files(
    files: list[pathlib.Path],
    validator_path: pathlib.Path,
    validator_working_dir: pathlib.Path,
    no_expect_cloudconfig: bool,
    verbosity: int,
) -> int:
    def run_validator(
        file_path: pathlib.Path,
        expect_cloudconfig: bool,
        legacy: bool,
    ) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(validator_path)]
        if not expect_cloudconfig:
            command.append("--no-expect-cloudconfig")
        if legacy:
            command.append("--legacy")
        command.extend(["-v"] * verbosity)
        command.append(str(file_path))

        return subprocess.run(
            command,
            check=False,
            cwd=validator_working_dir,
            text=True,
            capture_output=True,
        )

    def print_output(result: subprocess.CompletedProcess[str]) -> None:
        if result.stdout:
            print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
        if result.stderr:
            print(result.stderr, end="" if result.stderr.endswith("\n") else "\n")

    def get_autoinstall_data(file_path: pathlib.Path, expect_cloudconfig: bool) -> dict | None:
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
        except (OSError, yaml.YAMLError):
            return None

        if not isinstance(data, dict):
            return None

        if expect_cloudconfig:
            autoinstall_data = data.get("autoinstall")
            return autoinstall_data if isinstance(autoinstall_data, dict) else None

        if "autoinstall" in data and isinstance(data["autoinstall"], dict):
            return data["autoinstall"]

        return data

    def should_use_legacy(file_path: pathlib.Path, expect_cloudconfig: bool) -> tuple[bool, str | None]:
        autoinstall_data = get_autoinstall_data(file_path, expect_cloudconfig)
        if not autoinstall_data:
            return False, None

        source_data = autoinstall_data.get("source")
        if not isinstance(source_data, dict):
            return False, None

        source_id = source_data.get("id")
        if isinstance(source_id, str) and source_id != "synthesized":
            reason = (
                "Detected source.id='"
                f"{source_id}' "
                "(default/new Subiquity runtime validator is only compatible with 'synthesized' source id)."
            )
            return True, reason

        return False, None

    has_errors = False

    for file_path in files:
        print(f"Running Subiquity validator for: {file_path.as_posix()}")

        expect_cloudconfig = not no_expect_cloudconfig
        use_legacy, legacy_reason = should_use_legacy(file_path, expect_cloudconfig)
        if use_legacy and legacy_reason:
            print(f"Using --legacy for this file: {legacy_reason}")
            if "GITHUB_ACTIONS" in os.environ:
                print(
                    "::notice file="
                    f"{file_path.as_posix()}"
                    "::Using --legacy validation due to non-synthesized source.id."
                )

        result = run_validator(
            file_path=file_path,
            expect_cloudconfig=expect_cloudconfig,
            legacy=use_legacy,
        )
        print_output(result)

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
        files = [
            path
            for path in discover_template_files(root)
            if not is_within(path, subiquity_dir)
        ]

    if not files:
        print("No autoinstall template YAML files found.")
        return 0

    print(f"Validating {len(files)} file(s) with Subiquity official validator:")
    for path in files:
        print(f" - {path.as_posix()}")

    exit_code = validate_files(
        files=files,
        validator_path=validator_path,
        validator_working_dir=subiquity_dir,
        no_expect_cloudconfig=args.no_expect_cloudconfig,
        verbosity=args.verbosity,
    )

    if exit_code == 0:
        print("All autoinstall template YAML files passed Subiquity validation.")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

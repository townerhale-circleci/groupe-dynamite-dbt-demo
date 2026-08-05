"""Validate that dbt model SQL filenames are strict snake_case.

Fashion-retail dbt projects at scale rely on predictable, lowercase file names so
that `ref()` targets, generated docs, and CI stay consistent across Garage and
Dynamite domains. This check fails the build on any uppercase or otherwise
non-snake-case ``.sql`` model filename.

Strict snake_case here means: a lowercase letter followed by lowercase letters or
digits, with single underscores between segments (no leading/trailing underscore,
no double underscores, no uppercase, no hyphens/dots/spaces).

Usage:
    python scripts/validate_model_names.py [MODELS_DIR]

Exit code 0 when all model filenames are valid, 1 otherwise.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Anchored pattern for a strict snake_case stem.
_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


def is_snake_case(name: str) -> bool:
    """Return True if ``name`` (a filename stem) is strict snake_case."""
    return bool(_SNAKE_CASE.match(name))


def find_invalid_model_files(models_dir: str | Path) -> list[Path]:
    """Return every ``.sql`` file under ``models_dir`` whose stem is not snake_case.

    Only ``.sql`` files are considered (dbt models). YAML/Markdown/other files are
    ignored. The result is sorted for deterministic output.
    """
    root = Path(models_dir)
    invalid = [
        path
        for path in root.rglob("*.sql")
        if not is_snake_case(path.stem)
    ]
    return sorted(invalid)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail on uppercase / non-snake-case dbt model SQL filenames.",
    )
    parser.add_argument(
        "models_dir",
        nargs="?",
        default="models",
        help="Directory containing dbt model SQL files (default: models).",
    )
    args = parser.parse_args(argv)

    invalid = find_invalid_model_files(args.models_dir)
    if invalid:
        print("Invalid dbt model filenames (must be snake_case):")
        for path in invalid:
            print(f"  - {path}")
        print(f"{len(invalid)} invalid filename(s) found.")
        return 1

    print(f"All dbt model filenames under '{args.models_dir}' are valid snake_case.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

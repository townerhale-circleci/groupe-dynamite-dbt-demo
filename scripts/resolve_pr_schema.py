"""Resolve a safe, deterministic Snowflake schema name for a CI (PR) run.

Every pull-request build in CircleCI materialises its dbt models into its OWN
schema so concurrent PRs never collide and cleanup is unambiguous. This module
derives that schema name from CircleCI's built-in environment variables.

Resolution order (first usable wins):
    1. Numeric PR id from ``CIRCLE_PULL_REQUEST`` (the trailing ``/pull/<n>``)
       or, failing that, ``CIRCLE_PR_NUMBER``.
    2. The sanitized git branch (``CIRCLE_BRANCH``).
    3. The build number (``CIRCLE_BUILD_NUM``).

Safety guarantees (enforced regardless of source):
    * The name ALWAYS begins with ``PR_`` -- so it can never collide with the
      promotion schemas ``DEV`` / ``PROD`` and is trivially recognisable by the
      guarded cleanup macro/job.
    * The name contains ONLY ``A-Z``, ``0-9`` and ``_`` (uppercased).
    * The name never exceeds Snowflake's 255-char identifier limit.

Usage (CLI):
    python scripts/resolve_pr_schema.py
    # prints e.g. PR_42 to stdout; exit 1 (message on stderr) if unresolvable.
"""
from __future__ import annotations

import os
import re
import sys
from collections.abc import Mapping

# Snowflake unquoted/quoted identifiers are limited to 255 characters.
MAX_IDENTIFIER_LENGTH = 255

# Mandatory prefix. Guarantees the schema is never DEV/PROD and is recognisable
# as a disposable per-PR schema by the cleanup safeguards.
SCHEMA_PREFIX = "PR_"

# The full resolved schema must match this (uppercase, alnum + underscore).
SCHEMA_PATTERN = re.compile(r"^PR_[A-Z0-9_]+$")

# Reserved promotion schemas that must never be produced here.
RESERVED_SCHEMAS = frozenset({"DEV", "PROD"})

_PR_URL_TAIL = re.compile(r"/(\d+)/?$")
_NON_IDENTIFIER = re.compile(r"[^A-Z0-9]+")


def _clean_token(raw: str) -> str:
    """Uppercase ``raw`` and collapse any run of non ``A-Z0-9`` into ``_``.

    Leading/trailing underscores are stripped so we never emit ``PR__X`` or a
    trailing ``_``. Returns ``""`` when nothing survives sanitisation.
    """
    upper = raw.strip().upper()
    token = _NON_IDENTIFIER.sub("_", upper)
    return token.strip("_")


def _numeric_pr_token(env: Mapping[str, str]) -> str | None:
    """Return the numeric PR id from the PR URL or PR number, else None."""
    url = env.get("CIRCLE_PULL_REQUEST", "").strip()
    if url:
        match = _PR_URL_TAIL.search(url)
        if match:
            return match.group(1)

    number = env.get("CIRCLE_PR_NUMBER", "").strip()
    if number.isdigit():
        return number

    return None


def resolve_pr_schema(env: Mapping[str, str] | None = None) -> str:
    """Return the safe uppercase ``PR_...`` schema for the current CI run.

    Raises:
        ValueError: if none of PR id / branch / build number is available.
    """
    if env is None:
        env = os.environ

    token = _numeric_pr_token(env)

    if token is None:
        token = _clean_token(env.get("CIRCLE_BRANCH", "")) or None

    if token is None:
        build = _clean_token(env.get("CIRCLE_BUILD_NUM", "")) or None
        token = build

    if not token:
        raise ValueError(
            "Cannot resolve a PR schema: none of CIRCLE_PULL_REQUEST, "
            "CIRCLE_PR_NUMBER, CIRCLE_BRANCH or CIRCLE_BUILD_NUM was set."
        )

    schema = f"{SCHEMA_PREFIX}{token}"[:MAX_IDENTIFIER_LENGTH]

    # Defensive invariants (should hold by construction).
    assert schema.startswith(SCHEMA_PREFIX)
    assert schema not in RESERVED_SCHEMAS
    assert SCHEMA_PATTERN.match(schema), schema
    return schema


def main(argv: list[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    """CLI entry point: print the resolved schema, or error to stderr."""
    try:
        print(resolve_pr_schema(env))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

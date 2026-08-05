"""Unit tests for scripts/resolve_pr_schema.py.

The resolver derives a *deterministic, safe* Snowflake schema name for a CI run
from CircleCI environment variables. Contract:

* Prefer a numeric PR identifier (from the PR URL or PR number).
* Otherwise use the sanitized git branch.
* Otherwise fall back to the build number.
* The result ALWAYS begins with ``PR_``.
* The result contains ONLY ``A-Z``, ``0-9`` and ``_`` (uppercase).
* The result never exceeds Snowflake's identifier length limit (255).
* The result is never ``DEV`` or ``PROD`` (those are reserved for promotion).
"""
from __future__ import annotations

import pytest

from scripts.resolve_pr_schema import (
    MAX_IDENTIFIER_LENGTH,
    SCHEMA_PATTERN,
    resolve_pr_schema,
)


def test_prefers_numeric_pr_url() -> None:
    env = {
        "CIRCLE_PULL_REQUEST": "https://github.com/acme/repo/pull/42",
        "CIRCLE_BRANCH": "feature/some-branch",
        "CIRCLE_BUILD_NUM": "999",
    }
    assert resolve_pr_schema(env) == "PR_42"


def test_pr_url_takes_precedence_over_pr_number() -> None:
    env = {
        "CIRCLE_PULL_REQUEST": "https://github.com/acme/repo/pull/42",
        "CIRCLE_PR_NUMBER": "7",
    }
    assert resolve_pr_schema(env) == "PR_42"


def test_uses_pr_number_when_no_url() -> None:
    env = {
        "CIRCLE_PR_NUMBER": "7",
        "CIRCLE_BRANCH": "feature/some-branch",
        "CIRCLE_BUILD_NUM": "999",
    }
    assert resolve_pr_schema(env) == "PR_7"


def test_ignores_non_numeric_pr_url_tail_and_falls_back() -> None:
    # A PR URL without a trailing number is not a usable numeric PR id.
    env = {
        "CIRCLE_PULL_REQUEST": "https://github.com/acme/repo/pulls",
        "CIRCLE_BRANCH": "hotfix/login",
        "CIRCLE_BUILD_NUM": "5",
    }
    assert resolve_pr_schema(env) == "PR_HOTFIX_LOGIN"


def test_sanitizes_branch_uppercase_and_symbols() -> None:
    env = {"CIRCLE_BRANCH": "feature/Build-Demo"}
    assert resolve_pr_schema(env) == "PR_FEATURE_BUILD_DEMO"


def test_branch_with_unicode_and_punctuation_is_sanitized() -> None:
    env = {"CIRCLE_BRANCH": "fix/#123-café"}
    result = resolve_pr_schema(env)
    assert result == "PR_FIX_123_CAF"
    assert SCHEMA_PATTERN.match(result)


def test_falls_back_to_build_number() -> None:
    env = {"CIRCLE_BUILD_NUM": "987"}
    assert resolve_pr_schema(env) == "PR_987"


def test_empty_branch_falls_back_to_build_number() -> None:
    env = {"CIRCLE_BRANCH": "   ", "CIRCLE_BUILD_NUM": "987"}
    assert resolve_pr_schema(env) == "PR_987"


def test_branch_that_sanitizes_to_empty_falls_back_to_build_number() -> None:
    env = {"CIRCLE_BRANCH": "///", "CIRCLE_BUILD_NUM": "987"}
    assert resolve_pr_schema(env) == "PR_987"


def test_empty_pr_url_string_is_ignored() -> None:
    env = {"CIRCLE_PULL_REQUEST": "", "CIRCLE_BUILD_NUM": "12"}
    assert resolve_pr_schema(env) == "PR_12"


def test_raises_when_nothing_resolvable() -> None:
    with pytest.raises(ValueError):
        resolve_pr_schema({})


def test_result_always_starts_with_pr_prefix() -> None:
    for env in (
        {"CIRCLE_PULL_REQUEST": "https://github.com/a/b/pull/1"},
        {"CIRCLE_BRANCH": "main-ish"},
        {"CIRCLE_BUILD_NUM": "3"},
    ):
        assert resolve_pr_schema(env).startswith("PR_")


@pytest.mark.parametrize("bad_branch", ["dev", "DEV", "prod", "PROD"])
def test_never_returns_reserved_names(bad_branch: str) -> None:
    # Even if a branch is literally "dev"/"prod", the PR_ prefix keeps it safe.
    result = resolve_pr_schema({"CIRCLE_BRANCH": bad_branch})
    assert result not in {"DEV", "PROD"}
    assert result == f"PR_{bad_branch.upper()}"


def test_enforces_snowflake_identifier_length() -> None:
    env = {"CIRCLE_BRANCH": "a" * 500}
    result = resolve_pr_schema(env)
    assert len(result) <= MAX_IDENTIFIER_LENGTH
    assert result.startswith("PR_")


def test_only_allowed_characters_for_all_sources() -> None:
    for env in (
        {"CIRCLE_PULL_REQUEST": "https://github.com/a/b/pull/42"},
        {"CIRCLE_BRANCH": "Feature/Weird Name!!"},
        {"CIRCLE_BUILD_NUM": "77"},
    ):
        assert SCHEMA_PATTERN.match(resolve_pr_schema(env))


def test_main_prints_schema(capsys) -> None:
    from scripts.resolve_pr_schema import main

    exit_code = main(env={"CIRCLE_BRANCH": "feature/x"})
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "PR_FEATURE_X"


def test_main_errors_when_unresolvable(capsys) -> None:
    from scripts.resolve_pr_schema import main

    exit_code = main(env={})
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out.strip() == ""
    assert captured.err.strip() != ""

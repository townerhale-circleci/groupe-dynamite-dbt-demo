"""Unit tests for scripts/validate_model_names.py.

The validator enforces that every dbt model SQL filename is strict snake_case
(lowercase letters/digits separated by single underscores). It must fail on
uppercase or otherwise non-snake-case filenames.
"""
from __future__ import annotations

import pytest

from scripts.validate_model_names import (
    find_invalid_model_files,
    is_snake_case,
    main,
)


@pytest.mark.parametrize(
    "name",
    [
        "stg_orders",
        "fct_daily_sales",
        "fct_store_performance",
        "stg_order_items",
        "model1",
        "a",
        "brand2sales",
    ],
)
def test_is_snake_case_accepts_valid_names(name: str) -> None:
    assert is_snake_case(name) is True


@pytest.mark.parametrize(
    "name",
    [
        "StgOrders",          # PascalCase
        "stgOrders",          # camelCase
        "STG_ORDERS",         # SCREAMING_CASE
        "Stg_Orders",         # Title_Case
        "stg-orders",         # hyphen
        "stg orders",         # space
        "stg__orders",        # double underscore
        "_stg_orders",        # leading underscore
        "stg_orders_",        # trailing underscore
        "1stg",               # leading digit
        "",                   # empty
        "stg.orders",         # dot
    ],
)
def test_is_snake_case_rejects_invalid_names(name: str) -> None:
    assert is_snake_case(name) is False


def _write(path, text: str = "select 1 as id\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_find_invalid_model_files_returns_only_bad_sql(tmp_path) -> None:
    models = tmp_path / "models"
    _write(models / "staging" / "stg_orders.sql")
    _write(models / "marts" / "fct_daily_sales.sql")
    _write(models / "staging" / "StgReturns.sql")       # bad: casing
    _write(models / "marts" / "fct-return-rates.sql")   # bad: hyphen

    invalid = find_invalid_model_files(models)
    invalid_names = sorted(p.name for p in invalid)

    assert invalid_names == ["StgReturns.sql", "fct-return-rates.sql"]


def test_find_invalid_model_files_ignores_non_sql_and_yaml(tmp_path) -> None:
    models = tmp_path / "models"
    _write(models / "stg_orders.sql")
    _write(models / "_staging.yml", "version: 2\n")     # yml config, not a model
    _write(models / "README.md", "# docs\n")

    assert find_invalid_model_files(models) == []


def test_find_invalid_model_files_empty_when_all_valid(tmp_path) -> None:
    models = tmp_path / "models"
    _write(models / "staging" / "stg_customers.sql")
    _write(models / "marts" / "fct_inventory_availability.sql")

    assert find_invalid_model_files(models) == []


def test_main_returns_nonzero_when_invalid(tmp_path, capsys) -> None:
    models = tmp_path / "models"
    _write(models / "BadModel.sql")

    exit_code = main([str(models)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "BadModel.sql" in captured.out


def test_main_returns_zero_when_clean(tmp_path, capsys) -> None:
    models = tmp_path / "models"
    _write(models / "stg_orders.sql")

    exit_code = main([str(models)])

    assert exit_code == 0

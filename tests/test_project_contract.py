"""Offline validation of the dbt project contract (no Snowflake required).

Guards the structural invariants a reviewer would otherwise only catch by
running dbt against a warehouse: naming, documentation coverage, env-var-only
credentials, and presence of the required marts and bootstrap templates.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from scripts.validate_model_names import find_invalid_model_files

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / "models"
SEEDS_DIR = PROJECT_ROOT / "seeds"

SENSITIVE_PROFILE_KEYS = {
    "account",
    "user",
    "password",
    "role",
    "warehouse",
    "database",
    "schema",
}

REQUIRED_MARTS = {
    "fct_daily_sales",
    "fct_store_performance",
    "fct_inventory_availability",
    "fct_return_rates",
}


def _load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_dbt_project_core_settings() -> None:
    project = _load_yaml(PROJECT_ROOT / "dbt_project.yml")
    assert project["name"] == "groupe_dynamite"
    assert project["profile"] == "groupe_dynamite"
    assert project["config-version"] == 2
    assert "models" in project["model-paths"]
    assert "seeds" in project["seed-paths"]


def test_profiles_use_only_env_vars() -> None:
    profiles = _load_yaml(PROJECT_ROOT / "profiles.yml")
    output = profiles["groupe_dynamite"]["outputs"]["dev"]
    assert output["type"] == "snowflake"
    for key in SENSITIVE_PROFILE_KEYS:
        value = output[key]
        assert isinstance(value, str)
        assert "env_var(" in value, f"{key} is not sourced from an env var"


def test_target_schema_comes_from_dbt_schema_env_var() -> None:
    profiles = _load_yaml(PROJECT_ROOT / "profiles.yml")
    schema_value = profiles["groupe_dynamite"]["outputs"]["dev"]["schema"]
    assert "DBT_SCHEMA" in schema_value


def test_all_model_filenames_are_snake_case() -> None:
    assert find_invalid_model_files(MODELS_DIR) == []


def test_required_marts_exist() -> None:
    marts = {p.stem for p in (MODELS_DIR / "marts").glob("*.sql")}
    missing = REQUIRED_MARTS - marts
    assert not missing, f"missing marts: {sorted(missing)}"


def test_every_model_is_documented() -> None:
    documented: set[str] = set()
    for yml in MODELS_DIR.rglob("_*.yml"):
        parsed = _load_yaml(yml) or {}
        for model in parsed.get("models", []):
            documented.add(model["name"])

    on_disk = {p.stem for p in MODELS_DIR.rglob("*.sql")}
    undocumented = on_disk - documented
    dangling = documented - on_disk
    assert not undocumented, f"models missing docs: {sorted(undocumented)}"
    assert not dangling, f"docs without model files: {sorted(dangling)}"


def test_every_seed_is_documented() -> None:
    parsed = _load_yaml(SEEDS_DIR / "_seeds.yml") or {}
    documented = {seed["name"] for seed in parsed.get("seeds", [])}
    on_disk = {p.stem for p in SEEDS_DIR.glob("*.csv")}
    assert documented == on_disk, (
        f"seed doc mismatch: docs={sorted(documented)} files={sorted(on_disk)}"
    )


def test_non_negative_generic_test_macro_exists() -> None:
    macro = PROJECT_ROOT / "macros" / "test_non_negative.sql"
    text = macro.read_text(encoding="utf-8")
    assert "{% test non_negative(" in text


def test_env_is_gitignored_and_example_has_no_secret() -> None:
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore

    example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "DBT_SCHEMA" in example
    # No real .env should be committed alongside the project.
    assert not (PROJECT_ROOT / ".env").exists()


def test_sqlfluff_configured_for_snowflake() -> None:
    text = (PROJECT_ROOT / ".sqlfluff").read_text(encoding="utf-8")
    assert "dialect = snowflake" in text


def test_bootstrap_and_teardown_templates_are_prefixed_and_idempotent() -> None:
    bootstrap = (PROJECT_ROOT / "SQL" / "bootstrap.sql").read_text(encoding="utf-8")
    teardown = (PROJECT_ROOT / "SQL" / "teardown.sql").read_text(encoding="utf-8")

    assert "GROUPE_DYNAMITE_DEMO" in bootstrap
    assert "GROUPE_DYNAMITE_DEMO" in teardown
    assert "IF NOT EXISTS" in bootstrap
    assert "IF EXISTS" in teardown


def test_bootstrap_can_create_all_ci_target_schemas() -> None:
    bootstrap = (PROJECT_ROOT / "SQL" / "bootstrap.sql").read_text(encoding="utf-8")

    for schema in ("RAW", "DEV", "PROD"):
        assert (
            f"CREATE SCHEMA IF NOT EXISTS GROUPE_DYNAMITE_DEMO.{schema}"
            in bootstrap
        )
    assert (
        "GRANT CREATE SCHEMA ON DATABASE GROUPE_DYNAMITE_DEMO "
        "TO ROLE GROUPE_DYNAMITE_DEMO_ROLE"
    ) in " ".join(bootstrap.split())

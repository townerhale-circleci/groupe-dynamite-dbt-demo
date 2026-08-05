"""Offline contract tests for .circleci/config.yml.

These parse the YAML and assert the *semantics* the CI must guarantee -- job
naming, context placement, expression-based branch selection, the approval
hold, artifact preservation, cleanup dependency/safeguards, and the PR schema
resolver wiring. They run without CircleCI or Snowflake.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / ".circleci" / "config.yml"

BRANCH_PIPELINE_VALUE = "<< pipeline.git.branch >>"

OFFLINE_JOBS = {"validate-model-names", "python-tests", "sqlfluff"}
SNOWFLAKE_JOBS = {
    "dbt-compile",
    "dbt-pr-build",
    "dbt-pr-cleanup",
    "dbt-main-dev",
    "dbt-main-prod",
}
SNOWFLAKE_CONTEXT = "snowflake-dbt-demo"

REQUIRED_ARTIFACT_PATHS = {
    "target/manifest.json",
    "target/run_results.json",
    "target/compiled",
    "logs",
}


@pytest.fixture(scope="module")
def raw_text() -> str:
    return CONFIG_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


# --- helpers ---------------------------------------------------------------

def _run_commands(job: dict) -> list[str]:
    """Return the shell text of every `run` step in a job."""
    commands: list[str] = []
    for step in job.get("steps", []):
        if isinstance(step, dict) and "run" in step:
            run = step["run"]
            commands.append(run if isinstance(run, str) else run.get("command", ""))
    return commands


def _step_kinds(job: dict) -> list[str]:
    """Return an ordered list of step identifiers (command name or step key)."""
    kinds: list[str] = []
    for step in job.get("steps", []):
        if isinstance(step, str):
            kinds.append(step)
        elif isinstance(step, dict):
            kinds.append(next(iter(step)))
    return kinds


def _workflow_job_entry(config: dict, workflow: str, job_name: str) -> dict:
    for entry in config["workflows"][workflow]["jobs"]:
        if isinstance(entry, dict) and job_name in entry:
            return entry[job_name]
        if isinstance(entry, str) and entry == job_name:
            return {}
    raise AssertionError(f"{job_name} not found in workflow {workflow}")


def _workflow_job_names(config: dict, workflow: str) -> set[str]:
    names: set[str] = set()
    for entry in config["workflows"][workflow]["jobs"]:
        names.add(next(iter(entry)) if isinstance(entry, dict) else entry)
    return names


# --- core config semantics -------------------------------------------------

def test_config_version_is_2_1(config: dict) -> None:
    assert config["version"] == 2.1


def test_no_orbs_or_dynamic_config(config: dict) -> None:
    assert "orbs" not in config
    assert config.get("setup") in (None, False)


def test_executor_uses_cimg_python_312(config: dict) -> None:
    image = config["executors"]["python"]["docker"][0]["image"]
    assert image == "cimg/python:3.12"


def test_setup_uses_uv_sync_frozen(config: dict) -> None:
    steps = config["commands"]["setup"]["steps"]
    commands = " ".join(
        step["run"] if isinstance(step["run"], str) else step["run"]["command"]
        for step in steps
        if isinstance(step, dict) and "run" in step
    )
    assert "uv sync --frozen" in commands
    assert "install uv" in commands.lower() or "pip install uv" in commands


def test_all_expected_jobs_exist(config: dict) -> None:
    expected = OFFLINE_JOBS | SNOWFLAKE_JOBS
    assert expected.issubset(set(config["jobs"]))


# --- context placement ------------------------------------------------------

def test_snowflake_context_only_on_credentialed_jobs(config: dict) -> None:
    for workflow in ("pr", "main"):
        for entry in config["workflows"][workflow]["jobs"]:
            if not isinstance(entry, dict):
                continue
            job_name = next(iter(entry))
            spec = entry[job_name] or {}
            contexts = spec.get("context", [])
            if isinstance(contexts, str):
                contexts = [contexts]
            if job_name in SNOWFLAKE_JOBS:
                assert SNOWFLAKE_CONTEXT in contexts, f"{job_name} missing context"
            else:
                assert SNOWFLAKE_CONTEXT not in contexts, (
                    f"{job_name} must not receive Snowflake context"
                )


def test_offline_gates_complete_before_credentialed_compile(config: dict) -> None:
    compile_job = _workflow_job_entry(config, "pr", "dbt-compile")
    assert set(compile_job["requires"]) == OFFLINE_JOBS


def test_offline_jobs_never_get_context(config: dict) -> None:
    for job_name in OFFLINE_JOBS:
        for workflow in ("pr", "main"):
            if job_name in _workflow_job_names(config, workflow):
                spec = _workflow_job_entry(config, workflow, job_name)
                assert "context" not in (spec or {})


# --- expression-based branch selection (no deprecated filter maps) ----------

def test_no_deprecated_branch_filter_maps(raw_text: str) -> None:
    assert "filters:" not in raw_text
    assert "branches:" not in raw_text


def test_pr_workflow_excludes_main_via_expression(config: dict) -> None:
    when = config["workflows"]["pr"]["when"]
    assert when == {"not": {"equal": ["main", BRANCH_PIPELINE_VALUE]}}


def test_main_workflow_only_on_main_via_expression(config: dict) -> None:
    when = config["workflows"]["main"]["when"]
    assert when == {"equal": ["main", BRANCH_PIPELINE_VALUE]}


def test_config_compilation_only_depends_on_branch(raw_text: str) -> None:
    # GitHub App compatibility: config-compile-time conditions must use only the
    # git branch, never PR-only pipeline event fields.
    for forbidden in (
        "pipeline.event",
        "pipeline.trigger",
        "pipeline.git.pull_request",
    ):
        assert forbidden not in raw_text


def test_pr_and_main_workflows_are_disjoint(config: dict) -> None:
    pr_jobs = _workflow_job_names(config, "pr")
    main_jobs = _workflow_job_names(config, "main")
    assert "dbt-main-dev" not in pr_jobs
    assert "dbt-main-prod" not in pr_jobs
    assert "dbt-pr-build" not in main_jobs
    assert "dbt-pr-cleanup" not in main_jobs


# --- approval hold ----------------------------------------------------------

def test_manual_approval_hold_between_dev_and_prod(config: dict) -> None:
    hold = _workflow_job_entry(config, "main", "hold-promote-prod")
    assert hold["type"] == "approval"
    assert hold["requires"] == ["dbt-main-dev"]

    prod = _workflow_job_entry(config, "main", "dbt-main-prod")
    assert prod["requires"] == ["hold-promote-prod"]


def test_main_dev_and_prod_use_reserved_schemas(config: dict) -> None:
    assert (
        config["jobs"]["dbt-main-dev"]["environment"]["DBT_SCHEMA"]
        == "GROUPE_DYNAMITE_DEMO_DEV"
    )
    assert (
        config["jobs"]["dbt-main-prod"]["environment"]["DBT_SCHEMA"]
        == "GROUPE_DYNAMITE_DEMO_PROD"
    )


# --- artifact preservation --------------------------------------------------

def test_persist_command_covers_all_required_paths(config: dict) -> None:
    steps = config["commands"]["persist_dbt_artifacts"]["steps"]
    artifact_steps = [
        step["store_artifacts"]
        for step in steps
        if isinstance(step, dict) and "store_artifacts" in step
    ]
    paths = {step["path"] for step in artifact_steps}
    assert REQUIRED_ARTIFACT_PATHS.issubset(paths)
    assert all(step["when"] == "always" for step in artifact_steps)


@pytest.mark.parametrize("job_name", ["dbt-pr-build", "dbt-main-dev", "dbt-main-prod"])
def test_artifacts_persisted_after_dbt_build(config: dict, job_name: str) -> None:
    kinds = _step_kinds(config["jobs"][job_name])
    assert "persist_dbt_artifacts" in kinds
    # Artifact persistence must come AFTER the build step so failures still
    # upload artifacts (store_artifacts runs after a failed step).
    build_index = next(
        i
        for i, step in enumerate(config["jobs"][job_name]["steps"])
        if isinstance(step, dict)
        and "run" in step
        and "dbt build" in step["run"].get("command", "")
    )
    assert kinds.index("persist_dbt_artifacts") > build_index


def test_pytest_junit_results_stored(config: dict) -> None:
    job = config["jobs"]["python-tests"]
    commands = " ".join(_run_commands(job))
    assert "--junitxml=" in commands
    kinds = _step_kinds(job)
    assert "store_test_results" in kinds


# --- cleanup dependency + safeguards ---------------------------------------

def test_cleanup_uses_flexible_post_build_requires(config: dict) -> None:
    cleanup = _workflow_job_entry(config, "pr", "dbt-pr-cleanup")
    requires = cleanup["requires"]
    # Cleanup runs after every state in which a build could have created a
    # schema, but not `not_run` (offline-gate failures create no schema).
    assert requires == [
        {
            "dbt-pr-build": [
                "success",
                "failed",
                "canceled",
                "unauthorized",
            ]
        }
    ]


def test_cleanup_invokes_guarded_drop_macro(config: dict) -> None:
    commands = " ".join(_run_commands(config["jobs"]["dbt-pr-cleanup"]))
    assert "drop_pr_schema" in commands
    assert "resolve_pr_schema.py" in commands


def test_pr_build_resolves_schema_and_builds(config: dict) -> None:
    commands = " ".join(_run_commands(config["jobs"]["dbt-pr-build"]))
    assert "resolve_pr_schema.py" in commands
    assert "dbt build" in commands


def test_drop_macro_is_guarded_to_pr_schemas() -> None:
    macro = (PROJECT_ROOT / "macros" / "drop_pr_schema.sql").read_text(encoding="utf-8")
    assert "startswith('GROUPE_DYNAMITE_DEMO_PR_')" in macro
    assert "raise_compiler_error" in macro
    assert "'GROUPE_DYNAMITE_DEMO_PROD'" in macro
    assert "drop schema if exists" in macro


def test_distinct_dbt_compile_job_resolves_pr_schema(config: dict) -> None:
    commands = " ".join(_run_commands(config["jobs"]["dbt-compile"]))
    assert "resolve_pr_schema.py" in commands
    assert "dbt compile" in commands
    assert "dbt build" not in commands

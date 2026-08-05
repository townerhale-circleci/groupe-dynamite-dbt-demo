# groupe-dynamite-dbt-demo

Synthetic fashion-retail **dbt Core + Snowflake** demo for Groupe Dynamite
(Garage & Dynamite brands). It models sales across **store, ecommerce, and
mobile** channels plus inventory and returns, and demonstrates the tooling and
conventions for a migration from dbt Cloud to dbt Core.

> All data is small, synthetic, and referentially consistent. No secrets are
> stored in the repo; the dbt profile reads **only environment variables**.

## What's inside

- **Seeds** (`seeds/`) — synthetic raw sources: brands, products/SKUs, stores,
  customers, orders, order_items, returns, inventory.
- **Staging models** (`models/staging/`) — typed, cleaned 1:1 views over seeds.
- **Marts** (`models/marts/`) — `fct_daily_sales`, `fct_store_performance`,
  `fct_inventory_availability`, `fct_return_rates`.
- **Tests** — dbt generic tests (`not_null`, `unique`, `relationships`,
  `accepted_values`, and a custom `non_negative` retail rule) plus offline
  `pytest` suites for seed integrity and the project contract.
- **Tooling** — `scripts/validate_model_names.py` (snake_case filename gate),
  SQLFluff config (Snowflake dialect), and `SQL/` bootstrap/teardown templates.

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
```

## Local validation (offline — no Snowflake required)

```bash
# 1. Python unit + integrity + contract tests
uv run pytest

# 2. Model-name convention gate (snake_case)
uv run python scripts/validate_model_names.py models

# 3. SQL style/lint (Snowflake dialect, offline Jinja templater)
uv run sqlfluff lint models

# 4. dbt parse (validates project/model graph; no warehouse connection)
#    dbt loads the profile, so export throwaway values first:
export DBT_SNOWFLAKE_ACCOUNT=x DBT_SNOWFLAKE_USER=x DBT_SNOWFLAKE_PASSWORD=x \
       DBT_SNOWFLAKE_ROLE=x DBT_SNOWFLAKE_WAREHOUSE=x \
       DBT_SNOWFLAKE_DATABASE=x DBT_SCHEMA=ANALYTICS
uv run dbt parse --profiles-dir . --project-dir .
```

## CircleCI (`.circleci/config.yml`)

Two branch-selected workflows (chosen by modern expression-based `when:` blocks
on `<< pipeline.git.branch >>`, not deprecated branch filter maps):

- **`pr`** — every branch except `main`. Offline gates run first with **no**
  credentials: `validate-model-names` (snake_case gate), `python-tests`
  (pytest, JUnit stored), and `sqlfluff`. The credentialed `dbt-compile` job
  performs a real Snowflake compile, then `dbt-pr-build` runs a **real**
  `dbt build` into a disposable per-PR schema, and `dbt-pr-cleanup` drops it.
- **`main`** — `main` only. `dbt-main-dev` builds into `DBT_SCHEMA=DEV`, then a
  **manual approval hold**, then `dbt-main-prod` builds into `DBT_SCHEMA=PROD`.

Key behaviours:

- **Snowflake credentials** come only from the `snowflake-dbt-demo` **context**,
  attached only to the five jobs that touch Snowflake.
- **Per-PR schema** is resolved at run time by
  `scripts/resolve_pr_schema.py` (numeric PR → sanitized branch → build number),
  always `PR_…`, uppercase `A-Z0-9_`, length-capped, never `DEV`/`PROD`.
- **Cleanup** uses modern flexible `requires` (`dbt-pr-build: terminal`) so it
  runs after the build reaches any terminal status (success, failed, canceled,
  unauthorized, not_run) and always tears the schema down. The
  `drop_pr_schema` macro refuses anything not prefixed `PR_` and refuses
  `DEV`/`PROD`.
- **Artifacts** (`target/manifest.json`, `target/run_results.json`,
  `target/compiled`, `logs`) are stored after the build step, so they persist
  even when `dbt build` fails (`store_artifacts` runs after a failed step; it
  does not run only for killed or timed-out jobs).
- **Reruns** are manual, at the **job** boundary ("Rerun from failed" re-runs a
  failed job and everything downstream from scratch). There is no step-level
  dbt resume and no automatic rerun; `dbt build` always starts fresh.

`dbt parse` remains part of local offline validation. CircleCI uses a distinct,
credentialed `dbt-compile` job because compilation can open a warehouse
connection before the real `dbt-pr-build`.

### Validate the CI config locally

```bash
# Offline contract tests for the config (semantics, contexts, filters, etc.)
uv run pytest tests/test_circleci_config.py

# If the CircleCI CLI is installed and authenticated:
circleci config validate .circleci/config.yml
```

### Connected demo project

- CircleCI project: `gh/townerhale-circleci/groupe-dynamite-dbt-demo`
- Credential context: `snowflake-dbt-demo` (created empty; populate it only
  after the Snowflake service identity is provisioned)
- GitHub namespace: personal account, so the demo uses a visible manual
  approval hold and does not claim organization/team-restricted enforcement

## Running against Snowflake (later)

1. Copy `.env.example` to `.env` and fill in real values (never commit `.env`).
2. Review and run `SQL/bootstrap.sql` manually to provision least-privilege
   `GROUPE_DYNAMITE_DEMO`-prefixed objects.
3. `uv run dbt seed`, then `uv run dbt build` (runs models + tests).
4. Tear down with `SQL/teardown.sql` when finished.

Detailed demo documentation will be added later.

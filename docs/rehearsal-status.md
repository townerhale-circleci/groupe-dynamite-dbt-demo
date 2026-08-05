# Rehearsal evidence & status

Honest record of what has actually been verified vs. what has not. **Read this
before promising any live capability.** "Unverified" means exactly that — it does
not mean broken, but you must not present it as proven.

_Last updated: 2026-08-05._

---

## ✅ Verified

### Local offline validation
- **`uv run pytest` → 102 passed.** Full offline suite green (project contract,
  PR-schema resolver, CircleCI config contract, seed integrity, model-name
  validator).
- **Model-name gate** (`scripts/validate_model_names.py models`) passes on the
  clean tree and fails (exit 1) on the uppercase scenario.
- **SQLFluff lint** (`sqlfluff lint models`, Snowflake dialect, offline Jinja
  templater) passes.
- **`dbt parse`** (with throwaway env vars, no warehouse) succeeds — the model
  graph is valid.
- **CircleCI config validation** — `circleci config validate
  .circleci/config.yml` and the offline contract tests pass. The current config
  requires all three offline gates before `dbt-compile`, and skips cleanup when
  `dbt-pr-build` is `not_run`.

### CircleCI — pipeline #2 (offline gates + credentialed jobs)
- **Offline jobs passed:** `validate-model-names`, `python-tests`, and
  `sqlfluff` ran green without the context.
- **Historical caveat:** pipeline #2 ran before the offline-to-compile ordering
  guard and before the context was populated, so `dbt-compile` failed on
  `DBT_SNOWFLAKE_ACCOUNT`. `dbt-pr-build` was `not_run`;
  `dbt-pr-cleanup` ran under the former `terminal` dependency and failed on the
  same missing variable. Main promotion jobs were not part of this branch run.
- The current config fixes that ordering; pipeline #11 below verifies it live.

### CircleCI — pipeline #3 + Cursor MCP retrieval
- **Pipeline #3** and a **Cursor CircleCI MCP** read-only retrieval both
  **identified `Customer_Lifetime_Value.sql`** as the offending uppercase model in
  the `demo/fail-uppercase-model` scenario — confirming the MCP backup can surface
  the failing detail from CI without editing anything.

### CircleCI — pipeline #11 (current credential-boundary config)
- `validate-model-names`, `python-tests`, and `sqlfluff` all passed before the
  credentialed stage.
- Only then did `dbt-compile` start and fail on the expected missing
  `DBT_SNOWFLAKE_ACCOUNT`.
- `dbt-pr-build` and `dbt-pr-cleanup` were both `not_run`, so no PR schema was
  created and no unnecessary cleanup job attached the Snowflake context.
- GitHub showed only the three green offline checks plus the expected red
  `dbt-compile` check, matching the workflow dependency design.

### Snowflake browser-SSO privilege preflight
- Snowflake CLI browser SSO and `dbt debug` both connected successfully.
- The available role cannot create account-level databases, warehouses, roles,
  or service users. The user-level fallback could create the three isolated
  `GROUPE_DYNAMITE_DEMO_*` schemas in a personal database.
- A real DEV `dbt build` reached all eight seed executions, then Snowflake
  rejected each with `060119 (0A000): Tables cannot currently be created in a
  personal database.` No model or data test ran.
- This is a definitive privilege/platform blocker, not a dbt parsing failure.
  Live completion requires either the reviewed `SQL/bootstrap.sql` resources
  from an admin or a writable non-personal sandbox database with CREATE
  SCHEMA/TABLE/VIEW, plus non-interactive CI authentication.

### Isolated trial Snowflake environment
- Provisioned the dedicated X-Small warehouse, database, prefixed RAW/DEV/PROD
  schemas, least-privilege role, and `TYPE=SERVICE` user from the reviewed
  bootstrap design.
- Snowflake CLI and `dbt debug` both authenticated as the service user with
  `SNOWFLAKE_JWT`; the private key remains outside the repository.
- A real DEV `dbt build` completed successfully in about 19 seconds:
  **146 PASS, 0 WARN, 0 ERROR, 0 SKIP** across 8 seeds, 12 models, and 126 data
  tests.
- The CircleCI context now contains the seven required variable names with
  masked values. A live CI run is still required before calling the
  credentialed CI path verified.

---

## ❌ Not yet verified

Do **not** claim these as working until their live CI runs complete.

- **Snowflake live `dbt build`** into a
  `GROUPE_DYNAMITE_DEMO_PR_…` schema (the real Moment 2 build).
- **Manual approval hold** (`hold-promote-prod`) exercised end-to-end.
- **PROD promotion** (`dbt-main-prod` building into
  `GROUPE_DYNAMITE_DEMO_PROD`).
- **Artifact retrieval** of a *real* failed build's `run_results.json` / `logs/`
  (offline jobs' artifacts exist; a credentialed failure's artifacts haven't been
  produced because the credentialed jobs haven't run).
- **Rerun-from-failed** at the job boundary against a live build.
- **PR schema cleanup** (`dbt-pr-cleanup` dropping a real prefixed PR schema
  after a live build).

To move any of these to ✅, complete [preflight](preflight-checklist.md) sections
C–D, run it live, and update this page with the concrete result.

---

## GitHub branch protection — verified

The first protection attempt returned **HTTP 403** while this was a private
personal-account repository. After explicit operator approval, the repository
was made public and strict required checks were enabled on `main` for:

- `ci/circleci: validate-model-names`
- `ci/circleci: python-tests`
- `ci/circleci: sqlfluff`
- `ci/circleci: dbt-compile`
- `ci/circleci: dbt-pr-build`

PR #1 then reported `mergeStateStatus: BLOCKED` while `dbt-compile` was red and
`dbt-pr-build` had not run. This proves the failing CircleCI status blocks the
merge on this demo repository.

Customer POC caveat: this public visibility choice is for the demo only. A
customer should keep source private under an organization/plan that supports
required checks and team restrictions.

---

## Status matrix

| Capability | Status | Evidence / blocker |
|------------|:------:|--------------------|
| Local pytest (102) | ✅ | offline suite green |
| Model-name gate | ✅ | passes clean; fails on uppercase |
| SQLFluff lint | ✅ | Snowflake dialect, offline |
| `dbt parse` | ✅ | graph valid, no warehouse |
| CircleCI config validate | ✅ | offline contract tests pass |
| Offline CI jobs (pipeline #2) | ✅ | green, no context |
| Live offline-before-compile ordering | ✅ | pipeline #11; cleanup skipped `not_run` build |
| Credentialed CI path | ⚠️ | context populated; awaiting a fresh pipeline |
| MCP identifies failing model | ✅ | pipeline #3 + Cursor MCP → `Customer_Lifetime_Value.sql` |
| Snowflake browser SSO / `dbt debug` | ✅ | connection succeeded |
| Isolated fallback schemas | ⚠️ | created, but personal DB forbids tables |
| Trial service-user `dbt debug` | ✅ | key-pair JWT authentication succeeded |
| Live Snowflake DEV build | ✅ | 146/146 successful |
| Live Snowflake PR build | ❌ | fresh credentialed CI pipeline required |
| Approval hold end-to-end | ❌ | needs live `main` run |
| PROD promotion | ❌ | needs live `main` run |
| GitHub enforced merge block | ✅ | strict required checks; PR #1 reported BLOCKED |
| Failed-build artifact retrieval | ❌ | credentialed jobs haven't run live |
| Rerun-from-failed (live) | ❌ | needs live build |
| PR schema cleanup (live) | ❌ | needs live build |

Legend: ✅ verified · ⚠️ verified-with-caveat · ❌ not yet verified.

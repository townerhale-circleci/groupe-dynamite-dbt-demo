# Preflight checklist

Run this the morning of the demo, in order. Every item has an explicit
**pass/fail gate**. If a gate fails, fix it or switch that moment to its
degraded form (see [demo-runbook.md](demo-runbook.md) stop conditions and
[recovery-fallback.md](recovery-fallback.md)) — do not improvise live.

> **No secrets anywhere.** Nothing in this checklist prints or stores a secret.
> Snowflake credentials live only in the CircleCI `snowflake-dbt-demo` context;
> you confirm they are *set*, never read their values.

## Names you will need (verify, don't guess)

| Thing | Value |
|-------|-------|
| CircleCI project | `gh/townerhale-circleci/groupe-dynamite-dbt-demo` |
| CircleCI context | `snowflake-dbt-demo` |
| Snowflake database | `GROUPE_DYNAMITE_DEMO` |
| Snowflake warehouse | `GROUPE_DYNAMITE_DEMO_WH` |
| Snowflake role | `GROUPE_DYNAMITE_DEMO_ROLE` |
| Snowflake user | `GROUPE_DYNAMITE_DEMO_USER` |
| Promotion schemas | `DEV`, `PROD` |
| PR schemas | `PR_<…>` (from `scripts/resolve_pr_schema.py`; uppercase `A–Z0–9_`) |
| Context variable names (values NOT shown) | `DBT_SNOWFLAKE_ACCOUNT`, `DBT_SNOWFLAKE_USER`, `DBT_SNOWFLAKE_PASSWORD`, `DBT_SNOWFLAKE_ROLE`, `DBT_SNOWFLAKE_WAREHOUSE`, `DBT_SNOWFLAKE_DATABASE` |

`DBT_SCHEMA` is **not** a context variable — CI sets it per job (`PR_<…>` / `DEV`
/ `PROD`). `DBT_THREADS` is optional (defaults to 4).

---

## A. Local repo & offline gates (no Snowflake)

Run at repo root. Each command must exit 0.

```bash
# A1. Dependencies resolve from the lockfile.
uv sync --frozen

# A2. Offline pytest suite.
uv run pytest

# A3. Model-name convention gate (snake_case).
uv run python scripts/validate_model_names.py models

# A4. SQLFluff lint (Snowflake dialect, offline Jinja templater).
uv run sqlfluff lint models

# A5. dbt parse (graph validity; no warehouse). Throwaway env values only:
export DBT_SNOWFLAKE_ACCOUNT=x DBT_SNOWFLAKE_USER=x DBT_SNOWFLAKE_PASSWORD=x \
       DBT_SNOWFLAKE_ROLE=x DBT_SNOWFLAKE_WAREHOUSE=x \
       DBT_SNOWFLAKE_DATABASE=x DBT_SCHEMA=ANALYTICS
uv run dbt parse --profiles-dir . --project-dir .

# A6. CircleCI config contract tests (offline semantics of the pipeline).
uv run pytest tests/test_circleci_config.py

# A7. (If CircleCI CLI installed + authenticated) validate the config file.
circleci config validate .circleci/config.yml
```

**Pass gate:** A1–A6 exit 0; the pytest run reports the expected suite green
(rehearsal baseline: **100 passed** — see [rehearsal-status.md](rehearsal-status.md)).
A7 prints "Config file is valid" if the CLI is present.
**Fail gate:** any non-zero exit → the offline demo (Moment 1) is at risk; fix
before proceeding. The `x` env values above are throwaway and must never be real.

---

## B. Scenario branches are in the failing state

You demo the **fail** branches; the **fix** branches are the prepared repair.
Confirm both exist on the remote and record each branch's current tip SHA so you
can restore it afterward (operator-only; see
[scenario-catalog.md](scenario-catalog.md)).

```bash
git fetch origin --prune

# List the scenario branches (all 8 should appear).
git branch -r | grep -E 'origin/demo/(fail|fix)-'

# Record the CURRENT (failing) tip of each fail branch. Save this output
# somewhere you control — you will need it to restore after the demo.
for b in uppercase-model invalid-cast broken-reference business-rule; do
  printf '%s ' "demo/fail-$b"; git rev-parse "origin/demo/fail-$b";
done
```

**Pass gate:** all four `demo/fail-*` and all four `demo/fix-*` branches exist,
and each fail branch's tip SHA is recorded.
**Fail gate:** a fail branch already points at its fixed state (a teammate ran a
rehearsal and didn't restore) → see [recovery-fallback.md](recovery-fallback.md)
→ "Demo branch already fixed" and restore it with `--force-with-lease` **before**
the demo.

> Base note: the four scenario PRs (#2 business rule, #3 uppercase, #4 invalid
> cast, #5 broken reference) currently target `feature/build-demo`. After the
> implementation PR (#1) merges to `main`, retarget them to `main` — see
> [scenario-catalog.md](scenario-catalog.md).

---

## C. CircleCI project & pipeline

In the CircleCI UI for `gh/townerhale-circleci/groupe-dynamite-dbt-demo`:

- **C1.** Project is set up and **following** the GitHub repo (pushes produce
  pipelines). Pass gate: a recent pipeline is listed.
- **C2.** Context `snowflake-dbt-demo` exists under the owning org/account.
  Pass gate: it lists exactly the six variable **names** from the table above.
  **Do not open/read the values.** Fail gate: `DBT_SNOWFLAKE_ACCOUNT` (or any of
  the six) missing → credentialed jobs will fail on connect; see
  [recovery-fallback.md](recovery-fallback.md) → "Missing context vars".
- **C3.** Expected status checks appear on a PR (Checks tab). The check contexts
  are, per job (confirm the exact strings in the Checks UI — CircleCI publishes
  one per job):

  - `ci/circleci: validate-model-names`
  - `ci/circleci: python-tests`
  - `ci/circleci: sqlfluff`
  - `ci/circleci: dbt-compile`
  - `ci/circleci: dbt-pr-build`
  - `ci/circleci: dbt-pr-cleanup`

  On `main`: `ci/circleci: dbt-main-dev` and `ci/circleci: dbt-main-prod` (the
  approval `hold-promote-prod` is a workflow gate, not a status check).

  Pass gate: the offline three post green on a healthy branch; the credentialed
  checks appear (state depends on whether the context is populated).

---

## D. Snowflake reachability (only if doing live Moments 2 & 3)

You are confirming the demo identity can connect and that the target objects
exist — **not** reading any secret. Do this from a trusted machine using your
own `.env` (never commit it), or ask the Snowflake owner to confirm in a
worksheet.

- **D1.** `GROUPE_DYNAMITE_DEMO` database and `GROUPE_DYNAMITE_DEMO_WH` warehouse
  exist; `GROUPE_DYNAMITE_DEMO_ROLE` and `GROUPE_DYNAMITE_DEMO_USER` exist with
  the grants from `SQL/bootstrap.sql`.
- **D2.** A no-op connect works with the demo identity (local `.env`, throwaway
  schema):

  ```bash
  # Uses your own local .env (gitignored). Values never printed.
  set -a; source .env; set +a
  export DBT_SCHEMA=PR_PREFLIGHT
  uv run dbt debug --profiles-dir . --project-dir .
  ```

- **D3.** `DEV` and `PROD` schemas exist (or dbt will create them on first build)
  and are safe to overwrite for the demo.

**Pass gate:** D2 `dbt debug` reports "All checks passed!" and connection OK.
**Fail gate:** any auth/permission error → Moments 2 & 3 go to their narrated
fallback; see [recovery-fallback.md](recovery-fallback.md). Currently these are
**unverified** — see [rehearsal-status.md](rehearsal-status.md).

---

## E. Backup path (MCP) reachable — optional

- **E1.** In Cursor, confirm the CircleCI MCP can list the project's recent
  pipelines and read a job's logs/artifacts (read-only). Pass gate: it returns a
  recent pipeline for the project. This is a *backup* only — see
  [mcp-backup-flow.md](mcp-backup-flow.md).

---

## Final go / no-go

| Capability | Needs | Go if… |
|------------|-------|--------|
| Moment 1 (blocked PR) | A1–A6, C1, C3 | offline gates green locally + on CI |
| Moment 2 (actionable failure) | + B, C2, D2 | context populated + Snowflake connects |
| Moment 3 (DEV→approval→PROD) | + D1, D3 | DEV/PROD reachable |
| MCP backup | E1 | optional; only after the core demo |

If Moment 2/3 prerequisites fail, you can still deliver Moment 1 live and
**narrate** 2 and 3 truthfully from config + the diagram. Say so out loud.

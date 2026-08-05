# Rehearsal evidence & status

Honest record of what has actually been verified vs. what has not. **Read this
before promising any live capability.** "Unverified" means exactly that — it does
not mean broken, but you must not present it as proven.

_Last updated: 2026-08-05._

---

## ✅ Verified

### Local offline validation
- **`uv run pytest` → 100 passed.** Full offline suite green (project contract,
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
  guard was added, so `dbt-compile` also started and failed because the context
  lacks `DBT_SNOWFLAKE_ACCOUNT`. `dbt-pr-build` was `not_run`;
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

---

## ❌ Not yet verified

Do **not** claim these as working. They require a populated context + live
Snowflake (and, for merge blocking, a GitHub entitlement this repo lacks).

- **Snowflake live `dbt build`** into a `PR_` schema (the real Moment 2 build).
- **Manual approval hold** (`hold-promote-prod`) exercised end-to-end.
- **PROD promotion** (`dbt-main-prod` building into `PROD`).
- **GitHub merge blocking** — enforced required checks blocking a merge (see the
  entitlement note below).
- **Artifact retrieval** of a *real* failed build's `run_results.json` / `logs/`
  (offline jobs' artifacts exist; a credentialed failure's artifacts haven't been
  produced because the credentialed jobs haven't run).
- **Rerun-from-failed** at the job boundary against a live build.
- **PR schema cleanup** (`dbt-pr-cleanup` dropping a real `PR_` schema after a
  live build).

To move any of these to ✅, complete [preflight](preflight-checklist.md) sections
C–D, run it live, and update this page with the concrete result.

---

## GitHub branch protection — entitlement limitation (record exactly)

Configuring branch protection / required status checks on this repo returns
**HTTP 403**. This is an **entitlement limitation, not a pipeline gap**: the repo
is a **private repo under a personal GitHub account**, and enforced required
status checks on a private repo require **GitHub Pro** (or the repo must be
**public**, or owned by an org with the entitlement).

Therefore:
- **Do not claim** that required status checks are established or that merges are
  automatically blocked on this repo.
- The "blocked unsafe PR" moment is demonstrated by the **failing (red) check**
  that such a rule would key off of, plus operator discipline (not merging).
- In a customer **org** (or a Pro/public repo), that same red check becomes a
  real, enforced merge block. Frame it that way — see
  [poc-extension.md](poc-extension.md) §3 and
  [recovery-fallback.md](recovery-fallback.md) §4.

---

## Status matrix

| Capability | Status | Evidence / blocker |
|------------|:------:|--------------------|
| Local pytest (100) | ✅ | offline suite green |
| Model-name gate | ✅ | passes clean; fails on uppercase |
| SQLFluff lint | ✅ | Snowflake dialect, offline |
| `dbt parse` | ✅ | graph valid, no warehouse |
| CircleCI config validate | ✅ | offline contract tests pass |
| Offline CI jobs (pipeline #2) | ✅ | green, no context |
| Live offline-before-compile ordering | ✅ | pipeline #11; cleanup skipped `not_run` build |
| Credentialed CI path | ⚠️ | compile blocked on missing `DBT_SNOWFLAKE_ACCOUNT`; build not run |
| MCP identifies failing model | ✅ | pipeline #3 + Cursor MCP → `Customer_Lifetime_Value.sql` |
| Live Snowflake PR build | ❌ | needs populated context |
| Approval hold end-to-end | ❌ | needs live `main` run |
| PROD promotion | ❌ | needs live `main` run |
| GitHub enforced merge block | ❌ | 403 entitlement (personal private repo) |
| Failed-build artifact retrieval | ❌ | credentialed jobs haven't run live |
| Rerun-from-failed (live) | ❌ | needs live build |
| PR schema cleanup (live) | ❌ | needs live build |

Legend: ✅ verified · ⚠️ verified-with-caveat · ❌ not yet verified.

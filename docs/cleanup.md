# Cleanup guide

Return the demo to a clean state afterward. **Every destructive action here is
manual and operator-gated** — nothing in this guide should be automated, and
nothing runs on its own. Work top-down: transient CI schemas first, then
promotion schemas, then GitHub/branches, then (only if fully finished) the full
Snowflake teardown.

> Confirm you are targeting **only** `GROUPE_DYNAMITE_DEMO*` objects before
> running anything destructive. No secrets appear in this guide.

---

## 1. PR schemas (`PR_<…>`) — usually automatic, verify anyway

`dbt-pr-cleanup` drops each PR's disposable schema after a started build
succeeds, fails, is canceled, or becomes unauthorized. It does not run when the
build is `not_run`, because offline-gate failures create no schema. To confirm
none leaked, list schemas in Snowflake and drop any
stray `PR_` schema with the **guarded** macro (it refuses non-`PR_` names and
refuses `DEV`/`PROD`):

```sql
-- In a Snowflake worksheet, review before running:
SHOW SCHEMAS IN DATABASE GROUPE_DYNAMITE_DEMO;   -- look for PR_ leftovers
```

```bash
# For each stray PR_ schema (credentials from your local .env; never committed):
uv run dbt run-operation drop_pr_schema \
    --args '{schema_name: PR_<the_schema>}' --profiles-dir . --project-dir .
```

The macro will `raise_compiler_error` and drop nothing if the name isn't `PR_…`
or is `DEV`/`PROD`. Safe by construction.

---

## 2. DEV / PROD demo schemas — manual, deliberate

These are the promotion schemas. Drop them **only** if you're tearing the demo
down (not between rehearsals — you'll just rebuild them). The guarded macro
**refuses** `DEV`/`PROD` on purpose, so this is a plain, explicit SQL action:

```sql
-- Manual. Review, confirm the database, then run:
DROP SCHEMA IF EXISTS GROUPE_DYNAMITE_DEMO.DEV;
DROP SCHEMA IF EXISTS GROUPE_DYNAMITE_DEMO.PROD;
```

If you're keeping the demo warm for future runs, **skip this** — a rebuild
overwrites DEV/PROD anyway.

---

## 3. Context secret names — rotate/remove (values never shown)

If the engagement is over, remove the Snowflake credentials from the
`snowflake-dbt-demo` context, or rotate them. You operate on **names**, never
values.

- In the CircleCI UI → Contexts → `snowflake-dbt-demo`, delete these variables
  (or the whole context if nothing else uses it):
  - `DBT_SNOWFLAKE_ACCOUNT`
  - `DBT_SNOWFLAKE_USER`
  - `DBT_SNOWFLAKE_PASSWORD`
  - `DBT_SNOWFLAKE_ROLE`
  - `DBT_SNOWFLAKE_WAREHOUSE`
  - `DBT_SNOWFLAKE_DATABASE`
- If the demo Snowflake user persists, **rotate its password** in Snowflake even
  after deleting the context value, so no stale secret remains anywhere.

Never paste the values into chat, a doc, or a commit while doing this.

---

## 4. Remote scenario branches & PRs — manual

Once the demo is done and you don't need the scenarios again:

```bash
git fetch origin --prune

# Close (don't delete) the PRs first if you want to preserve the discussion,
# then delete the remote branches. Deleting the fail/fix branch pair per scenario:
for b in uppercase-model invalid-cast broken-reference business-rule; do
  git push origin --delete "demo/fail-$b" "demo/fix-$b";
done
```

- Close PRs **#2, #3, #4, #5** in GitHub (or let branch deletion auto-close them).
- Keep `feature/build-demo` until the implementation PR (#1) has merged to `main`;
  delete it only after #1 lands and you've retargeted/closed the scenarios.
- **Do not delete `main`.**

This rewrites nothing — deleting a remote branch is not a force operation. Restore
of a *failing state* (force-with-lease) is a separate operator action documented
in [scenario-catalog.md](scenario-catalog.md); it is **not** part of cleanup.

---

## 5. Full Snowflake teardown — manual, last

When the demo is permanently finished, remove everything `SQL/bootstrap.sql`
created. Review each statement, then run in a worksheet with the appropriate
admin role. `SQL/teardown.sql` is the reviewed template:

```sql
-- SQL/teardown.sql (review before running; DROP DATABASE is irreversible):
DROP USER IF EXISTS GROUPE_DYNAMITE_DEMO_USER;         -- SECURITYADMIN
DROP ROLE IF EXISTS GROUPE_DYNAMITE_DEMO_ROLE;         -- SECURITYADMIN
DROP DATABASE IF EXISTS GROUPE_DYNAMITE_DEMO;          -- SYSADMIN (cascades schemas)
DROP WAREHOUSE IF EXISTS GROUPE_DYNAMITE_DEMO_WH;      -- SYSADMIN
```

`DROP DATABASE` cascades every schema (including `DEV`/`PROD` and any `PR_`
leftovers), so steps 1–2 are unnecessary if you run the full teardown. Confirm
the database name one more time before executing — this is irreversible.

---

## Order-of-operations summary

| Step | Action | Destructive? | Who / where |
|------|--------|:---:|-------------|
| 1 | Drop stray `PR_` schemas | yes (guarded) | operator, dbt macro |
| 2 | Drop `DEV`/`PROD` schemas | yes | operator, Snowflake worksheet |
| 3 | Remove/rotate context secrets | n/a (names) | operator, CircleCI UI + Snowflake |
| 4 | Delete scenario branches, close PRs | branch delete (non-force) | operator, git + GitHub |
| 5 | Full Snowflake teardown | **yes, irreversible** | admin, `SQL/teardown.sql` |

Nothing here is automated. Do each step consciously.

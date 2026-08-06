# Cleanup guide

Return the demo to a clean state afterward. **Every destructive action here is
manual and operator-gated** — nothing in this guide should be automated, and
nothing runs on its own. Work top-down: transient CI schemas first, then
promotion schemas, then GitHub/branches, then (only if fully finished) the full
Snowflake teardown.

> Confirm you are targeting **only** `GROUPE_DYNAMITE_DEMO*` objects before
> running anything destructive. No secrets appear in this guide.

---

## 1. Prefixed PR schemas — usually automatic, verify anyway

`dbt-pr-cleanup` drops each PR's disposable schema after a started build
succeeds, fails, is canceled, or becomes unauthorized. It does not run when the
build is `not_run`, because offline-gate failures create no schema. To confirm
none leaked, list schemas in the approved demo database and drop any stray
`GROUPE_DYNAMITE_DEMO_PR_…` schema with the guarded macro:

```sql
-- Replace this placeholder outside the repo; review before running:
SHOW SCHEMAS IN DATABASE <APPROVED_DEMO_DATABASE>;
```

```bash
# For each stray prefixed PR schema (credentials from local .env; never committed):
uv run dbt run-operation drop_pr_schema \
    --args '{schema_name: GROUPE_DYNAMITE_DEMO_PR_<id>}' \
    --profiles-dir . --project-dir .
```

The macro drops nothing unless the name begins
`GROUPE_DYNAMITE_DEMO_PR_`; it also protects the prefixed RAW/DEV/PROD schemas.

---

## 2. Prefixed DEV / PROD schemas — manual, deliberate

These are the promotion schemas. Drop them **only** if you're tearing the demo
down (not between rehearsals — you'll just rebuild them). The guarded macro
**refuses** promotion schemas on purpose, so this is an explicit SQL action:

```sql
-- Manual. Replace the database placeholder outside the repo, then review:
DROP SCHEMA IF EXISTS <APPROVED_DEMO_DATABASE>.GROUPE_DYNAMITE_DEMO_DEV;
DROP SCHEMA IF EXISTS <APPROVED_DEMO_DATABASE>.GROUPE_DYNAMITE_DEMO_PROD;
DROP SCHEMA IF EXISTS <APPROVED_DEMO_DATABASE>.GROUPE_DYNAMITE_DEMO_RAW;
```

If you're keeping the demo warm for future runs, **skip this** — a rebuild
overwrites the DEV/PROD targets anyway.

---

## 3. Context secret names — rotate/remove (values never shown)

If the engagement is over, remove the Snowflake credentials from the
`snowflake-dbt-demo` context, or rotate them. You operate on **names**, never
values.

- In the CircleCI UI → Contexts → `snowflake-dbt-demo`, delete these variables
  (or the whole context if nothing else uses it):
  - `DBT_SNOWFLAKE_ACCOUNT`
  - `DBT_SNOWFLAKE_USER`
  - `DBT_SNOWFLAKE_AUTHENTICATOR`
  - `DBT_SNOWFLAKE_PRIVATE_KEY`
  - `DBT_SNOWFLAKE_ROLE`
  - `DBT_SNOWFLAKE_WAREHOUSE`
  - `DBT_SNOWFLAKE_DATABASE`
- Rotate or revoke whichever approved CI credential was used, so no stale
  password, key, or token remains.

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
- PRs #1 and #6 are merged and the scenarios now target `main`.
  `feature/build-demo` can be deleted when it is no longer needed as historical
  rehearsal evidence.
- Close the prepared `demo/promotion-ready` PR after the demo if it was not
  merged, then delete that branch.
- **Do not delete `main`.**

This rewrites nothing — deleting a remote branch is not a force operation. Restore
of a *failing state* (force-with-lease) is a separate operator action documented
in [scenario-catalog.md](scenario-catalog.md); it is **not** part of cleanup.

---

## 5. Full Snowflake teardown — manual, last

This applies only if an administrator used the full standalone
`SQL/bootstrap.sql` path. The current least-privilege fallback created schemas
inside an existing database, so use steps 1–2 and **never drop that database**.
For a standalone deployment, review `SQL/teardown.sql` with an admin:

```sql
-- SQL/teardown.sql (review before running; DROP DATABASE is irreversible):
DROP USER IF EXISTS GROUPE_DYNAMITE_DEMO_USER;         -- SECURITYADMIN
DROP ROLE IF EXISTS GROUPE_DYNAMITE_DEMO_ROLE;         -- SECURITYADMIN
DROP DATABASE IF EXISTS GROUPE_DYNAMITE_DEMO;          -- SYSADMIN (cascades schemas)
DROP WAREHOUSE IF EXISTS GROUPE_DYNAMITE_DEMO_WH;      -- SYSADMIN
```

`DROP DATABASE` cascades every prefixed demo schema in the standalone path.
Never run it against a shared or personal database.

---

## Order-of-operations summary

| Step | Action | Destructive? | Who / where |
|------|--------|:---:|-------------|
| 1 | Drop stray prefixed PR schemas | yes (guarded) | operator, dbt macro |
| 2 | Drop prefixed RAW/DEV/PROD schemas | yes | operator, Snowflake worksheet |
| 3 | Remove/rotate context secrets | n/a (names) | operator, CircleCI UI + Snowflake |
| 4 | Delete scenario branches, close PRs | branch delete (non-force) | operator, git + GitHub |
| 5 | Full Snowflake teardown | **yes, irreversible** | admin, `SQL/teardown.sql` |

Nothing here is automated. Do each step consciously.

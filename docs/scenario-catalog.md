# Scenario catalog

Four prepared failure PRs, each with a matching fix branch. You demo the
**fail** branch; the **fix** branch is the prepared repair you fast-forward to,
live. Each scenario fails at a *different* stage of the pipeline, which is the
teaching point: unsafe things fail early and cheap, real data/SQL problems fail
with evidence.

> **Accuracy note.** The exact changed file and line in each `fail` branch should
> be confirmed during [preflight](preflight-checklist.md) (open the PR's *Files
> changed* tab, or diff the branch on a machine where cross-branch git reads are
> permitted). The descriptions below are by design of the pipeline; the
> uppercase filename (`Customer_Lifetime_Value.sql`) is confirmed from rehearsal
> MCP retrieval (see [rehearsal-status.md](rehearsal-status.md)).

## At a glance

| PR | Fail branch | Fix branch | Fails at | Caught by | Context attached? |
|----|-------------|------------|----------|-----------|:---:|
| #3 | `demo/fail-uppercase-model` | `demo/fix-uppercase-model` | offline gate | `validate-model-names` | ❌ no |
| #5 | `demo/fail-broken-reference` | `demo/fix-broken-reference` | compile / parse | `dbt-compile` (and local `dbt parse`) | ✅ yes; graph fails before a warehouse query |
| #4 | `demo/fail-invalid-cast` | `demo/fix-invalid-cast` | real build in Snowflake | `dbt-pr-build` (runtime SQL error) | ✅ yes |
| #2 | `demo/fail-business-rule` | `demo/fix-business-rule` | data test after build | `dbt-pr-build` (`non_negative` test) | ✅ yes |

Primary runbook uses **#3** (Moment 1) and **#4** (Moment 2). #5 and #2 are
strong alternates / follow-ups.

---

## #3 — Uppercase model name (blocked unsafe PR)

- **What's wrong:** a model file with an uppercase, non-snake_case name —
  `Customer_Lifetime_Value.sql`. Violates the naming convention enforced by
  `scripts/validate_model_names.py`.
- **Where it's caught:** the offline `validate-model-names` job, **before** the
  `snowflake-dbt-demo` context is attached to anything. Exit 1, message lists the
  invalid filename.
- **Why it matters:** an unsafe change can't reach Snowflake; the failing check is
  the merge-block signal.
- **Fix:** `demo/fix-uppercase-model` renames the file to
  `customer_lifetime_value.sql` (and fixes any `ref()` accordingly).
- **Reproduce locally:** `uv run python scripts/validate_model_names.py models`.

## #5 — Broken `ref()` (compile/parse failure)

- **What's wrong:** a model references a non-existent model via `ref('…')`, so the
  dbt graph can't resolve.
- **Where it's caught:** locally by `uv run dbt parse`; in CI by `dbt-compile`
  (compilation fails before the real `dbt-pr-build`). Offline lint/tests may still
  pass, which is the lesson: graph integrity is a distinct gate.
- **Fix:** `demo/fix-broken-reference` restores the correct `ref()` target.
- **Reproduce locally:** `uv run dbt parse --profiles-dir . --project-dir .` with
  the throwaway env vars from the preflight (it errors on the unresolved ref).

## #4 — Invalid cast (actionable Snowflake runtime failure)

- **What's wrong:** a `CAST`/type conversion that is syntactically valid and
  passes lint + compile, but fails at execution in Snowflake (e.g. casting a
  non-numeric value to a number).
- **Where it's caught:** `dbt-pr-build`, at run time in the disposable
  `GROUPE_DYNAMITE_DEMO_PR_…` schema. `run_results.json` records the failing node with `status: "error"` and
  the Snowflake message; `logs/` holds the compiled SQL.
- **Why it matters:** this is the *actionable failure* — evidence in artifacts, no
  guessing, human applies the fix.
- **Fix:** `demo/fix-invalid-cast` corrects the cast/expression.

## #2 — Business rule (`non_negative` test failure)

- **What's wrong:** model logic (or seed-derived data) produces a **negative**
  value in a column the retail rules forbid from going negative. The custom
  `non_negative` generic test (`macros/test_non_negative.sql`) fails.
- **Where it's caught:** the test phase of `dbt-pr-build` — the model **builds**,
  then the test fails, so `run_results.json` shows a `test` node failure with the
  failing rows query. Columns guarded by `non_negative` include `net_sales`,
  `gross_sales`, `avg_order_value`, `quantity_available`, `units_sold`,
  `units_returned`, `return_amount`, and `return_rate` (see
  `models/marts/_marts.yml`).
- **Why it matters:** shows that dbt tests encode business rules, not just schema
  shape; a build can succeed and still be rejected by a rule.
- **Fix:** `demo/fix-business-rule` corrects the logic so the value can't go
  negative.

---

## Repairing a scenario live — fast-forward fail → fix (safe)

The fix branch is the failing branch plus the repair commit(s), so the failing
PR branch can be **fast-forwarded** to the fixed state. Fast-forward only — no
rebase, no force — so it's non-destructive and obvious.

```bash
git fetch origin

# Pick ONE scenario. Example: invalid cast (PR #4).
git switch demo/fail-invalid-cast

# Fast-forward the PR branch to the prepared fix. --ff-only refuses to run
# unless it is a clean fast-forward, so you can't accidentally rewrite history.
git merge --ff-only origin/demo/fix-invalid-cast

# Push the updated PR branch. This triggers a fresh CI run on the PR.
git push origin demo/fail-invalid-cast
```

Repeat with the matching branch names for the other scenarios:
`demo/fail-uppercase-model` ↔ `demo/fix-uppercase-model`,
`demo/fail-broken-reference` ↔ `demo/fix-broken-reference`,
`demo/fail-business-rule` ↔ `demo/fix-business-rule`.

**If `--ff-only` refuses** (the fix isn't a fast-forward of the fail branch), do
**not** force. Either the branches diverged or a rehearsal left them modified —
stop and reconcile off-demo. See "Demo branch already fixed" in
[recovery-fallback.md](recovery-fallback.md).

---

## Restoring a scenario to its failing state — operator-only, force-with-lease

After a rehearsal or the live demo, the fail branch points at the fixed commit.
To reset it back to the recorded failing SHA, use `--force-with-lease`. This is
**an operator action, performed deliberately by a human — never automated, never
scripted into CI.**

Preconditions:
1. You recorded the failing tip SHA during [preflight](preflight-checklist.md)
   step B (`git rev-parse origin/demo/fail-<scenario>`). Call it `<BAD_SHA>`.
2. You know the branch's current remote SHA (the fixed one). Call it
   `<CURRENT_REMOTE_SHA>` — get it with `git rev-parse origin/demo/fail-<scenario>`
   after a fetch.

```bash
git fetch origin

# Confirm what the remote currently points at (the fixed state).
git rev-parse origin/demo/fail-invalid-cast   # -> <CURRENT_REMOTE_SHA>

# Move your local branch back to the recorded failing commit.
git switch demo/fail-invalid-cast
git reset --hard <BAD_SHA>

# Push the reset, but ONLY if the remote is still at the SHA you expect.
# --force-with-lease aborts if someone else moved the branch meanwhile.
git push --force-with-lease=demo/fail-invalid-cast:<CURRENT_REMOTE_SHA> \
    origin demo/fail-invalid-cast
```

Rules for this operation:
- A human runs it, understanding it rewrites the remote branch history.
- Never bare `--force`; always `--force-with-lease` pinned to the expected SHA.
- Never wire this into a hook, script, or CI job.
- If the lease check fails, stop and investigate — do not retry with `--force`.

---

## Base retargeting (temporary)

The four scenario PRs currently open against **`feature/build-demo`** because the
implementation PR (#1) has not landed on `main` yet. Once #1 merges to `main`:

1. In each scenario PR (#2, #3, #4, #5), change the base branch from
   `feature/build-demo` to `main` (GitHub PR → *Edit* → base branch).
2. Re-run CI on each so the checks reflect the `main` base.
3. Confirm the PR diffs still show only the intended single-file change (the
   retarget shouldn't pull in unrelated commits).

Do the retarget off-demo, verify, then use the branches as above.
